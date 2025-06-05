from temporalio import activity
from asyncio.tasks import gather
import os
import asyncio
from qdrant_client import models
import uuid

from database.database_utils import (
    get_record,
    get_all_records,
    get_first_matching_record
)

from database.vector_database_utils import (
    text_to_vec,
    get_qdrant_client
)

from database.database_models import (
    VECTORS_FOR_PB_DATA,
    VectorMetadata,
    PDF_CHUNKS, PDF_SEGMENTS, PDF_TOPICS, JOB_REQUESTS,
    PdfChunksRecord, PdfSegmentsRecord, PdfTopicsRecord, JobRequestsRecord
)

from utils import (
    save_json, read_json, remove_file
)


# --- HELPFUL TYPES ---
ChunkId = str
ChunkIdsBatchFilePath = str
# 100 is the max the current embedding API can handle in one call
MAX_BATCH_SIZE_FOR_EMBEDDING = 100 
BATCH_SIZE = 250


# --- Helper Functions ---
async def prepare_vector_metadata_for_chunk(chunk_id: str) -> VectorMetadata:
    chunk: PdfChunksRecord = await get_record(PDF_CHUNKS, chunk_id)
    parent_segment: PdfSegmentsRecord = await get_record(PDF_SEGMENTS, chunk['segment'])
    parent_topic: PdfTopicsRecord | None = await get_first_matching_record(PDF_TOPICS, options={
        "filter": f"""
        source_pdf='{chunk['source_pdf']}' && 
        start_indx<={parent_segment['segment_index_in_document']} &&
        end_indx>={parent_segment['segment_index_in_document']}
        """
    })

    if parent_topic is None:
        raise Exception(f"Failed to get parent topic for chunk - {chunk_id}")
    
    vec_metadata: VectorMetadata = {
        "source_pdf": chunk['source_pdf'],
        "chunk_id": chunk['id'],
        "segment_id": parent_segment['id'],
        "topic_id": parent_topic['id'],
        "chunk_index_in_segment": chunk['chunk_index_in_segment'],
        "segment_index_in_document": parent_segment['segment_index_in_document'],
        "topic_number": parent_topic['topic_number'],
        "summary_text": parent_topic['context_summary'],
        "chunk_text": chunk['chunk_text'],
        "segment_type": parent_segment['segment_type']
    }

    return vec_metadata


async def construct_context_vector_and_save(chunk_ids: list[ChunkId]):
    activity.logger.info(f"Starting vector creation and save for chunk batch - {chunk_ids[0]}")

    # Create the vector metadata for each chunk
    vector_metadata_generate_handles = []
    for chunk_id in chunk_ids:
        handle = prepare_vector_metadata_for_chunk(chunk_id)
        vector_metadata_generate_handles.append(handle)
    
    vector_metadata_lst: list[VectorMetadata] = await asyncio.tasks.gather(*vector_metadata_generate_handles)

    text_lst = []
    for metadata_elem in vector_metadata_lst:
        text_lst.append(f"{metadata_elem['summary_text']}\n{metadata_elem['chunk_text']}")

    embeddings = await text_to_vec(text_lst, "RETRIEVAL_DOCUMENT")

    if embeddings is None:
        raise Exception(
            f"Failed to generate vector for chunk & topic - {chunk_ids[0]}")

    # Pair together vector and metadata
    points = []
    for vec, vec_metadata in zip(embeddings, vector_metadata_lst):
        point = models.PointStruct(
            id=str(uuid.uuid4()), 
            vector=vec.values, # type: ignore
            payload=vec_metadata # type: ignore
        )
        points.append(point)

    # Save to vec DB
    client = await get_qdrant_client()
    operation = await client.upsert(
        collection_name=VECTORS_FOR_PB_DATA,
        wait=True,
        points=points
    )

    if operation.status != 'completed':
        raise Exception(f'Failed to save vector to DB - {chunk_id}')


# --- Activites ---
@activity.defn
async def fetch_chunk_ids_and_save_batch(job_record: JobRequestsRecord) -> list[ChunkIdsBatchFilePath]:
    source_pdf_id = job_record['source_pdf']
    chunks: list[PdfChunksRecord] = await get_all_records(PDF_CHUNKS, options={
        "filter": f"source_pdf='{source_pdf_id}'",
        "fields": "id"
    })

    batch_file_paths: list[ChunkIdsBatchFilePath] = []
    base_job_temp_dir = f"/tmp/{job_record['id']}"
    await asyncio.to_thread(os.makedirs, base_job_temp_dir, exist_ok=True)

    for idx in range(0, len(chunks), BATCH_SIZE):
        current_batch: list[ChunkId] = [chunk['id'] 
                                        for chunk in chunks[idx:idx+BATCH_SIZE]]
        filename_suffix = f"vector_chunk_{idx}_{idx + BATCH_SIZE}.json"
        tmp_file_path = os.path.join(base_job_temp_dir, filename_suffix)
        await asyncio.to_thread(save_json, tmp_file_path, current_batch)
        batch_file_paths.append(tmp_file_path)
    
    return batch_file_paths


@activity.defn
async def process_chunk_batch(chunk_ids_batch_path: ChunkIdsBatchFilePath):
    chunk_ids: list[ChunkId] = await asyncio.to_thread(read_json, chunk_ids_batch_path)
    
    context_vector_batch_handles = []
    for idx in range(0, len(chunk_ids), MAX_BATCH_SIZE_FOR_EMBEDDING):
        current_batch_of_chunk_ids = chunk_ids[idx: idx + MAX_BATCH_SIZE_FOR_EMBEDDING]
        handle = construct_context_vector_and_save(current_batch_of_chunk_ids)
        context_vector_batch_handles.append(handle)

    await gather(*context_vector_batch_handles)

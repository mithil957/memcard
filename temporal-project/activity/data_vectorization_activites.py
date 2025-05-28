from temporalio import activity

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
    PDF_CHUNKS, PDF_SEGMENTS, PDF_TOPICS,
    PdfChunksRecord, PdfSegmentsRecord, PdfTopicsRecord
)


# --- HELPFUL TYPES ---
ChunkId = str
ChunkBatch = list[ChunkId]


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


# --- Activites ---
@activity.defn
async def get_chunk_id_batches(source_pdf_id: str) -> list[ChunkBatch]:
    chunks: list[PdfChunksRecord] = await get_all_records(PDF_CHUNKS, options={
        "filter": f"source_pdf='{source_pdf_id}'",
        "fields": "id"
    })

    batches: list[ChunkBatch] = []
    for i in range(0, len(chunks), 100):
        current_batch: list[ChunkId] = [chunk['id'] for chunk in chunks[i:i+100]]
        batches.append(current_batch)
    
    return batches


@activity.defn
async def construct_context_vector_and_save(chunk_ids: ChunkBatch):
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

from temporalio import activity
import asyncio
from asyncio.tasks import gather
import os
from baml_client.config import set_log_level
from baml_client import types
from baml_client.async_client import b
from prompts.chunks_prompt import CHUNKING_PROMPT

from utils import (
    save_json, read_json, remove_file
)

from database.database_utils import (
    get_record,
    get_all_records,
    save_record
)

from database.database_models import (
    PdfSegmentsRecord, PdfChunksRecord, JobRequestsRecord,
    PDF_SEGMENTS, PDF_CHUNKS, JOB_REQUESTS
)

from database.baml_funcs import chunk_segment

# --- CONFIG ---
set_log_level("OFF")
BATCH_SIZE = 200


# --- Helpful Types ---
SegmentId = str
SegmentBatchFilePath = str


# --- Helpful Functions ---
async def chunk_segment_and_save(segment_id: SegmentId):
    # Fetch segment
    pdf_segment_record: PdfSegmentsRecord = await get_record(PDF_SEGMENTS, segment_id)
    
    segment_baml = types.SegmentRaw(
        segment_text=pdf_segment_record['segment_text'],
        segment_type=types.SegmentType(pdf_segment_record['segment_type'])
    )

    # Chunk segment
    instructions = CHUNKING_PROMPT['chunker']['signature']['instructions']
    demo_examples = [types.DemoExampleV2(**d) for d in CHUNKING_PROMPT['chunker']['demos']]

    chunks: list[str] = await chunk_segment(instructions, demo_examples, segment_baml)

    # Save chunks
    for indx, chunk in enumerate(chunks):
        chunk_record: PdfChunksRecord = {
            "segment": pdf_segment_record['id'],
            "source_pdf": pdf_segment_record['source_pdf'],
            "chunk_index_in_segment": indx,
            "chunk_text": chunk
        } # type: ignore

        try:
            saved_record: PdfChunksRecord = await save_record(PDF_CHUNKS, chunk_record)
            activity.logger.info(f"Saved chunk record - {saved_record['id']}")
        except Exception as e:
            activity.logger.error(f"Error saving chunk - {chunk_record} - {e}")


# --- Activites ---
@activity.defn
async def fetch_segment_ids_and_save_batch(job_record: JobRequestsRecord) -> list[SegmentBatchFilePath]:
    source_pdf_id = job_record['source_pdf']

    records: list[PdfSegmentsRecord] = await get_all_records(PDF_SEGMENTS, options={
        "filter": f"source_pdf='{source_pdf_id}'",
        "fields": "id"
    })

    segment_batch_file_paths = []
    base_job_temp_dir = f"/tmp/{job_record['id']}"
    await asyncio.to_thread(os.makedirs, base_job_temp_dir, exist_ok=True)
    
    segment_ids = [record['id'] for record in records]
    for idx in range(0, len(segment_ids), BATCH_SIZE):
        segement_batch = segment_ids[idx: idx + BATCH_SIZE]
        filename_suffix = f"segment_{idx}_{idx + BATCH_SIZE}.json"
        tmp_file_path = os.path.join(base_job_temp_dir, filename_suffix)
        await asyncio.to_thread(save_json, tmp_file_path, segement_batch)
        segment_batch_file_paths.append(tmp_file_path)
    
    return segment_batch_file_paths


@activity.defn
async def fetch_segment_batch_and_chunk(segment_batch_path: SegmentBatchFilePath) -> list[SegmentId]:
    segment_ids_for_batch: list[SegmentId] = await asyncio.to_thread(read_json, segment_batch_path)

    chunking_hundles = []
    for segment_id in segment_ids_for_batch:
        handle = chunk_segment_and_save(segment_id)
        chunking_hundles.append(handle)
    
    await gather(*chunking_hundles)
    return segment_ids_for_batch
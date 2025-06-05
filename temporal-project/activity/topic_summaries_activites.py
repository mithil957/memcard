from temporalio import activity
import os
import asyncio
from asyncio.tasks import gather

from baml_client.config import set_log_level
from baml_client import types
from baml_client.async_client import b
from baml_py.errors import BamlClientError

from database.database_utils import (
    get_all_records,
    update_record,
    get_first_matching_record
)

from database.database_models import (
    PdfTopicsRecord, PdfSegmentsRecord, JobRequestsRecord,
    PDF_TOPICS, PDF_SEGMENTS, JOB_REQUESTS
)

from utils import (
    save_json, read_json, remove_file
)

from database.baml_funcs import generate_topic_summary, generate_contextual_topic_summary

# ---  CONFIG --- 
set_log_level("OFF")
BATCH_SIZE = 200

# --- Helpful Types ---
PdfTopicsRecordsBatchFilePath = str

# --- Helpful Functions ---
async def generate_and_save_base_summary(topic_record: PdfTopicsRecord):
    # get segments within topic range
    segment_records: list[PdfSegmentsRecord] = await get_all_records(PDF_SEGMENTS, options={
        "filter": f"""
        source_pdf='{topic_record['source_pdf']}' && 
        segment_index_in_document>={topic_record['start_indx']} &&
        segment_index_in_document<={topic_record['end_indx']}
        """,
        "sort": "segment_index_in_document"
    })

    raw_segments_baml = []
    for segment in segment_records:
        raw_segment = types.SegmentRaw(segment_type=types.SegmentType(segment["segment_type"]),
                         segment_text=segment['segment_text'])
        raw_segments_baml.append(raw_segment)

    try:
        base_summary = await generate_topic_summary(raw_segments_baml)
    except BamlClientError as e:
        if "PROHIBITED_CONTENT" in e.message: # type: ignore
            base_summary = "FAILED - PROHIBITED_CONTENT"
        else:
            raise e
    

    # update the topic record with base summary
    record_with_summary: PdfTopicsRecord = {
        "base_summary": base_summary.rstrip('\n') # BAML includes this char after parsing, so need to remove it here
    } # type: ignore

    await update_record(PDF_TOPICS, topic_record['id'], record_with_summary)


async def generate_and_save_context_summary(topic_record: PdfTopicsRecord):
    # get segements within topic range
    segment_records: list[PdfSegmentsRecord] = await get_all_records(PDF_SEGMENTS, options={
        "filter": f"""
            source_pdf='{topic_record['source_pdf']}' && 
            segment_index_in_document>={topic_record['start_indx']} &&
            segment_index_in_document<={topic_record['end_indx']}
            """,
        "sort": "segment_index_in_document"
    })

    raw_segments_baml = []
    for segment in segment_records:
        raw_segment = types.SegmentRaw(segment_type=types.SegmentType(segment["segment_type"]),
                         segment_text=segment['segment_text'])
        raw_segments_baml.append(raw_segment)

    
    # get surrounding topics
    prev_topic: PdfTopicsRecord | None = await get_first_matching_record(PDF_TOPICS, options={
        "filter": f"""
            source_pdf='{topic_record['source_pdf']}' &&
            topic_number={topic_record['topic_number'] - 1}
            """})
        
    prev_topic_base_summary = "N/A" if prev_topic is None else prev_topic["base_summary"]

    next_topic: PdfTopicsRecord | None = await get_first_matching_record(PDF_TOPICS, options={
        "filter": f"""
            source_pdf='{topic_record['source_pdf']}' &&
            topic_number={topic_record['topic_number'] + 1}
            """})
    
    next_topic_base_summary = "N/A" if next_topic is None else next_topic["base_summary"]

    # get contexutal summary
    try:
        context_summary = await generate_contextual_topic_summary(prev_topic_base_summary, next_topic_base_summary, raw_segments_baml)
    except BamlClientError as e:
        if "PROHIBITED_CONTENT" in e.message: # type: ignore
            base_summary = "FAILED - PROHIBITED_CONTENT"
        else:
            raise e

    # update the topic record with context summary
    record_with_summary: PdfTopicsRecord = {
        "context_summary": context_summary.rstrip('\n') # Same as earlier comment
    } # type: ignore

    await update_record(PDF_TOPICS, topic_record['id'], record_with_summary)

# --- Activites ---
@activity.defn
async def fetch_topic_bounds_and_save_batch(job_record: JobRequestsRecord) -> list[PdfTopicsRecordsBatchFilePath]:
    source_pdf_id = job_record['source_pdf']

    records: list[PdfTopicsRecord] = await get_all_records(PDF_TOPICS, options={
        "filter": f"source_pdf='{source_pdf_id}'",
        "sort": "topic_number"
    })

    topic_records_batch_file_paths = []
    base_job_temp_dir = f"/tmp/{job_record['id']}"
    await asyncio.to_thread(os.makedirs, base_job_temp_dir, exist_ok=True)

    for idx in range(0, len(records), BATCH_SIZE):
        topic_records_batch = records[idx: idx + BATCH_SIZE]
        filename_suffix = f"topic_records_{idx}_{idx + BATCH_SIZE}.json"
        tmp_file_path = os.path.join(base_job_temp_dir, filename_suffix)
        await asyncio.to_thread(save_json, tmp_file_path, topic_records_batch)
        topic_records_batch_file_paths.append(tmp_file_path)

    return topic_records_batch_file_paths
    

@activity.defn
async def fetch_topic_records_batch_and_generate_base_summaries(topic_record_batch_path: PdfTopicsRecordsBatchFilePath):
    topic_records: list[PdfTopicsRecord] = await asyncio.to_thread(read_json, topic_record_batch_path)

    base_summary_update_handles = []
    for topic_record in topic_records:
        handle = generate_and_save_base_summary(topic_record)
        base_summary_update_handles.append(handle)
    
    await gather(*base_summary_update_handles)


@activity.defn
async def fetch_topic_records_batch_and_generate_context_summaries(topic_record_batch_path: PdfTopicsRecordsBatchFilePath):
    topic_records: list[PdfTopicsRecord] = await asyncio.to_thread(read_json, topic_record_batch_path)

    context_summary_update_handles = []
    for topic_record in topic_records:
        handle = generate_and_save_context_summary(topic_record)
        context_summary_update_handles.append(handle)
    
    await gather(*context_summary_update_handles)
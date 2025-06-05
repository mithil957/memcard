from temporalio import activity
from baml_client.config import set_log_level
from baml_client import types
from baml_client.async_client import b
from baml_py.errors import BamlClientError

import asyncio
from asyncio.tasks import gather
import os

from utils import (
    save_json, read_json, remove_file
)

from database.database_models import (
    PdfSegmentsRecord, PdfTopicsRecord, JobRequestsRecord,
    PDF_SEGMENTS, PDF_TOPICS, JOB_REQUESTS
)

from database.database_utils import (
    get_all_records,
    get_record,
    save_record,
    get_first_matching_record
)

from database.baml_funcs import identify_topic_bounds

# --- CONFIG ---
set_log_level("OFF")
BATCH_SIZE = 60
SLIDE_SIZE = 30

# --- Helpful Types ---
SegmentId = str
SegmentIndx = int
IsLastSegment = bool
SegmentInfo = tuple[SegmentId, SegmentIndx]
SegmentBatch = list[SegmentInfo]
FilePathForSegmentBatch = str
TopicBoundary = int
TopicBoundsWithSourcePDF = tuple[list[TopicBoundary], str]

# --- Activites ---
@activity.defn
async def fetch_segment_info_and_save_batch(job_record: JobRequestsRecord) -> list[FilePathForSegmentBatch]:
    source_pdf_id = job_record['source_pdf']
    records: list[PdfSegmentsRecord] = await get_all_records(PDF_SEGMENTS, options={
        "filter": f"source_pdf='{source_pdf_id}'",
        "fields": "id,segment_index_in_document",
        "sort": "segment_index_in_document"
    })

    segment_infos: list[SegmentInfo] = [
        (record['id'], record['segment_index_in_document'])
        for record in records
    ]

    base_job_temp_dir = f"/tmp/{job_record['id']}"
    await asyncio.to_thread(os.makedirs, base_job_temp_dir, exist_ok=True)
    
    # Turn the ids into batches by sliding over them using a window, (slide by 20 & collect 40)
    file_paths_for_segment_batches: list[FilePathForSegmentBatch] = []
    for i in range(0, len(segment_infos), SLIDE_SIZE):
        segment_info_batch = segment_infos[i: i + BATCH_SIZE]
        filename_suffix = f"topic_bounds_{i}_{i + BATCH_SIZE}.json"
        tmp_file_path = os.path.join(base_job_temp_dir, filename_suffix)
        await asyncio.to_thread(save_json, tmp_file_path, segment_info_batch)
        file_paths_for_segment_batches.append(tmp_file_path)

    return file_paths_for_segment_batches


@activity.defn
async def get_topic_bounds_for_batch(segment_batch_file_path: FilePathForSegmentBatch) -> list[TopicBoundary]:
    segment_batch = await asyncio.to_thread(read_json, segment_batch_file_path)
    
    # Fetch segments
    pdf_segment_fetch_handles = []
    for segment_id, _ in segment_batch:
        handle = get_record(PDF_SEGMENTS, segment_id)
        pdf_segment_fetch_handles.append(handle)

    pdf_segment_records: list[PdfSegmentsRecord] = await gather(*pdf_segment_fetch_handles)
    pdf_segment_records.sort(key=lambda x: x['segment_index_in_document'])

    # Find topic bounds
    segments_baml = []
    for idx, record in enumerate(pdf_segment_records):
        segments_baml.append(
            types.Segment(
                segment_number=idx,
                segment_text=record['segment_text'],
                segment_type=types.SegmentType(record["segment_type"])
            )
        )

    try:
        topic_bounds = await identify_topic_bounds(segments_baml)
        # Calculate topic bounds with offset using the index of the first segment
        segment_index = pdf_segment_records[0]["segment_index_in_document"]
        return list(map(lambda bound: bound + segment_index, topic_bounds))
    except BamlClientError as e:
        # TODO add more robust default option
        # when API call fails
        return list(map(lambda bound: bound + segment_index, [0, len(segments_baml)]))


@activity.defn
async def get_last_segment_index_of_document(source_pdf_id) -> int:
    pdf_segment_record: PdfSegmentsRecord | None = await get_first_matching_record(PDF_SEGMENTS, options={
        "filter": f"source_pdf='{source_pdf_id}'",
        "fields": "id,segment_index_in_document",
        "sort": "-segment_index_in_document"
    })

    if pdf_segment_record is None:
        raise Exception(f"Couldn't find last segment of document - {source_pdf_id}")
    
    return pdf_segment_record['segment_index_in_document']


@activity.defn
async def reduced_topic_bounds_and_save(topic_bounds_with_pdf_id: TopicBoundsWithSourcePDF):
    all_unique_topic_bounds, source_pdf_id = topic_bounds_with_pdf_id

    pdf_topic_insert_handles = []
    topic_number = 0
    for start_indx, end_indx in zip(all_unique_topic_bounds, all_unique_topic_bounds[1:]):
        topic_record: PdfTopicsRecord = {
            "source_pdf": source_pdf_id,
            "start_indx": start_indx,
            "end_indx": end_indx,
            "topic_number": topic_number
        }  # type: ignore

        handle = save_record(PDF_TOPICS, topic_record)
        pdf_topic_insert_handles.append(handle)
        topic_number += 1

    activity.logger.info(f"Trying to save all topic records - {len(pdf_topic_insert_handles)}")
    await gather(*pdf_topic_insert_handles)

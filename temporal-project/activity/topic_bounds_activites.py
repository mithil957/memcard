from temporalio import activity
from baml_client.config import set_log_level
from baml_client import types
from baml_client.async_client import b

from asyncio.tasks import gather

from database.database_models import (
    PdfSegmentsRecord, PdfTopicsRecord,
    PDF_SEGMENTS, PDF_TOPICS
)

from database.database_utils import (
    get_all_records,
    get_record,
    save_record,
    get_first_matching_record
)

# --- CONFIG ---
set_log_level("OFF")

# --- Helpful Types ---
SegmentId = str
SegmentIndx = int
IsLastSegment = bool
SegmentInfo = tuple[SegmentId, SegmentIndx]
SegmentBatch = list[SegmentInfo]
TopicBoundary = int
TopicBoundsWithSourcePDF = tuple[list[TopicBoundary], str]

# --- Activites ---
@activity.defn
async def construct_segment_batches(source_pdf_id: str) -> list[SegmentBatch]:
    records: list[PdfSegmentsRecord] = await get_all_records(PDF_SEGMENTS, options={
        "filter": f"source_pdf='{source_pdf_id}'",
        "fields": "id,segment_index_in_document",
        "sort": "segment_index_in_document"
    })

    segment_infos: list[SegmentInfo] = [(record['id'], record['segment_index_in_document'])
           for record in records]

    # Turn the ids into batches by sliding over them using a window, (slide by 20 & collect 40)
    batches: list[SegmentBatch] = []
    for i in range(0, len(segment_infos), 20):
        batches.append(segment_infos[i: i+40])

    return batches


@activity.defn
async def get_topic_bounds_for_batch(segment_batch: SegmentBatch) -> list[TopicBoundary]:
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

    topic_bounds = await b.IdentifyMultipleTopicBoundaries(segments_baml)

    # Calculate topic bounds with offset using the index of the first segment
    segment_index = pdf_segment_records[0]["segment_index_in_document"]
    return list(map(lambda bound: bound + segment_index, topic_bounds))


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

    activity.logger.info(
        f"Trying to save all topic records - {len(pdf_topic_insert_handles)}")
    await gather(*pdf_topic_insert_handles)

from temporalio import activity

from baml_client.config import set_log_level
from baml_client import types
from baml_client.async_client import b

from database.database_utils import (
    get_all_records,
    update_record,
    get_first_matching_record
)

from database.database_models import (
    PdfTopicsRecord, PdfSegmentsRecord,
    PDF_TOPICS, PDF_SEGMENTS
)

# ---  CONFIG --- 
set_log_level("OFF")


# --- Activites ---
@activity.defn
async def get_topic_bounds(source_pdf_id: str) -> list[PdfTopicsRecord]:
    records: list[PdfTopicsRecord] = await get_all_records(PDF_TOPICS, options={
        "filter": f"source_pdf='{source_pdf_id}'",
        "sort": "topic_number"
    })

    return records


@activity.defn
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

    base_summary = await b.GenerateTopicSummary(raw_segments_baml)

    # update the topic record with base summary
    record_with_summary: PdfTopicsRecord = {
        "base_summary": base_summary.rstrip('\n') # BAML includes this char after parsing, so need to remove it here
    } # type: ignore

    await update_record(PDF_TOPICS, topic_record['id'], record_with_summary)


@activity.defn
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
    context_summary = await b.GenerateContextualTopicSummary(prev_topic_base_summary, next_topic_base_summary, raw_segments_baml)

    # update the topic record with context summary
    record_with_summary: PdfTopicsRecord = {
        "context_summary": context_summary.rstrip('\n') # Same as earlier comment
    } # type: ignore

    await update_record(PDF_TOPICS, topic_record['id'], record_with_summary)
    
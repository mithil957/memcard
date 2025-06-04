from temporalio import activity

from baml_client.config import set_log_level
from baml_client import types
from baml_client.async_client import b
from prompts.chunks_prompt import CHUNKING_PROMPT

from database.database_utils import (
    get_record,
    get_all_records,
    save_record
)

from database.database_models import (
    PdfSegmentsRecord, PdfChunksRecord,
    PDF_SEGMENTS, PDF_CHUNKS
)

from database.baml_funcs import chunk_segment

# --- CONFIG ---
set_log_level("OFF")

# --- Helpful Types ---
SegmentId = str

# --- Activites ---
@activity.defn
async def fetch_segment_ids(source_pdf_id: str) -> list[SegmentId]:
    records: list[PdfSegmentsRecord] = await get_all_records(PDF_SEGMENTS, options={
        "filter": f"source_pdf='{source_pdf_id}'",
        "fields": "id"
    })
    
    return [record['id'] for record in records]


@activity.defn
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

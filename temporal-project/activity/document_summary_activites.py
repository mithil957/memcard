from temporalio import activity
from baml_client.config import set_log_level
from baml_client import types
from baml_client.async_client import b

from database.database_models import (
    PdfTopicsRecord, PdfSummaryRecord,
    PDF_TOPICS, PDF_SUMMARY
)

from database.database_utils import (
    get_all_records,
    save_record
)

from database.baml_funcs import generate_document_summary

# --- CONFIG ---
set_log_level("OFF")

# --- Activites ---
@activity.defn
async def generate_and_save_document_summary(source_pdf_id: str) -> PdfSummaryRecord:
    records: list[PdfTopicsRecord] = await get_all_records(PDF_TOPICS, options={
        "filter": f"source_pdf='{source_pdf_id}'",
        "sort": "topic_number",
        "fields": "context_summary"
    })

    summaries = [record["context_summary"] for record in records]

    # TODO - should prob improve this part
    if sum(map(lambda x: len(x), summaries)) >= 5 * 1e5:
        document_summary = "Too many tokens to generate a summary for, perform 2nd order summary"
    else:
        try:
            document_summary = await generate_document_summary(summaries)
        except Exception as e:
            document_summary = "Errored out"

    document_summary_record: PdfSummaryRecord = {
        "document_summary": document_summary,
        "source_pdf": source_pdf_id,
    } # type: ignore

    return await save_record(PDF_SUMMARY, document_summary_record)
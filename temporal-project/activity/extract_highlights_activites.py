import fitz
from dataclasses import dataclass
from temporalio import activity
from asyncio.tasks import gather

from database.database_models import (
    PDF_HIGHLIGHTS, USER_PDFS, JOB_REQUESTS,
    UserPdfRecord, PdfHighlightsRecord, JobRequestsRecord
)

from database.database_utils import (
    get_record, 
    construct_file_url, 
    download_file,
    save_record,
    get_all_records,
    get_first_matching_record,
    delete_record
)

# --- Helpful Types ---
UserPdfId = str
UploadedPdfIdAndProcessedPdfId = tuple[UserPdfId, UserPdfId]

@dataclass
class PdfInfo:
    id: str
    pb_filename: str
    original_filename: str

@dataclass
class ExtractedHighlight:
    text: str
    page_number: int



# --- Activites ---
@activity.defn
async def check_if_pdf_already_processed(pdf_record_id: str) -> UserPdfId | None:
    user_pdf_record: UserPdfRecord = await get_record(USER_PDFS, pdf_record_id)
    file_name_when_uploaded = user_pdf_record['original_filename']

    matching_records: list[UserPdfRecord] = await get_all_records(USER_PDFS, options={
        'filter': f"original_filename='{file_name_when_uploaded}'"
    })

    # We didn't find any other pdfs with the same name
    if len(matching_records) == 0:
        return None
    
    matched_record_ids = [r['id'] for r in matching_records]
    for record_id in matched_record_ids:
        job_request_status = await get_first_matching_record(JOB_REQUESTS, options={
            'filter': f"source_pdf='{record_id}' && status='Finished'"
        })

        # We found a record where a PDF with the same name already had cards generated for it
        if job_request_status is not None:
            # TODO delete duplicate PDF
            return record_id
    
    # We found a matching pdf name but that pdf didn't make it all the way through to card generation
    return None


@activity.defn
async def delete_all_old_highlights(pdf_record_id: str):
    records: list[PdfHighlightsRecord] = await get_all_records(PDF_HIGHLIGHTS, options={
        'filter': f"user_pdf='{pdf_record_id}'",
        'fields': 'id'
    })

    highlight_delete_handles = []
    for r in records:
        handle = delete_record(PDF_HIGHLIGHTS, r['id'])
        highlight_delete_handles.append(handle)
    
    await gather(*highlight_delete_handles)
    

@activity.defn
async def extract_and_save_highlights(pdf_id_pair: UploadedPdfIdAndProcessedPdfId):
    # Will be the same if duplicate wasn't found
    pdf_id_to_extract_from, pdf_id_to_save_on = pdf_id_pair

    if pdf_id_to_extract_from == pdf_id_to_save_on:
        activity.logger.info(f"Unique PDF to extract highlights from - {pdf_id_to_extract_from}")
    else:
        activity.logger.info(f"Extracting from {pdf_id_to_extract_from} and saving highlights on {pdf_id_to_save_on}")

    # Fetch record
    record: UserPdfRecord = await get_record(USER_PDFS, pdf_id_to_extract_from)
    activity.logger.info(f"PDF file record: {record}")

    # Fetch file URL
    file_url = construct_file_url(record, record['pdf_document'])
    activity.logger.info(f"Requesting PDF from URL: {file_url}")

    # Download file
    pdf_bytes = await download_file(file_url)
    activity.logger.info(f"Downloaded {file_url} ~ {len(pdf_bytes) / 1e6} MB")

    # Convert to PDF and extract highlights
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    highlights = []

    for page_num in range(doc.page_count):
        page = doc[page_num]
        annots = page.annots()

        if annots:
            for annot in annots:
                if annot.type[0] == 8: # Highlight annotation type
                    highlight_text = page.get_textbox(annot.rect)
                    if len(highlight_text.strip()) != 0:
                        highlights.append(ExtractedHighlight(highlight_text.strip(), page_num))

    # Save highlights
    if len(highlights) == 0:
        try:
            saved_record: PdfHighlightsRecord = await save_record(PDF_HIGHLIGHTS, {
                "user_pdf": pdf_id_to_save_on,
                "text": "N/A",
                "page_number": 0
            })
            activity.logger.info(f"No highlights to save for PDF record ID: {saved_record['id']}")
        except Exception as e:
            activity.logger.error(f"Error saving EMPTY highlight - {pdf_id_to_save_on} - {e}")


    for highlight in highlights:
        try:
            saved_record: PdfHighlightsRecord = await save_record(PDF_HIGHLIGHTS, {
                "user_pdf": pdf_id_to_save_on,
                "text": highlight.text,
                "page_number": highlight.page_number
            })
            activity.logger.info(f"Saved highlight - {saved_record['id']} - {highlight.text[:20]}")
        except Exception as e:
            activity.logger.error(f"Error saving highlight - {pdf_id_to_save_on} - {e}")

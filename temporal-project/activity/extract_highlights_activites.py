import fitz
from dataclasses import dataclass
from temporalio import activity

from database.database_models import (
    UserPdfRecord, 
    USER_PDFS, 
    PDF_HIGHLIGHTS, 
    PdfHighlightsRecord
)

from database.database_utils import (
    get_record, 
    construct_file_url, 
    download_file,
    save_record
)


@dataclass
class PdfInfo:
    id: str
    pb_filename: str
    original_filename: str

@dataclass
class ExtractedHighlight:
    text: str
    page_number: int



@activity.defn
async def extract_and_save_highlights(pdf_record_id: str):
    # Fetch record
    record: UserPdfRecord = await get_record(USER_PDFS, pdf_record_id)
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
                "user_pdf": pdf_record_id,
                "text": "N/A",
                "page_number": 0
            })
            activity.logger.info(f"No highlights to save for PDF record ID: {saved_record['id']}")
        except Exception as e:
            activity.logger.error(f"Error saving EMPTY highlight - {pdf_record_id} - {e}")


    for highlight in highlights:
        try:
            saved_record: PdfHighlightsRecord = await save_record(PDF_HIGHLIGHTS, {
                "user_pdf": pdf_record_id,
                "text": highlight.text,
                "page_number": highlight.page_number
            })
            activity.logger.info(f"Saved highlight - {saved_record['id']} - {highlight.text[:20]}")
        except Exception as e:
            activity.logger.error(f"Error saving highlight - {pdf_record_id} - {e}")

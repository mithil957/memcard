from typing import TypedDict, Any

# --- QDRANT ---
VECTORS_FOR_PB_DATA = "chunk_summary_context_vectors"

class VectorMetadata(TypedDict):
    source_pdf: str
    chunk_id: str
    segment_id: str
    topic_id: str
    chunk_index_in_segment: int
    segment_index_in_document: int
    topic_number: int
    summary_text: str
    chunk_text: str
    segment_type: str

# --- POCKETBASE ---
USER_PDFS = "user_pdfs"

class UserPdfRecord(TypedDict):
    id: str
    created: str
    updated: str
    file_size: int
    original_filename: str
    pdf_document: str
    user: str


PDF_HIGHLIGHTS = "pdf_highlights"

class PdfHighlightsRecord(TypedDict):
    id: str
    text: str
    user_pdf: str
    page_number: int
    created: str
    updated: str


JOB_REQUESTS = "job_requests"

class JobRequestsRecord(TypedDict):
    id: str
    user: str
    source_pdf: str
    status: str
    created: str
    updated: str

PDF_SEGMENTS = "pdf_segments"

class PdfSegmentsRecord(TypedDict):
    id: str
    source_pdf: str
    segment_text: str
    segment_type: str
    segment_index_in_document: int
    page_range: float
    created: str
    updated: str

PDF_CHUNKS = "pdf_chunks"

class PdfChunksRecord(TypedDict):
    id: str
    segment: str
    source_pdf: str
    chunk_index_in_segment: int
    chunk_text: str
    created: str
    updated: str

PDF_TOPICS = "pdf_topics"

class PdfTopicsRecord(TypedDict):
    id: str
    source_pdf: str
    topic_number: int
    start_indx: int
    end_indx: int
    base_summary: str
    context_summary: str
    created: str
    updated: str

PDF_SUMMARY = "pdf_summary"

class PdfSummaryRecord(TypedDict):
    id: str
    source_pdf: str
    document_summary: str
    created: str
    updated: str


FLASHCARDS_STORE = "flashcards_store"

class FlashcardsStoreRecord(TypedDict):
    id: str
    front: str
    back: str
    card_type: str
    source_job: str
    source_pdf: str
    user_id: str
    rating: str
    comments_by_user: str
    context_generated_from: dict[str, Any]
    created: str
    updated: str
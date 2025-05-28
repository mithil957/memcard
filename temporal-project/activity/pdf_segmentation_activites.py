import base64
import fitz
from temporalio import activity
from PIL import Image as PILImage
import io
import datetime
import os
import asyncio

from baml_client.config import set_log_level
from baml_client.async_client import types, b
from baml_py import Image as BamlImage

from database.database_utils import (
    get_record,
    construct_file_url,
    download_file,
    save_record
)

from utils import (
    save_json,
    read_json,
    remove_file
)

from database.database_models import (
    PdfSegmentsRecord, UserPdfRecord, JobRequestsRecord,
    JOB_REQUESTS, PDF_SEGMENTS,  USER_PDFS)

# --- CONFIG ---
set_log_level("OFF")

# --- HELPFUL TYPES ---
ImageStr = str
ImageStrWithPageRange = tuple[ImageStr, float]
ImageStrWithPageRangeFilePath = str

SegmentsWithPageRange = tuple[list[types.Segment], float]
SegmentsWithPageRangeFilePath = str

JobRecordWithSegmentFilePaths = tuple[JobRequestsRecord,
                                      list[SegmentsWithPageRangeFilePath]]


# --- HELPER FUNCTIONS ---
def get_page_image_from_pdf(document: fitz.Document, page_idx: int) -> ImageStr:
    page = document.load_page(page_idx)
    pix = page.get_pixmap()  # type: ignore
    img_bytes = pix.tobytes("png")
    base64_encoded_string = base64.b64encode(img_bytes).decode('utf-8')
    return base64_encoded_string


def combine_page_images(img_str_left: str, img_str_right: str) -> ImageStr:
    img_strs = [img_str_left, img_str_right]
    img_bytes = [base64.b64decode(img_str) for img_str in img_strs]
    img1, img2 = [PILImage.open(io.BytesIO(img_byte)).convert('RGB')
                  for img_byte in img_bytes]

    max_width = max(img1.width, img2.width)
    total_height = img1.height + img2.height
    combined_img = PILImage.new(
        'RGB', (max_width, total_height), color='white')
    combined_img.paste(img1, (0, 0))
    combined_img.paste(img2, (0, img1.height))

    buffer = io.BytesIO()
    combined_img.save(buffer, format="PNG")
    buffer.seek(0)

    combined_bytes = buffer.getvalue()
    combined_base64 = base64.b64encode(combined_bytes).decode('utf-8')

    return combined_base64


def recreate_file_path(file_type_prefix: str, segment_record: PdfSegmentsRecord, job_record: JobRequestsRecord) -> str:
    job_id = job_record['id']
    page_range = "_".join(str(segment_record['page_range']).split("."))
    print(f"job id - {job_id}")
    print(f"page range - {page_range}")

    return f"/tmp/{job_id}/{file_type_prefix}_{page_range}.json"


# --- Activites ---
@activity.defn
async def fetch_job_record(job_record_id: str) -> JobRequestsRecord:
    # Fetch record
    job_raw_record: JobRequestsRecord = await get_record(JOB_REQUESTS, job_record_id)

    if 'created' in job_raw_record and isinstance(job_raw_record['created'], datetime.datetime):
        job_raw_record['created'] = job_raw_record['created'].isoformat()

    if 'updated' in job_raw_record and isinstance(job_raw_record['updated'], datetime.datetime):
        job_raw_record['updated'] = job_raw_record['updated'].isoformat()

    return job_raw_record


@activity.defn
async def fetch_pdf_and_split_into_image_strs(job_record: JobRequestsRecord) -> list[ImageStrWithPageRangeFilePath]:
    pdf_record: UserPdfRecord = await get_record(USER_PDFS, job_record['source_pdf'])

    # Fetch file URL
    file_url = construct_file_url(pdf_record, pdf_record['pdf_document'])

    # Download file
    pdf_bytes = await download_file(file_url)

    # Turn to PDF
    document = fitz.open(stream=pdf_bytes, filetype="pdf")

    # Split into image strings and save them
    image_str_paths: list[ImageStrWithPageRangeFilePath] = []

    base_job_temp_dir = f"/tmp/{job_record['id']}"
    await asyncio.to_thread(os.makedirs, base_job_temp_dir, exist_ok=True)

    num_pages = document.page_count

    for page_indx in range(0, num_pages, 2):
        curr_page_idx, next_page_idx = page_indx, page_indx + 1
        page_img_curr = get_page_image_from_pdf(document, curr_page_idx)
        page_img_next = get_page_image_from_pdf(document, next_page_idx)
        combined_page_image = combine_page_images(page_img_curr, page_img_next)
        filename_suffix = f"page_{curr_page_idx}_{next_page_idx}.json"
        tmp_file_path = os.path.join(base_job_temp_dir, filename_suffix)
        item: ImageStrWithPageRange = (
            combined_page_image, float(f"{curr_page_idx}.{next_page_idx}"))
        await asyncio.to_thread(save_json, tmp_file_path, item)
        image_str_paths.append(tmp_file_path)

    return image_str_paths


@activity.defn
async def get_segments_given_page_image(page_path: ImageStrWithPageRangeFilePath) -> SegmentsWithPageRangeFilePath:
    page_path_head = "/".join(page_path.split('/')[:-1])
    curr_page_idx, next_page_idx = page_path[:-5].split('/')[-1].split('_')[1:]

    page_content = await asyncio.to_thread(read_json, page_path)
    page: ImageStrWithPageRange = tuple(page_content)
    
    segments = await b.SegmentPageImage(BamlImage.from_base64("image/png", page[0]))
    
    tmp_file_path: SegmentsWithPageRangeFilePath = f"{page_path_head}/segment_{curr_page_idx}_{next_page_idx}.json"
    item = (
        [segment.model_dump() for segment in segments],
        float(f"{curr_page_idx}.{next_page_idx}")
    )

    await asyncio.to_thread(save_json, tmp_file_path, item)
    return tmp_file_path


@activity.defn
async def save_segments_to_db(job_record_with_segment_paths: JobRecordWithSegmentFilePaths):
    job_record, segment_file_paths = job_record_with_segment_paths
    pdf_id = job_record['source_pdf']

    segments_per_page: list[SegmentsWithPageRange] = []

    for file_path in segment_file_paths:
        loaded_data_raw = tuple(await asyncio.to_thread(read_json, file_path))
        loaded_segment_dicts: list[dict] = loaded_data_raw[0]
        page_range: float = loaded_data_raw[1]

        loaded_segments: list[types.Segment] = []
        for seg_dict in loaded_segment_dicts:
            loaded_segments.append(types.Segment(**seg_dict))

        segments_per_page.append((loaded_segments, page_range))

    segments_per_page.sort(key=lambda x: x[1])  # sort by page range
    segment_indx = 0

    for segment_page in segments_per_page:
        segments, page_range = segment_page

        for segment in segments:
            segment_record: PdfSegmentsRecord = {
                "id": None,
                "created": None,
                "updated": None,
                "segment_text": segment.segment_text,
                "segment_type": segment.segment_type,
                "page_range": page_range,
                "segment_index_in_document": segment_indx,
                "source_pdf": pdf_id
            } # type: ignore

            try:
                # save to DB
                record: PdfSegmentsRecord = await save_record(PDF_SEGMENTS, segment_record)
                activity.logger.info(f"Saved segment - {record['id']}")

                # delete from temp storage
                img_page_file_path = recreate_file_path("page", segment_record, job_record)
                segment_file_path = recreate_file_path("segment", segment_record, job_record)
                await asyncio.to_thread(remove_file, img_page_file_path)
                await asyncio.to_thread(remove_file, segment_file_path)

            except Exception as e:
                activity.logger.error(
                    f"Error processing segment - {segment_record} - {job_record['id']} - {e}")
                
            finally:
                segment_indx += 1

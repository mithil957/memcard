import pytest
import os
from temporalio.testing import ActivityEnvironment
from activity.pdf_segmentation_activites import (
    fetch_job_record,
    fetch_pdf_and_split_into_image_strs,
    get_segments_given_page_image,
    save_segments_to_db,
)
from asyncio.tasks import gather
from database.database_utils import get_all_records, delete_record

from database.database_models import PDF_SEGMENTS, PdfSegmentsRecord
from tests.test_setup_cleanup_fixture import (
    run_around_tests
)

@pytest.mark.asyncio
async def test_segmentation_activites(run_around_tests):
    env = ActivityEnvironment()
    job_record = await env.run(fetch_job_record, "6q744g5gnpji19l")
    assert job_record['id'] == "6q744g5gnpji19l"
    assert job_record['source_pdf'] == "5u67g97440v3x03"

    img_strs_file_paths = await env.run(fetch_pdf_and_split_into_image_strs, job_record)
    assert len(img_strs_file_paths) == 14

    segments_generate_handles = []
    for img_file_path in img_strs_file_paths:
        handle = env.run(get_segments_given_page_image, img_file_path)
        segments_generate_handles.append(handle)
    
    segment_file_paths = await gather(*segments_generate_handles)
    assert len(segment_file_paths) != 0

    await env.run(save_segments_to_db, (job_record, segment_file_paths))

    records: list[PdfSegmentsRecord] = await get_all_records(PDF_SEGMENTS, options={
        "filter": f"source_pdf='{job_record['source_pdf']}'"
    })
    assert records != 0

    files = os.listdir(f"/tmp/{job_record['id']}")
    assert 'page_0_1.json' not in files
    assert 'page_2_3.json' not in files
    assert 'segment_0_1.json' not in files
    assert 'segment_2_3.json' not in files

import pytest
from temporalio.testing import ActivityEnvironment
from activity.topic_bounds_activites import (
    fetch_segment_info_and_save_batch,
    get_topic_bounds_for_batch,
    get_last_segment_index_of_document,
    reduced_topic_bounds_and_save,
    TopicBoundary
)
from tests.test_setup_cleanup_fixture import (
    run_around_tests
)
from database.database_utils import (
    get_record,
    get_all_records
)
from database.database_models import (
    PDF_TOPICS, JOB_REQUESTS, JobRequestsRecord
)
from asyncio.tasks import gather
from functools import reduce


@pytest.mark.asyncio
async def test_topic_bounds_activites(run_around_tests):
    env = ActivityEnvironment()
    job_record: JobRequestsRecord = await get_record(JOB_REQUESTS, "k2j4q17558q9b7d")
    source_pdf_id = job_record['source_pdf']

    segment_info_batch_file_paths = await env.run(fetch_segment_info_and_save_batch, job_record)
    assert len(segment_info_batch_file_paths) != 0

    all_topic_boundaries_found: list[list[TopicBoundary]] = []

    for idx in range(0, len(segment_info_batch_file_paths), 10):
        current_mini_batch = segment_info_batch_file_paths[idx: idx + 10]

        topic_bounds_fetch_handles = []
        for segment_info_batch_path in current_mini_batch:
            handle = env.run(get_topic_bounds_for_batch, segment_info_batch_path)
            topic_bounds_fetch_handles.append(handle)
        
        current_topic_bounds_found: list[list[TopicBoundary]] = await gather(*topic_bounds_fetch_handles)
        all_topic_boundaries_found.extend(current_topic_bounds_found)
        

    last_segment_index = await env.run(get_last_segment_index_of_document, source_pdf_id)
    all_topic_boundaries_found.append([last_segment_index])
    all_topic_boundaries_found.append([0])
    
    reduced_topic_boundaries = sorted(
        reduce(lambda l, r: l | set(r), all_topic_boundaries_found, set()))
    assert len(reduced_topic_boundaries) != 0

    await env.run(reduced_topic_bounds_and_save, (reduced_topic_boundaries, source_pdf_id))

    records = await get_all_records(PDF_TOPICS, options={
        "filter": f"source_pdf='{source_pdf_id}'"
    })

    assert len(records) != 0

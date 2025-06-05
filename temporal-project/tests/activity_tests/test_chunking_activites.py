import pytest
from temporalio.testing import ActivityEnvironment
from activity.segment_chunking_activites import (
    fetch_segment_ids_and_save_batch,
    fetch_segment_batch_and_chunk,
)
from database.database_models import (
    PDF_CHUNKS, JOB_REQUESTS, JobRequestsRecord
)
from database.database_utils import (
    get_all_records,
    get_record
)
from asyncio.tasks import gather
from tests.test_setup_cleanup_fixture import (
    run_around_tests
)


@pytest.mark.asyncio
async def test_chunking_activites(run_around_tests):
    env = ActivityEnvironment()
    job_record: JobRequestsRecord = await get_record(JOB_REQUESTS, "k2j4q17558q9b7d")

    segment_batch_file_paths = await env.run(fetch_segment_ids_and_save_batch, job_record)
    assert len(segment_batch_file_paths) != 0

    for segment_batch_path in segment_batch_file_paths:
        segment_ids_for_batch = await env.run(fetch_segment_batch_and_chunk, segment_batch_path)

        for segment_id in segment_ids_for_batch:
            records = await get_all_records(PDF_CHUNKS, options={
                "filter": f"segment='{segment_id}'"
            })
        
            assert len(records) != 0
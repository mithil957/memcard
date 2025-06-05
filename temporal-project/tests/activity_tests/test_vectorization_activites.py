import pytest
from temporalio.testing import ActivityEnvironment
from activity.data_vectorization_activites import (
    fetch_chunk_ids_and_save_batch,
    process_chunk_batch
)
from database.vector_database_utils import (
    perform_vector_search_within_document,
    get_matching_records,
    delete_records_by_id
)

from database.database_models import (
    JOB_REQUESTS, JobRequestsRecord
)
from database.database_utils import get_record
from asyncio.tasks import gather
from tests.test_setup_cleanup_fixture import (
    run_around_tests
)
from database.database_models import VECTORS_FOR_PB_DATA

@pytest.mark.asyncio
async def test_data_vectorization_activites(run_around_tests):
    env = ActivityEnvironment()
    job_record: JobRequestsRecord = await get_record(JOB_REQUESTS, "k2j4q17558q9b7d")
    chunk_batch_file_paths = await env.run(fetch_chunk_ids_and_save_batch, job_record)

    for chunk_bath_path in chunk_batch_file_paths:
        await env.run(process_chunk_batch, chunk_bath_path)

    matches = await perform_vector_search_within_document(VECTORS_FOR_PB_DATA, "optimization", job_record['source_pdf'])
    assert len(matches) != 0


@pytest.mark.asyncio
async def test_clean_all_vectors_for_source_pdf(run_around_tests):
    job_record: JobRequestsRecord = await get_record(JOB_REQUESTS, "k2j4q17558q9b7d")
    source_pdf_id = job_record['source_pdf']

    records = await get_matching_records(VECTORS_FOR_PB_DATA, 
                                         'source_pdf', 
                                         source_pdf_id, limit=1000)
    assert len(records) != 0

    record_ids = [r.id for r in records]
    await delete_records_by_id(VECTORS_FOR_PB_DATA, record_ids)

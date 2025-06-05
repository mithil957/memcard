import pytest
from temporalio.testing import ActivityEnvironment
from activity.topic_summaries_activites import (
    fetch_topic_bounds_and_save_batch,
    fetch_topic_records_batch_and_generate_base_summaries,
    fetch_topic_records_batch_and_generate_context_summaries
)

from tests.test_setup_cleanup_fixture import (
    run_around_tests
)
from database.database_utils import (
    get_record,
    get_first_matching_record
)
from database.database_models import (
    PDF_TOPICS, PdfTopicsRecord,
    JOB_REQUESTS, JobRequestsRecord
)
from asyncio.tasks import gather

@pytest.mark.asyncio
async def test_topic_summaries_activities(run_around_tests):
    env = ActivityEnvironment()
    job_record: JobRequestsRecord = await get_record(JOB_REQUESTS, "k2j4q17558q9b7d")

    topic_records_batch_paths = await env.run(fetch_topic_bounds_and_save_batch, job_record)
    assert len(topic_records_batch_paths) != 0

    for topic_record_batch_path in topic_records_batch_paths:
        await env.run(fetch_topic_records_batch_and_generate_base_summaries, topic_record_batch_path)
    

    first_topic: PdfTopicsRecord | None = await get_first_matching_record(PDF_TOPICS, options={
        'filter': f"source_pdf='{job_record['source_pdf']}'"
    })

    assert first_topic is not None

    fetched_record: PdfTopicsRecord = await get_record(PDF_TOPICS, first_topic['id'])
    assert len(fetched_record['base_summary']) != 0

    for topic_record_batch_path in topic_records_batch_paths:
        await env.run(fetch_topic_records_batch_and_generate_context_summaries, topic_record_batch_path)

    fetched_record: PdfTopicsRecord = await get_record(PDF_TOPICS, first_topic['id'])
    assert len(fetched_record['context_summary']) != 0

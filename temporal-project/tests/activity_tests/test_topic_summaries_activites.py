import pytest
from temporalio.testing import ActivityEnvironment
from activity.topic_summaries_activites import (
    get_topic_bounds,
    generate_and_save_base_summary,
    generate_and_save_context_summary
)

from tests.test_setup_cleanup_fixture import (
    run_around_tests
)
from database.database_utils import (
    get_record
)
from database.database_models import (
    PDF_TOPICS, PdfTopicsRecord
)
from asyncio.tasks import gather

@pytest.mark.asyncio
async def test_topic_summaries_activities(run_around_tests):
    env = ActivityEnvironment()
    source_pdf_id = "5u67g97440v3x03"
    pdf_topic_records = await env.run(get_topic_bounds, source_pdf_id)
    assert len(pdf_topic_records) != 0

    base_summary_update_handles = []
    for topic_record in pdf_topic_records:
        handle = env.run(generate_and_save_base_summary, topic_record)
        base_summary_update_handles.append(handle)
    
    await gather(*base_summary_update_handles)

    first_topic = pdf_topic_records[0]
    fetched_record: PdfTopicsRecord = await get_record(PDF_TOPICS, first_topic['id'])
    assert len(fetched_record['base_summary']) != 0

    context_summary_update_handles = []
    for topic_record in pdf_topic_records:
        handle = env.run(generate_and_save_context_summary, topic_record)
        context_summary_update_handles.append(handle)
    
    await gather(*context_summary_update_handles)

    fetched_record: PdfTopicsRecord = await get_record(PDF_TOPICS, first_topic['id'])
    assert len(fetched_record['context_summary']) != 0

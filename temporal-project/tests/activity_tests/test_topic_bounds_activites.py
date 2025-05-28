import pytest
from temporalio.testing import ActivityEnvironment
from activity.topic_bounds_activites import (
    construct_segment_batches,
    get_topic_bounds_for_batch,
    get_last_segment_index_of_document,
    reduced_topic_bounds_and_save
)
from tests.test_setup_cleanup_fixture import (
    run_around_tests
)
from database.database_utils import (
    get_all_records
)
from database.database_models import (
    PDF_TOPICS
)
from asyncio.tasks import gather
from functools import reduce


@pytest.mark.asyncio
async def test_topic_bounds_activites(run_around_tests):
    env = ActivityEnvironment()
    source_pdf_id = "5u67g97440v3x03"
    segment_batches = await env.run(construct_segment_batches, source_pdf_id)
    assert len(segment_batches) != 0

    topic_bounds_fetch_handles = []
    for segment_batch in segment_batches:
        handle = env.run(get_topic_bounds_for_batch, segment_batch)
        topic_bounds_fetch_handles.append(handle)

    all_topic_boundaries_found = await gather(*topic_bounds_fetch_handles)

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

import pytest
from temporalio.testing import ActivityEnvironment
from activity.segment_chunking_activites import (
    fetch_segment_ids,
    chunk_segment_and_save
)
from database.database_models import PDF_CHUNKS
from database.database_utils import (
    get_all_records
)
from asyncio.tasks import gather
from tests.test_setup_cleanup_fixture import (
    run_around_tests
)


@pytest.mark.asyncio
async def test_chunking_activites(run_around_tests):
    env = ActivityEnvironment()
    segment_ids = await env.run(fetch_segment_ids, "5u67g97440v3x03")
    assert len(segment_ids) != 0

    handles = []
    for segment_id in segment_ids:
        handle = env.run(chunk_segment_and_save, segment_id)
        handles.append(handle)
    
    await gather(*handles)

    for segment_id in segment_ids:
        records = await get_all_records(PDF_CHUNKS, options={
            "filter": f"segment='{segment_id}'"
        })
    
        assert len(records) != 0

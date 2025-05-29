import pytest
from temporalio.testing import ActivityEnvironment
from activity.data_vectorization_activites import (
    get_chunk_id_batches,
    construct_context_vector_and_save
)
from database.vector_database_utils import perform_vector_search_within_document
from asyncio.tasks import gather
from tests.test_setup_cleanup_fixture import (
    run_around_tests
)
from database.database_models import VECTORS_FOR_PB_DATA

@pytest.mark.asyncio
async def test_data_vectorization_activites(run_around_tests):
    env = ActivityEnvironment()
    source_pdf_id = "5u67g97440v3x03"
    chunk_batches = await env.run(get_chunk_id_batches, source_pdf_id)

    context_vector_insert_handles = []
    for chunk_batch in chunk_batches:
        handle = env.run(construct_context_vector_and_save, chunk_batch)
        context_vector_insert_handles.append(handle)
    
    await gather(*context_vector_insert_handles)

    matches = await perform_vector_search_within_document(VECTORS_FOR_PB_DATA, "optimization", source_pdf_id)
    assert len(matches) != 0
    
    

import pytest
from temporalio.testing import ActivityEnvironment
from activity.generate_cards_activities import (
    get_all_highlights,
    get_matches_for_highlight,
    transform_matches_into_groups,
    generate_and_save_flashcards_from_group,
    MetadataWithHighlight
)

from database.database_utils import (
    get_all_records
)

from database.database_models import (
    FLASHCARDS_STORE, FlashcardsStoreRecord
)

from asyncio.tasks import gather
from tests.test_setup_cleanup_fixture import (
    run_around_tests
)

@pytest.mark.asyncio
async def test_generate_flashcards_activites(run_around_tests):
    env = ActivityEnvironment()
    job_record_id = "626f77kbu519vqw"
    source_pdf_id = "5u67g97440v3x03"
    user_id = "3xcovqmh35qgsb0"

    highlights = await env.run(get_all_highlights, source_pdf_id)
    assert len(highlights) != 0

    highlight_vector_fetch_handles = []
    for highlight in highlights:
        handle = env.run(get_matches_for_highlight, highlight)
        highlight_vector_fetch_handles.append(handle)
    
    all_matches: list[list[MetadataWithHighlight]] = await gather(*highlight_vector_fetch_handles)

    assert len(all_matches) != 0

    groups = transform_matches_into_groups(all_matches)
    assert len(groups) != 0

    flashcard_generate_handles = []
    for g in groups:
        handle = env.run(generate_and_save_flashcards_from_group, ((job_record_id, source_pdf_id, user_id), g))
        flashcard_generate_handles.append(handle)
    
    await gather(*flashcard_generate_handles)

    flashcards: list[FlashcardsStoreRecord] = await get_all_records(FLASHCARDS_STORE, options={
        'filter': f"source_pdf='{source_pdf_id}'"
    })
    assert len(flashcards) != 0


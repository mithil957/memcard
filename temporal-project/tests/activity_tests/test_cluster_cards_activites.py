import pytest
from temporalio.testing import ActivityEnvironment
from activity.cluster_cards_activites import (
    cluster_generated_cards
)

from database.database_utils import (
    get_all_records
)

from database.database_models import (
    FLASHCARDS_STORE, FlashcardsStoreRecord
)

from tests.test_setup_cleanup_fixture import (
    run_around_tests
)


@pytest.mark.asyncio
async def test_cluster_flashcards_activites(run_around_tests):
    env = ActivityEnvironment()
    source_job_id = "79zx252cp28ns63"
    source_pdf_id = "3z77342vg53fa64"
    user_id = "p02e2u60814c59s"

    await env.run(cluster_generated_cards, (source_job_id, source_pdf_id, user_id))

    flashcards: list[FlashcardsStoreRecord] = await get_all_records(FLASHCARDS_STORE, options={
        'filter': f"""
            source_job='{source_job_id}' &&
            source_pdf='{source_pdf_id}' &&
            user_id='{user_id}'
        """
    })

    # Check that we have more than one cluster created
    assert len(set(map(lambda x: x['cluster_label'], flashcards))) != 1

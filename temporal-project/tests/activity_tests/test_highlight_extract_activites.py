import pytest
from temporalio.testing import ActivityEnvironment
from database.database_utils import get_all_records
from database.database_models import PDF_HIGHLIGHTS, PdfHighlightsRecord
from activity.extract_highlights_activites import extract_and_save_highlights

from tests.test_setup_cleanup_fixture import (
    run_around_tests
)

@pytest.mark.asyncio
async def test_highlight_extraction_activites(run_around_tests):
    env = ActivityEnvironment()
    source_pdf_id = "5u67g97440v3x03"
    await env.run(extract_and_save_highlights, (source_pdf_id, source_pdf_id))

    highlights: list[PdfHighlightsRecord] = await get_all_records(PDF_HIGHLIGHTS, options={
        'filter': f"user_pdf='{source_pdf_id}'"
    })

    assert len(highlights) != 0


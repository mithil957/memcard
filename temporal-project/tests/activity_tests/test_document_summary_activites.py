import pytest
from temporalio.testing import ActivityEnvironment
from activity.document_summary_activites import (
    generate_and_save_document_summary
)

from tests.test_setup_cleanup_fixture import (
    run_around_tests
)

from database.database_utils import (
    get_record
)

from database.database_models import (
    PDF_SUMMARY, PdfSummaryRecord
)

@pytest.mark.asyncio
async def test_document_summary_activites(run_around_tests):
    env = ActivityEnvironment()
    source_pdf_id = "5u67g97440v3x03"
    saved_record: PdfSummaryRecord = await env.run(generate_and_save_document_summary, source_pdf_id)
    assert saved_record is not None
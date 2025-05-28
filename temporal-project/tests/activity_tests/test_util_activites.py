import pytest
from temporalio.testing import ActivityEnvironment

from activity.util_activites import (
    set_job_request_status
)

from database.database_utils import (
    get_record
)

from database.database_models import (
    JOB_REQUESTS, JobRequestsRecord
)

@pytest.mark.asyncio
async def test_set_job_status():
    env = ActivityEnvironment()
    job_record_id = "626f77kbu519vqw"
    await env.run(set_job_request_status, (job_record_id, "Highlight Extraction"))

    record: JobRequestsRecord = await get_record(JOB_REQUESTS, job_record_id)
    assert record['status'] == "Highlight Extraction"
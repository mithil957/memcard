from temporalio import activity

from database.database_utils import (
    get_record, 
    update_record
)

from database.database_models import (
    JOB_REQUESTS, JobRequestsRecord
)

from typing import Literal

# --- Helpful Types ---
JobRequestStates = Literal["Queued", 
                           "Highlight Extraction", 
                           "Segmentation", 
                           "Chunking", "Topic Bounds",
                           "Topic Summaries", "Document Summary",
                           "Vectors", 
                           "Flashcards Generated", "Flashcards Clustered",
                           "Finished", "Error",
                           ]

JobRecordWithStatus = tuple[str, JobRequestStates]

# --- Activites ---
@activity.defn
async def set_job_request_status(record_with_status: JobRecordWithStatus):
    job_record_id, status = record_with_status
    
    await update_record(JOB_REQUESTS, job_record_id, {
        "status": status
    })


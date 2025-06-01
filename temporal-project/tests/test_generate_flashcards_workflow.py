import pytest

from temporalio.worker import Worker
from temporalio.testing import WorkflowEnvironment

from activity.util_activites import (
    set_job_request_status
)

from activity.extract_highlights_activites import (
    check_if_pdf_already_processed,
    delete_all_old_highlights,
    extract_and_save_highlights
)

from activity.pdf_segmentation_activites import (
    fetch_job_record,
    fetch_pdf_and_split_into_image_strs,
    get_segments_given_page_image,
    save_segments_to_db,
)
from activity.segment_chunking_activites import (
    fetch_segment_ids,
    chunk_segment_and_save
)

from activity.topic_bounds_activites import (
    construct_segment_batches,
    get_topic_bounds_for_batch,
    get_last_segment_index_of_document,
    reduced_topic_bounds_and_save,
)

from activity.topic_summaries_activites import (
    get_topic_bounds,
    generate_and_save_base_summary,
    generate_and_save_context_summary
)

from activity.document_summary_activites import (
    generate_and_save_document_summary
)

from activity.data_vectorization_activites import (
    get_chunk_id_batches,
    construct_context_vector_and_save
)

from activity.generate_cards_activities import (
    get_all_highlights,
    get_matches_for_highlight,
    generate_and_save_flashcards_from_group
)

from activity.cluster_cards_activites import (
    cluster_generated_cards
)

from workflows.generate_flashcards import GenerateFlashcardsWorkflow
from workflows.generate_flashcards import GenerateFlashcardsParameters


@pytest.mark.asyncio
async def test_generate_flashcards_workflow():
    task_queue_name = "test-queue"

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=task_queue_name,
            workflows=[GenerateFlashcardsWorkflow],
            activities=[
                # Utils
                set_job_request_status,
                # Highlights
                check_if_pdf_already_processed,
                delete_all_old_highlights,
                extract_and_save_highlights,
                # Segmentation
                fetch_job_record,
                fetch_pdf_and_split_into_image_strs,
                get_segments_given_page_image,
                save_segments_to_db,
                # Chunking
                fetch_segment_ids,
                chunk_segment_and_save,
                # Topic bounds
                construct_segment_batches,
                get_topic_bounds_for_batch,
                get_last_segment_index_of_document,
                reduced_topic_bounds_and_save,
                # Topic summaries
                get_topic_bounds,
                generate_and_save_base_summary,
                generate_and_save_context_summary,
                # Document summaries
                generate_and_save_document_summary,
                # Vectorization
                get_chunk_id_batches,
                construct_context_vector_and_save,
                # Flashcard generation
                get_all_highlights,
                get_matches_for_highlight,
                generate_and_save_flashcards_from_group,
                # Flashcard clustering
                cluster_generated_cards
            ],
        ):
            job_record_id = "6q744g5gnpji19l"
            await env.client.execute_workflow(
                GenerateFlashcardsWorkflow.run,
                GenerateFlashcardsParameters(job_record_id=job_record_id),
                id="test-generate-flashcards",
                task_queue=task_queue_name
            )

            # files = os.listdir(f"/tmp/{job_record_id}")
            # assert len(files) == 0

            # job_record: JobRequestsRecord = await get_record(JOB_REQUESTS, job_record_id)
            # records: list[PdfSegmentsRecord] = await get_all_records(JOB_REQUESTS, options={
            #     "filter": f"source_pdf='{job_record['source_pdf']}'"
            # })
            # assert records != 0

            # # TEST CLEAN UP
            # for record in records:
            #     await delete_record(PDF_SEGMENTS, record["id"])

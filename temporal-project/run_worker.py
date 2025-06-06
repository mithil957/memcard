import concurrent.futures
import aiohttp
import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

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
    fetch_segment_ids_and_save_batch,
    fetch_segment_batch_and_chunk,
)

from activity.topic_bounds_activites import (
    fetch_segment_info_and_save_batch,
    get_topic_bounds_for_batch,
    get_last_segment_index_of_document,
    reduced_topic_bounds_and_save,
)

from activity.topic_summaries_activites import (
    fetch_topic_bounds_and_save_batch,
    fetch_topic_records_batch_and_generate_base_summaries,
    fetch_topic_records_batch_and_generate_context_summaries
)

from activity.document_summary_activites import (
    generate_and_save_document_summary
)

from activity.data_vectorization_activites import (
    fetch_chunk_ids_and_save_batch,
    process_chunk_batch
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

import logging
import os


async def main():
    temporal_url = os.getenv("TEMPORAL_SERVER_URL", "localhost:7233")
    max_retries = 10
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            client = await Client.connect(temporal_url, namespace="default")
            print("Successfully connected to Temporal service.")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                print(f"Error occurred - {e}")
                raise

    async with aiohttp.ClientSession() as session:
        worker = Worker(
            client,
            task_queue="general-work-queue",
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
                fetch_segment_ids_and_save_batch,
                fetch_segment_batch_and_chunk,
                # Topic bounds
                fetch_segment_info_and_save_batch,
                get_topic_bounds_for_batch,
                get_last_segment_index_of_document,
                reduced_topic_bounds_and_save,
                # Topic summaries
                fetch_topic_bounds_and_save_batch,
                fetch_topic_records_batch_and_generate_base_summaries,
                fetch_topic_records_batch_and_generate_context_summaries,
                # Document summaries
                generate_and_save_document_summary,
                # Vectorization
                fetch_chunk_ids_and_save_batch,
                process_chunk_batch,
                # Flashcard generation
                get_all_highlights,
                get_matches_for_highlight,
                generate_and_save_flashcards_from_group,
                # Flashcard Clustering
                cluster_generated_cards
            ]
        )
        print("Starting the worker...")
        await worker.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

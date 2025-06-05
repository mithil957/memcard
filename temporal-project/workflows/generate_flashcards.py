from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from dataclasses import dataclass
from asyncio.tasks import gather
from functools import reduce


with workflow.unsafe.imports_passed_through():
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
        SegmentsWithPageRangeFilePath
    )

    from activity.segment_chunking_activites import (
        fetch_segment_ids_and_save_batch,
        fetch_segment_batch_and_chunk
    )

    from activity.topic_bounds_activites import (
        fetch_segment_info_and_save_batch,
        get_topic_bounds_for_batch,
        get_last_segment_index_of_document,
        reduced_topic_bounds_and_save,
        TopicBoundary
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
        transform_matches_into_groups,
        generate_and_save_flashcards_from_group
    )

    from activity.cluster_cards_activites import (
        cluster_generated_cards
    )

    from activity.util_activites import (
        set_job_request_status
    )


@dataclass
class GenerateFlashcardsParameters:
    job_record_id: str


@workflow.defn
class GenerateFlashcardsWorkflow:
    @workflow.run
    async def run(self, job_parameters: GenerateFlashcardsParameters) -> str:
        workflow.logger.info(
            f"Starting generate flashcards job for {job_parameters.job_record_id}")

        short_timeout = timedelta(seconds=30)
        medium_timeout = timedelta(minutes=5)
        long_timeout = timedelta(minutes=15)

        few_shot = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=100),
            maximum_attempts=3
        )

        job_record = await workflow.start_activity(
            fetch_job_record,
            job_parameters.job_record_id,
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        # Check if duplicate
        processed_pdf_id = await workflow.start_activity(
            check_if_pdf_already_processed,
            job_record['source_pdf'],
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        # We found an already processed PDF for we can use all previously constructed segments, chunks, topics, vectors
        if processed_pdf_id is not None:
            workflow.logger.info(
                f"Duplicate PDF found - {job_parameters.job_record_id} - {processed_pdf_id}")
            workflow.logger.info(
                f"Flashcard generation starts - {job_parameters.job_record_id}")
            await workflow.start_activity(
                delete_all_old_highlights,
                processed_pdf_id,
                start_to_close_timeout=long_timeout,
                retry_policy=few_shot
            )

            await workflow.start_activity(
                extract_and_save_highlights,
                (job_record['source_pdf'], processed_pdf_id),
                start_to_close_timeout=long_timeout,
                retry_policy=few_shot
            )

            await workflow.start_activity(
                set_job_request_status,
                (job_record['id'], "Highlight Extraction"),
                start_to_close_timeout=long_timeout,
                retry_policy=few_shot
            )

            highlights = await workflow.start_activity(
                get_all_highlights,
                processed_pdf_id,
                schedule_to_close_timeout=long_timeout,
                retry_policy=few_shot
            )

            if len(highlights) == 0:
                await workflow.start_activity(
                    set_job_request_status,
                    (job_record['id'], "Finished"),
                    start_to_close_timeout=long_timeout,
                    retry_policy=few_shot
                )
            
                return "Workflow done - Skipped flashcard generation because no highlights found"

            highlight_vector_fetch_handles = []

            for highlight in highlights:
                handle = workflow.start_activity(
                    get_matches_for_highlight,
                    (highlight, processed_pdf_id),
                    schedule_to_close_timeout=long_timeout,
                    retry_policy=few_shot
                )
                highlight_vector_fetch_handles.append(handle)

            all_matches = await gather(*highlight_vector_fetch_handles)

            groups = transform_matches_into_groups(all_matches)

            flashcard_generate_handles = []
            for selected_group in groups:
                handle = workflow.start_activity(
                    generate_and_save_flashcards_from_group,
                    (
                        # Here we can save the flashcards with the new PDF id
                        (job_record['id'], job_record['source_pdf'], job_record['user']),
                        selected_group
                    ),
                    start_to_close_timeout=long_timeout,
                    retry_policy=few_shot
                )
                flashcard_generate_handles.append(handle)

            await gather(*flashcard_generate_handles)

            await workflow.start_activity(
                set_job_request_status,
                (job_record['id'], "Flashcards Generated"),
                start_to_close_timeout=long_timeout,
                retry_policy=few_shot
            )

            await workflow.start_activity(
                cluster_generated_cards,
                (job_record['id'], job_record['source_pdf'],
                 job_record['user']),
                start_to_close_timeout=long_timeout,
                retry_policy=few_shot
            )

            await workflow.start_activity(
                set_job_request_status,
                (job_record['id'], "Flashcards Clustered"),
                start_to_close_timeout=long_timeout,
                retry_policy=few_shot
            )

            await workflow.start_activity(
                set_job_request_status,
                (job_record['id'], "Finished"),
                start_to_close_timeout=long_timeout,
                retry_policy=few_shot
            )

            return "Workflow done - Skipped steps because duplicate found"

        # Extract and save highlights of the PDF
        await workflow.start_activity(
            extract_and_save_highlights,
            (job_record['source_pdf'], job_record['source_pdf']),
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        await workflow.start_activity(
            set_job_request_status,
            (job_record['id'], "Highlight Extraction"),
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        image_str_file_paths = await workflow.start_activity(
            fetch_pdf_and_split_into_image_strs,
            job_record,
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        segments_handles = []
        for page_path in image_str_file_paths:
            handle = workflow.start_activity(
                get_segments_given_page_image,
                page_path,
                start_to_close_timeout=long_timeout,
                retry_policy=few_shot
            )
            segments_handles.append(handle)

        segment_file_paths: list[SegmentsWithPageRangeFilePath] = await gather(*segments_handles)

        await workflow.start_activity(
            save_segments_to_db,
            (job_record, segment_file_paths),
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        await workflow.start_activity(
            set_job_request_status,
            (job_record['id'], "Segmentation"),
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        workflow.logger.info(
            f"Segmentation completed - {job_parameters.job_record_id}")
        workflow.logger.info(
            f"Chunking started - {job_parameters.job_record_id}")

        segment_batch_file_paths = await workflow.start_activity(
            fetch_segment_ids_and_save_batch,
            job_record,
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        for segment_batch_path in segment_batch_file_paths:
            # Fetch the ids for that batch and process in one go
            _ = await workflow.start_activity(
                fetch_segment_batch_and_chunk,
                segment_batch_path,
                start_to_close_timeout=long_timeout,
                retry_policy=few_shot
            )

        await workflow.start_activity(
            set_job_request_status,
            (job_record['id'], "Chunking"),
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        workflow.logger.info(
            f"Chunking completed - {job_parameters.job_record_id}")
        workflow.logger.info(
            f"Topic bounds started - {job_parameters.job_record_id}")

        segment_info_batch_file_paths = await workflow.start_activity(
            fetch_segment_info_and_save_batch,
            job_record,
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        topic_boundaries_found: list[list[TopicBoundary]] = []

        for idx in range(0, len(segment_info_batch_file_paths), 10):
            current_mini_batch = segment_info_batch_file_paths[idx: idx + 10]

            topic_bounds_fetch_handles = []
            for segment_info_batch_path in current_mini_batch:
                handle = workflow.start_activity(
                    get_topic_bounds_for_batch,
                    segment_info_batch_path,
                    start_to_close_timeout=long_timeout,
                    retry_policy=few_shot
                )
                topic_bounds_fetch_handles.append(handle)
            
            current_topic_bounds_found: list[list[TopicBoundary]] = await gather(*topic_bounds_fetch_handles)
            topic_boundaries_found.extend(current_topic_bounds_found)

        last_segment_index = await workflow.start_activity(
            get_last_segment_index_of_document,
            job_record['source_pdf'],
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        topic_boundaries_found.append([last_segment_index])
        topic_boundaries_found.append([0])

        topic_boundaries_reduced: list[TopicBoundary] = sorted(
            reduce(lambda l, r: l | set(r), topic_boundaries_found, set()))
        await workflow.start_activity(
            reduced_topic_bounds_and_save,
            (topic_boundaries_reduced, job_record['source_pdf']),
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        await workflow.start_activity(
            set_job_request_status,
            (job_record['id'], "Topic Bounds"),
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        workflow.logger.info(
            f"Topic bounds finished - {job_parameters.job_record_id}")
        workflow.logger.info(
            f"Topic summaries start - {job_parameters.job_record_id}"
        )

        topic_records_batch_paths = await workflow.start_activity(
            fetch_topic_bounds_and_save_batch,
            job_record,
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )
        
        workflow.logger.info(
            f"Topic summaries - fetched all topic records - {job_parameters.job_record_id}"
        )

        for topic_record_batch_path in topic_records_batch_paths:
            await workflow.start_activity(
                fetch_topic_records_batch_and_generate_base_summaries,
                topic_record_batch_path,
                start_to_close_timeout=long_timeout,
                retry_policy=few_shot
            )

        workflow.logger.info(
            f"Topic summaries - updated base summary - {job_parameters.job_record_id}"
        )

        for topic_record_batch_path in topic_records_batch_paths:
            await workflow.start_activity(
                fetch_topic_records_batch_and_generate_context_summaries,
                topic_record_batch_path,
                start_to_close_timeout=long_timeout,
                retry_policy=few_shot
            )

        workflow.logger.info(
            f"Topic summaries - updated context summary - {job_parameters.job_record_id}"
        )

        await workflow.start_activity(
            set_job_request_status,
            (job_record['id'], "Topic Summaries"),
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        workflow.logger.info(
            f"Topic summaries finished - {job_parameters.job_record_id}"
        )

        workflow.logger.info(
            f"Document summary started - {job_parameters.job_record_id}"
        )

        document_summary_record = await workflow.start_activity(
            generate_and_save_document_summary,
            job_record['source_pdf'],
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        await workflow.start_activity(
            set_job_request_status,
            (job_record['id'], "Document Summary"),
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        workflow.logger.info(
            f"Document summary finished - {document_summary_record} - {job_parameters.job_record_id}"
        )
        workflow.logger.info(
            f"Vectorization starts - {job_parameters.job_record_id}")

        chunk_batch_file_paths = await workflow.start_activity(
            fetch_chunk_ids_and_save_batch,
            job_record,
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        for chunk_batch_path in chunk_batch_file_paths:
            await workflow.start_activity(
                process_chunk_batch,
                chunk_batch_path,
                start_to_close_timeout=long_timeout,
                retry_policy=few_shot
            )

        await workflow.start_activity(
            set_job_request_status,
            (job_record['id'], "Vectors"),
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        workflow.logger.info(
            f"Vectorization ends - {job_parameters.job_record_id}")
        workflow.logger.info(
            f"Flashcard generation starts - {job_parameters.job_record_id}")

        highlights = await workflow.start_activity(
            get_all_highlights,
            job_record['source_pdf'],
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        if len(highlights) == 0:
            await workflow.start_activity(
                set_job_request_status,
                (job_record['id'], "Finished"),
                start_to_close_timeout=long_timeout,
                retry_policy=few_shot
            )
            
            return "Workflow done - Skipped flashcard generation because no highlights found"
        

        highlight_vector_fetch_handles = []
        for highlight in highlights:
            handle = workflow.start_activity(
                get_matches_for_highlight,
                (highlight, job_record['source_pdf']),
                schedule_to_close_timeout=long_timeout,
                retry_policy=few_shot
            )
            highlight_vector_fetch_handles.append(handle)

        all_matches = await gather(*highlight_vector_fetch_handles)

        groups = transform_matches_into_groups(all_matches)

        flashcard_generate_handles = []
        for selected_group in groups:
            handle = workflow.start_activity(
                generate_and_save_flashcards_from_group,
                (
                    (job_record['id'], job_record['source_pdf'], job_record['user']),
                    selected_group
                ),
                start_to_close_timeout=long_timeout,
                retry_policy=few_shot
            )
            flashcard_generate_handles.append(handle)

        await gather(*flashcard_generate_handles)

        await workflow.start_activity(
            set_job_request_status,
            (job_record['id'], "Flashcards Generated"),
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        workflow.logger.info(
            f"Flashcard generation finished - {job_parameters.job_record_id}")

        await workflow.start_activity(
            cluster_generated_cards,
            (job_record['id'], job_record['source_pdf'], job_record['user']),
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        await workflow.start_activity(
            set_job_request_status,
            (job_record['id'], "Flashcards Clustered"),
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        await workflow.start_activity(
            set_job_request_status,
            (job_record['id'], "Finished"),
            start_to_close_timeout=long_timeout,
            retry_policy=few_shot
        )

        return "Workflow done"

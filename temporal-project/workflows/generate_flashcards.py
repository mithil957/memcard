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
        fetch_segment_ids,
        chunk_segment_and_save
    )

    from activity.topic_bounds_activites import (
        construct_segment_batches,
        get_topic_bounds_for_batch,
        get_last_segment_index_of_document,
        reduced_topic_bounds_and_save,
        TopicBoundary
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
        transform_matches_into_groups,
        generate_and_save_flashcards_from_group
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

        one_shot = RetryPolicy(maximum_attempts=1)
        few_shot = RetryPolicy(maximum_attempts=3)

        job_record = await workflow.start_activity(
            fetch_job_record,
            job_parameters.job_record_id,
            start_to_close_timeout=short_timeout,
            retry_policy=one_shot
        )

        # Check if duplicate
        processed_pdf_id = await workflow.start_activity(
            check_if_pdf_already_processed,
            job_record['source_pdf'],
            start_to_close_timeout=short_timeout,
            retry_policy=one_shot
        )

        if processed_pdf_id is not None:
            workflow.logger.info(f"Duplicate PDF found - {job_parameters.job_record_id} - {processed_pdf_id}")
            workflow.logger.info(f"Flashcard generation starts - {job_parameters.job_record_id}")
            await workflow.start_activity(
                delete_all_old_highlights,
                processed_pdf_id,
                start_to_close_timeout=short_timeout,
                retry_policy=one_shot
            )

            await workflow.start_activity(
                extract_and_save_highlights,
                (job_record['source_pdf'], processed_pdf_id),
                start_to_close_timeout=short_timeout,
                retry_policy=one_shot
            )

            await workflow.start_activity(
                set_job_request_status,
                (job_record['id'], "Highlight Extraction"),
                start_to_close_timeout=short_timeout,
                retry_policy=one_shot
            )

            highlights = await workflow.start_activity(
                get_all_highlights,
                processed_pdf_id,
                schedule_to_close_timeout=short_timeout,
                retry_policy=few_shot
            )

            highlight_vector_fetch_handles = []
            
            for highlight in highlights:
                handle = workflow.start_activity(
                    get_matches_for_highlight, 
                    highlight,
                    schedule_to_close_timeout=short_timeout,
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
                        (job_record['id'], job_record['source_pdf'], job_record['user']), # Here we can save the flashcards with the new PDF id
                        selected_group
                    ),
                    start_to_close_timeout=medium_timeout,
                    retry_policy=few_shot
                )
                flashcard_generate_handles.append(handle)
            
            await gather(*flashcard_generate_handles) 

            await workflow.start_activity(
                set_job_request_status,
                (job_record['id'], "Finished"),
                start_to_close_timeout=short_timeout,
                retry_policy=one_shot
            )

            return "Workflow done - Skipped steps because duplicate found"


        # Extract and save highlights of the PDF
        await workflow.start_activity(
            extract_and_save_highlights, 
            (job_record['source_pdf'], job_record['source_pdf']),
            start_to_close_timeout=short_timeout,
            retry_policy=one_shot
        )

        await workflow.start_activity(
            set_job_request_status,
            (job_record['id'], "Highlight Extraction"),
            start_to_close_timeout=short_timeout,
            retry_policy=one_shot
        )

        image_str_file_paths = await workflow.start_activity(
            fetch_pdf_and_split_into_image_strs,
            job_record,
            start_to_close_timeout=short_timeout,
            retry_policy=one_shot
        )

        segments_handles = []
        for page_path in image_str_file_paths:
            handle = workflow.start_activity(
                get_segments_given_page_image,
                page_path,
                start_to_close_timeout=short_timeout,
                retry_policy=few_shot
            )
            segments_handles.append(handle)

        segment_file_paths: list[SegmentsWithPageRangeFilePath] = await gather(*segments_handles)

        await workflow.start_activity(
            save_segments_to_db,
            (job_record, segment_file_paths),
            start_to_close_timeout=medium_timeout,
            retry_policy=few_shot
        )

        await workflow.start_activity(
            set_job_request_status,
            (job_record['id'], "Segmentation"),
            start_to_close_timeout=short_timeout,
            retry_policy=one_shot
        )

        workflow.logger.info(
            f"Segmentation completed - {job_parameters.job_record_id}")
        workflow.logger.info(
            f"Chunking started - {job_parameters.job_record_id}")

        segment_ids = await workflow.start_activity(
            fetch_segment_ids,
            job_record['source_pdf'],
            start_to_close_timeout=short_timeout,
            retry_policy=few_shot
        )

        chunking_handles = []
        for segment_id in segment_ids:
            handle = workflow.start_activity(
                chunk_segment_and_save,
                segment_id,
                start_to_close_timeout=medium_timeout,
                retry_policy=few_shot
            )
            chunking_handles.append(handle)

        if chunking_handles:
            await gather(*chunking_handles)

        await workflow.start_activity(
            set_job_request_status,
            (job_record['id'], "Chunking"),
            start_to_close_timeout=short_timeout,
            retry_policy=one_shot
        )

        workflow.logger.info(
            f"Chunking completed - {job_parameters.job_record_id}")
        workflow.logger.info(
            f"Topic bounds started - {job_parameters.job_record_id}")

        segment_batches = await workflow.start_activity(
            construct_segment_batches,
            job_record['source_pdf'],
            start_to_close_timeout=short_timeout,
            retry_policy=few_shot
        )

        topic_bounds_fetch_handles = []
        for segment_batch in segment_batches:
            handle = workflow.start_activity(
                get_topic_bounds_for_batch,
                segment_batch,
                start_to_close_timeout=medium_timeout,
                retry_policy=few_shot
            )
            topic_bounds_fetch_handles.append(handle)

        topic_boundaries_found: list[list[TopicBoundary]] = await gather(*topic_bounds_fetch_handles)
        
        last_segment_index = await workflow.start_activity(
            get_last_segment_index_of_document, 
            job_record['source_pdf'],
            schedule_to_close_timeout=short_timeout,
            retry_policy=few_shot
        )

        topic_boundaries_found.append([last_segment_index])
        topic_boundaries_found.append([0])

        topic_boundaries_reduced: list[TopicBoundary] = sorted(
            reduce(lambda l, r: l | set(r), topic_boundaries_found, set()))
        await workflow.start_activity(
            reduced_topic_bounds_and_save,
            (topic_boundaries_reduced, job_record['source_pdf']),
            schedule_to_close_timeout=medium_timeout,
            retry_policy=few_shot
        )

        await workflow.start_activity(
            set_job_request_status,
            (job_record['id'], "Topic Bounds"),
            start_to_close_timeout=short_timeout,
            retry_policy=one_shot
        )

        workflow.logger.info(
            f"Topic bounds finished - {job_parameters.job_record_id}")
        workflow.logger.info(
            f"Topic summaries start - {job_parameters.job_record_id}"
        )

        pdf_topic_records = await workflow.start_activity(
            get_topic_bounds,
            job_record['source_pdf'],
            schedule_to_close_timeout=short_timeout,
            retry_policy=few_shot
        )
        workflow.logger.info(
            f"Topic summaries - fetched all topic records - {job_parameters.job_record_id}"
        )

        base_summary_update_handles = []
        for topic_record in pdf_topic_records:
            handle = workflow.start_activity(
                generate_and_save_base_summary,
                topic_record,
                schedule_to_close_timeout=short_timeout,
                retry_policy=few_shot
            )
            base_summary_update_handles.append(handle)

        await gather(*base_summary_update_handles)
        workflow.logger.info(
            f"Topic summaries - updated base summary - {job_parameters.job_record_id}"
        )

        context_summary_update_handles = []
        for topic_record in pdf_topic_records:
            handle = workflow.start_activity(
                generate_and_save_context_summary,
                topic_record,
                schedule_to_close_timeout=short_timeout,
                retry_policy=few_shot
            )
            context_summary_update_handles.append(handle)

        await gather(*context_summary_update_handles)

        await workflow.start_activity(
            set_job_request_status,
            (job_record['id'], "Topic Summaries"),
            start_to_close_timeout=short_timeout,
            retry_policy=one_shot
        )

        workflow.logger.info(
            f"Topic summaries - updated context summary - {job_parameters.job_record_id}"
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
            schedule_to_close_timeout=short_timeout,
            retry_policy=few_shot
        )

        await workflow.start_activity(
            set_job_request_status,
            (job_record['id'], "Document Summary"),
            start_to_close_timeout=short_timeout,
            retry_policy=one_shot
        )

        workflow.logger.info(
            f"Document summary finished - {document_summary_record} - {job_parameters.job_record_id}"
        )
        workflow.logger.info(f"Vectorization starts - {job_parameters.job_record_id}")

        chunk_batches = await workflow.start_activity(
            get_chunk_id_batches,
            job_record['source_pdf'],
            schedule_to_close_timeout=short_timeout,
            retry_policy=few_shot
        )

        context_vector_insert_handles = []
        for chunk_batch in chunk_batches:
            handle = workflow.start_activity(
                construct_context_vector_and_save, 
                chunk_batch,
                schedule_to_close_timeout=short_timeout,
                retry_policy=few_shot
            )
            context_vector_insert_handles.append(handle)
        
        await gather(*context_vector_insert_handles)

        await workflow.start_activity(
            set_job_request_status,
            (job_record['id'], "Vectors"),
            start_to_close_timeout=short_timeout,
            retry_policy=one_shot
        )

        workflow.logger.info(f"Vectorization ends - {job_parameters.job_record_id}")
        workflow.logger.info(f"Flashcard generation starts - {job_parameters.job_record_id}")

        highlights = await workflow.start_activity(
            get_all_highlights,
            job_record['source_pdf'],
            schedule_to_close_timeout=short_timeout,
            retry_policy=few_shot
        )

        highlight_vector_fetch_handles = []
        for highlight in highlights:
            handle = workflow.start_activity(
                get_matches_for_highlight, 
                highlight,
                schedule_to_close_timeout=short_timeout,
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
                start_to_close_timeout=medium_timeout,
                retry_policy=few_shot
            )
            flashcard_generate_handles.append(handle)
        
        await gather(*flashcard_generate_handles) 

        await workflow.start_activity(
            set_job_request_status,
            (job_record['id'], "Finished"),
            start_to_close_timeout=short_timeout,
            retry_policy=one_shot
        )

        workflow.logger.info(f"Flashcard generation finished - {job_parameters.job_record_id}")
        return "Workflow done"



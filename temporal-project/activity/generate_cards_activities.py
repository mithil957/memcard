from temporalio import activity

from asyncio.tasks import gather
from qdrant_client import models
from functools import reduce

from database.database_utils import (
    get_record,
    get_all_records,
    save_record
)

from database.vector_database_utils import (
    DocumentCoordinate,
    perform_vector_search,
    traverse_document_to_coordinate
)

from database.database_models import (
    VECTORS_FOR_PB_DATA,
    VectorMetadata,
    FLASHCARDS_STORE, PDF_HIGHLIGHTS,
    FlashcardsStoreRecord, PdfHighlightsRecord
)

from baml_client.config import set_log_level
from baml_client.async_client import types, b

# --- CONFIG ---
set_log_level("OFF")


# --- Helpful Types ---
HighlightRecordId = str
Highlight = str


class MetadataWithHighlight(VectorMetadata):
    highlight_text: str


SourceJobId = str
SourcePdfId = str
UserId = str
RelatedIdsWithGroup = tuple[tuple[SourceJobId,
                                  SourcePdfId, UserId], list[MetadataWithHighlight]]

# --- Helpful Functions ---


def flatten_match_results_for_all_highlights(l: list[MetadataWithHighlight],
                                             r: list[MetadataWithHighlight]) -> list[MetadataWithHighlight]:
    l.extend(r)
    return l


def append_or_new_group(l: tuple[int, int, list[list[MetadataWithHighlight]]],
                        r: MetadataWithHighlight) -> tuple[int, int, list[list[MetadataWithHighlight]]]:
    # we allow adding to a group if the next topic is within 1 and if the range of topics in a group is within 3

    last_elem_topic_number, range_of_group, current_grouping = l

    topic_delta = r['topic_number'] - last_elem_topic_number
    if topic_delta <= 1 and (range_of_group + topic_delta) <= 3:
        current_grouping[-1].append(r)
        return (r['topic_number'], range_of_group + topic_delta, current_grouping)
    else:
        current_grouping.append([r])
        return (r['topic_number'], 0, current_grouping)


def group_by_topic(l: tuple[int, list[list[VectorMetadata]]],
                   r: VectorMetadata) -> tuple[int, list[list[VectorMetadata]]]:
    last_topic_number, groups = l
    if r['topic_number'] == last_topic_number:
        groups[-1].append(r)
    else:
        groups.append([r])

    return (r['topic_number'], groups)


def transform_matches_into_groups(matches_for_highlights: list[list[MetadataWithHighlight]]) -> list[list[MetadataWithHighlight]]:
    flattend_matches = reduce(
        flatten_match_results_for_all_highlights, matches_for_highlights, [])

    flattend_matches.sort(key=lambda x: DocumentCoordinate(
        x['segment_index_in_document'],
        x['chunk_index_in_segment'])
    )
    _, _, groups = reduce(append_or_new_group, flattend_matches, (-10, 0, []))

    return groups


async def map_from_context_topic(context_topic: list[VectorMetadata]) -> types.TopicSummaryWithSegments:
    if len(context_topic) == 0:
        raise Exception("got empty context topic")

    topic_summary = context_topic[0]['summary_text']
    segments_checked = set()
    segments = []
    for c in context_topic:
        segment_id = c['segment_id']
        if segment_id not in segments_checked:
            record = await get_record("pdf_segments", segment_id)
            segments.append(types.SegmentRaw(
                segment_type=record['segment_type'], segment_text=record['segment_text']))
            segments_checked.add(segment_id)

    return types.TopicSummaryWithSegments(topicSummary=topic_summary, segments=segments)


# --- Activites ---
@activity.defn
async def get_all_highlights(source_pdf_id: str) -> list[Highlight]:
    records: list[PdfHighlightsRecord] = await get_all_records(PDF_HIGHLIGHTS, options={
        'filter': f"user_pdf='{source_pdf_id}'",
        'fields': 'id,text'
    })

    return [record['text'] for record in records]


@activity.defn
async def get_matches_for_highlight(highlight: Highlight) -> list[MetadataWithHighlight]:
    points = await perform_vector_search(VECTORS_FOR_PB_DATA, highlight, limit=4)
    return list(map(
        lambda p: {**p.payload, **{"highlight_text": highlight}}, # type: ignore
        points
    ))


@activity.defn
async def generate_and_save_flashcards_from_group(group_data: RelatedIdsWithGroup):
    related_ids, selected_group = group_data
    source_job_id, source_pdf_id, user_id = related_ids

    # Establish starting point
    first_chunk_in_group = selected_group[0]
    starting_coord = DocumentCoordinate(
        first_chunk_in_group['segment_index_in_document'], 0)

    # Establish ending point
    last_chunk_in_group = selected_group[-1]
    ending_coord = DocumentCoordinate(
        last_chunk_in_group['segment_index_in_document'] + 1, 0)

    # Walk through the document
    document_walk_for_group = await traverse_document_to_coordinate(
        source_pdf=selected_group[0]['source_pdf'],
        start=starting_coord,
        end=ending_coord
    )

    # Make sure that we only have full segments, so we drop the dangling chunk
    last_elem_in_walk = document_walk_for_group[-1]
    coord_of_last_elem = DocumentCoordinate(
        last_elem_in_walk['segment_index_in_document'], last_elem_in_walk['chunk_index_in_segment'])

    if len(document_walk_for_group) != 0 and coord_of_last_elem == ending_coord:
        document_walk_for_group.pop()

    # Generate flashcards
    _, context_topics = reduce(
        group_by_topic, document_walk_for_group, (-10, []))
    topic_summaries_with_segments: list[types.TopicSummaryWithSegments] = []

    for ct in context_topics:
        topic_summ_with_segment_baml = await map_from_context_topic(ct)
        topic_summaries_with_segments.append(topic_summ_with_segment_baml)

    highlights = list(set(map(lambda x: x['highlight_text'], selected_group)))
    flashcards = await b.GenerateFlashcardsDetailed(types.StudyInput(topics=topic_summaries_with_segments, highlights=highlights))

    # Save to store
    flashcard_save_handle = []
    for card in flashcards:
        record_to_save: FlashcardsStoreRecord = {
            "front": card.front,
            "back": card.back,
            "card_type": card.type.value,
            "source_job": source_job_id,
            "source_pdf": source_pdf_id,
            "user_id": user_id,
            "context_generated_from": {
                "starting_coord": f"{starting_coord.segment_index},{starting_coord.chunk_index}",
                "ending_coord": f"{ending_coord.segment_index},{ending_coord.chunk_index}",
                "highlights": highlights
            }
        }  # type: ignore

        handle = save_record(FLASHCARDS_STORE, record_to_save)
        flashcard_save_handle.append(handle)

    await gather(*flashcard_save_handle)

from functools import reduce
from itertools import groupby
from asyncio.tasks import gather

from database.database_models import (
    VectorMetadata, VECTORS_FOR_PB_DATA,
     PdfSummaryRecord, PDF_SUMMARY,
     PdfSegmentsRecord, PDF_SEGMENTS
)

from database.vector_database_utils import (
    perform_vector_search,
    DocumentCoordinate,
    traverse_document_to_coordinate
)

from database.database_utils import (
    get_record,
    get_first_matching_record
)

from baml_client.async_client import types
from dataclasses import dataclass

# --- Helpful types ---
@dataclass
class TopicSummaryWithSegments:
    topic_summary: str
    segments: list[types.SegmentRaw]

    def to_formatted_string(self) -> str:
        formatted_lines = []
        formatted_lines.append(f"Topic Summary: {self.topic_summary}\n")
        
        for i, segment in enumerate(self.segments):
            segment_header = f"Segment {i+1}"
            segment_header += f" (Type: {segment.segment_type.value})"

            formatted_lines.append(segment_header + ":")
            formatted_lines.append(segment.segment_text.strip())
            if i < len(self.segments) - 1:
                formatted_lines.append("\n")

        formatted_lines.append("---")
        
        return "\n".join(formatted_lines)

SourcePdfId = str
SourcePdfAndCoordinateWithMetadocumentPart = tuple[SourcePdfId, DocumentCoordinate, str]



# --- Helper functions ---
def group_by_source_pdf(l: tuple[str, list[list[VectorMetadata]]],
                        r: VectorMetadata) -> tuple[str, list[list[VectorMetadata]]]:
    last_source_pdf, groups = l
    if r['source_pdf'] == last_source_pdf:
        groups[-1].append(r)
    else:
        groups.append([r])
    
    return (r['source_pdf'], groups)

def group_by_topic(l: tuple[int, list[list[VectorMetadata]]], 
                   r: VectorMetadata) -> tuple[int, list[list[VectorMetadata]]]:
    last_source_pdf, groups = l
    if r['topic_number'] == last_source_pdf:
        groups[-1].append(r)
    else:
        groups.append([r])
    
    return (r['topic_number'], groups)


def append_or_new_group(l: tuple[int, int, list[list[VectorMetadata]]],
                        r: VectorMetadata) -> tuple[int, int, list[list[VectorMetadata]]]:
    # we allow adding to a group if the next topic is within 1 and if the range of topics in a group is within 3

    last_elem_topic_number, range_of_group, current_grouping = l

    topic_delta = r['topic_number'] - last_elem_topic_number
    if topic_delta <= 1 and (range_of_group + topic_delta) <= 3:
        current_grouping[-1].append(r)
        return (r['topic_number'], range_of_group + topic_delta, current_grouping)
    else:
        current_grouping.append([r])
        return (r['topic_number'], 0, current_grouping)
    
    
async def map_from_context_topic(context_topic: list[VectorMetadata]) -> TopicSummaryWithSegments:
    if len(context_topic) == 0:
        raise Exception("got empty context topic")

    topic_summary = context_topic[0]['summary_text']
    segments_checked = set()
    segments = []
    for c in context_topic:
        segment_id = c['segment_id']
        if segment_id not in segments_checked:
            record: PdfSegmentsRecord = await get_record(PDF_SEGMENTS, segment_id)
            segments.append(types.SegmentRaw(
                segment_type=types.SegmentType(record['segment_type']), 
                segment_text=record['segment_text']))
            segments_checked.add(segment_id)

    return TopicSummaryWithSegments(topic_summary=topic_summary, segments=segments)


def construct_topic_range_groups(source_pdf_group: list[VectorMetadata]) -> list[list[VectorMetadata]]:
    # Sort the document group so the matches are in chronological order
    source_pdf_group.sort(key=lambda x: DocumentCoordinate(
        x['segment_index_in_document'],
        x['chunk_index_in_segment'])
    )

    # Form topic groups within the document
    _, _, groups = reduce(append_or_new_group, source_pdf_group, (-10, 0, []))

    return groups


async def generate_metadocument_part(topic_range_group: list[VectorMetadata]) -> SourcePdfAndCoordinateWithMetadocumentPart:
    first_chunk_in_group = topic_range_group[0]
    starting_coord = DocumentCoordinate(first_chunk_in_group['segment_index_in_document'], 0)

    last_chunk_in_group = topic_range_group[-1]
    ending_coord = DocumentCoordinate(last_chunk_in_group['segment_index_in_document'] + 1, 0)

    document_walk_for_group = await traverse_document_to_coordinate(
        source_pdf=topic_range_group[0]['source_pdf'],
        start=starting_coord,
        end=ending_coord
    )

    # Make sure that we only have full segments, so we drop the dangling chunk
    last_elem_in_walk = document_walk_for_group[-1]
    coord_of_last_elem = DocumentCoordinate(
        last_elem_in_walk['segment_index_in_document'], last_elem_in_walk['chunk_index_in_segment'])
    
    if len(document_walk_for_group) != 0 and coord_of_last_elem == ending_coord:
        document_walk_for_group.pop()

    # Construct topic summaries with segments
    _, context_topics = reduce(group_by_topic, document_walk_for_group, (-10, []))
    topic_summaries_with_segments: list[TopicSummaryWithSegments] = []

    for ct in context_topics:
        single_topic_summ_with_segments = await map_from_context_topic(ct)
        topic_summaries_with_segments.append(single_topic_summ_with_segments)
    
    meta_document_part = "\n".join(list(map(lambda elem: elem.to_formatted_string(), topic_summaries_with_segments)))
    return (first_chunk_in_group['source_pdf'], starting_coord, meta_document_part)


# --- Main function ---
async def get_metadocument_for_query(query: str) -> str:
    points = await perform_vector_search(VECTORS_FOR_PB_DATA, query, limit=8)
    points_metadata: list[VectorMetadata] = list(map(lambda p: p.payload, points)) # type: ignore
    
    points_metadata.sort(key=lambda p: p['source_pdf'])

    # Establish groups via source pdf id
    _, groups_by_source_pdf = reduce(group_by_source_pdf, points_metadata, ("", []))

    metadocument_part_construct_handles = []

    for source_pdf_group in groups_by_source_pdf:
        groups_by_topic_range = construct_topic_range_groups(source_pdf_group)
        for topic_range_group in groups_by_topic_range:
            handle = generate_metadocument_part(topic_range_group)
            metadocument_part_construct_handles.append(handle)
    
    # Gather all parts where each elem has a source pdf id, doc coord, and part string
    metadocument_parts: list[SourcePdfAndCoordinateWithMetadocumentPart] = await gather(*metadocument_part_construct_handles)

    # Construct document summary table for all pdfs involved
    document_summary_fetch_handles = []
    for source_pdf_group in groups_by_source_pdf:
        source_pdf_id = source_pdf_group[0]['source_pdf']
        handle = get_first_matching_record(PDF_SUMMARY, options={
            'filter': f"source_pdf='{source_pdf_id}'"
        })
        document_summary_fetch_handles.append(handle)
    
    document_summary_records: list[PdfSummaryRecord] = await gather(*document_summary_fetch_handles)
    document_summary_table = {elem['source_pdf']: elem['document_summary'] for elem in document_summary_records}

    # Construct full metadocument
    metadocument = []
    metadocument_parts.sort(key=lambda part: part[0]) # groupby works on consecutive elements, so sort first then groupby
    part_idx = 1
    total_parts = len(document_summary_table)

    for source_pdf_id, metadocument_source_pdf_group in groupby(metadocument_parts, lambda part: part[0]):
        # Note - metadocument_source_pdf_group is a itertools._grouper object, sorted will cast it to list

        doc_summary = document_summary_table[source_pdf_id]
        metadocument.append(f"# Part {part_idx} of {total_parts}")
        metadocument.append(f"### Related Document Summary")
        metadocument.append(doc_summary.strip())
        metadocument.append("\n")

        metadocument.append("#### Related Topics")
        sorted_metadocument_parts = sorted(metadocument_source_pdf_group, key=lambda part: part[1])
        metadocument_doc_string = "\n".join(list(map(lambda part: part[2], sorted_metadocument_parts)))

        metadocument.append(metadocument_doc_string)
        metadocument.append("\n")

        part_idx += 1
        
    return "\n".join(metadocument)


    









from baml_client.async_client import types, b
from baml_py import Image as BamlImage
from database.tps_utils import rate_limit

@rate_limit("baml", 100)
async def segment_page_image(page_image: BamlImage):
    return await b.SegmentPageImage(page_image)


@rate_limit("baml", 100)
async def chunk_segment(instruction_text: str, 
                        demos: list[types.DemoExampleV2], 
                        input_segment: types.SegmentRaw) -> list[str]:
    return await b.ChunkSegmentV2(instruction_text, demos, input_segment)


@rate_limit("baml", 100)
async def identify_topic_bounds(segments: list[types.Segment]) -> list[int]:
    return await b.IdentifyMultipleTopicBoundaries(segments)


@rate_limit("baml", 100)
async def generate_topic_summary(segments: list[types.SegmentRaw]) -> str:
    return await b.GenerateTopicSummary(segments)


@rate_limit("baml", 100)
async def generate_contextual_topic_summary(prev_summary: str, 
                                            next_summary: str, 
                                            segments: list[types.SegmentRaw]) -> str:
    return await b.GenerateContextualTopicSummary(prev_summary, next_summary, segments)


@rate_limit("baml", 50)
async def generate_document_summary(summaries: list[str]) -> str:
    return await b.GenerateDocumentSummary(summaries)


@rate_limit("baml", 100)
async def generate_flashcards(study_input: types.StudyInput) -> list[types.Flashcard]:
    return await b.GenerateFlashcardsDetailed(study_input)


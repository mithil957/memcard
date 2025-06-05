from config import QDRANT_URL, GEMINI_API_KEY
from database.database_models import VECTORS_FOR_PB_DATA, VectorMetadata
from async_lru import alru_cache
from typing import Literal
from async_lru import alru_cache
from qdrant_client import models, AsyncQdrantClient
import google.genai as genai
from google.genai import types as genai_types
from dataclasses import dataclass
from database.tps_utils import rate_limit
from typing import Any

import asyncio


# --- Helpful Types ---
EmbedType = Literal["RETRIEVAL_QUERY",
                    "RETRIEVAL_DOCUMENT", "CODE_RETRIEVAL_QUERY",
                    "CLUSTERING"]


@dataclass(order=True)
class DocumentCoordinate:
    segment_index: int
    chunk_index: int

    def next_chunk(self) -> 'DocumentCoordinate':
        return DocumentCoordinate(self.segment_index, self.chunk_index + 1)

    def next_segment(self) -> 'DocumentCoordinate':
        return DocumentCoordinate(self.segment_index + 1, 0)


# --- Helpful Functions ---
@alru_cache(maxsize=1)
async def get_qdrant_client() -> AsyncQdrantClient:
    return AsyncQdrantClient(QDRANT_URL)


def _sync_embed_batch(text_lst: list[str], embed_type: EmbedType) -> list[genai_types.ContentEmbedding]:
    client = genai.Client(api_key=GEMINI_API_KEY)

    result = client.models.embed_content(
        model="models/text-embedding-004",
        contents=text_lst,  # type: ignore
        config=genai_types.EmbedContentConfig(task_type=embed_type))

    if result is None or result.embeddings is None:
        raise Exception("Embedding API returned no embeddings")
    return result.embeddings

@rate_limit("embedding", tps=50)
async def text_to_vec(text_lst: list[str], embed_type: EmbedType) -> list[genai_types.ContentEmbedding]:
    embeddings = await asyncio.to_thread(_sync_embed_batch, text_lst, embed_type)
    return embeddings


async def perform_vector_search_within_document(collection_name: str, query_text: str, source_pdf_id: str, limit=7) -> list[models.ScoredPoint]:
    embeddings = await text_to_vec([query_text], "RETRIEVAL_QUERY")
    vec_of_text = embeddings[0].values

    if vec_of_text is None:
        raise Exception(f"Failed to generate vector - {query_text}")

    client = await get_qdrant_client()
    matches = await client.search(
        collection_name=collection_name,
        query_vector=vec_of_text,
        limit=limit,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key='source_pdf',
                    match=models.MatchValue(value=source_pdf_id)
                )
            ]
        ),
        search_params=models.SearchParams(
            quantization=models.QuantizationSearchParams(
                ignore=False,
                rescore=True,
                oversampling=2.0
            )
        )
    )

    return matches


async def perform_vector_search(collection_name: str, query_text: str, limit=20) -> list[models.ScoredPoint]:
    embeddings = await text_to_vec([query_text], "RETRIEVAL_QUERY")
    vec_of_text = embeddings[0].values

    if vec_of_text is None:
        raise Exception(f"Failed to generate vector - {query_text}")

    client = await get_qdrant_client()
    matches = await client.search(
        collection_name=collection_name,
        query_vector=vec_of_text,
        limit=limit,
        search_params=models.SearchParams(
            quantization=models.QuantizationSearchParams(
                ignore=False,
                rescore=True,
                oversampling=2.0
            )
        )
    )

    return matches


async def check_coordinate(source_pdf_id: str, coordinate: DocumentCoordinate) -> VectorMetadata | None:
    client = await get_qdrant_client()
    res = await client.scroll(
        collection_name=VECTORS_FOR_PB_DATA,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="source_pdf", match=models.MatchValue(value=source_pdf_id)),
                models.FieldCondition(key="segment_index_in_document", match=models.MatchValue(
                    value=coordinate.segment_index)),
                models.FieldCondition(key="chunk_index_in_segment", match=models.MatchValue(
                    value=coordinate.chunk_index)),
            ]
        ),
        limit=1,
        with_payload=True,
        with_vectors=False
    )

    elems = res[0]
    if len(elems) == 0:
        return None

    metadata: VectorMetadata = elems[0].payload  # type: ignore
    return metadata


async def traverse_document_from_coordinate(source_pdf: str, start: DocumentCoordinate, max_depth=10) -> list[VectorMetadata]:
    # Check if given coordinate is valid
    metadata = await check_coordinate(source_pdf, start)
    if metadata is None:
        raise Exception(
            f"Invalid starting coordinate - {source_pdf} - {start}")

    current_coordinate = start
    current_depth = 1

    results = [metadata]

    while current_depth < max_depth:
        found_next = False

        for next_coord in [current_coordinate.next_chunk(), current_coordinate.next_segment()]:
            metadata_at_next_coord = await check_coordinate(source_pdf, next_coord)

            if metadata_at_next_coord:
                found_next = True
                results.append(metadata_at_next_coord)
                current_coordinate = next_coord
                current_depth += 1
                break

        if not found_next:
            break

    return results


async def traverse_document_to_coordinate(source_pdf: str, start: DocumentCoordinate, end: DocumentCoordinate, cutoff=100) -> list[VectorMetadata]:
    # Check if given coordinate is valid
    metadata = await check_coordinate(source_pdf, start)
    if metadata is None:
        raise Exception(
            f"Invalid starting coordinate - {source_pdf} - {start}")

    current_coordinate = start
    current_depth = 1

    results = [metadata]

    while current_depth < cutoff and current_coordinate != end:
        found_next = False

        for next_coord in [current_coordinate.next_chunk(), current_coordinate.next_segment()]:
            metadata_at_next_coord = await check_coordinate(source_pdf, next_coord)

            if metadata_at_next_coord:
                found_next = True
                results.append(metadata_at_next_coord)
                current_coordinate = next_coord
                current_depth += 1
                break

        if not found_next:
            break

    if current_depth >= cutoff:
        raise Exception(
            f"Max depth reached without finding coordinate. Last coordinate - {current_coordinate} ")

    return results


async def get_matching_records(collection_name: str, key_name: str, key_value: Any, limit = 200) -> list[models.Record]:
    client = await get_qdrant_client()
    result = await client.scroll(
        collection_name=collection_name,
        scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key=key_name,
                        match=models.MatchValue(value=key_value)
                    )
                ]
            ),
        limit=limit
    )

    records, _ = result
    return records


async def delete_records_by_id(collection_name: str, record_ids: list[Any]):
    client = await get_qdrant_client()
    await client.delete(
        collection_name=collection_name,
            points_selector=models.PointIdsList(
            points=record_ids
        )
    )
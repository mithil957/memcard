import logging
import pytest
from qdrant_client import models
from database.database_utils import (
    get_all_records,
    delete_record
)
from database.database_models import (
    PDF_HIGHLIGHTS, 
    PDF_CHUNKS, PDF_SEGMENTS, PDF_TOPICS, PDF_SUMMARY, 
    FLASHCARDS_STORE,
    VECTORS_FOR_PB_DATA,

)
from database.vector_database_utils import (
    get_qdrant_client
)
from asyncio.tasks import gather

@pytest.fixture(autouse=True)
def run_around_tests():
    logging.basicConfig(level=logging.INFO)
    yield
    logging.info("---- Tests are done ----")


@pytest.mark.asyncio
async def test_delete_all_records():
    collection_names = [
        PDF_CHUNKS, PDF_HIGHLIGHTS, PDF_SEGMENTS, PDF_SUMMARY,
        PDF_TOPICS, FLASHCARDS_STORE
    ]

    for target_collection in collection_names:
        records = await get_all_records(target_collection, options={
            "fields": "id"
        })
        
        record_delete_handles = []
        for record in records:
            handle = delete_record(target_collection, record['id'])
            record_delete_handles.append(handle)
        
        await gather(*record_delete_handles)


@pytest.mark.asyncio
async def test_reset_vector_db():
    client = await get_qdrant_client()

    if await client.collection_exists(collection_name=VECTORS_FOR_PB_DATA):
            return

    await client.create_collection(
        collection_name=VECTORS_FOR_PB_DATA,
        vectors_config=models.VectorParams(
            size=768, distance=models.Distance.DOT),
        quantization_config=models.BinaryQuantization(
            binary=models.BinaryQuantizationConfig(
                always_ram=False,
            ),
        ),
        on_disk_payload=True
    )

    payload_indexes_to_create = [
        ("source_pdf", models.PayloadSchemaType.KEYWORD),
        ("topic_number", models.PayloadSchemaType.INTEGER),
        ("segment_index_in_document", models.PayloadSchemaType.INTEGER),
        ("chunk_index_in_segment", models.PayloadSchemaType.INTEGER)
    ]

    for field_name, field_schema in payload_indexes_to_create:
        await client.create_payload_index(
            collection_name=VECTORS_FOR_PB_DATA,
            field_name=field_name,
            field_schema=field_schema,
        )
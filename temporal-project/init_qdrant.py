import asyncio
from qdrant_client import models

from database.vector_database_utils import get_qdrant_client
from database.database_models import VECTORS_FOR_PB_DATA


async def setup_qdrant():
    print("Starting Qdrant collection setup...")
    client = await get_qdrant_client()
    try:

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

    except Exception as e:
        print(f"An error occured during Qdrant setup: {e}")
        raise
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(setup_qdrant())

import pytest
from actions.generate_meta_document import get_metadocument_for_query

@pytest.mark.asyncio
async def test_get_metadocument_for_query():
    q = "Tell me something interesting"

    metadoc = await get_metadocument_for_query(q)
    assert len(metadoc) != 0
from temporalio import activity
from asyncio.tasks import gather
from sklearn.metrics import pairwise_distances
from sklearn.cluster import AgglomerativeClustering
import numpy as np

from database.database_utils import (
    get_all_records,
    update_record
)

from database.vector_database_utils import (
    text_to_vec
)

from database.database_models import (
    FLASHCARDS_STORE,
    FlashcardsStoreRecord
)

# --- Helpful Types ---
SourceJobId = str
SourcePdfId = str
UserId = str
RelatedIds = tuple[SourceJobId, SourcePdfId, UserId]

BinVecWithId = tuple[np.typing.NDArray, str]

# --- Helpful functions ---
async def card_to_binary_vector_with_record_id(card: FlashcardsStoreRecord) -> BinVecWithId:
    embed_str = f"{card['front']} - {card['back']}"
    embeds = await text_to_vec([embed_str], "CLUSTERING")
    float_vec = np.array(embeds[0].values)
    bin_vec = (float_vec >= 0).astype(int)

    return (bin_vec, card['id'])

# --- Activites ---
@activity.defn
async def cluster_generated_cards(relatedIds: RelatedIds):
    source_job_id, source_pdf_id, user_id = relatedIds

    flashcards: list[FlashcardsStoreRecord] = await get_all_records(FLASHCARDS_STORE, options={
        'filter': f"""
            source_job='{source_job_id}' &&
            source_pdf='{source_pdf_id}' &&
            user_id='{user_id}'
        """
    })

    card_embed_handles = []
    for card in flashcards:
        handle = card_to_binary_vector_with_record_id(card)
        card_embed_handles.append(handle)
    
    bin_vecs_with_ids: list[BinVecWithId] = await gather(*card_embed_handles)
    bin_vecs = np.vstack(list(map(lambda elem: elem[0], bin_vecs_with_ids)))
    hamming_distance_matrix = pairwise_distances(bin_vecs, metric='hamming')

    clusterer = AgglomerativeClustering(
        n_clusters=None, 
        distance_threshold=0.3,
        linkage='complete',
        metric='precomputed'
    )

    clusterer.fit(hamming_distance_matrix)
    labels = clusterer.labels_

    record_ids: list[str] = list(map(lambda elem: elem[1], bin_vecs_with_ids))

    cluster_update_handles = []
    for record_id, cluster_label in zip(record_ids, labels):
        handle = update_record(FLASHCARDS_STORE, record_id, {
            'cluster_label': int(cluster_label)
        })
        cluster_update_handles.append(handle)
    
    await gather(*cluster_update_handles)

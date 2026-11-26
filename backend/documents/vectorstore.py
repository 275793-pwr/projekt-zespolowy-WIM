"""Dostęp do wbudowanej bazy wektorowej Chroma."""
from functools import cache

import chromadb
from django.conf import settings


@cache
def _client(path):
    return chromadb.PersistentClient(path=path)


def collection():
    return _client(settings.CHROMA_PATH).get_or_create_collection("chunks", metadata={"hnsw:space": "cosine"})


def delete_ids(ids):
    if ids:
        collection().delete(ids=list(ids))


def query(vector, k):
    """Zwraca [(chroma_id, podobieństwo)], najlepsze pierwsze. podobieństwo = 1 - odległość kosinusowa."""
    chunks = collection()
    count = chunks.count()
    if count == 0:
        return []
    result = chunks.query(query_embeddings=[vector], n_results=min(k, count))
    return [(chroma_id, 1.0 - distance) for chroma_id, distance in zip(result["ids"][0], result["distances"][0])]

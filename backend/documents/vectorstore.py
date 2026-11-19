import chromadb
from django.conf import settings

_clients = {}


def collection():
    path = settings.CHROMA_PATH
    if path not in _clients:
        _clients[path] = chromadb.PersistentClient(path=path)
    return _clients[path].get_or_create_collection("chunks", metadata={"hnsw:space": "cosine"})


def add(ids, vectors, metadatas, documents):
    collection().add(ids=ids, embeddings=vectors, metadatas=metadatas, documents=documents)


def delete_ids(ids):
    if ids:
        collection().delete(ids=list(ids))


def query(vector, k):
    """Returns [(chroma_id, similarity)], best first. similarity = 1 - cosine distance."""
    col = collection()
    if col.count() == 0:
        return []
    res = col.query(query_embeddings=[vector], n_results=min(k, col.count()))
    return [(i, 1.0 - d) for i, d in zip(res["ids"][0], res["distances"][0])]

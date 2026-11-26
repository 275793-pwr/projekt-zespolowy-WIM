"""Cykl życia dokumentu w indeksie: indeksowanie i usuwanie."""
import logging
import uuid

from django.db import transaction
from pypdf import PdfReader

from llm import client as llm

from . import vectorstore
from .chunking import chunk_pages
from .models import DocumentChunk, DocumentStatus

logger = logging.getLogger(__name__)


class IndexingError(Exception):
    """Komunikat trafia do `Document.failure_reason`."""


def _set_status(document, status, failure_reason=""):
    document.status = status
    document.failure_reason = failure_reason
    document.save(update_fields=["status", "failure_reason", "updated_at"])


def _store_chunks(document, chunks, vectors):
    """Zapisuje fragmenty w SQL i wektory w Chroma; przy błędzie nie zostaje żadne z nich."""
    chroma_ids = [str(uuid.uuid4()) for _ in chunks]
    try:
        with transaction.atomic():
            DocumentChunk.objects.filter(document=document).delete()
            DocumentChunk.objects.bulk_create(
                DocumentChunk(document=document, chroma_id=chroma_id, **chunk)
                for chunk, chroma_id in zip(chunks, chroma_ids)
            )
            vectorstore.collection().add(
                ids=chroma_ids,
                embeddings=vectors,
                metadatas=[{"document_id": str(document.id), "page": chunk["page"]} for chunk in chunks],
                documents=[chunk["text"] for chunk in chunks],
            )
            document.status = DocumentStatus.READY
            document.save(update_fields=["status", "page_count", "updated_at"])
    except Exception as error:
        logger.exception("indexing failed")
        vectorstore.delete_ids(chroma_ids)
        raise IndexingError(f"Błąd zapisu indeksu: {error}") from error


def _build_index(document):
    try:
        pages = [page.extract_text() or "" for page in PdfReader(document.file.path).pages]
    except Exception as error:  # uszkodzony lub zaszyfrowany PDF
        raise IndexingError(f"Nie można odczytać pliku PDF: {error}") from error
    document.page_count = len(pages)

    chunks = chunk_pages(pages)
    if not chunks:
        raise IndexingError("Brak warstwy tekstowej w PDF (prawdopodobnie skan). Wgraj PDF z tekstem lub wykonaj OCR.")

    try:
        vectors = llm.embed([chunk["text"] for chunk in chunks])
    except llm.LLMError as error:
        raise IndexingError(f"Błąd usługi embeddingów: {error}") from error

    _store_chunks(document, chunks, vectors)


def index_document(document):
    """Indeksowanie synchroniczne; później można je opakować w zadanie Celery bez zmian."""
    _set_status(document, DocumentStatus.PROCESSING)
    try:
        _build_index(document)
    except IndexingError as error:
        _set_status(document, DocumentStatus.FAILED, str(error))
    return document


def delete_document(document):
    """Usuwa dokument razem z fragmentami, wektorami w Chroma i plikiem PDF."""
    vectorstore.delete_ids(list(document.chunks.values_list("chroma_id", flat=True)))
    file = document.file
    document.delete()  # fragmenty i cytaty znikają kaskadowo
    if file:
        file.delete(save=False)

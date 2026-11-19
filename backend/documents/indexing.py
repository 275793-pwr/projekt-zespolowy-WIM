import logging
import uuid

from django.db import transaction
from pypdf import PdfReader

from llm import client as llm
from . import vectorstore
from .chunking import chunk_pages
from .models import Document, DocumentChunk, DocumentStatus

log = logging.getLogger(__name__)


def extract_pages(path):
    reader = PdfReader(path)
    return [(p.extract_text() or "") for p in reader.pages]


def _fail(doc, reason):
    doc.status = DocumentStatus.FAILED
    doc.failure_reason = reason
    doc.save(update_fields=["status", "failure_reason", "updated_at"])


def index_document(doc):
    """Synchronous indexing; later it can be wrapped as a Celery task unchanged."""
    doc.status = DocumentStatus.PROCESSING
    doc.failure_reason = ""
    doc.save(update_fields=["status", "failure_reason", "updated_at"])
    try:
        pages = extract_pages(doc.file.path)
    except Exception as e:  # corrupt / encrypted PDF
        _fail(doc, f"Nie można odczytać pliku PDF: {e}")
        return doc
    doc.page_count = len(pages)
    chunks = chunk_pages(pages)
    if not chunks:
        _fail(doc, "Brak warstwy tekstowej w PDF (prawdopodobnie skan). Wgraj PDF z tekstem lub wykonaj OCR.")
        return doc
    try:
        result = llm.embed([c["text"] for c in chunks])
    except llm.LLMError as e:
        _fail(doc, f"Błąd usługi embeddingów: {e}")
        return doc

    ids = [str(uuid.uuid4()) for _ in chunks]
    try:
        with transaction.atomic():
            DocumentChunk.objects.filter(document=doc).delete()
            DocumentChunk.objects.bulk_create(
                [
                    DocumentChunk(document=doc, chunk_index=c["chunk_index"], page=c["page"],
                                  chapter=c["chapter"], text=c["text"], chroma_id=cid)
                    for c, cid in zip(chunks, ids)
                ]
            )
            vectorstore.add(
                ids, result.vectors,
                [{"document_id": str(doc.id), "page": c["page"]} for c in chunks],
                [c["text"] for c in chunks],
            )
            doc.status = DocumentStatus.READY
            doc.save(update_fields=["status", "page_count", "updated_at"])
    except Exception as e:
        log.exception("indexing failed")
        vectorstore.delete_ids(ids)
        _fail(doc, f"Błąd zapisu indeksu: {e}")
    return doc

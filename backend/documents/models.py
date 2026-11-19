import uuid

from django.conf import settings
from django.db import models


class DocumentStatus(models.TextChoices):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="pdfs/")
    status = models.CharField(max_length=12, choices=DocumentStatus.choices, default=DocumentStatus.UPLOADED)
    failure_reason = models.TextField(blank=True, default="")
    page_count = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="documents"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "documents"
        ordering = ["-created_at"]


class DocumentChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.PositiveIntegerField()
    page = models.PositiveIntegerField()
    chapter = models.CharField(max_length=100, blank=True, default="")
    text = models.TextField()
    chroma_id = models.CharField(max_length=64, unique=True)

    class Meta:
        db_table = "document_chunks"
        ordering = ["document", "chunk_index"]
        constraints = [models.UniqueConstraint(fields=["document", "chunk_index"], name="uniq_chunk_index")]

import uuid

from django.conf import settings
from django.db import models

from documents.models import Document, DocumentChunk


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations")
    title = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "conversations"


class MessageRole(models.TextChoices):
    USER = "user"
    ASSISTANT = "assistant"


class AnswerStatus(models.TextChoices):
    ANSWERED = "answered"
    REFUSED = "refused"
    ERROR = "error"


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=MessageRole.choices)
    content = models.TextField()
    status = models.CharField(max_length=10, choices=AnswerStatus.choices, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messages"
        ordering = ["created_at"]


class Citation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="citations")
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    chunk = models.ForeignKey(DocumentChunk, null=True, on_delete=models.SET_NULL)
    position = models.PositiveSmallIntegerField()  # the [n] number shown to the model
    page = models.PositiveIntegerField()
    chapter = models.CharField(max_length=100, blank=True, default="")
    excerpt = models.TextField()
    score = models.FloatField(default=0)

    class Meta:
        db_table = "citations"
        ordering = ["message", "position"]


class MessageFeedback(models.Model):
    """Przygotowane na później (kciuk w górę/w dół); nieużywane w MVP."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="feedback")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.SmallIntegerField()  # 1 / -1
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "message_feedback"


class QueryStatus(models.TextChoices):
    SUCCESS = "success"
    REFUSED = "refused"
    API_ERROR = "api_error"


class QueryLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, null=True, on_delete=models.SET_NULL)
    message = models.ForeignKey(Message, null=True, on_delete=models.SET_NULL)
    model = models.CharField(max_length=100, blank=True, default="")
    tokens_in = models.PositiveIntegerField(default=0)
    tokens_out = models.PositiveIntegerField(default=0)
    latency_ms = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=12, choices=QueryStatus.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "query_logs"

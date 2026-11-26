from django.conf import settings
from rest_framework import serializers

from .models import Document

PDF_MAGIC = b"%PDF-"


class DocumentCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    file = serializers.FileField()

    def validate_file(self, file):
        if file.size > settings.MAX_PDF_BYTES:
            limit_mb = settings.MAX_PDF_BYTES // 1024 // 1024
            raise serializers.ValidationError(f"Plik jest za duży (limit {limit_mb} MB).")
        header = file.read(len(PDF_MAGIC))
        file.seek(0)
        if not file.name.lower().endswith(".pdf") or header != PDF_MAGIC:
            raise serializers.ValidationError("Dozwolone są tylko pliki PDF.")
        return file


class DocumentSerializer(serializers.ModelSerializer):
    chunk_count = serializers.IntegerField(source="chunks.count", read_only=True)

    class Meta:
        model = Document
        fields = ["id", "title", "status", "failure_reason", "page_count", "chunk_count", "created_at"]

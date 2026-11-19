from rest_framework import serializers

from .models import Document


class DocumentCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    file = serializers.FileField()

    def validate_file(self, f):
        from django.conf import settings

        if f.size > settings.MAX_PDF_BYTES:
            raise serializers.ValidationError(f"Plik jest za duży (limit {settings.MAX_PDF_BYTES // 1024 // 1024} MB).")
        head = f.read(5)
        f.seek(0)
        if not f.name.lower().endswith(".pdf") or head != b"%PDF-":
            raise serializers.ValidationError("Dozwolone są tylko pliki PDF.")
        return f


class DocumentSerializer(serializers.ModelSerializer):
    chunk_count = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ["id", "title", "status", "failure_reason", "page_count", "chunk_count", "created_at"]

    def get_chunk_count(self, obj):
        return obj.chunks.count()

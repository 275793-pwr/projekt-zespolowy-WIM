from rest_framework.generics import RetrieveDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCorpusAdmin
from . import vectorstore
from .indexing import index_document
from .models import Document
from .serializers import DocumentCreateSerializer, DocumentSerializer


class DocumentListCreateView(APIView):
    permission_classes = [IsCorpusAdmin]

    def get(self, request):
        return Response(DocumentSerializer(Document.objects.all(), many=True).data)

    def post(self, request):
        ser = DocumentCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        f = ser.validated_data["file"]
        title = ser.validated_data.get("title") or f.name.rsplit(".", 1)[0]
        doc = Document.objects.create(title=title, file=f, uploaded_by=request.user)
        index_document(doc)
        return Response(
            {"id": str(doc.id), "title": doc.title, "status": doc.status, "failure_reason": doc.failure_reason},
            status=201,
        )


class DocumentDetailView(RetrieveDestroyAPIView):
    permission_classes = [IsCorpusAdmin]
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def perform_destroy(self, instance):
        """Usuwa dokument razem z fragmentami, wektorami w Chroma i plikiem PDF."""
        vectorstore.delete_ids(list(instance.chunks.values_list("chroma_id", flat=True)))
        file = instance.file
        instance.delete()  # fragmenty i cytaty znikają kaskadowo
        if file:
            file.delete(save=False)

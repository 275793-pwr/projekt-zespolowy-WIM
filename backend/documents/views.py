from rest_framework import status
from rest_framework.generics import RetrieveDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCorpusAdmin

from .indexing import delete_document, index_document
from .models import Document
from .serializers import DocumentCreateSerializer, DocumentSerializer


class DocumentListCreateView(APIView):
    permission_classes = [IsCorpusAdmin]

    def get(self, request):
        return Response(DocumentSerializer(Document.objects.all(), many=True).data)

    def post(self, request):
        serializer = DocumentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data["file"]
        title = serializer.validated_data.get("title") or file.name.rsplit(".", 1)[0]
        document = Document.objects.create(title=title, file=file, uploaded_by=request.user)
        index_document(document)
        return Response(
            {
                "id": str(document.id),
                "title": document.title,
                "status": document.status,
                "failure_reason": document.failure_reason,
            },
            status=status.HTTP_201_CREATED,
        )


class DocumentDetailView(RetrieveDestroyAPIView):
    permission_classes = [IsCorpusAdmin]
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def perform_destroy(self, instance):
        delete_document(instance)

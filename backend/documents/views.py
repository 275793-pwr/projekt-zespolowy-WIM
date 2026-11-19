from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCorpusAdmin
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


class DocumentDetailView(RetrieveAPIView):
    permission_classes = [IsCorpusAdmin]
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

import logging

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from . import rag

logger = logging.getLogger(__name__)


class AskSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=2000)
    conversation_id = serializers.UUIDField(required=False)


class AskView(APIView):
    def post(self, request):
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            data = rag.ask(
                request.user,
                serializer.validated_data["question"],
                serializer.validated_data.get("conversation_id"),
            )
        except Exception:  # student nigdy nie dostaje 500
            logger.exception("ask failed")
            data = {"message_id": None, "status": "error", "answer": rag.ERROR_TEXT, "sources": []}
        return Response(data)

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from . import rag


class AskSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=2000)
    conversation_id = serializers.UUIDField(required=False)


class AskView(APIView):
    def post(self, request):
        ser = AskSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            data = rag.ask(request.user, ser.validated_data["question"].strip(), ser.validated_data.get("conversation_id"))
        except Exception:  # never a 500 for the student
            import logging

            logging.getLogger(__name__).exception("ask failed")
            data = {"message_id": None, "status": "error", "answer": rag.ERROR_TEXT, "sources": []}
        return Response(data)

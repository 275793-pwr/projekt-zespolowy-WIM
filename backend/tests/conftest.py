import math
import re
import zlib
from pathlib import Path

import pytest
from rest_framework.test import APIClient

from accounts.models import Role, User
from llm import client as llm

SAMPLE_PDF = Path(__file__).resolve().parent.parent / "eval" / "regulamin_studiow.pdf"


def fake_vec(text, dim=256):
    v = [0.0] * dim
    for w in re.findall(r"\w+", text.lower()):
        v[zlib.crc32(w[:5].encode()) % dim] += 1
    n = math.sqrt(sum(x * x for x in v)) or 1
    return [x / n for x in v]


class FakeLLM:
    def __init__(self):
        self.chat_calls = []
        self.embed_calls = []
        self.answer = "Odpowiedź testowa [1]."

    def embed(self, texts, model=None):
        self.embed_calls.append(list(texts))
        return llm.EmbedResult([fake_vec(t) for t in texts], 1, "fake-embed")

    def chat(self, messages, model=None, max_tokens=0):
        self.chat_calls.append(messages)
        return llm.ChatResult(self.answer, 100, 20, "fake-chat")


@pytest.fixture(autouse=True)
def isolated(settings, tmp_path):
    settings.CHROMA_PATH = str(tmp_path / "chroma")
    settings.MEDIA_ROOT = str(tmp_path / "media")
    settings.LLM_RETRY_BACKOFF = 0
    settings.SIMILARITY_THRESHOLD = 0.3


@pytest.fixture
def fake_llm(monkeypatch):
    f = FakeLLM()
    monkeypatch.setattr(llm, "embed", f.embed)
    monkeypatch.setattr(llm, "chat", f.chat)
    return f


def _client(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


@pytest.fixture
def student(db):
    return User.objects.create_user("s@example.com", "pw123456", role=Role.STUDENT)


@pytest.fixture
def admin(db):
    return User.objects.create_user("a@example.com", "pw123456", role=Role.CORPUS_ADMIN)


@pytest.fixture
def student_client(student):
    return _client(student)


@pytest.fixture
def admin_client(admin):
    return _client(admin)


@pytest.fixture
def indexed_doc(admin_client, fake_llm):
    from django.core.files.uploadedfile import SimpleUploadedFile

    r = admin_client.post(
        "/api/documents/",
        {"title": "Regulamin studiów", "file": SimpleUploadedFile("r.pdf", SAMPLE_PDF.read_bytes(), "application/pdf")},
        format="multipart",
    )
    assert r.status_code == 201 and r.json()["status"] == "ready", r.json()
    fake_llm.embed_calls.clear()
    return r.json()["id"]

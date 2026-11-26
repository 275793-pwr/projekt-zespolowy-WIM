"""Jedyny punkt dostępu do dostawcy LLM (czat + embeddingi). Widoki nigdy nie wołają API bezpośrednio."""
import logging
import time
from dataclasses import dataclass

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Zgłaszany po wyczerpaniu ponowień lub przy błędzie, którego nie warto powtarzać."""


@dataclass
class ChatResult:
    text: str
    tokens_in: int
    tokens_out: int
    model: str


class _RetryableError(Exception):
    """Błąd przejściowy: timeout, brak połączenia, 429, 5xx lub niepoprawny JSON."""


def _post_once(url, payload, headers):
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=settings.LLM_TIMEOUT)
    except (requests.Timeout, requests.ConnectionError) as error:
        raise _RetryableError(type(error).__name__) from error
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError as error:
            raise _RetryableError("invalid JSON from provider") from error
    if response.status_code == 429 or response.status_code >= 500:
        raise _RetryableError(f"HTTP {response.status_code}")
    raise LLMError(f"HTTP {response.status_code}: {response.text[:200]}")


def _post(path, payload):
    url = settings.LLM_BASE_URL.rstrip("/") + path
    headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}", "Content-Type": "application/json"}
    attempts = settings.LLM_RETRIES + 1
    try:
        for attempt in range(1, attempts + 1):
            try:
                return _post_once(url, payload, headers)
            except _RetryableError as error:
                if attempt == attempts:
                    raise LLMError(str(error)) from error
                time.sleep(settings.LLM_RETRY_BACKOFF * attempt)
    except LLMError as error:
        logger.warning("LLM call failed: %s", error)
        raise


def chat(messages):
    data = _post(
        "/chat/completions",
        {"model": settings.CHAT_MODEL, "messages": messages, "max_tokens": 1500, "temperature": 0.1},
    )
    try:
        text = (data["choices"][0]["message"].get("content") or "").strip()
    except (KeyError, IndexError, TypeError, AttributeError) as error:
        raise LLMError("unexpected response shape") from error
    if not text:
        raise LLMError("empty answer")
    usage = data.get("usage") or {}
    return ChatResult(
        text=text,
        tokens_in=usage.get("prompt_tokens", 0),
        tokens_out=usage.get("completion_tokens", 0),
        model=data.get("model", settings.CHAT_MODEL),
    )


def embed(texts):
    """Zwraca wektory tekstów; wysyła je partiami, a nie jedno żądanie na tekst."""
    vectors = []
    for offset in range(0, len(texts), settings.EMBED_BATCH_SIZE):
        batch = texts[offset : offset + settings.EMBED_BATCH_SIZE]
        data = _post("/embeddings", {"model": settings.EMBEDDING_MODEL, "input": batch})
        try:
            rows = sorted(data["data"], key=lambda row: row.get("index", 0))
            batch_vectors = [row["embedding"] for row in rows]
        except (KeyError, TypeError) as error:
            raise LLMError("unexpected embeddings response") from error
        if len(batch_vectors) != len(batch):
            raise LLMError("embeddings count mismatch")
        vectors.extend(batch_vectors)
    return vectors

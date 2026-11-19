"""Single entry point for the LLM provider (chat + embeddings). Views never call the API directly."""
import logging
import time
from dataclasses import dataclass

import requests
from django.conf import settings

log = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised after retries are exhausted or on a non-retryable failure."""


@dataclass
class ChatResult:
    text: str
    tokens_in: int
    tokens_out: int
    model: str


@dataclass
class EmbedResult:
    vectors: list
    tokens: int
    model: str


def _post(path, payload):
    url = settings.LLM_BASE_URL.rstrip("/") + path
    headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}", "Content-Type": "application/json"}
    attempts = settings.LLM_RETRIES + 1
    last = "unknown"
    for attempt in range(attempts):
        retryable = True
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=settings.LLM_TIMEOUT)
            if resp.status_code == 200:
                try:
                    return resp.json()
                except ValueError:
                    last = "invalid JSON from provider"
            elif resp.status_code == 429 or resp.status_code >= 500:
                last = f"HTTP {resp.status_code}"
            else:
                retryable = False
                last = f"HTTP {resp.status_code}: {resp.text[:200]}"
        except (requests.Timeout, requests.ConnectionError) as e:
            last = f"{type(e).__name__}"
        if not retryable:
            break
        if attempt < attempts - 1:
            time.sleep(settings.LLM_RETRY_BACKOFF * (attempt + 1))
    log.warning("LLM call failed: %s", last)
    raise LLMError(last)


def chat(messages, model=None, max_tokens=1500):
    model = model or settings.CHAT_MODEL
    data = _post("/chat/completions", {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0.1})
    try:
        text = (data["choices"][0]["message"].get("content") or "").strip()
    except (KeyError, IndexError, TypeError, AttributeError):
        raise LLMError("unexpected response shape")
    if not text:
        raise LLMError("empty answer")
    usage = data.get("usage") or {}
    return ChatResult(text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), data.get("model", model))


def embed(texts, model=None):
    """Embeds texts in batches (not one request per text)."""
    model = model or settings.EMBEDDING_MODEL
    vectors, tokens = [], 0
    size = settings.EMBED_BATCH_SIZE
    for i in range(0, len(texts), size):
        batch = texts[i : i + size]
        data = _post("/embeddings", {"model": model, "input": batch})
        try:
            rows = sorted(data["data"], key=lambda r: r.get("index", 0))
            vecs = [r["embedding"] for r in rows]
        except (KeyError, TypeError):
            raise LLMError("unexpected embeddings response")
        if len(vecs) != len(batch):
            raise LLMError("embeddings count mismatch")
        vectors.extend(vecs)
        tokens += (data.get("usage") or {}).get("prompt_tokens", 0)
    return EmbedResult(vectors, tokens, model)

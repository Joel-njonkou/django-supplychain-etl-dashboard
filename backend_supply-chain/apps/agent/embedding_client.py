import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

from .llm_client import LLMUnavailable

log = logging.getLogger(__name__)
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:batchEmbedContents"
OUTPUT_DIMENSIONALITY = 768


def embed_texts(texts):
    if not settings.RAG_ENABLED:
        raise LLMUnavailable("RAG_API_KEY et RAG_EMBEDDING_MODEL doivent être configurés")
    if not texts:
        return []

    requests = [
        {
            "model": f"models/{settings.RAG_EMBEDDING_MODEL}",
            "content": {"parts": [{"text": text}]},
            "embedContentConfig": {"outputDimensionality": OUTPUT_DIMENSIONALITY},
        }
        for text in texts
    ]
    request = Request(
        API_URL.format(model=settings.RAG_EMBEDDING_MODEL),
        data=json.dumps({"requests": requests}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": settings.RAG_API_KEY,
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=settings.LLM_TIMEOUT_S) as response:
            payload = json.loads(response.read().decode("utf-8"))
        vectors = [item["values"] for item in payload["embeddings"]]
        if len(vectors) != len(texts) or any(len(vector) != OUTPUT_DIMENSIONALITY for vector in vectors):
            raise LLMUnavailable("Réponse Gemini Embeddings de dimensions inattendues")
        return vectors
    except HTTPError as exc:
        log.warning("Gemini Embeddings a retourné HTTP %s", exc.code)
        raise LLMUnavailable(f"Gemini Embeddings HTTP {exc.code}", status_code=exc.code) from exc
    except (URLError, TimeoutError, KeyError, ValueError) as exc:
        log.warning("Appel Gemini Embeddings échoué : %s", type(exc).__name__)
        raise LLMUnavailable("Appel Gemini Embeddings échoué") from exc
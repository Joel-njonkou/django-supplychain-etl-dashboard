import hashlib
import math
import re
import unicodedata

from django.conf import settings
from django.core.cache import cache

from .embedding_client import embed_texts
from .models import KnowledgeChunk

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 160
STOP_WORDS = {
    "avec", "dans", "des", "est", "les", "pour", "qui", "sur", "une", "the",
    "and", "for", "from", "that", "this", "with",
}


def _title(text, fallback):
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()[:250] or fallback
    return fallback[:250]


def chunk_document(text, fallback_title):
    title = _title(text, fallback_title)
    sections = []
    section = title
    lines = []

    def save_section():
        body = "\n".join(lines).strip()
        if body:
            sections.append((section, body))

    for line in text.splitlines():
        if line.startswith("#"):
            save_section()
            section = line.lstrip("# ").strip()[:250] or title
            lines = []
        else:
            lines.append(line)
    save_section()

    chunks = []
    for section_name, body in sections:
        paragraphs = [part.strip().replace("\n", " ") for part in re.split(r"\n\s*\n", body) if part.strip()]
        current = ""
        for paragraph in paragraphs:
            remaining = paragraph
            while remaining:
                separator = "\n\n" if current else ""
                available = CHUNK_SIZE - len(current) - len(separator)
                if len(remaining) <= available:
                    current += separator + remaining
                    break

                if available <= 0:
                    chunks.append((section_name, current))
                    current = current[-CHUNK_OVERLAP:]
                    continue

                boundary = remaining.rfind(" ", 0, available)
                boundary = boundary if boundary > available // 2 else available
                current += separator + remaining[:boundary].strip()
                remaining = remaining[boundary:].strip()
                chunks.append((section_name, current))
                current = current[-CHUNK_OVERLAP:]
        if current:
            chunks.append((section_name, current))

    return title, chunks


def _tokens(text):
    folded = unicodedata.normalize("NFKD", text.casefold())
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    return {token for token in re.findall(r"[a-z0-9]{2,}", folded) if token not in STOP_WORDS}


def _cosine(left, right):
    if not left or len(left) != len(right):
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def _query_embedding(query):
    digest = hashlib.sha256(query.encode("utf-8")).hexdigest()
    key = f"agent:rag:query:{settings.RAG_EMBEDDING_MODEL}:{digest}"
    vector = cache.get(key)
    if vector is None:
        vector = embed_texts([f"task: question answering | query: {query}"])[0]
        cache.set(key, vector, 900)
    return vector


def retrieve(query, top_k=None):
    query = query.strip()
    if not query:
        return {"query": query, "results": []}

    chunks = list(KnowledgeChunk.objects.all())
    if not chunks:
        return {"query": query, "results": [], "message": "Aucun document n'est indexé."}

    query_vector = _query_embedding(query)
    query_tokens = _tokens(query)
    ranked = []
    for chunk in chunks:
        semantic = max(0.0, _cosine(query_vector, chunk.embedding))
        content_tokens = _tokens(chunk.content)
        lexical = (
            len(query_tokens & content_tokens) / math.sqrt(len(query_tokens) * len(content_tokens))
            if query_tokens and content_tokens
            else 0.0
        )
        score = 0.8 * semantic + 0.2 * lexical
        ranked.append((score, chunk))

    limit = max(1, min(int(top_k or settings.RAG_TOP_K), 8))
    ranked.sort(key=lambda item: (-item[0], item[1].source, item[1].chunk_index))
    results = [
        {
            "ref": f"{chunk.source}#chunk-{chunk.chunk_index + 1}",
            "source": chunk.source,
            "title": chunk.title,
            "section": chunk.section,
            "score": round(score, 4),
            "excerpt": chunk.content,
        }
        for score, chunk in ranked[:limit]
        if score >= 0.12
    ]
    return {"query": query, "results": results}
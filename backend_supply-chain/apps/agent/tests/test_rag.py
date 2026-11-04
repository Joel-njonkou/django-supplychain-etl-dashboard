import json
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.test import override_settings

from apps.agent import embedding_client, loop, rag
from apps.agent.management.commands import index_agent_knowledge
from apps.agent.models import KnowledgeChunk


def test_chunk_document_keeps_passages_within_the_limit():
    text = "# Guide\n\n## Délais\n\n" + "retard délai prévu " * 180

    title, chunks = rag.chunk_document(text, "guide")

    assert title == "Guide"
    assert chunks
    assert all(section == "Délais" for section, _ in chunks)
    assert all(len(content) <= rag.CHUNK_SIZE for _, content in chunks)


@pytest.mark.django_db
def test_retrieve_ranked_chunks_returns_citable_references(monkeypatch):
    KnowledgeChunk.objects.create(
        source="knowledge_base/delais.md",
        title="Délais de livraison",
        section="Retards",
        chunk_index=0,
        content="Le retard correspond au dépassement du délai prévu.",
        embedding=[1.0, 0.0],
        content_hash="one",
    )
    KnowledgeChunk.objects.create(
        source="knowledge_base/couts.md",
        title="Coûts estimés",
        section="Méthode",
        chunk_index=0,
        content="Le montant est une estimation de coût logistique.",
        embedding=[0.0, 1.0],
        content_hash="two",
    )
    monkeypatch.setattr(rag, "_query_embedding", lambda query: [1.0, 0.0])

    result = rag.retrieve("retard délai prévu", top_k=1)

    assert result["results"][0]["ref"] == "knowledge_base/delais.md#chunk-1"
    assert result["results"][0]["section"] == "Retards"


@pytest.mark.django_db
def test_index_command_reuses_embeddings_for_unchanged_sources(tmp_path, monkeypatch):
    (tmp_path / "procedure.md").write_text(
        "# Procédure\n\nVérifier le délai prévu avant toute analyse.\n",
        encoding="utf-8",
    )
    embedded_texts = []

    def fake_embed(texts):
        embedded_texts.extend(texts)
        return [[1.0, 0.0] for _ in texts]

    monkeypatch.setattr(index_agent_knowledge, "embed_texts", fake_embed)
    with override_settings(RAG_ENABLED=True, RAG_DOCUMENTS_DIR=str(tmp_path)):
        call_command("index_agent_knowledge", verbosity=0)
        first_embedding_count = len(embedded_texts)
        call_command("index_agent_knowledge", verbosity=0)

    assert first_embedding_count > 0
    assert len(embedded_texts) == first_embedding_count
    assert KnowledgeChunk.objects.filter(source="knowledge_base/procedure.md").exists()


def test_chat_returns_sources_from_retrieval_tool(monkeypatch):
    tool_call = SimpleNamespace(
        id="rag-1",
        function=SimpleNamespace(
            name="search_knowledge",
            arguments='{"query":"délai prévu"}',
        ),
    )
    scripted = iter([
        SimpleNamespace(content="", tool_calls=[tool_call]),
        SimpleNamespace(content="Le guide précise la règle [knowledge_base/delais.md#chunk-1].", tool_calls=None),
    ])
    monkeypatch.setattr(loop, "available_tools", lambda: [])
    monkeypatch.setattr(loop, "execute_tool", lambda *args: {
        "results": [{
            "ref": "knowledge_base/delais.md#chunk-1",
            "source": "knowledge_base/delais.md",
            "title": "Délais",
            "section": "Retards",
            "score": 0.83,
            "excerpt": "Le retard dépasse le délai prévu.",
        }],
    })
    monkeypatch.setattr(loop, "chat", lambda *args, **kwargs: next(scripted))

    result = loop.run_agent([], "Quelle est la règle sur le délai prévu ?")

    assert result["source"] == "llm"
    assert result["sources"][0]["ref"] == "knowledge_base/delais.md#chunk-1"


def test_gemini_embedding_2_uses_native_batch_api_and_secret_header():
    response = BytesIO(json.dumps({
        "embeddings": [{"values": [0.25] * embedding_client.OUTPUT_DIMENSIONALITY}],
    }).encode("utf-8"))
    with override_settings(
        RAG_ENABLED=True,
        RAG_API_KEY="test-secret",
        RAG_EMBEDDING_MODEL="gemini-embedding-2",
        LLM_TIMEOUT_S=10,
    ), patch.object(embedding_client, "urlopen", return_value=response) as urlopen:
        vectors = embedding_client.embed_texts(["title: Guide | text: Délai prévu"])

    request = urlopen.call_args.args[0]
    assert request.full_url == (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-embedding-2:batchEmbedContents"
    )
    assert dict(request.header_items())["X-goog-api-key"] == "test-secret"
    assert "test-secret" not in request.full_url
    body = json.loads(request.data)
    assert body["requests"][0]["model"] == "models/gemini-embedding-2"
    assert body["requests"][0]["content"]["parts"][0]["text"].startswith("title: Guide")
    assert len(vectors[0]) == embedding_client.OUTPUT_DIMENSIONALITY
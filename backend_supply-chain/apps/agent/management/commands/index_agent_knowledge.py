import hashlib
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.agent.embedding_client import embed_texts
from apps.agent.llm_client import LLMUnavailable
from apps.agent.models import KnowledgeChunk
from apps.agent.rag import chunk_document


class Command(BaseCommand):
    help = "Indexe le guide du projet et les documents Markdown/TXT de la base de connaissances."

    def handle(self, *args, **options):
        if not settings.RAG_ENABLED:
            raise CommandError("Configurez LLM_BASE_URL et RAG_EMBEDDING_MODEL avant l'indexation.")

        project_root = settings.BASE_DIR.parent
        knowledge_dir = Path(settings.RAG_DOCUMENTS_DIR)
        documents = []
        guide = project_root / "GUIDE_COMPRENDRE_LE_PROJET.md"
        if guide.is_file():
            documents.append(("GUIDE_COMPRENDRE_LE_PROJET.md", guide))
        if knowledge_dir.is_dir():
            documents.extend(
                (f"knowledge_base/{path.relative_to(knowledge_dir).as_posix()}", path)
                for path in sorted(knowledge_dir.rglob("*"))
                if path.is_file() and path.suffix.lower() in {".md", ".txt"}
            )
        if not documents:
            raise CommandError("Aucun document Markdown ou TXT à indexer.")

        prepared = []
        for source, path in documents:
            text = path.read_text(encoding="utf-8").strip()
            title, chunks = chunk_document(text, path.stem)
            for index, (section, content) in enumerate(chunks):
                prepared.append({
                    "source": source,
                    "title": title,
                    "section": section,
                    "chunk_index": index,
                    "content": content,
                    "content_hash": hashlib.sha256(
                        f"gemini-embedding-v1\0{settings.RAG_EMBEDDING_MODEL}\0{title}\0{content}".encode("utf-8")
                    ).hexdigest(),
                    "embedding_input": f"title: {title} | text: {content}",
                })
        if not prepared:
            raise CommandError("Les documents trouvés ne contiennent aucun passage indexable.")

        sources = {document[0] for document in documents}
        existing = {
            (chunk.source, chunk.chunk_index): chunk
            for chunk in KnowledgeChunk.objects.filter(source__in=sources)
        }
        missing = [
            item for item in prepared
            if (old := existing.get((item["source"], item["chunk_index"]))) is None
            or old.content_hash != item["content_hash"]
        ]

        try:
            vectors = []
            for start in range(0, len(missing), 48):
                vectors.extend(embed_texts([item["embedding_input"] for item in missing[start:start + 48]]))
        except LLMUnavailable as exc:
            raise CommandError(f"Impossible de calculer les embeddings : {exc}") from exc
        if len(vectors) != len(missing):
            raise CommandError("Le fournisseur a retourné un nombre inattendu d'embeddings.")

        vector_by_key = {
            (item["source"], item["chunk_index"]): vector
            for item, vector in zip(missing, vectors)
        }
        rows = []
        for item in prepared:
            key = (item["source"], item["chunk_index"])
            old = existing.get(key)
            vector = vector_by_key.get(key, old.embedding if old else None)
            if vector is None:
                raise CommandError(f"Embedding absent pour {item['source']} (passage {item['chunk_index']}).")
            item.pop("embedding_input")
            rows.append(KnowledgeChunk(**item, embedding=vector))

        with transaction.atomic():
            KnowledgeChunk.objects.all().delete()
            KnowledgeChunk.objects.bulk_create(rows, batch_size=100)

        self.stdout.write(self.style.SUCCESS(
            f"Index RAG mis à jour : {len(documents)} document(s), {len(rows)} passage(s), "
            f"{len(missing)} embedding(s) calculé(s)."
        ))
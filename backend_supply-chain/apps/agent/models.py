from django.db import models


class KnowledgeChunk(models.Model):
	source = models.CharField(max_length=500)
	title = models.CharField(max_length=250)
	section = models.CharField(max_length=250, blank=True)
	chunk_index = models.PositiveIntegerField()
	content = models.TextField()
	embedding = models.JSONField()
	content_hash = models.CharField(max_length=64)
	indexed_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["source", "chunk_index"]
		constraints = [
			models.UniqueConstraint(
				fields=["source", "chunk_index"],
				name="agent_unique_knowledge_chunk",
			),
		]

"""Retrieval: embed query -> vector search -> rerank (US-2).

This is first built as a plain function, then exposed to the agent as the
``search_docs`` tool (US-7). Building it standalone means M1 has a working
retrieve-then-answer chat before the agent exists.

AI-concept note: vector search finds *semantically similar* chunks; the reranker
then re-scores them for *relevance* to the exact query, fixing "similar but not
quite right" hits.
"""

from __future__ import annotations

from .. import providers
from ..repositories import ChunkRepository, SettingsRepository


class Retriever:
    def __init__(self):
        self.embedder = providers.make_embedding_provider()
        self.vectors = providers.make_vector_store()
        self.reranker = providers.make_reranker()
        self.chunks = ChunkRepository()
        self.settings = SettingsRepository()

    def search_docs(self, query: str, k: int | None = None) -> list[dict]:
        cfg = self.settings.get()
        k = k or cfg.top_k
        # Retrieve a few extra candidates so the reranker has room to reorder.
        candidates = self.vectors.search(self.embedder.embed([query])[0], k * 3)
        if not candidates:
            return []
        chunk_map = self.chunks.get_many([cid for cid, _ in candidates])
        items = []
        for chunk_id, score in candidates:
            row = chunk_map.get(chunk_id)
            if not row:
                continue
            items.append(
                {
                    "chunk_id": chunk_id,
                    "document_id": row["document_id"],
                    "title": row["doc_title"],
                    "location": row["location"],
                    "text": row["text"],
                    "score": round(score, 4),
                }
            )
        if cfg.rerank_enabled:
            items = self.reranker.rerank(query, items)
        else:
            for it in items:
                it["rerank_score"] = it["score"]
        return items[:k]

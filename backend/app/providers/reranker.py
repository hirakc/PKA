"""Rerankers: re-score retrieved chunks for true relevance.

AI-concept note (reranking): vector similarity finds passages that are *similar*,
but not always *relevant* to the exact question. A reranker re-scores each
(query, chunk) pair. Production systems use a cross-encoder model; here we use a
lightweight lexical-overlap reranker so it runs offline while teaching the idea.
"""

from __future__ import annotations

import math
import re
from collections import Counter

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


class NoopReranker:
    def rerank(self, query: str, items: list[dict]) -> list[dict]:
        for it in items:
            it["rerank_score"] = it.get("score", 0.0)
        return items


class LexicalReranker:
    """Score by overlap of query terms with the chunk, with a mild length penalty."""

    def rerank(self, query: str, items: list[dict]) -> list[dict]:
        q_terms = Counter(_tokens(query))
        if not q_terms:
            return NoopReranker().rerank(query, items)
        for it in items:
            c_terms = Counter(_tokens(it["text"]))
            overlap = sum(min(q_terms[t], c_terms[t]) for t in q_terms)
            coverage = sum(1 for t in q_terms if c_terms[t] > 0) / len(q_terms)
            length_penalty = 1.0 / (1.0 + math.log(1 + len(c_terms)))
            # Blend lexical relevance with the original vector score.
            it["rerank_score"] = round(
                0.6 * coverage + 0.3 * (overlap * length_penalty) + 0.1 * it.get("score", 0.0),
                4,
            )
        items.sort(key=lambda x: x["rerank_score"], reverse=True)
        return items

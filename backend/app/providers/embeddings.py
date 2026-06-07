"""Embedding providers: turn text into vectors so we can compare *meaning*.

- ``HashingEmbeddingProvider`` is a dependency-free, fully-offline stand-in. It uses
  the hashing trick (bag-of-words hashed into a fixed-size vector) so the whole app
  runs with no API keys. It captures lexical overlap, not deep semantics — good
  enough to *learn* the RAG mechanics.
- ``OpenAIEmbeddingProvider`` swaps in real semantic embeddings when a key is set.
"""

from __future__ import annotations

import hashlib
import math
import re

from .. import config

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


class HashingEmbeddingProvider:
    """Hashing-trick embeddings (offline, deterministic)."""

    def __init__(self, dim: int = 256):
        self.dim = dim

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        tokens = _tokenize(text)
        for tok in tokens:
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]


class OpenAIEmbeddingProvider:
    """Real semantic embeddings via an OpenAI-compatible API."""

    def __init__(self):
        self.dim = 1536
        self.model = config.DEFAULT_SETTINGS.embedding_model
        if self.model.startswith("local"):
            self.model = "text-embedding-3-small"

    def embed(self, texts: list[str]) -> list[list[float]]:
        import httpx

        resp = httpx.post(
            f"{config.OPENAI_BASE_URL}/embeddings",
            headers={"Authorization": f"Bearer {config.OPENAI_API_KEY}"},
            json={"model": self.model, "input": texts},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        return [d["embedding"] for d in data]

"""Ingestion pipeline: parse -> chunk -> embed -> upsert (UC-2, FR-7..FR-10).

AI-concept note:
- *chunking* — documents are split into ~500-token pieces with overlap so a passage's
  context isn't lost at boundaries, and so citations point at a precise location.
- *embeddings* — each chunk becomes a vector capturing its meaning.
- *upsert / dedup* — idempotent writes let us re-index safely; a content hash avoids
  indexing the same source twice (FR-10).
"""

from __future__ import annotations

import hashlib
import html
import re

from .. import providers
from ..repositories import ChunkRepository, DocumentRepository
from ..util import approx_tokens

CHUNK_WORDS = 400
CHUNK_OVERLAP = 50


def _strip_html(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
    text = re.sub(r"(?s)<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def parse_bytes(data: bytes, doc_type: str) -> str:
    if doc_type == "pdf":
        from io import BytesIO

        from pypdf import PdfReader

        reader = PdfReader(BytesIO(data))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    text = data.decode("utf-8", errors="replace")
    if doc_type == "html":
        return _strip_html(text)
    return text


def fetch_url(url: str) -> str:
    import httpx

    resp = httpx.get(url, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    return _strip_html(resp.text)


def chunk_text(text: str) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks, start = [], 0
    while start < len(words):
        window = words[start : start + CHUNK_WORDS]
        chunks.append(" ".join(window))
        if start + CHUNK_WORDS >= len(words):
            break
        start += CHUNK_WORDS - CHUNK_OVERLAP
    return chunks


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


class IngestionService:
    def __init__(self):
        self.docs = DocumentRepository()
        self.chunks = ChunkRepository()
        self.embedder = providers.make_embedding_provider()
        self.vectors = providers.make_vector_store()

    def index_document(self, doc_id: str, raw_text: str) -> None:
        """Run the (background) pipeline for an already-created Document row."""
        try:
            self.docs.set_status(doc_id, "Parsing")
            pieces = chunk_text(raw_text)
            if not pieces:
                self.docs.set_status(doc_id, "Failed", error="No extractable text", chunk_count=0)
                return
            vectors = self.embedder.embed(pieces)
            for seq, (piece, vec) in enumerate(zip(pieces, vectors)):
                chunk_id = self.chunks.add(
                    doc_id, piece, f"chunk {seq + 1}", approx_tokens(piece), seq
                )
                self.vectors.upsert(chunk_id, doc_id, vec)
            self.docs.set_status(doc_id, "Indexed", chunk_count=len(pieces))
        except Exception as exc:  # isolate failure to this document (NFR-3)
            self.docs.set_status(doc_id, "Failed", error=str(exc))

    def reindex(self, doc_id: str, raw_text: str) -> None:
        self.chunks.delete_by_document(doc_id)
        self.vectors.delete_by_document(doc_id)
        self.index_document(doc_id, raw_text)

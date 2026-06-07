"""A simple, local vector store backed by SQLite + numpy.

AI-concept note (semantic search): we store each chunk's embedding and, at query
time, compute cosine similarity between the query vector and every chunk vector,
returning the top-k. A production system uses an ANN index (Chroma/LanceDB/pgvector)
for speed, but the brute-force version makes the *concept* crystal clear and needs
zero extra dependencies.
"""

from __future__ import annotations

import numpy as np

from ..db import get_conn


class SqliteVectorStore:
    def upsert(self, chunk_id: str, document_id: str, vector: list[float]) -> None:
        arr = np.asarray(vector, dtype=np.float32)
        conn = get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO chunk_vectors (chunk_id, document_id, dim, vector) "
            "VALUES (?, ?, ?, ?)",
            (chunk_id, document_id, arr.shape[0], arr.tobytes()),
        )
        conn.commit()

    def search(self, vector: list[float], k: int) -> list[tuple[str, float]]:
        conn = get_conn()
        rows = conn.execute(
            "SELECT chunk_id, vector FROM chunk_vectors"
        ).fetchall()
        if not rows:
            return []
        q = np.asarray(vector, dtype=np.float32)
        q_norm = np.linalg.norm(q) or 1.0
        scored: list[tuple[str, float]] = []
        for row in rows:
            v = np.frombuffer(row["vector"], dtype=np.float32)
            if v.shape != q.shape:
                continue
            sim = float(np.dot(q, v) / (q_norm * (np.linalg.norm(v) or 1.0)))
            scored.append((row["chunk_id"], sim))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    def delete_by_document(self, document_id: str) -> None:
        conn = get_conn()
        conn.execute("DELETE FROM chunk_vectors WHERE document_id = ?", (document_id,))
        conn.commit()

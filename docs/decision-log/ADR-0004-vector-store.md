# ADR-0004 — Vector store: embedded SQLite + numpy (brute-force search)

- **Status:** Accepted
- **Version:** 1.0
- **Date:** 2026-06-07

## Context

RAG needs to store chunk embeddings and find the top-k most similar to a query. The HLD proposed
Chroma / LanceDB / pgvector. The app must run **offline with zero setup** and stay easy to learn
from.

## Decision

Implement `SqliteVectorStore`: store each embedding as a `BLOB` in a `chunk_vectors` table and
compute **cosine similarity in numpy** over all vectors at query time (brute force), returning
top-k. It sits behind the `VectorStore` interface so a real ANN store can replace it later.

## Consequences

**Pros**
- Zero extra services/dependencies; fully local and reproducible.
- Brute-force cosine makes the *concept* of semantic search explicit and inspectable.
- Same DB file holds metadata and vectors — trivial backup/reset.

**Cons**
- O(N) per query: fine for hundreds–thousands of chunks, not millions.
- No approximate-nearest-neighbor index, quantization, or sharding.

## Alternatives considered

- **Chroma / LanceDB** — great embedded ANN stores; deferred to avoid heavier deps for a learning
  build. The interface makes swapping straightforward.
- **pgvector (Postgres)** — rejected for v1: needs a running database server, contradicting the
  local-first, zero-setup goal.

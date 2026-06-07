# ADR-0013 — Chunking strategy and default embeddings

- **Status:** Accepted
- **Version:** 1.0
- **Date:** 2026-06-07

## Context

Ingestion must split documents for retrieval and turn chunks into vectors (US-1). Chunk size and
embedding choice affect retrieval quality, citation granularity, and offline runnability.

## Decision

- **Chunking:** split on whitespace into windows of **~400 words with 50-word overlap**
  (approximately the ~500-token / 50-overlap target in the LLD). Each chunk records a `location`.
- **Default embeddings:** a **256-dimension hashing-trick** vector (bag-of-words hashed with sign),
  L2-normalized. Deterministic and offline.
- **Dedup:** a SHA-256 **content hash** prevents indexing the same source twice (FR-10).
- Both chunking params and the embedding provider are configurable / swappable.

## Consequences

**Pros**
- Overlap preserves context across chunk boundaries; per-chunk `location` enables precise citations.
- Hashing embeddings need no model/network and make vector search reproducible for learning.
- Content-hash dedup is simple and effective.

**Cons**
- Hashing embeddings capture lexical overlap, not deep semantics — weaker than real embeddings
  (mitigated by swapping in OpenAI embeddings; see [ADR-0006](ADR-0006-offline-first-providers.md)).
- Word-count chunking is coarser than token-accurate or structure-aware splitting.

## Alternatives considered

- **sentence-transformers (local)** — better semantics; deferred (heavy `torch` dependency).
- **Token-accurate / semantic chunking** — deferred: more complex; word windows suffice for v1.

# ADR-0006 — Offline-first providers behind interfaces

- **Status:** Accepted
- **Version:** 1.0
- **Date:** 2026-06-07

## Context

The app should be runnable immediately for learning, ideally **without any API keys or network**,
while still allowing real hosted providers. The HLD highlights a "local <-> hosted / private <->
powerful" spectrum and the concept of **provider abstraction**.

## Decision

Define interfaces (`EmbeddingProvider`, `LLMClient`, `VectorStore`, `WebSearchProvider`,
`Reranker`) and ship **offline default implementations**, selectable via env vars through a
factory (`providers/__init__.py`):

| Capability | Default (offline) | Real provider |
|---|---|---|
| Embeddings | hashing-trick vectors (`local`) | OpenAI (`openai`) |
| LLM | deterministic policy mock (`mock`) | OpenAI function calling (`openai`) |
| Web search | mock results (`mock`) | Tavily (`tavily`) |
| Reranker | lexical overlap (`lexical`) | (pluggable) |

## Consequences

**Pros**
- Runs with zero keys/network; the whole agentic loop is exercisable and testable immediately.
- Teaches provider abstraction directly; swapping is a one-line env change.
- The mock LLM encodes a transparent policy (docs -> web -> answer) that makes the loop legible.

**Cons**
- Mock providers are not intelligent; answer quality is illustrative, not production-grade.
- Two code paths per provider to keep working (mock + real).

## Alternatives considered

- **Require OpenAI/Tavily keys from day one** — rejected: blocks immediate, offline learning and
  CI/smoke testing.
- **Local models via Ollama / sentence-transformers** — deferred: pulls heavy dependencies
  (e.g. torch); the interfaces leave this open as a future provider.

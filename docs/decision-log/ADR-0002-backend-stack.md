# ADR-0002 — Backend stack: Python + FastAPI

- **Status:** Accepted
- **Version:** 1.0
- **Date:** 2026-06-07

## Context

The backend must run a RAG/agent pipeline, expose a streaming chat API, and integrate with
ML-adjacent libraries (embeddings, parsers, LLM SDKs). The PRD proposes Python (FastAPI) or Node.

## Decision

Use **Python 3 + FastAPI**, served by **uvicorn**. Keep runtime dependencies minimal:
`fastapi`, `uvicorn`, `python-multipart`, `numpy`, `pypdf`, `httpx`.

## Consequences

**Pros**
- Best ecosystem for AI/RAG work (embeddings, parsing, vector math, LLM SDKs).
- FastAPI gives typed request models, async, and easy `StreamingResponse` for SSE.
- Small dependency surface keeps install fast and the learning code readable.

**Cons**
- A second language alongside the TS frontend (acceptable; clear separation of concerns).
- Python packaging/venv friction vs an all-JS stack.

## Alternatives considered

- **Node/Express backend** — rejected: would unify language with the frontend but has a weaker
  Python-grade ML/RAG library ecosystem for a learning project.

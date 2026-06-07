# Personal Knowledge Assistant (PKA)

A private, single-user **agentic RAG** chatbot that answers questions grounded in your own
documents, falls back to web search when needed, cites every source, and logs each request as
a fully inspectable trace.

This repository implements **Approach C (Agentic RAG)** from the design docs:
- [`docs/requirements/PRD.md`](docs/requirements/PRD.md) — product requirements
- [`docs/design/HLD.md`](docs/design/HLD.md) — high-level design (approach comparison)
- [`docs/design/LLD.md`](docs/design/LLD.md) — low-level design (sequence diagrams)

It is built to **learn AI concepts**, so every module is annotated with the concept it teaches:
embeddings, chunking, semantic search, reranking, function calling, the ReAct agent loop,
guardrails, grounding/citations, and LLM observability.

## Architecture

```
React + TypeScript (Vite)  ──HTTP/SSE──►  FastAPI backend
  Chat · Sources · Monitoring · Settings        │
                                                 ├─ Agent (ReAct loop + guardrails)
                                                 ├─ Tools: search_docs · search_web · fetch_url
                                                 ├─ Ingestion (parse → chunk → embed → upsert)
                                                 ├─ Tracer (one trace per request)
                                                 └─ SQLite (metadata + traces) + vector store
```

### Runs fully offline by default
The default providers are local/offline so the app works with **zero API keys**:
- **Embeddings:** hashing-trick vectors (`local`)
- **LLM:** a deterministic mock that drives the ReAct loop (`mock`)
- **Web search:** a mock provider (`mock`)
- **Reranker:** lexical overlap (`lexical`)

Swap in real providers via environment variables (see below).

## Quick start

### 1. Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Backend runs at `http://localhost:8000` (health: `/api/health`).

Run the end-to-end smoke test (ingestion → retrieval → agent → tracing → metrics):
```bash
python smoke_test.py
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`. The dev server proxies `/api` to the backend.

## Using real (hosted) providers

Set these before starting the backend:

```bash
# OpenAI for LLM (function calling) and/or embeddings
export PKA_LLM_PROVIDER=openai
export PKA_EMBEDDING_PROVIDER=openai
export OPENAI_API_KEY=sk-...

# Tavily for real web search + extraction
export PKA_WEB_PROVIDER=tavily
export TAVILY_API_KEY=tvly-...
```

Everything sits behind interfaces (`backend/app/providers/`), so swapping providers does not
touch the rest of the app — this is the "provider abstraction" concept in action.

## Feature → user-story map

| Screen | Features | User stories |
|---|---|---|
| **Chat** | streaming answers, inline citations (indigo=doc, amber=web), per-message web toggle, live agent activity, feedback, history | US-3, US-9, US-10, US-12, US-13 |
| **Sources** | drag-drop / URL ingest, status pills, preview, reindex, delete | US-1, US-11 |
| **Monitoring** | metric cards, filterable log explorer, single-trace waterfall, CSV/JSON export | US-4, US-5, US-6 |
| **Settings** | model, top-k, rerank, max-iterations, token budget, web default, pricing | US-14 |

## Project layout

```
backend/
  app/
    providers/    embeddings, llm, vector_store, web_search, reranker (+ interfaces)
    services/     ingestion, retrieval, tools, agent, tracer, citations, chat, metrics
    routers/      chat, documents, traces, metrics, feedback, conversations, settings
    db.py, repositories.py, config.py, util.py, sse.py, main.py
  smoke_test.py
frontend/
  src/views/      ChatView, SourcesView, MonitoringView, SettingsView
  src/api.ts      REST + SSE client
```

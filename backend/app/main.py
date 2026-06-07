"""PKA FastAPI application entrypoint.

Run with:  uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .db import init_db
from .routers import (
    chat,
    conversations,
    documents,
    feedback,
    metrics,
    settings,
    traces,
)

app = FastAPI(title="Personal Knowledge Assistant (PKA)", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "providers": {
            "embeddings": config.EMBEDDING_PROVIDER,
            "llm": config.LLM_PROVIDER,
            "web": config.WEB_SEARCH_PROVIDER,
            "reranker": config.RERANKER,
        },
    }


app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(traces.router)
app.include_router(metrics.router)
app.include_router(feedback.router)
app.include_router(conversations.router)
app.include_router(settings.router)

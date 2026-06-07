"""SQLite connection + schema migrations.

AI-concept note: relational metadata (documents, chunks, conversations, traces)
lives here, while the *embedding vectors* live in the vector store keyed by
``chunk_id``. This SQL-vs-vector split is a standard RAG pattern (LLD section 3).
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager

from .config import DB_PATH

_local = threading.local()


def get_conn() -> sqlite3.Connection:
    """One connection per thread (SQLite connections are not thread-safe)."""
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        _local.conn = conn
    return conn


@contextmanager
def transaction():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    type        TEXT NOT NULL,
    source_uri  TEXT,
    content_hash TEXT,
    added_at    TEXT NOT NULL,
    status      TEXT NOT NULL,
    error       TEXT,
    size        INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS chunks (
    id          TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    text        TEXT NOT NULL,
    location    TEXT,
    token_count INTEGER DEFAULT 0,
    seq         INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id);

CREATE TABLE IF NOT EXISTS conversations (
    id         TEXT PRIMARY KEY,
    title      TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id              TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,
    content         TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);

CREATE TABLE IF NOT EXISTS citations (
    id          TEXT PRIMARY KEY,
    message_id  TEXT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL,
    ref         TEXT,
    title       TEXT,
    location    TEXT,
    score       REAL,
    idx         INTEGER
);
CREATE INDEX IF NOT EXISTS idx_citations_msg ON citations(message_id);

CREATE TABLE IF NOT EXISTS traces (
    id              TEXT PRIMARY KEY,
    conversation_id TEXT,
    message_id      TEXT,
    query           TEXT,
    model           TEXT,
    iterations      INTEGER DEFAULT 0,
    used_web        INTEGER DEFAULT 0,
    tokens_in       INTEGER DEFAULT 0,
    tokens_out      INTEGER DEFAULT 0,
    cost            REAL DEFAULT 0,
    latency_ms      INTEGER DEFAULT 0,
    status          TEXT,
    error           TEXT,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_traces_created ON traces(created_at);

CREATE TABLE IF NOT EXISTS trace_steps (
    id        TEXT PRIMARY KEY,
    trace_id  TEXT NOT NULL REFERENCES traces(id) ON DELETE CASCADE,
    seq       INTEGER NOT NULL,
    kind      TEXT NOT NULL,
    tool_name TEXT,
    latency_ms INTEGER DEFAULT 0,
    detail    TEXT
);
CREATE INDEX IF NOT EXISTS idx_steps_trace ON trace_steps(trace_id);

CREATE TABLE IF NOT EXISTS feedback (
    id         TEXT PRIMARY KEY,
    message_id TEXT REFERENCES messages(id) ON DELETE CASCADE,
    trace_id   TEXT,
    rating     INTEGER NOT NULL,
    note       TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunk_vectors (
    chunk_id  TEXT PRIMARY KEY REFERENCES chunks(id) ON DELETE CASCADE,
    document_id TEXT NOT NULL,
    dim       INTEGER NOT NULL,
    vector    BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_vectors_doc ON chunk_vectors(document_id);

CREATE TABLE IF NOT EXISTS settings (
    id   INTEGER PRIMARY KEY CHECK (id = 1),
    data TEXT NOT NULL
);
"""


def init_db() -> None:
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()

# ADR-0005 — Relational store: SQLite via stdlib (no ORM)

- **Status:** Accepted
- **Version:** 1.0
- **Date:** 2026-06-07

## Context

PKA stores documents, chunks, conversations, messages, citations, traces, trace steps, feedback,
and settings (LLD section 3). It is single-user and local-first (PRD NFR-1).

## Decision

Use **SQLite** through Python's stdlib `sqlite3` with a hand-written schema (`db.py`) and a thin
repository layer (`repositories.py`). Connections are **thread-local** (`check_same_thread=False`)
with WAL mode and `PRAGMA foreign_keys=ON`. No ORM.

## Consequences

**Pros**
- Single-file, zero-ops, local — perfect for a private single-user app.
- stdlib only: nothing to install; the SQL is visible and teachable.
- FK `ON DELETE CASCADE` makes deleting a document remove its chunks/vectors immediately (UC-8).

**Cons**
- Manual SQL/CRUD instead of ORM conveniences and migrations tooling.
- Thread-local connections require care for background tasks (handled).

## Alternatives considered

- **SQLAlchemy ORM** — rejected: adds a dependency and abstraction that obscures the SQL in a
  learning project.
- **Postgres** — rejected for v1: needs a server; SQLite covers single-user needs.

# PKA Decision Log

This folder is the **ongoing, versioned record of the significant decisions** made while
building the Personal Knowledge Assistant (PKA) — covering the HLD/LLD design, the technology
stack, and key implementation trade-offs.

We use the **ADR (Architecture Decision Record)** format: one short, numbered document per
decision. ADRs are append-only history, not living documents — so the reasoning at the time is
never lost.

## How to read an ADR

Each record (`ADR-NNNN-title.md`) has:

- **Status** — `Proposed` | `Accepted` | `Superseded by ADR-XXXX` | `Deprecated`
- **Version** — bumped when the decision itself is revised in place (see Versioning below)
- **Date** — when the (latest) decision was made
- **Context** — the forces and constraints in play
- **Decision** — what we chose
- **Consequences** — the resulting pros and cons
- **Alternatives considered** — what we rejected and why

## Versioning convention

- ADRs are **immutable once `Accepted`** for the *substance* of the decision.
- **Minor clarifications** (wording, links, added consequences) bump the in-file **Version**
  (e.g. `1.0 -> 1.1`) and are noted in that ADR's **Revision history** section.
- A **reversal or material change** is recorded as a **new ADR** that `Supersedes` the old one;
  the old ADR's Status is updated to `Superseded by ADR-XXXX`. This preserves the trail.
- Example in this log: [ADR-0001](ADR-0001-rag-architecture-approach.md) was revised from
  recommending Approach B to choosing Approach C (Agentic RAG) — captured as a version bump with
  full revision history, since no code had been committed yet.

## Index

| ADR | Title | Status | Version |
|---|---|---|---|
| [0001](ADR-0001-rag-architecture-approach.md) | RAG architecture approach (Naive vs Gated vs Agentic) | Accepted | 2.0 |
| [0002](ADR-0002-backend-stack.md) | Backend stack: Python + FastAPI | Accepted | 1.0 |
| [0003](ADR-0003-frontend-stack.md) | Frontend stack: React + TypeScript + Vite | Accepted | 1.0 |
| [0004](ADR-0004-vector-store.md) | Vector store: embedded SQLite + numpy (brute force) | Accepted | 1.0 |
| [0005](ADR-0005-relational-store.md) | Relational store: SQLite via stdlib (no ORM) | Accepted | 1.0 |
| [0006](ADR-0006-offline-first-providers.md) | Offline-first providers behind interfaces | Accepted | 1.0 |
| [0007](ADR-0007-hand-rolled-agent-loop.md) | Hand-rolled agent loop vs a framework | Accepted | 1.0 |
| [0008](ADR-0008-agent-guardrails.md) | Agent guardrails (max-iterations, token budget, forced final) | Accepted | 1.0 |
| [0009](ADR-0009-tool-design.md) | Tool design and the tool boundary | Accepted | 1.0 |
| [0010](ADR-0010-citation-scheme.md) | Citation scheme and source provenance | Accepted | 1.0 |
| [0011](ADR-0011-sse-streaming.md) | Streaming via SSE over POST (not EventSource) | Accepted | 1.0 |
| [0012](ADR-0012-tracing-model.md) | Observability: one trace per request, variable steps | Accepted | 1.0 |
| [0013](ADR-0013-chunking-and-embeddings.md) | Chunking strategy and default embeddings | Accepted | 1.0 |
| [0014](ADR-0014-build-order.md) | Build order: functions first, agent last | Accepted | 1.0 |
| [0015](ADR-0015-no-git-init.md) | Repository / version-control posture during build | Accepted | 1.0 |

## Adding a new decision

1. Copy the structure of any existing ADR.
2. Use the next free number (`ADR-0016-...`).
3. Add a row to the Index table above.
4. If it changes an earlier decision, set the old ADR's Status to `Superseded by ADR-00NN` and
   explain the change in the new ADR's Context.

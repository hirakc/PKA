# ADR-0014 — Build order: functions first, agent last

- **Status:** Accepted
- **Version:** 1.0
- **Date:** 2026-06-07

## Context

Approach C is the most complex path. We need a build sequence that always leaves a working system
and matches the PRD milestones M1-M4.

## Decision

Build in this order (LLD section 12):

1. **M1** — ingestion + `search_docs` as a plain function + a retrieve-then-answer chat.
2. **M2** — the Tracer, log explorer, and metrics.
3. **M3** — wrap the pieces as tools and add the agent ReAct loop + guardrails + web tools.
4. **M4** — sources management, history, feedback, settings, export.

The agentic loop is added **last**, on top of already-tested retrieval and tracing.

## Consequences

**Pros**
- Always a runnable system; each milestone is independently verifiable.
- Retrieval and observability are proven before the non-deterministic agent is layered on.
- Mirrors the conceptual ladder A -> B -> C from [ADR-0001](ADR-0001-rag-architecture-approach.md).

**Cons**
- The M1 "retrieve-then-answer" path is partly superseded by the agent (kept as a reference
  implementation in `services/chat.py` for comparison/learning).

## Alternatives considered

- **Agent-first** — rejected: debugging an agent on top of unverified retrieval/tracing is far
  harder and offers no working intermediate system.

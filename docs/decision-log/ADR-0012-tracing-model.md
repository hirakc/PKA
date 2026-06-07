# ADR-0012 — Observability: one trace per request, variable steps

- **Status:** Accepted
- **Version:** 1.0
- **Date:** 2026-06-07

## Context

Observability is a headline PKA feature (PRD NFR-4: "no answer without an inspectable trace").
An agent's path is non-deterministic, so the number of steps varies per request.

## Decision

Every chat request opens exactly one `Trace` and appends ordered `TraceStep` rows. `TraceStep.kind`
is one of `reason | tool_call | tool_result | final`; tool steps also record `tool_name`. The
`Trace` stores `iterations`, `used_web`, tokens in/out, estimated `cost`, total `latency_ms`, and
`status`. Aggregate metrics (US-6) are computed from traces, including **p50/p95 latency**.

## Consequences

**Pros**
- A variable-length agent run is fully reconstructable as a step waterfall (UC-7).
- Trace + feedback form a labeled dataset for future evaluation/tuning.
- Cost/latency/iteration accounting is built in, not bolted on.

**Cons**
- A DB write per step adds minor overhead (acceptable at single-user scale).
- Detail payloads are summarized to keep trace size bounded.

## Alternatives considered

- **Logging to flat files / stdout** — rejected: not queryable or drill-downable in the UI.
- **External tracing (OpenTelemetry/Langfuse)** — deferred: valuable later, but adds a dependency
  and obscures the concept for a learning build.

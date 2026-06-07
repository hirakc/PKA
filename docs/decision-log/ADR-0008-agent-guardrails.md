# ADR-0008 — Agent guardrails (max-iterations, token budget, forced final)

- **Status:** Accepted
- **Version:** 1.0
- **Date:** 2026-06-07

## Context

An autonomous ReAct loop can loop indefinitely, call tools needlessly, or run up cost/latency —
the main cons of the agentic approach (ADR-0001). LLD section 10 specifies guardrails.

## Decision

Bound every run with tunable guardrails (persisted in Settings, FR-19):

- `MAX_ITERATIONS` (default 6) — hard cap on reason->act cycles.
- `TOKEN_BUDGET` (default 12000) — when exceeded, tools are withheld so the model must answer.
- **Forced final turn** — if the loop ends without an answer, send "answer now with what you have,
  or say you don't know," guaranteeing termination and an honest abstention (FR-6).
- **Web toggle** — when web is disabled, `search_web`/`fetch_url` are simply not advertised.

## Consequences

**Pros**
- Bounds worst-case cost and latency; guarantees the loop terminates.
- Makes the agent safe to run with the offline mock and with real paid APIs alike.
- All knobs are settings, so their effect on behavior is observable in Monitoring.

**Cons**
- A low cap can cut off a genuinely multi-step answer (tunable trade-off).
- Token estimates are approximate for the mock provider.

## Alternatives considered

- **No limits** — rejected: unsafe and expensive for an autonomous loop.
- **LLM-judged stopping only** — rejected as the sole mechanism: non-deterministic; hard caps are
  a necessary backstop.

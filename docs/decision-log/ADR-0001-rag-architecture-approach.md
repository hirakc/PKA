# ADR-0001 — RAG architecture approach (Naive vs Gated vs Agentic)

- **Status:** Accepted
- **Version:** 2.0
- **Date:** 2026-06-07

## Context

PKA must answer questions from the user's documents, fall back to the web when needed, and cite
sources (PRD G1-G3). The project's stated purpose is **learning AI concepts**. Three candidate
architectures were compared in the HLD:

- **A — Naive RAG:** always retrieve, then generate. Simplest; no fallback, no "I don't know".
- **B — Confidence-Gated RAG + Web Fallback:** retrieve -> rerank -> a hard-coded confidence gate
  decides docs vs web vs abstain.
- **C — Agentic RAG:** the LLM decides, via function calling in a ReAct loop, which tools to call.

## Decision

Build **Approach C (Agentic RAG)**. Approaches A and B are retained in the HLD as the conceptual
ladder, and their components (retrieval, reranking, web search) are **reused as the agent's
tools** rather than discarded.

## Consequences

**Pros**
- Directly teaches the agentic paradigm: function calling, the ReAct loop, autonomous control.
- Handles multi-step and mixed-source questions naturally (PRD UC-4).
- Reuses A/B building blocks, so no work is wasted.

**Cons (and mitigations)**
- Non-deterministic and harder to debug -> mitigated by one rich trace per run ([ADR-0012](ADR-0012-tracing-model.md)).
- Higher cost/latency from multiple LLM calls -> mitigated by guardrails ([ADR-0008](ADR-0008-agent-guardrails.md)).

## Alternatives considered

- **Approach A** — rejected: fails the web-fallback and abstention requirements (G3, FR-6).
- **Approach B** — initially recommended for predictability, but rejected as the final choice
  because the explicit learning goal is the agentic pattern. Its deterministic gate is still
  documented as the mental model that precedes C.

## Revision history

- **1.0 (2026-06-07):** Recommended Approach B (confidence-gated) as the best balance for v1.
- **2.0 (2026-06-07):** Superseded the recommendation in place — user chose Approach C to learn
  the agentic flow. No code had been written yet, so an in-file version bump (rather than a new
  superseding ADR) was the appropriate record.

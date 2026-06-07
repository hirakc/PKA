# ADR-0007 — Hand-rolled agent loop vs a framework

- **Status:** Accepted
- **Version:** 1.0
- **Date:** 2026-06-07

## Context

Approach C ([ADR-0001](ADR-0001-rag-architecture-approach.md)) needs a ReAct agent loop. Options
range from frameworks (LangGraph, LlamaIndex agents) to writing the loop by hand.

## Decision

**Hand-roll** the ReAct loop in `services/agent.py`: a plain Python loop that calls the
`LLMClient`, dispatches tool calls through the `ToolRegistry`, appends observations to the message
list, and stops on a final answer or a guardrail.

## Consequences

**Pros**
- Maximum transparency — the agent loop is ~100 readable lines, ideal for learning how agents work.
- No framework abstractions, version churn, or hidden control flow.
- Full control over streaming events and trace emission.

**Cons**
- We re-implement conveniences a framework provides (retries, tool schemas, memory helpers).
- More responsibility for correctness of the loop and guardrails.

## Alternatives considered

- **LangGraph / LlamaIndex agents** — deferred: powerful, but obscure the mechanics the project
  exists to teach. Can be adopted later behind the same service boundary.

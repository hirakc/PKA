# ADR-0009 — Tool design and the tool boundary

- **Status:** Accepted
- **Version:** 1.0
- **Date:** 2026-06-07

## Context

In an agentic system the LLM acts via tools. We must decide which tools exist, how they are
described to the model, and where the safety boundary sits (LLD section 4).

## Decision

Expose three typed tools through a `ToolRegistry`:

- `search_docs(query, k?)` — embed -> vector search -> rerank over the user's corpus.
- `search_web(query)` — public web search (only advertised when web is enabled).
- `fetch_url(url)` — fetch + extract clean readable text.

The LLM only ever **requests** a tool by name + JSON arguments; the backend validates and
executes it. Unknown/disabled tools return a typed `ToolError` the agent can recover from. Each
tool appends to an ordered `collected_sources` list used for citations ([ADR-0010](ADR-0010-citation-scheme.md)).

## Consequences

**Pros**
- Clear safety boundary: the model cannot touch the DB or network directly.
- Tool schemas teach function-calling contracts explicitly.
- Reuses the M1 retrieval function unchanged — it simply becomes a tool.

**Cons**
- Tools are executed sequentially (no parallel tool calls) — simpler but slower for independent calls.
- Tool schemas must be kept in sync with their implementations by hand.

## Alternatives considered

- **One mega "search" tool** — rejected: separate tools make the agent's choices (and traces) clearer.
- **Letting the model call the vector store directly** — rejected: breaks the safety boundary.

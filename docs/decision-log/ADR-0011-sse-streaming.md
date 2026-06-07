# ADR-0011 — Streaming via SSE over POST (not EventSource)

- **Status:** Accepted
- **Version:** 1.0
- **Date:** 2026-06-07

## Context

The chat must stream the answer and live agent activity (FR-1). The request carries a JSON body
(query, conversation id, web toggle), and we want a simple event protocol.

## Decision

Stream **Server-Sent Events from a `POST /api/chat`** endpoint using FastAPI `StreamingResponse`.
On the client, read the `fetch` `ReadableStream` and parse SSE frames manually. Event types:
`start`, `trace`, `tool_call`, `tool_result`, `token`, `done`.

## Consequences

**Pros**
- Keeps a rich JSON request body while still streaming (browser `EventSource` is GET-only).
- One-way server->client streaming fits the chat model; no WebSocket machinery needed.
- Typed event names map cleanly to UI updates (activity log, token stream, final payload).

**Cons**
- Manual SSE frame parsing on the client (small, contained helper in `api.ts`).
- No built-in auto-reconnect that native `EventSource` provides.

## Alternatives considered

- **Native `EventSource`** — rejected: GET-only, can't carry the JSON body cleanly.
- **WebSockets** — rejected: bidirectional and heavier than needed for one-way streaming.

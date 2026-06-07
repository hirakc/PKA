# ADR-0003 — Frontend stack: React + TypeScript + Vite

- **Status:** Accepted
- **Version:** 1.0
- **Date:** 2026-06-07

## Context

The PRD specifies four screens (Chat, Sources, Web fallback, Monitoring) with a defined design
language (dark rail, indigo doc citations, amber web sources) and assumes a React + TS frontend.

## Decision

Use **React 18 + TypeScript**, bundled with **Vite**. No UI component library — hand-written CSS
with design tokens (CSS variables) matching the PRD palette. A Vite dev proxy forwards `/api` to
the backend.

## Consequences

**Pros**
- Matches the PRD assumption and the Figma design language.
- Vite gives fast dev server + simple proxy; TS catches integration bugs at build time.
- Zero UI-library lock-in keeps the styling explicit and easy to learn from.

**Cons**
- Hand-rolled components mean slightly more boilerplate than a component kit.
- No design-system guarantees (acceptable for a single-user learning app).

## Alternatives considered

- **Svelte / Vue** — rejected: PRD already assumes React; React has the largest ecosystem.
- **A component library (MUI/shadcn)** — deferred: not needed for four screens, and raw CSS is
  more transparent for learning.

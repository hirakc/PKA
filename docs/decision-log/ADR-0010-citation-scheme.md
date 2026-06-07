# ADR-0010 — Citation scheme and source provenance

- **Status:** Accepted
- **Version:** 1.0
- **Date:** 2026-06-07

## Context

Trust requires that every claim be attributable to a source, with document vs web provenance
always obvious (PRD FR-3, UC-4; design language: indigo=doc, amber=web).

## Decision

- The agent maintains an **ordered `collected_sources` list** (docs first, then web) across the run.
- The model cites claims with **`[n]` markers** that index into that list (1-based).
- The `CitationBuilder` parses `[n]` markers from the final answer and writes a `Citation` row per
  used marker, tagged `source_type` = `doc` | `web`.
- The UI renders `[n]` as colored pills and lists source chips (indigo for docs, amber + outbound
  link for web).

## Consequences

**Pros**
- Deterministic mapping from answer text to concrete sources; verifiable provenance.
- Mixed-source answers (UC-4) naturally show which parts came from docs vs web.
- Works identically for the mock and real LLMs.

**Cons**
- Relies on the model emitting well-formed `[n]` markers; malformed markers are simply dropped.
- Marker numbering is positional, so the prompt must instruct consistent numbering.

## Alternatives considered

- **Span-level / offset citations** — more precise but far more complex; rejected for v1.
- **No inline markers, just a sources list** — rejected: loses per-claim attribution.

"""Tracer — one structured trace per request (PRD FR-14, NFR-4).

AI-concept note (LLM observability): an agent's path is non-deterministic, so we
record every step (reason / tool_call / tool_result / final) in order with timing.
The trace is your debugger, your cost meter, and your future eval dataset. "You
can't improve what you can't see."
"""

from __future__ import annotations

import time

from ..repositories import TraceRepository


class Trace:
    def __init__(self, trace_id: str, repo: TraceRepository):
        self.id = trace_id
        self._repo = repo
        self._seq = 0
        self._t0 = time.perf_counter()

    def step(self, kind: str, detail: dict, tool_name: str | None = None, latency_ms: int = 0) -> None:
        self._seq += 1
        self._repo.add_step(self.id, self._seq, kind, tool_name, latency_ms, detail)

    def finalize(self, **fields) -> None:
        fields.setdefault("latency_ms", int((time.perf_counter() - self._t0) * 1000))
        self._repo.finalize(self.id, **fields)


class Tracer:
    def __init__(self):
        self.repo = TraceRepository()

    def open(self, conversation_id: str, query: str, model: str) -> Trace:
        trace_id = self.repo.create(conversation_id, query, model)
        return Trace(trace_id, self.repo)

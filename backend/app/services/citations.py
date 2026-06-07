"""Citation builder (US-10) — attribute answer claims to their sources.

AI-concept note (provenance): the answer text contains [n] markers; we map each one
onto the n-th source the agent actually collected (docs first, then web). Each
citation is tagged ``doc`` or ``web`` so the UI can render document sources in indigo
and web sources in amber, making mixed-source answers (UC-4) transparent.
"""

from __future__ import annotations

import re

from ..repositories import CitationRepository

_MARKER_RE = re.compile(r"\[(\d+)\]")


def build_citations(message_id: str, answer: str, collected_sources: list[dict]) -> list[dict]:
    repo = CitationRepository()
    used_indices = sorted({int(m) for m in _MARKER_RE.findall(answer)})
    saved = []
    for idx in used_indices:
        if 1 <= idx <= len(collected_sources):
            src = collected_sources[idx - 1]
            repo.add(
                message_id,
                src["source_type"],
                src["ref"],
                src["title"],
                src.get("location"),
                src.get("score"),
                idx,
            )
            saved.append({**src, "idx": idx})
    return saved

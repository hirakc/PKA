"""Server-Sent Events helpers for streaming chat + agent step events."""

from __future__ import annotations

import json


def sse_event(event: str, data: dict) -> str:
    """Format a single SSE frame."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"

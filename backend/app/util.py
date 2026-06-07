"""Small shared helpers: ids, timestamps, tokens, cost."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from . import config


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def estimate_cost(tokens_in: int, tokens_out: int, settings) -> float:
    return round(
        (tokens_in / 1000) * settings.price_per_1k_input
        + (tokens_out / 1000) * settings.price_per_1k_output,
        6,
    )

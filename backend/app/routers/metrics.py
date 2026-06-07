"""Metrics API (US-6, FR-16)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from ..services.metrics import compute_metrics

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("")
def metrics(days: int = Query(default=7, ge=1, le=365)):
    return compute_metrics(days)

"""Feedback API (US-13, UC-9)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..repositories import FeedbackRepository

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    message_id: str
    trace_id: str | None = None
    rating: int  # +1 (up) or -1 (down)
    note: str | None = None


@router.post("")
def add_feedback(req: FeedbackRequest):
    fid = FeedbackRepository().add(req.message_id, req.trace_id, req.rating, req.note)
    return {"id": fid}


@router.get("/recent")
def recent_feedback():
    return {"feedback": FeedbackRepository().recent()}

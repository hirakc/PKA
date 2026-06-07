"""Chat API — streams the agent's steps + answer over SSE (UC-1, UC-3, UC-4)."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..repositories import SettingsRepository
from ..services.chat import ChatService

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    conversation_id: str | None = None
    web_enabled: bool | None = None  # per-message override (FR-5)


@router.post("/chat")
def chat(req: ChatRequest):
    web_enabled = req.web_enabled
    if web_enabled is None:
        web_enabled = SettingsRepository().get().web_enabled_default

    service = ChatService()
    generator = service.stream(req.conversation_id, req.query, web_enabled)
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

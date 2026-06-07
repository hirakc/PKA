"""Conversations API — history with citations (UC-5)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..repositories import (
    CitationRepository,
    ConversationRepository,
    MessageRepository,
)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("")
def list_conversations(search: str | None = Query(default=None)):
    return {"conversations": ConversationRepository().list(search=search)}


@router.get("/{conversation_id}")
def get_conversation(conversation_id: str):
    conv = ConversationRepository().get(conversation_id)
    if not conv:
        raise HTTPException(404, "not found")
    messages = MessageRepository().list(conversation_id)
    cites = CitationRepository()
    for m in messages:
        if m["role"] == "assistant":
            m["citations"] = cites.list(m["id"])
    return {"conversation": conv, "messages": messages}

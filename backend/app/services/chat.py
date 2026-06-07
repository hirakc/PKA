"""Chat service — persistence + streaming, wrapping the agent.

Two answer strategies live here:

- ``simple_answer`` — the M1 "retrieve-then-answer" approach (US-3): one retrieval,
  one generation, no agent. Kept as a reference implementation and for comparison.
- ``stream`` — the production path (US-8): the agentic ReAct loop, which *decides*
  whether to use documents, the web, or both.
"""

from __future__ import annotations

from ..repositories import (
    ConversationRepository,
    MessageRepository,
    SettingsRepository,
)
from ..sse import sse_event
from .agent import Agent
from .citations import build_citations
from .retrieval import Retriever


class ChatService:
    def __init__(self):
        self.conversations = ConversationRepository()
        self.messages = MessageRepository()
        self.settings = SettingsRepository()

    # --- M1 reference path (no agent) ---------------------------------------
    def simple_answer(self, query: str) -> dict:
        """Retrieve top-k chunks and ground an answer in them (UC-1)."""
        retriever = Retriever()
        hits = retriever.search_docs(query)
        if not hits:
            return {"answer": "I don't know — no relevant passages in your documents.", "sources": []}
        top = hits[:2]
        body = " ".join(
            f"{h['text'][:160].strip()} [{i + 1}]" for i, h in enumerate(top)
        )
        return {"answer": f"Based on your documents: {body}", "sources": top}

    # --- Agentic path (streamed over SSE) -----------------------------------
    def stream(self, conversation_id: str | None, query: str, web_enabled: bool):
        if not conversation_id:
            conversation_id = self.conversations.create(title=query[:60] or "New chat")
        else:
            self.conversations.touch(conversation_id)
        self.messages.add(conversation_id, "user", query)

        yield sse_event("start", {"conversation_id": conversation_id})

        agent = Agent()
        final_payload = None
        for event, data in agent.run(conversation_id, query, web_enabled):
            if event == "final":
                final_payload = data
                continue
            yield sse_event(event, data)

        # Persist the assistant message + its citations.
        answer = final_payload["answer"] if final_payload else "I don't know."
        message_id = self.messages.add(conversation_id, "assistant", answer)
        citations = build_citations(
            message_id, answer, final_payload["sources"] if final_payload else []
        )
        self.conversations.touch(conversation_id)

        yield sse_event(
            "done",
            {
                "conversation_id": conversation_id,
                "message_id": message_id,
                "trace_id": final_payload.get("trace_id") if final_payload else None,
                "answer": answer,
                "citations": citations,
                "used_web": final_payload.get("used_web") if final_payload else False,
                "iterations": final_payload.get("iterations") if final_payload else 0,
                "tokens_in": final_payload.get("tokens_in") if final_payload else 0,
                "tokens_out": final_payload.get("tokens_out") if final_payload else 0,
                "cost": final_payload.get("cost") if final_payload else 0,
            },
        )

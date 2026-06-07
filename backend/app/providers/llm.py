"""LLM clients (function-calling capable).

Two implementations:

- ``MockLLMClient`` — a deterministic, offline stand-in that emulates the
  reason -> act -> observe loop so the whole agentic pipeline runs with no API key.
  It is *not* intelligent; it follows a fixed policy (try documents first, fall back
  to web, then answer) which is exactly enough to exercise and *learn* the mechanics.
- ``OpenAILLMClient`` — real function calling against an OpenAI-compatible API.

AI-concept note (function calling): the model never executes anything itself. It
returns a structured request to call a named tool with arguments; the backend runs
the tool and feeds the result back. Here that contract is the ``LLMResponse`` /
``ToolCall`` shape.
"""

from __future__ import annotations

import json
import re

from .. import config
from .base import LLMResponse, ToolCall, ToolSpec

DOC_CONFIDENCE_THRESHOLD = 0.18


def _last_user_query(messages: list[dict]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            return m.get("content", "")
    return ""


def _tool_results(messages: list[dict], name: str) -> list[dict]:
    out = []
    for m in messages:
        if m.get("role") == "tool" and m.get("name") == name:
            try:
                out.append(json.loads(m.get("content", "{}")))
            except json.JSONDecodeError:
                pass
    return out


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _first_sentences(text: str, n: int = 2) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(parts[:n]).strip()


class MockLLMClient:
    """Policy-driven fake LLM that drives the agent loop deterministically."""

    def chat(self, messages, tools=None, stream_tokens=None) -> LLMResponse:
        tools = tools or []
        tool_names = {t.name for t in tools}
        query = _last_user_query(messages)
        tokens_in = sum(_approx_tokens(m.get("content") or "") for m in messages)

        doc_runs = _tool_results(messages, "search_docs")
        web_runs = _tool_results(messages, "search_web")
        fetch_runs = _tool_results(messages, "fetch_url")

        # 1) Always consult the user's documents first.
        if "search_docs" in tool_names and not doc_runs:
            return LLMResponse(
                tool_calls=[ToolCall(name="search_docs", arguments={"query": query})],
                tokens_in=tokens_in,
            )

        # Evaluate document confidence (top rerank score).
        top_doc_score = 0.0
        doc_hits: list[dict] = []
        if doc_runs:
            doc_hits = doc_runs[-1].get("results", [])
            if doc_hits:
                top_doc_score = max(h.get("rerank_score", h.get("score", 0)) for h in doc_hits)

        docs_confident = top_doc_score >= DOC_CONFIDENCE_THRESHOLD and bool(doc_hits)

        # 2) If documents are weak and web is allowed, search the web.
        if not docs_confident and "search_web" in tool_names and not web_runs:
            return LLMResponse(
                tool_calls=[ToolCall(name="search_web", arguments={"query": query})],
                tokens_in=tokens_in,
            )

        # 3) Optionally fetch the most promising web page for fuller content.
        if web_runs and "fetch_url" in tool_names and not fetch_runs:
            hits = web_runs[-1].get("results", [])
            if hits:
                return LLMResponse(
                    tool_calls=[ToolCall(name="fetch_url", arguments={"url": hits[0]["url"]})],
                    tokens_in=tokens_in,
                )

        # 4) Compose the final, grounded answer from whatever we collected.
        content = self._compose_answer(query, doc_hits, web_runs, fetch_runs, docs_confident)
        if stream_tokens:
            for tok in re.findall(r"\S+\s*", content):
                stream_tokens(tok)
        return LLMResponse(
            content=content, tokens_in=tokens_in, tokens_out=_approx_tokens(content)
        )

    def _compose_answer(self, query, doc_hits, web_runs, fetch_runs, docs_confident) -> str:
        # Sources are numbered in the order the agent collected them (docs first,
        # then web). The citation builder maps [n] back to these sources.
        if docs_confident and doc_hits:
            top = doc_hits[:2]
            body = " ".join(
                f"{_first_sentences(h['text'])} [{i + 1}]" for i, h in enumerate(top)
            )
            return f"Based on your documents: {body}"

        web_hits = web_runs[-1].get("results", []) if web_runs else []
        if web_hits:
            offset = len(doc_hits[:2])  # web citations are numbered after any doc ones
            snippets = []
            for i, h in enumerate(web_hits[:2]):
                text = h.get("content") or h.get("snippet") or h.get("title", "")
                snippets.append(f"{_first_sentences(text)} [{offset + i + 1}]")
            return "I could not find this in your documents, so I searched the web: " + " ".join(
                snippets
            )

        return (
            "I don't know — I couldn't find a confident answer in your documents"
            " or on the web for that question."
        )


class OpenAILLMClient:
    """Real function calling against an OpenAI-compatible Chat Completions API."""

    def __init__(self):
        self.model = config.DEFAULT_SETTINGS.model

    def _to_openai_tools(self, tools: list[ToolSpec]) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    def chat(self, messages, tools=None, stream_tokens=None) -> LLMResponse:
        import httpx

        payload: dict = {"model": self.model, "messages": messages}
        if tools:
            payload["tools"] = self._to_openai_tools(tools)
            payload["tool_choice"] = "auto"

        resp = httpx.post(
            f"{config.OPENAI_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {config.OPENAI_API_KEY}"},
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        choice = data["choices"][0]["message"]
        usage = data.get("usage", {})

        tool_calls = []
        for tc in choice.get("tool_calls", []) or []:
            fn = tc["function"]
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            tool_calls.append(ToolCall(name=fn["name"], arguments=args, call_id=tc.get("id", "")))

        content = choice.get("content")
        if content and stream_tokens:
            for tok in re.findall(r"\S+\s*", content):
                stream_tokens(tok)

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
        )

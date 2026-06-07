"""Agent orchestrator — the ReAct loop + guardrails (US-8, LLD sections 7 & 10).

    Reason -> Act -> Observe -> repeat -> Answer

AI-concept note:
- *ReAct*: each turn the LLM either calls a tool (act) or emits the final answer.
  Tool results (observations) are appended to the running message list so the model
  can reason over them on the next turn.
- *Guardrails*: MAX_ITERATIONS and TOKEN_BUDGET bound cost/latency; if the loop runs
  out, we force a final "answer now or say you don't know" turn. This is what
  separates a useful agent from a runaway one.

The agent is a generator that yields ``(event, data)`` tuples so the API can stream
the agent's thinking, tool calls, observations, and answer tokens live over SSE.
"""

from __future__ import annotations

import json
import time

from .. import providers
from ..repositories import SettingsRepository
from ..util import estimate_cost
from .tools import ToolError, ToolRegistry
from .tracer import Tracer

SYSTEM_PROMPT = (
    "You are PKA, a personal knowledge assistant. Answer the user's question.\n"
    "- Prefer the user's private documents: call search_docs first.\n"
    "- If the documents are insufficient and web tools are available, call search_web,\n"
    "  then fetch_url on the most promising result.\n"
    "- You may call tools multiple times. When you have enough, answer.\n"
    "- Answer ONLY from tool results. Cite every claim as [n] where n is the source number.\n"
    "- If neither documents nor web give a confident answer, say you don't know."
)


class Agent:
    def __init__(self):
        self.llm = providers.make_llm_client()
        self.settings = SettingsRepository()
        self.tracer = Tracer()

    def run(self, conversation_id: str, query: str, web_enabled: bool):
        cfg = self.settings.get()
        registry = ToolRegistry(web_enabled=web_enabled)
        trace = self.tracer.open(conversation_id, query, cfg.model)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ]
        tokens_in = tokens_out = 0
        used_web = False
        final_answer = None
        iterations = 0

        yield "trace", {"trace_id": trace.id}

        for i in range(cfg.max_iterations):
            iterations = i + 1
            budget_exhausted = (tokens_in + tokens_out) >= cfg.token_budget
            turn_tools = None if budget_exhausted else registry.specs()

            t0 = time.perf_counter()
            resp = self.llm.chat(messages, tools=turn_tools)
            latency = int((time.perf_counter() - t0) * 1000)
            tokens_in += resp.tokens_in
            tokens_out += resp.tokens_out

            if resp.is_final:
                final_answer = resp.content or ""
                trace.step("reason", {"decision": "final", "iteration": iterations}, latency_ms=latency)
                break

            # The model requested one or more tools (we execute sequentially).
            for call in resp.tool_calls:
                trace.step(
                    "tool_call",
                    {"arguments": call.arguments, "iteration": iterations},
                    tool_name=call.name,
                    latency_ms=latency,
                )
                yield "tool_call", {"tool": call.name, "arguments": call.arguments}

                ts = time.perf_counter()
                try:
                    result = registry.dispatch(call.name, call.arguments)
                    status = "ok"
                except ToolError as exc:
                    result = {"error": str(exc)}
                    status = "error"
                tool_latency = int((time.perf_counter() - ts) * 1000)

                if call.name in ("search_web", "fetch_url") and status == "ok":
                    used_web = True

                trace.step(
                    "tool_result",
                    {"status": status, "summary": _summarize(result)},
                    tool_name=call.name,
                    latency_ms=tool_latency,
                )
                yield "tool_result", {"tool": call.name, "status": status, "summary": _summarize(result)}

                messages.append(
                    {"role": "assistant", "content": None, "tool_call": {"name": call.name, "arguments": call.arguments}}
                )
                messages.append(
                    {"role": "tool", "name": call.name, "content": json.dumps(result)}
                )

        # Guardrail: ran out of iterations/budget without answering -> force a final turn.
        if final_answer is None:
            messages.append(
                {"role": "user", "content": "Answer now with what you have, or say you don't know."}
            )
            resp = self.llm.chat(messages, tools=None)
            tokens_in += resp.tokens_in
            tokens_out += resp.tokens_out
            final_answer = resp.content or "I don't know."
            trace.step("reason", {"decision": "forced_final"}, latency_ms=0)

        # Stream the final answer to the client token-by-token.
        for tok in _tokenize_for_stream(final_answer):
            yield "token", {"text": tok}

        trace.step("final", {"tokens_in": tokens_in, "tokens_out": tokens_out}, latency_ms=0)

        cost = estimate_cost(tokens_in, tokens_out, cfg)
        trace.finalize(
            iterations=iterations,
            used_web=1 if used_web else 0,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost=cost,
            status="ok",
        )

        yield "final", {
            "answer": final_answer,
            "sources": registry.collected_sources,
            "trace_id": trace.id,
            "used_web": used_web,
            "iterations": iterations,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost": cost,
        }


def _summarize(result: dict) -> str:
    if "error" in result:
        return f"error: {result['error']}"
    if "results" in result:
        return f"{len(result['results'])} result(s)"
    if "content" in result:
        return f"{len(result['content'])} chars extracted"
    return "ok"


def _tokenize_for_stream(text: str):
    import re

    return re.findall(r"\S+\s*", text)

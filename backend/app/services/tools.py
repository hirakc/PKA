"""Tool registry — the agent's typed API (US-7, LLD section 4).

AI-concept note (function calling + the tool boundary): the LLM can only *request*
an action by naming a tool and its arguments. The backend validates and executes it.
The model never touches the database or the network directly — this boundary is the
safety layer of an agentic system. Each tool also appends to ``collected_sources`` so
citations can later be attributed (US-10).
"""

from __future__ import annotations

from .. import providers
from ..providers.base import ToolSpec
from .retrieval import Retriever


class ToolError(Exception):
    pass


class ToolRegistry:
    def __init__(self, web_enabled: bool):
        self.web_enabled = web_enabled
        self.retriever = Retriever()
        self.web = providers.make_web_search()
        # Sources collected across the whole run, in call order. The final answer's
        # [n] markers map onto this list (1-indexed).
        self.collected_sources: list[dict] = []

    def specs(self) -> list[ToolSpec]:
        specs = [
            ToolSpec(
                name="search_docs",
                description="Search the user's private documents for relevant passages.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "What to look for"},
                        "k": {"type": "integer", "description": "How many passages"},
                    },
                    "required": ["query"],
                },
            )
        ]
        if self.web_enabled:
            specs.append(
                ToolSpec(
                    name="search_web",
                    description="Search the public web when the documents are insufficient.",
                    parameters={
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"],
                    },
                )
            )
            specs.append(
                ToolSpec(
                    name="fetch_url",
                    description="Fetch and extract the readable text of a web page.",
                    parameters={
                        "type": "object",
                        "properties": {"url": {"type": "string"}},
                        "required": ["url"],
                    },
                )
            )
        return specs

    def dispatch(self, name: str, args: dict) -> dict:
        if name == "search_docs":
            return self._search_docs(args)
        if name == "search_web":
            if not self.web_enabled:
                raise ToolError("web search is disabled")
            return self._search_web(args)
        if name == "fetch_url":
            if not self.web_enabled:
                raise ToolError("web fetch is disabled")
            return self._fetch_url(args)
        raise ToolError(f"unknown tool: {name}")

    def _search_docs(self, args: dict) -> dict:
        query = args.get("query", "")
        results = self.retriever.search_docs(query, args.get("k"))
        for r in results:
            self.collected_sources.append(
                {
                    "source_type": "doc",
                    "ref": r["chunk_id"],
                    "title": r["title"],
                    "location": r["location"],
                    "score": r.get("rerank_score", r.get("score")),
                }
            )
        return {"results": results}

    def _search_web(self, args: dict) -> dict:
        hits = self.web.search(args.get("query", ""))
        results = [
            {"title": h.title, "url": h.url, "snippet": h.snippet, "content": h.content}
            for h in hits
        ]
        for h in hits:
            self.collected_sources.append(
                {
                    "source_type": "web",
                    "ref": h.url,
                    "title": h.title,
                    "location": h.url,
                    "score": None,
                }
            )
        return {"results": results}

    def _fetch_url(self, args: dict) -> dict:
        res = self.web.fetch(args.get("url", ""))
        return {"url": res.url, "title": res.title, "content": res.content}

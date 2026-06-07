"""Web search providers (the agent's fallback tool).

AI-concept note (tool use as fallback + content extraction): when the private corpus
can't answer, the agent reaches outside itself. ``search_web`` returns a result list;
``fetch_url`` extracts clean readable text (clean text beats raw HTML for the LLM).
``MockWebSearch`` keeps the app fully offline for learning; ``TavilyWebSearch`` is the
real provider.
"""

from __future__ import annotations

import html
import re

from .. import config
from .base import WebResult


def _strip_html(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
    text = re.sub(r"(?s)<[^>]+>", " ", raw)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


class MockWebSearch:
    """Deterministic offline web search so the fallback path is exercisable."""

    def search(self, query: str, max_results: int = 5) -> list[WebResult]:
        topic = query.strip() or "your topic"
        samples = [
            WebResult(
                title=f"{topic} — overview",
                url=f"https://example.com/wiki/{re.sub(r'[^a-z0-9]+', '-', topic.lower())}",
                snippet=f"A general overview of {topic} with key facts and background.",
                content=(
                    f"{topic} is a subject of broad interest. This simulated web page "
                    f"summarizes commonly known points about {topic} for demonstration "
                    "of the web-fallback path. Replace MockWebSearch with TavilyWebSearch "
                    "for real results."
                ),
            ),
            WebResult(
                title=f"{topic} — frequently asked questions",
                url=f"https://example.org/faq/{re.sub(r'[^a-z0-9]+', '-', topic.lower())}",
                snippet=f"Common questions and concise answers about {topic}.",
                content=f"FAQ-style notes about {topic}, provided by the mock web provider.",
            ),
        ]
        return samples[:max_results]

    def fetch(self, url: str) -> WebResult:
        return WebResult(
            title=url,
            url=url,
            snippet="",
            content=f"Simulated extracted content for {url} (MockWebSearch).",
        )


class TavilyWebSearch:
    """Real web search + extraction via Tavily."""

    def search(self, query: str, max_results: int = 5) -> list[WebResult]:
        import httpx

        resp = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": config.TAVILY_API_KEY,
                "query": query,
                "max_results": max_results,
                "include_raw_content": False,
            },
            timeout=30,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return [
            WebResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("content", ""),
                content=r.get("content", ""),
            )
            for r in results
        ]

    def fetch(self, url: str) -> WebResult:
        import httpx

        resp = httpx.get(url, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        text = _strip_html(resp.text)
        title_match = re.search(r"(?is)<title>(.*?)</title>", resp.text)
        title = html.unescape(title_match.group(1).strip()) if title_match else url
        return WebResult(title=title, url=url, snippet=text[:300], content=text[:8000])

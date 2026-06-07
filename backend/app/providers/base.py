"""Provider interfaces (the swappable boundaries of the system)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


# --- LLM message / tool types ------------------------------------------------
@dataclass
class ToolSpec:
    """A tool advertised to the LLM (this is what enables function calling)."""

    name: str
    description: str
    parameters: dict  # JSON schema


@dataclass
class ToolCall:
    name: str
    arguments: dict
    call_id: str = ""


@dataclass
class LLMResponse:
    """The LLM returns *either* a final answer or one/more tool calls."""

    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0

    @property
    def is_final(self) -> bool:
        return not self.tool_calls


@runtime_checkable
class EmbeddingProvider(Protocol):
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


@runtime_checkable
class LLMClient(Protocol):
    def chat(
        self,
        messages: list[dict],
        tools: list[ToolSpec] | None = None,
        stream_tokens=None,
    ) -> LLMResponse:
        """Run one turn. ``tools`` enables function calling; ``stream_tokens`` is an
        optional callback ``(str) -> None`` invoked for each streamed token of a final
        answer."""
        ...


@runtime_checkable
class VectorStore(Protocol):
    def upsert(self, chunk_id: str, document_id: str, vector: list[float]) -> None: ...
    def search(self, vector: list[float], k: int) -> list[tuple[str, float]]: ...
    def delete_by_document(self, document_id: str) -> None: ...


@dataclass
class WebResult:
    title: str
    url: str
    snippet: str
    content: str = ""


@runtime_checkable
class WebSearchProvider(Protocol):
    def search(self, query: str, max_results: int = 5) -> list[WebResult]: ...
    def fetch(self, url: str) -> WebResult: ...


@runtime_checkable
class Reranker(Protocol):
    def rerank(self, query: str, items: list[dict]) -> list[dict]:
        """Return ``items`` reordered, each with an added ``rerank_score``."""
        ...

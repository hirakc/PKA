"""Provider abstractions + a factory that wires the configured implementations.

AI-concept note (provider abstraction): every external capability — embeddings,
the LLM, the vector store, web search, reranking — sits behind an interface. This
lets you swap *local/offline* defaults for *hosted/powerful* providers without
touching the rest of the app, and to compare the privacy-vs-quality spectrum.
"""

from __future__ import annotations

from .. import config
from .base import EmbeddingProvider, LLMClient, Reranker, VectorStore, WebSearchProvider
from .embeddings import HashingEmbeddingProvider, OpenAIEmbeddingProvider
from .llm import MockLLMClient, OpenAILLMClient
from .reranker import LexicalReranker, NoopReranker
from .vector_store import SqliteVectorStore
from .web_search import MockWebSearch, TavilyWebSearch


def make_embedding_provider() -> EmbeddingProvider:
    if config.EMBEDDING_PROVIDER == "openai" and config.OPENAI_API_KEY:
        return OpenAIEmbeddingProvider()
    return HashingEmbeddingProvider()


def make_llm_client() -> LLMClient:
    if config.LLM_PROVIDER == "openai" and config.OPENAI_API_KEY:
        return OpenAILLMClient()
    return MockLLMClient()


def make_vector_store() -> VectorStore:
    return SqliteVectorStore()


def make_web_search() -> WebSearchProvider:
    if config.WEB_SEARCH_PROVIDER == "tavily" and config.TAVILY_API_KEY:
        return TavilyWebSearch()
    return MockWebSearch()


def make_reranker() -> Reranker:
    if config.RERANKER == "lexical":
        return LexicalReranker()
    return NoopReranker()


__all__ = [
    "EmbeddingProvider",
    "LLMClient",
    "Reranker",
    "VectorStore",
    "WebSearchProvider",
    "make_embedding_provider",
    "make_llm_client",
    "make_vector_store",
    "make_web_search",
    "make_reranker",
]

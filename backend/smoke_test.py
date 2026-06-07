"""End-to-end smoke test of the backend with offline (mock) providers.

Exercises: ingestion -> retrieval -> agent ReAct loop -> tracing -> citations -> metrics.
Run: python smoke_test.py
"""

from __future__ import annotations

import os
import tempfile

# Use an isolated temp DB so the smoke test never touches real data.
os.environ["PKA_DATA_DIR"] = tempfile.mkdtemp(prefix="pka_smoke_")

from app.db import init_db  # noqa: E402
from app.repositories import DocumentRepository, TraceRepository  # noqa: E402
from app.services.chat import ChatService  # noqa: E402
from app.services.ingestion import IngestionService  # noqa: E402
from app.services.metrics import compute_metrics  # noqa: E402
from app.services.retrieval import Retriever  # noqa: E402


def collect_stream(gen) -> list[str]:
    return [frame for frame in gen]


def main() -> None:
    init_db()
    docs = DocumentRepository()
    ingest = IngestionService()

    # 1) Ingest two documents.
    doc1 = docs.create("RAG notes", "txt", None, "h1", 100)
    ingest.index_document(
        doc1,
        "Retrieval augmented generation grounds an LLM in retrieved chunks. "
        "Embeddings turn text into vectors so we can compare meaning. "
        "Reranking re-scores chunks for relevance to the question.",
    )
    doc2 = docs.create("Agents notes", "txt", None, "h2", 100)
    ingest.index_document(
        doc2,
        "An agent runs a ReAct loop: reason, act with tools, observe, repeat. "
        "Guardrails like a max iteration cap keep the loop safe and cheap.",
    )
    assert docs.get(doc1)["status"] == "Indexed", "doc1 should be indexed"
    print("[1] ingestion ok: 2 docs indexed")

    # 2) Retrieval finds the right chunk.
    hits = Retriever().search_docs("What is reranking?")
    assert hits, "expected retrieval hits"
    assert "rerank" in hits[0]["text"].lower() or "rank" in hits[0]["text"].lower()
    print(f"[2] retrieval ok: top score={hits[0]['rerank_score']} title={hits[0]['title']!r}")

    # 3) Agentic chat answering from documents (web off).
    frames = collect_stream(
        ChatService().stream(None, "What is a ReAct loop?", web_enabled=False)
    )
    assert any("tool_call" in f for f in frames), "agent should call a tool"
    done = [f for f in frames if "event: done" in f][-1]
    assert "citations" in done
    print("[3] agent (docs) ok: streamed tool_call + token + done with citations")

    # 4) Web fallback for an out-of-corpus question (web on).
    frames = collect_stream(
        ChatService().stream(None, "Who won the 2026 world cup final?", web_enabled=True)
    )
    assert any("search_web" in f for f in frames), "agent should fall back to web"
    print("[4] web fallback ok: agent called search_web")

    # 5) Tracing recorded steps; metrics aggregate.
    traces = TraceRepository().list()
    assert traces, "expected traces"
    trace = TraceRepository().get(traces[0]["id"])
    assert trace["steps"], "trace should have ordered steps"
    kinds = [s["kind"] for s in trace["steps"]]
    print(f"[5] tracing ok: latest trace has {len(trace['steps'])} steps: {kinds}")

    m = compute_metrics(days=7)
    assert m["total_queries"] >= 2
    print(
        f"[6] metrics ok: queries={m['total_queries']} "
        f"web_fallback_rate={m['web_fallback_rate']} avg_iters={m['avg_iterations']}"
    )

    print("\nALL SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()

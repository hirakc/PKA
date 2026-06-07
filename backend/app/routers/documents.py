"""Documents API: ingest, list, preview, reindex, delete (UC-2, UC-8)."""

from __future__ import annotations

import os

from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, UploadFile

from ..repositories import ChunkRepository, DocumentRepository
from ..services.ingestion import IngestionService, content_hash, fetch_url, parse_bytes

router = APIRouter(prefix="/api/documents", tags=["documents"])

_EXT_TO_TYPE = {".pdf": "pdf", ".md": "md", ".markdown": "md", ".txt": "txt", ".html": "html", ".htm": "html"}


def _index_text(doc_id: str, raw_text: str):
    IngestionService().index_document(doc_id, raw_text)


def _index_url(doc_id: str, url: str):
    svc = IngestionService()
    try:
        raw = fetch_url(url)
    except Exception as exc:
        DocumentRepository().set_status(doc_id, "Failed", error=f"fetch failed: {exc}")
        return
    svc.index_document(doc_id, raw)


@router.post("", status_code=202)
async def add_document(
    background: BackgroundTasks,
    file: UploadFile | None = None,
    url: str | None = Form(default=None),
    text: str | None = Form(default=None),
    title: str | None = Form(default=None),
):
    docs = DocumentRepository()

    if file is not None:
        data = await file.read()
        ext = os.path.splitext(file.filename or "")[1].lower()
        doc_type = _EXT_TO_TYPE.get(ext, "txt")
        try:
            raw_text = parse_bytes(data, doc_type)
        except Exception as exc:
            raise HTTPException(400, f"could not parse file: {exc}")
        chash = content_hash(raw_text)
        existing = docs.find_by_hash(chash)
        if existing:
            return {"id": existing["id"], "status": existing["status"], "deduped": True}
        doc_id = docs.create(title or file.filename or "Untitled", doc_type, file.filename, chash, len(data))
        background.add_task(_index_text, doc_id, raw_text)
        return {"id": doc_id, "status": "Queued", "deduped": False}

    if url:
        doc_id = docs.create(title or url, "url", url, None, 0)
        background.add_task(_index_url, doc_id, url)
        return {"id": doc_id, "status": "Queued", "deduped": False}

    if text:
        chash = content_hash(text)
        existing = docs.find_by_hash(chash)
        if existing:
            return {"id": existing["id"], "status": existing["status"], "deduped": True}
        doc_id = docs.create(title or "Pasted text", "txt", None, chash, len(text))
        background.add_task(_index_text, doc_id, text)
        return {"id": doc_id, "status": "Queued", "deduped": False}

    raise HTTPException(400, "provide a file, url, or text")


@router.get("")
def list_documents():
    return {"documents": DocumentRepository().list()}


@router.get("/{doc_id}/preview")
def preview_document(doc_id: str):
    doc = DocumentRepository().get(doc_id)
    if not doc:
        raise HTTPException(404, "not found")
    chunks = ChunkRepository()
    conn_rows = chunks_for_preview(doc_id)
    return {"document": doc, "chunks": conn_rows}


def chunks_for_preview(doc_id: str, limit: int = 20):
    from ..db import get_conn

    rows = get_conn().execute(
        "SELECT id, text, location, seq FROM chunks WHERE document_id=? ORDER BY seq ASC LIMIT ?",
        (doc_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


@router.post("/{doc_id}/reindex", status_code=202)
def reindex_document(doc_id: str, background: BackgroundTasks):
    docs = DocumentRepository()
    doc = docs.get(doc_id)
    if not doc:
        raise HTTPException(404, "not found")
    # Re-derive text: from URL re-fetch, otherwise from stored chunks.
    if doc["type"] == "url" and doc["source_uri"]:
        background.add_task(_reindex_url, doc_id, doc["source_uri"])
    else:
        raw = _reconstruct_text(doc_id)
        background.add_task(_reindex_text, doc_id, raw)
    docs.set_status(doc_id, "Queued")
    return {"id": doc_id, "status": "Queued"}


def _reconstruct_text(doc_id: str) -> str:
    return "\n\n".join(c["text"] for c in chunks_for_preview(doc_id, limit=100000))


def _reindex_text(doc_id: str, raw: str):
    IngestionService().reindex(doc_id, raw)


def _reindex_url(doc_id: str, url: str):
    try:
        raw = fetch_url(url)
    except Exception as exc:
        DocumentRepository().set_status(doc_id, "Failed", error=f"fetch failed: {exc}")
        return
    IngestionService().reindex(doc_id, raw)


@router.delete("/{doc_id}")
def delete_document(doc_id: str):
    docs = DocumentRepository()
    if not docs.get(doc_id):
        raise HTTPException(404, "not found")
    # Cascade removes chunks + vectors (FK ON DELETE CASCADE), making the source
    # immediately unsearchable (UC-8 acceptance).
    IngestionService().vectors.delete_by_document(doc_id)
    docs.delete(doc_id)
    return {"deleted": doc_id}

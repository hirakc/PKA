"""Data-access layer (thin CRUD over SQLite).

Keeping persistence in one place means every feature — chat, ingestion, tracing,
monitoring — shares one source of truth (the schema in ``db.py``).
"""

from __future__ import annotations

import json

from .config import DEFAULT_SETTINGS, Settings
from .db import get_conn
from .util import new_id, now_iso


# --- Documents & chunks ------------------------------------------------------
class DocumentRepository:
    def create(self, title, type_, source_uri, content_hash, size) -> str:
        doc_id = new_id("doc_")
        get_conn().execute(
            "INSERT INTO documents (id,title,type,source_uri,content_hash,added_at,status,size,chunk_count)"
            " VALUES (?,?,?,?,?,?,?,?,0)",
            (doc_id, title, type_, source_uri, content_hash, now_iso(), "Queued", size),
        )
        get_conn().commit()
        return doc_id

    def set_status(self, doc_id, status, error=None, chunk_count=None):
        conn = get_conn()
        if chunk_count is not None:
            conn.execute(
                "UPDATE documents SET status=?, error=?, chunk_count=? WHERE id=?",
                (status, error, chunk_count, doc_id),
            )
        else:
            conn.execute(
                "UPDATE documents SET status=?, error=? WHERE id=?", (status, error, doc_id)
            )
        conn.commit()

    def get(self, doc_id):
        row = get_conn().execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
        return dict(row) if row else None

    def find_by_hash(self, content_hash):
        row = get_conn().execute(
            "SELECT * FROM documents WHERE content_hash=?", (content_hash,)
        ).fetchone()
        return dict(row) if row else None

    def list(self):
        rows = get_conn().execute(
            "SELECT * FROM documents ORDER BY added_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def delete(self, doc_id):
        conn = get_conn()
        conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))
        conn.commit()


class ChunkRepository:
    def add(self, document_id, text, location, token_count, seq) -> str:
        chunk_id = new_id("chk_")
        get_conn().execute(
            "INSERT INTO chunks (id,document_id,text,location,token_count,seq) VALUES (?,?,?,?,?,?)",
            (chunk_id, document_id, text, location, token_count, seq),
        )
        get_conn().commit()
        return chunk_id

    def get_many(self, chunk_ids):
        if not chunk_ids:
            return {}
        marks = ",".join("?" for _ in chunk_ids)
        rows = get_conn().execute(
            f"SELECT c.*, d.title AS doc_title FROM chunks c JOIN documents d ON d.id=c.document_id"
            f" WHERE c.id IN ({marks})",
            list(chunk_ids),
        ).fetchall()
        return {r["id"]: dict(r) for r in rows}

    def delete_by_document(self, document_id):
        conn = get_conn()
        conn.execute("DELETE FROM chunks WHERE document_id=?", (document_id,))
        conn.commit()


# --- Conversations & messages ------------------------------------------------
class ConversationRepository:
    def create(self, title) -> str:
        cid = new_id("cnv_")
        ts = now_iso()
        get_conn().execute(
            "INSERT INTO conversations (id,title,created_at,updated_at) VALUES (?,?,?,?)",
            (cid, title, ts, ts),
        )
        get_conn().commit()
        return cid

    def touch(self, cid):
        get_conn().execute(
            "UPDATE conversations SET updated_at=? WHERE id=?", (now_iso(), cid)
        )
        get_conn().commit()

    def get(self, cid):
        row = get_conn().execute("SELECT * FROM conversations WHERE id=?", (cid,)).fetchone()
        return dict(row) if row else None

    def list(self, search: str | None = None):
        if search:
            like = f"%{search}%"
            rows = get_conn().execute(
                "SELECT DISTINCT c.* FROM conversations c LEFT JOIN messages m ON m.conversation_id=c.id"
                " WHERE c.title LIKE ? OR m.content LIKE ? ORDER BY c.updated_at DESC",
                (like, like),
            ).fetchall()
        else:
            rows = get_conn().execute(
                "SELECT * FROM conversations ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]


class MessageRepository:
    def add(self, conversation_id, role, content) -> str:
        mid = new_id("msg_")
        get_conn().execute(
            "INSERT INTO messages (id,conversation_id,role,content,created_at) VALUES (?,?,?,?,?)",
            (mid, conversation_id, role, content, now_iso()),
        )
        get_conn().commit()
        return mid

    def list(self, conversation_id):
        rows = get_conn().execute(
            "SELECT * FROM messages WHERE conversation_id=? ORDER BY created_at ASC",
            (conversation_id,),
        ).fetchall()
        return [dict(r) for r in rows]


class CitationRepository:
    def add(self, message_id, source_type, ref, title, location, score, idx) -> str:
        cid = new_id("cit_")
        get_conn().execute(
            "INSERT INTO citations (id,message_id,source_type,ref,title,location,score,idx)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (cid, message_id, source_type, ref, title, location, score, idx),
        )
        get_conn().commit()
        return cid

    def list(self, message_id):
        rows = get_conn().execute(
            "SELECT * FROM citations WHERE message_id=? ORDER BY idx ASC", (message_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# --- Traces ------------------------------------------------------------------
class TraceRepository:
    def create(self, conversation_id, query, model) -> str:
        tid = new_id("trc_")
        get_conn().execute(
            "INSERT INTO traces (id,conversation_id,query,model,status,created_at)"
            " VALUES (?,?,?,?,?,?)",
            (tid, conversation_id, query, model, "running", now_iso()),
        )
        get_conn().commit()
        return tid

    def add_step(self, trace_id, seq, kind, tool_name, latency_ms, detail) -> str:
        sid = new_id("stp_")
        get_conn().execute(
            "INSERT INTO trace_steps (id,trace_id,seq,kind,tool_name,latency_ms,detail)"
            " VALUES (?,?,?,?,?,?,?)",
            (sid, trace_id, seq, kind, tool_name, latency_ms, json.dumps(detail)),
        )
        get_conn().commit()
        return sid

    def finalize(self, trace_id, **fields):
        if not fields:
            return
        cols = ",".join(f"{k}=?" for k in fields)
        get_conn().execute(
            f"UPDATE traces SET {cols} WHERE id=?", (*fields.values(), trace_id)
        )
        get_conn().commit()

    def get(self, trace_id):
        row = get_conn().execute("SELECT * FROM traces WHERE id=?", (trace_id,)).fetchone()
        if not row:
            return None
        trace = dict(row)
        steps = get_conn().execute(
            "SELECT * FROM trace_steps WHERE trace_id=? ORDER BY seq ASC", (trace_id,)
        ).fetchall()
        trace["steps"] = [
            {**dict(s), "detail": json.loads(s["detail"]) if s["detail"] else {}}
            for s in steps
        ]
        return trace

    def list(self, source: str | None = None, status: str | None = None, search: str | None = None, limit: int = 200):
        clauses, params = [], []
        if source == "web":
            clauses.append("used_web=1")
        elif source == "documents":
            clauses.append("used_web=0")
        if status == "errors":
            clauses.append("status='error'")
        if search:
            clauses.append("query LIKE ?")
            params.append(f"%{search}%")
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = get_conn().execute(
            f"SELECT * FROM traces{where} ORDER BY created_at DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
        return [dict(r) for r in rows]


class FeedbackRepository:
    def add(self, message_id, trace_id, rating, note) -> str:
        fid = new_id("fbk_")
        get_conn().execute(
            "INSERT INTO feedback (id,message_id,trace_id,rating,note,created_at) VALUES (?,?,?,?,?,?)",
            (fid, message_id, trace_id, rating, note, now_iso()),
        )
        get_conn().commit()
        return fid

    def for_message(self, message_id):
        rows = get_conn().execute(
            "SELECT * FROM feedback WHERE message_id=? ORDER BY created_at DESC", (message_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def recent(self, limit=100):
        rows = get_conn().execute(
            "SELECT * FROM feedback ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


class SettingsRepository:
    def get(self) -> Settings:
        row = get_conn().execute("SELECT data FROM settings WHERE id=1").fetchone()
        if not row:
            return Settings()
        data = json.loads(row["data"])
        merged = {**DEFAULT_SETTINGS.to_dict(), **data}
        return Settings(**{k: merged[k] for k in DEFAULT_SETTINGS.to_dict()})

    def save(self, settings: Settings) -> Settings:
        conn = get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO settings (id,data) VALUES (1,?)",
            (json.dumps(settings.to_dict()),),
        )
        conn.commit()
        return settings

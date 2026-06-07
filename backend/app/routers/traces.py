"""Traces API — log explorer + single-trace waterfall (UC-6, UC-7) + export (FR-18)."""

from __future__ import annotations

import csv
import io
import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse, Response

from ..repositories import TraceRepository

router = APIRouter(prefix="/api/traces", tags=["traces"])


@router.get("")
def list_traces(
    source: str | None = Query(default=None),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
):
    return {"traces": TraceRepository().list(source=source, status=status, search=search)}


@router.get("/export")
def export_traces(format: str = Query(default="json")):
    rows = TraceRepository().list(limit=100000)
    if format == "csv":
        buf = io.StringIO()
        if rows:
            writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        return PlainTextResponse(
            buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=traces.csv"},
        )
    return Response(
        json.dumps(rows, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=traces.json"},
    )


@router.get("/{trace_id}")
def get_trace(trace_id: str):
    trace = TraceRepository().get(trace_id)
    if not trace:
        raise HTTPException(404, "not found")
    return trace

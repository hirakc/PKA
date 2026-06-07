"""Aggregate metrics (US-6, FR-16).

AI-concept note (LLMOps signals): the numbers that matter for an LLM system are
volume, latency *percentiles* (p50/p95, not just averages), cost, error rate, and —
for an agent — how many tool-loop iterations it takes and how often it used the web.
"""

from __future__ import annotations

from ..db import get_conn


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    idx = int(round((pct / 100) * (len(values) - 1)))
    return float(values[idx])


def compute_metrics(days: int = 7) -> dict:
    conn = get_conn()
    rows = conn.execute(
        "SELECT latency_ms, cost, used_web, status, iterations FROM traces"
        " WHERE created_at >= datetime('now', ?)",
        (f"-{days} days",),
    ).fetchall()
    rows = [dict(r) for r in rows]
    total = len(rows)
    latencies = [r["latency_ms"] for r in rows if r["latency_ms"]]
    errors = sum(1 for r in rows if r["status"] == "error")
    web = sum(1 for r in rows if r["used_web"])
    iters = [r["iterations"] for r in rows if r["iterations"]]

    by_day = {}
    day_rows = conn.execute(
        "SELECT substr(created_at,1,10) AS day, COUNT(*) c, SUM(cost) cost FROM traces"
        " WHERE created_at >= datetime('now', ?) GROUP BY day ORDER BY day",
        (f"-{days} days",),
    ).fetchall()
    for d in day_rows:
        by_day[d["day"]] = {"queries": d["c"], "cost": round(d["cost"] or 0, 6)}

    return {
        "window_days": days,
        "total_queries": total,
        "p50_latency_ms": _percentile(latencies, 50),
        "p95_latency_ms": _percentile(latencies, 95),
        "total_cost": round(sum(r["cost"] or 0 for r in rows), 6),
        "error_rate": round(errors / total, 4) if total else 0.0,
        "web_fallback_rate": round(web / total, 4) if total else 0.0,
        "doc_vs_web": {"documents": total - web, "web": web},
        "avg_iterations": round(sum(iters) / len(iters), 2) if iters else 0.0,
        "by_day": by_day,
    }

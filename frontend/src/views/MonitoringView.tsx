import { useEffect, useState } from "react";
import { api } from "../api";
import type { Metrics, TraceDetail, TraceRow } from "../types";

const FILTERS = [
  { id: "", label: "All" },
  { id: "documents", label: "Documents" },
  { id: "web", label: "Web" },
];

export function MonitoringView() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [traces, setTraces] = useState<TraceRow[]>([]);
  const [source, setSource] = useState("");
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<TraceDetail | null>(null);

  const loadMetrics = () => api.metrics(7).then(setMetrics);
  const loadTraces = () =>
    api.listTraces({ source, status, search }).then((r) => setTraces(r.traces));

  useEffect(() => {
    loadMetrics();
  }, []);
  useEffect(() => {
    loadTraces();
  }, [source, status, search]);

  async function openTrace(id: string) {
    setSelected(await api.getTrace(id));
  }

  return (
    <>
      <div className="header">
        <h1>Monitoring</h1>
        <span className="muted">Every query produces one inspectable trace</span>
        <div className="spacer" style={{ flex: 1 }} />
        <button className="btn secondary" onClick={() => api.exportTraces("csv")}>Export CSV</button>
        <button className="btn secondary" onClick={() => api.exportTraces("json")}>Export JSON</button>
      </div>
      <div className="content">
        {metrics && (
          <div className="metric-cards">
            <Card value={metrics.total_queries} label="Queries (7d)" />
            <Card value={`${Math.round(metrics.p95_latency_ms)}ms`} label="p95 latency" />
            <Card value={`$${metrics.total_cost.toFixed(4)}`} label="Total cost" />
            <Card value={`${(metrics.web_fallback_rate * 100).toFixed(0)}%`} label="Web fallback" />
            <Card value={`${(metrics.error_rate * 100).toFixed(0)}%`} label="Error rate" />
            <Card value={metrics.avg_iterations} label="Avg agent steps" />
          </div>
        )}

        <div className="row" style={{ marginBottom: 14 }}>
          {FILTERS.map((f) => (
            <button
              key={f.id}
              className={`btn secondary ${source === f.id ? "active" : ""}`}
              style={{ borderColor: source === f.id ? "var(--indigo)" : undefined }}
              onClick={() => setSource(f.id)}
            >
              {f.label}
            </button>
          ))}
          <button
            className="btn secondary"
            style={{ borderColor: status === "errors" ? "var(--red)" : undefined }}
            onClick={() => setStatus(status === "errors" ? "" : "errors")}
          >
            Errors
          </button>
          <input
            type="text"
            placeholder="Search queries…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ maxWidth: 240 }}
          />
        </div>

        <div className="panel">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Query</th>
                <th>Source</th>
                <th>Steps</th>
                <th>Latency</th>
                <th>Cost</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {traces.map((t) => (
                <tr key={t.id} className="clickable" onClick={() => openTrace(t.id)}>
                  <td className="muted">{new Date(t.created_at).toLocaleTimeString()}</td>
                  <td>{t.query?.slice(0, 60)}</td>
                  <td>
                    {t.used_web ? (
                      <span className="pill amber">Web</span>
                    ) : (
                      <span className="pill indigo">Docs</span>
                    )}
                  </td>
                  <td>{t.iterations}</td>
                  <td>{t.latency_ms}ms</td>
                  <td>${(t.cost || 0).toFixed(5)}</td>
                  <td>
                    {t.status === "error" ? (
                      <span className="pill red">error</span>
                    ) : (
                      <span className="pill green">ok</span>
                    )}
                  </td>
                </tr>
              ))}
              {traces.length === 0 && (
                <tr>
                  <td colSpan={7} className="muted">No traces yet — ask something in Chat.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {selected && <TraceWaterfall trace={selected} onClose={() => setSelected(null)} />}
      </div>
    </>
  );
}

function Card({ value, label }: { value: React.ReactNode; label: string }) {
  return (
    <div className="metric-card">
      <div className="value">{value}</div>
      <div className="label">{label}</div>
    </div>
  );
}

function TraceWaterfall({ trace, onClose }: { trace: TraceDetail; onClose: () => void }) {
  return (
    <div className="panel" style={{ marginTop: 16 }}>
      <div className="row">
        <h3 style={{ margin: 0 }}>Trace · {trace.query?.slice(0, 50)}</h3>
        <div className="spacer" style={{ flex: 1 }} />
        <button className="feedback-btn" onClick={onClose}>Close</button>
      </div>
      <div className="answer-footer" style={{ marginBottom: 12 }}>
        <span>model: {trace.model}</span>
        <span>{trace.iterations} iterations</span>
        <span>{trace.tokens_in + trace.tokens_out} tokens</span>
        <span>${(trace.cost || 0).toFixed(5)}</span>
        <span>{trace.latency_ms}ms</span>
      </div>
      <div className="waterfall">
        {trace.steps.map((s) => (
          <div key={s.seq}>
            <div className="wf-step">
              <span className="seq">{s.seq}</span>
              <span className="pill indigo">{s.kind}</span>
              {s.tool_name && <code>{s.tool_name}</code>}
              <div className="spacer" style={{ flex: 1 }} />
              <span className="muted">{s.latency_ms}ms</span>
            </div>
            {Object.keys(s.detail || {}).length > 0 && (
              <div className="wf-detail">{JSON.stringify(s.detail, null, 2)}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { api } from "../api";
import type { Settings } from "../types";

export function SettingsView() {
  const [s, setS] = useState<Settings | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.getSettings().then(setS);
  }, []);

  if (!s) return <div className="content">Loading…</div>;

  function set<K extends keyof Settings>(key: K, value: Settings[K]) {
    setS((prev) => (prev ? { ...prev, [key]: value } : prev));
    setSaved(false);
  }

  async function save() {
    const updated = await api.saveSettings(s!);
    setS(updated);
    setSaved(true);
  }

  return (
    <>
      <div className="header">
        <h1>Settings</h1>
        <span className="muted">Tune models and agent guardrails (watch the effect in Monitoring)</span>
      </div>
      <div className="content">
        <div className="panel" style={{ maxWidth: 720 }}>
          <h3 style={{ marginTop: 0 }}>Models</h3>
          <div className="grid-2">
            <div className="field">
              <label>LLM model</label>
              <input type="text" value={s.model} onChange={(e) => set("model", e.target.value)} />
            </div>
            <div className="field">
              <label>Embedding model</label>
              <input
                type="text"
                value={s.embedding_model}
                onChange={(e) => set("embedding_model", e.target.value)}
              />
            </div>
          </div>

          <h3>Retrieval</h3>
          <div className="grid-2">
            <div className="field">
              <label>Top-k chunks</label>
              <input
                type="number"
                value={s.top_k}
                onChange={(e) => set("top_k", Number(e.target.value))}
              />
            </div>
            <div className="field">
              <label>Reranking</label>
              <label className="web-toggle">
                <input
                  type="checkbox"
                  checked={s.rerank_enabled}
                  onChange={(e) => set("rerank_enabled", e.target.checked)}
                />
                Enable reranker
              </label>
            </div>
          </div>

          <h3>Agent guardrails</h3>
          <div className="grid-2">
            <div className="field">
              <label>Max iterations</label>
              <input
                type="number"
                value={s.max_iterations}
                onChange={(e) => set("max_iterations", Number(e.target.value))}
              />
            </div>
            <div className="field">
              <label>Token budget</label>
              <input
                type="number"
                value={s.token_budget}
                onChange={(e) => set("token_budget", Number(e.target.value))}
              />
            </div>
          </div>
          <div className="field">
            <label className="web-toggle">
              <input
                type="checkbox"
                checked={s.web_enabled_default}
                onChange={(e) => set("web_enabled_default", e.target.checked)}
              />
              Enable web fallback by default
            </label>
          </div>

          <h3>Cost estimate (USD per 1K tokens)</h3>
          <div className="grid-2">
            <div className="field">
              <label>Input</label>
              <input
                type="number"
                step="0.00001"
                value={s.price_per_1k_input}
                onChange={(e) => set("price_per_1k_input", Number(e.target.value))}
              />
            </div>
            <div className="field">
              <label>Output</label>
              <input
                type="number"
                step="0.00001"
                value={s.price_per_1k_output}
                onChange={(e) => set("price_per_1k_output", Number(e.target.value))}
              />
            </div>
          </div>

          <div className="row">
            <button className="btn" onClick={save}>Save settings</button>
            {saved && <span className="pill green">Saved</span>}
          </div>
        </div>
      </div>
    </>
  );
}

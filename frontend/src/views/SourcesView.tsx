import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { DocumentRow } from "../types";

function statusPill(status: string) {
  if (status === "Indexed") return <span className="pill green">Indexed</span>;
  if (status === "Failed") return <span className="pill red">Failed</span>;
  return <span className="pill amber">{status}</span>;
}

export function SourcesView() {
  const [docs, setDocs] = useState<DocumentRow[]>([]);
  const [url, setUrl] = useState("");
  const [drag, setDrag] = useState(false);
  const [preview, setPreview] = useState<any>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = () => api.listDocuments().then((r) => setDocs(r.documents));

  useEffect(() => {
    load();
    // Poll so status pills advance Queued -> Parsing -> Indexed.
    const t = setInterval(load, 2000);
    return () => clearInterval(t);
  }, []);

  async function handleFiles(files: FileList | null) {
    if (!files) return;
    for (const f of Array.from(files)) await api.uploadFile(f);
    load();
  }

  async function addUrl() {
    if (!url.trim()) return;
    await api.addUrl(url.trim());
    setUrl("");
    load();
  }

  return (
    <>
      <div className="header">
        <h1>Sources</h1>
        <span className="muted">Your knowledge base</span>
      </div>
      <div className="content">
        <div
          className={`dropzone ${drag ? "drag" : ""}`}
          onClick={() => fileRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDrag(true);
          }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDrag(false);
            handleFiles(e.dataTransfer.files);
          }}
        >
          Drop PDF / Markdown / TXT / HTML here, or click to choose
          <input
            ref={fileRef}
            type="file"
            multiple
            accept=".pdf,.md,.markdown,.txt,.html,.htm"
            style={{ display: "none" }}
            onChange={(e) => handleFiles(e.target.files)}
          />
        </div>

        <div className="row" style={{ margin: "16px 0" }}>
          <input
            type="text"
            placeholder="…or paste a URL to ingest"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addUrl()}
          />
          <button className="btn" onClick={addUrl}>Add URL</button>
        </div>

        <div className="panel">
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Type</th>
                <th>Added</th>
                <th>Chunks</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.id}>
                  <td>{d.title}</td>
                  <td className="muted">{d.type}</td>
                  <td className="muted">{new Date(d.added_at).toLocaleDateString()}</td>
                  <td>{d.chunk_count}</td>
                  <td>
                    {statusPill(d.status)}
                    {d.status === "Failed" && d.error && (
                      <div className="muted" style={{ fontSize: 11 }}>{d.error}</div>
                    )}
                  </td>
                  <td>
                    <div className="row">
                      <button
                        className="feedback-btn"
                        onClick={async () => setPreview(await api.previewDocument(d.id))}
                      >
                        Preview
                      </button>
                      <button className="feedback-btn" onClick={() => api.reindex(d.id).then(load)}>
                        Reindex
                      </button>
                      <button
                        className="feedback-btn"
                        onClick={() => api.deleteDocument(d.id).then(load)}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {docs.length === 0 && (
                <tr>
                  <td colSpan={6} className="muted">No documents yet — add one above.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {preview && (
          <div className="panel" style={{ marginTop: 16 }}>
            <div className="row">
              <h3 style={{ margin: 0 }}>{preview.document.title}</h3>
              <div className="spacer" style={{ flex: 1 }} />
              <button className="feedback-btn" onClick={() => setPreview(null)}>Close</button>
            </div>
            {preview.chunks.map((c: any) => (
              <div key={c.id} style={{ marginTop: 10 }}>
                <span className="pill indigo">{c.location}</span>
                <p className="muted" style={{ marginTop: 4 }}>{c.text.slice(0, 280)}…</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

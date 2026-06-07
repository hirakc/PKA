import type {
  Conversation,
  DocumentRow,
  Metrics,
  Settings,
  TraceDetail,
  TraceRow,
} from "./types";

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const api = {
  // Documents
  listDocuments: () =>
    fetch("/api/documents").then((r) => json<{ documents: DocumentRow[] }>(r)),
  uploadFile: (file: File, title?: string) => {
    const fd = new FormData();
    fd.append("file", file);
    if (title) fd.append("title", title);
    return fetch("/api/documents", { method: "POST", body: fd }).then((r) => json(r));
  },
  addUrl: (url: string) => {
    const fd = new FormData();
    fd.append("url", url);
    return fetch("/api/documents", { method: "POST", body: fd }).then((r) => json(r));
  },
  addText: (text: string, title: string) => {
    const fd = new FormData();
    fd.append("text", text);
    fd.append("title", title);
    return fetch("/api/documents", { method: "POST", body: fd }).then((r) => json(r));
  },
  reindex: (id: string) =>
    fetch(`/api/documents/${id}/reindex`, { method: "POST" }).then((r) => json(r)),
  deleteDocument: (id: string) =>
    fetch(`/api/documents/${id}`, { method: "DELETE" }).then((r) => json(r)),
  previewDocument: (id: string) =>
    fetch(`/api/documents/${id}/preview`).then((r) => json(r)),

  // Traces & metrics
  listTraces: (params: { source?: string; status?: string; search?: string }) => {
    const q = new URLSearchParams();
    if (params.source) q.set("source", params.source);
    if (params.status) q.set("status", params.status);
    if (params.search) q.set("search", params.search);
    return fetch(`/api/traces?${q}`).then((r) => json<{ traces: TraceRow[] }>(r));
  },
  getTrace: (id: string) => fetch(`/api/traces/${id}`).then((r) => json<TraceDetail>(r)),
  metrics: (days = 7) => fetch(`/api/metrics?days=${days}`).then((r) => json<Metrics>(r)),
  exportTraces: (format: "csv" | "json") => {
    window.open(`/api/traces/export?format=${format}`, "_blank");
  },

  // Conversations
  listConversations: (search?: string) =>
    fetch(`/api/conversations${search ? `?search=${encodeURIComponent(search)}` : ""}`).then(
      (r) => json<{ conversations: Conversation[] }>(r)
    ),
  getConversation: (id: string) =>
    fetch(`/api/conversations/${id}`).then((r) => json(r)),

  // Feedback
  feedback: (message_id: string, trace_id: string | null, rating: number, note?: string) =>
    fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message_id, trace_id, rating, note }),
    }).then((r) => json(r)),

  // Settings
  getSettings: () => fetch("/api/settings").then((r) => json<Settings>(r)),
  saveSettings: (s: Partial<Settings>) =>
    fetch("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(s),
    }).then((r) => json<Settings>(r)),
};

export type SSEHandler = (event: string, data: any) => void;

/**
 * POST to /api/chat and parse the Server-Sent Events stream from the response body.
 * (EventSource only supports GET, so we read the ReadableStream manually.)
 */
export async function streamChat(
  body: { query: string; conversation_id?: string | null; web_enabled?: boolean },
  onEvent: SSEHandler
): Promise<void> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.body) throw new Error("no response body");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      let event = "message";
      let data = "";
      for (const line of frame.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (data) onEvent(event, JSON.parse(data));
    }
  }
}

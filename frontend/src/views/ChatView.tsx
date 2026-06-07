import { useEffect, useRef, useState } from "react";
import { api, streamChat } from "../api";
import type { ChatMessage, Citation, Conversation } from "../types";

function renderAnswer(text: string, citations: Citation[] = []) {
  // Replace [n] markers with colored pills (indigo=doc, amber=web).
  const byIdx = new Map(citations.map((c) => [c.idx, c]));
  const parts = text.split(/(\[\d+\])/g);
  return parts.map((part, i) => {
    const m = part.match(/^\[(\d+)\]$/);
    if (m) {
      const idx = Number(m[1]);
      const c = byIdx.get(idx);
      const cls = c?.source_type === "web" ? "cite web" : "cite doc";
      return (
        <span key={i} className={cls} title={c ? `${c.title}` : `source ${idx}`}>
          {idx}
        </span>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

export function ChatView() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [webEnabled, setWebEnabled] = useState(true);
  const [busy, setBusy] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [search, setSearch] = useState("");
  const [feedbackGiven, setFeedbackGiven] = useState<Record<string, number>>({});
  const endRef = useRef<HTMLDivElement>(null);

  const loadConversations = (q?: string) =>
    api.listConversations(q).then((r) => setConversations(r.conversations));

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function openConversation(id: string) {
    const r: any = await api.getConversation(id);
    setConversationId(id);
    setMessages(
      r.messages.map((m: any) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        citations: m.citations || [],
      }))
    );
  }

  function newChat() {
    setConversationId(null);
    setMessages([]);
  }

  async function send() {
    const query = input.trim();
    if (!query || busy) return;
    setInput("");
    setBusy(true);

    setMessages((m) => [...m, { role: "user", content: query }]);
    // Placeholder assistant message we fill as tokens stream in.
    const assistantIndex = messages.length + 1;
    setMessages((m) => [...m, { role: "assistant", content: "", steps: [] }]);

    let answer = "";
    try {
      await streamChat({ query, conversation_id: conversationId, web_enabled: webEnabled }, (event, data) => {
        setMessages((prev) => {
          const copy = [...prev];
          const a = { ...copy[assistantIndex] } as ChatMessage;
          if (event === "start") {
            if (!conversationId) setConversationId(data.conversation_id);
          } else if (event === "tool_call") {
            a.steps = [...(a.steps || []), { kind: "tool_call", tool: data.tool }];
          } else if (event === "tool_result") {
            a.steps = [
              ...(a.steps || []),
              { kind: "tool_result", tool: data.tool, summary: data.summary, status: data.status },
            ];
          } else if (event === "token") {
            answer += data.text;
            a.content = answer;
          } else if (event === "done") {
            a.id = data.message_id;
            a.content = data.answer;
            a.citations = data.citations;
            a.used_web = data.used_web;
            a.trace_id = data.trace_id;
            a.iterations = data.iterations;
            a.tokens_in = data.tokens_in;
            a.tokens_out = data.tokens_out;
            a.cost = data.cost;
          }
          copy[assistantIndex] = a;
          return copy;
        });
      });
    } catch (e) {
      setMessages((prev) => {
        const copy = [...prev];
        copy[assistantIndex] = { role: "assistant", content: `Error: ${String(e)}` };
        return copy;
      });
    } finally {
      setBusy(false);
      loadConversations();
    }
  }

  async function giveFeedback(msg: ChatMessage, rating: number) {
    if (!msg.id) return;
    await api.feedback(msg.id, msg.trace_id || null, rating);
    setFeedbackGiven((f) => ({ ...f, [msg.id!]: rating }));
  }

  const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
  const showWebBanner = lastAssistant?.used_web;

  return (
    <>
      <div className="header">
        <h1>Chat</h1>
        <span className="muted">Ask grounded questions about your documents</span>
        <div className="spacer" style={{ flex: 1 }} />
        <button className="btn secondary" onClick={newChat}>+ New chat</button>
      </div>
      <div className="content" style={{ display: "flex", gap: 20, height: "100%" }}>
        {/* History sidebar (UC-5) */}
        <div style={{ width: 220, flexShrink: 0 }}>
          <input
            type="text"
            placeholder="Search history…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              loadConversations(e.target.value);
            }}
            style={{ marginBottom: 10 }}
          />
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {conversations.map((c) => (
              <button
                key={c.id}
                className="rail-conv btn secondary"
                style={{ textAlign: "left", background: c.id === conversationId ? "var(--panel-2)" : undefined }}
                onClick={() => openConversation(c.id)}
              >
                {c.title}
              </button>
            ))}
            {conversations.length === 0 && <span className="muted">No conversations yet</span>}
          </div>
        </div>

        {/* Conversation */}
        <div className="chat-wrap" style={{ flex: 1 }}>
          {showWebBanner && (
            <div className="banner">
              No confident match in your documents — PKA searched the web. Web sources are shown in amber.
            </div>
          )}
          <div className="messages">
            {messages.map((m, i) => (
              <div key={i} className={`msg ${m.role}`}>
                <div className="bubble">
                  {m.role === "assistant" ? renderAnswer(m.content || "…", m.citations) : m.content}
                </div>

                {m.role === "assistant" && m.steps && m.steps.length > 0 && (
                  <div className="agent-activity">
                    {m.steps.map((s, j) => (
                      <div key={j} className="step">
                        {s.kind === "tool_call" ? "→ calling" : "✓ result from"} <code>{s.tool}</code>
                        {s.summary ? ` — ${s.summary}` : ""}
                      </div>
                    ))}
                  </div>
                )}

                {m.role === "assistant" && m.citations && m.citations.length > 0 && (
                  <div className="sources">
                    {m.citations.map((c) => (
                      <span key={c.idx} className={`source-chip ${c.source_type}`}>
                        <b>{c.idx}</b>
                        {c.source_type === "web" ? (
                          <a href={c.ref} target="_blank" rel="noreferrer" style={{ color: "inherit" }}>
                            {c.title}
                          </a>
                        ) : (
                          <span>{c.title} · {c.location}</span>
                        )}
                      </span>
                    ))}
                  </div>
                )}

                {m.role === "assistant" && m.id && (
                  <div className="answer-footer">
                    <span>{m.used_web ? "Web" : "Documents"}</span>
                    {typeof m.iterations === "number" && <span>{m.iterations} agent steps</span>}
                    {typeof m.tokens_in === "number" && (
                      <span>{m.tokens_in + (m.tokens_out || 0)} tokens</span>
                    )}
                    {typeof m.cost === "number" && <span>${m.cost.toFixed(5)}</span>}
                    <button
                      className={`feedback-btn ${feedbackGiven[m.id] === 1 ? "active" : ""}`}
                      onClick={() => giveFeedback(m, 1)}
                    >
                      👍
                    </button>
                    <button
                      className={`feedback-btn ${feedbackGiven[m.id] === -1 ? "active" : ""}`}
                      onClick={() => giveFeedback(m, -1)}
                    >
                      👎
                    </button>
                  </div>
                )}
              </div>
            ))}
            <div ref={endRef} />
          </div>

          <div className="composer">
            <textarea
              rows={2}
              placeholder="Ask a question…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
            />
            <label className="web-toggle">
              <input
                type="checkbox"
                checked={webEnabled}
                onChange={(e) => setWebEnabled(e.target.checked)}
              />
              Web
            </label>
            <button className="btn" onClick={send} disabled={busy}>
              {busy ? "…" : "Send"}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

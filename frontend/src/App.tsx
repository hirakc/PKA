import { useState } from "react";
import { ChatView } from "./views/ChatView";
import { SourcesView } from "./views/SourcesView";
import { MonitoringView } from "./views/MonitoringView";
import { SettingsView } from "./views/SettingsView";

type Tab = "chat" | "sources" | "monitoring" | "settings";

const TABS: { id: Tab; label: string }[] = [
  { id: "chat", label: "Chat" },
  { id: "sources", label: "Sources" },
  { id: "monitoring", label: "Monitoring" },
  { id: "settings", label: "Settings" },
];

export function App() {
  const [tab, setTab] = useState<Tab>("chat");

  return (
    <div className="app">
      <nav className="rail">
        <div className="brand">
          PKA
          <small>Personal Knowledge Assistant</small>
        </div>
        {TABS.map((t) => (
          <button
            key={t.id}
            className={tab === t.id ? "active" : ""}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
        <div className="spacer" />
        <div className="provider">Agentic RAG · local-first</div>
      </nav>
      <main className="main">
        {tab === "chat" && <ChatView />}
        {tab === "sources" && <SourcesView />}
        {tab === "monitoring" && <MonitoringView />}
        {tab === "settings" && <SettingsView />}
      </main>
    </div>
  );
}

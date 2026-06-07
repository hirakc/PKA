export interface DocumentRow {
  id: string;
  title: string;
  type: string;
  source_uri: string | null;
  added_at: string;
  status: string;
  error: string | null;
  size: number;
  chunk_count: number;
}

export interface Citation {
  source_type: "doc" | "web";
  ref: string;
  title: string;
  location?: string | null;
  score?: number | null;
  idx: number;
}

export interface ChatMessage {
  id?: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  used_web?: boolean;
  trace_id?: string | null;
  iterations?: number;
  tokens_in?: number;
  tokens_out?: number;
  cost?: number;
  // Live agent activity shown while streaming.
  steps?: AgentStep[];
}

export interface AgentStep {
  kind: "tool_call" | "tool_result";
  tool: string;
  summary?: string;
  status?: string;
}

export interface TraceRow {
  id: string;
  query: string;
  model: string;
  iterations: number;
  used_web: number;
  tokens_in: number;
  tokens_out: number;
  cost: number;
  latency_ms: number;
  status: string;
  created_at: string;
}

export interface TraceStep {
  seq: number;
  kind: string;
  tool_name: string | null;
  latency_ms: number;
  detail: Record<string, unknown>;
}

export interface TraceDetail extends TraceRow {
  steps: TraceStep[];
}

export interface Metrics {
  window_days: number;
  total_queries: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  total_cost: number;
  error_rate: number;
  web_fallback_rate: number;
  doc_vs_web: { documents: number; web: number };
  avg_iterations: number;
  by_day: Record<string, { queries: number; cost: number }>;
}

export interface Settings {
  model: string;
  embedding_model: string;
  top_k: number;
  rerank_enabled: boolean;
  max_iterations: number;
  token_budget: number;
  web_enabled_default: boolean;
  price_per_1k_input: number;
  price_per_1k_output: number;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

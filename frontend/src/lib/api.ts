const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  let res: Response;
  try {
    res = await fetch(url, {
      headers: { "Content-Type": "application/json", ...options?.headers },
      ...options,
    });
  } catch (e) {
    const hint =
      typeof window !== "undefined" &&
      window.location.origin.startsWith("http://127.0.0.1")
        ? " You opened the app on 127.0.0.1 — the API must allow that origin (CORS) and NEXT_PUBLIC_API_URL must reach a running backend (try http://127.0.0.1:8000 if the API is bound to 127.0.0.1)."
        : " Start the API (e.g. uvicorn app.main:app from the backend folder) and ensure NEXT_PUBLIC_API_URL matches where it listens.";
    const msg = e instanceof Error ? e.message : String(e);
    throw new Error(`${msg} — cannot reach ${url}.${hint}`);
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Trades
  getTrades: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<Trade[]>(`/api/trades${qs}`);
  },
  getTrade: (id: string) => request<Trade>(`/api/trades/${id}`),
  createTrade: (data: TradeCreate) =>
    request<Trade>("/api/trades", { method: "POST", body: JSON.stringify(data) }),
  previewWebullTradeImport: (params?: { account_id?: string; strategy_name?: string }) => {
    const p = new URLSearchParams();
    if (params?.account_id) p.set("account_id", params.account_id);
    if (params?.strategy_name) p.set("strategy_name", params.strategy_name);
    const qs = p.toString() ? `?${p.toString()}` : "";
    return request<WebullTradeImportPreview>(`/api/trades/sync/webull/preview${qs}`);
  },
  importWebullTrades: (body?: { account_id?: string; strategy_name?: string }) =>
    request<WebullTradeImportResult>("/api/trades/sync/webull", {
      method: "POST",
      body: JSON.stringify(body ?? {}),
    }),
  closeTrade: (id: string, data: TradeClose) =>
    request<Trade>(`/api/trades/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  getSnapshots: (tradeId: string) =>
    request<Snapshot[]>(`/api/trades/${tradeId}/snapshots`),

  // Positions
  getPositions: () => request<Position[]>("/api/positions"),
  createPosition: (data: PositionCreate) =>
    request<Position>("/api/positions", { method: "POST", body: JSON.stringify(data) }),

  // Analytics
  getStrategyAnalysis: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<StrategyAnalysis[]>(`/api/analytics/strategy${qs}`);
  },
  getGreeksAnalysis: () => request<GreeksAnalysis>("/api/analytics/greeks"),
  getBehaviorAnalysis: () => request<BehaviorAnalysis>("/api/analytics/behavior"),

  // AI Insights
  chat: (message: string) =>
    request<{ response: string }>("/api/insights/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
  getInsightFeed: (limit = 20) =>
    request<InsightLog[]>(`/api/insights/feed?limit=${limit}`),
  generateInsights: () =>
    request<{ insights_generated: number }>("/api/insights/generate", { method: "POST" }),

  // Sentiment / Bets
  getWsbSentiment: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<SentimentData[]>(`/api/sentiment/wsb${qs}`);
  },
  getBets: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<Bet[]>(`/api/sentiment/bets${qs}`);
  },
  updateBet: (id: string, data: { status?: string; notes?: string }) =>
    request<Bet>(`/api/sentiment/bets/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  // Market Data
  getSnapshot: (symbol: string) => request<Record<string, unknown>>(`/api/market-data/snapshot/${symbol}`),
  getBars: (symbol: string, timespan = "D1") =>
    request<Record<string, unknown>>(`/api/market-data/bars/${symbol}?timespan=${timespan}`),
};

// --- Types ---

export interface WebullTradeImportPreview {
  error?: string;
  account_id?: string;
  accounts?: { account_id?: string }[];
  would_create: {
    position_id: string;
    symbol: string;
    quantity: number;
    direction: string;
    position_type: string;
    entry_price: number;
  }[];
  skipped: { reason: string; position_id?: string }[];
}

export interface WebullTradeImportResult {
  error?: string;
  account_id?: string;
  imported?: number;
  trade_ids?: string[];
}

export interface Trade {
  id: string;
  created_at: string;
  strategy_name: string;
  setup_classification: string | null;
  account: string;
  tags: string[] | null;
  webull_account_id?: string | null;
  webull_position_id?: string | null;
  entry_timestamp: string;
  underlying_symbol: string;
  entry_price: number;
  entry_iv: number | null;
  iv_rank: number | null;
  market_context: string | null;
  position_type: string;
  direction: string;
  quantity: number;
  max_risk: number | null;
  max_profit: number | null;
  buying_power_used: number | null;
  strike_price: number | null;
  expiration_date: string | null;
  premium: number | null;
  entry_delta: number | null;
  entry_gamma: number | null;
  entry_theta: number | null;
  entry_vega: number | null;
  exit_timestamp: string | null;
  exit_price: number | null;
  realized_pnl: number | null;
  realized_pnl_pct: number | null;
  trade_thesis: string;
  invalidation_conditions: string;
  exit_plan: Record<string, unknown> | null;
  post_review: Record<string, unknown> | null;
  status: string;
}

export interface TradeCreate {
  strategy_name: string;
  account: string;
  entry_timestamp: string;
  underlying_symbol: string;
  entry_price: number;
  position_type: string;
  direction: string;
  quantity: number;
  trade_thesis: string;
  entry_rationale: string;
  invalidation_conditions: string;
  [key: string]: unknown;
}

export interface TradeClose {
  exit_timestamp: string;
  exit_price: number;
  [key: string]: unknown;
}

export interface Snapshot {
  id: string;
  trade_id: string;
  timestamp: string;
  underlying_price: number;
  position_value: number;
  delta: number | null;
  gamma: number | null;
  theta: number | null;
  vega: number | null;
  iv: number | null;
}

export interface Position {
  id: string;
  symbol: string;
  quantity: number;
  avg_cost: number;
  current_value: number | null;
  unrealized_pnl: number | null;
  position_type: string;
  notes: string | null;
  updated_at: string;
}

export interface PositionCreate {
  symbol: string;
  quantity: number;
  avg_cost: number;
  position_type?: string;
  notes?: string;
}

export interface StrategyAnalysis {
  strategy_name: string;
  total_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  avg_pnl: number;
  avg_pnl_pct: number;
  total_pnl: number;
  expectancy: number;
}

export interface GreeksAnalysis {
  trades_analyzed: number;
  avg_entry_delta: number | null;
  details: Record<string, unknown>[];
}

export interface BehaviorAnalysis {
  total_trades: number;
  plan_adherence_rate: number | null;
  early_exits: number;
  late_exits: number;
  on_time_exits: number;
}

export interface InsightLog {
  id: string;
  insight_type: string;
  content: string;
  related_symbols: string[] | null;
  created_at: string;
}

export interface SentimentData {
  id: string;
  symbol: string;
  mention_count: number;
  avg_sentiment: number;
  top_posts: Record<string, unknown> | null;
  scraped_at: string;
  is_spike: boolean;
}

export interface Bet {
  id: string;
  symbol: string;
  source_post_ids: string[] | null;
  sentiment_score: number;
  mention_velocity: number | null;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

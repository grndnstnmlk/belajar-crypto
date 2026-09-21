/**
 * Market & Workstation TypeScript Type Definitions
 * Strictly typed interfaces for Apex Terminal / Belajar Kripto.
 */

export interface WatchlistItem {
  symbol: string;
  pair?: string;
  price: number;
  change_24h: number;
  is_leader?: boolean;
  rs_score?: number;
  high_24h?: number;
  low_24h?: number;
  volume?: number;
}

export interface Position {
  symbol: string;
  side: 'BUY' | 'SELL' | 'LONG' | 'SHORT';
  leverage: number;
  entry_price: number;
  mark_price: number;
  sl: number;
  tp: number;
  unrealized_pnl?: number;
  pnl_usd?: number;
  pnl?: number;
  ticket?: number | string;
  backend?: string;
  structural_level?: string;
}

export interface MacroAssetItem {
  symbol: string;
  name?: string;
  value?: number;
  price?: number;
  change_pct: number;
  state?: string;
  unit?: string;
}

export interface MacroAssets {
  mstr_stock?: MacroAssetItem;
  coinbase_stock?: MacroAssetItem;
  nasdaq_qqq?: MacroAssetItem;
  spx_500?: MacroAssetItem;
  gold_futures?: MacroAssetItem;
  dxy_index?: MacroAssetItem;
  us10y_yield?: MacroAssetItem;
}

export interface WallStreetSentiment {
  avg_equity_momentum_pct: number;
  sentiment: string;
  mstr_change_pct: number;
  coin_change_pct: number;
  qqq_change_pct: number;
}

export interface FeedData {
  positions: Position[];
  balance_usd: number;
  watchlist: WatchlistItem[];
  execution_backend: string;
  mode: string;
  is_paused: boolean;
  session?: {
    current_session: string;
    description: string;
    volatility: string;
  };
  news_shield?: {
    is_blackout: boolean;
    status: string;
    reason: string;
    next_event: string;
    next_time: string;
  };
  btc_regime?: {
    regime?: string;
    description?: string;
  };
  derivatives_sentiment?: Record<string, any>;
  onchain_fundamental?: Record<string, any>;
  cognitive_stream?: Array<{
    timestamp: string;
    thought: string;
    agent?: string;
  }>;
  recent_debates?: Array<{
    topic: string;
    verdict: string;
    timestamp: string;
  }>;
  wallstreet_sentiment?: WallStreetSentiment;
  macro_equities?: MacroAssets;
  last_sync?: string;
}

export interface IntelligenceData {
  compass?: {
    btc_dominance?: number;
    usdt_dominance?: number;
    eth_d?: number;
    sol_d?: number;
    regime_title?: string;
    advice?: string;
    alt_permission?: boolean;
    regime_code?: string;
  };
  heat?: {
    portfolio_heat_pct?: number;
    status?: string;
  };
  coinbase_premium?: {
    coinbase_price?: number;
    global_price?: number;
    premium_usd?: number;
    premium_pct?: number;
    regime?: string;
    is_us_inflow?: boolean;
  };
  derivatives?: {
    open_interest_formatted?: string;
    oi_change_1h_pct?: number;
    long_short_ratio?: number;
    long_pct?: number;
    short_pct?: number;
    funding_rate_pct?: number;
    total_liq_4h?: number;
    long_liq_dominance?: number;
    regime?: string;
  };
  liquidity?: {
    imbalance?: {
      bids_usd?: number;
      asks_usd?: number;
      total_depth_usd?: number;
      imbalance_ratio?: number;
      bid_share_pct?: number;
      ask_share_pct?: number;
      regime?: string;
    };
  };
  macro?: {
    fed_liquidity_billions?: number;
    fed_net_liquidity?: number;
    dxy?: { price?: number; change_pct?: number; state?: string };
    us10y?: { yield_pct?: number; change_pct?: number; state?: string };
    fear_and_greed?: { score?: number; classification?: string };
    macro_regime?: string;
    macro_label?: string;
    bias_detail?: string;
  };
  quant_risk?: {
    historical?: {
      var_95_usd?: number;
      cvar_95_usd?: number;
      max_drawdown_usd?: number;
      win_rate_pct?: number;
    };
  };
  sentiment_narrative?: {
    market_posture?: string;
  };
  wallstreet_sentiment?: WallStreetSentiment;
  macro_equities?: MacroAssets;
  onchain_fundamental?: Record<string, any>;
  jev_intelligence?: {
    symbol?: string;
    market?: string;
    conviction?: string;
    summary?: string;
    horizon_seconds?: number;
    decision?: {
      action?: 'buy' | 'sell' | 'hold';
      probabilities?: { buy?: number; sell?: number; hold?: number };
      up_in_10?: number;
      latency_ms?: number;
      engine?: string;
    };
    state?: {
      mid?: number;
      spreadBps?: number;
      bookImbalance?: number;
      depth?: Record<string, any>;
      book?: { bids?: string[]; asks?: string[] };
    };
  };
  timestamp?: string;
}

export interface JournalMetrics {
  win_rate_pct?: number;
  profit_factor?: number;
  math_expectancy?: number;
  payoff_ratio?: number;
  net_pnl_usd?: number;
  total_trades?: number;
  max_drawdown_pct?: number;
}

export interface JournalTrade {
  close_time: string;
  symbol: string;
  side: string;
  strategy: string;
  entry_price: number;
  exit_price: number;
  net_pnl?: number;
  realized_pnl?: number;
  r_multiple?: number;
  exit_reason?: string;
}

export interface StrategyMatrixItem {
  strategy: string;
  total_trades: number;
  win_loss: string;
  win_rate_pct: number;
  payoff_ratio: number;
  half_kelly: number;
  net_pnl: number;
  allocated_risk: string;
}

export interface KanbanTicket {
  id: string;
  title: string;
  stage: 'discovered' | 'debate' | 'risk' | 'board' | 'exec';
  agent: string;
  symbol?: string;
  side?: string;
  confidence?: number;
  notes?: string;
}

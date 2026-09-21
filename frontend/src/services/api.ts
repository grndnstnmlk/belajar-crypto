import type { FeedData, IntelligenceData, JournalMetrics, JournalTrade } from '../types/market';

const API_BASE = '';

export async function fetchFeed(): Promise<FeedData> {
  const res = await fetch(`${API_BASE}/api/feed`);
  if (!res.ok) throw new Error(`Feed fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchMarketIntelligence(): Promise<IntelligenceData> {
  const res = await fetch(`${API_BASE}/api/market_intelligence`);
  if (!res.ok) throw new Error(`Market intelligence fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchChartData(symbol = 'BTC', bar = '1H') {
  const res = await fetch(`${API_BASE}/api/klines?symbol=${encodeURIComponent(symbol)}&bar=${encodeURIComponent(bar)}`);
  if (!res.ok) throw new Error(`Chart fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchJournal(): Promise<{ metrics: JournalMetrics; ledger: JournalTrade[] }> {
  const res = await fetch(`${API_BASE}/api/journal`);
  if (!res.ok) throw new Error(`Journal fetch failed: ${res.statusText}`);
  return res.json();
}

export async function submitManualOrder(
  symbol: string,
  action: 'BUY' | 'SELL',
  riskPct: number,
  execMode: 'POST_ONLY' | 'LIMIT_CHASE' | 'MARKET' = 'POST_ONLY'
) {
  const res = await fetch(`${API_BASE}/api/action/manual_entry`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      symbol,
      action,
      risk_pct: riskPct,
      exec_mode: execMode,
      strategy: 'Manual Terminal Execution',
    }),
  });
  return res.json();
}

export async function closePosition(symbol: string) {
  const res = await fetch(`${API_BASE}/api/action/close`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol }),
  });
  return res.json();
}

export async function setBreakeven(symbol: string) {
  const res = await fetch(`${API_BASE}/api/action/breakeven`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol }),
  });
  return res.json();
}

export async function setTradingModeApi(mode: string) {
  const res = await fetch(`${API_BASE}/api/action/set_mode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode }),
  });
  return res.json();
}

export async function togglePauseApi() {
  const res = await fetch(`${API_BASE}/api/action/toggle_pause`, {
    method: 'POST',
  });
  return res.json();
}

export async function queryAiOfficer(query: string) {
  const res = await fetch(`${API_BASE}/api/ai/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  return res.json();
}

# Belajar Kripto — Data Pipelines & Execution Flows (Graft)

This document details how data moves through the workstation: from market feeds to order routing, risk checks, and telemetry.

---

## 1. Real-Time Market Feed Pipeline (< 0.05ms In-Memory RAM Cache)

```mermaid
sequenceDiagram
    participant BWS as Binance WebSocket Stream
    participant RAM as In-Memory Cache (_LIVE_MARK_PRICES / _LIVE_BOOK_TICKERS)
    participant TD as Trading Desk / Scalper
    participant DS as Dashboard Server (SSE)
    
    BWS->>RAM: Stream !markPrice@arr@1s and !bookTicker
    Note over RAM: Updated in RAM in < 0.05ms (Thread-Safe)
    TD->>RAM: get_mark_price(sym) & get_book_ticker(sym)
    RAM-->>TD: Instant Price (< 0.002ms)
    DS->>RAM: Poll for Live Watchlist & Spread
    RAM-->>DS: Zero-latency Data
```

---

## 2. Pre-Trade Execution Pipeline & Risk Haircuts

```mermaid
sequenceDiagram
    participant SC as Screener / Fast Scalper
    participant HTF as HTF Macro Lock Engine
    participant OF as Orderbook Delta Sniper
    participant AI as Local Cognitive Brain (Ollama)
    participant RISK as Nautilus & Dynamic Kelly
    participant BIN as Binance Client
    
    SC->>HTF: audit_htf_macro_bias(sym, side)
    Note over HTF: Check 4H/Daily EMA 50/200 & Funding Rate
    alt Trend Disallowed
        HTF-->>SC: VETO (Counter-trend setup rejected)
    else Trend Confirmed
        HTF-->>SC: APPROVED
        SC->>OF: check_order_book_depth(sym, qty, side)
        Note over OF: Level-2 Depth Imbalance >= 2.0x & CVD Absorption
        OF-->>SC: Liquidity Confirmed
        SC->>AI: conduct_cognitive_review(setup, ctx)
        Note over AI: GPU Accelerated DeepSeek-R1 Review (< 5s)
        AI-->>SC: APPROVE (Confidence >= 75%)
        SC->>RISK: calculate_position_size(equity, risk_pct, sl_pct)
        Note over RISK: Dynamic Proportional Floor (35% scalp / 30% swing)
        RISK-->>SC: Final pos_size_usd
        SC->>BIN: dispatch_order(sym, qty, side, type=LIMIT_CHASE)
        Note over BIN: Chase Limit Order for 1.0s, fallback to Market
    end
```

---

## 3. Post-Trade Lifecycle & Telemetry Persistence

1. **Order Fill**: `binance_client.py` captures execution ticket.
2. **Fast Position Watcher**: Background daemon thread monitors open positions every 8 seconds.
3. **Adaptive Profit Harvest & Micro-BE**:
   - At $+0.8	ext{R}$: Moves Stop Loss to Breakeven (Zero Capital Risk).
   - At $+1.5	ext{R}$: Harvests partial TP1 (40%).
   - At $+2.0	ext{R}$: `pyramiding_engine.py` evaluates adding +30% runner size.
4. **Trade Journal Logging**:
   - On position close, logs trade record to `data/trade_journal_ledger.json`.
   - Triggers `self_improve.py` (ATLAS Karpathy Autoresearch Loop) to update Sharpe ratio, win rate, and expectancy.
5. **Dashboard SSE Stream**:
   - `dashboard_server.py` pushes updated telemetry to `dashboard.html` over Server-Sent Events (`/api/stream/events`).

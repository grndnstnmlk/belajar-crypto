# AGENTS.md — Mission Control AI Development Guidelines

## Project Context
Belajar Kripto is an institutional-grade autonomous crypto trading and research workstation built around the **Akademi Crypto curriculum** and real-time **Binance Futures API**.

---

## 1. UI/UX & Frontend Standards (Mandatory)
Every visual modification to [`dashboard.html`](dashboard.html) must strictly adhere to [`DESIGN.md`](DESIGN.md):
- **Design Language**: GSAP® Animated Chalkboard in a Design Studio (`#0e100f` near-black wall, `#fffce1` warm cream text, 5-discipline color taxonomy).
- **Buttons**: Outlined Ghost Pills with `100px` radius; no solid-fill secondary buttons.
- **Cards**: Flat `8px` cards (`#141514`) with hairline `1px solid #282829` borders; no blurry drop-shadows.
- **Typography**: `-0.02em` tracking, signature `{ Section }` brackets.
- **Quality Standard**: Zero visual clutter, zero text wrapping on navigation bars, and complete test suite validation (`scratch/total_system_debug.py`).

---

## 2. Trading Engine & Risk Guardrails
- Autonomous trades execute on **Binance Futures Testnet (Demo)** on **20x Leverage** with strict **SMC Trailing Stops**, **Fractional Kelly Sizing (2.0%)**, and **Macro News Blackout Shields**.
- **Hard HTF Macro Bias Lock**: All trading desks must align strictly with 4H & Daily EMA 50/200 trends; counter-trend signals are discarded to eliminate 70%–80% of fakeout losses.
- **Monte Carlo Risk Engine**: 1,000-path bootstrap simulation regulates dynamic risk haircuts based on 95% VaR Drawdown.
- **Smart Pyramiding**: Adds +30% position size at +2R when Stop Loss is locked beyond Breakeven (Zero Capital Risk).
- **Regime-Adaptive Switcher**: Automatically switches strategy between Hyper-Trending (1:5R+ runners), Moderate Trend (1:3.5R), Ranging Consolidation (1:2.0R ORB), and Volatile Chop (Defensive Scalp).
- **Order Book Delta Sniping**: Reads Level-2 depth imbalance (>=2.5x) and CVD absorption to front-run limit walls and expand R:R to 1:5.0 - 1:8.0.
- **Dynamic Beta-Neutral Portfolio Hedge**: Calculates Net Portfolio Beta-Weighted Delta ($USD\Delta$) and deploys BTC Short Hedges during BTC flash crash shocks.
- High-frequency position monitoring runs via dedicated background watcher threads.
- All closed trades must be logged to the **Trade Journal** (`trade_journal_ledger.json`) with dynamic date filtering and today-first reporting.
- Every modification must pass all tests in `scratch/total_system_debug.py` with a 100% health score.

---

## 3. Active Custom Skills
- `design-taste-frontend`: Frontend taste and aesthetic excellence.
- `high-end-visual-design`: Agency-grade typography and spatial hierarchy.
- `crypto-trading-strategist`: Multi-timeframe confluence, SMC, and Wyckoff execution.
- `crypto-journal-tracker`: Quant metrics and performance analytics.

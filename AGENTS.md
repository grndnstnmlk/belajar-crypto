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
- Autonomous trades execute on **Binance Futures Testnet (Demo)** with strict **SMC Trailing Stops**, **Fractional Kelly Sizing**, and **Macro News Blackout Shields**.
- High-frequency position monitoring runs via dedicated background watcher threads.
- All closed trades must be logged to the **Trade Journal** (`trade_journal_ledger.json`) with dynamic date filtering and today-first reporting.

---

## 3. Active Custom Skills
- `design-taste-frontend`: Frontend taste and aesthetic excellence.
- `high-end-visual-design`: Agency-grade typography and spatial hierarchy.
- `crypto-trading-strategist`: Multi-timeframe confluence, SMC, and Wyckoff execution.
- `crypto-journal-tracker`: Quant metrics and performance analytics.

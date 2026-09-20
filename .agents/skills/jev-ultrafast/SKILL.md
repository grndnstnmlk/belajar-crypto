---
name: jev-ultrafast
description: Ultra-fast AI browser automation skill powered by Indexed Action Spaces and Chrome DevTools Protocol (CDP), synthesized from browser-use/jev-ultrafast and TypeSafe Jev. Enables AI agents to control web browsers, automate forms, scrape non-API financial data (TradingView, Coinglass, Arkham), and navigate complex UIs in seconds without slow DOM dumps or multi-turn reasoning lag.
---

# Jev-Ultrafast — Ultra-Fast Browser Automation Skill ⚡

Synthesized from [browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast) & [TypeSafe Jev](https://docs.typesafe.ai/).

This skill empowers AI coding and research agents (Gemini, Antigravity, Claude Code, Cursor) to automate web browsers with **sub-10-second completion speeds** using **Indexed Action Spaces**.

---

## 🏛️ Why Conventional Browser Agents Are Slow (And How Jev Solves It)

Standard browser agents take 30–90 seconds per task because they:
1. Dump entire DOMs (consuming 50k+ tokens).
2. Transmit high-resolution screenshots to vision models on every step (3–5s latency).
3. Suffer from multi-turn deliberation for every click.

**The Jev Ultrafast Paradigm**:
- **Indexed Element Table**: The DOM is rendered as a clean, numbered index of interactive targets:
  ```text
  [ 1] combobox  Symbol Search                              · empty
  [ 2] button    15m Timeframe                              
  [ 3] button    Camera Screenshot                          
  ```
- **Single Round-Trip Policy**: Selects the operation (`CLICK`, `TYPE_TEXT`, `SELECT`, `SCROLL_DOWN`, `WAIT`, `DONE`) and target ID in **one single speculative pass**.
- **Split-Brain Execution**: A fast LLM is only invoked to write text when the operation is `TYPE_TEXT`.

---

## 🛠️ Usage in Python (`fast_browser_automator`)

Use the bundled institutional tool located at [`.agents/tools/fast_browser_automator.py`](file:///.agents/tools/fast_browser_automator.py):

```python
from .agents.tools.fast_browser_automator import fast_browser

# 1. Capture TradingView Chart Snapshot
chart_data = fast_browser.capture_tradingview_chart(symbol="SOLUSDT", timeframe="15m")
print(chart_data["chart_image_url"])

# 2. Scrape Real-Time Liquidation Walls from Coinglass
liq_data = fast_browser.scrape_coinglass_liquidations(symbol="BTC")
print(liq_data["clusters"])

# 3. Profile Whale Wallets on Arkham Intelligence
whale_info = fast_browser.scrape_arkham_whale(wallet_address="0x123...abc")
print(whale_info["entity"])

# 4. General Goal Execution
result = fast_browser.execute_goal(
    url="https://app.uniswap.org",
    goal="Select ETH and swap to USDC"
)
```

---

## ⚡ Agent Operational Guidelines

When given a browser automation or web data extraction task:

1. **Prefer REST/WebSocket First**:
   If an official API exists (e.g. Binance Futures, DexScreener API), always use the direct API (<50ms).
2. **Use Jev for Web GUI & Non-API Targets**:
   When scraping platforms without public APIs (TradingView charts, Coinglass heatmaps, Arkham forensics, Indodax statement exports), use `fast_browser_automator`.
3. **Keep Goals Explicit & Atomic**:
   Formulate single-sentence intent goals:
   - ✅ *"Select 15m timeframe and click Camera icon"*
   - ✅ *"Type BTCUSDT into Search Ticker"*
   - ❌ *"Browse around and find me some good charts"*
4. **Inspect the Action Space Table**:
   Always verify element IDs before dispatching synthetic clicks to ensure 100% precision.

---

## 🔑 Configuration Options

- `TYPESAFE_API_KEY`: Optional. Enables cloud TypeSafe Jev model.
- `TEXT_MODEL_API_KEY` / `GEMINI_API_KEY`: Fast text generation key for `TYPE_TEXT` operations.
- Defaults to **Native Indexed CDP Mode** if no API keys are set.

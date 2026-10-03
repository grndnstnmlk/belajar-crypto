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
- **Ollama Real-Time Internet Web RAG & Continuous Learning**: Local AI Brain (`deepseek-r1:8b`) receives live web search and sentiment grounding (Cointelegraph, CoinDesk, Decrypt, Reddit, Jina Reader, Binance Vision) and autonomously runs continuous learning cycles committing discovered institutional tactics into `agent_memory_bank.json`.
- **Eight-Agent Desk Pipeline & Harvest Moon Retro Office**: Autonomous 8-agent swarm handoff pipeline (01 Search -> 02 Risk -> 03 Whale -> 04 Shill -> 05 Analyst -> 06 Head of Desk -> 07 Sniper -> 08 Journal) with real-time 16-bit Harvest Moon retro office visualization in `dashboard.html` and telemetry endpoint `/api/desk/eight_agents`.
- **Sentry Observability & Telemetry Engine**: Production error tracking, performance tracing, and local in-memory event buffer with automatic credential scrubbing (API keys, secrets, tokens). Telemetry endpoint at `/api/sentry/status` and diagnostic probe endpoint at `/api/sentry/test`.
- **AstraQuant 7-Tier Calculus & CIO Council Engine**: 7-tier continuous derivative microstructure matrix (T0 Settlement, T0.5 CVD Orderflow, T1 L2 Orderbook, T1.5 Options IV Smile & Skew, T2 Term Basis, T3 VWAP & POC, T4 Kinematics), 4-seat adversarial debate with CIO game-theoretic Paranoid Veto arbitration, 5-zone hierarchical prompt caching compiler, and dual-leg cloud OCO bracket planner (TP1 1.8x ATR, TP2 Runner with BE ratchet). Endpoints at `/api/astra/calculus`, `/api/astra/council`, and `/api/astra/summary`.
- **Coucou / Mochi Dynamic Island Companion Engine**: Interactive desktop & web agent companion modeled after Coucou's Mochi. Features organic eye tracking following cursor vector coordinates, natural blinking and idle breathing states, interactive poke reactions with rapid-poke dizziness threshold (4+ pokes within 2.5s), procedural Web Audio synthesizer chimes (`retroAudioCtx`), one-click action approval bridge (`allow`/`deny`), and Coucou hook protocol support (`coucou_agent`). Endpoints at `/api/coucou/status`, `/api/coucou/event`, and `/api/coucou/action`.
- **Whale / Smart-Money Copy Sniper Engine (MohammedRashad/Crypto-Copy-Trader)**: Master-Slave autonomous proportional copy trading engine synthesizing high-frequency whale tracking and institutional market makers (Wintermute, DWF Labs, GMX Whales). Incorporates microsecond slippage audit hurdles (< 15.0 bps / 0.15% adverse slippage gatekeeper to eliminate front-running/dumping), 4H/Daily HTF SMC macro bias lock, 20x Fractional Kelly sizing (1.5% capital risk), exchange quantity precision formatting, and Dual-Leg Cloud OCO brackets (TP1 1.8x ATR, TP2 Runner with BE ratchet). Endpoints at `/api/copy_trader/status`, `/api/copy_trader/trigger`, and `/api/copy_trader/config`.
- High-frequency position monitoring runs via dedicated background watcher threads.
- All closed trades must be logged to the **Trade Journal** (`trade_journal_ledger.json`) with dynamic date filtering and today-first reporting.
- Every modification must pass all tests in `scratch/total_system_debug.py` with a 100% health score.

---

## 3. Active Custom Skills
- `design-taste-frontend`: Frontend taste and aesthetic excellence.
- `high-end-visual-design`: Agency-grade typography and spatial hierarchy.
- `crypto-trading-strategist`: Multi-timeframe confluence, SMC, and Wyckoff execution.
- `crypto-journal-tracker`: Quant metrics and performance analytics.
- `smoothui-magicui-library`: Curated high-end SaaS component patterns from SmoothUI, Magic UI, Aceternity, Motion Primitives, and Origin UI.
- `antislop`: Core anti-AI-slop filter across UI, copywriting, and code.
- `graft`: Codebase knowledge graph and architectural context layer powered by Graft (trailhq/graft).
- `jev-ultrafast`: Ultra-fast AI browser automation using indexed action spaces for rapid web scraping and OSINT.
- `iris`: High-speed camera and visual verification skill for coding agents powered by Iris (brijr/iris).

<!-- antislop:start -->
## antislop
For UI, copy, people, mobile layout, or code comments work, read `.agents/skills/antislop/SKILL.md` (core) and then the skill for the task:
- UI / visual: `.agents/skills/antislop-ui/SKILL.md`
- Copy & text: `.agents/skills/antislop-copywriting/SKILL.md`
- People: `.agents/skills/antislop-human/SKILL.md`
- Mobile / responsive: `.agents/skills/antislop-layoutmobile/SKILL.md`
- Code comments: `.agents/skills/antislop-code/SKILL.md`
<!-- antislop:end -->

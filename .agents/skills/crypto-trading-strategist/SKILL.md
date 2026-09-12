---
name: crypto-trading-strategist
description: Master Crypto Trading & Research Strategy agent playbook synthesized from the entire Akademi Crypto curriculum (Fundamental, On-Chain, Smart Money Concepts, Order Flow, Wyckoff, Risk Management, Top-Down Analysis, and Execution). Use when analyzing crypto markets, auditing token fundamentals, generating trade setups, or formulating automated trading strategies.
---

# Crypto Trading & Research Strategist Playbook
*Synthesized from the Complete Akademi Crypto Curriculum (Modules 01 - 08)*

This skill provides an institutional-grade, rule-based framework for researching crypto assets, executing multi-timeframe technical analysis (SMC / Wyckoff / Order Flow), and managing trading risk with mathematical discipline.

---

## 🏛️ Core Principles & Golden Rules

1. **Risk First, Profit Second**: Capital preservation is paramount. Never risk more than **1% to 2%** of total account equity on any single trade.
2. **Trend & Liquidity Rule**: Never trade against higher-timeframe market structure. The market moves to hunt liquidity (Stop Loss pools / Liquidation clusters) before continuing its true direction.
3. **No Setup, No Trade**: If a token or chart does not pass the strict Pre-Flight Checklist, stay in stablecoins/cash. Cash is an active position.
4. **Separation of Investment vs Trading**:
   - **Spot Investing (Long-Term)**: High conviction (BTC/ETH 60-80%, Layer 1/2 leaders), DCA in bear market, hold through 4-year cycle.
   - **Trading (Short/Mid-Term)**: Strictly rule-based, defined Stop Loss, disciplined Take Profit, no emotional attachment.

---

## 📊 Phase 1: Macro & Market Regime Filter

Before taking any trade or investment position, evaluate the broad market climate:

### 1. 4-Year Bitcoin Cycle & Macro Liquidity
- **Cycle Stage**: Identify whether the market is in *Accumulation (Bear market floor)*, *Early Bull (Pre/Post Halving)*, *Euphoria/Markup (Parabolic)*, or *Distribution (Post-cycle peak)*.
- **Global Liquidity (M2)**: Crypto bull runs correlate with expanding global central bank balance sheets and interest rate cut cycles.

### 2. Capital Rotation Flow
Monitor the standard liquidity waterfall:
$$\text{Fiat / Stablecoins} \longrightarrow \text{Bitcoin (BTC)} \longrightarrow \text{Ethereum \& Major L1s} \longrightarrow \text{Mid-Cap Narratives} \longrightarrow \text{Small-Cap \& Meme Waves}$$

- **Bitcoin Dominance ($\text{BTC.D}$)**:
  - $\text{BTC.D}$ Rising + BTC Price Rising $\rightarrow$ Only trade BTC; Altcoins will bleed or lag.
  - $\text{BTC.D}$ Falling + BTC Consolidating/Rising $\rightarrow$ **Altcoin Season active**; focus on sector leaders.

### 3. Sector & Narrative Screening
- Identify the active dominant narratives (e.g., AI x Crypto, DePIN, Real World Assets (RWA), Solana/Ethereum Layer 2s).
- **Rule**: Buy when a narrative is in stealth accumulation or first breakout; take profit aggressively when mainstream hype peaks.

---

## 🔍 Phase 2: Fundamental & On-Chain Audit

Evaluate token health before considering technical setups:

| Metric / Check | Healthy / Bullish Criteria | Warning / Bearish Signal |
| :--- | :--- | :--- |
| **Market Cap vs FDV** | $\text{Mcap} / \text{FDV} \ge 0.60$ (High circulating supply) | $\text{Mcap} / \text{FDV} < 0.20$ (Massive incoming dilution) |
| **Token Unlocks** | No cliff unlock $> 3\%$ within next 14–30 days | Massive cliff unlock (>5% supply) imminent $\rightarrow$ Short/Avoid |
| **VC & Seed Price** | Current price near institutional entry or fair discount | Current price 50x–100x above Seed round with vesting active |
| **TVL & Revenue** | TVL growing, $\text{Mcap} / \text{TVL} < 1.5$, positive real protocol fee accrual | Fake transactions, wash trading, zero revenue flow to token |
| **Security & Contract** | Liquidity locked, mint revoked, 0% buy/sell tax, pass TokenSniffer/RugCheck | HoneyPot risk, blacklist function, mutable code |

---

## 📈 Phase 3: Technical Analysis & Execution Framework

### 1. Top-Down Analysis (TDA) Hierarchy
Always analyze charts from top to bottom:
1. **Weekly / Daily (Macro View)**: Determine overall trend (Bullish/Bearish/Range), key supply/demand zones, and major liquidity pools.
2. **4-Hour / 1-Hour (Structural View)**: Identify swing highs/lows, Market Structure Breaks (BOS), and unmitigated Order Blocks.
3. **15-Minute / 5-Minute (Execution Trigger)**: Look for Change of Character (CHoCH), Liquidity Sweeps, and tight Invalidation levels.

### 2. Smart Money Concepts (SMC) Setup Matrix
- **Order Block (OB)**: The last opposite candle before an impulsive move that broke market structure and created a Fair Value Gap (FVG).
  - *Bullish OB*: Last down candle before strong upward impulse breaking resistance.
  - *Bearish OB*: Last up candle before strong downward breakdown breaking support.
  - *Entry*: Limit order at the 50% equilibrium or open of an **unmitigated** OB with fresh FVG.
- **Fair Value Gap (FVG)**: 3-candle price imbalance where Candle 1 wick and Candle 3 wick do not overlap.
- **Liquidity Sweep (Judas Swing / Spring)**: Price quickly pierces previous Highs (Buy-side Liquidity) or Lows (Sell-side Liquidity) and rejects sharply with a long wick, trapping breakout retail traders.

### 3. Fibonacci Confluence
- Pull Fibonacci from Major Swing Low to Swing High (in uptrends):
  - **Golden Pocket Zone (0.618 – 0.65)**: Highest probability reversal bounce when overlapping with an Order Block or horizontal S/R flip.
  - **Extension Targets (1.272, 1.618, 2.618)**: Realistic Take Profit zones during price discovery.

### 4. Order Flow & Derivatives Confirmation
- **Open Interest (OI) & Price**:
  - Price $\uparrow$ + OI $\uparrow$ = Strong bullish continuation (Fresh long accumulation).
  - Price $\uparrow$ + OI $\downarrow$ = Short squeeze / weak rally (Likely reversal imminent).
- **Cumulative Volume Delta (CVD)**: Look for absorption divergence (e.g., Price makes Lower Low, but CVD makes Higher Low $\rightarrow$ Whale absorption).
- **Liquidation Heatmaps**: Price magnetically seeks large clusters of high-leverage liquidation levels before reversing.

---

## 🛡️ Phase 4: Strict Risk & Position Management (Non-Negotiable)

### 1. Position Sizing Formula
Never trade fixed coin quantities; calculate size strictly from risk:

$$\text{Position Size (\$) } = \frac{\text{Account Balance (\$) } \times \text{Risk \%}}{|\text{Entry Price} - \text{Stop Loss Price}| \div \text{Entry Price}}$$

*Example*: Account = $10,000, Risk = 1.5% ($150). Entry = $100, Stop Loss = $95 (5% distance).
$$\text{Position Size} = \frac{\$150}{0.05} = \$3,000$$

### 2. Execution Guardrails
- **Minimum Risk-to-Reward (R:R)**: $1 : 2.0$ minimum (Ideal $1 : 3+$).
- **Stop Loss Placement**: Must be set at the technical invalidation point (e.g., just below the low of the Order Block / Swing Low). **Never move Stop Loss further away once entered.**
- **Take Profit (Scale-Out Rule)**:
  - **TP 1 (1:1.5 to 1:2 R:R)**: Close 33% - 50% of position and move Stop Loss to Breakeven (Entry).
  - **TP 2 (Key Resistance / FVG Fill)**: Close 25% - 30% of position.
  - **TP 3 (Runner / Fibonacci Extension)**: Trail remaining position using trailing stop / 4H swing structure.

---

## 🤖 Phase 5: Agent Analysis & Output Template

When the user asks for a coin/market analysis, trade setup, or portfolio review, output the response using the following structured format:

```markdown
### 🎯 [COIN/USDT] — Strategy Analysis & Setup

#### 1. Fundamental & Narrative Context
- **Sector/Narrative**: [e.g., Layer 1, AI, DePIN, Meme]
- **Mcap / FDV / Unlock Status**: [Assessment of dilution and tokenomics]
- **Market Sentiment & Relative Strength**: [Strength vs BTC]

#### 2. Technical Confluence (Top-Down)
- **Higher Timeframe Trend (1D/4H)**: [Bullish / Bearish / Range]
- **Key Levels & SMC Structures**: [Order Block, FVG, Liquidity Pools identified]
- **Momentum & Volume/OI**: [Divergence, Open Interest condition]

#### 3. Actionable Trade Setup (If Valid)
- **Direction**: [LONG / SHORT / WATCHLIST WAIT]
- **Entry Range**: [$X.XX - $X.XX] (Confluence zone / OB)
- **Stop Loss**: [$X.XX] (Invalidation point — Risk: X.X%)
- **Take Profit Targets**:
  - TP1: [$X.XX] (R:R 1:1.5 - Lock initial profit & move SL to BE)
  - TP2: [$X.XX] (R:R 1:3.0)
  - TP3: [$X.XX] (Runner target / Fib Extension)
- **Risk-to-Reward Ratio**: [1 : X.X]
- **Max Recommended Position Risk**: [1.0% - 2.0%]

#### 4. Invalidation & Risk Warnings
- [Specific trigger that voids this setup, e.g., 4H candle close below $X.XX or upcoming high-impact token unlock]
```

---

## 🛠️ Phase 6: Agent Tools ("Mata & Tangan") Integration

The agent has access to dedicated execution tools inside the workspace:

### 1. 👁️ "Mata" (Live Market Intelligence)
Run [market_eyes.py](file:///c:/Users/USER/Downloads/Githubku/belajar%20kripto/.agents/tools/market_eyes.py) to pull live prices, 24h volume, perpetual funding rates, EMAs, RSI, and Fair Value Gaps (FVG):
```bash
python .agents/tools/market_eyes.py --symbol SOL --bar 4H
```

### 2. ✋ "Tangan" (Paper Trading Execution Engine)
Run [trade_hands.py](file:///c:/Users/USER/Downloads/Githubku/belajar%20kripto/.agents/tools/trade_hands.py) to open virtual positions, audit Stop Loss / Take Profit hits against live market feeds, and track PnL:
```bash
# Check current paper portfolio & open positions
python .agents/tools/trade_hands.py status

# Open a new trade with automatic live entry price
python .agents/tools/trade_hands.py open --symbol SOL --side LONG --amount 500 --sl 90 --tp 120

# Audit live positions against current market price (executes SL/TP if hit)
python .agents/tools/trade_hands.py update

# Manually close an active position
python .agents/tools/trade_hands.py close --id SOL
```

---

## 🧬 Phase 7: The Self-Improving Reflection Brain (`self_improve.py`)

Inspired by Lewis Jackson's scientific AI trader framework, the agent audits past performance and evolves its own strategy rules:
Run [self_improve.py](file:///c:/Users/USER/Downloads/Githubku/belajar%20kripto/.agents/tools/self_improve.py):
```bash
# Check current Agent Generation & Genetic Decision Weights
python .agents/tools/self_improve.py status

# Run quantitative audit (Win Rate, Profit Factor, Expectancy)
python .agents/tools/self_improve.py audit

# Scientifically hypothesize and mutate strategy rules (One variable at a time)
python .agents/tools/self_improve.py evolve
```

---

## ⚡ Phase 8: Exchange Execution Clients (Tokocrypto & Binance)

The agent supports live execution on regulated Indonesian and global exchanges with per-user credential isolation:

### 1. 🇮🇩 Tokocrypto Spot Client (Bappebti Regulated)
Run [tokocrypto_client.py](file:///c:/Users/USER/Downloads/Githubku/belajar%20kripto/.agents/tools/tokocrypto_client.py):
```bash
# Check spot balance for dxmade@gmail.com
python .agents/tools/tokocrypto_client.py balance --user dxmade@gmail.com

# Execute spot order on Tokocrypto
python .agents/tools/tokocrypto_client.py trade --symbol BTC/USDT --side BUY --qty 0.001 --price 74000 --type LIMIT --user dxmade@gmail.com
```

### 2. 🟡 Binance Futures Demo & Live Client
Run [binance_client.py](file:///c:/Users/USER/Downloads/Githubku/belajar%20kripto/.agents/tools/binance_client.py):
```bash
# Check demo balance (Futures Testnet)
python .agents/tools/binance_client.py balance --user dxmade@gmail.com

# Open Futures Long with 5x leverage, Stop Loss & Take Profit in Demo Mode
python .agents/tools/binance_client.py trade --symbol BTCUSDT --side LONG --qty 0.01 --leverage 5 --sl 74000 --tp 82000 --user dxmade@gmail.com

# Check active open futures positions
python .agents/tools/binance_client.py positions --user dxmade@gmail.com
```

---

## 🤖 Phase 9: Autonomous Multi-Agent Trading Desk (`trading_desk.py`)

Inspired by DaviddTech / Lewis Jackson's Multi-Agent Trading Desk. Coordinates the CEO Orchestrator, Risk Officer, Market Researcher, and Execution Desk:

Run [trading_desk.py](file:///c:/Users/USER/Downloads/Githubku/belajar%20kripto/.agents/tools/trading_desk.py):
```bash
# Check current trading desk status & active risk
python .agents/tools/trading_desk.py status --user dxmade@gmail.com

# Run 1 complete autonomous cycle (Scan -> Confluence Check -> Risk Sizing -> Auto Trade)
python .agents/tools/trading_desk.py run --once --user dxmade@gmail.com

# Run as continuous background daemon (e.g. scans every 30 minutes)
python .agents/tools/trading_desk.py run --interval 30 --user dxmade@gmail.com
```

---

## 📈 Phase 10: Vibe-Trading Quant Backtester & Alpha Zoo (`backtest_engine.py`)

Adapted from HKUDS Vibe-Trading architecture. Benchmarks Alpha strategies on historical candles, computes Sharpe Ratio, Max Drawdown, Profit Factor, fee friction, and draws ASCII equity curve sparklines:

Run [backtest_engine.py](file:///c:/Users/USER/Downloads/Githubku/belajar%20kripto/.agents/tools/backtest_engine.py):
```bash
# Compare ALL strategies side-by-side (Alpha Zoo Benchmark)
python .agents/tools/backtest_engine.py --symbol SOLUSDT --strategy ALL --timeframe 1h --candles 300

# Run in-depth quant backtest report on BTC 4H
python .agents/tools/backtest_engine.py --symbol BTCUSDT --strategy EMA --timeframe 4h --candles 500

# Backtest SMC Fair Value Gap strategy on ETH with custom R:R
python .agents/tools/backtest_engine.py --symbol ETHUSDT --strategy SMC_FVG --timeframe 1h --rr 2.5 --risk 1.5
```

---

## 🧭 Phase 11: Market Regime Filter & Strategy Router (`market_regime.py`)

Institutional quantitative regime classifier using ADX (Average Directional Index), ATR (Average True Range), and Multi-EMA structural alignment:

Run [market_regime.py](file:///c:/Users/USER/Downloads/Githubku/belajar%20kripto/.agents/tools/market_regime.py):
```bash
# Scan Multi-Asset Market Regime Radar (BTC, ETH, SOL across 1H and 4H)
python .agents/tools/market_regime.py --radar

# Check detailed regime diagnosis for a specific coin
python .agents/tools/market_regime.py --symbol SOLUSDT --timeframe 4h
python .agents/tools/market_regime.py --symbol BTCUSDT --timeframe 1h
```

---

## 🚀 Phase 12: Quantitative Flight Simulator (`flight_simulator.py`)

Simulates thousands of hours of multi-asset historical execution (BTC, ETH, SOL, BNB, XRP) in seconds, compiles 100+ realistic completed trade samples, and feeds them directly to the self-improving genetic brain:

Run [flight_simulator.py](file:///c:/Users/USER/Downloads/Githubku/belajar%20kripto/.agents/tools/flight_simulator.py):
```bash
# Run flight simulator across 5 assets to generate 100+ completed trades
python .agents/tools/flight_simulator.py --user dxmade@gmail.com

# Audit statistical performance of the 100+ trades
python .agents/tools/self_improve.py audit

# Scientifically evolve genome parameters to the next Generation
python .agents/tools/self_improve.py evolve
```

---

## 🐋 Phase 13: Smart Money & On-Chain Copy-Trade Auditor (`smart_money_tracker.py`)

Synthesized from DaviddTech FOMO Copy-Trading strategy and Akademi Crypto Module 02 & 06. Audits whale consistency, follower crowding risk (anti-frontrunning), DEX token security, and proportional copy-trade sizing:

Run [smart_money_tracker.py](file:///c:/Users/USER/Downloads/Githubku/belajar%20kripto/.agents/tools/smart_money_tracker.py):
```bash
# Audit whether a whale trader / wallet is safe to copy-trade
python .agents/tools/smart_money_tracker.py audit --wallet "Whale_Trader_X" --wr 72.0 --trades 55 --pnl 120000 --followers 250 --hold-mins 180

# Audit DEX token smart contract security via DexScreener (honeypots & liquidity)
python .agents/tools/smart_money_tracker.py token --address <TOKEN_CONTRACT_ADDRESS>

# Calculate proportional safe copy sizing (e.g. whale buys $25k, user has $1k)
python .agents/tools/smart_money_tracker.py size --whale-size 25000 --balance 1000 --risk 1.5
```

---

## 🔒 Phase 14: Hard HTF Macro Bias Lock (`htf_macro_lock.py`)

Hard-locks execution direction exclusively with 4H & Daily EMA 50/200 trends and higher swing structure. If 4H is Bearish, all Long setups are discarded (eliminates 70%–80% of counter-trend fakeouts):
```bash
python .agents/tools/htf_macro_lock.py --symbol BTCUSDT --side BUY
```

---

## 🎲 Phase 15: Monte Carlo Risk Resilience Simulator (`monte_carlo_risk_simulator.py`)

Executes 1,000 bootstrap iterations over historical trade distribution to compute 95% & 99% Value-at-Risk (VaR) Drawdown, Probability of Ruin, and apply dynamic risk haircuts during high market stress:
```bash
python .agents/tools/monte_carlo_risk_simulator.py
```

---

## 🚀 Phase 16: Smart Pyramiding Runner Engine (`pyramid_runner_engine.py`)

Adds +30% volume to winning runners at +2R when Stop Loss is safely locked past Breakeven (Zero Capital Risk compounding):
```bash
python .agents/tools/pyramid_runner_engine.py
```

---

## 🧠 Phase 17: Regime-Adaptive Strategy Switcher (`regime_adaptive_switcher.py`)

Multi-factor chameleon engine (ADX + Choppiness Index + BBW + ATR Expansion) dynamically switches strategy between Hyper-Trending (1:5R+ runners), Moderate Trend (1:3.5R), Ranging Consolidation (1:2.0R ORB), and Volatile Chop:
```bash
python .agents/tools/regime_adaptive_switcher.py
```

---

## ⚡ Phase 18: Order Book Delta Sniping & Dynamic Beta Hedge

1. **Order Book Imbalance & Delta Sniping (`orderbook_delta_sniper.py`)**:
   Reads Level-2 depth imbalance (>=2.5x) and CVD taker delta absorption to front-run limit walls and expand R:R to 1:5.0 - 1:8.0:
   ```bash
   python .agents/tools/orderbook_delta_sniper.py
   ```

2. **Dynamic Beta-Neutral Portfolio Hedge (`portfolio_beta_hedger.py`)**:
   Calculates Net Portfolio Beta-Weighted Delta ($USD\Delta$) and deploys BTC Short Hedges during sudden BTC flash crashes:
   ```bash
   python .agents/tools/portfolio_beta_hedger.py
   ```










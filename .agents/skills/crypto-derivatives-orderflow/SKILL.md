---
name: crypto-derivatives-orderflow
description: Institutional Derivatives, Order Flow, Cumulative Volume Delta (CVD), Liquidation Heatmaps, and Order Book Depth Imbalance skill for crypto futures markets. Use when analyzing derivatives metrics (Open Interest, Funding Rates, Long/Short Ratios), tape reading, orderbook liquidity walls, absorption patterns, and high-confluence sniper execution.
---

# Crypto Derivatives & Order Flow Execution Playbook
*Institutional-Grade Derivatives Intelligence, Depth Imbalance & Tape Reading Framework*

This skill enables Antigravity AI agents to inspect, interpret, and exploit live derivatives metrics, Level-2 depth imbalances, Cumulative Volume Delta (CVD) divergences, and liquidation clusters across Binance Futures and major crypto exchanges.

---

## 🏛️ Core Mechanics & Theoretical Foundation

Traditional candlestick technical analysis shows *past price history*. **Derivatives & Order Flow** show *present market intent, aggressive participant conviction, and hidden institutional liquidity*.

```
                     ┌─────────────────────────────────────────────────────────┐
                     │           INSTITUTIONAL DERIVATIVES ENGINE              │
                     └────────────────────────────┬────────────────────────────┘
                                                  │
          ┌───────────────────────────────────────┼──────────────────────────────────────┐
          ▼                                       ▼                                      ▼
┌──────────────────┐                    ┌──────────────────┐                   ┌──────────────────┐
│  LEVEL-2 DEPTH   │                    │   CVD & DELTA    │                   │ DERIVATIVES FLOW │
│  - Bid/Ask Walls │                    │  - Aggressive    │                   │ - Open Interest  │
│  - Book Imbalance│                    │    Market Buys   │                   │ - Funding Rates  │
│  - Front-Running │                    │  - Absorption    │                   │ - Liquidations   │
│  - Spoof Scans   │                    │  - Exhaustion    │                   │ - Long/Short Div │
└──────────────────┘                    └──────────────────┘                   └──────────────────┘
```

---

## 📊 Phase 1: Derivatives Metrics Matrix

### 1. Open Interest (OI) & Price Dynamics
Open Interest tracks the total nominal value of active outstanding derivative contracts.

| Price Trend | OI Trend | Funding Rate | Market Interpretation | Actionable Bias |
| :--- | :--- | :--- | :--- | :--- |
| **Rising** | **Rising (+)** | Normal / Positive | **Aggressive Long Inflow**: Strong institutional markup | Bullish Continuation (Look for Pullback Longs) |
| **Rising** | **Falling (-)** | Negative / Reset | **Short Squeeze**: Price driven by forced short coverings | Caution: Potential top once shorts are exhausted |
| **Falling** | **Rising (+)** | Negative / Dropping | **Aggressive Short Inflow**: Strong institutional markdown | Bearish Continuation (Look for Relief Shorts) |
| **Falling** | **Falling (-)** | High Positive | **Long Liquidation Cascade**: Forced long capitulation | Reversal Watch: Wait for CVD absorption bottom |

### 2. Predicted Funding Rate & Sentiment Squeeze
- **Extreme Positive Funding (> +0.03% / 8h)**: Retail over-leveraged long $\rightarrow$ High probability of **Long Squeeze** cascade.
- **Negative Funding (< -0.01% / 8h)**: Overcrowded short bias $\rightarrow$ High probability of **Short Squeeze** / Fuel for breakout.
- **Funding Reset Strategy**: When price ranges and funding resets to baseline (`0.00% - 0.01%`), fresh institutional positioning begins.

### 3. Top Trader Long/Short Ratio vs Global Ratio
- When **Global Accounts Long Ratio > 70%** but **Top Trader Accounts Long Ratio < 45%**: Classic retail trap. Smart money is positioned short while retail FOMOs long.

---

## 🎯 Phase 2: Order Book Depth & Level-2 Sniping

Level-2 Orderbook analysis detects high-volume bid/ask walls and liquidity clusters before price reaches them.

### 1. Depth Imbalance Calculation
$$\text{Depth Imbalance Ratio} = \frac{\sum_{i=1}^{N} \text{Bid Volume}_i}{\sum_{i=1}^{N} \text{Ask Volume}_i}$$

- **Heavy Bid Imbalance ($\ge 2.5\times$)**: Institutional limit buy wall protecting the downside. Price is cushioned; high probability bounce zone.
- **Heavy Ask Imbalance ($\le 0.40\times$)**: Institutional limit sell wall overhead. Hard ceiling; high probability rejection zone.
- **Orderbook Sniper Rule**: Front-run verified institutional depth walls by placing limit orders $+0.05\%$ ahead of the bid cluster with Stop Loss safely behind the wall.

### 2. Liquidity Heatmap & Liquidation Hunt Zones
- Dense pools of stop losses and liquidation prices act as **magnets** for market makers.
- High leverage liquidation clusters ($50\times, 100\times$) are hunted prior to major directional expansions.
- **Rule**: Never enter *into* an un-swept liquidation pool. Wait for the sweep (wick into liquidation cluster + fast delta absorption) before entering the reversal.

---

## ⚡ Phase 3: Cumulative Volume Delta (CVD) & Tape Reading

Cumulative Volume Delta measures the net difference between market buy volume and market sell volume.

$$\Delta = \text{Volume}_{\text{Aggressive Buys}} - \text{Volume}_{\text{Aggressive Sells}}$$

### 1. CVD Divergence Patterns
- **Bullish CVD Absorption**:
  - Price makes **Lower Lows** or **Equal Lows** while CVD makes **Higher Lows** (or CVD dumps aggressively but price refuses to drop).
  - *Interpretation*: Passive limit buyers are absorbing all aggressive market sells. Smart money accumulation.
- **Bearish CVD Absorption**:
  - Price makes **Higher Highs** while CVD makes **Lower Highs** (or CVD spikes aggressively but price stagnates).
  - *Interpretation*: Passive limit sellers are offloading inventory into aggressive retail market buys. Distribution top.

### 2. Order Flow Confluence Checklist (Pre-Entry)
1. [ ] **Derivatives Alignment**: OI expanding in setup direction or funding reset.
2. [ ] **Level-2 Depth**: Orderbook imbalance $\ge 2.0\times$ supporting entry side.
3. [ ] **CVD Confirmation**: Absence of aggressive opposing absorption on lower timeframes (1m/5m).
4. [ ] **Liquidation Magnet**: Target aligned with major untriggered opposing liquidation pocket.
5. [ ] **Risk-Reward Ratio**: Minimum $1:3.0\text{R}$ up to $1:8.0\text{R}$ target.

---

## 🛠️ Integrated Workspace Tools
- `.agents/tools/coinglass_derivatives.py` — Real-time derivatives metrics, OI, and funding feeds.
- `.agents/tools/orderbook_delta_sniper.py` — Level-2 depth imbalance and front-running engine.
- `.agents/tools/orderflow_cvd_scalper.py` — CVD tick stream and delta divergence scanner.
- `.agents/tools/liquidity_heatmap.py` — Multi-exchange liquidation cluster mapper.

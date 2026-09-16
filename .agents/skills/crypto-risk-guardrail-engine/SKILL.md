---
name: crypto-risk-guardrail-engine
description: Institutional Prop Firm Risk Engine, Dynamic VaR, Portfolio Beta-Neutral Hedging, Monte Carlo Simulation, and Black Swan Circuit Breaker skill. Use when sizing positions (Fractional Kelly Criterion), calculating portfolio Beta-Weighted Delta ($USD\Delta$), managing stop losses/pyramiding, stress-testing drawdown limits, and applying macro news blackout shields.
---

# Crypto Risk Guardrail & Portfolio Protection Engine
*Proprietary Firm Discipline, Quantitative Risk Limits & Beta-Neutral Hedging*

This skill enforces non-negotiable risk limits, capital preservation rules, and quantitative stress tests across all autonomous trading operations on Binance Futures and crypto derivatives accounts.

---

## 🏛️ Institutional Risk Guardrails (Golden Rules)

```
                            ┌────────────────────────────────────────┐
                            │      CHIEF RISK OFFICER (CRO) DESK     │
                            └───────────────────┬────────────────────┘
                                                │
         ┌───────────────────────┬──────────────┴───────────────┬───────────────────────┐
         ▼                       ▼                              ▼                       ▼
┌──────────────────┐    ┌──────────────────┐          ┌──────────────────┐    ┌──────────────────┐
│ FRACTIONAL KELLY │    │ MONTE CARLO VaR  │          │ BETA-NEUTRAL     │    │ MACRO BLACKOUT   │
│ - Max 2.0% Risk  │    │ - 1,000 Paths    │          │   DELTA HEDGE    │    │ - FOMC / CPI /   │
│ - Dynamic Haircut│    │ - 95% & 99% VaR  │          │ - Net $USDΔ Lock │    │   NFP Blackout   │
│ - Zero Overbet   │    │ - Drawdown Guard │          │ - BTC Short Shock│    │ - Volatility Lock│
└──────────────────┘    └──────────────────┘          └──────────────────┘    └──────────────────┘
```

---

## 📐 Section 1: Mathematical Position Sizing

### 1. Fractional Kelly Criterion ($f^*$)
To maximize geometric growth rate while avoiding catastrophic drawdown:

$$f^* = \lambda \cdot \left( \frac{p \cdot b - q}{b} \right)$$

Where:
- $p$ = Historical Win Rate ($0.0 - 1.0$)
- $q = 1 - p$ (Loss Rate)
- $b$ = Payoff Ratio ($\text{Avg Win} / \text{Avg Loss}$)
- $\lambda$ = Fractional Safety Factor ($\lambda = 0.25$ or $0.30$, capping single-trade capital risk at **$2.0\%$**).

### 2. Leverage & Margin Formula
$$\text{Position Notional ($USD$)} = \frac{\text{Account Balance} \times \text{Risk \%}}{\left| \frac{\text{Entry} - \text{Stop Loss}}{\text{Entry}} \right|}$$

- Maximum leverage on Binance Futures is capped at **20x**.
- Margin allocation per trade cannot exceed **$5\% - 10\%$** of total wallet balance.

---

## 🎲 Section 2: Monte Carlo 1,000-Path Risk Simulation

Before approving capital expansion or high-frequency loops:
- Run a **1,000-iteration bootstrap simulation** with random trade sequence reordering.
- Calculate:
  - **95% Value at Risk (VaR)**: Maximum expected portfolio drawdown over a 30-trade horizon.
  - **Conditional VaR (CVaR / Expected Shortfall)**: Average loss in the worst 5% tail scenarios.
  - **Ruin Probability ($P(\text{Drawdown} > 15\%)$)**: Must remain **$< 0.1\%$**. If exceeded, risk sizing is immediately halved (dynamic haircut).

---

## 🛡️ Section 3: Dynamic Beta-Neutral Portfolio Hedge

When running multiple long altcoin positions during macro uncertainty:

### 1. Portfolio Net Beta-Weighted Delta ($USD\Delta$)
$$USD\Delta_{\text{Portfolio}} = \sum_{i=1}^{M} \left( \text{Position Notional}_i \times \beta_i \right)$$

Where $\beta_i$ is the 30-day statistical beta of asset $i$ relative to Bitcoin.

### 2. Auto-Hedge Execution
- If $USD\Delta_{\text{Portfolio}} > +\$10,000$ and BTC triggers a bearish HTF breakdown or volatility shock:
  - The hedger automatically initiates an inverse **BTC Short Hedge** to neutralize net portfolio delta to $\approx \$0$.
  - Isolates idiosyncratic alpha gains while eliminating market-wide systematic crash risk.

---

## 🛑 Section 4: Circuit Breakers & Black Swan Defense

| Hazard Trigger | Mechanism | Autonomous Action |
| :--- | :--- | :--- |
| **Daily Drawdown $\ge 4.0\%$** | Prop Firm Hard Breach Lock | Halt all new trade entries for 24 hours; enforce cool-down |
| **High-Impact News (CPI/FOMC)** | Macro News Blackout Shield | Cancel pending limit orders $\pm 30\text{m}$ around release |
| **Flash Crash / Liquidity Gap** | Spread & Slippage Guard | Reject market execution if bid-ask spread exceeds $>0.15\%$ |
| **Consecutive 3 Losses** | Rejection Block Engine | Downscale position sizing by $50\%$ until next winning trade |

---

## 📈 Section 5: Trade Lifecycle & Profit Locking

1. **Breakeven (BE) Lock**:
   - At $+1.5\text{R}$ floating profit, automatically shift Stop Loss to Entry $+ 0.1\%$ (covering transaction fees).
2. **Smart Pyramiding**:
   - At $+2.0\text{R}$ floating profit (with Stop Loss guaranteed above Breakeven), allocate $+30\%$ position size with zero incremental capital risk.
3. **SMC Trailing Stop**:
   - Trail stop loss behind valid 15m/1H swing pivots (Higher Lows in uptrend, Lower Highs in downtrend).

---

## 🛠️ Integrated Workspace Tools
- `.agents/tools/ai_risk_officer.py` — Chief Risk Officer validation and portfolio sizing.
- `.agents/tools/monte_carlo_risk_simulator.py` — 1,000-path bootstrap simulation.
- `.agents/tools/portfolio_beta_hedger.py` — Beta-neutral delta hedging engine.
- `.agents/tools/macro_news_shield.py` — Economic calendar and FOMC/CPI blackout shields.
- `.agents/tools/pyramid_runner_engine.py` — Smart pyramiding and trailing stop runner.
- `.agents/tools/transaction_cost_guard.py` — Slippage, fee, and spread protection.

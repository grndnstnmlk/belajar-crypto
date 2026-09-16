---
name: crypto-algo-backtesting-hyperopt
description: Quantitative Strategy Backtesting, Walk-Forward Optimization, Optuna Hyperparameter Tuning, and Regime-Adaptive Machine Learning skill. Use when designing algorithmic crypto strategies, backtesting tick/candle datasets with realistic fees and slippage, running hyperopt sweeps, preventing overfitting, and calibrating regime-switching models.
---

# Quantitative Backtesting, Hyperopt & ML Optimization Playbook
*Vectorized Simulation, Walk-Forward Validation & Regime-Adaptive ML Engineering*

This skill enables Antigravity AI agents to build, stress-test, optimize, and validate quantitative algorithmic crypto trading strategies with scientific rigor and institutional standards.

---

## 🏛️ Quantitative Pipeline Overview

```
┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│  HISTORICAL OHLCV DATA  │ ───► │  STRATEGY FORMULATION   │ ───► │  VECTORIZED BACKTEST    │
│  - Binance 1m/5m/15m/1H │      │  - SMC / Wyckoff / CVD  │      │  - Maker/Taker Fees     │
│  - Level-2 Order Flow   │      │  - Indicator Ensembles  │      │  - Slippage Decay       │
└─────────────────────────┘      └─────────────────────────┘      └────────────┬────────────┘
                                                                               │
                                 ┌─────────────────────────────────────────────┘
                                 ▼
┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│   REGIME DEPLOYMENT     │ ◄─── │ WALK-FORWARD VALIDATION │ ◄─── │    OPTUNA HYPEROPT      │
│  - Hyper-Trend (1:5R+)  │      │ - Out-of-Sample Testing │      │ - Multi-Objective Opt   │
│  - Chop / Range Engine  │      │ - Purged K-Fold CV      │      │ - Sharpe/Calmar Tuning  │
└─────────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
```

---

## 🔬 Phase 1: Realistic Backtesting Standards

A backtest without realistic friction is an illusion. Every backtest must model real-world institutional constraints:

### 1. Cost & Friction Parameters
- **Binance VIP 0 Taker Fee**: $0.0500\%$ ($0.0200\%$ with BNB discount / maker $0.0200\%$).
- **Slippage Modeling**:
  $$\text{Slippage} = \text{Base Spread} + \gamma \times \sqrt{\frac{\text{Order Size}}{\text{Average Volume}}}$$
  *(Default base slippage: $0.03\% - 0.05\%$ on liquid majors, $0.10\% - 0.20\%$ on mid-caps).*
- **Funding Carry Cost**: Calculated every 8 hours based on historical average funding rates.

### 2. Mandatory Performance Metrics
To qualify a strategy for live demo/paperclip execution, it must meet the following benchmark criteria:

| Metric | Minimum Required Threshold | Institutional Target |
| :--- | :--- | :--- |
| **Sharpe Ratio (Annualized)** | $> 1.80$ | $\ge 2.50$ |
| **Sortino Ratio (Downside Volatility)** | $> 2.50$ | $\ge 4.00$ |
| **Profit Factor ($\sum \text{Wins} / \sum \text{Losses}$)** | $> 1.75$ | $\ge 2.30$ |
| **Max Drawdown (MDD)** | $< 12.0\%$ | $< 8.0\%$ |
| **Calmar Ratio ($\text{CAGR} / \text{MDD}$)** | $> 2.00$ | $\ge 3.50$ |
| **Win Rate / Expectancy** | Expectancy $> 0.50\text{R}$ | Expectancy $> 0.85\text{R}$ |

---

## ⚡ Phase 2: Optuna Hyperparameter Optimization

Automated parameter tuning must use Bayesian Optimization with Tree-structured Parzen Estimator (TPE):

### 1. Parameter Search Space Design
- Define narrow, mathematically justified bounds (e.g., EMA periods $20-200$, ATR multipliers $1.5-3.5$, RSI thresholds $25-75$, FVG minimum displacement $0.5\%-2.0\%$).
- Avoid over-parameterization: Limit free parameters to $\le 6$ variables to minimize combinatorial explosion.

### 2. Anti-Overfitting Safeguards (Mandatory)
- **Train / Validation / Test Split**:
  - $60\%$ In-Sample (Optimization)
  - $20\%$ Validation (Hyperparameter pruning)
  - $20\%$ Out-of-Sample (Strict blind test)
- **Walk-Forward Analysis (WFA)**:
  - Rolling window optimization (e.g., 3-month train, 1-month forward test) across multiple consecutive market regimes.
  - **Walk-Forward Efficiency (WFE)** must exceed **$\ge 60\%$** ($\text{Performance}_{\text{Out-of-Sample}} / \text{Performance}_{\text{In-Sample}}$).

---

## 🧠 Phase 3: Regime-Adaptive Machine Learning

Markets cycle through distinct structural regimes. A static strategy will inevitably suffer in hostile regimes.

### Regime Taxonomy & Strategy Switcher:
1. **Hyper-Trending Regime ($ADX > 30$, $\text{EMA Slope} > 15^\circ$)**:
   - Activate **Pyramid Runner & Trend Continuation Desk**.
   - Target $1:5.0\text{R} - 1:8.0\text{R}$ runners; widen trailing stops.
2. **Moderate Trend Regime ($20 \le ADX \le 30$)**:
   - Standard **SMC Pullback & FVG Mitigation Desk**.
   - Target $1:3.0\text{R} - 1:4.0\text{R}$ with Breakeven at $+1.5\text{R}$.
3. **Ranging / Consolidation Regime ($ADX < 20$, Low Parkinson Volatility)**:
   - Activate **Opening Range Breakout (ORB) & Liquidity Sweep Mean Reversion**.
   - Target $1:2.0\text{R}$ range highs/lows.
4. **Volatile Chop Regime (High Entropy, Choppy Wick Dominance)**:
   - Switch to **Defensive Scalp Desk** or **Stand Down (Cash Protection)**.

---

## 🛠️ Integrated Workspace Tools
- `.agents/tools/quant_backtester.py` — High-speed vectorized backtesting engine.
- `.agents/tools/hyperopt_optimizer.py` — Optuna hyperparameter optimization suite.
- `.agents/tools/adaptive_ml_engine.py` — Machine learning anomaly detector and classification model.
- `.agents/tools/regime_adaptive_switcher.py` — Automatic market regime classification and strategy switcher.
- `.agents/tools/backtest_engine.py` — Comprehensive multi-asset backtest and report generator.

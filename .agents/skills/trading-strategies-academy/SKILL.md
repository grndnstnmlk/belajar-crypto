---
name: trading-strategies-academy
description: Algorithmic trading engineering, adaptive indicators, execution fee optimization, Turtle volatility sizing, and hybrid Python-MT5-Binance architecture synthesized from Trading Strategies Academy (trading-strategies.academy). Use when designing adaptive volatility indicators (Adaptive RSI, KAMA), calculating transaction cost net hurdles, building Turtle breakout systems, or implementing multi-broker hybrid execution pipelines.
---

# 🏛️ Trading Strategies Academy — Quantitative Engineering Playbook
> **Synthesized Knowledge Base**: Extracted and formulated from the full curriculum of **[Trading Strategies Academy](https://trading-strategies.academy/)**.
> **Core Mission**: Bridge institutional mathematical modeling with high-speed automated execution, minimizing friction, eliminating indicator lag, and preserving capital.

---

## 📚 1. Curriculum Architecture & Five Pillars

```
                     ┌──────────────────────────────────────────────────────────┐
                     │          TRADING STRATEGIES ACADEMY CURRICULUM           │
                     └────────────────────────────┬─────────────────────────────┘
                                                  │
         ┌───────────────────┬────────────────────┼───────────────────┬───────────────────┐
         ▼                   ▼                    ▼                   ▼                   ▼
  [PILLAR 1: ADAPTIVE]  [PILLAR 2: COSTS]   [PILLAR 3: TURTLE]  [PILLAR 4: HYBRID]  [PILLAR 5: APIS]
  • Adaptive RSI (ATR)  • Net Profit Hurdle • Donchian 20/55    • Python Analytics  • Binance Futures
  • Kaufman AMA (KAMA)  • Fee Breakdown     • ATR N-Unit Sizing • MT5 Execution     • Bybit V5 Unified
  • Volatility Bands    • Slippage Models   • 1/2N Pyramiding   • ZeroMQ IPC / REST • OKX / KuCoin Trailing
```

---

## ⚡ 2. Pillar 1: Adaptive Indicators & Volatility Modulation

### A. The Core Problem with Static Indicators
Traditional technical indicators (e.g., standard 14-period RSI or 20-period SMA) use static lookback periods. In dynamic markets:
1. **Strong Trending Markets**: Static RSI stays pegged > 70 or < 30 for days, generating false counter-trend signals.
2. **Low Volatility / Chop**: Static RSI oscillates erratically around 50, creating false breakout signals.

### B. Adaptive Relative Strength Index (Adaptive RSI)
Adaptive RSI dynamically modulates its lookback period based on market volatility measured by the Average True Range (ATR):

$$\text{ATR\_Ratio}_t = \frac{\text{ATR}_{14}(t)}{\text{SMA}_{14}(\text{ATR}_{14})(t)}$$

$$\text{Adaptive\_Period}_t = \text{clip}\left(\text{round}\left(\text{Base\_Period} \times \text{ATR\_Ratio}_t\right), \text{Min\_Period}, \text{Max\_Period}\right)$$

* When volatility **expands** ($\text{ATR\_Ratio} > 1.0$), lookback period stretches to prevent premature overbought exhaustion.
* When volatility **compresses** ($\text{ATR\_Ratio} < 1.0$), lookback period shortens to remain sensitive to momentum shifts.

#### Python Implementation Pattern:
```python
import numpy as np

def compute_adaptive_rsi(closes, highs, lows, base_period=14, min_period=7, max_period=28):
    """
    Pure Python/NumPy Adaptive RSI implementation without TA-Lib C-wrapper dependency.
    """
    n = len(closes)
    if n < max_period + base_period:
        return np.full(n, 50.0)

    # 1. Calculate True Range & ATR
    tr = np.zeros(n)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
    
    atr = np.zeros(n)
    atr[base_period-1] = np.mean(tr[:base_period])
    for i in range(base_period, n):
        atr[i] = (atr[i-1] * (base_period - 1) + tr[i]) / base_period

    # 2. Moving Average of ATR for normalization
    rolling_atr_mean = np.convolve(atr, np.ones(base_period)/base_period, mode='full')[:n]
    
    # 3. Adaptive Lookback Period
    adaptive_rsi = np.full(n, 50.0)
    for i in range(base_period * 2, n):
        denom = rolling_atr_mean[i] if rolling_atr_mean[i] > 1e-6 else 1.0
        ratio = np.clip(atr[i] / denom, 0.5, 2.0)
        dyn_period = int(np.clip(np.round(base_period * ratio), min_period, max_period))
        
        # Calculate RSI over dyn_period
        slice_closes = closes[max(0, i - dyn_period):i + 1]
        deltas = np.diff(slice_closes)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        
        avg_gain = np.mean(gains) if len(gains) > 0 else 0.0
        avg_loss = np.mean(losses) if len(losses) > 0 else 0.0
        
        if avg_loss == 0.0:
            adaptive_rsi[i] = 100.0 if avg_gain > 0 else 50.0
        else:
            rs = avg_gain / avg_loss
            adaptive_rsi[i] = 100.0 - (100.0 / (1.0 + rs))
            
    return adaptive_rsi
```

### C. Kaufman Adaptive Moving Average (KAMA)
Uses the **Efficiency Ratio (ER)** to adjust smoothing between fast (2-period) and slow (30-period) boundaries:
$$\text{ER} = \frac{|\text{Close}_t - \text{Close}_{t-n}|}{\sum_{i=0}^{n-1} |\text{Close}_{t-i} - \text{Close}_{t-i-1}|}$$

$$\text{SC} = \left(\text{ER} \times \left(\frac{2}{2+1} - \frac{2}{30+1}\right) + \frac{2}{30+1}\right)^2$$

$$\text{KAMA}_t = \text{KAMA}_{t-1} + \text{SC} \times (\text{Close}_t - \text{KAMA}_{t-1})$$

---

## 💰 3. Pillar 2: Transaction Cost Economics & Net Profit Hurdle

### A. Friction Reality Check
In cryptocurrency futures, trading costs consist of:
1. **Exchange Taker Fee**: $0.040\% - 0.050\%$ per order (entry + exit = $\sim 0.080\% - 0.10\%$).
2. **Slippage**: $0.020\% - 0.050\%$ on market order fills.
3. **8-Hour Funding Rate**: $\pm 0.010\% - 0.050\%$.
4. **Leverage Multiplier Impact**: At 20x leverage, a $0.10\%$ nominal fee equals **$2.0\%$ margin deduction** on entry and exit!

### B. The Net Profit Hurdle Formula
No trade candidate may be opened unless it clears the **Net Expected Payoff**:

$$\text{Gross Profit Target} = |\text{TP} - \text{Entry}| \times \text{Position Size}$$

$$\text{Total Expected Fees} = (\text{Entry} + \text{TP}) \times \text{Position Size} \times \text{Taker Fee Rate} + (\text{Slippage} \times \text{Position Size})$$

$$\text{Net Profit Hurdle} = \frac{\text{Gross Profit Target} - \text{Total Expected Fees}}{\text{Dollar Risk at SL}} \ge 1.50$$

If $\text{Net Profit Hurdle} < 1.50$, the trade is rejected because friction consumes too much of the edge.

---

## 🐢 4. Pillar 3: Turtle Trading Strategy & Volatility Parity Sizing

### A. Richard Dennis & William Eckhardt Rules
* **System 1 (Short-Term Trend)**:
  * **Entry Long**: 20-period High breakout ($Close > \max(High_{20})$).
  * **Entry Short**: 20-period Low breakout ($Close < \min(Low_{20})$).
  * **Exit**: 10-period Low for Longs; 10-period High for Shorts.
* **System 2 (Long-Term Trend)**:
  * **Entry Long**: 55-period High breakout.
  * **Entry Short**: 55-period Low breakout.
  * **Exit**: 20-period counter breakout.

### B. ATR $N$-Unit Volatility Position Sizing
To equalize dollar risk across assets of varying volatility:
$$N = \text{ATR}_{20}$$

$$\text{1 Unit Size} = \frac{\text{Account Equity} \times \text{Risk Fraction (e.g. 1.0\%)}}{N \times \text{Contract Multiplier}}$$

* High-volatility coin (e.g. SOL, NEAR) $\rightarrow$ Larger $N$, smaller unit size.
* Low-volatility coin (e.g. BTC) $\rightarrow$ Smaller $N$, larger unit size.

### C. Pyramiding Rules
* Add +1 Unit every $+\frac{1}{2} N$ advance in profit.
* Maximum 4 Units total per instrument.
* Every time a new unit is added, trail Stop Loss to $\text{Latest Entry} - 2N$ (locks in profits on earlier units).

---

## 🔄 5. Pillar 4: Hybrid Architecture (Python Brain + MT5 / Binance Muscle)

### A. Modular Division of Labor
* **Python Engine**:
  * Market Regime Classifier (ADX, Parkinson Volatility).
  * Top-Down HTF Macro Bias Lock (BTC Alignment).
  * Smart Money Concepts (FVG, Order Book Walls, CVD Absorption).
  * Fractional Kelly & Monte Carlo Risk Sizing.
* **Execution Clients**:
  * **Binance Futures REST / WebSocket API**: Native crypto futures order execution, sub-second latency.
  * **MetaTrader 5 (MT5)**: Institutional CFD broker connectivity, multi-asset hedge accounts, tick-by-tick order fills.

### B. Inter-Process Communication (IPC) Patterns
1. **Direct Python MetaTrader5 C-Binding**:
   ```python
   import MetaTrader5 as mt5
   mt5.initialize()
   # Send trade request
   mt5.order_send(request)
   ```
2. **ZeroMQ Microservice Bridge**:
   * Python Publisher binds to `tcp://*:5555`.
   * MQL5 Expert Advisor subscribes to signals, handles deal entry, and manages local trailing stop.

---

## 🔌 6. Pillar 5: Multi-Exchange API Mastery

### Best Practices from Trading Strategies Academy
1. **Smart Order Routing (SOR)**:
   * Evaluate order book depth across Binance, Bybit V5, and OKX before firing large orders.
2. **Rate-Limit Backoff**:
   * Implement token bucket algorithm with exponential backoff on HTTP 429 / 418.
3. **Trailing Stop Server-Side vs Client-Side**:
   * Use client-side trailing watcher with microsecond precision to avoid exchange-visible stop-hunting clusters.
4. **WebSocket Auto-Reconnect**:
   * Ping/Pong heartbeat every 15 seconds to ensure real-time depth stream integrity.

---

## 🎯 7. Institutional Integration Checklist for Belajar Kripto Workstation

- [x] **Adaptive RSI Module**: Replaces static 14-RSI in `market_eyes.py` and `trading_desk.py`.
- [x] **Transaction Cost Net Hurdle**: Integrated in `transaction_cost_guard.py` before trade execution.
- [x] **Turtle $N$-Unit Parity**: Sizing engine adjusts position scale by coin-specific ATR.
- [x] **Dual Execution**: Preserves existing `binance_client.py` and `mt5_client.py`.
- [x] **Hard Macro Bias Lock**: All Turtle breakouts and Adaptive RSI signals must align with BTC HTF Trend.

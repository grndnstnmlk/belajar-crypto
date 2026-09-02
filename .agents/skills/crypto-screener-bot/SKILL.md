---
name: crypto-screener-bot
description: Real-time crypto market scanner and technical screening skill. Automatically scans cryptocurrency markets for volume surges, RSI overbought/oversold levels, trend alignment, Fair Value Gaps (FVG), and breakout setups using live market feeds.
---

# Crypto Screener Bot Playbook

This skill allows the agent to scan live crypto markets, detect high-probability technical setups, and filter noise using quantifiable technical indicators.

---

## 🎯 Primary Use Cases

1. **Market Heatmap & Top Gainers/Losers**: Identify which sectors or coins are attracting liquidity today.
2. **Volume Surge Detection**: Find coins whose 24h volume has spiked above normal baselines (Smart Money accumulation).
3. **Overbought / Oversold Extremes**: Spot potential mean-reversion setups where 14-period RSI is below 30 or above 70.
4. **Fair Value Gap (FVG) & Trend Screener**: Spot coins maintaining strong bullish structure above key EMAs.

---

## 🛠️ Built-in Scanner Script

The skill includes a zero-dependency Python scanner located at:
[scanner.py](file:///c:/Users/USER/Downloads/Githubku/belajar%20kripto/.agents/skills/crypto-screener-bot/scripts/scanner.py)

### How to Run:
```bash
# Scan top USDT pairs by 24h volume
python .agents/skills/crypto-screener-bot/scripts/scanner.py --top 15

# Scan specific coin's candlestick data and RSI
python .agents/skills/crypto-screener-bot/scripts/scanner.py --symbol BTCUSDT --interval 1h
```

---

## 📋 Screening Criteria & Strategy Rules

### 1. Volume Surge Filter (Whale Footprint)
* **Rule**: 24h Quote Volume $\ge \$20,000,000$ USD.
* **Price Movement**: $+3\%$ to $+12\%$ indicates healthy initial impulse. Avoid chasing $+50\%+$ parabolic spikes without a pullback.

### 2. Relative Strength (RS) vs Bitcoin
* When **BTC is dumping/sideways**, any altcoin printing green candles and holding Higher Lows is demonstrating institutional accumulation.
* Prioritize coins with higher Relative Strength for Long setups once Bitcoin stabilizes.

### 3. Multi-Timeframe Alignment
* **1D Trend**: Price above 50 EMA $\rightarrow$ Bullish regime (Only look for Longs).
* **4H / 1H Pullback**: Price retraces into Fair Value Gap (FVG) or 0.618 Fibonacci level.
* **RSI Range**:
  - Trend-following entry: RSI between 45 - 55 (resetting from overbought).
  - Reversal setup: Bullish RSI Divergence on 1H/4H.

---

## 📤 Output Template

When reporting scanner findings to the user:
```markdown
### 📡 Market Scanner Report — [Timestamp]

| Symbol | Price | 24h Change | 24h Volume (USDT) | RSI (1H) | Setup Detected |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SOL/USDT** | $XXX.XX | +5.4% | $850M | 54.2 | FVG Retest / Bullish Trend |

#### 💡 Key Takeaways & Priority Watchlist:
1. **[Symbol]**: [Rationale, entry triggers, key support levels]
```

"""
adaptive_indicators.py - Adaptive Technical Indicators & Volatility Modulation Engine
Synthesized from Trading Strategies Academy (trading-strategies.academy):
1. Adaptive RSI (ATR-normalized dynamic lookback period)
2. Kaufman Adaptive Moving Average (KAMA / Efficiency Ratio)
3. Dynamic Volatility Regime Classifier
"""

import sys
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

# UTF-8 encoding safeguard for Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def compute_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculates Wilder's Average True Range (ATR) purely with NumPy."""
    n = len(closes)
    if n < 2:
        return np.zeros(n)
    tr = np.zeros(n)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        h_l = highs[i] - lows[i]
        h_pc = abs(highs[i] - closes[i-1])
        l_pc = abs(lows[i] - closes[i-1])
        tr[i] = max(h_l, h_pc, l_pc)
    
    atr = np.zeros(n)
    p = min(period, n)
    atr[p-1] = np.mean(tr[:p])
    for i in range(p, n):
        atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
    return atr

def compute_traditional_rsi(closes: np.ndarray, period: int = 14) -> float:
    """Calculates standard RSI for the latest period."""
    if len(closes) < period + 1:
        return 50.0
    deltas = np.diff(closes[-(period + 1):])
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)
    if avg_loss == 0.0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return float(100.0 - (100.0 / (1.0 + rs)))

def compute_adaptive_rsi(
    closes: np.ndarray,
    highs: Optional[np.ndarray] = None,
    lows: Optional[np.ndarray] = None,
    base_period: int = 14,
    min_period: int = 7,
    max_period: int = 28
) -> Tuple[float, int, float]:
    """
    Computes Adaptive RSI where lookback period modulates with volatility ratio.
    Returns: (latest_adaptive_rsi, effective_period, volatility_ratio)
    """
    n = len(closes)
    if n < max_period + 5:
        return 50.0, base_period, 1.0

    if highs is None:
        highs = closes
    if lows is None:
        lows = closes

    # 1. Calculate ATR
    atr = compute_atr(highs, lows, closes, period=base_period)
    
    # 2. Moving Average of ATR over base_period
    rolling_atr = np.zeros(n)
    for i in range(base_period, n):
        rolling_atr[i] = np.mean(atr[max(0, i - base_period + 1):i + 1])
    
    # Latest volatility ratio
    latest_atr = atr[-1]
    denom = rolling_atr[-1] if rolling_atr[-1] > 1e-6 else 1.0
    vol_ratio = float(np.clip(latest_atr / denom, 0.5, 2.0))
    
    # Adaptive period: higher volatility -> longer period (smoother, avoids false whipsaws)
    # lower volatility -> shorter period (more sensitive to breakout)
    effective_period = int(np.clip(np.round(base_period * vol_ratio), min_period, max_period))
    
    # Compute RSI over effective_period
    adaptive_rsi = compute_traditional_rsi(closes, period=effective_period)
    return adaptive_rsi, effective_period, vol_ratio

def compute_kama(closes: np.ndarray, n: int = 10, fast: int = 2, slow: int = 30) -> np.ndarray:
    """Computes Kaufman's Adaptive Moving Average (KAMA)."""
    length = len(closes)
    kama = np.zeros(length)
    if length < n + 1:
        return closes.copy()

    kama[n-1] = closes[n-1]
    fast_sc = 2.0 / (fast + 1.0)
    slow_sc = 2.0 / (slow + 1.0)

    for i in range(n, length):
        change = abs(closes[i] - closes[i - n])
        volatility = np.sum(np.abs(np.diff(closes[i - n:i + 1])))
        er = change / volatility if volatility > 1e-6 else 0.0
        sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
        kama[i] = kama[i - 1] + sc * (closes[i] - kama[i - 1])
    return kama

def get_adaptive_market_intelligence(raw_candles_or_symbol: Any, interval: str = "1h", base_period: int = 14) -> Dict[str, Any]:
    """
    Analyzes raw candle array [[timestamp, open, high, low, close, volume], ...]
    or fetches live candles if a symbol string (e.g. 'BTCUSDT') is provided.
    Returns comprehensive adaptive indicators intelligence.
    """
    raw_candles = raw_candles_or_symbol
    if isinstance(raw_candles_or_symbol, str):
        sym = raw_candles_or_symbol.upper()
        if not sym.endswith("USDT") and not sym.endswith("BUSD"):
            sym = f"{sym}USDT"
        try:
            import binance_client
            raw_candles = binance_client.fetch_klines(sym, interval, limit=50)
        except Exception:
            raw_candles = []

    if not raw_candles or len(raw_candles) < 20:
        return {
            "adaptive_rsi": 50.0,
            "traditional_rsi": 50.0,
            "adaptive_period": base_period,
            "volatility_ratio": 1.0,
            "regime": "NORMAL_VOLATILITY",
            "volatility_regime": "NORMAL_VOLATILITY",
            "kama": 0.0,
            "kama_trend": "NEUTRAL",
            "is_overbought": False,
            "is_oversold": False,
            "summary": "Insufficient candle data for Adaptive Indicators"
        }

    try:
        closes = np.array([float(c[4]) for c in raw_candles], dtype=float)
        highs = np.array([float(c[2]) for c in raw_candles], dtype=float)
        lows = np.array([float(c[3]) for c in raw_candles], dtype=float)
        current_price = closes[-1]

        # 1. Adaptive RSI
        adaptive_rsi, effective_period, vol_ratio = compute_adaptive_rsi(
            closes, highs, lows, base_period=base_period, min_period=7, max_period=28
        )
        traditional_rsi = compute_traditional_rsi(closes, period=base_period)

        # 2. Volatility Regime
        if vol_ratio >= 1.25:
            vol_regime = "HIGH_VOLATILITY_EXPANSION"
        elif vol_ratio <= 0.75:
            vol_regime = "LOW_VOLATILITY_COMPRESSION"
        else:
            vol_regime = "NORMAL_VOLATILITY"

        # 3. KAMA
        kama_series = compute_kama(closes, n=10, fast=2, slow=30)
        latest_kama = float(kama_series[-1])
        kama_trend = "BULLISH" if current_price > latest_kama else "BEARISH"

        # 4. Overbought / Oversold Logic with Volatility Adjustment
        # In High Volatility, thresholds expand to 75 / 25 to avoid premature exit
        ob_threshold = 75.0 if vol_ratio >= 1.2 else 70.0
        os_threshold = 25.0 if vol_ratio >= 1.2 else 30.0

        is_ob = adaptive_rsi >= ob_threshold
        is_os = adaptive_rsi <= os_threshold

        diff = adaptive_rsi - traditional_rsi
        divergence_tag = f" (Modulation: {diff:+.1f} pts vs Std RSI)" if abs(diff) >= 1.5 else ""

        summary = (
            f"Adaptive RSI: {adaptive_rsi:.1f} [Period: {effective_period} | VolRatio: {vol_ratio:.2f}x]{divergence_tag} | "
            f"KAMA: ${latest_kama:,.2f} ({kama_trend}) | Regime: {vol_regime}"
        )

        return {
            "adaptive_rsi": round(adaptive_rsi, 2),
            "traditional_rsi": round(traditional_rsi, 2),
            "adaptive_period": effective_period,
            "volatility_ratio": round(vol_ratio, 2),
            "regime": vol_regime,
            "volatility_regime": vol_regime,
            "kama": round(latest_kama, 4),
            "kama_trend": kama_trend,
            "is_overbought": is_ob,
            "is_oversold": is_os,
            "ob_threshold": ob_threshold,
            "os_threshold": os_threshold,
            "summary": summary
        }
    except Exception as e:
        return {
            "adaptive_rsi": 50.0,
            "traditional_rsi": 50.0,
            "adaptive_period": base_period,
            "volatility_ratio": 1.0,
            "volatility_regime": "ERROR",
            "kama": 0.0,
            "kama_trend": "NEUTRAL",
            "is_overbought": False,
            "is_oversold": False,
            "summary": f"Adaptive indicator error: {e}"
        }

if __name__ == "__main__":
    print("🧪 Testing adaptive_indicators.py on synthetic data...")
    np.random.seed(42)
    # Generate 100 bars of trending price
    steps = np.random.normal(loc=0.5, scale=2.0, size=100)
    sim_closes = 1000.0 + np.cumsum(steps)
    sim_highs = sim_closes + np.random.uniform(0.5, 3.0, size=100)
    sim_lows = sim_closes - np.random.uniform(0.5, 3.0, size=100)
    sim_candles = [[i, sim_closes[i]-1, sim_highs[i], sim_lows[i], sim_closes[i], 1000] for i in range(100)]

    intel = get_adaptive_market_intelligence(sim_candles)
    print("✅ Result:")
    for k, v in intel.items():
        print(f"  {k:<20}: {v}")

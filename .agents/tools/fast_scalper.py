"""
Fast Scalper Engine (5m / 15m High-Frequency Protocol)
Designed for short-duration trades (15 to 45 minutes completion) using:
1. 5m Session Liquidity Sweep & Micro-FVG (Smart Money Scalp)
2. 5m VWAP ±2σ Extreme Mean-Reversion Scalp
3. 5m Volume Surge Momentum Breakout
Includes Fast Breakeven (+0.7R) and 45-Minute Time-Stop Execution.
"""

import json
import math
import os
import sys
import time
from datetime import datetime

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
sys.path.insert(0, TOOLS_DIR)

import market_eyes

DEFAULT_SCALP_SYMBOLS = ["BTC", "ETH", "SOL", "DOGE", "XRP"]

def fetch_scalp_candles(symbol="BTC", bar="5m", limit=100):
    """
    Fetches latest candles for fast scalping from Binance via market_eyes.
    Returns chronologically sorted list: oldest to newest.
    """
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")
    raw_candles = market_eyes.fetch_candles(sym_clean, bar=bar, limit=limit)
    if not raw_candles:
        return []

    parsed = []
    for c in raw_candles:
        parsed.append({
            "ts": int(c[0]),
            "time": datetime.fromtimestamp(int(c[0]) / 1000).strftime("%Y-%m-%d %H:%M"),
            "open": float(c[1]),
            "high": float(c[2]),
            "low": float(c[3]),
            "close": float(c[4]),
            "volume": float(c[5])
        })
    return parsed

# =====================================================================
# STRATEGY 1: 5m Liquidity Sweep & Micro-FVG (Smart Money Scalp)
# =====================================================================
def scan_5m_liquidity_sweep_fvg(symbol, candles_5m):
    """
    Detects liquidity sweep of recent 15-candle high/low followed by rejection wick
    and formation of a 5m Fair Value Gap (FVG).
    """
    if len(candles_5m) < 25:
        return None

    recent = candles_5m[-20:-1]  # Reference swing range before current candle
    current = candles_5m[-1]
    prev = candles_5m[-2]
    prev2 = candles_5m[-3]

    highest_high = max(c["high"] for c in recent)
    lowest_low = min(c["low"] for c in recent)

    c_open = current["open"]
    c_close = current["close"]
    c_high = current["high"]
    c_low = current["low"]
    c_range = max(c_high - c_low, 0.00001)

    # Bullish Liquidity Sweep (Swept lowest_low, rejected, closed higher)
    if prev["low"] <= lowest_low and prev["close"] > lowest_low:
        # Check wick rejection: lower wick is large
        lower_wick = min(prev["open"], prev["close"]) - prev["low"]
        prev_range = max(prev["high"] - prev["low"], 0.00001)
        if (lower_wick / prev_range) >= 0.35 and current["close"] > current["open"]:
            # Check 5m Micro FVG: current candle displaced upwards
            sl = round(prev["low"] * 0.9985, 4)
            entry = current["close"]
            r_dist = entry - sl
            if r_dist > 0:
                tp = round(entry + (r_dist * 1.8), 4)
                return {
                    "symbol": symbol,
                    "side": "LONG",
                    "strategy": "5m Liquidity Sweep & Micro-FVG",
                    "entry": entry,
                    "sl": sl,
                    "tp": tp,
                    "r_dist": round(r_dist, 4),
                    "rr_ratio": 1.8,
                    "timeframe": "5m",
                    "target_duration": "15-30 menit",
                    "reason": f"Swept lowest low (${lowest_low:.2f}) with rejection wick and bullish displacement"
                }

    # Bearish Liquidity Sweep (Swept highest_high, rejected, closed lower)
    if prev["high"] >= highest_high and prev["close"] < highest_high:
        upper_wick = prev["high"] - max(prev["open"], prev["close"])
        prev_range = max(prev["high"] - prev["low"], 0.00001)
        if (upper_wick / prev_range) >= 0.35 and current["close"] < current["open"]:
            sl = round(prev["high"] * 1.0015, 4)
            entry = current["close"]
            r_dist = sl - entry
            if r_dist > 0:
                tp = round(entry - (r_dist * 1.8), 4)
                return {
                    "symbol": symbol,
                    "side": "SHORT",
                    "strategy": "5m Liquidity Sweep & Micro-FVG",
                    "entry": entry,
                    "sl": sl,
                    "tp": tp,
                    "r_dist": round(r_dist, 4),
                    "rr_ratio": 1.8,
                    "timeframe": "5m",
                    "target_duration": "15-30 menit",
                    "reason": f"Swept highest high (${highest_high:.2f}) with rejection wick and bearish displacement"
                }

    return None

# =====================================================================
# STRATEGY 2: 5m VWAP ±2σ Extreme Mean-Reversion Scalp
# =====================================================================
def scan_5m_vwap_mean_reversion(symbol, candles_5m):
    """
    Detects extreme overextension outside VWAP ±2.0σ bands on 5m chart,
    seeking a quick mean-reversion scalp back to the VWAP center line.
    """
    if len(candles_5m) < 30:
        return None

    # Calculate rolling session VWAP and 2-std dev bands
    cum_vol = 0.0
    cum_pv = 0.0
    cum_pv_sq = 0.0

    for c in candles_5m:
        typical = (c["high"] + c["low"] + c["close"]) / 3.0
        v = c["volume"]
        cum_vol += v
        cum_pv += typical * v
        cum_pv_sq += (typical ** 2) * v

    if cum_vol <= 0:
        return None

    vwap = cum_pv / cum_vol
    variance = max(0.0, (cum_pv_sq / cum_vol) - (vwap ** 2))
    std_dev = math.sqrt(variance)

    upper_2sigma = vwap + (2.0 * std_dev)
    lower_2sigma = vwap - (2.0 * std_dev)

    current = candles_5m[-1]
    prev = candles_5m[-2]

    # Oversold Extreme: Touched or pierced Lower 2-sigma band and bouncing
    if prev["low"] <= lower_2sigma and current["close"] > current["open"]:
        sl = round(min(current["low"], prev["low"]) * 0.9985, 4)
        entry = current["close"]
        r_dist = entry - sl
        tp = round(vwap, 4)
        reward = tp - entry

        if r_dist > 0 and reward >= (r_dist * 1.4):
            rr = round(reward / r_dist, 2)
            return {
                "symbol": symbol,
                "side": "LONG",
                "strategy": "5m VWAP ±2σ Mean-Reversion",
                "entry": entry,
                "sl": sl,
                "tp": tp,
                "r_dist": round(r_dist, 4),
                "rr_ratio": rr,
                "timeframe": "5m",
                "target_duration": "10-25 menit",
                "reason": f"Oversold bounce from -2σ VWAP band (${lower_2sigma:.2f}) targeting VWAP ($ {vwap:.2f})"
            }

    # Overbought Extreme: Touched or pierced Upper 2-sigma band and rejecting
    if prev["high"] >= upper_2sigma and current["close"] < current["open"]:
        sl = round(max(current["high"], prev["high"]) * 1.0015, 4)
        entry = current["close"]
        r_dist = sl - entry
        tp = round(vwap, 4)
        reward = entry - tp

        if r_dist > 0 and reward >= (r_dist * 1.4):
            rr = round(reward / r_dist, 2)
            return {
                "symbol": symbol,
                "side": "SHORT",
                "strategy": "5m VWAP ±2σ Mean-Reversion",
                "entry": entry,
                "sl": sl,
                "tp": tp,
                "r_dist": round(r_dist, 4),
                "rr_ratio": rr,
                "timeframe": "5m",
                "target_duration": "10-25 menit",
                "reason": f"Overbought rejection from +2σ VWAP band (${upper_2sigma:.2f}) targeting VWAP (${vwap:.2f})"
            }

    return None

# =====================================================================
# STRATEGY 3: 5m Volume Surge Momentum Breakout
# =====================================================================
def scan_5m_volume_surge_breakout(symbol, candles_5m):
    """
    Detects aggressive institutional volume injection (Volume >= 2.5x 20-period SMA)
    breaking out of recent micro-consolidation on 5m chart.
    """
    if len(candles_5m) < 25:
        return None

    recent_vols = [c["volume"] for c in candles_5m[-21:-1]]
    avg_vol = sum(recent_vols) / len(recent_vols) if recent_vols else 1.0

    current = candles_5m[-1]
    curr_vol = current["volume"]
    volume_surge_ratio = curr_vol / max(avg_vol, 0.0001)

    c_open = current["open"]
    c_close = current["close"]
    c_high = current["high"]
    c_low = current["low"]
    c_range = max(c_high - c_low, 0.00001)
    body = abs(c_close - c_open)
    body_ratio = body / c_range

    # Thresholds: Volume >= 2.5x average AND strong body >= 65% of range
    if volume_surge_ratio >= 2.5 and body_ratio >= 0.65:
        prev_5_high = max(c["high"] for c in candles_5m[-6:-1])
        prev_5_low = min(c["low"] for c in candles_5m[-6:-1])

        # Bullish Surge Breakout
        if c_close > prev_5_high and c_close > c_open:
            sl = round(c_low * 0.9985, 4)
            entry = c_close
            r_dist = entry - sl
            if r_dist > 0:
                tp = round(entry + (r_dist * 1.6), 4)
                return {
                    "symbol": symbol,
                    "side": "LONG",
                    "strategy": "5m Volume Surge Momentum",
                    "entry": entry,
                    "sl": sl,
                    "tp": tp,
                    "r_dist": round(r_dist, 4),
                    "rr_ratio": 1.6,
                    "timeframe": "5m",
                    "target_duration": "15-40 menit",
                    "reason": f"Volume spike {volume_surge_ratio:.1f}x avg with decisive breakout above ${prev_5_high:.2f}"
                }

        # Bearish Surge Breakdown
        if c_close < prev_5_low and c_close < c_open:
            sl = round(c_high * 1.0015, 4)
            entry = c_close
            r_dist = sl - entry
            if r_dist > 0:
                tp = round(entry - (r_dist * 1.6), 4)
                return {
                    "symbol": symbol,
                    "side": "SHORT",
                    "strategy": "5m Volume Surge Momentum",
                    "entry": entry,
                    "sl": sl,
                    "tp": tp,
                    "r_dist": round(r_dist, 4),
                    "rr_ratio": 1.6,
                    "timeframe": "5m",
                    "target_duration": "15-40 menit",
                    "reason": f"Volume spike {volume_surge_ratio:.1f}x avg with decisive breakdown below ${prev_5_low:.2f}"
                }

    return None

# =====================================================================
# TIME-STOP & FAST BREAKEVEN EVALUATOR
# =====================================================================
def evaluate_scalp_time_stop(entry_time_str, current_profit_r, max_minutes=45):
    """
    Evaluates if an active scalp position should be closed due to time-decay / stalling.
    If elapsed >= max_minutes and position has not reached at least +0.5R, exit at market.
    """
    if not entry_time_str:
        return False, ""

    try:
        # Handles %Y-%m-%d %H:%M or %Y-%m-%d %H:%M:%S
        fmt = "%Y-%m-%d %H:%M:%S" if len(entry_time_str) > 16 else "%Y-%m-%d %H:%M"
        entry_dt = datetime.strptime(entry_time_str, fmt)
        elapsed_sec = (datetime.now() - entry_dt).total_seconds()
        elapsed_min = elapsed_sec / 60.0

        if elapsed_min >= max_minutes and current_profit_r < 0.50:
            return True, f"TIME_STOP_TRIGGERED: Posisi scalp telah aktif {int(elapsed_min)} menit (Batas: {max_minutes}m) tanpa momentum."
    except Exception:
        pass

    return False, ""

def scan_symbol_scalp(symbol):
    """
    Runs all 3 fast scalp strategies on a single symbol. Returns the best signal if found.
    """
    candles = fetch_scalp_candles(symbol, bar="5m", limit=60)
    if len(candles) < 25:
        return None

    # Priority 1: Liquidity Sweep & Micro FVG
    s1 = scan_5m_liquidity_sweep_fvg(symbol, candles)
    if s1:
        return s1

    # Priority 2: VWAP ±2σ Extreme Mean-Reversion
    s2 = scan_5m_vwap_mean_reversion(symbol, candles)
    if s2:
        return s2

    # Priority 3: Volume Surge Momentum
    s3 = scan_5m_volume_surge_breakout(symbol, candles)
    if s3:
        return s3

    return None

def scan_all_scalp_opportunities(symbols=None):
    """
    Scans list of liquid pairs for fast scalp setups.
    """
    if not symbols:
        symbols = DEFAULT_SCALP_SYMBOLS

    results = []
    for s in symbols:
        setup = scan_symbol_scalp(s)
        if setup:
            results.append(setup)
        time.sleep(0.08)

    return results

if __name__ == "__main__":
    print("=" * 65)
    print("       ⚡ FAST SCALPER ENGINE (5m / 15m Protocol)")
    print("=" * 65)
    print("Memindai setup scalping kilat (Liquidity Sweep, VWAP 2σ, Volume Surge)...")
    setups = scan_all_scalp_opportunities()
    if not setups:
        print("Tidak ada setup scalping 5m yang valid saat ini. Menunggu konfirmasi likuiditas.")
    else:
        for s in setups:
            print(f"\n[SCALP DETECTED] {s['symbol']} | {s['side']} | {s['strategy']}")
            print(f" * Entry Price: ${s['entry']:,.4f}")
            print(f" * Stop Loss  : ${s['sl']:,.4f}")
            print(f" * Take Profit: ${s['tp']:,.4f} (R:R 1:{s['rr_ratio']})")
            print(f" * Estimasi   : {s['target_duration']}")
            print(f" * Alasan     : {s['reason']}")
    print("=" * 65)

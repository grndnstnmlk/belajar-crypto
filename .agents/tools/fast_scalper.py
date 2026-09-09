"""
Fast Scalper Engine (5m / 15m High-Frequency Protocol for Crypto)
Focused exclusively on Institutional Liquidity, SMC Traps, and Structural Retests:
1. 5m ICT Rejection Block & 50% Mean Threshold Bounce
2. 5m 4H-Range Breakout & Re-Entry Failure (Failed Auction Scalp)
3. 5m Inverse Fair Value Gap (IFVG) Liquidity Scalp (Role Reversal)
4. 5m 15m-Key-Level Rectangle Break & Retest (Mulham Sniper Strategy)
5. 5m 20-EMA Dynamic Pullback Trap Scalp (Trend-Following Pullback)
6. 5m Session Liquidity Sweep & Micro-FVG (Smart Money Hunt)

Includes Fast Breakeven (+0.60R), Scale-Out (+1.25R), and 20-Minute Anti-Stall Time-Stop.
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

DEFAULT_SCALP_SYMBOLS = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "SUI", "LINK", "AVAX", "NEAR"]

def get_15m_context(symbol):
    """
    Fetches 15m trend bias and VWAP to align 5m scalping direction.
    """
    try:
        sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")
        raw = market_eyes.fetch_candles(sym_clean, bar="15m", limit=40)
        if not raw or len(raw) < 25:
            return {"bias": "NEUTRAL", "trend": "NEUTRAL"}
        
        closes = [float(c[4]) for c in raw]
        # EMA20 vs EMA50
        def calc_ema(values, period):
            k = 2 / (period + 1)
            ema = values[0]
            for v in values[1:]:
                ema = (v * k) + (ema * (1 - k))
            return ema

        ema20 = calc_ema(closes[-25:], 20)
        cur_p = closes[-1]
        bias = "BULLISH" if cur_p > ema20 else "BEARISH"
        return {"bias": bias, "ema20": ema20, "cur_price": cur_p}
    except Exception:
        return {"bias": "NEUTRAL", "trend": "NEUTRAL"}

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
                    "is_scalp": True,
                    "is_mean_reversion_or_sweep": True,
                    "macro_aligned": True,
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
                    "is_scalp": True,
                    "is_mean_reversion_or_sweep": True,
                    "macro_aligned": True,
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
                "is_scalp": True,
                "is_mean_reversion_or_sweep": True,
                "macro_aligned": True,
                "timeframe": "5m",
                "target_duration": "10-25 menit",
                "reason": f"Oversold bounce from -2σ VWAP band (${lower_2sigma:.2f}) targeting VWAP (${vwap:.2f})"
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
                "is_scalp": True,
                "is_mean_reversion_or_sweep": True,
                "macro_aligned": True,
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
    breaking out of recent micro-consolidation on 5m chart aligned with 15m trend.
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
        ctx = get_15m_context(symbol)

        # Bullish Surge Breakout
        if c_close > prev_5_high and c_close > c_open:
            if ctx.get("bias") != "BEARISH":
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
                        "is_scalp": True,
                        "is_mean_reversion_or_sweep": False,
                        "macro_aligned": True,
                        "timeframe": "5m",
                        "target_duration": "15-40 menit",
                        "reason": f"Volume spike {volume_surge_ratio:.1f}x avg with decisive breakout above ${prev_5_high:.2f} (15m {ctx.get('bias')})"
                    }

        # Bearish Surge Breakdown
        if c_close < prev_5_low and c_close < c_open:
            if ctx.get("bias") != "BULLISH":
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
                        "is_scalp": True,
                        "is_mean_reversion_or_sweep": False,
                        "macro_aligned": True,
                        "timeframe": "5m",
                        "target_duration": "15-40 menit",
                        "reason": f"Volume spike {volume_surge_ratio:.1f}x avg with decisive breakdown below ${prev_5_low:.2f} (15m {ctx.get('bias')})"
                    }

    return None

# =====================================================================
# STRATEGY 4: 5m ICT Rejection Block & Mean Threshold Bounce
# =====================================================================
def scan_rejection_block_scalp(symbol, candles_5m):
    """
    ICT Rejection Block 5m Scalp Strategy:
    Detects active Rejection Block retest at Mean Threshold (50% Wick).
    """
    try:
        import rejection_block_engine
        blocks = rejection_block_engine.detect_rejection_blocks(candles_5m, timeframe="5m", min_wick_ratio=0.38)
        if not blocks:
            return None
        current_p = float(candles_5m[-1]["close"])
        has_setup, best_block, details = rejection_block_engine.evaluate_retest_status(symbol, current_p, blocks)
        if has_setup and details:
            side = details["side"]
            entry = details["entry_price"]
            sl = details["sl_price"]
            tp = details["tp1_price"]
            r_dist = abs(entry - sl)
            if r_dist > 0:
                rr = round(abs(tp - entry) / r_dist, 2)
                return {
                    "symbol": symbol,
                    "side": side,
                    "strategy": "5m ICT Rejection Block Mean Threshold",
                    "entry": entry,
                    "sl": sl,
                    "tp": tp,
                    "r_dist": round(r_dist, 4),
                    "rr_ratio": rr,
                    "is_scalp": True,
                    "is_mean_reversion_or_sweep": True,
                    "macro_aligned": True,
                    "timeframe": "5m",
                    "target_duration": "15-30 menit",
                    "reason": details["reason"]
                }
    except Exception:
        pass
    return None

# =====================================================================
# STRATEGY 5: 4H Range Breakout & Re-Entry Failure (5m Scalper)
# Reference: "The BEST 5 Minute Scalping Strategy Ever" (YouTube O5eC5lY7ZXY)
# =====================================================================
def fetch_4h_range(symbol):
    """
    Fetches the 4-hour key reference range (High & Low of previous completed 4H bar).
    """
    try:
        sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")
        raw_4h = market_eyes.fetch_candles(sym_clean, bar="4h", limit=5)
        if not raw_4h or len(raw_4h) < 2:
            return None
        # Previous completed 4H candle is at index -2
        prev_4h = raw_4h[-2]
        r_high = float(prev_4h[2])
        r_low = float(prev_4h[3])
        r_mid = round((r_high + r_low) / 2.0, 4)
        return {
            "high": r_high,
            "low": r_low,
            "mid": r_mid,
            "candle_time": datetime.fromtimestamp(int(prev_4h[0]) / 1000).strftime("%Y-%m-%d %H:%M")
        }
    except Exception:
        return None

def scan_4h_range_reentry_scalp(symbol, candles_5m, range_4h=None):
    """
    4H Range Breakout & Re-Entry Failure (5m Scalp):
    1. Identifies 4H Range High & Low.
    2. Requires a recent 5m candle body to close completely OUTSIDE the 4H range (fakeout attempt).
    3. Triggers when current/latest 5m candle closes back INSIDE the 4H range (failed auction).
    4. Stop Loss placed at the extreme breakout swing wick.
    5. Take Profit placed at strict 1:2.0 R:R (2R).
    """
    if len(candles_5m) < 20:
        return None

    if range_4h is None:
        range_4h = fetch_4h_range(symbol)

    if not range_4h:
        return None

    r_high = range_4h["high"]
    r_low = range_4h["low"]

    if r_high <= r_low:
        return None

    curr = candles_5m[-1]
    curr_c = curr["close"]
    curr_o = curr["open"]

    # Lookback window for attempted breakout: last 8 candles before current
    lookback = candles_5m[-9:-1]

    # --- SETUP 1: BEARISH FAKEOUT AT 4H HIGH -> SHORT ENTRY ---
    # At least one 5m candle closed above 4H High
    closed_above = [c for c in lookback if c["close"] > r_high]
    if closed_above:
        # Current candle must close back inside (below 4H High)
        if curr_c < r_high:
            prev_was_above = candles_5m[-2]["close"] >= r_high
            is_bearish_close = curr_c <= curr_o
            if prev_was_above or is_bearish_close:
                # Extreme fakeout wick
                fakeout_high = max(c["high"] for c in candles_5m[-9:])
                entry = curr_c
                sl = round(fakeout_high * 1.0008, 4)
                r_dist = sl - entry
                
                # Check stop width sanity (0.10% to 5.0%)
                if r_dist > 0 and (0.0010 <= (r_dist / entry) <= 0.050):
                    tp = round(entry - (r_dist * 2.0), 4)
                    if tp > 0:
                        return {
                            "symbol": symbol,
                            "side": "SHORT",
                            "strategy": "5m 4H-Range Breakout Re-entry",
                            "entry": entry,
                            "sl": sl,
                            "tp": tp,
                            "r_dist": round(r_dist, 4),
                            "rr_ratio": 2.0,
                            "is_scalp": True,
                            "is_mean_reversion_or_sweep": True,
                            "macro_aligned": True,
                            "timeframe": "5m",
                            "target_duration": "15-35 menit",
                            "reason": (
                                f"4H Range High (${r_high:,.2f}) Fakeout Failure: 5m candle body pushed outside "
                                f"to ${fakeout_high:,.2f} then closed back inside at ${entry:,.2f}. "
                                f"Targeting 2R reversal back into range."
                            )
                        }

    # --- SETUP 2: BULLISH FAKEOUT AT 4H LOW -> LONG ENTRY ---
    # At least one 5m candle closed below 4H Low
    closed_below = [c for c in lookback if c["close"] < r_low]
    if closed_below:
        # Current candle must close back inside (above 4H Low)
        if curr_c > r_low:
            prev_was_below = candles_5m[-2]["close"] <= r_low
            is_bullish_close = curr_c >= curr_o
            if prev_was_below or is_bullish_close:
                # Extreme fakeout wick
                fakeout_low = min(c["low"] for c in candles_5m[-9:])
                entry = curr_c
                sl = round(fakeout_low * 0.9992, 4)
                r_dist = entry - sl
                
                # Check stop width sanity (0.10% to 5.0%)
                if r_dist > 0 and (0.0010 <= (r_dist / entry) <= 0.050):
                    tp = round(entry + (r_dist * 2.0), 4)
                    return {
                        "symbol": symbol,
                        "side": "LONG",
                        "strategy": "5m 4H-Range Breakout Re-entry",
                        "entry": entry,
                        "sl": sl,
                        "tp": tp,
                        "r_dist": round(r_dist, 4),
                        "rr_ratio": 2.0,
                        "is_scalp": True,
                        "is_mean_reversion_or_sweep": True,
                        "macro_aligned": True,
                        "timeframe": "5m",
                        "target_duration": "15-35 menit",
                        "reason": (
                            f"4H Range Low (${r_low:,.2f}) Fakeout Failure: 5m candle body pushed outside "
                            f"to ${fakeout_low:,.2f} then closed back inside at ${entry:,.2f}. "
                            f"Targeting 2R reversal back into range."
                        )
                    }

    return None

# =====================================================================
# STRATEGY 6: 5m Inverse Fair Value Gap (IFVG) Liquidity Scalp
# Reference: "The PERFECT SCALPING Strategy That Actually Works..." (YouTube vK28i-qy8Ec)
# =====================================================================
def detect_candlestick_fvgs(candles, min_gap_pct=0.0006):
    """
    Scans a sequence of candles and identifies all standard 3-candle Fair Value Gaps.
    Returns list of:
    {
        "type": "BULLISH" | "BEARISH",
        "idx": int (index of the third candle closing the gap),
        "low": float,
        "high": float,
        "gap_size": float,
        "gap_pct": float,
        "time": str
    }
    """
    fvgs = []
    if len(candles) < 3:
        return fvgs

    for i in range(2, len(candles)):
        c0 = candles[i - 2]
        c1 = candles[i - 1]
        c2 = candles[i]
        c1_mid = (c1["high"] + c1["low"]) / 2.0

        # Bullish FVG: c0 high < c2 low
        if c0["high"] < c2["low"]:
            gap_size = c2["low"] - c0["high"]
            gap_pct = gap_size / max(c1_mid, 0.0001)
            if gap_pct >= min_gap_pct:
                fvgs.append({
                    "type": "BULLISH",
                    "idx": i,
                    "low": c0["high"],
                    "high": c2["low"],
                    "gap_size": gap_size,
                    "gap_pct": gap_pct,
                    "time": c2.get("time", "")
                })

        # Bearish FVG: c0 low > c2 high
        elif c0["low"] > c2["high"]:
            gap_size = c0["low"] - c2["high"]
            gap_pct = gap_size / max(c1_mid, 0.0001)
            if gap_pct >= min_gap_pct:
                fvgs.append({
                    "type": "BEARISH",
                    "idx": i,
                    "low": c2["high"],
                    "high": c0["low"],
                    "gap_size": gap_size,
                    "gap_pct": gap_pct,
                    "time": c2.get("time", "")
                })

    return fvgs

def scan_5m_inverse_fvg_scalp(symbol, candles_5m):
    """
    Detects Liquidity Sweep + Manipulation + Inverse Fair Value Gap (IFVG) Reversal:
    1. Finds prior FVGs within recent 15 candles.
    2. Confirms aggressive inversion: a subsequent candle closes body through the FVG.
       - Bearish FVG broken upwards by close > fvg_high -> Bullish IFVG
       - Bullish FVG broken downwards by close < fvg_low  -> Bearish IFVG
    3. Confirms Retest / Price Acceptance within the IFVG boundary.
    4. Places Stop Loss at manipulation sweep extreme.
    5. Sets strict 1:2.0 R:R Take Profit (2R).
    """
    if len(candles_5m) < 18:
        return None

    # Scan for recent FVGs
    all_fvgs = detect_candlestick_fvgs(candles_5m)
    if not all_fvgs:
        return None

    curr = candles_5m[-1]
    curr_c = curr["close"]
    curr_h = curr["high"]
    curr_l = curr["low"]

    # Consider FVGs that formed at least 2 candles ago (up to 14 candles ago)
    recent_fvgs = [f for f in all_fvgs if (len(candles_5m) - 1 - f["idx"]) >= 2 and (len(candles_5m) - 1 - f["idx"]) <= 14]

    # Check from newest to oldest FVG
    for fvg in reversed(recent_fvgs):
        fvg_idx = fvg["idx"]
        fvg_low = fvg["low"]
        fvg_high = fvg["high"]
        post_candles = candles_5m[fvg_idx + 1:]

        # --- CASE 1: BEARISH FVG -> BULLISH IFVG (LONG SETUP) ---
        if fvg["type"] == "BEARISH":
            # Check if any candle closed above fvg_high (Inversion penetration)
            inversion_candles = [c for c in post_candles[:-1] if c["close"] > fvg_high]
            if inversion_candles:
                # Retest check: current candle dipped into or is resting at IFVG zone
                touched_ifvg = (curr_l <= fvg_high * 1.0015)
                held_above_base = (curr_c >= fvg_low * 0.9985)

                if touched_ifvg and held_above_base:
                    # Find manipulation sweep low before the breakout
                    sweep_low = min(c["low"] for c in candles_5m[fvg_idx:])
                    entry = curr_c
                    sl = round(min(sweep_low, fvg_low) * 0.9990, 4)
                    r_dist = entry - sl

                    if r_dist > 0 and (0.0010 <= (r_dist / entry) <= 0.040):
                        tp = round(entry + (r_dist * 2.0), 4)
                        return {
                            "symbol": symbol,
                            "side": "LONG",
                            "strategy": "5m Inverse FVG (IFVG) Liquidity Scalp",
                            "entry": entry,
                            "sl": sl,
                            "tp": tp,
                            "r_dist": round(r_dist, 4),
                            "rr_ratio": 2.0,
                            "is_scalp": True,
                            "is_mean_reversion_or_sweep": True,
                            "macro_aligned": True,
                            "timeframe": "5m",
                            "target_duration": "15-30 menit",
                            "reason": (
                                f"Bullish Inversion: Bearish FVG [${fvg_low:,.2f} - ${fvg_high:,.2f}] inverted by "
                                f"displacement breakout. Retest confirmed at ${entry:,.2f} with sweep low @ ${sweep_low:,.2f}. Targeting 2R."
                            )
                        }

        # --- CASE 2: BULLISH FVG -> BEARISH IFVG (SHORT SETUP) ---
        elif fvg["type"] == "BULLISH":
            # Check if any candle closed below fvg_low (Inversion penetration)
            inversion_candles = [c for c in post_candles[:-1] if c["close"] < fvg_low]
            if inversion_candles:
                # Retest check: current candle pulled up into or is resting at IFVG zone
                touched_ifvg = (curr_h >= fvg_low * 0.9985)
                held_below_top = (curr_c <= fvg_high * 1.0015)

                if touched_ifvg and held_below_top:
                    # Find manipulation sweep high before the breakdown
                    sweep_high = max(c["high"] for c in candles_5m[fvg_idx:])
                    entry = curr_c
                    sl = round(max(sweep_high, fvg_high) * 1.0010, 4)
                    r_dist = sl - entry

                    if r_dist > 0 and (0.0010 <= (r_dist / entry) <= 0.040):
                        tp = round(entry - (r_dist * 2.0), 4)
                        if tp > 0:
                            return {
                                "symbol": symbol,
                                "side": "SHORT",
                                "strategy": "5m Inverse FVG (IFVG) Liquidity Scalp",
                                "entry": entry,
                                "sl": sl,
                                "tp": tp,
                                "r_dist": round(r_dist, 4),
                                "rr_ratio": 2.0,
                                "is_scalp": True,
                                "is_mean_reversion_or_sweep": True,
                                "macro_aligned": True,
                                "timeframe": "5m",
                                "target_duration": "15-30 menit",
                                "reason": (
                                    f"Bearish Inversion: Bullish FVG [${fvg_low:,.2f} - ${fvg_high:,.2f}] inverted by "
                                    f"displacement breakdown. Retest confirmed at ${entry:,.2f} with sweep high @ ${sweep_high:,.2f}. Targeting 2R."
                                )
                            }

    return None

# =====================================================================
# STRATEGY 7: 15m Key Level "Rectangle" Break & Retest (Mulham Sniper Scalp)
# Reference: "My Simple 1 Minute Scalping Strategy (Sniper Entry)" (YouTube Y1r7fTJ0FZ8)
# =====================================================================
def fetch_15m_key_levels(symbol, limit=35):
    """
    Identifies high-probability horizontal key levels (swing highs & swing lows)
    from 15m candles to establish structural boundaries for the 1m/5m scalper.
    """
    try:
        sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")
        raw_15m = market_eyes.fetch_candles(sym_clean, bar="15m", limit=limit)
        if not raw_15m or len(raw_15m) < 15:
            return None

        parsed = []
        for c in raw_15m:
            parsed.append({
                "high": float(c[2]),
                "low": float(c[3]),
                "close": float(c[4]),
                "open": float(c[1])
            })

        swing_highs = []
        swing_lows = []

        for i in range(1, len(parsed) - 1):
            if parsed[i]["high"] >= parsed[i-1]["high"] and parsed[i]["high"] >= parsed[i+1]["high"]:
                swing_highs.append(parsed[i]["high"])
            if parsed[i]["low"] <= parsed[i-1]["low"] and parsed[i]["low"] <= parsed[i+1]["low"]:
                swing_lows.append(parsed[i]["low"])

        if not swing_highs:
            swing_highs = [max(p["high"] for p in parsed[:-2])]
        if not swing_lows:
            swing_lows = [min(p["low"] for p in parsed[:-2])]

        # Cluster levels within 0.15% to deduplicate
        def cluster_levels(levels, tol=0.0015):
            if not levels:
                return []
            sorted_lvls = sorted(levels)
            clusters = []
            curr_cluster = [sorted_lvls[0]]
            for l in sorted_lvls[1:]:
                if (l - curr_cluster[-1]) / curr_cluster[-1] <= tol:
                    curr_cluster.append(l)
                else:
                    clusters.append(sum(curr_cluster) / len(curr_cluster))
                    curr_cluster = [l]
            if curr_cluster:
                clusters.append(sum(curr_cluster) / len(curr_cluster))
            return [round(c, 4) for c in clusters]

        return {
            "highs": cluster_levels(swing_highs),
            "lows": cluster_levels(swing_lows),
            "latest_close": parsed[-1]["close"]
        }
    except Exception:
        return None

def scan_15m_rectangle_break_retest_scalp(symbol, candles_5m, levels_15m=None):
    """
    15m Key Level "Rectangle" Break & Retest Sniper Scalp (Mulham Trading):
    1. Identifies HTF 15m structural Highs (Resistance) & Lows (Support).
    2. Detects a 5m candle breaking cleanly through the 15m level.
    3. Defines the "Rectangle" zone encompassing the key level and breakout body.
    4. Confirms Retest + Rejection within the Rectangle (Role Reversal / S-to-R or R-to-S).
    5. Sets invalidation Stop Loss just outside the Rectangle and Take Profit at strict 1:2.0 R:R (2R).
    """
    if len(candles_5m) < 18:
        return None

    if levels_15m is None:
        levels_15m = fetch_15m_key_levels(symbol)

    if not levels_15m:
        return None

    highs = levels_15m.get("highs", [])
    lows = levels_15m.get("lows", [])
    if not highs and not lows:
        return None

    curr = candles_5m[-1]
    curr_c = curr["close"]
    curr_o = curr["open"]
    curr_h = curr["high"]
    curr_l = curr["low"]

    lookback = candles_5m[-14:-1]

    # --- CASE 1: RESISTANCE BREAKOUT -> SUPPORT RETEST (LONG ENTRY) ---
    for R in reversed(highs):
        # Find 5m candles in lookback that closed above R
        breakout_candidates = [
            (idx, c) for idx, c in enumerate(lookback)
            if c["close"] > R and c["close"] > c["open"]
        ]
        if breakout_candidates:
            bo_sub_idx, bo_candle = breakout_candidates[0]
            # Global index of breakout in candles_5m
            bo_global_idx = (len(candles_5m) - 14) + bo_sub_idx

            if bo_global_idx < len(candles_5m) - 1:
                rect_top = round(max(bo_candle["close"], R * 1.0005), 4)
                rect_bottom = round(min(bo_candle["open"], R * 0.9985), 4)

                post_candles = candles_5m[bo_global_idx + 1:]
                min_low = min(c["low"] for c in post_candles)
                min_close = min(c["close"] for c in post_candles)

                touched_rect = min_low <= rect_top * 1.0015
                held_base = min_close >= rect_bottom * 0.9975

                # Current candle rejection: closed above rect_bottom and bullish or long lower wick
                lower_wick = curr_c - curr_l
                full_range = max(curr_h - curr_l, 0.00001)
                is_bullish_reaction = (curr_c > curr_o) or (lower_wick / full_range >= 0.40)

                if touched_rect and held_base and is_bullish_reaction and curr_c >= rect_bottom:
                    retest_low = min(c["low"] for c in post_candles)
                    entry = curr_c
                    sl = round(min(rect_bottom, retest_low) * 0.9990, 4)
                    r_dist = entry - sl

                    if r_dist > 0 and (0.0010 <= (r_dist / entry) <= 0.045):
                        tp = round(entry + (r_dist * 2.0), 4)
                        return {
                            "symbol": symbol,
                            "side": "LONG",
                            "strategy": "5m 15m-Key-Level Rectangle Break & Retest",
                            "entry": entry,
                            "sl": sl,
                            "tp": tp,
                            "r_dist": round(r_dist, 4),
                            "rr_ratio": 2.0,
                            "is_scalp": True,
                            "is_mean_reversion_or_sweep": True,
                            "macro_aligned": True,
                            "timeframe": "5m",
                            "target_duration": "15-35 menit",
                            "reason": (
                                f"15m Resistance (${R:,.2f}) broken & flipped to Support: Rectangle [${rect_bottom:,.2f} - ${rect_top:,.2f}] "
                                f"retested with bullish rejection @ ${entry:,.2f}. SL @ ${sl:,.2f}, targeting 2R (${tp:,.2f})."
                            )
                        }

    # --- CASE 2: SUPPORT BREAKDOWN -> RESISTANCE RETEST (SHORT ENTRY) ---
    for S in lows:
        # Find 5m candles in lookback that closed below S
        breakdown_candidates = [
            (idx, c) for idx, c in enumerate(lookback)
            if c["close"] < S and c["close"] < c["open"]
        ]
        if breakdown_candidates:
            bd_sub_idx, bd_candle = breakdown_candidates[0]
            bd_global_idx = (len(candles_5m) - 14) + bd_sub_idx

            if bd_global_idx < len(candles_5m) - 1:
                rect_top = round(max(bd_candle["open"], S * 1.0015), 4)
                rect_bottom = round(min(bd_candle["close"], S * 0.9995), 4)

                post_candles = candles_5m[bd_global_idx + 1:]
                max_high = max(c["high"] for c in post_candles)
                max_close = max(c["close"] for c in post_candles)

                touched_rect = max_high >= rect_bottom * 0.9985
                held_ceiling = max_close <= rect_top * 1.0025

                # Current candle rejection: closed below rect_top and bearish or long upper wick
                upper_wick = curr_h - curr_c
                full_range = max(curr_h - curr_l, 0.00001)
                is_bearish_reaction = (curr_c < curr_o) or (upper_wick / full_range >= 0.40)

                if touched_rect and held_ceiling and is_bearish_reaction and curr_c <= rect_top:
                    retest_high = max(c["high"] for c in post_candles)
                    entry = curr_c
                    sl = round(max(rect_top, retest_high) * 1.0010, 4)
                    r_dist = sl - entry

                    if r_dist > 0 and (0.0010 <= (r_dist / entry) <= 0.045):
                        tp = round(entry - (r_dist * 2.0), 4)
                        return {
                            "symbol": symbol,
                            "side": "SHORT",
                            "strategy": "5m 15m-Key-Level Rectangle Break & Retest",
                            "entry": entry,
                            "sl": sl,
                            "tp": tp,
                            "r_dist": round(r_dist, 4),
                            "rr_ratio": 2.0,
                            "is_scalp": True,
                            "is_mean_reversion_or_sweep": True,
                            "macro_aligned": True,
                            "timeframe": "5m",
                            "target_duration": "15-35 menit",
                            "reason": (
                                f"15m Support (${S:,.2f}) broken & flipped to Resistance: Rectangle [${rect_bottom:,.2f} - ${rect_top:,.2f}] "
                                f"retested with bearish rejection @ ${entry:,.2f}. SL @ ${sl:,.2f}, targeting 2R (${tp:,.2f})."
                            )
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

# =====================================================================
# STRATEGY 8: 5m 20-EMA Dynamic Pullback Trap Scalp
# Reference: "(9 Wins Out of 10)... This 90% WIN RATE Scalping Strategy Should Be Illegal" (YouTube ll_9xH10KPY)
# =====================================================================
def calc_ema_series(values, period):
    """
    Computes exponential moving average series for the given values and period.
    """
    if not values:
        return []
    k = 2.0 / (period + 1.0)
    res = []
    ema = values[0]
    for v in values:
        ema = (v * k) + (ema * (1.0 - k))
        res.append(ema)
    return res

def scan_5m_20ema_pullback_trap_scalp(symbol, candles_5m):
    """
    Trader DNA 20-EMA Dynamic Pullback Trap Scalping Strategy:
    1. Identifies Trend Filter (Green / Red Market Bias via 20 EMA vs 50 EMA and 15m context).
    2. Detects a temporary counter-trend deviation / discount dip:
       - LONG: Price pulls back below 20 EMA in previous candles (discount liquidity trap).
       - SHORT: Price rallies above 20 EMA in previous candles (premium bull trap).
    3. Confirms rejection and reclaim of 20 EMA on current candle:
       - LONG: Current candle closes back ABOVE 20 EMA with bullish body/wick.
       - SHORT: Current candle closes back BELOW 20 EMA with bearish body/wick.
    4. Places Stop Loss at the swing extreme of the pullback/rally.
    5. Sets Take Profit at strict 1:2.0 R:R (2R).
    """
    if len(candles_5m) < 25:
        return None

    closes = [c["close"] for c in candles_5m]
    ema20_s = calc_ema_series(closes, 20)
    ema50_s = calc_ema_series(closes, 50)

    if not ema20_s or not ema50_s:
        return None

    curr = candles_5m[-1]
    curr_c = curr["close"]
    curr_o = curr["open"]
    curr_ema20 = ema20_s[-1]
    curr_ema50 = ema50_s[-1]

    ctx = get_15m_context(symbol)
    m15_bias = ctx.get("bias", "NEUTRAL")

    pullback_window = candles_5m[-6:-1]
    prev = candles_5m[-2]

    # --- CASE 1: BULLISH 20-EMA PULLBACK TRAP (LONG ENTRY) ---
    is_bullish_trend = (curr_ema20 >= curr_ema50) or (m15_bias == "BULLISH")
    if is_bullish_trend and m15_bias != "BEARISH":
        dipped_below = any(c["low"] < ema20_s[-(6 - idx)] for idx, c in enumerate(pullback_window))
        reclaimed = (curr_c > curr_ema20) and (curr_c > curr_o) and (prev["close"] <= curr_ema20 * 1.0015)

        if dipped_below and reclaimed:
            pullback_low = min(c["low"] for c in candles_5m[-6:])
            entry = curr_c
            sl = round(pullback_low * 0.9990, 4)
            r_dist = entry - sl

            if r_dist > 0 and (0.0010 <= (r_dist / entry) <= 0.040):
                tp = round(entry + (r_dist * 2.0), 4)
                return {
                    "symbol": symbol,
                    "side": "LONG",
                    "strategy": "5m 20-EMA Dynamic Pullback Trap",
                    "entry": entry,
                    "sl": sl,
                    "tp": tp,
                    "r_dist": round(r_dist, 4),
                    "rr_ratio": 2.0,
                    "is_scalp": True,
                    "is_mean_reversion_or_sweep": True,
                    "macro_aligned": True,
                    "timeframe": "5m",
                    "target_duration": "10-25 menit",
                    "reason": (
                        f"20-EMA Discount Trap: Price dipped below 20 EMA (${curr_ema20:,.2f}) to ${pullback_low:,.2f} "
                        f"and reclaimed with bullish close @ ${entry:,.2f}. SL @ ${sl:,.2f}, targeting 2R (${tp:,.2f})."
                    )
                }

    # --- CASE 2: BEARISH 20-EMA PULLBACK TRAP (SHORT ENTRY) ---
    is_bearish_trend = (curr_ema20 <= curr_ema50) or (m15_bias == "BEARISH")
    if is_bearish_trend and m15_bias != "BULLISH":
        rallied_above = any(c["high"] > ema20_s[-(6 - idx)] for idx, c in enumerate(pullback_window))
        reclaimed = (curr_c < curr_ema20) and (curr_c < curr_o) and (prev["close"] >= curr_ema20 * 0.9985)

        if rallied_above and reclaimed:
            rally_high = max(c["high"] for c in candles_5m[-6:])
            entry = curr_c
            sl = round(rally_high * 1.0010, 4)
            r_dist = sl - entry

            if r_dist > 0 and (0.0010 <= (r_dist / entry) <= 0.040):
                tp = round(entry - (r_dist * 2.0), 4)
                return {
                    "symbol": symbol,
                    "side": "SHORT",
                    "strategy": "5m 20-EMA Dynamic Pullback Trap",
                    "entry": entry,
                    "sl": sl,
                    "tp": tp,
                    "r_dist": round(r_dist, 4),
                    "rr_ratio": 2.0,
                    "is_scalp": True,
                    "is_mean_reversion_or_sweep": True,
                    "macro_aligned": True,
                    "timeframe": "5m",
                    "target_duration": "10-25 menit",
                    "reason": (
                        f"20-EMA Premium Trap: Price rallied above 20 EMA (${curr_ema20:,.2f}) to ${rally_high:,.2f} "
                        f"and rejected with bearish close @ ${entry:,.2f}. SL @ ${sl:,.2f}, targeting 2R (${tp:,.2f})."
                    )
                }

# =====================================================================
# STRATEGY 9: 5m Akademi Crypto High Win-Rate Scalping Blueprint
# Reference: Akademi Crypto Curriculum & "Strategi Scalping Crypto Win Rate Tinggi"
# =====================================================================
def calc_stochastic(candles, k_period=14, d_period=3):
    """
    Calculates 14-period Stochastic Oscillator (%K and %D with d_period SMA smoothing).
    Returns dict {"k": float, "d": float, "prev_k": float, "prev_d": float}.
    """
    if len(candles) < k_period + d_period:
        return None

    raw_k = []
    start_idx = max(0, len(candles) - (d_period + 1))
    for i in range(start_idx, len(candles)):
        window = candles[max(0, i - k_period + 1) : i + 1]
        highest_h = max(c["high"] for c in window)
        lowest_l = min(c["low"] for c in window)
        curr_c = candles[i]["close"]
        hl_range = max(highest_h - lowest_l, 0.00001)
        k_val = ((curr_c - lowest_l) / hl_range) * 100.0
        raw_k.append(k_val)

    if len(raw_k) < d_period + 1:
        return None

    curr_k = raw_k[-1]
    prev_k = raw_k[-2]
    curr_d = sum(raw_k[-d_period:]) / float(d_period)
    prev_d = sum(raw_k[-d_period - 1 : -1]) / float(d_period)

    return {
        "k": round(curr_k, 2),
        "d": round(curr_d, 2),
        "prev_k": round(prev_k, 2),
        "prev_d": round(prev_d, 2)
    }

def scan_5m_akademi_crypto_scalp(symbol, candles_5m):
    """
    Akademi Crypto Standard High Win-Rate Scalping Blueprint:
    1. Multi-Timeframe Institutional Trend Alignment (15m Context + 50 EMA).
    2. 5m EMA Dynamic Pocket: Fast EMA 9 (momentum) vs Base EMA 21 (equilibrium).
    3. Momentum Oscillator Filter: Stochastic 14,3,3 in Oversold/Overbought zone.
       - LONG: Price pulls into EMA 9/21 pocket while Stoch %K <= 35 or bullish hook (%K > %D).
       - SHORT: Price rallies into EMA 9/21 pocket while Stoch %K >= 65 or bearish hook (%K < %D).
    4. Price Action Rejection: Confirmation candle bouncing out of the pocket.
    5. Strict 1:2.0 R:R (2R) with Micro-Breakeven (+0.60R) protection.
    """
    if len(candles_5m) < 25:
        return None

    closes = [c["close"] for c in candles_5m]
    ema9_s = calc_ema_series(closes, 9)
    ema21_s = calc_ema_series(closes, 21)
    ema50_s = calc_ema_series(closes, 50)

    if not ema9_s or not ema21_s or not ema50_s:
        return None

    stoch = calc_stochastic(candles_5m, k_period=14, d_period=3)
    if not stoch:
        return None

    curr = candles_5m[-1]
    curr_c = curr["close"]
    curr_o = curr["open"]
    curr_h = curr["high"]
    curr_l = curr["low"]

    curr_ema9 = ema9_s[-1]
    curr_ema21 = ema21_s[-1]
    curr_ema50 = ema50_s[-1]

    ctx = get_15m_context(symbol)
    m15_bias = ctx.get("bias", "NEUTRAL")

    pullback_window = candles_5m[-5:]

    # --- CASE 1: AKADEMI CRYPTO BULLISH SCALP (LONG SETUP) ---
    is_bullish_trend = (curr_ema9 >= curr_ema21) and (curr_ema21 >= curr_ema50 * 0.9975)
    if is_bullish_trend and m15_bias != "BEARISH":
        tested_pocket = any(
            c["low"] <= ema9_s[-(5 - idx)] * 1.0015 and c["low"] >= ema21_s[-(5 - idx)] * 0.9960
            for idx, c in enumerate(pullback_window)
        )
        # Stochastic confirmation: %K in oversold (<= 40) or hooked up out of oversold (prev_k <= 35)
        stoch_confirmed = (stoch["k"] <= 40.0) or (stoch["prev_k"] <= 35.0) or (stoch["k"] >= stoch["d"] and stoch["prev_k"] <= 45.0)
        is_bullish_bounce = (curr_c > curr_o) and (curr_c >= curr_ema9 * 0.9990)

        if tested_pocket and stoch_confirmed and is_bullish_bounce:
            pocket_low = min(c["low"] for c in pullback_window)
            entry = curr_c
            sl = round(min(curr_ema21, pocket_low) * 0.9990, 4)
            r_dist = round(entry - sl, 4)

            if r_dist > 0 and (0.0010 <= (r_dist / entry) <= 0.040):
                tp = round(entry + (r_dist * 2.0), 4)
                return {
                    "symbol": symbol,
                    "side": "LONG",
                    "strategy": "5m Akademi Crypto High Win-Rate Scalp",
                    "entry": entry,
                    "sl": sl,
                    "tp": tp,
                    "r_dist": round(r_dist, 4),
                    "rr_ratio": 2.0,
                    "is_scalp": True,
                    "is_mean_reversion_or_sweep": True,
                    "macro_aligned": True,
                    "timeframe": "5m",
                    "target_duration": "15-30 menit",
                    "reason": (
                        f"Akademi Crypto Pocket Bounce: Tested EMA 9/21 dynamic pocket (${curr_ema21:,.2f}-${curr_ema9:,.2f}) "
                        f"with Stoch %K @ {stoch['k']:.1f} (prev %K @ {stoch['prev_k']:.1f} Oversold Hook). Bullish close @ ${entry:,.2f}, targeting 2R (${tp:,.2f})."
                    )
                }

    # --- CASE 2: AKADEMI CRYPTO BEARISH SCALP (SHORT SETUP) ---
    is_bearish_trend = (curr_ema9 <= curr_ema21) and (curr_ema21 <= curr_ema50 * 1.0025)
    if is_bearish_trend and m15_bias != "BULLISH":
        tested_pocket = any(
            c["high"] >= ema9_s[-(5 - idx)] * 0.9985 and c["high"] <= ema21_s[-(5 - idx)] * 1.0040
            for idx, c in enumerate(pullback_window)
        )
        # Stochastic confirmation: %K in overbought (>= 60) or hooked down out of overbought (prev_k >= 65)
        stoch_confirmed = (stoch["k"] >= 60.0) or (stoch["prev_k"] >= 65.0) or (stoch["k"] <= stoch["d"] and stoch["prev_k"] >= 55.0)
        is_bearish_bounce = (curr_c < curr_o) and (curr_c <= curr_ema9 * 1.0010)

        if tested_pocket and stoch_confirmed and is_bearish_bounce:
            pocket_high = max(c["high"] for c in pullback_window)
            entry = curr_c
            sl = round(max(curr_ema21, pocket_high) * 1.0010, 4)
            r_dist = round(sl - entry, 4)

            if r_dist > 0 and (0.0010 <= (r_dist / entry) <= 0.040):
                tp = round(entry - (r_dist * 2.0), 4)
                return {
                    "symbol": symbol,
                    "side": "SHORT",
                    "strategy": "5m Akademi Crypto High Win-Rate Scalp",
                    "entry": entry,
                    "sl": sl,
                    "tp": tp,
                    "r_dist": round(r_dist, 4),
                    "rr_ratio": 2.0,
                    "is_scalp": True,
                    "is_mean_reversion_or_sweep": True,
                    "macro_aligned": True,
                    "timeframe": "5m",
                    "target_duration": "15-30 menit",
                    "reason": (
                        f"Akademi Crypto Pocket Rejection: Tested EMA 9/21 dynamic pocket (${curr_ema9:,.2f}-${curr_ema21:,.2f}) "
                        f"with Stoch %K @ {stoch['k']:.1f} (prev %K @ {stoch['prev_k']:.1f} Overbought Hook). Bearish close @ ${entry:,.2f}, targeting 2R (${tp:,.2f})."
                    )
                }

    return None

def scan_symbol_scalp(symbol):
    """
    Runs fast scalp strategies on a single symbol. Returns the best signal if found.
    Focuses exclusively on Elite Institutional Crypto Micro-Structure & Liquidity Trap setups:
    1. ICT Rejection Block 50% Mean Threshold
    2. 4H Range Breakout & Re-Entry Failure (Failed Auction)
    3. Inverse FVG (IFVG) Liquidity Scalp
    4. 15m Key Level Rectangle Break & Retest (Mulham Sniper)
    5. 20-EMA Dynamic Pullback Trap (Trend Following)
    6. 5m Liquidity Sweep & Micro-FVG (Smart Money Trap)
    
    [DEACTIVATED / SISISIHKAN]:
    - Volume Surge Momentum (High False Positive / Exhaustion Dump Trap)
    - Blind VWAP ±2σ Mean-Reversion (Band-Riding Trend Runover Risk)
    - EMA 9/21 + Stochastic Cross (Lagging Oscillator Whipsaw in 5m Chop)
    """
    candles = fetch_scalp_candles(symbol, bar="5m", limit=60)
    if len(candles) < 25:
        return None

    # Priority 0: Order Flow CVD Divergence & DOM Stacked Imbalance Scalp
    try:
        import orderflow_cvd_scalper
        s_of = orderflow_cvd_scalper.scan_5m_orderflow_cvd_scalp(symbol, candles)
        if s_of:
            return s_of
    except Exception:
        pass

    # Priority 0.5: 5m/15m Opening Range Breakout (ORB V4.1 - London / NY / Daily Open Momentum)
    try:
        import orb_scalper
        s_orb = orb_scalper.scan_5m_orb_scalp(symbol, candles)
        if s_orb:
            return s_orb
    except Exception:
        pass

    # Priority 1: ICT Rejection Block Mean Threshold Bounce (Pure Wick Manipulation Trap)
    s_rb = scan_rejection_block_scalp(symbol, candles)
    if s_rb:
        return s_rb

    # Priority 2: 4H Range Breakout & Re-Entry Failure (Failed Auction / Macro Fakeout)
    s_4h = scan_4h_range_reentry_scalp(symbol, candles)
    if s_4h:
        return s_4h

    # Priority 3: 5m Inverse FVG (IFVG) Liquidity Scalp (Institutional Role Reversal)
    s_ifvg = scan_5m_inverse_fvg_scalp(symbol, candles)
    if s_ifvg:
        return s_ifvg

    # Priority 4: 15m Key Level Rectangle Break & Retest (Mulham Sniper Structural Retest)
    s_rect = scan_15m_rectangle_break_retest_scalp(symbol, candles)
    if s_rect:
        return s_rect

    # Priority 5: 5m 20-EMA Dynamic Pullback Trap (Trend-Following Discount Entry)
    s_ema = scan_5m_20ema_pullback_trap_scalp(symbol, candles)
    if s_ema:
        return s_ema

    # Priority 6: Liquidity Sweep & Micro-FVG (Smart Money BSL/SSL Hunt)
    s_sweep = scan_5m_liquidity_sweep_fvg(symbol, candles)
    if s_sweep:
        return s_sweep

    # Note: Volume Surge, VWAP ±2σ, and Stoch MA Crossover are intentionally bypassed.
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
    print("       ⚡ FAST SCALPER ENGINE (5m / 15m Institutional Crypto)")
    print("=" * 65)
    print("Memindai peluang scalping likuiditas institusional (Rejection Block, 4H Fakeout, IFVG, Mulham 15m)...")
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

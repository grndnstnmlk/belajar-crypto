"""
session_adaptive_strategy.py - 24/7 Session-Adaptive Multi-Regime Strategy Engine
Dynamically aligns algorithmic trading strategies with the 4 distinct global liquidity sessions:

1. 🇯🇵 ASIAN SESSION (07:00 - 13:00 WIB / 00:00 - 06:00 UTC):
   - Strategy: VWAP & Value Area Boundary Mean Reversion (Tight SL, Range Inversion).

2. 🇬🇧 LONDON KILL ZONE (14:00 - 18:00 WIB / 07:00 - 11:00 UTC):
   - Strategy: Asian Range Liquidity Sweep & Judas Swing Reversal (Sweep of Asian High/Low -> 1:3.5R Expansion).

3. 🇺🇸 NEW YORK KILL ZONE (19:30 - 23:30 WIB / 12:30 - 16:30 UTC):
   - Strategy: Institutional FVG Trend Expansion & Order Flow Breakout (High-velocity runners).

4. 🌙 ASIAN PRE-MARKET & DEAD ZONE (00:00 - 06:50 WIB / 17:00 - 23:50 UTC):
   - Strategy: Defensive Boundary Squeeze & Asian Range Builder (Records Asian High/Low, Blocks High-Risk Breakouts).

5. 🛡️ UNIVERSAL 24/7 ANTI-STALL TIME-DECAY SHIELD:
   - Closes dormant trades (>120 mins without momentum) at Breakeven to free capital.
"""

import os
import sys
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Windows console UTF-8 safety
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
sys.path.insert(0, TOOLS_DIR)

WIB = timezone(timedelta(hours=7))

# -------------------------------------------------------------
# 1. 24-Hour Session Classifier
# -------------------------------------------------------------
def get_active_24h_regime(dt=None) -> Dict[str, Any]:
    """Classifies the exact 24-hour session window and selects the optimal strategy profile."""
    if dt is None:
        dt_utc = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt_utc = dt.replace(tzinfo=WIB).astimezone(timezone.utc)
    else:
        dt_utc = dt.astimezone(timezone.utc)

    dt_wib = dt_utc.astimezone(WIB)
    wib_hour = dt_wib.hour + (dt_wib.minute / 60.0)

    if 19.5 <= wib_hour < 23.5:
        return {
            "session_code": "NY_KZ",
            "session_name": "🇺🇸 NEW YORK KILL ZONE",
            "optimal_strategy": "NY_INSTITUTIONAL_TREND_EXPANSION",
            "min_rr": 3.5,
            "style": "TREND_RUNNER",
            "description": "High institutional volume & macro trend continuation. Ideal for 1:3.5R+ runners."
        }
    elif 14.0 <= wib_hour < 18.0:
        return {
            "session_code": "LONDON_KZ",
            "session_name": "🇬🇧 LONDON KILL ZONE",
            "optimal_strategy": "LONDON_JUDAS_SWING_SWEEP",
            "min_rr": 3.0,
            "style": "LIQUIDITY_SWEEP_REVERSAL",
            "description": "Sweeps of Asian High/Low -> High probability reversal expansions."
        }
    elif 7.0 <= wib_hour < 13.0:
        return {
            "session_code": "ASIA",
            "session_name": "🇯🇵 ASIAN ACCUMULATION",
            "optimal_strategy": "ASIAN_RANGE_MEAN_REVERSION",
            "min_rr": 2.5,
            "style": "RANGE_MEAN_REVERSION",
            "description": "Value Area & VWAP bounce between established consolidation boundaries."
        }
    else:
        return {
            "session_code": "DEAD_ZONE",
            "session_name": "🌙 ASIAN PRE-MARKET / DEFENSIVE SQUEEZE",
            "optimal_strategy": "DEFENSIVE_ASIAN_RANGE_BUILDER",
            "min_rr": 3.0,
            "style": "CAPITAL_PRESERVATION",
            "description": "Establishes Asian Range High/Low boundaries. High-bar selective execution."
        }

# -------------------------------------------------------------
# 2. Asian Range (High/Low) & London Judas Swing Detector
# -------------------------------------------------------------
def calculate_asian_range_and_judas_setup(candles_15m: List[List[Any]]) -> Dict[str, Any]:
    """
    Computes Asian Range boundaries (00:00 - 07:00 WIB) and detects London Judas Swing:
    - Judas High Sweep (Sell Signal): Price spikes above Asian High during London KZ then immediately closes back inside range.
    - Judas Low Sweep (Buy Signal): Price spikes below Asian Low during London KZ then immediately closes back inside range.
    """
    if not candles_15m or len(candles_15m) < 32:
        return {"has_judas": False, "signal": "NONE", "summary": "Insufficient candles for Asian range"}

    # Take candles from past 24 hours
    recent = candles_15m[-32:]
    highs = [float(c[2]) for c in recent]
    lows = [float(c[3]) for c in recent]
    closes = [float(c[4]) for c in recent]

    asian_high = max(highs[:24])
    asian_low = min(lows[:24])
    asian_range_height = max(asian_high - asian_low, 0.0001)

    curr_close = closes[-1]
    curr_high = highs[-1]
    curr_low = lows[-1]

    # Judas Bullish Reversal: Spiked below Asian Low during London KZ, closed back above Asian Low
    if curr_low < asian_low and curr_close > (asian_low + 0.05 * asian_range_height):
        dist_sl = max(curr_close - (curr_low * 0.998), curr_close * 0.005)
        entry = curr_close
        sl = round(curr_low * 0.998, 4)
        tp = round(entry + (dist_sl * 3.5), 4)
        rr = (tp - entry) / dist_sl
        return {
            "has_judas": True,
            "signal": "BULLISH_JUDAS_SWING",
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "rr": round(rr, 2),
            "asian_high": round(asian_high, 4),
            "asian_low": round(asian_low, 4),
            "summary": f"🇬🇧 LONDON JUDAS SWING (LONG): Asian Low swept @ ${asian_low:,.4f} -> Bullish Reversal | Target R:R 1:{rr:.2f}"
        }

    # Judas Bearish Reversal: Spiked above Asian High during London KZ, closed back below Asian High
    if curr_high > asian_high and curr_close < (asian_high - 0.05 * asian_range_height):
        dist_sl = max((curr_high * 1.002) - curr_close, curr_close * 0.005)
        entry = curr_close
        sl = round(curr_high * 1.002, 4)
        tp = round(entry - (dist_sl * 3.5), 4)
        rr = (entry - tp) / dist_sl
        return {
            "has_judas": True,
            "signal": "BEARISH_JUDAS_SWING",
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "rr": round(rr, 2),
            "asian_high": round(asian_high, 4),
            "asian_low": round(asian_low, 4),
            "summary": f"🇬🇧 LONDON JUDAS SWING (SHORT): Asian High swept @ ${asian_high:,.4f} -> Bearish Reversal | Target R:R 1:{rr:.2f}"
        }

    return {
        "has_judas": False,
        "signal": "NONE",
        "asian_high": round(asian_high, 4),
        "asian_low": round(asian_low, 4),
        "summary": f"Asian Range: Low ${asian_low:,.4f} - High ${asian_high:,.4f} (No Judas Sweep Active)"
    }

# -------------------------------------------------------------
# 3. Universal Anti-Stall Time-Decay Shield
# -------------------------------------------------------------
def audit_trade_dormancy_and_stall(opened_at_str: str, current_r: float, max_stagnant_minutes: int = 120) -> Dict[str, Any]:
    """
    Protects capital from stagnant sideways chop:
    If a trade is open for > 120 minutes and floating between -0.3R and +0.3R,
    signals an Anti-Stall Early Exit at Breakeven.
    """
    try:
        dt_opened = datetime.strptime(opened_at_str, "%Y-%m-%d %H:%M:%S")
        elapsed_minutes = (datetime.now() - dt_opened).total_seconds() / 60.0
    except Exception:
        elapsed_minutes = 0.0

    is_stalled = False
    action = "HOLD"
    reason = "Trade running within normal parameters"

    if elapsed_minutes >= max_stagnant_minutes:
        if -0.35 <= current_r <= 0.35:
            is_stalled = True
            action = "AUTO_EXIT_BREAKEVEN_STALL"
            reason = f"🛡️ ANTI-STALL SHIELD: Trade stagnant for {elapsed_minutes:.0f} mins with zero momentum (R={current_r:+.2f}). Auto-exit at BE to preserve capital."

    return {
        "is_stalled": is_stalled,
        "elapsed_minutes": round(elapsed_minutes, 1),
        "current_r": current_r,
        "action": action,
        "reason": reason
    }

if __name__ == "__main__":
    reg = get_active_24h_regime()
    print("=== 24/7 SESSION-ADAPTIVE STRATEGY AUDIT ===")
    print(f"Sesi Saat Ini     : {reg['session_name']} ({reg['session_code']})")
    print(f"Strategi Optimal  : {reg['optimal_strategy']}")
    print(f"Target R:R        : Minimum 1:{reg['min_rr']}R")
    print(f"Karakteristik     : {reg['description']}")

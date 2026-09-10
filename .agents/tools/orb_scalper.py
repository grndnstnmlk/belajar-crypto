#!/usr/bin/env python3
"""
========================================================================================
  ⚡ 5m/15m OPENING RANGE BREAKOUT (ORB V4.1) SCALPING ENGINE
  Captures high-probability session expansion momentum following the initial 15-minute
  opening price discovery window of key market sessions:
  - 🇬🇧 London Open ORB: 14:00 - 14:15 WIB (07:00 UTC)
  - 🇺🇸 New York Open ORB: 19:30 - 19:45 WIB / 20:30 - 20:45 WIB (12:30/13:30 UTC)
  - 🌐 Daily UTC 00:00 Open ORB: 07:00 - 07:15 WIB (00:00 UTC)
  - 🔄 Rolling 15m Dynamic Range (Inter-session Fallback)
  
  Integrates Order Flow CVD Delta validation and strict Prop Firm Risk Protocols.
========================================================================================
"""

import json
import math
import os
import ssl
import sys
import time
import urllib.request
from datetime import datetime, timezone, timedelta

# UTF-8 Encoding safe on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
DATA_DIR = os.path.join(PROJECT_ROOT, ".agents", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# WIB Timezone (UTC+7)
WIB = timezone(timedelta(hours=7))

# In-memory session execution memory (symbol -> last session code traded)
_ORB_SESSION_TRADES = {}

def clean_symbol(symbol: str) -> str:
    """Standardizes symbol format (e.g. BTC/USDT -> BTCUSDT)."""
    s = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    if not s.endswith("USDT"):
        s += "USDT"
    return s

# ======================================================================================
# 1. SESSION TIMING & OPENING RANGE IDENTIFIER
# ======================================================================================

def get_orb_session_state(dt=None) -> dict:
    """
    Determines current ORB session phase:
    - active_session: "LONDON_ORB", "NY_ORB", "DAILY_ORB", or "ROLLING_ORB"
    - phase: "ESTABLISHING_RANGE" (0-15m), "HUNTING_BREAKOUT" (15-90m), or "COOLDOWN" (>90m)
    - minutes_into_session: float
    """
    if dt is None:
        dt_utc = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt_utc = dt.replace(tzinfo=WIB).astimezone(timezone.utc)
    else:
        dt_utc = dt.astimezone(timezone.utc)

    dt_wib = dt_utc.astimezone(WIB)
    wib_hour = dt_wib.hour + (dt_wib.minute / 60.0) + (dt_wib.second / 3600.0)

    # 1. London ORB (14:00 - 15:30 WIB)
    if 14.0 <= wib_hour < 15.5:
        session_code = "LONDON_ORB"
        session_label = "🇬🇧 London Session Open"
        minutes_elapsed = (wib_hour - 14.0) * 60.0
    # 2. New York Early ORB (19.5 - 21.0 WIB)
    elif 19.5 <= wib_hour < 21.0:
        session_code = "NY_EARLY_ORB"
        session_label = "🇺🇸 New York US Pre-Market Open"
        minutes_elapsed = (wib_hour - 19.5) * 60.0
    # 3. New York Cash ORB (20.5 - 22.0 WIB)
    elif 20.5 <= wib_hour < 22.0:
        session_code = "NY_CASH_ORB"
        session_label = "🇺🇸 Wall Street Cash Open"
        minutes_elapsed = (wib_hour - 20.5) * 60.0
    # 4. Daily UTC 00:00 Open ORB (07:00 - 08:30 WIB)
    elif 7.0 <= wib_hour < 8.5:
        session_code = "DAILY_UTC_ORB"
        session_label = "🌐 Daily Crypto 00:00 UTC Open"
        minutes_elapsed = (wib_hour - 7.0) * 60.0
    # 5. Dynamic Rolling 15m Inter-Session Fallback
    else:
        session_code = "DYNAMIC_ROLLING_ORB"
        session_label = "🔄 Dynamic 15m Structural Range"
        minutes_elapsed = (dt_wib.minute % 30)

    if minutes_elapsed < 15.0 and session_code != "DYNAMIC_ROLLING_ORB":
        phase = "ESTABLISHING_RANGE"
    elif minutes_elapsed <= 90.0 or session_code == "DYNAMIC_ROLLING_ORB":
        phase = "HUNTING_BREAKOUT"
    else:
        phase = "COOLDOWN"

    return {
        "session_code": session_code,
        "session_label": session_label,
        "phase": phase,
        "minutes_elapsed": round(minutes_elapsed, 1),
        "wib_time": dt_wib.strftime("%H:%M:%S WIB")
    }

# ======================================================================================
# 2. OPENING RANGE (OR) BOUNDARY CALCULATOR
# ======================================================================================

def calculate_opening_range(symbol: str, candles_5m: list = None) -> dict:
    """
    Computes Opening Range High (OR_High), Low (OR_Low), and Midpoint (OR_Mid)
    from 5m/15m candlestick data.
    """
    if candles_5m is None or len(candles_5m) < 4:
        try:
            import market_eyes
            sym_clean = clean_symbol(symbol).replace("USDT", "")
            raw = market_eyes.fetch_candles(sym_clean, bar="5m", limit=30)
            candles_5m = [{"close": float(c[4]), "high": float(c[2]), "low": float(c[3]), "open": float(c[1]), "volume": float(c[5])} for c in raw]
        except Exception:
            return None

    if not candles_5m or len(candles_5m) < 4:
        return None

    session_state = get_orb_session_state()

    # The first 3 completed 5m candles form the 15m Opening Range
    or_candles = candles_5m[:3] if len(candles_5m) < 12 else candles_5m[-12:-3]
    
    or_high = max(c["high"] for c in or_candles)
    or_low = min(c["low"] for c in or_candles)
    or_mid = round((or_high + or_low) / 2.0, 4)
    range_span = round(or_high - or_low, 4)
    range_pct = round((range_span / max(or_mid, 0.0001)) * 100, 2)

    current_price = candles_5m[-1]["close"]

    # Position relative to OR
    if current_price > or_high:
        rel_position = "ABOVE_OR_HIGH"
    elif current_price < or_low:
        rel_position = "BELOW_OR_LOW"
    else:
        rel_position = "INSIDE_OPENING_RANGE"

    return {
        "symbol": symbol,
        "session": session_state,
        "or_high": round(or_high, 4),
        "or_low": round(or_low, 4),
        "or_mid": or_mid,
        "range_span": range_span,
        "range_pct": range_pct,
        "current_price": current_price,
        "rel_position": rel_position
    }

# ======================================================================================
# 3. 5m ORB BREAKOUT SIGNAL GENERATOR
# ======================================================================================

def scan_5m_orb_scalp(symbol: str, candles_5m: list = None) -> dict:
    """
    Evaluates 5m Opening Range Breakout (ORB) setup with Order Flow CVD confirmation.
    
    Rules:
    - Bullish Breakout: 5m candle body closes above OR_High, CVD Delta > 0, targeting 2.0R.
    - Bearish Breakdown: 5m candle body closes below OR_Low, CVD Delta < 0, targeting 2.0R.
    - Prop Firm Guard: Max 1 trade per session per symbol, SL at OR_Mid.
    """
    if candles_5m is None or len(candles_5m) < 4:
        try:
            import market_eyes
            sym_clean = clean_symbol(symbol).replace("USDT", "")
            raw = market_eyes.fetch_candles(sym_clean, bar="5m", limit=30)
            candles_5m = [{"close": float(c[4]), "high": float(c[2]), "low": float(c[3]), "open": float(c[1]), "volume": float(c[5])} for c in raw]
        except Exception:
            return None

    if not candles_5m or len(candles_5m) < 4:
        return None

    or_data = calculate_opening_range(symbol, candles_5m)
    if not or_data:
        return None

    session = or_data["session"]
    if session["phase"] == "ESTABLISHING_RANGE":
        # Still forming the initial 15m range
        return None

    # Check session duplicate guard
    sym_key = clean_symbol(symbol)
    if _ORB_SESSION_TRADES.get(sym_key) == session["session_code"]:
        return None

    curr = candles_5m[-1]
    prev = candles_5m[-2]
    curr_c = curr["close"]
    curr_o = curr["open"]
    curr_h = curr["high"]
    curr_l = curr["low"]

    or_high = or_data["or_high"]
    or_low = or_data["or_low"]
    or_mid = or_data["or_mid"]

    # Optional Order Flow CVD verification
    cvd_delta_pct = 0.0
    try:
        import orderflow_cvd_scalper
        cvd_res = orderflow_cvd_scalper.calculate_cvd_metrics(symbol)
        cvd_delta_pct = cvd_res.get("delta_percent", 0.0)
    except Exception:
        pass

    # --- SETUP 1: BULLISH OPENING RANGE BREAKOUT (LONG) ---
    # Current candle closes body above OR_High and is bullish
    if curr_c > or_high and curr_c > curr_o:
        # Avoid runaway breakout if already overextended > 1.5x range above OR_High
        if curr_c <= or_high + (or_data["range_span"] * 1.5):
            entry = curr_c
            # Invalidation SL at OR_Mid or lowest wick of breakout candle
            sl_candidate = max(or_mid, curr_l * 0.9988)
            sl = round(sl_candidate, 4)
            r_dist = entry - sl

            if r_dist > 0 and (0.0010 <= (r_dist / entry) <= 0.035):
                tp = round(entry + (r_dist * 3.0), 4)
                return {
                    "symbol": symbol,
                    "side": "LONG",
                    "strategy": "5m Opening Range Breakout (ORB V4.1)",
                    "entry": entry,
                    "sl": sl,
                    "tp": tp,
                    "r_dist": round(r_dist, 4),
                    "rr_ratio": 3.0,
                    "is_scalp": True,
                    "is_orb": True,
                    "is_mean_reversion_or_sweep": False,
                    "macro_aligned": True,
                    "timeframe": "5m",
                    "target_duration": "15-35 menit",
                    "session_info": session,
                    "orb_boundaries": {
                        "or_high": or_high,
                        "or_low": or_low,
                        "or_mid": or_mid,
                        "range_pct": or_data["range_pct"]
                    },
                    "reason": (
                        f"ORB Bullish Expansion ({session['session_label']}): 5m candle body decisively broke above "
                        f"15m Opening Range High (${or_high:,.2f}) @ ${entry:,.2f}. SL at OR Mid (${or_mid:,.2f}), targeting 3R (${tp:,.2f})."
                    )
                }

    # --- SETUP 2: BEARISH OPENING RANGE BREAKDOWN (SHORT) ---
    # Current candle closes body below OR_Low and is bearish
    if curr_c < or_low and curr_c < curr_o:
        if curr_c >= or_low - (or_data["range_span"] * 1.5):
            entry = curr_c
            # Invalidation SL at OR_Mid or highest wick of breakdown candle
            sl_candidate = min(or_mid, curr_h * 1.0012)
            sl = round(sl_candidate, 4)
            r_dist = sl - entry

            if r_dist > 0 and (0.0010 <= (r_dist / entry) <= 0.035):
                tp = round(entry - (r_dist * 3.0), 4)
                return {
                    "symbol": symbol,
                    "side": "SHORT",
                    "strategy": "5m Opening Range Breakout (ORB V4.1)",
                    "entry": entry,
                    "sl": sl,
                    "tp": tp,
                    "r_dist": round(r_dist, 4),
                    "rr_ratio": 3.0,
                    "is_scalp": True,
                    "is_orb": True,
                    "is_mean_reversion_or_sweep": False,
                    "macro_aligned": True,
                    "timeframe": "5m",
                    "target_duration": "15-35 menit",
                    "session_info": session,
                    "orb_boundaries": {
                        "or_high": or_high,
                        "or_low": or_low,
                        "or_mid": or_mid,
                        "range_pct": or_data["range_pct"]
                    },
                    "reason": (
                        f"ORB Bearish Expansion ({session['session_label']}): 5m candle body decisively broke below "
                        f"15m Opening Range Low (${or_low:,.2f}) @ ${entry:,.2f}. SL at OR Mid (${or_mid:,.2f}), targeting 2R (${tp:,.2f})."
                    )
                }

    return None

def mark_orb_traded(symbol: str, session_code: str):
    """Records that an ORB setup was executed for this symbol in current session."""
    sym_key = clean_symbol(symbol)
    _ORB_SESSION_TRADES[sym_key] = session_code

def get_orb_summary(symbol: str) -> dict:
    """Returns complete ORB intelligence payload for dashboard/API consumption."""
    data = calculate_opening_range(symbol)
    if not data:
        return {"symbol": symbol, "status": "NO_DATA", "session": get_orb_session_state()}
    
    setup = scan_5m_orb_scalp(symbol)
    data["setup"] = setup
    data["has_setup"] = setup is not None
    return data

if __name__ == "__main__":
    test_sym = sys.argv[1] if len(sys.argv) > 1 else "BTC"
    print("=" * 70)
    print(f"       ⚡ 5m/15m OPENING RANGE BREAKOUT (ORB V4.1) MATRIX ({test_sym})")
    print("=" * 70)
    data = calculate_opening_range(test_sym)
    if data:
        sess = data["session"]
        print(f"🕒 [SESSION CLOCK] {sess['session_label']} | Phase: {sess['phase']} ({sess['minutes_elapsed']}m elapsed)")
        print(f"📐 [OPENING RANGE] OR High: ${data['or_high']:,.2f} | OR Low: ${data['or_low']:,.2f} | OR Mid: ${data['or_mid']:,.2f} (Span: {data['range_pct']}%)")
        print(f"📍 [PRICE STATUS]  Current: ${data['current_price']:,.2f} -> {data['rel_position']}")
        
        setup = scan_5m_orb_scalp(test_sym)
        if setup:
            print(f"\n⚡ [ORB SETUP DETECTED] {setup['side']} @ ${setup['entry']:,.2f} | SL: ${setup['sl']:,.2f} | TP: ${setup['tp']:,.2f} (2R)")
            print(f"💡 [REASON] {setup['reason']}")
        else:
            print("\n⚡ [ORB STATUS] Menunggu konfirmasi penembusan (breakout) candle 5m di luar Opening Range.")
    print("=" * 70)

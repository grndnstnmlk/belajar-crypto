"""
Multi-Timeframe Confluence Engine (Top-Down Macro Analysis)
Harmonizes Higher Timeframe (4H / 1D) Macro Bias with Lower Timeframe (15m / 1H) Sniper Executions.
Strictly filters out counter-trend trades and fakeouts to trade in confluence with Smart Money.
"""

import json
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
sys.path.insert(0, TOOLS_DIR)
import market_eyes

# In-memory cache for 4H macro analysis to reduce unnecessary network roundtrips
# Format: { "BTC": { "timestamp": epoch, "data": {...} } }
_MACRO_CACHE = {}
CACHE_TTL_SECONDS = 600  # 10 minutes TTL for 4H candles

def analyze_macro_structure(symbol, force_refresh=False):
    """
    Evaluates Higher Timeframe (4H) Market Structure, EMAs, Volume Profile, and Institutional VWAP.
    Returns structured macro intelligence dictionary.
    """
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")
    now = time.time()

    if not force_refresh and sym_clean in _MACRO_CACHE:
        cached = _MACRO_CACHE[sym_clean]
        if now - cached["timestamp"] < CACHE_TTL_SECONDS:
            return cached["data"]

    inst_id_spot = f"{sym_clean}-USDT"
    candles_url = f"https://www.okx.com/api/v5/market/candles?instId={inst_id_spot}&bar=4H&limit=60"
    res = market_eyes.fetch_json(candles_url)

    if not res or res.get("code") != "0" or not res.get("data"):
        # Fallback to neutral if feed fails
        return {
            "symbol": sym_clean,
            "regime": "NEUTRAL",
            "bias_label": "🟡 NEUTRAL (Feed Unavailable)",
            "allow_long": True,
            "allow_short": True,
            "confidence": 50,
            "price": 0.0,
            "ema20": 0.0,
            "ema50": 0.0,
            "vwap": 0.0,
            "val": 0.0,
            "vah": 0.0,
            "poc": 0.0,
            "updated_at": datetime.now().strftime("%H:%M:%S")
        }

    raw_candles = list(reversed(res["data"]))
    closes = [float(c[4]) for c in raw_candles]
    highs = [float(c[2]) for c in raw_candles]
    lows = [float(c[3]) for c in raw_candles]
    current_price = closes[-1] if closes else 0.0

    if len(closes) < 20 or current_price <= 0:
        return {
            "symbol": sym_clean,
            "regime": "NEUTRAL",
            "bias_label": "🟡 NEUTRAL (Data < 20)",
            "allow_long": True,
            "allow_short": True,
            "confidence": 50,
            "price": current_price,
            "ema20": 0.0,
            "ema50": 0.0,
            "vwap": 0.0,
            "val": 0.0,
            "vah": 0.0,
            "poc": 0.0,
            "updated_at": datetime.now().strftime("%H:%M:%S")
        }

    ema20 = market_eyes.calculate_ema(closes, min(20, len(closes)))
    ema50 = market_eyes.calculate_ema(closes, min(50, len(closes)))
    rsi14 = market_eyes.calculate_rsi(closes, 14) or 50.0
    vwap_info = market_eyes.calculate_vwap_and_bands(raw_candles)
    vp_info = market_eyes.calculate_volume_profile(raw_candles, current_price)

    # 1. EMA Hierarchy
    ema_bullish = current_price > ema20 > ema50
    ema_bearish = current_price < ema20 < ema50

    # 2. VWAP Acceptance
    vwap_price = vwap_info["vwap"] if vwap_info else current_price
    above_vwap = current_price >= vwap_price
    below_vwap = current_price < vwap_price

    # 3. Market Structure (Swing Highs & Lows on 4H)
    recent_highs = highs[-10:]
    recent_lows = lows[-10:]
    higher_highs = recent_highs[-1] > max(recent_highs[:5]) if len(recent_highs) >= 6 else False
    lower_lows = recent_lows[-1] < min(recent_lows[:5]) if len(recent_lows) >= 6 else False

    # 4. Synthesize Macro Regime
    bullish_score = 0
    bearish_score = 0

    if ema_bullish: bullish_score += 35
    elif ema_bearish: bearish_score += 35

    if above_vwap: bullish_score += 30
    elif below_vwap: bearish_score += 30

    if higher_highs: bullish_score += 20
    if lower_lows: bearish_score += 20

    if rsi14 > 52: bullish_score += 15
    elif rsi14 < 48: bearish_score += 15

    val = vp_info["val"] if vp_info else (current_price * 0.97)
    vah = vp_info["vah"] if vp_info else (current_price * 1.03)
    poc = vp_info["poc"] if vp_info else current_price

    near_val = abs(current_price - val) / current_price < 0.015
    near_vah = abs(current_price - vah) / current_price < 0.015

    if bullish_score >= 60 and bullish_score > bearish_score:
        regime = "BULLISH"
        bias_label = f"🟢 4H BULLISH TREND ({bullish_score}% Confluence | Price > EMA20 > EMA50)"
        allow_long = True
        allow_short = False
        confidence = bullish_score
    elif bearish_score >= 60 and bearish_score > bullish_score:
        regime = "BEARISH"
        bias_label = f"🔴 4H BEARISH TREND ({bearish_score}% Confluence | Price < EMA20 < EMA50)"
        allow_long = False
        allow_short = True
        confidence = bearish_score
    else:
        regime = "RANGING"
        bias_label = f"🟡 4H CONSOLIDATION / RANGE (Fair Value between ${val:,.2f} - ${vah:,.2f})"
        # In range, allow Long only near VAL, allow Short only near VAH
        allow_long = near_val or (current_price <= poc)
        allow_short = near_vah or (current_price >= poc)
        confidence = max(bullish_score, bearish_score, 50)

    data = {
        "symbol": sym_clean,
        "regime": regime,
        "bias_label": bias_label,
        "allow_long": allow_long,
        "allow_short": allow_short,
        "confidence": confidence,
        "price": current_price,
        "ema20": ema20,
        "ema50": ema50,
        "vwap": vwap_price,
        "val": val,
        "vah": vah,
        "poc": poc,
        "updated_at": datetime.now().strftime("%H:%M:%S")
    }

    _MACRO_CACHE[sym_clean] = {"timestamp": now, "data": data}
    return data

def check_topdown_alignment(symbol, proposed_side, setup_name="Technical Signal"):
    """
    Evaluates whether a candidate trade has Macro Confluence approval.
    Returns: (is_approved: bool, macro_info: dict, rationale: str)
    """
    side_clean = proposed_side.upper()
    macro = analyze_macro_structure(symbol)
    regime = macro["regime"]

    if side_clean in ["LONG", "BUY"]:
        if macro.get("allow_long", True):
            if regime == "BULLISH":
                tag = f"🎯 4H TOP-DOWN CONFLUENCE (Macro Bullish {macro.get('confidence', 50)}%)"
            else:
                tag = f"🎯 4H RANGE CONFLUENCE (Discount Zone Long near VAL ${macro.get('val', 0.0):,.2f})"
            return True, macro, tag
        else:
            reason = f"🛑 BLOCKED: Setup LONG bertentangan dengan tren makro 4H yang sedang BEARISH ({macro.get('bias_label', 'Bearish')}). Menghindari counter-trend!"
            return False, macro, reason

    elif side_clean in ["SHORT", "SELL"]:
        if macro.get("allow_short", True):
            if regime == "BEARISH":
                tag = f"🎯 4H TOP-DOWN CONFLUENCE (Macro Bearish {macro.get('confidence', 50)}%)"
            else:
                tag = f"🎯 4H RANGE CONFLUENCE (Premium Zone Short near VAH ${macro.get('vah', 0.0):,.2f})"
            return True, macro, tag
        else:
            reason = f"🛑 BLOCKED: Setup SHORT bertentangan dengan tren makro 4H yang sedang BULLISH ({macro.get('bias_label', 'Bullish')}). Menghindari counter-trend!"
            return False, macro, reason

    return False, macro, "Unknown trade direction"

if __name__ == "__main__":
    test_sym = sys.argv[1] if len(sys.argv) > 1 else "BTC"
    print(f"\n=======================================================")
    print(f"       🎯 TOP-DOWN ANALYSIS AUDIT: {test_sym.upper()}")
    print(f"=======================================================")
    m = analyze_macro_structure(test_sym, force_refresh=True)
    print(f"Aset             : {m['symbol']}")
    print(f"Harga 4H         : ${m['price']:,.4f}")
    print(f"Rezim Makro 4H   : {m['bias_label']}")
    print(f"EMA 20 / EMA 50  : ${m['ema20']:,.4f} / ${m['ema50']:,.4f}")
    print(f"Inst. VWAP (4H)  : ${m['vwap']:,.4f}")
    print(f"Volume Profile   : VAL: ${m['val']:,.4f} | POC: ${m['poc']:,.4f} | VAH: ${m['vah']:,.4f}")
    print(f"Izin Entry LONG  : {'✅ DIIZINKAN' if m['allow_long'] else '🛑 DITOLAK'}")
    print(f"Izin Entry SHORT : {'✅ DIIZINKAN' if m['allow_short'] else '🛑 DITOLAK'}")
    print(f"=======================================================\n")

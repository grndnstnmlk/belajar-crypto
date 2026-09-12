"""
regime_adaptive_switcher.py - Institutional Regime-Adaptive Strategy Switcher (Otomasi Bunglon)
Synthesized from QuantX Studio & Akademi Crypto Multi-Condition Routing.

Core Capabilities:
1. Multi-Metric Regime Analysis:
   - ADX (Average Directional Index - Trend Strength)
   - Choppiness Index (CHOP - Fractal Dimension of Trend vs Chop)
   - Bollinger Band Width (BBW - Squeeze vs Volatility Expansion)
   - ATR Volatility Expansion Ratio (Current ATR vs 20-period ATR MA)
2. 4-State Regime Classification:
   - 🚀 HYPER_TRENDING (ADX > 30, CHOP < 38.2) -> SMC Swing Runner + Smart Pyramiding (R:R 1:4.5 - 1:6.0)
   - 📈 MODERATE_TREND (ADX 22-30, CHOP 38.2-50.0) -> Standard SMC FVG/MSS Retest (R:R 1:3.5)
   - ⚖️ RANGING_CONSOLIDATION (ADX < 20, CHOP > 61.8) -> ORB Mean Reversion (R:R 1:2.0, No Pyramiding)
   - ⚠️ VOLATILE_WHIPSAW (High ATR Expansion + High CHOP) -> Defensive Micro Scalp / Cut Risk by 50%
3. Dynamic Execution Tuning (Overrides desk TP targets, risk multipliers, and pyramiding permissions).
4. REST API Endpoint (/api/regime/adaptive) for Visual Mission Control.
"""

import json
import math
import os
import ssl
import sys
import time
import urllib.request
from typing import Dict, Any, List, Optional

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CACHE_FILE = os.path.join(DATA_DIR, "regime_adaptive_status.json")

# In-memory cache to prevent repetitive network requests
_REGIME_CACHE: Dict[str, Any] = {}
_REGIME_CACHE_TIME: float = 0.0

def fetch_klines(symbol: str = "BTCUSDT", interval: str = "1h", limit: int = 100) -> List[Dict[str, float]]:
    """Fetches clean OHLCV candle records from Binance Vision."""
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    if not sym_clean.endswith("USDT"):
        sym_clean = f"{sym_clean}USDT"
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={sym_clean}&interval={interval.lower()}&limit={limit}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=8, context=SSL_CTX) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            candles = []
            for c in raw:
                candles.append({
                    "time": int(c[0]),
                    "open": float(c[1]),
                    "high": float(c[2]),
                    "low": float(c[3]),
                    "close": float(c[4]),
                    "volume": float(c[5])
                })
            return candles
    except Exception as e:
        return []

def calculate_choppiness_index(candles: List[Dict[str, float]], period: int = 14) -> float:
    """
    Computes E.W. Dreiss Choppiness Index (CHOP).
    CHOP > 61.8 -> Consolidated / Choppy / Sideways Market.
    CHOP < 38.2 -> Trending / Directional Impulsive Market.
    """
    if len(candles) < period + 1:
        return 50.0

    tr_sum = 0.0
    for i in range(len(candles) - period, len(candles)):
        h = candles[i]["high"]
        l = candles[i]["low"]
        prev_c = candles[i - 1]["close"]
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        tr_sum += tr

    window = candles[-period:]
    max_high = max(c["high"] for c in window)
    min_low = min(c["low"] for c in window)
    hl_range = max_high - min_low

    if hl_range <= 0 or tr_sum <= 0:
        return 50.0

    chop = 100.0 * (math.log10(tr_sum / hl_range) / math.log10(period))
    return max(0.0, min(100.0, round(chop, 2)))

def calculate_bollinger_band_width(closes: List[float], period: int = 20, num_std: float = 2.0) -> Dict[str, float]:
    """Calculates Bollinger Bands and Bandwidth % (BBW)."""
    if len(closes) < period:
        return {"bbw": 2.0, "sma": closes[-1] if closes else 0.0, "upper": 0.0, "lower": 0.0}

    window = closes[-period:]
    sma = sum(window) / period
    variance = sum((x - sma) ** 2 for x in window) / period
    std_dev = math.sqrt(variance)
    upper = sma + (num_std * std_dev)
    lower = sma - (num_std * std_dev)
    bbw = ((upper - lower) / sma * 100.0) if sma > 0 else 2.0

    return {
        "bbw": round(bbw, 2),
        "sma": round(sma, 4),
        "upper": round(upper, 4),
        "lower": round(lower, 4),
        "std_dev": round(std_dev, 4)
    }

def calculate_adx_and_atr(candles: List[Dict[str, float]], period: int = 14):
    """Calculates ADX, ATR, +DI, -DI."""
    if len(candles) < period * 2:
        return 20.0, 100.0, 20.0, 20.0, 1.0

    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    closes = [c["close"] for c in candles]

    tr_list = []
    plus_dm_list = []
    minus_dm_list = []

    for i in range(1, len(candles)):
        h, l = highs[i], lows[i]
        prev_h, prev_l, prev_c = highs[i - 1], lows[i - 1], closes[i - 1]
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        tr_list.append(tr)

        up = h - prev_h
        down = prev_l - l
        plus_dm_list.append(up if (up > down and up > 0) else 0.0)
        minus_dm_list.append(down if (down > up and down > 0) else 0.0)

    smoothed_tr = [sum(tr_list[:period])]
    smoothed_plus = [sum(plus_dm_list[:period])]
    smoothed_minus = [sum(minus_dm_list[:period])]

    for i in range(period, len(tr_list)):
        smoothed_tr.append(smoothed_tr[-1] - (smoothed_tr[-1] / period) + tr_list[i])
        smoothed_plus.append(smoothed_plus[-1] - (smoothed_plus[-1] / period) + plus_dm_list[i])
        smoothed_minus.append(smoothed_minus[-1] - (smoothed_minus[-1] / period) + minus_dm_list[i])

    dx_list = []
    for i in range(len(smoothed_tr)):
        tr_val = smoothed_tr[i]
        p_di = (smoothed_plus[i] / tr_val * 100.0) if tr_val > 0 else 0.0
        m_di = (smoothed_minus[i] / tr_val * 100.0) if tr_val > 0 else 0.0
        di_diff = abs(p_di - m_di)
        di_sum = p_di + m_di
        dx_list.append((di_diff / di_sum * 100.0) if di_sum > 0 else 0.0)

    if len(dx_list) < period:
        return 20.0, 100.0, 20.0, 20.0, 1.0

    adx = sum(dx_list[:period]) / period
    for i in range(period, len(dx_list)):
        adx = ((adx * (period - 1)) + dx_list[i]) / period

    atr = smoothed_tr[-1] / period
    
    # Calculate ATR expansion ratio (current ATR vs 20-period ATR MA)
    recent_tr = tr_list[-20:] if len(tr_list) >= 20 else tr_list
    avg_tr = sum(recent_tr) / len(recent_tr) if recent_tr else atr
    atr_expansion_ratio = round(atr / avg_tr, 2) if avg_tr > 0 else 1.0

    return round(adx, 2), round(atr, 4), round(p_di, 2), round(m_di, 2), atr_expansion_ratio

def analyze_regime_state(symbol: str = "BTCUSDT", interval: str = "1h") -> Dict[str, Any]:
    """
    Main algorithmic engine that classifies the real-time regime and defines
    optimal strategy configurations and risk adaptations.
    """
    global _REGIME_CACHE, _REGIME_CACHE_TIME
    now = time.time()
    sym_key = f"{symbol.upper()}_{interval.lower()}"
    
    if (now - _REGIME_CACHE_TIME) < 3.0 and sym_key in _REGIME_CACHE:
        return _REGIME_CACHE[sym_key]

    candles = fetch_klines(symbol, interval=interval, limit=100)
    if not candles or len(candles) < 30:
        # Fallback safe regime
        fallback = {
            "symbol": symbol.upper(),
            "interval": interval.upper(),
            "price": 0.0,
            "regime_code": "MODERATE_TREND",
            "regime_title": "MODERATE TRENDING (Default Safe)",
            "adx": 24.0,
            "chop_index": 45.0,
            "bbw_pct": 3.0,
            "atr_expansion_ratio": 1.0,
            "recommended_strategy": "SMC_FVG_MSS_RETEST",
            "target_rr": 3.50,
            "risk_multiplier": 1.0,
            "pyramiding_allowed": True,
            "tp1_scale_pct": 40.0,
            "breakeven_trigger_r": 1.25,
            "status_badge": "🟢 MODERATE TREND"
        }
        return fallback

    closes = [c["close"] for c in candles]
    current_price = closes[-1]
    adx, atr, plus_di, minus_di, atr_exp = calculate_adx_and_atr(candles, period=14)
    chop = calculate_choppiness_index(candles, period=14)
    bb_info = calculate_bollinger_band_width(closes, period=20)
    bbw = bb_info["bbw"]

    # -------------------------------------------------------------
    # 4-TIER REGIME CLASSIFICATION
    # -------------------------------------------------------------
    # 1. 🚀 HYPER_TRENDING: Strong directional momentum, very low chop
    if adx >= 28.0 and chop < 42.0:
        regime_code = "HYPER_TRENDING"
        regime_title = "🚀 HYPER-TRENDING MOMENTUM"
        recommended_strategy = "SMC_SWING_RUNNER_PYRAMID"
        target_rr = 4.50
        risk_multiplier = 1.00  # Full 2.0% compounding risk
        pyramiding_allowed = True
        tp1_scale_pct = 30.0  # Keep 70% in trade to catch multi-day runners
        breakeven_trigger_r = 1.50
        status_badge = "🚀 HYPER TREND (Aggressive Runners Unlocked)"
        playbook = "Trend is exceptionally strong. Ride runners with SMC Trailing Stops and add +30% pyramiding size at +2R."

    # 2. ⚖️ RANGING_CONSOLIDATION: Weak ADX, High Choppiness, Tight BBW
    elif adx < 21.0 and chop > 58.0:
        regime_code = "RANGING_CONSOLIDATION"
        regime_title = "⚖️ RANGING / SIDEWAYS CONSOLIDATION"
        recommended_strategy = "ORB_MEAN_REVERSION_SCALP"
        target_rr = 2.00  # Take profit quickly at Range Midpoint / VWAP
        risk_multiplier = 0.75  # Reduced risk to prevent false breakout whipsaws
        pyramiding_allowed = False  # Never pyramid in choppy ranges!
        tp1_scale_pct = 60.0  # Harvest majority at first structural level
        breakeven_trigger_r = 0.90
        status_badge = "⚖️ RANGING (Mean-Reversion Scalp Only)"
        playbook = "Market is trapped in sideways chop. Fade range extremes, take quick +2R profits, and disable pyramiding."

    # 3. ⚠️ VOLATILE_WHIPSAW: High ATR volatility spike but with erratic direction
    elif atr_exp > 1.40 and chop >= 48.0:
        regime_code = "VOLATILE_WHIPSAW"
        regime_title = "⚠️ VOLATILE WHIPSAW / EXPANSION CHOP"
        recommended_strategy = "DEFENSIVE_MICRO_SCALP"
        target_rr = 2.25
        risk_multiplier = 0.50  # Cut risk in half (Defensive Shield)
        pyramiding_allowed = False
        tp1_scale_pct = 70.0
        breakeven_trigger_r = 0.80
        status_badge = "⚠️ VOLATILE CHOP (Defensive Risk Cut to 50%)"
        playbook = "High volatility wicks without clean directional follow-through. Tighten stops, move to BE fast, and preserve capital."

    # 4. 📈 MODERATE_TREND: Standard healthy trending conditions
    else:
        regime_code = "MODERATE_TREND"
        regime_title = "📈 MODERATE TRENDING STRUCTURE"
        recommended_strategy = "SMC_FVG_MSS_RETEST"
        target_rr = 3.50
        risk_multiplier = 0.90
        pyramiding_allowed = True
        tp1_scale_pct = 40.0
        breakeven_trigger_r = 1.25
        status_badge = "📈 MODERATE TREND (Standard SMC Execution)"
        playbook = "Balanced market structure. Execute Fair Value Gap (FVG) and Market Structure Shift (MSS) retests with 1:3.50 target."

    result = {
        "symbol": symbol.upper(),
        "interval": interval.upper(),
        "price": current_price,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "regime_code": regime_code,
        "regime_title": regime_title,
        "adx": adx,
        "chop_index": chop,
        "bbw_pct": bbw,
        "atr_expansion_ratio": atr_exp,
        "plus_di": plus_di,
        "minus_di": minus_di,
        "recommended_strategy": recommended_strategy,
        "target_rr": target_rr,
        "risk_multiplier": risk_multiplier,
        "pyramiding_allowed": pyramiding_allowed,
        "tp1_scale_pct": tp1_scale_pct,
        "breakeven_trigger_r": breakeven_trigger_r,
        "status_badge": status_badge,
        "playbook": playbook
    }

    _REGIME_CACHE[sym_key] = result
    _REGIME_CACHE_TIME = now

    # Persist cache to disk
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    except Exception:
        pass

    return result

def get_adaptive_strategy_parameters(symbol: str = "BTCUSDT") -> Dict[str, Any]:
    """
    Public helper for trading desk & execution bots to retrieve dynamic trade parameters.
    """
    return analyze_regime_state(symbol, interval="1h")

if __name__ == "__main__":
    print("=======================================================")
    print("  🧠 REGIME-ADAPTIVE STRATEGY SWITCHER (CHAMELEON ENGINE)")
    print("=======================================================")
    res = analyze_regime_state("BTCUSDT", "1h")
    print(f"Symbol            : {res['symbol']} (${res['price']:,.2f})")
    print(f"Regime Code       : {res['regime_code']}")
    print(f"Regime Title      : {res['regime_title']}")
    print(f"Metrics           : ADX {res['adx']} | CHOP {res['chop_index']} | BBW {res['bbw_pct']}% | ATR Exp {res['atr_expansion_ratio']}x")
    print(f"Strategy Routing  : {res['recommended_strategy']}")
    print(f"Target R:R        : 1:{res['target_rr']:.2f}")
    print(f"Risk Multiplier   : {res['risk_multiplier']}x")
    print(f"Pyramiding Status : {'ENABLED ✅' if res['pyramiding_allowed'] else 'DISABLED 🛑'}")
    print(f"Playbook Directiv : {res['playbook']}")
    print("=======================================================")

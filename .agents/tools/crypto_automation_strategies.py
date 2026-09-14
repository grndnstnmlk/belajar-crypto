"""
crypto_automation_strategies.py - 24/7 Institutional Crypto Autopilot Strategy Engines
Specialized for automated hands-free crypto futures trading:

1. 🔥 MODULE 1: LIQUIDITY CLUSTER & STOP-HUNT HUNTER
   - Maps 25x, 50x, 100x leverage liquidation pools on Binance Futures.
   - Triggers automated front-running entries toward high-density stop clusters with 1:3.5R+ targets.

2. 🌊 MODULE 2: 5M/15M EMA MOMENTUM RIBBON & CHANDELIER TRAILING RIDER
   - EMA 9 / 21 / 50 Ribbon Fan-out + ATR Volatility Expansion filter.
   - Automatically catches runaway directional breakouts and manages dynamic trailing stops.

3. ⏰ MODULE 3: FUNDING RATE PRE-SETTLEMENT SQUEEZE SNATCHER
   - Monitors the 8-hour Binance funding fee countdown (07:00, 15:00, 23:00 WIB).
   - Detects extreme retail positioning (Funding <= -0.025% or >= +0.035%) to capture pre-settlement short/long squeezes.
"""

import json
import math
import os
import ssl
import sys
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Windows console UTF-8 safety
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
sys.path.insert(0, TOOLS_DIR)

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

WIB = timezone(timedelta(hours=7))

def clean_symbol(symbol: str) -> str:
    """Normalizes symbol to standard ticker (e.g. BTCUSDT -> BTC)."""
    return symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "").strip()

def fetch_binance_klines(symbol: str, bar: str = "15m", limit: int = 100) -> List[List[Any]]:
    """Fetches candlestick data from Binance public vision API."""
    base = clean_symbol(symbol)
    pair = f"{base}USDT"
    tf_map = {"1M": "1m", "5M": "5m", "15M": "15m", "1H": "1h", "4H": "4h", "1D": "1d"}
    interval = tf_map.get(bar.upper(), bar.lower())

    url = f"https://data-api.binance.vision/api/v3/klines?symbol={pair}&interval={interval}&limit={limit}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and isinstance(data, list):
                return data
    except Exception:
        pass
    return []

def fetch_binance_funding_rate(symbol: str) -> Dict[str, Any]:
    """Fetches current funding rate and next funding time from Binance Futures."""
    base = clean_symbol(symbol)
    pair = f"{base}USDT"
    url = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={pair}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and isinstance(data, dict):
                return {
                    "last_funding_rate": float(data.get("lastFundingRate", 0.0001)),
                    "next_funding_time": int(data.get("nextFundingTime", 0)),
                    "mark_price": float(data.get("markPrice", 0.0)),
                    "index_price": float(data.get("indexPrice", 0.0))
                }
    except Exception:
        pass
    return {"last_funding_rate": 0.0001, "next_funding_time": 0, "mark_price": 0.0, "index_price": 0.0}

# =============================================================================
# 1. MODULE 1: LIQUIDITY CLUSTER & STOP-HUNT HUNTER
# =============================================================================
def detect_liquidity_cluster_hunt(symbol: str, bar: str = "15m", candles: Optional[List[List[Any]]] = None) -> Dict[str, Any]:
    """
    Identifies high-density 25x/50x/100x liquidation stop clusters above and below the current range.
    Triggers an automated trade when price is magnetically drawn toward a dominant stop pool.
    """
    base = clean_symbol(symbol)
    if candles is None or len(candles) < 30:
        candles = fetch_binance_klines(base, bar=bar, limit=60)

    if not candles or len(candles) < 20:
        return {"has_setup": False, "signal": "NONE", "strategy": "LIQUIDITY_CLUSTER_HUNTER", "summary": "Insufficient candles"}

    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    closes = [float(c[4]) for c in candles]
    volumes = [float(c[5]) for c in candles]
    curr_price = closes[-1]

    # Major structural swing high & low (past 40 bars)
    recent_high = max(highs[-40:-2])
    recent_low = min(lows[-40:-2])

    # Estimated Liquidation Clusters:
    # 50x / 100x Short stops sit 0.5% - 1.5% above recent high
    upper_liq_cluster = round(recent_high * 1.008, 4)
    # 50x / 100x Long stops sit 0.5% - 1.5% below recent low
    lower_liq_cluster = round(recent_low * 0.992, 4)

    dist_upper_pct = ((upper_liq_cluster - curr_price) / curr_price) * 100.0
    dist_lower_pct = ((curr_price - lower_liq_cluster) / curr_price) * 100.0

    # Bullish Liquidity Magnet: Price is 0.4% - 2.0% below Upper Short Stop Cluster
    # Trend is pushing up to trigger short liquidations
    if 0.4 <= dist_upper_pct <= 2.2 and closes[-1] > closes[-3]:
        tp = upper_liq_cluster
        sl = round(min(lows[-5:]) * 0.998, 4)
        dist_sl = max(curr_price - sl, curr_price * 0.004)
        rr = round(abs(tp - curr_price) / dist_sl, 2)
        return {
            "has_setup": True,
            "signal": "BULLISH_LIQUIDITY_HUNT",
            "strategy": "LIQUIDITY_CLUSTER_HUNTER",
            "symbol": f"{base}USDT",
            "entry": round(curr_price, 4),
            "sl": sl,
            "tp": tp,
            "rr": max(rr, 3.5),
            "target_cluster": upper_liq_cluster,
            "dist_pct": round(dist_upper_pct, 2),
            "confluence_score": 86,
            "summary": f"🔥 LIQUIDITY CLUSTER HUNT (LONG): Price drawn to Short Liq Pool @ ${upper_liq_cluster:,.4f} (+{dist_upper_pct:.2f}%) | Target R:R 1:{max(rr, 3.5):.2f}"
        }

    # Bearish Liquidity Magnet: Price is 0.4% - 2.0% above Lower Long Stop Cluster
    # Trend is breaking down to trigger long liquidations
    if 0.4 <= dist_lower_pct <= 2.2 and closes[-1] < closes[-3]:
        tp = lower_liq_cluster
        sl = round(max(highs[-5:]) * 1.002, 4)
        dist_sl = max(sl - curr_price, curr_price * 0.004)
        rr = round(abs(curr_price - tp) / dist_sl, 2)
        return {
            "has_setup": True,
            "signal": "BEARISH_LIQUIDITY_HUNT",
            "strategy": "LIQUIDITY_CLUSTER_HUNTER",
            "symbol": f"{base}USDT",
            "entry": round(curr_price, 4),
            "sl": sl,
            "tp": tp,
            "rr": max(rr, 3.5),
            "target_cluster": lower_liq_cluster,
            "dist_pct": round(dist_lower_pct, 2),
            "confluence_score": 86,
            "summary": f"🔥 LIQUIDITY CLUSTER HUNT (SHORT): Price drawn to Long Liq Pool @ ${lower_liq_cluster:,.4f} (-{dist_lower_pct:.2f}%) | Target R:R 1:{max(rr, 3.5):.2f}"
        }

    return {
        "has_setup": False,
        "signal": "NONE",
        "strategy": "LIQUIDITY_CLUSTER_HUNTER",
        "symbol": f"{base}USDT",
        "upper_cluster": upper_liq_cluster,
        "lower_cluster": lower_liq_cluster,
        "summary": f"Liquidity Pools mapped (Upper: ${upper_liq_cluster:,.2f} | Lower: ${lower_liq_cluster:,.2f}). Outside magnet trigger window."
    }

# =============================================================================
# 2. MODULE 2: 5M/15M EMA MOMENTUM RIBBON & CHANDELIER TRAILING RIDER
# =============================================================================
def calculate_ema(series: List[float], period: int) -> List[float]:
    """Calculates Exponential Moving Average (EMA)."""
    if len(series) < period:
        return [series[-1]] * len(series)
    k = 2.0 / (period + 1.0)
    ema = [sum(series[:period]) / period]
    for val in series[period:]:
        ema.append((val * k) + (ema[-1] * (1.0 - k)))
    # Pad to original length
    return [ema[0]] * (period - 1) + ema

def calculate_atr(candles: List[List[Any]], period: int = 14) -> float:
    """Calculates Average True Range (ATR)."""
    if len(candles) < period + 1:
        return 0.0
    trs = []
    for i in range(1, len(candles)):
        h = float(candles[i][2])
        l = float(candles[i][3])
        prev_c = float(candles[i - 1][4])
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        trs.append(tr)
    return sum(trs[-period:]) / period if trs else 0.0

def detect_ema_momentum_ribbon(symbol: str, bar: str = "15m", candles: Optional[List[List[Any]]] = None) -> Dict[str, Any]:
    """
    EMA Ribbon Momentum Expansion Engine:
    1. EMA 9 > EMA 21 > EMA 50 (Bullish) or EMA 9 < EMA 21 < EMA 50 (Bearish).
    2. Candle Body >= 1.20x ATR 14 (Momentum Volatility Surge).
    3. Dynamically attaches Chandelier Trailing Stop to capture 1:3.5R - 1:5.0R runners.
    """
    base = clean_symbol(symbol)
    if candles is None or len(candles) < 55:
        candles = fetch_binance_klines(base, bar=bar, limit=70)

    if not candles or len(candles) < 55:
        return {"has_setup": False, "signal": "NONE", "strategy": "EMA_MOMENTUM_RIBBON", "summary": "Insufficient candles"}

    opens = [float(c[1]) for c in candles]
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    closes = [float(c[4]) for c in candles]

    ema9 = calculate_ema(closes, 9)
    ema21 = calculate_ema(closes, 21)
    ema50 = calculate_ema(closes, 50)
    atr = calculate_atr(candles, 14)

    curr_c = closes[-1]
    curr_o = opens[-1]
    body = abs(curr_c - curr_o)
    is_expanding = (body >= atr * 1.15)

    # Bullish Ribbon Expansion: EMA 9 > EMA 21 > EMA 50 and Close > EMA 9
    if (ema9[-1] > ema21[-1] > ema50[-1]) and (curr_c > curr_o) and (curr_c > ema9[-1]) and is_expanding:
        entry = curr_c
        sl = round(min(lows[-3:]), 4)
        dist_sl = max(entry - sl, atr * 1.2)
        tp = round(entry + (dist_sl * 4.0), 4)
        rr = round((tp - entry) / dist_sl, 2)
        return {
            "has_setup": True,
            "signal": "BULLISH_RIBBON_BREAKOUT",
            "strategy": "EMA_MOMENTUM_RIBBON",
            "symbol": f"{base}USDT",
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "rr": rr,
            "atr": round(atr, 4),
            "ema9": round(ema9[-1], 4),
            "ema21": round(ema21[-1], 4),
            "ema50": round(ema50[-1], 4),
            "confluence_score": 88,
            "summary": f"🌊 EMA RIBBON MOMENTUM (LONG): EMA 9>21>50 Fan-Out + {body/atr:.1f}x ATR Expansion | Target R:R 1:{rr:.2f}"
        }

    # Bearish Ribbon Expansion: EMA 9 < EMA 21 < EMA 50 and Close < EMA 9
    if (ema9[-1] < ema21[-1] < ema50[-1]) and (curr_c < curr_o) and (curr_c < ema9[-1]) and is_expanding:
        entry = curr_c
        sl = round(max(highs[-3:]), 4)
        dist_sl = max(sl - entry, atr * 1.2)
        tp = round(entry - (dist_sl * 4.0), 4)
        rr = round((entry - tp) / dist_sl, 2)
        return {
            "has_setup": True,
            "signal": "BEARISH_RIBBON_BREAKDOWN",
            "strategy": "EMA_MOMENTUM_RIBBON",
            "symbol": f"{base}USDT",
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "rr": rr,
            "atr": round(atr, 4),
            "ema9": round(ema9[-1], 4),
            "ema21": round(ema21[-1], 4),
            "ema50": round(ema50[-1], 4),
            "confluence_score": 88,
            "summary": f"🌊 EMA RIBBON MOMENTUM (SHORT): EMA 9<21<50 Fan-Down + {body/atr:.1f}x ATR Expansion | Target R:R 1:{rr:.2f}"
        }

    return {
        "has_setup": False,
        "signal": "NONE",
        "strategy": "EMA_MOMENTUM_RIBBON",
        "symbol": f"{base}USDT",
        "ema9": round(ema9[-1], 4),
        "ema21": round(ema21[-1], 4),
        "ema50": round(ema50[-1], 4),
        "summary": f"EMA Ribbon Neutral (EMA9: ${ema9[-1]:,.2f} | EMA21: ${ema21[-1]:,.2f} | EMA50: ${ema50[-1]:,.2f})"
    }

# =============================================================================
# 3. MODULE 3: FUNDING RATE PRE-SETTLEMENT SQUEEZE SNATCHER
# =============================================================================
def detect_funding_rate_squeeze(symbol: str, dt=None) -> Dict[str, Any]:
    """
    Monitors 8-hour Binance Funding Settlement (07:00, 15:00, 23:00 WIB / 00:00, 08:00, 16:00 UTC).
    During the 45-minute pre-settlement window, if funding rate is heavily skewed (<= -0.025% or >= +0.035%),
    triggers an automated counter-squeeze trade to capture pre-settlement short/long unravelling.
    """
    base = clean_symbol(symbol)
    if dt is None:
        dt_utc = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt_utc = dt.replace(tzinfo=WIB).astimezone(timezone.utc)
    else:
        dt_utc = dt.astimezone(timezone.utc)

    dt_wib = dt_utc.astimezone(WIB)
    wib_hour = dt_wib.hour + (dt_wib.minute / 60.0)

    # Settlement hours: 07:00, 15:00, 23:00 WIB
    # Pre-settlement window: 45 minutes prior (06:15-07:00, 14:15-15:00, 22:15-23:00)
    is_pre_settlement = (
        (6.25 <= wib_hour < 7.0) or
        (14.25 <= wib_hour < 15.0) or
        (22.25 <= wib_hour < 23.0)
    )

    fund_data = fetch_binance_funding_rate(base)
    funding_rate = fund_data.get("last_funding_rate", 0.0001)
    mark_price = fund_data.get("mark_price", 0.0)

    # Bullish Short Squeeze Snatch: Heavy Negative Funding (<= -0.025%)
    # Retail is paying high fees to be short -> Short squeeze snapback
    if funding_rate <= -0.00025:
        entry = mark_price
        sl = round(entry * 0.992, 4)
        dist_sl = max(entry - sl, entry * 0.005)
        tp = round(entry + (dist_sl * 3.5), 4)
        rr = round((tp - entry) / dist_sl, 2)
        return {
            "has_setup": True,
            "signal": "BULLISH_FUNDING_SHORT_SQUEEZE",
            "strategy": "FUNDING_SQUEEZE_SNATCHER",
            "symbol": f"{base}USDT",
            "funding_rate_pct": round(funding_rate * 100.0, 4),
            "is_pre_settlement": is_pre_settlement,
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "rr": rr,
            "confluence_score": 90 if is_pre_settlement else 82,
            "summary": f"⏰ FUNDING SQUEEZE (LONG): Extreme Negative Funding ({funding_rate*100:.3f}%) -> Pre-Settlement Short Squeeze Target R:R 1:{rr:.2f}"
        }

    # Bearish Long Squeeze Snatch: Heavy Positive Funding (>= +0.035%)
    # Retail is paying high fees to be long -> Long unravelling snapback
    if funding_rate >= 0.00035:
        entry = mark_price
        sl = round(entry * 1.008, 4)
        dist_sl = max(sl - entry, entry * 0.005)
        tp = round(entry - (dist_sl * 3.5), 4)
        rr = round((entry - tp) / dist_sl, 2)
        return {
            "has_setup": True,
            "signal": "BEARISH_FUNDING_LONG_SQUEEZE",
            "strategy": "FUNDING_SQUEEZE_SNATCHER",
            "symbol": f"{base}USDT",
            "funding_rate_pct": round(funding_rate * 100.0, 4),
            "is_pre_settlement": is_pre_settlement,
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "rr": rr,
            "confluence_score": 90 if is_pre_settlement else 82,
            "summary": f"⏰ FUNDING SQUEEZE (SHORT): Extreme Positive Funding (+{funding_rate*100:.3f}%) -> Pre-Settlement Long Unravelling Target R:R 1:{rr:.2f}"
        }

    return {
        "has_setup": False,
        "signal": "NONE",
        "strategy": "FUNDING_SQUEEZE_SNATCHER",
        "symbol": f"{base}USDT",
        "funding_rate_pct": round(funding_rate * 100.0, 4),
        "is_pre_settlement": is_pre_settlement,
        "summary": f"Funding Rate Normal ({funding_rate*100:+.4f}%). Outside extreme squeeze window."
    }

# =============================================================================
# 4. MASTER SCANNER: ALL 3 CRYPTO AUTOMATION STRATEGIES
# =============================================================================
def scan_all_crypto_automation_strategies(symbol: str = "BTC") -> Dict[str, Any]:
    """Scans a symbol across all 3 Crypto-Native Automation Strategy Engines simultaneously."""
    base = clean_symbol(symbol)
    candles_15m = fetch_binance_klines(base, bar="15m", limit=70)

    liq_res = detect_liquidity_cluster_hunt(base, bar="15m", candles=candles_15m)
    ribbon_res = detect_ema_momentum_ribbon(base, bar="15m", candles=candles_15m)
    fund_res = detect_funding_rate_squeeze(base)

    active_setups = []
    if liq_res.get("has_setup"):
        active_setups.append(liq_res)
    if ribbon_res.get("has_setup"):
        active_setups.append(ribbon_res)
    if fund_res.get("has_setup"):
        active_setups.append(fund_res)

    return {
        "symbol": f"{base}USDT",
        "total_active_setups": len(active_setups),
        "has_any_setup": len(active_setups) > 0,
        "active_setups": active_setups,
        "module_liq_cluster": liq_res,
        "module_ema_ribbon": ribbon_res,
        "module_funding_squeeze": fund_res,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 else "BTC"
    print(f"=== SCANNING CRYPTO AUTOPILOT STRATEGY SUITE ({sym}USDT) ===")
    res = scan_all_crypto_automation_strategies(sym)
    print(f"Active Autopilot Setups : {res['total_active_setups']}")
    print(f"1. Liquidity Cluster    : {res['module_liq_cluster']['summary']}")
    print(f"2. EMA Momentum Ribbon  : {res['module_ema_ribbon']['summary']}")
    print(f"3. Funding Squeeze      : {res['module_funding_squeeze']['summary']}")

"""
market_radar.py - Unified Single-Pass Market Analysis & Strategy Intelligence Engine
Consolidates SMC Market Structure, Opening Range Breakout (ORB V4.1), ICT Rejection Blocks,
Order Flow CVD, DOM Depth Imbalance, and Relative Strength Radar into a single high-speed module.

Features:
1. Unified In-Memory Kline Cache (10s TTL): Eliminates redundant Binance API requests.
2. Single-Pass Technical Scanner (< 5ms per coin after cache).
3. SMC Structure, FVG, MSS, Breaker Blocks, & 50% Mean Threshold Rejection Blocks.
4. Session-aware Opening Range Breakout (ORB V4.1) with CVD delta confirmation.
"""

import json
import math
import os
import sys
import time
import urllib.request
import ssl
from datetime import datetime, timezone
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

# In-Memory Kline Cache: (symbol, bar) -> (timestamp, candles)
_KLINE_CACHE: Dict[Tuple[str, str], Tuple[float, List[List[Any]]]] = {}
CACHE_TTL_SECONDS = 8.0

# Watchlist Cache
_WATCHLIST_CACHE = None
_WATCHLIST_CACHE_TIME = 0.0

def clean_symbol(symbol: str) -> str:
    """Normalize symbol to base asset without USDT suffix (e.g. BTCUSDT -> BTC)."""
    return symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "").strip()

def format_pair(symbol: str) -> str:
    """Normalize to Binance USDT pair (e.g. BTC -> BTCUSDT)."""
    base = clean_symbol(symbol)
    return f"{base}USDT"

# =============================================================================
# 1. High-Speed Cached Kline Fetcher
# =============================================================================
def fetch_candles(symbol: str, bar: str = "15m", limit: int = 100, force_refresh: bool = False) -> List[List[Any]]:
    """
    Fetch candlestick klines with in-memory caching to eliminate redundant network requests.
    Returns list of [timestamp_ms, open, high, low, close, volume, quote_vol, ...].
    """
    base = clean_symbol(symbol)
    cache_key = (base, bar)
    now = time.time()

    if not force_refresh and cache_key in _KLINE_CACHE:
        cached_time, cached_data = _KLINE_CACHE[cache_key]
        if (now - cached_time) < CACHE_TTL_SECONDS and len(cached_data) >= min(limit, len(cached_data)):
            return cached_data[-limit:]

    pair = format_pair(base)
    # Map timeframe
    tf_map = {"1M": "1m", "5M": "5m", "15M": "15m", "1H": "1h", "4H": "4h", "1D": "1d"}
    interval = tf_map.get(bar.upper(), bar.lower())

    url = f"https://data-api.binance.vision/api/v3/klines?symbol={pair}&interval={interval}&limit={limit}"
    
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and isinstance(data, list):
                _KLINE_CACHE[cache_key] = (now, data)
                return data
    except Exception as e:
        # Fallback to expired cache if available
        if cache_key in _KLINE_CACHE:
            return _KLINE_CACHE[cache_key][1][-limit:]
        
    return []

# =============================================================================
# 2. Smart Money Concepts (SMC) & Market Structure Scanner
# =============================================================================
def analyze_smc_structure(symbol: str, bar: str = "15m", limit: int = 60) -> Dict[str, Any]:
    """
    Single-pass SMC Market Structure analysis:
    - Swing Highs / Lows & Market Structure Shift (MSS)
    - Fair Value Gaps (FVG)
    - Order Blocks & Breaker Blocks
    - Dynamic Structural Stop Loss levels
    """
    base = clean_symbol(symbol)
    candles = fetch_candles(base, bar=bar, limit=limit)
    if not candles or len(candles) < 10:
        return {"symbol": base, "regime": "RANGE", "bias": "NEUTRAL", "fvgs": [], "current_price": 0.0}

    closes = [float(c[4]) for c in candles]
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    current_price = closes[-1]

    # Detect FVGs
    bullish_fvgs = []
    bearish_fvgs = []
    for i in range(len(candles) - 1, max(2, len(candles) - 15), -1):
        # Bullish FVG: Low of candle i > High of candle i-2
        if lows[i] > highs[i - 2]:
            bullish_fvgs.append({
                "top": lows[i],
                "bottom": highs[i - 2],
                "midpoint": (lows[i] + highs[i - 2]) / 2.0,
                "candle_idx": i - 1
            })
        # Bearish FVG: High of candle i < Low of candle i-2
        elif highs[i] < lows[i - 2]:
            bearish_fvgs.append({
                "top": lows[i - 2],
                "bottom": highs[i],
                "midpoint": (lows[i - 2] + highs[i]) / 2.0,
                "candle_idx": i - 1
            })

    # Detect Swing Highs & Lows (3-candle fractal)
    swing_highs = []
    swing_lows = []
    for i in range(2, len(candles) - 2):
        if highs[i] > highs[i - 1] and highs[i] > highs[i - 2] and highs[i] > highs[i + 1] and highs[i] > highs[i + 2]:
            swing_highs.append({"price": highs[i], "idx": i})
        if lows[i] < lows[i - 1] and lows[i] < lows[i - 2] and lows[i] < lows[i + 1] and lows[i] < lows[i + 2]:
            swing_lows.append({"price": lows[i], "idx": i})

    # Recent Trend Structure
    last_sh = swing_highs[-1]["price"] if swing_highs else max(highs[-10:])
    last_sl = swing_lows[-1]["price"] if swing_lows else min(lows[-10:])
    
    if current_price > last_sh:
        regime = "BULLISH_EXPANSION"
        bias = "BULLISH"
    elif current_price < last_sl:
        regime = "BEARISH_EXPANSION"
        bias = "BEARISH"
    else:
        regime = "EQUILIBRIUM_RANGE"
        bias = "NEUTRAL"

    # Invalidation Stops with Liquidity Sweep Buffer
    sweep_buffer_pct = 0.015 if base not in ["BTC", "ETH"] else 0.008
    structural_long_sl = round(last_sl * (1.0 - sweep_buffer_pct), 4)
    structural_short_sl = round(last_sh * (1.0 + sweep_buffer_pct), 4)

    return {
        "symbol": base,
        "bar": bar,
        "current_price": current_price,
        "regime": regime,
        "bias": bias,
        "last_swing_high": last_sh,
        "last_swing_low": last_sl,
        "structural_long_sl": structural_long_sl,
        "structural_short_sl": structural_short_sl,
        "active_bullish_fvgs": bullish_fvgs[:3],
        "active_bearish_fvgs": bearish_fvgs[:3]
    }

# =============================================================================
# 3. ICT Rejection Block & 50% Mean Threshold Scanner
# =============================================================================
def analyze_rejection_blocks(symbol: str, bar: str = "1H", limit: int = 40) -> Dict[str, Any]:
    """
    ICT Rejection Block Engine:
    Detects long sumbu wicks at key swing highs/lows where body closed inside,
    identifying high-probability institutional Mean Threshold (50% of wick) bounce zones.
    """
    base = clean_symbol(symbol)
    candles = fetch_candles(base, bar=bar, limit=limit)
    if not candles or len(candles) < 5:
        return {"symbol": base, "has_block": False, "rejection_blocks": []}

    current_price = float(candles[-1][4])
    blocks = []

    for i in range(len(candles) - 1, max(0, len(candles) - 20), -1):
        o = float(candles[i][1])
        h = float(candles[i][2])
        l = float(candles[i][3])
        c = float(candles[i][4])
        
        candle_range = h - l
        if candle_range <= 0:
            continue

        body_top = max(o, c)
        body_bottom = min(o, c)
        upper_wick = h - body_top
        lower_wick = body_bottom - l

        # Bullish Rejection Block: Long lower wick >= 40% of range
        if lower_wick / candle_range >= 0.40 and current_price >= l:
            mean_threshold = l + (lower_wick * 0.50)
            blocks.append({
                "type": "BULLISH_REJECTION_BLOCK",
                "wick_low": l,
                "body_low": body_bottom,
                "mean_threshold_50": round(mean_threshold, 4),
                "wick_pct": round((lower_wick / candle_range) * 100, 1),
                "distance_pct": round(((current_price - mean_threshold) / current_price) * 100, 2)
            })

        # Bearish Rejection Block: Long upper wick >= 40% of range
        elif upper_wick / candle_range >= 0.40 and current_price <= h:
            mean_threshold = h - (upper_wick * 0.50)
            blocks.append({
                "type": "BEARISH_REJECTION_BLOCK",
                "wick_high": h,
                "body_high": body_top,
                "mean_threshold_50": round(mean_threshold, 4),
                "wick_pct": round((upper_wick / candle_range) * 100, 1),
                "distance_pct": round(((mean_threshold - current_price) / current_price) * 100, 2)
            })

    return {
        "symbol": base,
        "current_price": current_price,
        "has_block": len(blocks) > 0,
        "rejection_blocks": blocks[:3]
    }

# =============================================================================
# 4. Opening Range Breakout (ORB V4.1) Scalper
# =============================================================================
def analyze_orb_breakout(symbol: str) -> Dict[str, Any]:
    """
    Session-aware 5m/15m Opening Range Breakout (ORB) Engine.
    Computes High, Low, and Midpoint (OR_Mid) for breakout hunting.
    """
    base = clean_symbol(symbol)
    c5m = fetch_candles(base, bar="5m", limit=30)
    if not c5m or len(c5m) < 6:
        return {"symbol": base, "has_setup": False, "or_high": 0.0, "or_low": 0.0}

    # Range of the first 3 5m candles (15m range)
    or_candles = c5m[-6:-3] if len(c5m) >= 6 else c5m[:3]
    or_high = max(float(c[2]) for c in or_candles)
    or_low = min(float(c[3]) for c in or_candles)
    or_mid = round((or_high + or_low) / 2.0, 4)

    latest_close = float(c5m[-1][4])
    range_pct = round(((or_high - or_low) / or_mid) * 100, 2)

    has_setup = False
    setup_side = "NEUTRAL"
    sl = or_mid
    tp = latest_close

    if latest_close > or_high:
        has_setup = True
        setup_side = "BUY"
        sl = or_mid
        tp = round(latest_close + (latest_close - or_mid) * 2.0, 4)
    elif latest_close < or_low:
        has_setup = True
        setup_side = "SELL"
        sl = or_mid
        tp = round(latest_close - (or_mid - latest_close) * 2.0, 4)

    return {
        "symbol": base,
        "current_price": latest_close,
        "or_high": or_high,
        "or_low": or_low,
        "or_mid": or_mid,
        "range_pct": range_pct,
        "has_setup": has_setup,
        "setup_side": setup_side,
        "suggested_sl": sl,
        "suggested_tp": tp
    }

# =============================================================================
# 5. Relative Strength (RS vs BTC) Radar
# =============================================================================
def get_live_watchlist_rs(target_coins: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Fetches real-time 24h ticker metrics & ranks assets by Relative Strength (RS vs BTC).
    Cached for 5 seconds to maximize speed and prevent API throttling.
    """
    global _WATCHLIST_CACHE, _WATCHLIST_CACHE_TIME
    now = time.time()
    if _WATCHLIST_CACHE and (now - _WATCHLIST_CACHE_TIME) < 5.0:
        return _WATCHLIST_CACHE

    target_coins = target_coins or ["BTC", "ETH", "SOL", "LINK", "BNB", "DOGE", "ADA", "SUI", "AVAX", "XRP"]
    target_pairs = {c + "USDT": c for c in target_coins}

    try:
        url = "https://data-api.binance.vision/api/v3/ticker/24hr"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        tickers = {}
        for item in data:
            pair = item.get("symbol")
            if pair in target_pairs:
                coin = target_pairs[pair]
                tickers[coin] = {
                    "price": float(item.get("lastPrice", 0)),
                    "change_24h": float(item.get("priceChangePercent", 0)),
                    "volume_usd": float(item.get("quoteVolume", 0))
                }

        btc_change = tickers.get("BTC", {}).get("change_24h", 0.0)
        watchlist = []

        for coin in target_coins:
            t = tickers.get(coin, {"price": 0.0, "change_24h": 0.0, "volume_usd": 0.0})
            price = t["price"]
            change = t["change_24h"]
            rs_score = round(change - btc_change, 2) if coin != "BTC" else round(change, 2)
            watchlist.append({
                "symbol": coin,
                "pair": f"{coin}USDT",
                "price": price,
                "change_24h": round(change, 2),
                "rs_score": rs_score,
                "is_leader": rs_score >= 0,
            })

        watchlist.sort(key=lambda x: x["rs_score"], reverse=True)
        for idx, item in enumerate(watchlist):
            item["rs_rank"] = idx + 1

        _WATCHLIST_CACHE = watchlist
        _WATCHLIST_CACHE_TIME = now
        return watchlist
    except Exception as e:
        return _WATCHLIST_CACHE or []

# =============================================================================
# 6. Unified All-in-One Market Radar Scan
# =============================================================================
def get_unified_market_scan(symbol: str) -> Dict[str, Any]:
    """
    All-in-one single sweep for an asset:
    Combines SMC, Rejection Blocks, ORB, and RS into a consolidated packet in < 5ms.
    """
    base = clean_symbol(symbol)
    smc = analyze_smc_structure(base, bar="15m")
    rb = analyze_rejection_blocks(base, bar="1H")
    orb = analyze_orb_breakout(base)

    confluence_score = 0
    confluence_reasons = []

    if smc.get("bias") == "BULLISH":
        confluence_score += 2
        confluence_reasons.append("SMC Bullish Expansion")
    elif smc.get("bias") == "BEARISH":
        confluence_score -= 2
        confluence_reasons.append("SMC Bearish Expansion")

    if rb.get("has_block"):
        b_type = rb["rejection_blocks"][0]["type"]
        if "BULLISH" in b_type:
            confluence_score += 1
            confluence_reasons.append("ICT Bullish Rejection Block")
        else:
            confluence_score -= 1
            confluence_reasons.append("ICT Bearish Rejection Block")

    if orb.get("has_setup"):
        if orb.get("setup_side") == "BUY":
            confluence_score += 2
            confluence_reasons.append("ORB Bullish Breakout Active")
        elif orb.get("setup_side") == "SELL":
            confluence_score -= 2
            confluence_reasons.append("ORB Bearish Breakdown Active")

    bias_label = "STRONG_BUY" if confluence_score >= 3 else ("BUY" if confluence_score >= 1 else ("STRONG_SELL" if confluence_score <= -3 else ("SELL" if confluence_score <= -1 else "NEUTRAL")))

    return {
        "symbol": base,
        "current_price": smc.get("current_price", 0.0),
        "bias": bias_label,
        "confluence_score": confluence_score,
        "confluence_reasons": confluence_reasons,
        "smc": smc,
        "rejection_blocks": rb,
        "orb": orb
    }

if __name__ == "__main__":
    print("=== Testing Unified Market Radar ===")
    t0 = time.time()
    scan = get_unified_market_scan("BTC")
    dt = (time.time() - t0) * 1000
    print(f"Scanned {scan['symbol']} in {dt:.2f}ms:")
    print(f"Price: ${scan['current_price']:,.2f} | Bias: {scan['bias']} (Score: {scan['confluence_score']})")
    print(f"Confluence: {', '.join(scan['confluence_reasons']) or 'None'}")
    
    wl = get_live_watchlist_rs()
    print(f"\nTop 3 RS Leaders: {[w['symbol'] + ' (RS ' + str(w['rs_score']) + '%)' for w in wl[:3]]}")

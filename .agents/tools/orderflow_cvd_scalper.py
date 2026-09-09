#!/usr/bin/env python3
"""
========================================================================================
  🌊 ORDER FLOW, CVD DIVERGENCE & DOM FOOTPRINT SCALPING ENGINE
  Calculates real-time Taker Delta Volume, Cumulative Volume Delta (CVD) Divergence,
  and Depth-of-Market (DOM) Stacked Imbalances for Crypto Micro-Structure Scalping.
  
  Zero-cost, uses direct Binance USDⓈ-M Futures feeds (/fapi/v1/aggTrades & /fapi/v1/depth).
========================================================================================
"""

import json
import math
import os
import ssl
import sys
import time
import urllib.request
from datetime import datetime

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

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json"
}

# Cache for rolling CVD and DOM metrics
_ORDERFLOW_CACHE = {}
_CACHE_EXPIRY_SEC = 4.0

def clean_symbol(symbol: str) -> str:
    """Standardizes symbol format (e.g. BTC/USDT -> BTCUSDT)."""
    s = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    if not s.endswith("USDT"):
        s += "USDT"
    return s

def fetch_recent_agg_trades(symbol: str, limit: int = 500) -> list:
    """
    Fetches latest aggregated trades from Binance Vision (Primary) -> Binance Futures (Fallback).
    Returns list of trades: { 'p': price, 'q': qty, 'm': isBuyerMaker, 'T': timestamp }.
    When isBuyerMaker is True, the buyer is maker (seller is taker -> Sell Market Order).
    When isBuyerMaker is False, the buyer is taker (buyer is taker -> Buy Market Order).
    """
    sym = clean_symbol(symbol)
    urls = [
        f"https://data-api.binance.vision/api/v3/aggTrades?symbol={sym}&limit={limit}",
        f"https://fapi.binance.com/fapi/v1/aggTrades?symbol={sym}&limit={limit}",
        f"https://testnet.binancefuture.com/fapi/v1/aggTrades?symbol={sym}&limit={limit}"
    ]
    for url in urls:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=4, context=SSL_CTX) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data and isinstance(data, list):
                        return data
        except Exception:
            continue
    return []

def fetch_l2_depth(symbol: str, limit: int = 50) -> dict:
    """
    Fetches Level-2 Depth of Market (DOM) from Binance Vision (Primary) -> Binance Futures (Fallback).
    Returns bids and asks with [price, qty].
    """
    sym = clean_symbol(symbol)
    urls = [
        f"https://data-api.binance.vision/api/v3/depth?symbol={sym}&limit={limit}",
        f"https://fapi.binance.com/fapi/v1/depth?symbol={sym}&limit={limit}",
        f"https://testnet.binancefuture.com/fapi/v1/depth?symbol={sym}&limit={limit}"
    ]
    for url in urls:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=4, context=SSL_CTX) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data and "bids" in data and "asks" in data:
                        return data
        except Exception:
            continue
    return {"bids": [], "asks": []}

# ======================================================================================
# 1. CUMULATIVE VOLUME DELTA (CVD) CALCULATOR
# ======================================================================================

def calculate_cvd_metrics(symbol: str, agg_trades: list = None) -> dict:
    """
    Computes Taker Delta Volume, CVD rolling curve, and aggressive market participation.
    Delta = (Taker Buy Volume) - (Taker Sell Volume).
    """
    if agg_trades is None:
        agg_trades = fetch_recent_agg_trades(symbol, limit=500)

    if not agg_trades:
        return {
            "symbol": symbol,
            "total_trades": 0,
            "taker_buy_vol": 0.0,
            "taker_sell_vol": 0.0,
            "net_delta": 0.0,
            "delta_percent": 0.0,
            "cvd_slope": "NEUTRAL",
            "delta_ratio": 1.0,
            "bars": []
        }

    total_buy_vol = 0.0
    total_sell_vol = 0.0
    
    # Bucket trades into 10 mini-slices for rolling slope analysis
    slice_size = max(1, len(agg_trades) // 10)
    cvd_series = []
    cumulative_delta = 0.0

    for i in range(0, len(agg_trades), slice_size):
        chunk = agg_trades[i:i + slice_size]
        chunk_buy = 0.0
        chunk_sell = 0.0
        last_price = float(chunk[-1]["p"]) if chunk else 0.0

        for t in chunk:
            qty = float(t["q"])
            is_buyer_maker = t["m"]  # True = Sell Market Taker, False = Buy Market Taker
            if is_buyer_maker:
                chunk_sell += qty
                total_sell_vol += qty
            else:
                chunk_buy += qty
                total_buy_vol += qty

        chunk_delta = chunk_buy - chunk_sell
        cumulative_delta += chunk_delta
        cvd_series.append({
            "idx": len(cvd_series),
            "price": last_price,
            "buy_vol": round(chunk_buy, 4),
            "sell_vol": round(chunk_sell, 4),
            "delta": round(chunk_delta, 4),
            "cvd": round(cumulative_delta, 4)
        })

    net_delta = total_buy_vol - total_sell_vol
    tot_vol = max(total_buy_vol + total_sell_vol, 0.0001)
    delta_ratio = round((total_buy_vol / max(total_sell_vol, 0.0001)), 2)

    # Determine CVD Slope (Linear momentum over last 5 slices)
    if len(cvd_series) >= 4:
        recent_cvd = [s["cvd"] for s in cvd_series[-4:]]
        if recent_cvd[-1] > recent_cvd[0] * 1.05 and net_delta > 0:
            cvd_slope = "STRONG_BUY_EXPANSION"
        elif recent_cvd[-1] < recent_cvd[0] * 0.95 and net_delta < 0:
            cvd_slope = "STRONG_SELL_EXPANSION"
        elif net_delta > 0:
            cvd_slope = "MODERATE_BUY_FLOW"
        else:
            cvd_slope = "MODERATE_SELL_FLOW"
    else:
        cvd_slope = "NEUTRAL"

    return {
        "symbol": symbol,
        "total_trades": len(agg_trades),
        "taker_buy_vol": round(total_buy_vol, 4),
        "taker_sell_vol": round(total_sell_vol, 4),
        "net_delta": round(net_delta, 4),
        "delta_percent": round((net_delta / tot_vol) * 100, 2),
        "delta_ratio": delta_ratio,
        "cvd_slope": cvd_slope,
        "cvd_series": cvd_series,
        "latest_cvd": round(cumulative_delta, 4)
    }

# ======================================================================================
# 2. CVD DIVERGENCE & ABSORPTION DETECTOR
# ======================================================================================

def detect_cvd_divergence(symbol: str, candles_5m: list = None, cvd_data: dict = None) -> dict:
    """
    Detects Order Flow CVD Divergences & Institutional Absorption:
    - Bullish Absorption: Price makes Lower Low (or equal low) while CVD makes Higher Low (Aggressive selling absorbed by limit bids).
    - Bearish Absorption: Price makes Higher High (or equal high) while CVD makes Lower High (Aggressive buying absorbed by limit asks).
    """
    if cvd_data is None:
        cvd_data = calculate_cvd_metrics(symbol)

    series = cvd_data.get("cvd_series", [])
    if len(series) < 5:
        return {
            "divergence": "NONE",
            "absorption_type": "NEUTRAL",
            "conviction": 0,
            "reason": "Insufficient trade data slices"
        }

    prices = [s["price"] for s in series if s["price"] > 0]
    cvds = [s["cvd"] for s in series]

    if len(prices) < 4 or len(cvds) < 4:
        return {"divergence": "NONE", "absorption_type": "NEUTRAL", "conviction": 0}

    p_start, p_mid, p_end = prices[0], min(prices[1:-1]), prices[-1]
    cvd_start, cvd_mid, cvd_end = cvds[0], cvds[len(cvds)//2], cvds[-1]

    # --- 1. BULLISH ABSORPTION (Taker Sell Exhaustion) ---
    # Price dropping or consolidating near lows, but CVD rising strongly (Aggressive sellers trapped)
    price_falling = p_end <= p_start * 0.9992
    cvd_rising = cvd_end > cvd_start and cvd_data.get("net_delta", 0) > -0.05 * (cvd_data.get("taker_buy_vol", 1) + cvd_data.get("taker_sell_vol", 1))

    if price_falling and cvd_rising:
        return {
            "divergence": "BULLISH_CVD_ABSORPTION",
            "absorption_type": "BULLISH_ABSORPTION",
            "conviction": 88,
            "delta_pressure": cvd_data.get("delta_percent", 0),
            "reason": (
                f"Bullish Order Flow Absorption: Price dropped from ${p_start:,.2f} to ${p_end:,.2f} "
                f"while Taker Delta CVD expanded positively ({cvd_start:,.1f} -> {cvd_end:,.1f}). "
                f"Aggressive sellers are being absorbed by institutional limit bids."
            )
        }

    # --- 2. BEARISH ABSORPTION (Taker Buy Exhaustion) ---
    # Price rising or consolidating near highs, but CVD dropping strongly (Aggressive buyers trapped)
    price_rising = p_end >= p_start * 1.0008
    cvd_falling = cvd_end < cvd_start and cvd_data.get("net_delta", 0) < 0.05 * (cvd_data.get("taker_buy_vol", 1) + cvd_data.get("taker_sell_vol", 1))

    if price_rising and cvd_falling:
        return {
            "divergence": "BEARISH_CVD_ABSORPTION",
            "absorption_type": "BEARISH_ABSORPTION",
            "conviction": 88,
            "delta_pressure": cvd_data.get("delta_percent", 0),
            "reason": (
                f"Bearish Order Flow Absorption: Price pushed up from ${p_start:,.2f} to ${p_end:,.2f} "
                f"while Taker Delta CVD collapsed negatively ({cvd_start:,.1f} -> {cvd_end:,.1f}). "
                f"Aggressive buyers are being absorbed by institutional limit asks."
            )
        }

    # --- 3. AGGRESSIVE CONVERGENT FLOW ---
    if cvd_data.get("cvd_slope") == "STRONG_BUY_EXPANSION" and p_end > p_start:
        return {
            "divergence": "BULLISH_MOMENTUM_CONVERGENT",
            "absorption_type": "BULLISH_EXPANSION",
            "conviction": 75,
            "reason": f"Strong convergent taker buy aggression (+{cvd_data.get('delta_percent', 0):.1f}% Delta)."
        }
    elif cvd_data.get("cvd_slope") == "STRONG_SELL_EXPANSION" and p_end < p_start:
        return {
            "divergence": "BEARISH_MOMENTUM_CONVERGENT",
            "absorption_type": "BEARISH_EXPANSION",
            "conviction": 75,
            "reason": f"Strong convergent taker sell aggression ({cvd_data.get('delta_percent', 0):.1f}% Delta)."
        }

    return {
        "divergence": "NEUTRAL_BALANCED",
        "absorption_type": "NEUTRAL",
        "conviction": 50,
        "reason": "Order flow delta and price action are aligned neutrally."
    }

# ======================================================================================
# 3. DEPTH OF MARKET (DOM) STACKED IMBALANCE SCANNER
# ======================================================================================

def analyze_dom_stacked_imbalances(symbol: str, depth_data: dict = None) -> dict:
    """
    Analyzes L2 Order Book Depth (top 50 bids and asks) to detect:
    - Stacked Bid/Ask Imbalance Ratio (>= 3.0x dominant side)
    - Major Liquidity Support Walls & Resistance Ceilings
    - Near-Price (< 0.75%) Slippage Risk
    """
    if depth_data is None:
        depth_data = fetch_l2_depth(symbol, limit=50)

    bids = depth_data.get("bids", [])
    asks = depth_data.get("asks", [])

    if not bids or not asks:
        return {
            "symbol": symbol,
            "imbalance_ratio": 1.0,
            "regime": "NEUTRAL",
            "bid_depth_usd": 0.0,
            "ask_depth_usd": 0.0,
            "stacked_imbalances": []
        }

    best_bid = float(bids[0][0])
    best_ask = float(asks[0][0])
    mid_price = (best_bid + best_ask) / 2.0

    # Calculate depth in USD within ±1.5% range
    bid_depth_usd = 0.0
    ask_depth_usd = 0.0
    top_bid_wall = {"price": best_bid, "qty_usd": 0.0}
    top_ask_wall = {"price": best_ask, "qty_usd": 0.0}

    stacked_bids_count = 0
    stacked_asks_count = 0

    # Process Bids
    for p_str, q_str in bids:
        p = float(p_str)
        q = float(q_str)
        val = p * q
        if p >= mid_price * 0.985:  # Within 1.5% of mid
            bid_depth_usd += val
            if val > top_bid_wall["qty_usd"]:
                top_bid_wall = {"price": p, "qty_usd": val}

    # Process Asks
    for p_str, q_str in asks:
        p = float(p_str)
        q = float(q_str)
        val = p * q
        if p <= mid_price * 1.015:  # Within 1.5% of mid
            ask_depth_usd += val
            if val > top_ask_wall["qty_usd"]:
                top_ask_wall = {"price": p, "qty_usd": val}

    # Check for Stacked Imbalance (Pairwise Level comparison)
    min_len = min(len(bids), len(asks), 15)
    for i in range(min_len):
        b_val = float(bids[i][0]) * float(bids[i][1])
        a_val = float(asks[i][0]) * float(asks[i][1])
        if b_val >= a_val * 3.0 and b_val >= 25000:
            stacked_bids_count += 1
        elif a_val >= b_val * 3.0 and a_val >= 25000:
            stacked_asks_count += 1

    imbalance_ratio = round(bid_depth_usd / max(ask_depth_usd, 0.0001), 2)

    if imbalance_ratio >= 1.80 or stacked_bids_count >= 3:
        regime = "BID_STACKED_SUPPORT"
        bias = "BULLISH_DOM_WALL"
    elif imbalance_ratio <= 0.55 or stacked_asks_count >= 3:
        regime = "ASK_STACKED_RESISTANCE"
        bias = "BEARISH_DOM_WALL"
    else:
        regime = "BALANCED_DEPTH"
        bias = "NEUTRAL"

    return {
        "symbol": symbol,
        "mid_price": round(mid_price, 4),
        "bid_depth_usd": round(bid_depth_usd, 2),
        "ask_depth_usd": round(ask_depth_usd, 2),
        "imbalance_ratio": imbalance_ratio,
        "regime": regime,
        "bias": bias,
        "stacked_bids_count": stacked_bids_count,
        "stacked_asks_count": stacked_asks_count,
        "top_bid_wall": {
            "price": top_bid_wall["price"],
            "qty_usd": round(top_bid_wall["qty_usd"], 2),
            "distance_pct": round(((mid_price - top_bid_wall["price"]) / mid_price) * 100, 2)
        },
        "top_ask_wall": {
            "price": top_ask_wall["price"],
            "qty_usd": round(top_ask_wall["qty_usd"], 2),
            "distance_pct": round(((top_ask_wall["price"] - mid_price) / mid_price) * 100, 2)
        }
    }

# ======================================================================================
# 4. STANDALONE 5m ORDER FLOW & CVD SCALP SETUP GENERATOR
# ======================================================================================

def scan_5m_orderflow_cvd_scalp(symbol: str, candles_5m: list = None) -> dict:
    """
    Generates high-precision 5m Scalp Setups based on Order Flow CVD Absorption & DOM Stacks:
    - Long: Bullish CVD Absorption near Support/Bid Wall (R:R 1:2.0).
    - Short: Bearish CVD Absorption near Resistance/Ask Wall (R:R 1:2.0).
    """
    cvd_data = calculate_cvd_metrics(symbol)
    div_data = detect_cvd_divergence(symbol, candles_5m, cvd_data)
    dom_data = analyze_dom_stacked_imbalances(symbol)

    if not candles_5m or len(candles_5m) < 15:
        # Fallback if candles not passed
        try:
            import market_eyes
            sym_clean = clean_symbol(symbol).replace("USDT", "")
            raw = market_eyes.fetch_candles(sym_clean, bar="5m", limit=30)
            candles_5m = [{"close": float(c[4]), "high": float(c[2]), "low": float(c[3]), "open": float(c[1])} for c in raw]
        except Exception:
            return None

    if not candles_5m:
        return None

    curr = candles_5m[-1]
    curr_c = curr["close"]
    curr_l = curr["low"]
    curr_h = curr["high"]

    # --- CASE 1: BULLISH CVD ABSORPTION + DOM SUPPORT (LONG ENTRY) ---
    if div_data.get("divergence") == "BULLISH_CVD_ABSORPTION" or (
        dom_data.get("regime") == "BID_STACKED_SUPPORT" and cvd_data.get("net_delta", 0) > 0
    ):
        # Stop loss placed below recent micro-low or below top bid wall
        recent_low = min(c["low"] for c in candles_5m[-5:])
        bid_wall_p = dom_data["top_bid_wall"]["price"]
        sl_base = min(recent_low, bid_wall_p * 0.9992) if bid_wall_p > 0 else recent_low
        sl = round(sl_base * 0.9990, 4)
        entry = curr_c
        r_dist = entry - sl

        if r_dist > 0 and (0.0010 <= (r_dist / entry) <= 0.035):
            tp = round(entry + (r_dist * 2.0), 4)
            return {
                "symbol": symbol,
                "side": "LONG",
                "strategy": "5m Order Flow CVD Absorption Scalp",
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
                "orderflow_metrics": {
                    "cvd_delta_pct": cvd_data.get("delta_percent", 0),
                    "dom_imbalance_ratio": dom_data.get("imbalance_ratio", 1.0),
                    "absorption_conviction": div_data.get("conviction", 80)
                },
                "reason": (
                    f"Order Flow Bullish Absorption: {div_data.get('reason')} "
                    f"Supported by DOM Bid Wall @ ${dom_data['top_bid_wall']['price']:,.2f} (${dom_data['top_bid_wall']['qty_usd']:,.0f} USDT)."
                )
            }

    # --- CASE 2: BEARISH CVD ABSORPTION + DOM RESISTANCE (SHORT ENTRY) ---
    if div_data.get("divergence") == "BEARISH_CVD_ABSORPTION" or (
        dom_data.get("regime") == "ASK_STACKED_RESISTANCE" and cvd_data.get("net_delta", 0) < 0
    ):
        recent_high = max(c["high"] for c in candles_5m[-5:])
        ask_wall_p = dom_data["top_ask_wall"]["price"]
        sl_base = max(recent_high, ask_wall_p * 1.0008) if ask_wall_p > 0 else recent_high
        sl = round(sl_base * 1.0010, 4)
        entry = curr_c
        r_dist = sl - entry

        if r_dist > 0 and (0.0010 <= (r_dist / entry) <= 0.035):
            tp = round(entry - (r_dist * 2.0), 4)
            return {
                "symbol": symbol,
                "side": "SHORT",
                "strategy": "5m Order Flow CVD Absorption Scalp",
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
                "orderflow_metrics": {
                    "cvd_delta_pct": cvd_data.get("delta_percent", 0),
                    "dom_imbalance_ratio": dom_data.get("imbalance_ratio", 1.0),
                    "absorption_conviction": div_data.get("conviction", 80)
                },
                "reason": (
                    f"Order Flow Bearish Absorption: {div_data.get('reason')} "
                    f"Capped by DOM Ask Wall @ ${dom_data['top_ask_wall']['price']:,.2f} (${dom_data['top_ask_wall']['qty_usd']:,.0f} USDT)."
                )
            }

    return None

# ======================================================================================
# 5. UNIFIED ORDER FLOW INTEL SUMMARY
# ======================================================================================

def get_orderflow_summary(symbol: str = "BTC") -> dict:
    """
    Returns full order flow package for REST API & Web Dashboard.
    Cached for 4 seconds to prevent redundant rate-limit usage.
    """
    sym = clean_symbol(symbol)
    now = time.time()
    
    if sym in _ORDERFLOW_CACHE:
        cached_time, cached_val = _ORDERFLOW_CACHE[sym]
        if now - cached_time < _CACHE_EXPIRY_SEC:
            return cached_val

    cvd_data = calculate_cvd_metrics(sym)
    div_data = detect_cvd_divergence(sym, None, cvd_data)
    dom_data = analyze_dom_stacked_imbalances(sym)

    summary = {
        "symbol": sym,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cvd": cvd_data,
        "divergence": div_data,
        "dom": dom_data
    }

    _ORDERFLOW_CACHE[sym] = (now, summary)
    return summary

if __name__ == "__main__":
    test_sym = sys.argv[1] if len(sys.argv) > 1 else "BTC"
    print("=" * 70)
    print(f"       🌊 ORDER FLOW, CVD DIVERGENCE & DOM FOOTPRINT MATRIX ({test_sym})")
    print("=" * 70)
    data = get_orderflow_summary(test_sym)
    cvd = data["cvd"]
    dom = data["dom"]
    div = data["divergence"]

    print(f"📊 [CVD TAKER DELTA] Net Delta: {cvd['net_delta']:+,.2f} ({cvd['delta_percent']:+,.1f}%) | Ratio: {cvd['delta_ratio']}x | Slope: {cvd['cvd_slope']}")
    print(f"🧲 [DOM DEPTH L2]   Bids: ${dom['bid_depth_usd']:,.0f} vs Asks: ${dom['ask_depth_usd']:,.0f} (Ratio: {dom['imbalance_ratio']}x | {dom['regime']})")
    print(f"🧱 [DOM TOP WALLS]  Support Bid: ${dom['top_bid_wall']['price']:,.2f} (${dom['top_bid_wall']['qty_usd']:,.0f}) | Resist Ask: ${dom['top_ask_wall']['price']:,.2f} (${dom['top_ask_wall']['qty_usd']:,.0f})")
    print(f"🎯 [ABSORPTION]     Divergence: {div['divergence']} (Conviction: {div['conviction']}%)")
    print(f"💡 [REASON]         {div['reason']}")

    setup = scan_5m_orderflow_cvd_scalp(test_sym)
    if setup:
        print(f"\n⚡ [SCALP SIGNAL GENERATED] {setup['side']} @ ${setup['entry']:,.2f} | SL: ${setup['sl']:,.2f} | TP: ${setup['tp']:,.2f} (2R)")
    else:
        print("\n⚡ [SCALP STATUS] Tidak ada setup absorption ekstrim saat ini (Order flow seimbang).")
    print("=" * 70)

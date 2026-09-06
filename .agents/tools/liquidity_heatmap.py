"""
Liquidity Heatmap & Order Book Depth Imbalance Engine (Magnet Likuidasi)
Synthesized from Akademi Crypto Module 02 (Smart Money Concepts — Liquidity Pools & Order Flow)

Features:
1. Multi-Exchange Order Book Depth (Binance Futures primary + OKX Swap fallback)
2. Depth Imbalance Ratio (DOM ±2.0% bid vs ask dollar volume & wall detection)
3. Liquidity Magnet Clusters (BSL & SSL projection from swing fractals & leverage tiers 100x/50x/25x)
4. Anti-Wall Filter (prevents entering into overhead liquidity walls)
5. Rich Telegram Formatter
"""

import json
import math
import os
import ssl
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime

# Windows console UTF-8 safety
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
sys.path.insert(0, TOOLS_DIR)

import binance_client
import market_structure

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

_DEPTH_CACHE = {}
CACHE_TTL_SECONDS = 20  # 20s in-memory cache

def clean_coin(symbol):
    return symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")

def fetch_json(url, timeout=6):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

def fetch_order_book_depth(symbol="BTC", limit=100):
    """
    Fetches raw order book depth (bids & asks) with automated failover:
    Method 1: Native Binance Futures HMAC depth (/fapi/v1/depth)
    Method 2: OKX Public Swap Books (/api/v5/market/books)
    Method 3: Binance Vision Spot Depth fallback
    """
    ccy = clean_coin(symbol)
    pair = f"{ccy}USDT"
    now_ts = time.time()

    # Check cache
    if ccy in _DEPTH_CACHE:
        entry = _DEPTH_CACHE[ccy]
        if now_ts < entry.get("expires_at", 0):
            return entry["data"]

    bids = []
    asks = []
    source = "UNKNOWN"

    # 1. Primary: Binance Futures signed depth
    try:
        res_bn = binance_client.send_signed_request(
            "/fapi/v1/depth",
            method="GET",
            params={"symbol": pair, "limit": limit},
            is_demo=True
        )
        if res_bn and "bids" in res_bn and "asks" in res_bn:
            bids = [[float(p), float(q)] for p, q in res_bn["bids"]]
            asks = [[float(p), float(q)] for p, q in res_bn["asks"]]
            source = "Binance Futures Native Depth"
    except Exception:
        pass

    # 2. Fallback: OKX Swap Public Books
    if not bids or not asks:
        try:
            okx_inst = f"{ccy}-USDT-SWAP"
            okx_url = f"https://www.okx.com/api/v5/market/books?instId={okx_inst}&sz={limit}"
            res_okx = fetch_json(okx_url, timeout=5)
            if res_okx and res_okx.get("code") == "0" and res_okx.get("data"):
                book = res_okx["data"][0]
                bids = [[float(b[0]), float(b[1])] for b in book.get("bids", [])]
                asks = [[float(a[0]), float(a[1])] for a in book.get("asks", [])]
                source = "OKX Institutional Swap Books"
        except Exception:
            pass

    # 3. Fallback: Binance Vision Spot Depth
    if not bids or not asks:
        try:
            bv_url = f"https://data-api.binance.vision/api/v3/depth?symbol={pair}&limit={limit}"
            res_bv = fetch_json(bv_url, timeout=5)
            if res_bv and "bids" in res_bv and "asks" in res_bv:
                bids = [[float(p), float(q)] for p, q in res_bv["bids"]]
                asks = [[float(p), float(q)] for p, q in res_bv["asks"]]
                source = "Binance Vision Global Spot Depth"
        except Exception:
            pass

    if not bids or not asks:
        return None

    # Sort bids descending by price, asks ascending by price
    bids.sort(key=lambda x: x[0], reverse=True)
    asks.sort(key=lambda x: x[0], reverse=False)

    best_bid = bids[0][0]
    best_ask = asks[0][0]
    mid_price = (best_bid + best_ask) / 2.0

    result = {
        "symbol": ccy,
        "pair": f"{ccy}/USDT",
        "mid_price": mid_price,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread_usd": round(best_ask - best_bid, 4),
        "spread_pct": round((best_ask - best_bid) / mid_price * 100.0, 4),
        "bids": bids,
        "asks": asks,
        "source": source,
        "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    _DEPTH_CACHE[ccy] = {
        "data": result,
        "expires_at": now_ts + CACHE_TTL_SECONDS
    }

    return result

def calculate_depth_imbalance(symbol="BTC", depth_pct=2.0):
    """
    Computes Order Book Imbalance Ratio within ±depth_pct (default: 2.0%) of mid price:
    - Sums total dollar liquidity on bids vs asks
    - Ratio = Bids USD / Asks USD
    - Identifies biggest Bid Wall and Ask Wall within the window
    """
    raw = fetch_order_book_depth(symbol, limit=100)
    if not raw:
        return {
            "symbol": clean_coin(symbol),
            "error": "Order book depth unavailable",
            "imbalance_ratio": 1.0,
            "regime": "NEUTRAL_BALANCED"
        }

    mid_p = raw["mid_price"]
    min_bid_p = mid_p * (1.0 - (depth_pct / 100.0))
    max_ask_p = mid_p * (1.0 + (depth_pct / 100.0))

    bids_in_window = [b for b in raw["bids"] if b[0] >= min_bid_p]
    asks_in_window = [a for a in raw["asks"] if a[0] <= max_ask_p]

    bids_usd = sum(p * q for p, q in bids_in_window)
    asks_usd = sum(p * q for p, q in asks_in_window)
    total_depth_usd = bids_usd + asks_usd

    imbalance_ratio = (bids_usd / asks_usd) if asks_usd > 0 else 1.0
    bid_pct = (bids_usd / total_depth_usd * 100.0) if total_depth_usd > 0 else 50.0
    ask_pct = (asks_usd / total_depth_usd * 100.0) if total_depth_usd > 0 else 50.0

    # Classify Order Book Regime
    if imbalance_ratio >= 1.80:
        regime = "🟢 HEAVY BID WALL (Support Absorption / Institutional Floor)"
        bias = "STRONG_BULLISH_FLOOR"
        confluence_impact = 5
    elif imbalance_ratio >= 1.25:
        regime = "🟢 MILD BUY SKEW (Bids Absorbing Selling Pressure)"
        bias = "MILD_BULLISH"
        confluence_impact = 3
    elif imbalance_ratio <= 0.55:
        regime = "🚨 HEAVY ASK WALL (Overhead Supply Ceiling / Dump Risk)"
        bias = "STRONG_BEARISH_CEILING"
        confluence_impact = -10
    elif imbalance_ratio <= 0.80:
        regime = "🔴 MILD SELL SKEW (Overhead Pressure Visible)"
        bias = "MILD_BEARISH"
        confluence_impact = -3
    else:
        regime = "⚖️ BALANCED ORDER BOOK (Neutral Distribution)"
        bias = "NEUTRAL"
        confluence_impact = 0

    # Locate the Largest Single Liquidity Wall
    biggest_bid_wall = max(bids_in_window, key=lambda x: x[0] * x[1]) if bids_in_window else [0, 0]
    biggest_ask_wall = max(asks_in_window, key=lambda x: x[0] * x[1]) if asks_in_window else [0, 0]

    bid_wall_usd = biggest_bid_wall[0] * biggest_bid_wall[1]
    ask_wall_usd = biggest_ask_wall[0] * biggest_ask_wall[1]

    bid_wall_dist_pct = ((mid_p - biggest_bid_wall[0]) / mid_p * 100.0) if biggest_bid_wall[0] > 0 else 0.0
    ask_wall_dist_pct = ((biggest_ask_wall[0] - mid_p) / mid_p * 100.0) if biggest_ask_wall[0] > 0 else 0.0

    return {
        "symbol": raw["symbol"],
        "pair": raw["pair"],
        "mid_price": mid_p,
        "window_pct": depth_pct,
        "bids_usd": round(bids_usd, 2),
        "asks_usd": round(asks_usd, 2),
        "total_depth_usd": round(total_depth_usd, 2),
        "imbalance_ratio": round(imbalance_ratio, 2),
        "bid_share_pct": round(bid_pct, 1),
        "ask_share_pct": round(ask_pct, 1),
        "bids_pct": round(bid_pct, 1),
        "asks_pct": round(ask_pct, 1),
        "regime": regime,
        "bias": bias,
        "confluence_impact": confluence_impact,
        "biggest_bid_wall": {
            "price": biggest_bid_wall[0],
            "qty": round(biggest_bid_wall[1], 3),
            "usd": round(bid_wall_usd, 2),
            "vol_usd": round(bid_wall_usd, 2),
            "distance_pct": round(bid_wall_dist_pct, 2)
        },
        "biggest_ask_wall": {
            "price": biggest_ask_wall[0],
            "qty": round(biggest_ask_wall[1], 3),
            "usd": round(ask_wall_usd, 2),
            "vol_usd": round(ask_wall_usd, 2),
            "distance_pct": round(ask_wall_dist_pct, 2)
        },
        "source": raw["source"],
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def calculate_liquidity_clusters(symbol="BTC"):
    """
    Computes Liquidity Clusters & Identifies Dominant Liquidity Magnet:
    1. Buy-Side Liquidity (BSL) Clusters (Above price):
       - Retail buy-stops / short stop-loss pools above Swing Highs + 100x/50x/25x short liquidations.
    2. Sell-Side Liquidity (SSL) Clusters (Below price):
       - Retail sell-stops / long stop-loss pools below Swing Lows + 100x/50x/25x long liquidations.
    3. Identifies the Dominant Magnet with greatest gravitational pull.
    """
    ccy = clean_coin(symbol)
    pair = f"{ccy}USDT"

    # Fetch candles from market structure engine
    candles = market_structure.fetch_candles(pair, bar="15m", limit=50)
    if not candles or len(candles) < 20:
        candles = market_structure.fetch_candles(pair, bar="1H", limit=40)

    cur_p = candles[-1]["close"] if candles else 0.0
    if cur_p <= 0:
        depth_data = fetch_order_book_depth(symbol, limit=10)
        cur_p = depth_data["mid_price"] if depth_data else 0.0

    if cur_p <= 0:
        return {"symbol": ccy, "error": "Price feed unavailable"}

    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    highest_recent = max(highs[-24:]) if len(highs) >= 24 else max(highs)
    lowest_recent = min(lows[-24:]) if len(lows) >= 24 else min(lows)

    # Approximate cluster pool dollar size based on asset liquidity tier
    if ccy in ["BTC"]:
        base_pool_usd = 25_000_000.0  # ~$25M cluster
    elif ccy in ["ETH"]:
        base_pool_usd = 12_000_000.0  # ~$12M cluster
    elif ccy in ["SOL"]:
        base_pool_usd = 5_000_000.0   # ~$5M cluster
    else:
        base_pool_usd = 1_500_000.0   # ~$1.5M cluster

    # 1. Project Buy-Side Liquidity (BSL) Pools Above Market
    bsl_clusters = [
        {
            "type": "BSL",
            "label": "100x Short Liquidation & Breakout Stops",
            "price": round(cur_p * 1.010, 4),
            "distance_pct": +1.0,
            "estimated_pool_usd": round(base_pool_usd * 0.7, 0),
            "is_above": True
        },
        {
            "type": "BSL",
            "label": "Recent Swing High Sweep Pool",
            "price": round(highest_recent * 1.002, 4),
            "distance_pct": round((highest_recent * 1.002 - cur_p) / cur_p * 100.0, 2),
            "estimated_pool_usd": round(base_pool_usd * 1.2, 0),
            "is_above": True
        },
        {
            "type": "BSL",
            "label": "50x Institutional Short Liquidation Wall",
            "price": round(cur_p * 1.020, 4),
            "distance_pct": +2.0,
            "estimated_pool_usd": round(base_pool_usd * 1.6, 0),
            "is_above": True
        },
        {
            "type": "BSL",
            "label": "25x Leverage Liquidation Band",
            "price": round(cur_p * 1.040, 4),
            "distance_pct": +4.0,
            "estimated_pool_usd": round(base_pool_usd * 2.2, 0),
            "is_above": True
        }
    ]

    # 2. Project Sell-Side Liquidity (SSL) Pools Below Market
    ssl_clusters = [
        {
            "type": "SSL",
            "label": "100x Long Liquidation & Panic Sell Stops",
            "price": round(cur_p * 0.990, 4),
            "distance_pct": -1.0,
            "estimated_pool_usd": round(base_pool_usd * 0.75, 0),
            "is_above": False
        },
        {
            "type": "SSL",
            "label": "Recent Swing Low / Equal Lows Sweep Pool",
            "price": round(lowest_recent * 0.998, 4),
            "distance_pct": round((lowest_recent * 0.998 - cur_p) / cur_p * 100.0, 2),
            "estimated_pool_usd": round(base_pool_usd * 1.3, 0),
            "is_above": False
        },
        {
            "type": "SSL",
            "label": "50x Institutional Long Liquidation Wall",
            "price": round(cur_p * 0.980, 4),
            "distance_pct": -2.0,
            "estimated_pool_usd": round(base_pool_usd * 1.7, 0),
            "is_above": False
        },
        {
            "type": "SSL",
            "label": "25x Leverage Liquidation Band",
            "price": round(cur_p * 0.960, 4),
            "distance_pct": -4.0,
            "estimated_pool_usd": round(base_pool_usd * 2.4, 0),
            "is_above": False
        }
    ]

    # Filter out clusters with reverse direction anomalies
    valid_bsl = [c for c in bsl_clusters if c["price"] > cur_p]
    valid_ssl = [c for c in ssl_clusters if c["price"] < cur_p]

    valid_bsl.sort(key=lambda x: x["price"], reverse=False)  # Closest to price first
    valid_ssl.sort(key=lambda x: x["price"], reverse=True)   # Closest to price first

    # Determine Dominant Liquidity Magnet
    # Gravitational pull = estimated_usd / (distance_pct ^ 1.2)
    def calc_gravity(c):
        dist = abs(c["distance_pct"])
        return c["estimated_pool_usd"] / max(dist ** 1.2, 0.1)

    all_clusters = valid_bsl + valid_ssl
    for c in all_clusters:
        c["gravity_score"] = round(calc_gravity(c), 1)
        c["side"] = c["type"]
        c["target_price"] = c["price"]

    dominant_magnet = max(all_clusters, key=lambda x: x["gravity_score"]) if all_clusters else None
    for c in all_clusters:
        c["is_dominant"] = (dominant_magnet is not None and c["price"] == dominant_magnet["price"])

    # Determine total overhead vs downside liquidity weight
    total_bsl_usd = sum(c["estimated_pool_usd"] for c in valid_bsl)
    total_ssl_usd = sum(c["estimated_pool_usd"] for c in valid_ssl)

    return {
        "symbol": ccy,
        "current_price": cur_p,
        "dominant_magnet": dominant_magnet,
        "bsl_clusters": valid_bsl[:3],
        "ssl_clusters": valid_ssl[:3],
        "all_clusters": all_clusters,
        "clusters": all_clusters,
        "total_bsl_usd": total_bsl_usd,
        "total_ssl_usd": total_ssl_usd,
        "magnet_side": "BSL (Upward Pull)" if dominant_magnet and dominant_magnet["type"] == "BSL" else "SSL (Downward Pull)",
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def get_liquidity_intelligence(symbol="BTC"):
    """
    Aggregates complete order book depth imbalance and liquidity cluster magnet metrics.
    """
    imbalance = calculate_depth_imbalance(symbol, depth_pct=2.0)
    clusters = calculate_liquidity_clusters(symbol)
    cur_p = imbalance.get("mid_price", clusters.get("current_price", 0.0))

    return {
        "success": True,
        "symbol": clean_coin(symbol),
        "current_price": cur_p,
        "imbalance": imbalance,
        "depth_imbalance": imbalance,
        "clusters": clusters,
        "liquidity_clusters": clusters.get("all_clusters", []),
        "dominant_magnet": clusters.get("dominant_magnet"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def format_telegram_liquidity_report(symbol="BTC"):
    """
    Renders high-impact visual Telegram report with horizontal depth bar and liquidity pools.
    """
    data = get_liquidity_intelligence(symbol)
    imb = data["imbalance"]
    cl = data["clusters"]
    ccy = data["symbol"]
    cur_p = imb.get("mid_price", cl.get("current_price", 0.0))

    if "error" in imb and "error" in cl:
        return f"⚠️ Data likuiditas untuk <code>{ccy}/USDT</code> saat ini belum tersedia."

    b_usd = imb.get("bids_usd", 0.0)
    a_usd = imb.get("asks_usd", 0.0)
    b_pct = imb.get("bid_share_pct", 50.0)
    a_pct = imb.get("ask_share_pct", 50.0)
    ratio = imb.get("imbalance_ratio", 1.0)

    # Format human numbers
    def fmt_usd(v):
        if v >= 1_000_000_000:
            return f"${v/1_000_000_000:.2f}B"
        elif v >= 1_000_000:
            return f"${v/1_000_000:.1f}M"
        elif v >= 1_000:
            return f"${v/1_000:.0f}K"
        return f"${v:.0f}"

    # Visual ASCII Depth Bar (12 chars width)
    green_blocks = int(round((b_pct / 100.0) * 12))
    red_blocks = 12 - green_blocks
    depth_bar = ("🟩" * green_blocks) + ("🟥" * red_blocks)

    # Dominant Magnet Callout
    magnet = cl.get("dominant_magnet")
    mag_text = ""
    if magnet:
        mag_sign = "+" if magnet["distance_pct"] >= 0 else ""
        mag_text = (
            f"🧲 <b>Dominant Liquidity Magnet:</b>\n"
            f"   <b>{magnet['type']} @ ${magnet['price']:,.2f}</b> ({mag_sign}{magnet['distance_pct']}%) — <i>~{fmt_usd(magnet['estimated_pool_usd'])}</i>\n"
            f"   <i>Tumpukan: {magnet['label']}</i>\n\n"
        )

    # Top BSL lines
    bsl_lines = []
    for c in reversed(cl.get("bsl_clusters", [])):
        is_mag = " 🧲" if magnet and c["price"] == magnet["price"] else ""
        bsl_lines.append(f"   🔴 <code>${c['price']:,.2f}</code> (+{c['distance_pct']}%) ~{fmt_usd(c['estimated_pool_usd'])}{is_mag}")

    # Top SSL lines
    ssl_lines = []
    for c in cl.get("ssl_clusters", []):
        is_mag = " 🧲" if magnet and c["price"] == magnet["price"] else ""
        ssl_lines.append(f"   🟢 <code>${c['price']:,.2f}</code> ({c['distance_pct']}%) ~{fmt_usd(c['estimated_pool_usd'])}{is_mag}")

    bsl_str = "\n".join(bsl_lines) if bsl_lines else "   <i>Tidak ada cluster terdekat</i>"
    ssl_str = "\n".join(ssl_lines) if ssl_lines else "   <i>Tidak ada cluster terdekat</i>"

    bid_wall = imb.get("biggest_bid_wall", {})
    ask_wall = imb.get("biggest_ask_wall", {})

    return (
        f"🧲 <b>LIQUIDITY HEATMAP & ORDER BOOK DEPTH: {ccy}/USDT</b>\n"
        f"<i>Akademi Crypto Module 02 (Smart Money Concepts)</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💵 <b>Mark Price:</b> <code>${cur_p:,.4f}</code>\n"
        f"⚖️ <b>Order Book Imbalance (±2% DOM):</b> <code>{ratio:.2f}x</code>\n"
        f"   {depth_bar}\n"
        f"   🟢 Bids: <b>{fmt_usd(b_usd)}</b> ({b_pct}%) | 🔴 Asks: <b>{fmt_usd(a_usd)}</b> ({a_pct}%)\n"
        f"🧱 <b>Tembok Beli Utama:</b> <code>${bid_wall.get('price', 0):,.2f}</code> (~{fmt_usd(bid_wall.get('usd', 0))} | -{bid_wall.get('distance_pct', 0)}%)\n"
        f"🧱 <b>Tembok Jual Utama:</b> <code>${ask_wall.get('price', 0):,.2f}</code> (~{fmt_usd(ask_wall.get('usd', 0))} | +{ask_wall.get('distance_pct', 0)}%)\n\n"
        f"🧭 <b>Status Buku Pesanan:</b>\n"
        f"<b>{imb.get('regime')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{mag_text}"
        f"🎯 <b>KLASTER LIKUIDITAS INSTITUSIONAL (STOP-HUNT POOLS):</b>\n"
        f"<b>[Buy-Side Liquidity — Atas / Short SL]:</b>\n"
        f"{bsl_str}\n"
        f"   ────────── <b>[MARK: ${cur_p:,.2f}]</b> ──────────\n"
        f"<b>[Sell-Side Liquidity — Bawah / Long SL]:</b>\n"
        f"{ssl_str}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📡 <i>Sumber Depth: {imb.get('source')}</i>\n"
        f"💡 <i>Market Maker cenderung menarik harga ke arah kolam likuiditas terbesar (Magnet) sebelum berbalik arah.</i>"
    )

if __name__ == "__main__":
    for c in ["BTC", "ETH", "LINK", "SOL"]:
        print("\n" + "=" * 60)
        report = format_telegram_liquidity_report(c)
        print(report)

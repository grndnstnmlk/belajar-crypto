"""
TradingView Screener Institutional Adapter (tvscreener)
Broad-market scanner, multi-timeframe technical indicator harvester, and DEX/CEX momentum discovery.
Synthesized with Akademi Crypto Top-Down Screening & Institutional Confluence Framework.
"""

import os
import sys
import time
import json
import logging
from typing import Dict, List, Any, Optional

try:
    import tvscreener as tv
    import pandas as pd
    HAS_TVSCREENER = True
except ImportError:
    HAS_TVSCREENER = False

# Memory Cache to protect network bandwidth & achieve sub-millisecond latency
_CACHE = {
    "futures_scan": {"data": None, "timestamp": 0},
    "dex_gems": {"data": None, "timestamp": 0},
    "tech_summary": {} # key: symbol -> {"data": ..., "timestamp": ...}
}
CACHE_TTL_SECONDS = 30

def clean_base_symbol(tv_symbol: str) -> str:
    """Extracts clean base symbol from TradingView ticker (e.g. 'BINANCE:BTCUSDT.P' -> 'BTC')."""
    if not tv_symbol:
        return ""
    sym = tv_symbol.split(":")[-1].replace(".P", "")
    for quote in ["USDT", "USDC", "BUSD", "USD"]:
        if sym.endswith(quote):
            return sym[:-len(quote)]
    return sym

def format_technical_rating(raw_val: Any) -> str:
    """Converts TradingView numerical rating (-1.0 to +1.0) or string to human-readable label."""
    if isinstance(raw_val, (int, float)):
        if raw_val >= 0.5:
            return "STRONG_BUY"
        elif raw_val >= 0.1:
            return "BUY"
        elif raw_val <= -0.5:
            return "STRONG_SELL"
        elif raw_val <= -0.1:
            return "SELL"
        else:
            return "NEUTRAL"
    val_str = str(raw_val).strip().upper()
    if "STRONG BUY" in val_str:
        return "STRONG_BUY"
    elif "BUY" in val_str:
        return "BUY"
    elif "STRONG SELL" in val_str:
        return "STRONG_SELL"
    elif "SELL" in val_str:
        return "SELL"
    return "NEUTRAL"

def scan_binance_futures_universe(top_n: int = 30, min_volume_usd: float = 10_000_000) -> Dict[str, Any]:
    """
    Scans the entire Binance Futures market using TradingView Screener API.
    Returns categorized market leaders, momentum surges, oversold dips, and overbought extremes.
    """
    now = time.time()
    if _CACHE["futures_scan"]["data"] and (now - _CACHE["futures_scan"]["timestamp"] < CACHE_TTL_SECONDS):
        return _CACHE["futures_scan"]["data"]

    if not HAS_TVSCREENER:
        return _fallback_binance_scan(top_n=top_n)

    try:
        cs = tv.CryptoScreener()
        cs.where(tv.CryptoField.EXCHANGE == "BINANCE")
        cs.set_range(0, 150)
        df = cs.get()

        if df is None or df.empty:
            return _fallback_binance_scan(top_n=top_n)

        # Filter perpetual futures pairs (e.g., .P or USDT)
        items = []
        for _, row in df.iterrows():
            sym_raw = str(row.get("Symbol", ""))
            if not sym_raw.startswith("BINANCE:") or not (".P" in sym_raw or "USDT" in sym_raw):
                continue
            
            base = clean_base_symbol(sym_raw)
            if not base or base in ["USDC", "FDUSD", "TUSD", "EUR"]:
                continue

            price = float(row.get("Price", 0) or 0)
            vol_24h = float(row.get("24-Hour Volume", 0) or row.get("Volume", 0) or 0)
            vol_usd = float(row.get("24-Hour Quote Volume", 0) or (vol_24h * price) if price > 0 else 0)
            change_24h = float(row.get("Change %", 0) or row.get("Change", 0) or 0)
            rsi = float(row.get("Relative Strength Index (14)", 0) or row.get("RSI", 50) or 50)
            raw_rating = row.get("Technical Rating", "NEUTRAL")
            rating = format_technical_rating(raw_rating)
            volatility = float(row.get("Volatility", 0) or 0)
            atr = float(row.get("Average True Range (14)", 0) or 0)

            # Ignore illiquid pairs
            if vol_usd > 0 and vol_usd < min_volume_usd:
                continue

            items.append({
                "symbol": f"{base}USDT",
                "base": base,
                "tv_symbol": sym_raw,
                "price": price,
                "volume_usd": vol_usd,
                "change_24h_pct": round(change_24h, 2),
                "rsi_14": round(rsi, 2),
                "technical_rating": rating,
                "volatility_pct": round(volatility, 2),
                "atr": round(atr, 6),
                "timestamp": int(now * 1000)
            })

        # Sort and categorize
        items.sort(key=lambda x: x["volume_usd"], reverse=True)
        top_volume = items[:top_n]

        # Top gainers (Bullish Momentum)
        gainers = sorted(items, key=lambda x: x["change_24h_pct"], reverse=True)[:10]
        # Top losers / Oversold Dips (Potential Long Discount)
        losers = sorted(items, key=lambda x: x["change_24h_pct"])[:10]
        # Oversold RSI (< 35)
        oversold_dips = [x for x in items if x["rsi_14"] < 38]
        oversold_dips.sort(key=lambda x: x["rsi_14"])
        # Overbought RSI (> 65)
        overbought_pumps = [x for x in items if x["rsi_14"] > 65]
        overbought_pumps.sort(key=lambda x: x["rsi_14"], reverse=True)

        result = {
            "source": "TRADINGVIEW_SCREENER_API",
            "status": "SUCCESS",
            "total_pairs_scanned": len(items),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "top_volume": top_volume,
            "top_gainers": gainers,
            "top_losers": losers,
            "oversold_setups": oversold_dips[:10],
            "overbought_setups": overbought_pumps[:10],
            "recommendation_summary": {
                "strong_buys": len([x for x in items if "Strong Buy" in x["technical_rating"]]),
                "buys": len([x for x in items if "Buy" in x["technical_rating"] and "Strong" not in x["technical_rating"]]),
                "sells": len([x for x in items if "Sell" in x["technical_rating"]]),
                "neutral": len([x for x in items if "Neutral" in x["technical_rating"]])
            }
        }

        _CACHE["futures_scan"] = {"data": result, "timestamp": now}
        return result

    except Exception as e:
        return _fallback_binance_scan(top_n=top_n, error_note=str(e))

def get_tradingview_technical_summary(symbol: str) -> Dict[str, Any]:
    """
    Retrieves TradingView technical indicators and multi-indicator consensus rating for a specific coin.
    """
    base = symbol.upper().replace("USDT", "").replace("USDC", "").replace(".P", "")
    now = time.time()
    
    if base in _CACHE["tech_summary"]:
        entry = _CACHE["tech_summary"][base]
        if now - entry["timestamp"] < CACHE_TTL_SECONDS:
            return entry["data"]

    if not HAS_TVSCREENER:
        return {"symbol": f"{base}USDT", "base": base, "source": "FALLBACK_HEURISTIC", "status": "TV_UNAVAILABLE"}

    try:
        cs = tv.CryptoScreener()
        cs.where(tv.CryptoField.EXCHANGE == "BINANCE")
        cs.set_range(0, 100)
        df = cs.get()

        if df is not None and not df.empty:
            match = df[df["Symbol"].str.contains(f":{base}USDT", case=False, na=False)]
            if not match.empty:
                row = match.iloc[0]
                res = {
                    "symbol": f"{base}USDT",
                    "base": base,
                    "tv_symbol": str(row.get("Symbol")),
                    "price": float(row.get("Price", 0) or 0),
                    "change_24h_pct": float(row.get("Change %", 0) or 0),
                    "rsi_14": float(row.get("Relative Strength Index (14)", 50) or 50),
                    "macd_level": float(row.get("MACD Level (12, 26)", 0) or 0),
                    "macd_signal": float(row.get("MACD Signal (12, 26)", 0) or 0),
                    "stoch_k": float(row.get("Stochastic %K (14, 3, 3)", 50) or 50),
                    "technical_rating": format_technical_rating(row.get("Technical Rating", "NEUTRAL")),
                    "volatility_pct": float(row.get("Volatility", 0) or 0),
                    "volume_24h_usd": float(row.get("24-Hour Quote Volume", 0) or 0),
                    "source": "TRADINGVIEW_API",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                _CACHE["tech_summary"][base] = {"data": res, "timestamp": now}
                return res

    except Exception as e:
        pass

    return {
        "symbol": f"{base}USDT",
        "base": base,
        "source": "FALLBACK_NEUTRAL",
        "technical_rating": "NEUTRAL",
        "rsi_14": 50.0,
        "note": "TradingView single query timed out, neutral baseline applied."
    }

def scan_dex_and_altcoin_gems(top_n: int = 15) -> Dict[str, Any]:
    """
    Scans Coin / DEX screener for trending emerging tokens across decentralized ecosystems.
    """
    now = time.time()
    if _CACHE["dex_gems"]["data"] and (now - _CACHE["dex_gems"]["timestamp"] < CACHE_TTL_SECONDS * 2):
        return _CACHE["dex_gems"]["data"]

    if not HAS_TVSCREENER:
        return {"source": "FALLBACK", "gems": []}

    try:
        coin_s = tv.CoinScreener()
        coin_s.set_range(0, 50)
        df = coin_s.get()

        gems = []
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                sym = str(row.get("Symbol", "") or row.get("Name", ""))
                price = float(row.get("Price", 0) or 0)
                vol_usd = float(row.get("24-Hour Volume", 0) or 0)
                change = float(row.get("Change %", 0) or 0)
                mcap = float(row.get("Market Capitalization", 0) or 0)

                gems.append({
                    "name": str(row.get("Name", sym)),
                    "symbol": sym,
                    "price": price,
                    "market_cap_usd": mcap,
                    "volume_24h_usd": vol_usd,
                    "change_24h_pct": round(change, 2)
                })

        gems.sort(key=lambda x: x["volume_24h_usd"], reverse=True)
        res = {
            "source": "TRADINGVIEW_COIN_SCREENER",
            "status": "SUCCESS",
            "gems_count": len(gems),
            "gems": gems[:top_n],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        _CACHE["dex_gems"] = {"data": res, "timestamp": now}
        return res

    except Exception as e:
        return {"source": "FALLBACK", "error": str(e), "gems": []}

def _fallback_binance_scan(top_n: int = 20, error_note: str = "") -> Dict[str, Any]:
    """Graceful fallback to direct Binance 24hr ticker API if TradingView library fails."""
    import urllib.request
    try:
        url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        req = urllib.request.Request(url, headers={"User-Agent": "TVScreenerFallback/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        items = []
        for t in data:
            sym = t.get("symbol", "")
            if not sym.endswith("USDT"):
                continue
            base = sym[:-4]
            if base in ["USDC", "FDUSD", "TUSD", "EUR", "USDP"]:
                continue

            vol_usd = float(t.get("quoteVolume", 0))
            change = float(t.get("priceChangePercent", 0))
            price = float(t.get("lastPrice", 0))

            items.append({
                "symbol": sym,
                "base": base,
                "tv_symbol": f"BINANCE:{sym}.P",
                "price": price,
                "volume_usd": vol_usd,
                "change_24h_pct": round(change, 2),
                "rsi_14": 50.0,
                "technical_rating": "NEUTRAL_FALLBACK",
                "volatility_pct": 0.0,
                "atr": 0.0
            })

        items.sort(key=lambda x: x["volume_usd"], reverse=True)
        return {
            "source": "BINANCE_FUTURES_FALLBACK",
            "status": "FALLBACK_ACTIVE",
            "error_note": error_note,
            "total_pairs_scanned": len(items),
            "top_volume": items[:top_n],
            "top_gainers": sorted(items, key=lambda x: x["change_24h_pct"], reverse=True)[:10],
            "top_losers": sorted(items, key=lambda x: x["change_24h_pct"])[:10],
            "oversold_setups": [],
            "overbought_setups": []
        }
    except Exception as e:
        return {"source": "OFFLINE", "error": str(e), "top_volume": []}

if __name__ == "__main__":
    print("=== TESTING TRADINGVIEW SCREENER ADAPTER ===")
    start_t = time.time()
    res = scan_binance_futures_universe(top_n=10)
    dur = (time.time() - start_t) * 1000
    print(f"Scan selesai dalam {dur:.1f}ms (Source: {res.get('source')})")
    print(f"Total pairs: {res.get('total_pairs_scanned')}")
    print("\n--- TOP 5 BY VOLUME ---")
    for item in res.get("top_volume", [])[:5]:
        print(f" * {item['symbol']} | Price: ${item['price']:,.4f} | Vol: ${item['volume_usd']/1e6:,.1f}M | 24h: {item['change_24h_pct']:+.2f}% | Rating: {item['technical_rating']}")
    
    print("\n--- BTC TECHNICAL SUMMARY ---")
    btc_tech = get_tradingview_technical_summary("BTC")
    print(f"BTC Rating: {btc_tech.get('technical_rating')} | RSI: {btc_tech.get('rsi_14')} | Volatility: {btc_tech.get('volatility_pct')}%")

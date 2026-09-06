"""
Coinbase Institutional Premium Index Engine
Measures real-time price divergence between Coinbase Pro (US Institutional / Wall Street Spot)
and Binance/OKX (Global Retail / Offshore Crypto).

Replicates CryptoQuant's flagship institutional macro compass at 100% zero cost.
"""

import json
import os
import ssl
import sys
import time
import urllib.request
from datetime import datetime

# Windows console UTF-8 safety
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

_PREMIUM_CACHE = {}
CACHE_TTL = 30  # 30 seconds cache

def clean_coin(symbol):
    return symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")

def fetch_json(url, timeout=5):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

def get_coinbase_premium(symbol="BTC", force_refresh=False):
    """
    Computes Coinbase Premium Index:
    Spread = Coinbase Price - Global Benchmark Price
    Premium % = (Spread / Global Benchmark Price) * 100
    """
    ccy = clean_coin(symbol)
    now_ts = time.time()

    if not force_refresh and ccy in _PREMIUM_CACHE:
        entry = _PREMIUM_CACHE[ccy]
        if now_ts < entry.get("expires_at", 0):
            return entry["data"]

    # 1. Fetch Coinbase Spot Price
    cb_price = 0.0
    cb_url = f"https://api.coinbase.com/v2/prices/{ccy}-USD/spot"
    cb_res = fetch_json(cb_url)
    if cb_res and cb_res.get("data") and "amount" in cb_res["data"]:
        cb_price = float(cb_res["data"]["amount"])

    # 2. Fetch Global Benchmark Spot Price (OKX with Binance Vision fallback)
    global_price = 0.0
    okx_url = f"https://www.okx.com/api/v5/market/ticker?instId={ccy}-USDT"
    okx_res = fetch_json(okx_url)
    if okx_res and okx_res.get("code") == "0" and okx_res.get("data"):
        global_price = float(okx_res["data"][0].get("last", 0.0))

    if global_price <= 0:
        binance_url = f"https://data-api.binance.vision/api/v3/ticker/price?symbol={ccy}USDT"
        bn_res = fetch_json(binance_url)
        if bn_res and "price" in bn_res:
            global_price = float(bn_res["price"])

    if cb_price <= 0 or global_price <= 0:
        return {
            "symbol": ccy,
            "coinbase_price": cb_price,
            "global_price": global_price,
            "premium_usd": 0.0,
            "premium_pct": 0.0,
            "regime": "⚪ DATA UNAVAILABLE",
            "bias": "NEUTRAL",
            "confluence_bonus": 0,
            "is_us_inflow": False,
            "is_us_dump": False,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    spread_usd = cb_price - global_price
    premium_pct = (spread_usd / global_price) * 100.0

    # Interpret Institutional Regime (CryptoQuant Standard)
    if premium_pct >= 0.035:
        regime = "🚀 AGGRESSIVE US INSTITUTIONAL BUYING (Wall Street Inflow)"
        bias = "STRONG_BULLISH"
        confluence_bonus = +8
        is_us_inflow = True
        is_us_dump = False
    elif premium_pct >= 0.010:
        regime = "🟢 MILD US ACCUMULATION (Steady Institutional Bids)"
        bias = "BULLISH"
        confluence_bonus = +4
        is_us_inflow = True
        is_us_dump = False
    elif premium_pct >= -0.015:
        regime = "⚪ BALANCED FLOW (US / Global Equilibrium)"
        bias = "NEUTRAL"
        confluence_bonus = 0
        is_us_inflow = False
        is_us_dump = False
    elif premium_pct >= -0.040:
        regime = "⚠️ MILD US DISCOUNT (Lack of US Bids / Passive Market)"
        bias = "CAUTIOUS"
        confluence_bonus = -4
        is_us_inflow = False
        is_us_dump = False
    else:
        regime = "🚨 HEAVY US INSTITUTIONAL DISCOUNT (High Bull Trap / Dump Risk)"
        bias = "BEARISH_TRAP_RISK"
        confluence_bonus = -8
        is_us_inflow = False
        is_us_dump = True

    result = {
        "symbol": ccy,
        "coinbase_price": cb_price,
        "global_price": global_price,
        "premium_usd": round(spread_usd, 4),
        "premium_pct": round(premium_pct, 4),
        "regime": regime,
        "bias": bias,
        "confluence_bonus": confluence_bonus,
        "is_us_inflow": is_us_inflow,
        "is_us_dump": is_us_dump,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    _PREMIUM_CACHE[ccy] = {
        "data": result,
        "expires_at": now_ts + CACHE_TTL
    }

    return result

def get_all_premiums():
    """Fetches Coinbase Premium for core institutional assets (BTC, ETH, SOL)."""
    return {
        "BTC": get_coinbase_premium("BTC"),
        "ETH": get_coinbase_premium("ETH"),
        "SOL": get_coinbase_premium("SOL")
    }

def format_telegram_report(symbol_or_all="ALL"):
    """
    Formats rich Telegram card for Coinbase Institutional Premium Index.
    """
    if symbol_or_all.upper() == "ALL":
        data = get_all_premiums()
        lines = [
            "🏛️ <b>COINBASE INSTITUTIONAL PREMIUM INDEX</b>",
            "<i>CryptoQuant Macro Compass (Wall Street vs Global Retail)</i>",
            "━━━━━━━━━━━━━━━━━━"
        ]
        for coin, d in data.items():
            lines.append(
                f"💎 <b>{coin}:</b> <code>{d['premium_pct']:+.4f}%</code> (${d['premium_usd']:+,.2f})\n"
                f"   • Coinbase Spot: <code>${d['coinbase_price']:,.2f}</code>\n"
                f"   • Global Spot: <code>${d['global_price']:,.2f}</code>\n"
                f"   • Status: <i>{d['regime']}</i>\n"
            )

        lines.append("━━━━━━━━━━━━━━━━━━")
        lines.append("💡 <i>Nilai (+) = Institusi AS memborong koin fisik (Bullish Inflow).</i>")
        lines.append("💡 <i>Nilai (-) = Diskon di AS, rawan Bull Trap / pembongkaran posisi.</i>")
        lines.append(f"🕒 <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>")
        return "\n".join(lines)
    else:
        d = get_coinbase_premium(symbol_or_all)
        return (
            f"🏛️ <b>COINBASE PREMIUM INDEX: {d['symbol']}/USDT</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📈 <b>Index Premium:</b> <code>{d['premium_pct']:+.4f}%</code>\n"
            f"💵 <b>Selisih Harga:</b> <code>${d['premium_usd']:+,.2f} USD</code>\n"
            f"🏛️ <b>Coinbase Spot:</b> <code>${d['coinbase_price']:,.2f}</code>\n"
            f"🌐 <b>Global Spot:</b> <code>${d['global_price']:,.2f}</code>\n\n"
            f"🧭 <b>Sentimen Aliran Modal AS:</b>\n"
            f"<b>{d['regime']}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💡 <i>Indikator ini mendeteksi apakah pergerakan harga didorong pembelian nyata Wall Street atau sekadar manipulasi leverage ritel.</i>\n"
            f"🕒 <i>{d['updated_at']}</i>"
        )
# Alias for compatibility with external caller conventions
get_coinbase_premium_index = get_coinbase_premium

if __name__ == "__main__":
    for c in ["BTC", "ETH", "SOL"]:
        res = get_coinbase_premium(c)
        print("\n" + "=" * 50)
        print(f"[{c}] CB: ${res['coinbase_price']:,.2f} | Global: ${res['global_price']:,.2f} | Spread: {res['premium_usd']:+.2f} ({res['premium_pct']:+.4f}%)")
        print(f"Status: {res['regime']} (Confluence Bonus: {res['confluence_bonus']:+d})")

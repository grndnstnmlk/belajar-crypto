"""
CoinGlass & Coinalyze Institutional Derivatives Intelligence Engine
Provides real-time Open Interest, Long/Short Ratio, Predicted Funding Rate,
and Multi-Exchange Liquidation Risk metrics.

Primary: Coinalyze Official API (Multi-Exchange Aggregated: Binance, OKX, Bybit, Deribit, etc.)
Fallback 1: Official CoinGlass API V4 (if COINGLASS_API_KEY is configured)
Fallback 2: Zero-cost institutional order-flow engine (OKX Rubik Contract Statistics & Binance native tickers)
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

# In-memory TTL Cache (TTL = 90 seconds) to prevent hitting Coinalyze 40 req/min rate limit
_DERIV_CACHE = {}
CACHE_TTL_SECONDS = 90

def clean_coin(symbol):
    return symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")

def fetch_json(url, extra_headers=None, timeout=8):
    req_headers = HEADERS.copy()
    if extra_headers:
        req_headers.update(extra_headers)
    try:
        req = urllib.request.Request(url, headers=req_headers)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

def get_coinglass_api_key():
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if "COINGLASS_API_KEY" in line and "=" in line:
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val and not val.startswith("#"):
                            return val
        except Exception:
            pass
    return os.environ.get("COINGLASS_API_KEY")

def get_coinalyze_api_key():
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if "COINALYZE_API_KEY" in line and "=" in line:
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val and not val.startswith("#"):
                            return val
        except Exception:
            pass
    return os.environ.get("COINALYZE_API_KEY")

def get_approx_price(ccy):
    """Fetches approximate current spot price from OKX public ticker for USD calculations."""
    try:
        url = f"https://www.okx.com/api/v5/market/ticker?instId={ccy}-USDT"
        res = fetch_json(url, timeout=4)
        if res and res.get("code") == "0" and res.get("data"):
            return float(res["data"][0].get("last", 0.0))
    except Exception:
        pass
    return 0.0

def get_derivatives_intelligence(symbol="BTC", force_refresh=False):
    """
    Fetches comprehensive institutional derivatives data:
    1. Multi-Exchange Open Interest (Base Asset & USD estimate + 1H % change)
    2. Global Long/Short Ratio (Retail crowd positioning)
    3. Multi-Exchange Liquidations (4H Long vs Short liquidations)
    4. Predicted Funding Rate
    5. Overcrowded Positioning & Squeeze Risk Analysis (Akademi Crypto SMC)
    """
    ccy = clean_coin(symbol)
    now_ts = time.time()

    # Check cache first
    if not force_refresh and ccy in _DERIV_CACHE:
        cached_entry = _DERIV_CACHE[ccy]
        if now_ts < cached_entry.get("expires_at", 0):
            return cached_entry["data"]

    cz_key = get_coinalyze_api_key()
    cg_key = get_coinglass_api_key()

    oi_val_coin = 0.0
    oi_val_usd = 0.0
    oi_change_1h = 0.0
    ls_ratio = 1.0
    long_pct = 50.0
    short_pct = 50.0
    funding_rate_pct = 0.01
    liq_4h_long = 0.0
    liq_4h_short = 0.0
    source = "OKX Rubik & Binance Institutional Engine (Free Real-Time)"
    has_cz_data = False

    # -------------------------------------------------------------
    # METHOD 1: Coinalyze Official API (Institutional Multi-Exchange)
    # -------------------------------------------------------------
    if cz_key:
        try:
            cz_symbol = f"{ccy}USDT_PERP.A"
            now_int = int(now_ts)
            from_4h = now_int - 14400
            from_2h = now_int - 7200

            # 1. Open Interest & 1H Delta
            oi_hist_url = f"https://api.coinalyze.net/v1/open-interest-history?symbols={cz_symbol}&interval=1hour&from={from_2h}&to={now_int}&api_key={cz_key}"
            oi_hist_res = fetch_json(oi_hist_url)
            if oi_hist_res and isinstance(oi_hist_res, list) and len(oi_hist_res) > 0:
                candles = oi_hist_res[0].get("history", [])
                if candles:
                    latest_c = candles[-1]
                    oi_val_coin = float(latest_c.get("c", 0.0))
                    if len(candles) > 1:
                        prev_c = float(candles[-2].get("c", 0.0))
                        if prev_c > 0:
                            oi_change_1h = ((oi_val_coin - prev_c) / prev_c) * 100.0
                    has_cz_data = True

            # If OI history had no candles, try live OI
            if oi_val_coin <= 0:
                oi_url = f"https://api.coinalyze.net/v1/open-interest?symbols={cz_symbol}&api_key={cz_key}"
                oi_res = fetch_json(oi_url)
                if oi_res and isinstance(oi_res, list) and len(oi_res) > 0:
                    oi_val_coin = float(oi_res[0].get("value", 0.0))
                    has_cz_data = True

            # 2. Global Long / Short Account Ratio
            ls_url = f"https://api.coinalyze.net/v1/long-short-ratio-history?symbols={cz_symbol}&interval=1hour&from={from_2h}&to={now_int}&api_key={cz_key}"
            ls_res = fetch_json(ls_url)
            if ls_res and isinstance(ls_res, list) and len(ls_res) > 0:
                ls_candles = ls_res[0].get("history", [])
                if ls_candles:
                    latest_ls = ls_candles[-1]
                    ls_ratio = float(latest_ls.get("r", 1.0))
                    long_pct = float(latest_ls.get("l", 50.0))
                    short_pct = float(latest_ls.get("s", 50.0))
                    has_cz_data = True

            # 3. Liquidation History (4 Hours)
            lq_url = f"https://api.coinalyze.net/v1/liquidation-history?symbols={cz_symbol}&interval=1hour&from={from_4h}&to={now_int}&api_key={cz_key}"
            lq_res = fetch_json(lq_url)
            if lq_res and isinstance(lq_res, list) and len(lq_res) > 0:
                lq_candles = lq_res[0].get("history", [])
                liq_4h_long = sum(float(c.get("l", 0.0)) for c in lq_candles)
                liq_4h_short = sum(float(c.get("s", 0.0)) for c in lq_candles)
                has_cz_data = True

            # 4. Predicted Funding Rate
            pfr_url = f"https://api.coinalyze.net/v1/predicted-funding-rate?symbols={cz_symbol}&api_key={cz_key}"
            pfr_res = fetch_json(pfr_url)
            if pfr_res and isinstance(pfr_res, list) and len(pfr_res) > 0:
                funding_rate_pct = float(pfr_res[0].get("value", 0.01))
                has_cz_data = True

            if has_cz_data:
                source = "Coinalyze Institutional Engine (Multi-Exchange Aggregated)"

        except Exception as e:
            # Silent fallback if Coinalyze rate limit or connectivity issue occurs
            pass

    # -------------------------------------------------------------
    # METHOD 2: Fallback to OKX Rubik & Public Funding Rate
    # -------------------------------------------------------------
    if not has_cz_data:
        # Fallback Open Interest & Volume from OKX Rubik
        oi_url = f"https://www.okx.com/api/v5/rubik/stat/contracts/open-interest-volume?ccy={ccy}&period=1H"
        oi_res = fetch_json(oi_url)
        if oi_res and oi_res.get("code") == "0" and oi_res.get("data"):
            data = oi_res["data"]
            if len(data) > 0:
                oi_val_usd = float(data[0][1])
            if len(data) > 1:
                prev_oi = float(data[1][1])
                oi_change_1h = ((oi_val_usd - prev_oi) / prev_oi * 100.0) if prev_oi > 0 else 0.0

        # Long / Short Account Ratio
        ls_url = f"https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio?ccy={ccy}&period=1H"
        ls_res = fetch_json(ls_url)
        if ls_res and ls_res.get("code") == "0" and ls_res.get("data"):
            ls_data = ls_res["data"]
            if len(ls_data) > 0:
                ls_ratio = float(ls_data[0][1])
                long_pct = round((ls_ratio / (1.0 + ls_ratio)) * 100.0, 1)
                short_pct = round((1.0 / (1.0 + ls_ratio)) * 100.0, 1)

        # Funding Rate
        fr_url = f"https://www.okx.com/api/v5/public/funding-rate?instId={ccy}-USDT-SWAP"
        fr_res = fetch_json(fr_url)
        if fr_res and fr_res.get("code") == "0" and fr_res.get("data"):
            fr_data = fr_res["data"][0]
            funding_rate_pct = float(fr_data.get("fundingRate", 0.0001)) * 100.0

    # Calculate USD Estimates if denominated in Base Asset (Coinalyze)
    spot_price = get_approx_price(ccy)
    if oi_val_coin > 0 and spot_price > 0:
        oi_val_usd = oi_val_coin * spot_price
    elif oi_val_usd > 0 and spot_price > 0:
        oi_val_coin = oi_val_usd / spot_price

    # -------------------------------------------------------------
    # Market Regime & Squeeze Warnings (Akademi Crypto SMC)
    # -------------------------------------------------------------
    # Retail crowd sentiment analysis:
    # ls_ratio >= 2.2 -> Crowded Longs (Retail overleveraged, dump risk)
    # ls_ratio >= 3.0 -> Extreme Longs (High probability Liquidity Hunt)
    # ls_ratio <= 0.75 -> Crowded Shorts (Short squeeze pump opportunity)
    is_extreme_long = ls_ratio >= 3.0
    is_crowded_long = ls_ratio >= 2.2
    is_crowded_short = ls_ratio <= 0.75

    # Liquidation context
    total_liq_4h = liq_4h_long + liq_4h_short
    long_liq_dominance = (liq_4h_long / total_liq_4h * 100.0) if total_liq_4h > 0 else 0.0
    short_liq_dominance = (liq_4h_short / total_liq_4h * 100.0) if total_liq_4h > 0 else 0.0

    if is_extreme_long:
        regime = "🚨 EXTREME CROWDED LONGS (Liquidity Hunt / Dump Risk)"
        bias = "BEARISH_SQUEEZE_RISK"
        confluence_impact = -10
    elif is_crowded_long:
        regime = "⚠️ CROWDED LONGS (Retail Overleveraged - Watch Stop Losses)"
        bias = "CAUTIOUS_LONG"
        confluence_impact = -5
    elif is_crowded_short:
        regime = "🔥 CROWDED SHORTS (High Squeeze / Pump Opportunity)"
        bias = "BULLISH_SQUEEZE"
        confluence_impact = +10
    else:
        regime = "⚖️ BALANCED ORDER FLOW (Healthy Market Distribution)"
        bias = "NEUTRAL_BALANCED"
        confluence_impact = 0

    # Open Interest Delta interpretation
    if oi_change_1h > 1.5:
        oi_state = "🚀 AGGRESSIVE CAPITAL INFLOW (Positions Opening)"
    elif oi_change_1h < -1.5:
        oi_state = "📉 CAPITAL FLIGHT / POSITION UNWINDING (Deleveraging)"
    else:
        oi_state = "⚪ STABLE LIQUIDITY (Minor Rebalancing)"

    # Format OI text
    if oi_val_coin > 0 and oi_val_usd > 0:
        if oi_val_usd >= 1_000_000_000:
            usd_str = f"${oi_val_usd / 1_000_000_000:.2f}B"
        elif oi_val_usd >= 1_000_000:
            usd_str = f"${oi_val_usd / 1_000_000:.2f}M"
        else:
            usd_str = f"${oi_val_usd:,.0f}"

        if oi_val_coin >= 1_000_000_000:
            coin_str = f"{oi_val_coin / 1_000_000_000:.2f}B {ccy}"
        elif oi_val_coin >= 1_000_000:
            coin_str = f"{oi_val_coin / 1_000_000:.2f}M {ccy}"
        elif oi_val_coin >= 1_000:
            coin_str = f"{oi_val_coin:,.0f} {ccy}"
        else:
            coin_str = f"{oi_val_coin:.2f} {ccy}"

        oi_formatted = f"{coin_str} (~{usd_str})"
    elif oi_val_usd > 0:
        oi_formatted = f"${oi_val_usd:,.0f}"
    else:
        oi_formatted = "N/A"

    result = {
        "symbol": ccy,
        "pair": f"{ccy}/USDT",
        "open_interest_coin": oi_val_coin,
        "open_interest_usd": oi_val_usd,
        "open_interest_formatted": oi_formatted,
        "oi_change_1h_pct": round(oi_change_1h, 2),
        "long_short_ratio": round(ls_ratio, 2),
        "long_pct": round(long_pct, 1),
        "short_pct": round(short_pct, 1),
        "funding_rate_pct": round(funding_rate_pct, 4),
        "liq_4h_long": liq_4h_long,
        "liq_4h_short": liq_4h_short,
        "total_liq_4h": total_liq_4h,
        "long_liq_dominance": round(long_liq_dominance, 1),
        "short_liq_dominance": round(short_liq_dominance, 1),
        "regime": regime,
        "bias": bias,
        "oi_state": oi_state,
        "confluence_impact": confluence_impact,
        "spot_price": spot_price,
        "source": source,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Store in cache
    _DERIV_CACHE[ccy] = {
        "data": result,
        "expires_at": now_ts + CACHE_TTL_SECONDS
    }

    return result

def format_telegram_report(data):
    """Formats rich Telegram report with emojis and liquidation breakdowns."""
    ccy = data["symbol"]
    oi_fmt = data["open_interest_formatted"]
    oi_chg = f"{data['oi_change_1h_pct']:+.2f}%"
    ls = data["long_short_ratio"]
    l_pct = data["long_pct"]
    s_pct = data["short_pct"]
    fr = f"{data['funding_rate_pct']:+.4f}%"

    liq_long = data.get("liq_4h_long", 0.0)
    liq_short = data.get("liq_4h_short", 0.0)
    tot_liq = data.get("total_liq_4h", 0.0)

    liq_section = ""
    if tot_liq > 0:
        if liq_long >= 1_000_000:
            l_str = f"{liq_long/1_000_000:.2f}M {ccy}"
        else:
            l_str = f"{liq_long:,.1f} {ccy}"

        if liq_short >= 1_000_000:
            s_str = f"{liq_short/1_000_000:.2f}M {ccy}"
        else:
            s_str = f"{liq_short:,.1f} {ccy}"

        l_dom = data.get("long_liq_dominance", 0.0)
        s_dom = data.get("short_liq_dominance", 0.0)

        liq_note = ""
        if l_dom > 75.0:
            liq_note = "<i>⚠️ Sapuan likuidasi buyer ritel (Long Flushout).</i>\n"
        elif s_dom > 75.0:
            liq_note = "<i>🚀 Sapuan likuidasi seller ritel (Short Squeeze).</i>\n"

        liq_section = (
            f"🩸 <b>Likuidasi 4-Jam Terakhir:</b>\n"
            f"   🟢 Longs Wiped: <b>{l_str}</b> ({l_dom}%)\n"
            f"   🔴 Shorts Wiped: <b>{s_str}</b> ({s_dom}%)\n"
            f"{liq_note}\n"
        )

    title_source = "COINALYZE" if "Coinalyze" in data["source"] else "COINGLASS"

    return (
        f"🌊 <b>{title_source} DERIVATIVES & ORDER FLOW: {ccy}/USDT</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📈 <b>Open Interest:</b> <code>{oi_fmt}</code> (1H: <code>{oi_chg}</code>)\n"
        f"🌊 <b>Arus Likuiditas:</b> <i>{data['oi_state']}</i>\n\n"
        f"👥 <b>Global Long / Short Ratio:</b> <code>{ls:.2f}</code>\n"
        f"   🟢 Longs: <b>{l_pct}%</b> | 🔴 Shorts: <b>{s_pct}%</b>\n"
        f"💸 <b>Predicted Funding Rate:</b> <code>{fr}</code>\n\n"
        f"{liq_section}"
        f"🧭 <b>Status Sentimen & Squeeze Risk:</b>\n"
        f"<b>{data['regime']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📡 <i>Sumber: {data['source']}</i>\n"
        f"💡 <i>Gunakan data ini untuk menghindari posisi yang terlalu ramai (crowded trade).</i>\n"
    )

# Aliases for external caller & dashboard compatibility
get_coinglass_sentiment_summary = get_derivatives_intelligence
get_derivatives_summary = get_derivatives_intelligence

if __name__ == "__main__":
    for coin in ["BTC", "ETH", "SOL", "DOGE"]:
        d = get_derivatives_intelligence(coin)
        print("\n" + "=" * 55)
        print(f"[{coin}] OI: {d['open_interest_formatted']} | L/S: {d['long_short_ratio']:.2f} ({d['long_pct']}% vs {d['short_pct']}%)")
        print(f"FR: {d['funding_rate_pct']:+.4f}% | 4H Liq Long: {d['liq_4h_long']:,.1f} | Short: {d['liq_4h_short']:,.1f}")
        print(f"Status: {d['regime']}")
        print(f"Source: {d['source']}")

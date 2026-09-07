"""
Global Macro Liquidity & Sentiment Engine (Fincept Terminal Inspired)
Fetches real-time macroeconomic indicators without external API keys:
1. US Dollar Index (DXY) - Global Risk-Off Benchmark
2. US 10-Year Treasury Yield (^TNX) - Global Cost of Capital
3. Crypto Fear & Greed Index - Market Sentiment & Psychology
4. Macro Regime Classifier (RISK_ON, RISK_OFF, NEUTRAL)
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

_MACRO_CACHE = {}
CACHE_TTL_SECONDS = 180  # 3 minutes cache to minimize network roundtrips

def fetch_json(url, timeout=6):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
            data = resp.read()
            if not data:
                return None
            return json.loads(data.decode("utf-8"))
    except Exception:
        return None

def fetch_dxy_index():
    """
    Fetches real-time US Dollar Index (DXY) from Yahoo Finance public API.
    Ticker: DX-Y.NYB
    """
    url = "https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB?interval=1d&range=5d"
    res = fetch_json(url)
    if not res:
        return None

    try:
        result = res.get("chart", {}).get("result", [])[0]
        meta = result.get("meta", {})
        price = float(meta.get("regularMarketPrice", 0.0))
        prev_close = float(meta.get("chartPreviousClose", meta.get("previousClose", price)))
        chg_pct = ((price - prev_close) / prev_close * 100.0) if prev_close > 0 else 0.0

        return {
            "price": round(price, 3),
            "prev_close": round(prev_close, 3),
            "change_pct": round(chg_pct, 2),
            "state": "SURGING (Risk-Off)" if chg_pct > 0.25 else ("PLUNGING (Risk-On)" if chg_pct < -0.25 else "STABLE")
        }
    except Exception:
        return None

def fetch_us10y_yield():
    """
    Fetches real-time US 10-Year Treasury Yield (^TNX) from Yahoo Finance public API.
    """
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ETNX?interval=1d&range=5d"
    res = fetch_json(url)
    if not res:
        return None

    try:
        result = res.get("chart", {}).get("result", [])[0]
        meta = result.get("meta", {})
        rate = float(meta.get("regularMarketPrice", 0.0))
        prev_close = float(meta.get("chartPreviousClose", meta.get("previousClose", rate)))
        chg_pct = ((rate - prev_close) / prev_close * 100.0) if prev_close > 0 else 0.0

        return {
            "yield_pct": round(rate, 3),
            "prev_close": round(prev_close, 3),
            "change_pct": round(chg_pct, 2),
            "state": "SPIKING (Liquidity Tightening)" if chg_pct > 0.8 else ("COOLING (Liquidity Easing)" if chg_pct < -0.8 else "STEADY")
        }
    except Exception:
        return None

def fetch_fear_and_greed_index():
    """
    Fetches latest Crypto Fear & Greed Index from Alternative.me.
    """
    url = "https://api.alternative.me/fng/?limit=1"
    res = fetch_json(url)
    if not res:
        return None

    try:
        data = res.get("data", [])[0]
        score = int(data.get("value", 50))
        classification = data.get("value_classification", "Neutral")
        return {
            "score": score,
            "classification": classification
        }
    except Exception:
        return None

def get_macro_liquidity_summary(force_refresh=False):
    """
    Synthesizes all macro indicators into an institutional regime compass.
    """
    now_ts = time.time()
    if not force_refresh and "data" in _MACRO_CACHE:
        if now_ts - _MACRO_CACHE.get("ts", 0) < CACHE_TTL_SECONDS:
            return _MACRO_CACHE["data"]

    dxy = fetch_dxy_index()
    us10y = fetch_us10y_yield()
    fng = fetch_fear_and_greed_index()

    # Macro Regime Classifier
    regime = "NEUTRAL_EXPANSION"
    regime_label = "🟡 NEUTRAL / CONSOLIDATION"
    bias_detail = "Macro signals are balanced."

    dxy_chg = dxy.get("change_pct", 0.0) if dxy else 0.0
    us10y_chg = us10y.get("change_pct", 0.0) if us10y else 0.0
    fng_score = fng.get("score", 50) if fng else 50

    if dxy_chg <= -0.15 and us10y_chg <= 0.2:
        regime = "RISK_ON"
        regime_label = "🟢 GLOBAL RISK-ON (Dollar Weakness)"
        bias_detail = "DXY falling, capital flowing into risk assets & crypto."
    elif dxy_chg >= 0.20 or us10y_chg >= 1.5:
        regime = "RISK_OFF"
        regime_label = "🔴 GLOBAL RISK-OFF (Dollar Surging)"
        bias_detail = "DXY or Treasury yields spiking. Defensive positioning advised."
    elif fng_score <= 25:
        regime = "EXTREME_FEAR_ACCUMULATION"
        regime_label = "🛡️ EXTREME FEAR (Smart Money Value Zone)"
        bias_detail = "Market sentiment depressed. Look for reversal liquidity sweeps."
    elif fng_score >= 75:
        regime = "EUPHORIA_OVERBOUGHT"
        regime_label = "⚠️ GREED / OVERLEVERAGED (Watch for Flush)"
        bias_detail = "Excessive retail greed. Watch out for liquidation long flushes."

    result = {
        "dxy": dxy or {"price": 100.0, "change_pct": 0.0, "state": "UNKNOWN"},
        "us10y": us10y or {"yield_pct": 4.25, "change_pct": 0.0, "state": "UNKNOWN"},
        "fear_and_greed": fng or {"score": 50, "classification": "Neutral"},
        "macro_regime": regime,
        "macro_label": regime_label,
        "bias_detail": bias_detail,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    _MACRO_CACHE["data"] = result
    _MACRO_CACHE["ts"] = now_ts
    return result

def main():
    print("\n=======================================================")
    print("      🌐 GLOBAL MACRO LIQUIDITY ENGINE (FINCEPT SUITE)")
    print("=======================================================")

    m = get_macro_liquidity_summary(force_refresh=True)
    dxy = m["dxy"]
    us10y = m["us10y"]
    fng = m["fear_and_greed"]

    print(f"US Dollar Index (DXY): {dxy.get('price')} ({dxy.get('change_pct'):+,.2f}%) [{dxy.get('state')}]")
    print(f"US 10Y Yield (^TNX)  : {us10y.get('yield_pct')}% ({us10y.get('change_pct'):+,.2f}%) [{us10y.get('state')}]")
    print(f"Fear & Greed Index   : {fng.get('score')} / 100 [{fng.get('classification')}]")
    print("-------------------------------------------------------")
    print(f"Macro Regime         : {m.get('macro_label')}")
    print(f"Institutional Bias   : {m.get('bias_detail')}")
    print("=======================================================\n")

if __name__ == "__main__":
    main()

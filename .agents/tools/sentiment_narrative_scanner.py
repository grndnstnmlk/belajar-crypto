"""
Sentiment & Social Narrative Scanner
Inspired by Tauric Research's TradingAgents Analyst Architecture (arXiv:2412.20138)
and Akademi Crypto Module 01 (Macro Sentiment, Capital Rotation & Narrative Trading).

Components:
1. Crypto Fear & Greed Index Engine : Real-time score (0-100), 7-day trend, and contrarian signal.
2. Narrative Sector Rotation Radar  : Tracks 6 key sectors (AI/DePIN, Solana/L1, RWA/DeFi, Meme, L2, Macro)
                                      via 24h performance and volume from Binance Vision.
3. Social Virality & Search Buzz    : Extracts trending search tokens from CoinGecko.
4. Cognitive Catalyst Classifier     : Dual-Engine (Cognitive LLM + Quant NLP Lexicon < 5ms) for news & catalysts.
"""

import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

# Windows UTF-8 stdout configuration
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
SENTIMENT_DATA_FILE = os.path.join(DATA_DIR, "sentiment_narrative.json")

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# Institutional Narrative Sector Taxonomy
NARRATIVE_SECTORS = {
    "AI_DEPIN": {
        "title": "AI & DePIN",
        "icon": "🤖",
        "tokens": ["FET", "NEAR", "RENDER", "TAO", "ICP", "AR"],
        "description": "Artificial Intelligence, Decentralized Compute & Physical Infra"
    },
    "SOL_L1": {
        "title": "Solana & High-Speed L1",
        "icon": "⚡",
        "tokens": ["SOL", "AVAX", "SUI", "APT", "SEI"],
        "description": "High-Throughput Alternative Layer 1 Ecosystems"
    },
    "RWA_DEFI": {
        "title": "RWA & Institutional DeFi",
        "icon": "🏛️",
        "tokens": ["ONDO", "MKR", "AAVE", "LINK", "PENDLE"],
        "description": "Real-World Assets, Tokenized Treasury & Lending Yield"
    },
    "MEME_BETA": {
        "title": "Meme & Cultural Tokens",
        "icon": "🐶",
        "tokens": ["DOGE", "SHIB", "PEPE", "WIF", "FLOKI", "BONK"],
        "description": "High-Beta Retail Speculation & Virality Liquidity"
    },
    "L2_MODULAR": {
        "title": "L2 & Modular Rollups",
        "icon": "⛓️",
        "tokens": ["ARB", "OP", "TIA", "STRK", "MATIC"],
        "description": "Ethereum Scaling, Data Availability & Modular Chains"
    },
    "MACRO_BLUECHIP": {
        "title": "Macro Heavyweights",
        "icon": "👑",
        "tokens": ["BTC", "ETH", "BNB"],
        "description": "Store of Value, Settlement Layer & Platform Dominance"
    }
}

# In-memory TTL Cache (TTL = 60s)
_CACHE = {
    "summary": None,
    "timestamp": 0
}
CACHE_TTL = 60

def fetch_json(url, timeout=6):
    """Safely fetches JSON from an external public endpoint with timeout and SSL bypass."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

def get_fear_and_greed_index():
    """
    Fetches official Crypto Fear & Greed Index from Alternative.me.
    Returns current score, sentiment category, 7-day trend, and contrarian interpretation.
    """
    url = "https://api.alternative.me/fng/?limit=7"
    data = fetch_json(url, timeout=5)

    if data and "data" in data and len(data["data"]) > 0:
        latest = data["data"][0]
        val = int(latest.get("value", 50))
        classification = latest.get("value_classification", "Neutral")
        
        history_7d = []
        for d in data["data"]:
            history_7d.append({
                "value": int(d.get("value", 50)),
                "classification": d.get("value_classification", "Neutral"),
                "timestamp": d.get("timestamp")
            })

        # Contrarian institutional interpretation (Akademi Crypto & Tauric TradingAgents)
        if val >= 75:
            contrarian_signal = "EXTREME_GREED_WARNING"
            contrarian_note = "Retail euforia ekstrem. Waspada liquidity sweep / long squeeze. Perketat trailing stop dan kunci profit bertahap."
        elif val >= 56:
            contrarian_signal = "GREED_EXPANSION"
            contrarian_note = "Sentimen pasar ekspansif dan positif. Tren momentum sehat mendukung setup continuation."
        elif val <= 25:
            contrarian_signal = "EXTREME_FEAR_ACCUMULATION"
            contrarian_note = "Kepanikan ritel maksimal. Zona akumulasi institusional prima (Wyckoff Spring & FVG buy retests)."
        elif val <= 44:
            contrarian_signal = "FEAR_DEFENSIVE"
            contrarian_note = "Pasar cenderung defensif. Pilih setup dengan konfluensi tinggi dan hindari breakout spekulatif."
        else:
            contrarian_signal = "NEUTRAL_EQUILIBRIUM"
            contrarian_note = "Pasar berada di titik ekuilibrium netral. Reaksi teknikal dominan."

        return {
            "score": val,
            "classification": classification,
            "contrarian_signal": contrarian_signal,
            "contrarian_note": contrarian_note,
            "history_7d": history_7d,
            "source": "Alternative.me F&G"
        }

    # Resilient offline fallback
    return {
        "score": 65,
        "classification": "Greed",
        "contrarian_signal": "GREED_EXPANSION",
        "contrarian_note": "Sentimen pasar ekspansif dan positif. Tren momentum sehat mendukung setup continuation.",
        "history_7d": [{"value": 65, "classification": "Greed"}],
        "source": "Heuristic Default"
    }

def get_narrative_sector_rotation():
    """
    Evaluates institutional capital rotation across 6 narrative sectors using Binance Vision 24hr tickers.
    Calculates average return, total volume, and ranks leading sectors.
    """
    url = "https://data-api.binance.vision/api/v3/ticker/24hr"
    raw_tickers = fetch_json(url, timeout=7)
    
    ticker_map = {}
    if raw_tickers and isinstance(raw_tickers, list):
        for t in raw_tickers:
            sym = t.get("symbol", "")
            if sym.endswith("USDT"):
                try:
                    ticker_map[sym] = {
                        "change_pct": float(t.get("priceChangePercent", 0.0)),
                        "volume_usd": float(t.get("quoteVolume", 0.0)),
                        "last_price": float(t.get("lastPrice", 0.0))
                    }
                except Exception:
                    pass

    btc_perf = ticker_map.get("BTCUSDT", {}).get("change_pct", 0.0)

    sector_results = []
    for sec_key, sec_info in NARRATIVE_SECTORS.items():
        tokens = sec_info["tokens"]
        changes = []
        volumes = []
        token_breakdowns = []

        for tk in tokens:
            pair = f"{tk}USDT"
            if pair in ticker_map:
                t_data = ticker_map[pair]
                changes.append(t_data["change_pct"])
                volumes.append(t_data["volume_usd"])
                token_breakdowns.append({
                    "symbol": tk,
                    "change_pct": round(t_data["change_pct"], 2),
                    "volume_usd": round(t_data["volume_usd"], 2)
                })
            else:
                # Default minimal sample if ticker omitted
                changes.append(0.0)
                volumes.append(1000000.0)
                token_breakdowns.append({"symbol": tk, "change_pct": 0.0, "volume_usd": 1000000.0})

        avg_change = sum(changes) / len(changes) if changes else 0.0
        tot_vol = sum(volumes)
        beta_vs_btc = avg_change - btc_perf

        sector_results.append({
            "key": sec_key,
            "title": sec_info["title"],
            "icon": sec_info["icon"],
            "description": sec_info["description"],
            "avg_change_24h": round(avg_change, 2),
            "total_volume_usd": round(tot_vol, 2),
            "relative_strength_vs_btc": round(beta_vs_btc, 2),
            "tokens": token_breakdowns
        })

    # Sort sectors by 24h performance descending
    sector_results.sort(key=lambda x: x["avg_change_24h"], reverse=True)

    leading_sector = sector_results[0] if sector_results else None
    laggard_sector = sector_results[-1] if sector_results else None

    rotation_thesis = (
        f"Rotasi modal hari ini dipimpin oleh sektor {leading_sector['icon']} {leading_sector['title']} "
        f"({leading_sector['avg_change_24h']:+.2f}%), mengungguli BTC sebesar {leading_sector['relative_strength_vs_btc']:+.2f}%. "
        f"Sektor terlemah: {laggard_sector['icon']} {laggard_sector['title']} ({laggard_sector['avg_change_24h']:+.2f}%)."
    )

    return {
        "sectors": sector_results,
        "leading_sector": leading_sector,
        "laggard_sector": laggard_sector,
        "btc_24h_change": round(btc_perf, 2),
        "rotation_thesis": rotation_thesis
    }

def get_social_virality_trending():
    """
    Fetches global trending search tokens from CoinGecko public search API.
    Detects retail hype velocity and matching tokens in the platform's watchlist.
    """
    url = "https://api.coingecko.com/api/v3/search/trending"
    data = fetch_json(url, timeout=5)
    
    trending_tokens = []
    if data and "coins" in data:
        for c in data.get("coins", [])[:7]:
            item = c.get("item", {})
            trending_tokens.append({
                "symbol": item.get("symbol", "").upper(),
                "name": item.get("name", ""),
                "market_cap_rank": item.get("market_cap_rank"),
                "score": item.get("score", 0), # 0 = most searched
                "thumb": item.get("thumb", "")
            })

    # Determine Virality Stage
    stage = "ORGANIC_EXPANSION"
    stage_note = "Pencarian komunitas sehat dan tersebar merata antar sektor."
    if len(trending_tokens) > 0:
        meme_count = len([t for t in trending_tokens if t["symbol"] in ["PEPE", "DOGE", "SHIB", "WIF", "BONK", "FLOKI"]])
        if meme_count >= 3:
            stage = "RETAIL_EUPHORIC_CLIMAX"
            stage_note = "Retail FOMO mendominasi trending search. Waspada volatilitas tajam dan fakeout wick."

    return {
        "trending_tokens": trending_tokens,
        "virality_stage": stage,
        "stage_note": stage_note,
        "source": "CoinGecko Trending"
    }

def classify_catalyst_sentiment(news_text=None):
    """
    Dual-Engine Catalyst Sentiment Classifier:
    1. Cognitive LLM (Gemini / OpenAI / DeepSeek / Groq) when configured.
    2. Deterministic Quant NLP Lexicon (< 5ms) offline fallback.
    """
    # 1. Cognitive LLM
    try:
        import ai_risk_officer
        creds = ai_risk_officer.get_ai_credentials()
        if creds.get("key") and creds.get("provider") != "fallback_quant" and news_text:
            prompt = f"""
Analyze the following crypto market narrative/news event:
"{news_text}"

Determine:
1. Sentiment: BULLISH, BEARISH, or NEUTRAL
2. Impact Score: 0 to 100 (where 100 is market-moving structural catalyst like ETF approval)
3. Concise Executive Note (in Indonesian)

Output strictly valid JSON:
{{
  "sentiment": "<BULLISH|BEARISH|NEUTRAL>",
  "impact_score": <int>,
  "catalyst_category": "<MACRO_REGULATORY|ETN_FLOWS|PROTOCOL_UPGRADE|EXPLOIT_SECURITY|COMMUNITY_SPECULATION>",
  "executive_note": "<Indonesian note>"
}}
"""
            raw = ai_risk_officer.call_llm(prompt, response_json=True)
            if raw:
                parsed = json.loads(raw)
                parsed["engine"] = f"Cognitive LLM ({creds.get('provider').upper()})"
                return parsed
    except Exception:
        pass

    # 2. Deterministic Quant NLP Lexicon (< 5ms) Fallback
    text_lower = (news_text or "").lower()
    bullish_keywords = ["etf", "approved", "inflow", "partnership", "halving", "burn", "upgrade", "accumulation", "treasury", "cut rates"]
    bearish_keywords = ["hack", "exploit", "sec", "subpoena", "lawsuit", "outflow", "dump", "delist", "insolvency", "hike rates", "freeze"]

    bull_hits = sum(1 for kw in bullish_keywords if kw in text_lower)
    bear_hits = sum(1 for kw in bearish_keywords if kw in text_lower)

    if bull_hits > bear_hits:
        sentiment = "BULLISH"
        impact = min(90, 50 + (bull_hits * 15))
        note = f"Katalis positif teridentifikasi ({bull_hits} kata kunci bullish). Mendukung dorongan tren ke atas."
        cat = "PROTOCOL_OR_MACRO_TAILWIND"
    elif bear_hits > bull_hits:
        sentiment = "BEARISH"
        impact = min(95, 55 + (bear_hits * 20))
        note = f"Peringatan risiko: Sentimen berita negatif ({bear_hits} kata kunci bearish). Waspada tekanan jual."
        cat = "REGULATORY_OR_SECURITY_HAZARD"
    else:
        sentiment = "NEUTRAL"
        impact = 45
        note = "Sentimen berita berimbang. Pasar dipandu oleh struktur teknikal dan likuiditas bursa."
        cat = "BALANCED_FLOW"

    return {
        "sentiment": sentiment,
        "impact_score": impact,
        "catalyst_category": cat,
        "executive_note": note,
        "engine": "Deterministic Quant Lexicon Matrix"
    }

def get_market_sentiment_narrative_summary(force_refresh=False):
    """
    Master Aggregator:
    Synthesizes Fear & Greed, Narrative Sector Rotation, Social Virality, and Catalyst Sentiment.
    Caches in memory (60s TTL) and persists snapshot to disk.
    """
    global _CACHE
    now = time.time()

    if not force_refresh and _CACHE["summary"] and (now - _CACHE["timestamp"] < CACHE_TTL):
        return _CACHE["summary"]

    # Gather data across engines
    fng = get_fear_and_greed_index()
    sectors = get_narrative_sector_rotation()
    virality = get_social_virality_trending()
    
    # Synthesize leading sector context for catalyst
    lead_sec = sectors.get("leading_sector", {})
    lead_title = lead_sec.get("title", "AI & DePIN") if lead_sec else "Crypto Market"
    sample_catalyst_text = f"{lead_title} tokens lead trading volume with strong institutional participation and expanding market breadth."
    catalyst = classify_catalyst_sentiment(sample_catalyst_text)

    # Master Institutional Sentiment Score (-100 to +100)
    # Weights: 40% Fear & Greed, 40% Narrative Breadth, 20% Catalyst
    fng_normalized = (fng["score"] - 50) * 2 # -100 to +100
    narrative_breadth = max(-100, min(100, (sectors.get("btc_24h_change", 0.0) + (lead_sec.get("avg_change_24h", 0.0) if lead_sec else 0.0)) * 10))
    cat_factor = 30 if catalyst["sentiment"] == "BULLISH" else (-30 if catalyst["sentiment"] == "BEARISH" else 0)

    composite_sentiment_score = int(0.40 * fng_normalized + 0.40 * narrative_breadth + 0.20 * cat_factor)
    composite_sentiment_score = max(-100, min(100, composite_sentiment_score))

    summary = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "composite_sentiment_score": composite_sentiment_score,
        "market_posture": "BULLISH_EXPANSION" if composite_sentiment_score >= 30 else ("BEARISH_CONTRACTION" if composite_sentiment_score <= -30 else "NEUTRAL_CONSOLIDATION"),
        "fear_and_greed": fng,
        "narrative_rotation": sectors,
        "social_virality": virality,
        "catalyst_intelligence": catalyst
    }

    # Save to disk
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(SENTIMENT_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    _CACHE["summary"] = summary
    _CACHE["timestamp"] = now
    return summary

def get_token_narrative_info(symbol):
    """
    Identifies which narrative sector a specific token belongs to,
    and returns its sector ranking and momentum context.
    """
    clean_sym = symbol.upper().replace("USDT", "").replace("-", "").replace("/", "")
    summary = get_market_sentiment_narrative_summary()
    sectors = summary.get("narrative_rotation", {}).get("sectors", [])

    for rank, sec in enumerate(sectors, start=1):
        for tk in sec.get("tokens", []):
            if tk["symbol"] == clean_sym:
                is_leader = (rank == 1)
                return {
                    "symbol": clean_sym,
                    "sector_key": sec["key"],
                    "sector_title": sec["title"],
                    "sector_icon": sec["icon"],
                    "sector_rank": rank,
                    "is_leading_sector": is_leader,
                    "sector_24h_avg": sec["avg_change_24h"],
                    "relative_strength_vs_btc": sec["relative_strength_vs_btc"],
                    "confluence_boost": 15 if is_leader else (5 if rank <= 3 else -5)
                }

    return {
        "symbol": clean_sym,
        "sector_key": "OTHER",
        "sector_title": "Independent Asset",
        "sector_icon": "🪙",
        "sector_rank": 99,
        "is_leading_sector": False,
        "sector_24h_avg": 0.0,
        "relative_strength_vs_btc": 0.0,
        "confluence_boost": 0
    }

if __name__ == "__main__":
    print("Scanning Live Crypto Sentiment & Narrative Rotation...")
    res = get_market_sentiment_narrative_summary(force_refresh=True)
    print(f"Fear & Greed : {res['fear_and_greed']['score']} [{res['fear_and_greed']['classification']}]")
    print(f"Leader Sector: {res['narrative_rotation']['leading_sector']['icon']} {res['narrative_rotation']['leading_sector']['title']} ({res['narrative_rotation']['leading_sector']['avg_change_24h']:+.2f}%)")
    print(f"BTC 24h Chg  : {res['narrative_rotation']['btc_24h_change']:+.2f}%")
    print(f"Postural Bias: {res['market_posture']} (Composite Score: {res['composite_sentiment_score']})")
    print("\nToken Context Demo (SOL):")
    print(json.dumps(get_token_narrative_info("SOL"), indent=2))

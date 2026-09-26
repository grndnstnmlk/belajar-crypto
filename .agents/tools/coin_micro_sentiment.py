"""
coin_micro_sentiment.py - Institutional Per-Coin Micro Fear & Greed & Pump Pulse Tape Engine
Synthesized from CoinGecko-JEV Architecture (app/fng and app/pulse) and Akademi Crypto Market Microstructure.

Zero Paid API Cost:
Leverages Binance Vision / Binance Futures / OKX live feeds, WebSocket memory cache,
Level-2 order book depth, and aggTrades Cumulative Volume Delta (CVD) to provide:

1. Per-Coin Micro Fear & Greed Index (0-100):
   - Granular asset-level sentiment isolating individual coin euphoria/panic from aggregate market noise.
   - 4-Pillar Model: Momentum (25%), RSI-14 (25%), Order Book & CVD Delta (25%), 24h Range Position (25%).
   - Macro-Micro Divergence Signal (e.g. Asset Accumulation during Broad Market Fear).

2. Pump Pulse Tape Classifier:
   - Sub-second Level-2 order book tick reader measuring Pump Pressure vs Dump Pressure.
   - Classifies micro-tape dynamics: PUMP_IGNITION, BUY_ABSORPTION, DUMP_CASCADE, SELL_EXHAUSTION, BALANCED_CHOP.
   - Evaluates Smart Money Flow: ACCUMULATING, DISTRIBUTING, or NEUTRAL_ROTATION.
"""

import json
import math
import os
import sys
import time
from typing import Dict, Any, List, Optional, Tuple

# Windows UTF-8 stdout configuration
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# In-memory short-term TTL caches to ensure ultra-fast sub-millisecond responses
_FNG_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_PULSE_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
CACHE_TTL_FNG = 10.0   # 10s for coin sentiment
CACHE_TTL_PULSE = 2.0  # 2s for pump pulse tape

def _clamp(val: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    return max(min_val, min(max_val, val))

def get_coin_micro_fear_greed(symbol: str = "BTC") -> Dict[str, Any]:
    """
    Computes a granular, asset-specific Micro Fear & Greed Index (0 to 100)
    for an individual cryptocurrency without requiring a paid CoinGecko Analyst subscription.
    
    Includes Macro-Micro Divergence against broad market sentiment (Alternative.me).
    """
    global _FNG_CACHE
    base = symbol.upper().replace("-USDT", "").replace("USDT", "").replace("-", "").replace("/", "")
    pair = f"{base}USDT"
    now = time.time()

    if pair in _FNG_CACHE:
        ts, data = _FNG_CACHE[pair]
        if (now - ts) < CACHE_TTL_FNG:
            return data

    import market_eyes
    import orderbook_delta_sniper

    # 1. Fetch Ticker Data (Price, 24h change, 24h High/Low)
    ticker = market_eyes.fetch_ticker_data(base)
    if not ticker or ticker.get("price", 0) <= 0:
        # Fallback safe payload
        return {
            "symbol": pair,
            "score": 50,
            "classification": "NEUTRAL",
            "momentum_score": 50.0,
            "rsi_score": 50.0,
            "orderbook_cvd_score": 50.0,
            "range_score": 50.0,
            "divergence": {
                "macro_score": 50,
                "delta": 0,
                "verdict": "ALIGNED"
            },
            "status": "FALLBACK"
        }

    price = float(ticker.get("price", 0.0))
    chg_24h = float(ticker.get("change_pct", 0.0))
    high_24h = float(ticker.get("high_24h", price * 1.01))
    low_24h = float(ticker.get("low_24h", price * 0.99))

    # Pillar 1: Momentum Score (0-100)
    # 0% change = 50 pts; +10% = 85 pts; -10% = 15 pts
    momentum_score = _clamp(50.0 + (chg_24h * 3.5))

    # Pillar 2: RSI Oscillator Score (0-100)
    # Fetch 1H candles to compute 14-period RSI
    rsi_score = 50.0
    try:
        candles = market_eyes.fetch_candles(base, bar="1H", limit=30)
        if candles and len(candles) >= 15:
            closes = [c[4] for c in candles]
            calc_rsi = market_eyes.calculate_rsi(closes, period=14)
            if calc_rsi is not None:
                rsi_score = _clamp(calc_rsi)
    except Exception:
        rsi_score = 50.0

    # Pillar 3: Order Book Depth & CVD Delta Score (0-100)
    orderbook_cvd_score = 50.0
    try:
        sniper_data = orderbook_delta_sniper.analyze_orderbook_and_delta(pair)
        oir = float(sniper_data.get("order_imbalance_ratio", 0.0))  # -1.0 to +1.0
        cvd_pct = float(sniper_data.get("cvd_delta_pct", 0.0))      # -100 to +100
        
        oir_score = _clamp((oir + 1.0) * 50.0)
        cvd_score = _clamp((cvd_pct + 100.0) / 2.0)
        orderbook_cvd_score = _clamp((oir_score * 0.5) + (cvd_score * 0.5))
    except Exception:
        orderbook_cvd_score = 50.0

    # Pillar 4: 24h High/Low Price Range Position (0-100)
    # Measures whether price is pressing local highs or dragging near local lows
    range_span = high_24h - low_24h
    if range_span > 0:
        range_score = _clamp(((price - low_24h) / range_span) * 100.0)
    else:
        range_score = 50.0

    # Composite Micro Fear & Greed Score (Weighted Equal 25% each)
    composite = (0.25 * momentum_score) + (0.25 * rsi_score) + (0.25 * orderbook_cvd_score) + (0.25 * range_score)
    final_score = int(round(_clamp(composite)))

    # Classification
    if final_score >= 76:
        classification = "EXTREME_GREED"
        tone = "Euphoria / Overbought"
    elif final_score >= 56:
        classification = "GREED"
        tone = "Bullish Expansion"
    elif final_score >= 45:
        classification = "NEUTRAL"
        tone = "Equilibrium / Consolidation"
    elif final_score >= 25:
        classification = "FEAR"
        tone = "Bearish Contraction"
    else:
        classification = "EXTREME_FEAR"
        tone = "Capitulation / Oversold"

    # Macro Divergence Calculation
    macro_score = 50
    try:
        import sentiment_narrative_scanner
        macro_fng = sentiment_narrative_scanner.get_fear_and_greed_index()
        if macro_fng and "score" in macro_fng:
            macro_score = int(macro_fng["score"])
    except Exception:
        macro_score = 50

    delta = final_score - macro_score
    if delta >= 18:
        divergence_verdict = "BULLISH_RELATIVE_STRENGTH_DIVERGENCE"
        divergence_note = f"{base} menunjukkan akumulasi & kekuatan relatif institusional (+{delta} poin di atas sentimen makro crypto)."
    elif delta <= -18:
        divergence_verdict = "BEARISH_LAGGING_DIVERGENCE"
        divergence_note = f"{base} tertinggal di bawah pasar ({delta} poin dari makro), mengindikasikan tekanan distribusi lokal."
    else:
        divergence_verdict = "ALIGNED_WITH_MACRO"
        divergence_note = f"Sentimen {base} selaras dengan dinamika sentimen makro pasar crypto umum."

    result = {
        "symbol": pair,
        "base_asset": base,
        "score": final_score,
        "classification": classification,
        "tone": tone,
        "pillars": {
            "momentum_score": round(momentum_score, 1),
            "rsi_score": round(rsi_score, 1),
            "orderbook_cvd_score": round(orderbook_cvd_score, 1),
            "range_score": round(range_score, 1)
        },
        "market_metrics": {
            "price": price,
            "change_24h_pct": chg_24h,
            "high_24h": high_24h,
            "low_24h": low_24h
        },
        "divergence": {
            "macro_score": macro_score,
            "delta": delta,
            "verdict": divergence_verdict,
            "note": divergence_note
        },
        "timestamp": now,
        "status": "LIVE"
    }

    _FNG_CACHE[pair] = (now, result)
    return result

def get_pump_pulse_score(symbol: str = "BTC") -> Dict[str, Any]:
    """
    Sub-second Level-2 tape reader measuring real-time Pump Pressure vs Dump Pressure.
    Classifies immediate tape dynamics:
    - PUMP_IGNITION: Aggressive buy aggression + bid replenishment + positive delta.
    - BUY_ABSORPTION: Heavy market sells hitting passive limit bid walls without breakdown.
    - DUMP_CASCADE: Aggressive sell panic breaking down bids.
    - SELL_EXHAUSTION: Seller flow drying up with bids thickening.
    - BALANCED_CHOP: Range-bound microstructure equilibrium.
    """
    global _PULSE_CACHE
    base = symbol.upper().replace("-USDT", "").replace("USDT", "").replace("-", "").replace("/", "")
    pair = f"{base}USDT"
    now = time.time()

    if pair in _PULSE_CACHE:
        ts, data = _PULSE_CACHE[pair]
        if (now - ts) < CACHE_TTL_PULSE:
            return data

    import orderbook_delta_sniper

    # 1. Fetch Order Book Depth (Top 20)
    depth = orderbook_delta_sniper.fetch_orderbook_depth(pair, limit=20)
    bids = depth.get("bids", [])
    asks = depth.get("asks", [])

    if not bids or not asks:
        return {
            "symbol": pair,
            "pump_pressure": 50,
            "dump_pressure": 50,
            "pulse_verdict": "BALANCED_CHOP",
            "smart_money_flow": "NEUTRAL_ROTATION",
            "status": "FALLBACK"
        }

    bid_vol_usd = sum(p * q for p, q in bids[:20])
    ask_vol_usd = sum(p * q for p, q in asks[:20])
    total_depth = bid_vol_usd + ask_vol_usd

    oir = (bid_vol_usd - ask_vol_usd) / total_depth if total_depth > 0 else 0.0
    bid_ask_ratio = (bid_vol_usd / ask_vol_usd) if ask_vol_usd > 0 else 1.0

    # 2. Fetch Recent Aggressive Taker Trades
    trades = orderbook_delta_sniper.fetch_recent_agg_trades(pair, limit=80)
    buy_taker_vol = 0.0
    sell_taker_vol = 0.0

    for t in trades:
        qty = float(t.get("qty", 0.0))
        if t.get("is_buyer_maker", False):
            sell_taker_vol += qty
        else:
            buy_taker_vol += qty

    total_taker = buy_taker_vol + sell_taker_vol
    taker_buy_pct = (buy_taker_vol / total_taker * 100.0) if total_taker > 0 else 50.0
    taker_sell_pct = (sell_taker_vol / total_taker * 100.0) if total_taker > 0 else 50.0
    cvd_delta_pct = taker_buy_pct - taker_sell_pct

    # 3. Calculate Pump Pressure (0 - 100)
    # Factors: Order book bid dominance + Taker buying % + Positive CVD
    oir_pump_component = _clamp((oir + 1.0) * 50.0)  # 0 to 100
    taker_pump_component = _clamp(taker_buy_pct)     # 0 to 100
    pump_pressure = int(round(_clamp((0.45 * oir_pump_component) + (0.55 * taker_pump_component))))

    # 4. Calculate Dump Pressure (0 - 100)
    oir_dump_component = _clamp((1.0 - oir) * 50.0)   # 0 to 100
    taker_dump_component = _clamp(taker_sell_pct)     # 0 to 100
    dump_pressure = int(round(_clamp((0.45 * oir_dump_component) + (0.55 * taker_dump_component))))

    # 5. Pulse Verdict & Microstructure Mechanics
    if pump_pressure >= 72 and taker_buy_pct >= 62.0 and oir >= 0.15:
        verdict = "PUMP_IGNITION"
        verdict_desc = "🚀 PUMP IGNITION: Agresor beli mendominasi tape, orderbook bid tebal menembus resistensi."
        smart_flow = "AGGRESSIVE_ACCUMULATION"
    elif dump_pressure >= 60 and oir >= 0.25 and taker_sell_pct >= 58.0:
        verdict = "BUY_ABSORPTION"
        verdict_desc = "🛡️ BUY ABSORPTION: Penjual pasar agresif diserap sepenuhnya oleh iceberg bid institusional."
        smart_flow = "PASSIVE_ACCUMULATION"
    elif dump_pressure >= 72 and taker_sell_pct >= 62.0 and oir <= -0.15:
        verdict = "DUMP_CASCADE"
        verdict_desc = "🔻 DUMP CASCADE: Gelombang penjualan pasar meruntuhkan support bid."
        smart_flow = "AGGRESSIVE_DISTRIBUTION"
    elif pump_pressure >= 55 and oir <= -0.25 and taker_buy_pct >= 58.0:
        verdict = "SELL_ABSORPTION"
        verdict_desc = "🧱 SELL ABSORPTION: Pembeli pasar agresif tertahan di dinding limit ask institusional."
        smart_flow = "PASSIVE_DISTRIBUTION"
    elif dump_pressure >= 65 and taker_buy_pct >= 48.0 and oir >= 0.05:
        verdict = "SELL_EXHAUSTION"
        verdict_desc = "⚡ SELL EXHAUSTION: Tekanan jual mulai mengering, bid berangsur pulih."
        smart_flow = "ACCUMULATING"
    else:
        verdict = "BALANCED_CHOP"
        verdict_desc = "⚖️ BALANCED CHOP: Likuiditas seimbang, dinamika tape berkisar di zona ekuilibrium."
        smart_flow = "NEUTRAL_ROTATION"

    result = {
        "symbol": pair,
        "base_asset": base,
        "pump_pressure": pump_pressure,
        "dump_pressure": dump_pressure,
        "pulse_verdict": verdict,
        "pulse_description": verdict_desc,
        "smart_money_flow": smart_flow,
        "microstructure": {
            "oir": round(oir, 3),
            "bid_ask_volume_ratio": round(bid_ask_ratio, 2),
            "taker_buy_pct": round(taker_buy_pct, 1),
            "taker_sell_pct": round(taker_sell_pct, 1),
            "cvd_delta_pct": round(cvd_delta_pct, 1),
            "bid_depth_usd": round(bid_vol_usd, 2),
            "ask_depth_usd": round(ask_vol_usd, 2)
        },
        "timestamp": now,
        "status": "LIVE"
    }

    _PULSE_CACHE[pair] = (now, result)
    return result

def get_coin_sentiment_and_pulse_summary(symbol: str = "BTC") -> Dict[str, Any]:
    """
    Combined convenience aggregator uniting Micro Fear & Greed and Pump Pulse.
    """
    fng = get_coin_micro_fear_greed(symbol)
    pulse = get_pump_pulse_score(symbol)

    return {
        "symbol": fng.get("symbol"),
        "micro_fear_greed": fng,
        "pump_pulse": pulse,
        "timestamp": time.time()
    }

if __name__ == "__main__":
    test_coin = sys.argv[1] if len(sys.argv) > 1 else "BTC"
    print(f"=== TESTING COIN MICRO SENTIMENT & PUMP PULSE FOR {test_coin} ===")
    res = get_coin_sentiment_and_pulse_summary(test_coin)
    print(json.dumps(res, indent=2))

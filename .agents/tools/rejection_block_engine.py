"""
ICT Rejection Block Engine (Smart Money Reversal Predictor)
Synthesized from Smart Money Concepts (ICT) & Akademi Crypto Advanced Order Flow.

Key Logic:
1. Detects Swing High / Swing Low with long rejection wicks (>= 40% of candle range).
2. Confirms institutional displacement on subsequent candle(s).
3. Defines the Rejection Block:
   - Bullish: From lowest wick low to candle body low.
   - Bearish: From candle body high to highest wick high.
4. Calculates the Mean Threshold (50% Wick Equilibrium) for Optimal Trade Entry (OTE).
5. Evaluates active retest status (price retesting Mean Threshold) for high R:R reversal entries.
"""

import os
import sys
import json
import math
from datetime import datetime

# UTF-8 encoding safeguard for Windows consoles
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

try:
    import market_structure
except ImportError:
    market_structure = None


def normalize_candles(candles):
    """
    Normalizes candle data from Binance/OKX dicts or lists into standardized float dicts.
    """
    if not candles:
        return []

    norm = []
    for c in candles:
        if isinstance(c, dict):
            o = float(c.get("open", c.get("o", 0)))
            h = float(c.get("high", c.get("h", 0)))
            l = float(c.get("low", c.get("l", 0)))
            cl = float(c.get("close", c.get("c", 0)))
            v = float(c.get("volume", c.get("v", 0)))
            t = c.get("time", c.get("t", c.get("timestamp", 0)))
            norm.append({"open": o, "high": h, "low": l, "close": cl, "volume": v, "time": t})
        elif isinstance(c, (list, tuple)) and len(c) >= 5:
            # Assumes [time, open, high, low, close, volume]
            norm.append({
                "time": c[0],
                "open": float(c[1]),
                "high": float(c[2]),
                "low": float(c[3]),
                "close": float(c[4]),
                "volume": float(c[5]) if len(c) > 5 else 0.0
            })
    return norm


def detect_rejection_blocks(candles, timeframe="1H", min_wick_ratio=0.38, max_lookback=40):
    """
    Scans candlestick history for active Bullish and Bearish Rejection Blocks.

    Parameters:
    - candles: List of candle dicts/lists.
    - timeframe: Timeframe label (e.g. '1H', '15m', '4H').
    - min_wick_ratio: Minimum ratio of wick length to total candle range (default 0.38 / 38%).
    - max_lookback: How many past candles to inspect.

    Returns:
    List of active, uninvalidated Rejection Block dictionaries sorted by recency.
    """
    norm = normalize_candles(candles)
    if len(norm) < 4:
        return []

    lookback_candles = norm[-max_lookback:] if len(norm) > max_lookback else norm
    current_price = norm[-1]["close"]
    detected_blocks = []

    # Iterate through historical candles (excluding the current unclosed candle)
    n = len(lookback_candles)
    for i in range(2, n - 1):
        c = lookback_candles[i]
        c_open = c["open"]
        c_close = c["close"]
        c_high = c["high"]
        c_low = c["low"]
        c_range = max(c_high - c_low, 0.00001)

        body_top = max(c_open, c_close)
        body_bottom = min(c_open, c_close)

        # -------------------------------------------------------------
        # 1. BULLISH REJECTION BLOCK (Long lower wick at swing low)
        # -------------------------------------------------------------
        lower_wick = body_bottom - c_low
        lower_wick_ratio = lower_wick / c_range

        # Local Swing Low condition (lower low than at least 2 preceding candles)
        is_swing_low = c_low < lookback_candles[i - 1]["low"] and c_low < lookback_candles[i - 2]["low"]

        if is_swing_low and lower_wick_ratio >= min_wick_ratio:
            # Displacement check: At least one of next 3 candles pushes strongly above rejection body
            subsequent = lookback_candles[i + 1:]
            displaced = any(sub["close"] > body_top for sub in subsequent[:3])

            if displaced:
                block_high = body_bottom
                block_low = c_low
                mean_threshold = round((block_high + block_low) / 2.0, 6)

                # Invalidation check: Did price subsequently close below block_low?
                invalidated = any(sub["close"] < block_low for sub in subsequent)

                if not invalidated:
                    # Check how many times price has tested this block
                    touches = sum(1 for sub in subsequent if sub["low"] <= block_high and sub["high"] >= block_low)
                    
                    detected_blocks.append({
                        "type": "BULLISH_REJECTION_BLOCK",
                        "side": "LONG",
                        "timeframe": timeframe,
                        "index": i,
                        "formed_time": c.get("time"),
                        "block_high": round(block_high, 6),
                        "block_low": round(block_low, 6),
                        "mean_threshold": mean_threshold,
                        "wick_ratio": round(lower_wick_ratio, 3),
                        "touches": touches,
                        "status": "UNMITIGATED" if touches <= 2 else "PARTIALLY_MITIGATED"
                    })

        # -------------------------------------------------------------
        # 2. BEARISH REJECTION BLOCK (Long upper wick at swing high)
        # -------------------------------------------------------------
        upper_wick = c_high - body_top
        upper_wick_ratio = upper_wick / c_range

        # Local Swing High condition (higher high than at least 2 preceding candles)
        is_swing_high = c_high > lookback_candles[i - 1]["high"] and c_high > lookback_candles[i - 2]["high"]

        if is_swing_high and upper_wick_ratio >= min_wick_ratio:
            subsequent = lookback_candles[i + 1:]
            displaced = any(sub["close"] < body_bottom for sub in subsequent[:3])

            if displaced:
                block_high = c_high
                block_low = body_top
                mean_threshold = round((block_high + block_low) / 2.0, 6)

                # Invalidation check: Did price subsequently close above block_high?
                invalidated = any(sub["close"] > block_high for sub in subsequent)

                if not invalidated:
                    touches = sum(1 for sub in subsequent if sub["high"] >= block_low and sub["low"] <= block_high)

                    detected_blocks.append({
                        "type": "BEARISH_REJECTION_BLOCK",
                        "side": "SHORT",
                        "timeframe": timeframe,
                        "index": i,
                        "formed_time": c.get("time"),
                        "block_high": round(block_high, 6),
                        "block_low": round(block_low, 6),
                        "mean_threshold": mean_threshold,
                        "wick_ratio": round(upper_wick_ratio, 3),
                        "touches": touches,
                        "status": "UNMITIGATED" if touches <= 2 else "PARTIALLY_MITIGATED"
                    })

    # Return most recent blocks first
    detected_blocks.sort(key=lambda x: x["index"], reverse=True)
    return detected_blocks


def evaluate_retest_status(symbol, current_price, active_blocks, sweep_buffer_pct=None):
    """
    Evaluates if current price is actively retesting an active Rejection Block zone,
    especially around the high-confluence 50% Mean Threshold.

    Returns:
    (has_setup: bool, best_block: dict, evaluation_details: dict)
    """
    if not active_blocks or current_price <= 0:
        return False, None, {"status": "NO_BLOCKS"}

    if sweep_buffer_pct is None:
        if market_structure:
            sweep_buffer_pct = market_structure.get_asset_sweep_buffer(symbol)
        else:
            sweep_buffer_pct = 0.012

    for block in active_blocks:
        b_low = block["block_low"]
        b_high = block["block_high"]
        mt = block["mean_threshold"]
        side = block["side"]

        # Calculate distance to 50% Mean Threshold
        dist_to_mt_pct = abs(current_price - mt) / current_price

        # Check if price is within or kissing the block boundary
        tolerance = (b_high - b_low) * 0.20
        is_inside = (b_low - tolerance) <= current_price <= (b_high + tolerance)
        is_near_mt = dist_to_mt_pct <= 0.0065  # Within 0.65% of Mean Threshold

        if is_inside or is_near_mt:
            if side == "LONG":
                # Valid Bullish Retest: Price is in upper wick zone or hovering on MT
                sl_price = round(b_low * (1.0 - sweep_buffer_pct), 4)
                r_dist = current_price - sl_price
                if r_dist > 0:
                    tp1 = round(current_price + (r_dist * 2.0), 4)
                    tp2 = round(current_price + (r_dist * 3.5), 4)
                    
                    retest_state = "TESTING_MEAN_THRESHOLD" if is_near_mt else "INSIDE_REJECTION_BLOCK"
                    return True, block, {
                        "symbol": symbol,
                        "side": "LONG",
                        "setup_name": "Bullish Rejection Block Mean Threshold Bounce",
                        "entry_price": round(current_price, 4),
                        "mean_threshold": mt,
                        "block_range": (b_low, b_high),
                        "sl_price": sl_price,
                        "tp1_price": tp1,
                        "tp2_price": tp2,
                        "rr_ratio": 3.0,
                        "retest_state": retest_state,
                        "confluence_bonus": 12 if is_near_mt else 8,
                        "reason": f"Live retest of 1H Bullish Rejection Block ({retest_state}) @ ${current_price:,.4f} with Mean Threshold @ ${mt:,.4f}"
                    }
            else:
                # Valid Bearish Retest
                sl_price = round(b_high * (1.0 + sweep_buffer_pct), 4)
                r_dist = sl_price - current_price
                if r_dist > 0:
                    tp1 = round(current_price - (r_dist * 2.0), 4)
                    tp2 = round(current_price - (r_dist * 3.5), 4)

                    retest_state = "TESTING_MEAN_THRESHOLD" if is_near_mt else "INSIDE_REJECTION_BLOCK"
                    return True, block, {
                        "symbol": symbol,
                        "side": "SHORT",
                        "setup_name": "Bearish Rejection Block Mean Threshold Rejection",
                        "entry_price": round(current_price, 4),
                        "mean_threshold": mt,
                        "block_range": (b_low, b_high),
                        "sl_price": sl_price,
                        "tp1_price": tp1,
                        "tp2_price": tp2,
                        "rr_ratio": 3.0,
                        "retest_state": retest_state,
                        "confluence_bonus": 12 if is_near_mt else 8,
                        "reason": f"Live retest of 1H Bearish Rejection Block ({retest_state}) @ ${current_price:,.4f} with Mean Threshold @ ${mt:,.4f}"
                    }

    return False, None, {"status": "NO_ACTIVE_RETEST", "blocks_count": len(active_blocks)}


def get_rejection_block_intelligence(symbol, candles_1h, current_price=None):
    """
    Comprehensive entry point for Market Eyes & Trading Desk integration.
    Analyzes 1H candles, detects active rejection blocks, and evaluates current retest proximity.
    """
    if not candles_1h or len(candles_1h) < 4:
        return {
            "has_rejection_block": False,
            "blocks": [],
            "retest_setup": None,
            "summary": "Data lilin tidak mencukupi"
        }

    norm = normalize_candles(candles_1h)
    if current_price is None or current_price <= 0:
        current_price = norm[-1]["close"]

    blocks = detect_rejection_blocks(norm, timeframe="1H", min_wick_ratio=0.38)
    has_setup, best_block, eval_details = evaluate_retest_status(symbol, current_price, blocks)

    bullish_count = sum(1 for b in blocks if b["side"] == "LONG")
    bearish_count = sum(1 for b in blocks if b["side"] == "SHORT")

    if has_setup and eval_details:
        summary = (
            f"🎯 REJECTION BLOCK RETEST: {eval_details['side']} setup active "
            f"({eval_details['retest_state']}) | MT: ${eval_details['mean_threshold']:,.4f}"
        )
    elif blocks:
        latest = blocks[0]
        summary = (
            f"Active Rejection Blocks: {bullish_count} Bullish, {bearish_count} Bearish | "
            f"Latest: {latest['type']} ({latest['status']}) MT @ ${latest['mean_threshold']:,.4f}"
        )
    else:
        summary = "Tidak ada Rejection Block aktif di rentang harga saat ini."

    return {
        "has_rejection_block": len(blocks) > 0,
        "is_retesting_now": has_setup,
        "blocks": blocks,
        "retest_setup": eval_details if has_setup else None,
        "bullish_blocks": bullish_count,
        "bearish_blocks": bearish_count,
        "summary": summary
    }


if __name__ == "__main__":
    import urllib.request

    print("==================================================================")
    print("       🕯️ ICT REJECTION BLOCK ENGINE DIAGNOSTIC & LIVE TEST")
    print("==================================================================")
    
    test_coins = ["BTC", "ETH", "SOL"]
    for coin in test_coins:
        sym = f"{coin}USDT"
        url = f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval=1h&limit=50"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                candles = [{
                    "time": r[0],
                    "open": float(r[1]),
                    "high": float(r[2]),
                    "low": float(r[3]),
                    "close": float(r[4]),
                    "volume": float(r[5])
                } for r in raw]

                intel = get_rejection_block_intelligence(sym, candles)
                print(f"\n📊 {sym} (1H Price: ${candles[-1]['close']:,.2f}):")
                print(f" * Rejection Blocks Detected: {len(intel['blocks'])} (Bullish: {intel['bullish_blocks']} | Bearish: {intel['bearish_blocks']})")
                print(f" * Retest In Progress Now   : {'🔥 YES' if intel['is_retesting_now'] else '⚪ NO'}")
                print(f" * Intel Summary           : {intel['summary']}")

                if intel["blocks"]:
                    print(" * Top 2 Blocks:")
                    for b in intel["blocks"][:2]:
                        print(f"   - {b['type']} | Range: ${b['block_low']:,.2f} - ${b['block_high']:,.2f} | MT 50%: ${b['mean_threshold']:,.2f} | Wick: {b['wick_ratio']*100:.1f}%")
        except Exception as e:
            print(f"❌ Error testing {sym}: {e}")

    print("\n==================================================================")

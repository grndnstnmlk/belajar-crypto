"""
Market Eyes (Mata Agent) - Institutional Market Intelligence Engine
Fetches real-time price, multi-timeframe candles, technical indicators (RSI, EMA 20/50/200),
Fair Value Gaps (FVG), and Perpetual Funding Rates.
"""

import argparse
import json
import math
import sys
import urllib.request
import urllib.error

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
}

def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[Error] Fetching {url}: {e}", file=sys.stderr)
        return None

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [max(d, 0) for d in deltas[:period]]
    losses = [max(-d, 0) for d in deltas[:period]]

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    for d in deltas[period:]:
        gain = max(d, 0)
        loss = max(-d, 0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100.0 - (100.0 / (1.0 + rs)), 2)

def calculate_ema(values, period):
    if not values:
        return 0
    k = 2 / (period + 1)
    ema = values[0]
    for val in values[1:]:
        ema = (val * k) + (ema * (1 - k))
    return ema

def detect_three_touch_setup(highs, lows, closes, current_price, tolerance=0.008):
    """
    Patrick Nill 12x Robbins Cup Champion '3-Touch' Setup Detector.
    Identifies when a Support or Resistance level has had 2 prior swing tests
    and current price is currently executing the 3rd golden touch.
    """
    n = len(closes)
    if n < 15 or current_price <= 0:
        return None

    swing_lows = []
    for i in range(2, n - 2):
        if lows[i] <= lows[i - 1] and lows[i] <= lows[i - 2] and lows[i] <= lows[i + 1] and lows[i] <= lows[i + 2]:
            swing_lows.append((i, lows[i]))

    swing_highs = []
    for i in range(2, n - 2):
        if highs[i] >= highs[i - 1] and highs[i] >= highs[i - 2] and highs[i] >= highs[i + 1] and highs[i] >= highs[i + 2]:
            swing_highs.append((i, highs[i]))

    # Check Bullish 3-Touch Support
    sup_touches = [p for p in swing_lows if abs(p[1] - current_price) / current_price <= tolerance and p[0] < n - 2]
    if len(sup_touches) >= 2:
        avg_sup = sum(t[1] for t in sup_touches) / len(sup_touches)
        return {
            "type": "BULLISH_3_TOUCH",
            "side": "LONG",
            "level": round(avg_sup, 4),
            "touch_count": 3,
            "label": f"🌟 [PATRICK NILL 3-TOUCH] Golden Support Touch at ${avg_sup:,.4f}"
        }

    # Check Bearish 3-Touch Resistance
    res_touches = [p for p in swing_highs if abs(p[1] - current_price) / current_price <= tolerance and p[0] < n - 2]
    if len(res_touches) >= 2:
        avg_res = sum(t[1] for t in res_touches) / len(res_touches)
        return {
            "type": "BEARISH_3_TOUCH",
            "side": "SHORT",
            "level": round(avg_res, 4),
            "touch_count": 3,
            "label": f"🌟 [PATRICK NILL 3-TOUCH] Golden Resistance Touch at ${avg_res:,.4f}"
        }

    return None

def calculate_vwap_and_bands(raw_candles):
    """
    Trader 2 (Ex-Hedge Fund Manager) Institutional VWAP & Standard Deviation Bands.
    Calculates true institutional volume-weighted average price and +/-1σ / +/-2σ volatility bands.
    """
    if len(raw_candles) < 15:
        return None

    cum_vol = 0.0
    cum_pv = 0.0
    typical_prices = []
    volumes = []

    for c in raw_candles:
        h = float(c[2])
        l = float(c[3])
        cl = float(c[4])
        tp = (h + l + cl) / 3.0
        vol = float(c[6]) if len(c) > 6 and float(c[6]) > 0 else (float(c[5]) * cl)

        cum_vol += vol
        cum_pv += tp * vol
        typical_prices.append(tp)
        volumes.append(vol)

    if cum_vol <= 0:
        return None

    vwap = cum_pv / cum_vol

    # Volume-Weighted Standard Deviation
    sum_sq_diff = 0.0
    for tp, vol in zip(typical_prices, volumes):
        sum_sq_diff += vol * ((tp - vwap) ** 2)
    vw_std = math.sqrt(sum_sq_diff / cum_vol)

    upper_1 = vwap + (1.0 * vw_std)
    lower_1 = vwap - (1.0 * vw_std)
    upper_2 = vwap + (2.0 * vw_std)
    lower_2 = vwap - (2.0 * vw_std)

    current_price = float(raw_candles[-1][4])
    dist_vwap_pct = ((current_price - vwap) / vwap) * 100.0

    state = "Above VWAP (Bullish Acceptance)" if current_price > vwap else "Below VWAP (Bearish Acceptance)"
    if current_price >= upper_2:
        state = "Extreme Overbought (+2σ Volatility Exhaustion)"
    elif current_price <= lower_2:
        state = "Extreme Oversold (-2σ Volatility Exhaustion)"

    return {
        "vwap": round(vwap, 4),
        "upper_1": round(upper_1, 4),
        "lower_1": round(lower_1, 4),
        "upper_2": round(upper_2, 4),
        "lower_2": round(lower_2, 4),
        "std": round(vw_std, 4),
        "dist_pct": round(dist_vwap_pct, 2),
        "state": state
    }

def calculate_volume_profile(raw_candles, current_price, num_bins=35):
    """
    Auction Market Theory & Volume Profile (Fabio Valentini / Akademi Crypto Module 04-05).
    Calculates POC (Point of Control), VAH (Value Area High), VAL (Value Area Low - 70% Volume),
    and detects Failed Auction / Trapped Traders setups.
    """
    if len(raw_candles) < 15 or current_price <= 0:
        return None

    highs = [float(c[2]) for c in raw_candles]
    lows = [float(c[3]) for c in raw_candles]
    min_p = min(lows)
    max_p = max(highs)

    if max_p <= min_p:
        return None

    bin_width = (max_p - min_p) / num_bins
    bins = [0.0] * num_bins

    for c in raw_candles:
        h = float(c[2])
        l = float(c[3])
        vol = float(c[6]) if len(c) > 6 and float(c[6]) > 0 else (float(c[5]) * float(c[4]))
        start_idx = max(0, min(num_bins - 1, int((l - min_p) / bin_width)))
        end_idx = max(0, min(num_bins - 1, int((h - min_p) / bin_width)))
        span = max(1, end_idx - start_idx + 1)
        for b in range(start_idx, end_idx + 1):
            bins[b] += vol / span

    total_vol = sum(bins)
    if total_vol <= 0:
        return None

    # Point of Control (POC)
    poc_idx = max(range(num_bins), key=lambda i: bins[i])
    poc_price = min_p + (poc_idx + 0.5) * bin_width

    # Value Area (70% Volume distribution)
    target_vol = total_vol * 0.70
    accumulated_vol = bins[poc_idx]
    included_indices = {poc_idx}
    up_idx = poc_idx + 1
    down_idx = poc_idx - 1

    while accumulated_vol < target_vol and (up_idx < num_bins or down_idx >= 0):
        up_vol = bins[up_idx] if up_idx < num_bins else -1
        down_vol = bins[down_idx] if down_idx >= 0 else -1

        if up_vol >= down_vol and up_idx < num_bins:
            accumulated_vol += up_vol
            included_indices.add(up_idx)
            up_idx += 1
        elif down_idx >= 0:
            accumulated_vol += down_vol
            included_indices.add(down_idx)
            down_idx -= 1
        else:
            break

    val_idx = min(included_indices)
    vah_idx = max(included_indices)
    val_price = min_p + val_idx * bin_width
    vah_price = min_p + (vah_idx + 1) * bin_width

    # Fabio Valentini Failed Auction & Trapped Traders Check
    recent_candles = raw_candles[-4:]
    recent_low = min(float(c[3]) for c in recent_candles)
    recent_high = max(float(c[2]) for c in recent_candles)

    setup = None
    if recent_low < val_price and current_price >= val_price and current_price < poc_price * 1.01:
        setup = {
            "type": "BULLISH_FAILED_AUCTION",
            "side": "LONG",
            "sl": round(recent_low * 0.997, 4),
            "tp1": round(poc_price, 4),
            "tp2": round(vah_price, 4),
            "label": f"🔥 [FABIO VALENTINI AUCTION] Trapped Sellers below VAL -> Reclaimed VAL (${val_price:,.4f}) -> Target POC (${poc_price:,.4f})"
        }
    elif recent_high > vah_price and current_price <= vah_price and current_price > poc_price * 0.99:
        setup = {
            "type": "BEARISH_FAILED_AUCTION",
            "side": "SHORT",
            "sl": round(recent_high * 1.003, 4),
            "tp1": round(poc_price, 4),
            "tp2": round(val_price, 4),
            "label": f"🔥 [FABIO VALENTINI AUCTION] Trapped Buyers above VAH -> Rejected VAH (${vah_price:,.4f}) -> Target POC (${poc_price:,.4f})"
        }

    return {
        "poc": round(poc_price, 4),
        "vah": round(vah_price, 4),
        "val": round(val_price, 4),
        "setup": setup
    }

def detect_liquidity_sweep_mss(highs, lows, closes, current_price, tolerance=0.005):
    """
    Tim Flossbach (IQCapital / FirstClass Trading & Akademi Crypto Module 06)
    Liquidity Sweep + Market Structure Shift (MSS) Setup Detector.
    Identifies institutional liquidity sweeps of Buy-Side (BSL) or Sell-Side (SSL)
    pools followed by an aggressive market structure shift confirmation.
    """
    n = len(closes)
    if n < 20 or current_price <= 0:
        return None

    # 1. Identify Swing Highs & Swing Lows
    swing_highs = []
    swing_lows = []
    for i in range(2, n - 2):
        if highs[i] >= highs[i-1] and highs[i] >= highs[i-2] and highs[i] >= highs[i+1] and highs[i] >= highs[i+2]:
            swing_highs.append((i, highs[i]))
        if lows[i] <= lows[i-1] and lows[i] <= lows[i-2] and lows[i] <= lows[i+1] and lows[i] <= lows[i+2]:
            swing_lows.append((i, lows[i]))

    if not swing_highs or not swing_lows:
        return None

    # Check Bullish Sweep & MSS (SSL Swept)
    recent_start = max(0, n - 4)
    for k in range(recent_start, n):
        prior_lows = [p for p in swing_lows if p[0] < k - 1]
        for p_idx, p_level in prior_lows:
            if lows[k] < p_level and closes[k] >= p_level * 0.997:
                inter_highs = [h[1] for h in swing_highs if h[0] > p_idx and h[0] < k]
                break_level = max(inter_highs) if inter_highs else closes[p_idx]
                if current_price >= break_level * 0.999 or max(closes[k:]) > break_level:
                    sweep_low = lows[k]
                    opposing_high = max(h[1] for h in swing_highs[-3:]) if swing_highs else current_price * 1.03
                    return {
                        "type": "BULLISH_SWEEP_MSS",
                        "side": "LONG",
                        "sweep_level": round(sweep_low, 4),
                        "sl": round(sweep_low * 0.996, 4),
                        "target": round(opposing_high, 4),
                        "label": f"⚡ [TIM FLOSSBACH MSS] SSL Swept (${sweep_low:,.4f}) + Bullish MSS Confirmed -> Target ${opposing_high:,.4f}"
                    }

    # Check Bearish Sweep & MSS (BSL Swept)
    for k in range(recent_start, n):
        prior_highs = [p for p in swing_highs if p[0] < k - 1]
        for p_idx, p_level in prior_highs:
            if highs[k] > p_level and closes[k] <= p_level * 1.003:
                inter_lows = [l[1] for l in swing_lows if l[0] > p_idx and l[0] < k]
                break_level = min(inter_lows) if inter_lows else closes[p_idx]
                if current_price <= break_level * 1.001 or min(closes[k:]) < break_level:
                    sweep_high = highs[k]
                    opposing_low = min(l[1] for l in swing_lows[-3:]) if swing_lows else current_price * 0.97
                    return {
                        "type": "BEARISH_SWEEP_MSS",
                        "side": "SHORT",
                        "sweep_level": round(sweep_high, 4),
                        "sl": round(sweep_high * 1.004, 4),
                        "target": round(opposing_low, 4),
                        "label": f"⚡ [TIM FLOSSBACH MSS] BSL Swept (${sweep_high:,.4f}) + Bearish MSS Confirmed -> Target ${opposing_low:,.4f}"
                    }

    return None

def get_market_eyes(symbol="BTC", bar="1H"):
    base = symbol.upper().replace("-USDT", "").replace("USDT", "")
    inst_id_spot = f"{base}-USDT"
    inst_id_swap = f"{base}-USDT-SWAP"
    bar_clean = bar.upper()

    print(f"\n=======================================================")
    print(f"       👁️ MARKET EYES INTELLIGENCE: {inst_id_spot}")
    print(f"=======================================================")

    # 1. Fetch Spot Ticker
    ticker_url = f"https://www.okx.com/api/v5/market/ticker?instId={inst_id_spot}"
    ticker_res = fetch_json(ticker_url)
    if not ticker_res or ticker_res.get("code") != "0" or not ticker_res.get("data"):
        print(f"Error: Unable to find market ticker for {inst_id_spot}.")
        return None

    ticker_data = ticker_res["data"][0]
    current_price = float(ticker_data.get("last", 0))
    open_24h = float(ticker_data.get("open24h", 0))
    high_24h = float(ticker_data.get("high24h", 0))
    low_24h = float(ticker_data.get("low24h", 0))
    vol_quote_24h = float(ticker_data.get("volCcy24h", 0))
    change_pct = ((current_price - open_24h) / open_24h * 100) if open_24h > 0 else 0

    print(f"Current Price    : ${current_price:,.4f}")
    print(f"24h Price Change : {change_pct:+.2f}%")
    print(f"24h High / Low   : ${high_24h:,.4f} / ${low_24h:,.4f}")
    print(f"24h Quote Volume : ${vol_quote_24h / 1_000_000:,.2f} Million USDT")

    # 2. Fetch Funding Rate (Market Sentiment & Overleverage)
    funding_url = f"https://www.okx.com/api/v5/public/funding-rate?instId={inst_id_swap}"
    funding_res = fetch_json(funding_url)
    funding_rate = None
    if funding_res and funding_res.get("code") == "0" and funding_res.get("data"):
        raw_rate = float(funding_res["data"][0].get("fundingRate", 0))
        funding_rate = raw_rate * 100
        sentiment = "High Longs / Bullish Excess (Careful of Long Squeeze)" if funding_rate > 0.03 else "High Shorts / Squeeze Potential" if funding_rate < -0.01 else "Healthy / Balanced"
        print(f"Perp Funding Rate: {funding_rate:+.4f}% [{sentiment}]")

    # 3. Candlesticks & Technical Indicators
    candles_url = f"https://www.okx.com/api/v5/market/candles?instId={inst_id_spot}&bar={bar_clean}&limit=60"
    candles_res = fetch_json(candles_url)
    if candles_res and candles_res.get("code") == "0" and candles_res.get("data"):
        raw_candles = list(reversed(candles_res["data"]))
        closes = [float(c[4]) for c in raw_candles]
        highs = [float(c[2]) for c in raw_candles]
        lows = [float(c[3]) for c in raw_candles]

        rsi14 = calculate_rsi(closes, 14)
        ema20 = calculate_ema(closes, min(20, len(closes)))
        ema50 = calculate_ema(closes, min(50, len(closes)))

        print("-------------------------------------------------------")
        print(f"Timeframe        : {bar_clean}")
        rsi_zone = "Oversold (<30)" if rsi14 and rsi14 < 30 else "Overbought (>70)" if rsi14 and rsi14 > 70 else "Neutral (30-70)"
        print(f"RSI (14)         : {rsi14} [{rsi_zone}]")
        print(f"EMA 20 / EMA 50  : ${ema20:,.4f} / ${ema50:,.4f}")

        # Trend & Structure
        if current_price > ema20 > ema50:
            bias = "🟢 BULLISH CONTINUATION (Price > EMA20 > EMA50)"
        elif current_price < ema20 < ema50:
            bias = "🔴 BEARISH CONTINUATION (Price < EMA20 < EMA50)"
        else:
            bias = "🟡 RANGE / CONSOLIDATION (Mixed EMAs)"
        print(f"Trend Bias       : {bias}")

        # FVG Detection
        fvg = "None detected in recent 5 candles"
        for i in range(len(raw_candles) - 1, max(1, len(raw_candles) - 6), -1):
            if lows[i] > highs[i - 2]:
                fvg = f"Bullish FVG zone between ${highs[i-2]:,.4f} and ${lows[i]:,.4f}"
                break
            elif highs[i] < lows[i - 2]:
                fvg = f"Bearish FVG zone between ${lows[i-2]:,.4f} and ${highs[i]:,.4f}"
                break
        print(f"SMC Pattern      : {fvg}")

        # 3-Touch Detection (Patrick Nill 12x Robbins Cup Champion Rule)
        three_touch = detect_three_touch_setup(highs, lows, closes, current_price)
        if three_touch:
            print(f"Robbins Rule     : {three_touch['label']}")

        # Volume Profile & Auction Market Theory (Fabio Valentini Strategy)
        volume_profile = calculate_volume_profile(raw_candles, current_price)
        if volume_profile:
            print(f"Volume Profile   : VAH: ${volume_profile['vah']:,.4f} | POC: ${volume_profile['poc']:,.4f} | VAL: ${volume_profile['val']:,.4f}")
            if volume_profile.get("setup"):
                print(f"Auction Trigger  : {volume_profile['setup']['label']}")
            else:
                pos = "Above VAH (Premium Excursion)" if current_price > volume_profile['vah'] else "Below VAL (Discount Excursion)" if current_price < volume_profile['val'] else "Inside Value Area (Fair Balance)"
                print(f"Auction State    : {pos}")

        # Liquidity Sweep & Market Structure Shift (Tim Flossbach Strategy)
        liquidity_sweep = detect_liquidity_sweep_mss(highs, lows, closes, current_price)
        if liquidity_sweep:
            print(f"Liquidity Sweep  : {liquidity_sweep['label']}")

        # Institutional VWAP & Standard Deviation Bands (Ex-Hedge Fund Manager Strategy)
        vwap_data = calculate_vwap_and_bands(raw_candles)
        if vwap_data:
            print(f"Inst. VWAP       : ${vwap_data['vwap']:,.4f} [{vwap_data['dist_pct']:+,.2f}%] | Bands (±1σ): ${vwap_data['lower_1']:,.4f} - ${vwap_data['upper_1']:,.4f}")
            print(f"VWAP Bias        : {vwap_data['state']}")

    print(f"=======================================================\n")
    return {
        "symbol": inst_id_spot,
        "price": current_price,
        "change_pct": change_pct,
        "high_24h": high_24h if 'high_24h' in locals() else None,
        "low_24h": low_24h if 'low_24h' in locals() else None,
        "rsi": rsi14 if 'rsi14' in locals() else None,
        "ema20": ema20 if 'ema20' in locals() else None,
        "ema50": ema50 if 'ema50' in locals() else None,
        "bias": bias if 'bias' in locals() else "NEUTRAL",
        "fvg": fvg if 'fvg' in locals() else None,
        "three_touch": three_touch if 'three_touch' in locals() else None,
        "volume_profile": volume_profile if 'volume_profile' in locals() else None,
        "liquidity_sweep": liquidity_sweep if 'liquidity_sweep' in locals() else None,
        "vwap": vwap_data if 'vwap_data' in locals() else None,
        "funding_rate": funding_rate
    }

def main():
    parser = argparse.ArgumentParser(description="Market Eyes - Live Market Intelligence")
    parser.add_argument("--symbol", type=str, default="BTC", help="Asset ticker (e.g. BTC, ETH, SOL)")
    parser.add_argument("--bar", type=str, default="1H", help="Candle timeframe: 15m, 1H, 4H, 1D")
    args = parser.parse_args()

    get_market_eyes(args.symbol, args.bar)

if __name__ == "__main__":
    main()

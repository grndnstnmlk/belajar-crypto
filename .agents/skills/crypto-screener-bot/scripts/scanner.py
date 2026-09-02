"""
Crypto Market Live Scanner (Zero-Dependency)
Powered by OKX Public Spot API & Candlestick Feeds.
"""

import argparse
import json
import math
import sys
import urllib.request
import urllib.error

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[Error] Failed to fetch {url}: {e}", file=sys.stderr)
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

def scan_top_markets(limit=15):
    print(f"=== Scanning Top {limit} Crypto Markets by 24h Volume (OKX Spot) ===\n")
    url = "https://www.okx.com/api/v5/market/tickers?instType=SPOT"
    res = fetch_json(url)
    if not res or res.get("code") != "0":
        print("Could not retrieve market data.")
        return

    data = res.get("data", [])
    ignored_bases = ["USDC", "EUR", "DAI", "TUSD", "FDUSD", "AEUR"]
    valid = []

    for item in data:
        inst_id = item.get("instId", "")
        if not inst_id.endswith("-USDT"):
            continue
        base = inst_id.split("-")[0]
        if base in ignored_bases:
            continue

        try:
            last_price = float(item.get("last", 0))
            open_24h = float(item.get("open24h", 0))
            vol_24h = float(item.get("volCcy24h", 0))  # quote volume in USDT
            pct_change = ((last_price - open_24h) / open_24h * 100) if open_24h > 0 else 0.0

            valid.append({
                "instId": inst_id,
                "base": base,
                "price": last_price,
                "change_pct": pct_change,
                "volume_m": vol_24h / 1_000_000,
            })
        except (ValueError, TypeError):
            continue

    valid.sort(key=lambda x: x["volume_m"], reverse=True)
    top_coins = valid[:limit]

    print(f"{'Pair':<12} | {'Price ($)':<14} | {'24h Change':<12} | {'24h Volume':<12}")
    print("-" * 58)
    for c in top_coins:
        chg_sign = "+" if c["change_pct"] > 0 else ""
        chg_str = f"{chg_sign}{c['change_pct']:.2f}%"
        price_fmt = f"{c['price']:,.4f}" if c["price"] < 1 else f"{c['price']:,.2f}"
        print(f"{c['instId']:<12} | ${price_fmt:<13} | {chg_str:<12} | ${c['volume_m']:>7.1f}M")

def analyze_symbol(symbol, bar="1H"):
    base = symbol.upper().replace("-USDT", "").replace("USDT", "")
    inst_id = f"{base}-USDT"
    bar_clean = bar.upper()
    print(f"\nAnalyzing {inst_id} [{bar_clean}] candlestick data...")

    url = f"https://www.okx.com/api/v5/market/candles?instId={inst_id}&bar={bar_clean}&limit=60"
    res = fetch_json(url)
    if not res or res.get("code") != "0" or not res.get("data"):
        print(f"Failed to fetch candlesticks for {inst_id}. Make sure the pair exists.")
        return

    # OKX candles format: [ts, open, high, low, close, vol, volCcy, volCcyQuote, confirm]
    # Data is ordered from newest to oldest; reverse to chronological order
    raw_candles = list(reversed(res["data"]))

    closes = [float(k[4]) for k in raw_candles]
    highs = [float(k[2]) for k in raw_candles]
    lows = [float(k[3]) for k in raw_candles]

    current_price = closes[-1]
    rsi = calculate_rsi(closes, period=14)

    def calc_ema(values, period):
        k = 2 / (period + 1)
        ema = values[0]
        for val in values[1:]:
            ema = (val * k) + (ema * (1 - k))
        return ema

    ema20 = calc_ema(closes, min(20, len(closes)))
    ema50 = calc_ema(closes, min(50, len(closes)))

    # Fair Value Gap (FVG) detection in last 5 candles
    fvg_info = "None detected in recent 5 candles"
    for i in range(len(raw_candles) - 1, max(1, len(raw_candles) - 6), -1):
        if lows[i] > highs[i - 2]:
            fvg_info = f"Bullish FVG zone between ${highs[i-2]:,.4f} and ${lows[i]:,.4f}"
            break
        elif highs[i] < lows[i - 2]:
            fvg_info = f"Bearish FVG zone between ${lows[i-2]:,.4f} and ${highs[i]:,.4f}"
            break

    print(f"\n=======================================================")
    print(f"          TECHNICAL REPORT: {inst_id} ({bar_clean})")
    print(f"=======================================================")
    print(f"Current Price    : ${current_price:,.4f}")
    rsi_status = "Oversold (<30)" if rsi and rsi < 30 else "Overbought (>70)" if rsi and rsi > 70 else "Neutral (40-60)"
    print(f"RSI (14)         : {rsi}  [{rsi_status}]")
    print(f"EMA 20           : ${ema20:,.4f}")
    print(f"EMA 50           : ${ema50:,.4f}")

    if current_price > ema20 > ema50:
        trend = "STRONG BULLISH (Price > EMA20 > EMA50)"
    elif current_price < ema20 < ema50:
        trend = "STRONG BEARISH (Price < EMA20 < EMA50)"
    else:
        trend = "NEUTRAL / CONSOLIDATION"
    print(f"Market Structure : {trend}")
    print(f"SMC Pattern      : {fvg_info}")
    print(f"=======================================================\n")

def main():
    parser = argparse.ArgumentParser(description="Crypto Market Live Scanner (OKX Spot)")
    parser.add_argument("--top", type=int, default=15, help="Number of top volume coins to list")
    parser.add_argument("--symbol", type=str, default=None, help="Analyze specific token (e.g. BTC, ETH, SOL)")
    parser.add_argument("--bar", type=str, default="1H", help="Candle bar: 15m, 1H, 4H, 1D")
    args = parser.parse_args()

    if args.symbol:
        analyze_symbol(args.symbol, args.bar)
    else:
        scan_top_markets(args.top)

if __name__ == "__main__":
    main()

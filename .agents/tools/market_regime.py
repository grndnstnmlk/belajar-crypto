"""
Market Regime Filter & Classifier (Mata Deteksi Rezim Pasar)
Uses ADX (Average Directional Index), ATR (Average True Range), and Multi-EMA Alignment
to classify market state into Trending, Ranging/Sideways, or Volatility Squeeze.
Routes strategies adaptively to prevent false breakouts and sideways chop.
"""

import argparse
import json
import math
import os
import ssl
import sys
import urllib.request

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_klines(symbol="BTCUSDT", interval="1h", limit=120):
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    if not sym_clean.endswith("USDT"):
        sym_clean = f"{sym_clean}USDT"
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={sym_clean}&interval={interval.lower()}&limit={limit}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            candles = []
            for c in raw:
                candles.append({
                    "time": int(c[0]),
                    "open": float(c[1]),
                    "high": float(c[2]),
                    "low": float(c[3]),
                    "close": float(c[4]),
                    "volume": float(c[5])
                })
            return candles
    except Exception as e:
        print(f"[Error] Failed to fetch klines: {e}", file=sys.stderr)
        return []

def calculate_adx_and_atr(candles, period=14):
    if len(candles) < period * 2:
        return None, None, None, None

    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    closes = [c["close"] for c in candles]

    tr_list = []
    plus_dm_list = []
    minus_dm_list = []

    for i in range(1, len(candles)):
        h = highs[i]
        l = lows[i]
        prev_h = highs[i - 1]
        prev_l = lows[i - 1]
        prev_c = closes[i - 1]

        # True Range
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        tr_list.append(tr)

        # Directional Movement
        up_move = h - prev_h
        down_move = prev_l - l

        plus_dm = up_move if (up_move > down_move and up_move > 0) else 0.0
        minus_dm = down_move if (down_move > up_move and down_move > 0) else 0.0

        plus_dm_list.append(plus_dm)
        minus_dm_list.append(minus_dm)

    # Wilder's Smoothing
    smoothed_tr = [sum(tr_list[:period])]
    smoothed_plus = [sum(plus_dm_list[:period])]
    smoothed_minus = [sum(minus_dm_list[:period])]

    for i in range(period, len(tr_list)):
        smoothed_tr.append(smoothed_tr[-1] - (smoothed_tr[-1] / period) + tr_list[i])
        smoothed_plus.append(smoothed_plus[-1] - (smoothed_plus[-1] / period) + plus_dm_list[i])
        smoothed_minus.append(smoothed_minus[-1] - (smoothed_minus[-1] / period) + minus_dm_list[i])

    plus_di_list = []
    minus_di_list = []
    dx_list = []

    for i in range(len(smoothed_tr)):
        tr_val = smoothed_tr[i]
        p_dm = smoothed_plus[i]
        m_dm = smoothed_minus[i]

        p_di = (p_dm / tr_val * 100.0) if tr_val > 0 else 0.0
        m_di = (m_dm / tr_val * 100.0) if tr_val > 0 else 0.0

        plus_di_list.append(p_di)
        minus_di_list.append(m_di)

        di_diff = abs(p_di - m_di)
        di_sum = p_di + m_di
        dx = (di_diff / di_sum * 100.0) if di_sum > 0 else 0.0
        dx_list.append(dx)

    if len(dx_list) < period:
        return None, None, None, None

    # ADX smoothing of DX
    adx = sum(dx_list[:period]) / period
    for i in range(period, len(dx_list)):
        adx = ((adx * (period - 1)) + dx_list[i]) / period

    atr = smoothed_tr[-1] / period
    latest_plus_di = plus_di_list[-1]
    latest_minus_di = minus_di_list[-1]

    return round(adx, 2), round(atr, 4), round(latest_plus_di, 2), round(latest_minus_di, 2)

def calculate_ema(values, period):
    if not values:
        return 0
    k = 2 / (period + 1)
    ema = values[0]
    for val in values[1:]:
        ema = (val * k) + (ema * (1 - k))
    return ema

def detect_market_regime(symbol="BTCUSDT", interval="1h"):
    candles = fetch_klines(symbol, interval=interval, limit=100)
    if not candles or len(candles) < 30:
        return None

    adx, atr, plus_di, minus_di = calculate_adx_and_atr(candles, period=14)
    closes = [c["close"] for c in candles]
    current_price = closes[-1]
    ema20 = calculate_ema(closes, 20)
    ema50 = calculate_ema(closes, 50)

    atr_pct = (atr / current_price * 100.0) if (atr and current_price > 0) else 1.0

    # Classification Rules
    # 1. Volatility Squeeze
    if adx and adx < 18 and atr_pct < 1.2:
        regime = "VOLATILITY_SQUEEZE"
        regime_label = "⚪ VOLATILITY COMPRESSION / SQUEEZE"
        strategy_rec = "STANDBY / PREPARE BREAKOUT"
        desc = "Volatilitas sangat rendah & pasar sedang berkonsolidasi ketat. Potensi ledakan volatilitas segera terjadi."

    # 2. Strong Trending Market
    elif adx and adx >= 24:
        if plus_di > minus_di and current_price > ema20 > ema50:
            regime = "TRENDING_BULLISH"
            regime_label = "🟢 STRONG BULLISH TREND"
            strategy_rec = "TREND FOLLOWING (EMA CROSS / BUY DIPS)"
            desc = f"Tren naik kuat terkonfirmasi (ADX: {adx} >= 24, +DI > -DI). Strategi Trend Following sangat diunggulkan."
        elif minus_di > plus_di and current_price < ema20 < ema50:
            regime = "TRENDING_BEARISH"
            regime_label = "🔴 STRONG BEARISH TREND"
            strategy_rec = "TREND FOLLOWING (SELL RALLIES / SHORT BREAKOUT)"
            desc = f"Tren turun kuat terkonfirmasi (ADX: {adx} >= 24, -DI > +DI). Strategi Trend Following Short diunggulkan."
        else:
            regime = "TRENDING_MIXED"
            regime_label = "🟡 DEVELOPING TREND (TRANSITIONAL)"
            strategy_rec = "FAIR VALUE GAP (SMC_FVG RETEST)"
            desc = f"Momentum kuat terdeteksi (ADX: {adx}), tetapi arah struktur EMA masih bertransisi."

    # 3. Ranging / Choppy Market
    else:
        regime = "RANGING_CHOPPY"
        regime_label = "🟡 RANGING / SIDEWAYS / CHOPPY"
        strategy_rec = "MEAN REVERSION (RSI OVERSOLD/OVERBOUGHT)"
        desc = f"Pasar tidak memiliki tren kuat (ADX: {adx} < 24). Hindari Breakout! Gunakan strategi Mean Reversion pantulan Support/Resistance."

    return {
        "symbol": symbol.upper(),
        "interval": interval.upper(),
        "price": current_price,
        "adx": adx,
        "atr": atr,
        "atr_pct": round(atr_pct, 2),
        "plus_di": plus_di,
        "minus_di": minus_di,
        "ema20": round(ema20, 4),
        "ema50": round(ema50, 4),
        "regime": regime,
        "regime_label": regime_label,
        "strategy_rec": strategy_rec,
        "description": desc
    }

def display_regime_report(info):
    if not info:
        print("Gagal mendeteksi rezim pasar.")
        return

    print("\n" + "=" * 65)
    print(f"       🧭 MARKET REGIME CLASSIFIER & STRATEGY ROUTER")
    print(f"       Pair: {info['symbol']} | Timeframe: {info['interval']} | Harga: ${info['price']:,.4f}")
    print("=" * 65)
    print(f"Status Rezim Pasar     : {info['regime_label']}")
    print(f"Kekuatan Tren (ADX 14) : {info['adx']}  {'[Tren Kuat >= 24]' if info['adx']>=24 else '[Sideways / Lemah < 24]'}")
    print(f"Arah Momentum (+DI/-DI): +DI: {info['plus_di']} | -DI: {info['minus_di']}")
    print(f"Volatilitas ATR (14)   : ${info['atr']:,.4f} ({info['atr_pct']}% dari harga)")
    print(f"Struktur EMA 20 / 50   : ${info['ema20']:,.4f} / ${info['ema50']:,.4f}")
    print("-" * 65)
    print(f"🎯 Strategi Rekomendasi : {info['strategy_rec']}")
    print(f"📝 Keterangan Taktis   : {info['description']}")
    print("=" * 65 + "\n")

def scan_multi_asset_regimes(symbols=None):
    if symbols is None:
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

    print("\n" + "=" * 78)
    print("       🧭 MULTI-ASSET MARKET REGIME RADAR (1H & 4H)")
    print("=" * 78)
    print(f"{'Asset':<10} | {'TF':<4} | {'ADX 14':<8} | {'Status Rezim':<30} | {'Rekomendasi':<15}")
    print("-" * 78)
    for s in symbols:
        for tf in ["1h", "4h"]:
            inf = detect_market_regime(s, interval=tf)
            if inf:
                short_label = inf['regime'].replace("_", " ")
                print(f"{s:<10} | {tf.upper():<4} | {inf['adx']:<8} | {short_label:<30} | {inf['strategy_rec'][:15]}")
    print("=" * 78 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Market Regime Filter & Strategy Router")
    parser.add_argument("--symbol", type=str, default="SOLUSDT", help="Pair koin (misal: BTCUSDT, ETHUSDT, SOLUSDT)")
    parser.add_argument("--timeframe", type=str, default="1h", choices=["15m", "1h", "4h", "1d"])
    parser.add_argument("--radar", action="store_true", help="Scan radar rezim semua aset (BTC, ETH, SOL)")

    args = parser.parse_args()
    if args.radar:
        scan_multi_asset_regimes()
    else:
        sym_clean = args.symbol.upper().replace("-", "").replace("/", "").replace("_", "")
        if not sym_clean.endswith("USDT"):
            sym_clean = f"{sym_clean}USDT"
        info = detect_market_regime(sym_clean, interval=args.timeframe)
        display_regime_report(info)

if __name__ == "__main__":
    main()

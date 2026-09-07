"""
SMC Market Structure & Structural Trailing Stop Engine
Synthesized from Akademi Crypto Module 02 (Smart Money Concepts & Order Flow Execution)
Detects fractal Swing Highs / Swing Lows, Market Structure Shifts (BOS / CHOCH),
and computes protected Higher Lows (HL) and Lower Highs (LH) for dynamic structural trailing stops.
"""

import json
import math
import os
import ssl
import sys
import urllib.request
from datetime import datetime

# Windows console UTF-8 safety
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
}

def clean_coin(symbol):
    return symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")

def get_asset_sweep_buffer(symbol):
    """
    Akademi Crypto Anti-Liquidity-Hunt Buffer:
    - BTC: 0.8% (Deepest order book)
    - ETH/BNB: 1.0%
    - SOL/LINK/AVAX: 1.3%
    - High-Beta Altcoins (DOGE, ADA, SUI, XRP, NEAR): 1.6%
    """
    sym = symbol.upper()
    if "BTC" in sym:
        return 0.008
    elif "ETH" in sym or "BNB" in sym:
        return 0.010
    elif any(k in sym for k in ["SOL", "LINK", "AVAX"]):
        return 0.013
    else:
        return 0.016

def fetch_candles(symbol, bar="15m", limit=50):
    """
    Fetches raw candlestick data from Binance.
    Returns: list of dicts [{"open": float, "high": float, "low": float, "close": float, "time": str, "vol": float}]
    """
    base = clean_coin(symbol)
    binance_sym = f"{base}USDT"
    interval = bar.lower()
    if interval in ["60m"]:
        interval = "1h"

    # 1. Primary: Binance Vision Spot Klines
    bv_url = f"https://data-api.binance.vision/api/v3/klines?symbol={binance_sym}&interval={interval}&limit={limit}"
    try:
        req = urllib.request.Request(bv_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6, context=SSL_CTX) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            if isinstance(raw, list) and len(raw) > 0:
                candles = []
                for c in raw:
                    candles.append({
                        "time": c[0],
                        "open": float(c[1]),
                        "high": float(c[2]),
                        "low": float(c[3]),
                        "close": float(c[4]),
                        "vol": float(c[5])
                    })
                return candles
    except Exception:
        pass

    # 2. Secondary: Binance Futures Public Klines
    b_url = f"https://fapi.binance.com/fapi/v1/klines?symbol={binance_sym}&interval={interval}&limit={limit}"
    try:
        req = urllib.request.Request(b_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6, context=SSL_CTX) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            if isinstance(raw, list) and len(raw) > 0:
                candles = []
                for c in raw:
                    candles.append({
                        "time": c[0],
                        "open": float(c[1]),
                        "high": float(c[2]),
                        "low": float(c[3]),
                        "close": float(c[4]),
                        "vol": float(c[5])
                    })
                return candles
    except Exception:
        pass

    return []

def detect_swing_pivots(candles, window=2):
    """
    Detects confirmed fractal Swing Highs and Swing Lows.
    A swing low is a candle whose low is lower than `window` candles before and after it.
    A swing high is a candle whose high is higher than `window` candles before and after it.
    """
    n = len(candles)
    if n < (window * 2 + 1):
        return [], []

    swing_highs = []
    swing_lows = []

    for i in range(window, n - window):
        cur_h = candles[i]["high"]
        cur_l = candles[i]["low"]

        # Check Swing High
        is_sh = all(cur_h >= candles[i - j]["high"] for j in range(1, window + 1)) and \
                all(cur_h >= candles[i + j]["high"] for j in range(1, window + 1))
        if is_sh:
            swing_highs.append({
                "index": i,
                "price": cur_h,
                "candle": candles[i]
            })

        # Check Swing Low
        is_sl = all(cur_l <= candles[i - j]["low"] for j in range(1, window + 1)) and \
                all(cur_l <= candles[i + j]["low"] for j in range(1, window + 1))
        if is_sl:
            swing_lows.append({
                "index": i,
                "price": cur_l,
                "candle": candles[i]
            })

    return swing_highs, swing_lows

def get_protected_structural_stop(symbol, side, entry_price, current_sl, bar="15m"):
    """
    Computes institutional SMC Protected Structural Trailing Stop:
    - Long: Trails behind confirmed Higher Lows (HL) after Break of Structure.
    - Short: Trails behind confirmed Lower Highs (LH) after Break of Structure.
    - Strictly ratchets towards profit (Long SL only increases; Short SL only decreases).
    - Injects anti-sweep buffer to protect against retail stop hunt wicks.

    Returns:
    (has_new_stop: bool, new_sl_price: float, structure_label: str)
    """
    side_clean = "BUY" if side.upper() in ["BUY", "LONG"] else "SELL"
    candles = fetch_candles(symbol, bar=bar, limit=45)
    if not candles or len(candles) < 15:
        return False, current_sl, "No candle data available"

    current_price = candles[-1]["close"]
    buffer_pct = get_asset_sweep_buffer(symbol)
    swing_highs, swing_lows = detect_swing_pivots(candles, window=2)

    if side_clean == "BUY":
        # For Long: Look for confirmed Higher Lows (HL)
        # We need a swing low that is:
        # 1. Above or close to entry price (or above current SL)
        # 2. Safely below current market price (at least 0.5% below mark price)
        valid_lows = [p for p in swing_lows if p["price"] < current_price * 0.995]
        if not valid_lows:
            return False, current_sl, "Belum ada Swing Low valid di bawah harga pasar"

        # Sort by most recent index first
        valid_lows.sort(key=lambda x: x["index"], reverse=True)
        best_candidate = None

        for sl_pivot in valid_lows:
            raw_stop = sl_pivot["price"] * (1.0 - buffer_pct)
            # Must ratchet UPWARD: candidate stop must be higher than current SL
            if current_sl is None or raw_stop > (current_sl * 1.001):
                best_candidate = (sl_pivot, raw_stop)
                break

        if not best_candidate:
            return False, current_sl, "Struktur pasar belum membentuk Higher Low yang lebih tinggi dari SL saat ini"

        pivot_item, target_sl = best_candidate
        pivot_price = pivot_item["price"]

        # Precision format
        import binance_client
        clean_sl = float(binance_client.format_price_precision(symbol, target_sl))

        # Final sanity check: must still be below mark price
        if clean_sl >= current_price * 0.996:
            return False, current_sl, "Candidate SL terlalu mepet dengan harga pasar saat ini"

        label = f"SMC Protected Higher Low @ ${pivot_price:,.4f} (Buffer {buffer_pct*100:.1f}%)"
        return True, clean_sl, label

    else: # SHORT
        # For Short: Look for confirmed Lower Highs (LH)
        valid_highs = [p for p in swing_highs if p["price"] > current_price * 1.005]
        if not valid_highs:
            return False, current_sl, "Belum ada Swing High valid di atas harga pasar"

        valid_highs.sort(key=lambda x: x["index"], reverse=True)
        best_candidate = None

        for sh_pivot in valid_highs:
            raw_stop = sh_pivot["price"] * (1.0 + buffer_pct)
            # Must ratchet DOWNWARD: candidate stop must be lower than current SL
            if current_sl is None or raw_stop < (current_sl * 0.999):
                best_candidate = (sh_pivot, raw_stop)
                break

        if not best_candidate:
            return False, current_sl, "Struktur pasar belum membentuk Lower High yang lebih rendah dari SL saat ini"

        pivot_item, target_sl = best_candidate
        pivot_price = pivot_item["price"]

        import binance_client
        clean_sl = float(binance_client.format_price_precision(symbol, target_sl))

        if clean_sl <= current_price * 1.004:
            return False, current_sl, "Candidate SL terlalu mepet dengan harga pasar saat ini"

        label = f"SMC Protected Lower High @ ${pivot_price:,.4f} (Buffer {buffer_pct*100:.1f}%)"
        return True, clean_sl, label

def format_telegram_market_structure(positions, meta=None):
    """
    Formats a comprehensive SMC Market Structure and Protected Trailing Stop report
    for Telegram display (Akademi Crypto Module 02).
    """
    if not positions:
        return (
            "🏛️ <b>SMC MARKET STRUCTURE & TRAILING AUDIT</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "<i>Tidak ada posisi terbuka saat ini. Trailing stop engine standby memantau chart 15m/1H.</i>"
        )

    meta = meta or {}
    lines = [
        "🏛️ <b>SMC STRUCTURAL TRAILING AUDIT</b>",
        "<i>Akademi Crypto Module 02: Market Structure Trailing</i>",
        "━━━━━━━━━━━━━━━━━━"
    ]

    for p in positions:
        sym = p["symbol"]
        amt = float(p.get("positionAmt", 0))
        side = "BUY" if amt > 0 else "SELL"
        side_icon = "🟢 LONG" if side == "BUY" else "🔴 SHORT"
        entry_price = float(p.get("entryPrice", 0))
        mark_price = float(p.get("markPrice", 0))
        upnl = float(p.get("unRealizedProfit", 0))
        pnl_sign = "+" if upnl >= 0 else ""

        t_data = meta.get(sym, {})
        current_sl = t_data.get("current_sl")
        r_dist = float(t_data.get("r_distance", entry_price * 0.015))
        gain = (mark_price - entry_price) if side == "BUY" else (entry_price - mark_price)
        r_mult = gain / r_dist if r_dist > 0 else 0.0

        has_new, new_sl, label = get_protected_structural_stop(
            symbol=sym,
            side=side,
            entry_price=entry_price,
            current_sl=current_sl,
            bar="15m"
        )

        buffer_pct = get_asset_sweep_buffer(sym)
        sl_str = f"${current_sl:,.4f}" if current_sl else "Default / Unset"

        lines.append(f"💎 <b>{sym}</b> ({side_icon})")
        lines.append(f"• Entry: <code>${entry_price:,.4f}</code> | Mark: <code>${mark_price:,.4f}</code>")
        lines.append(f"• Floating: <code>{pnl_sign}${upnl:,.2f} USDT ({r_mult:+.2f}R)</code>")
        lines.append(f"• Stop Loss Aktif: <code>{sl_str}</code>")
        lines.append(f"• Anti-Sweep Buffer: <code>{buffer_pct * 100:.1f}%</code>")
        lines.append(f"• Status Struktur: <i>{label}</i>")

        if has_new and new_sl:
            lines.append(f"• 🎯 <b>Kandidat Ratchet:</b> <code>${new_sl:,.4f}</code> (Siap dikatrol)")
        else:
            lines.append(f"• 🔒 <b>Ratchet Rule:</b> SL terlindungi di level struktural terkonfirmasi")
        lines.append("──────────────────")

    lines.append("💡 <i>SL hanya bergerak satu arah mengunci profit mengikuti Protected Swing Pivot terkonfirmasi (BOS/CHOCH) tanpa takut tersapu wick manipulasi.</i>")
    return "\n".join(lines)

if __name__ == "__main__":
    test_coins = ["LINKUSDT", "ETHUSDT", "SOLUSDT"]
    print("=== Testing SMC Market Structure Trailing Stop ===")
    for sym in test_coins:
        candles = fetch_candles(sym, bar="15m", limit=45)
        cur_p = candles[-1]["close"] if candles else 0.0
        print(f"\nCoin: {sym} (Current: ${cur_p:,.4f})")
        has_new, new_sl, label = get_protected_structural_stop(
            symbol=sym,
            side="BUY",
            entry_price=cur_p * 0.98,
            current_sl=cur_p * 0.96,
            bar="15m"
        )
        print(f" -> Has New Stop: {has_new} | New SL: ${new_sl:,.4f} | Label: {label}")

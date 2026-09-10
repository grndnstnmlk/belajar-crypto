"""
Institutional Candlestick Chart Snapshot Generator & Telegram Photo Dispatcher
Generates high-resolution, dark-mode TradingView-style chart snapshots with:
- Crisp Candlesticks (Green #00c087 / Red #ff4d6a)
- Institutional VWAP Curve
- Horizontal Entry, Stop Loss, and Take Profit levels with Risk/Reward shaded zones
- Sends visual chart snapshots directly to Telegram via official sendPhoto API.
"""

import json
import math
import os
import re
import ssl
import sys
import time
import urllib.request
import uuid
import warnings
from datetime import datetime

# Suppress Matplotlib font missing glyph user warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

# Headless backend for Matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
CHARTS_DIR = os.path.join(DATA_DIR, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

sys.path.insert(0, TOOLS_DIR)
import market_eyes
import telegram_notifier

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

def fetch_candles_for_snapshot(symbol="BTC", bar="1H", limit=45):
    """
    Fetches latest candles for snapshot from Binance via market_eyes.
    """
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")
    bar_param = "5M" if "5M" in bar.upper() else ("15M" if "15M" in bar.upper() else "1H")
    raw_candles = market_eyes.fetch_candles(sym_clean, bar=bar_param, limit=limit)
    if not raw_candles:
        return []

    parsed = []
    for c in raw_candles:
        parsed.append({
            "time": datetime.fromtimestamp(int(c[0]) / 1000).strftime("%H:%M"),
            "open": float(c[1]),
            "high": float(c[2]),
            "low": float(c[3]),
            "close": float(c[4]),
            "volume": float(c[5])
        })
    return parsed

def compute_vwap(candles):
    """Computes running session VWAP values."""
    cum_pv = 0.0
    cum_vol = 0.0
    vwap_values = []
    for c in candles:
        typical_price = (c["high"] + c["low"] + c["close"]) / 3.0
        v = max(c["volume"], 0.001)
        cum_pv += typical_price * v
        cum_vol += v
        vwap_values.append(cum_pv / cum_vol if cum_vol > 0 else typical_price)
    return vwap_values

def sanitize_chart_text(text):
    """
    Strips emojis and non-ASCII characters that lack glyphs in Matplotlib default fonts (DejaVu Sans)
    to eliminate missing glyph UserWarnings and prevent ugly tofu/box artifacts on the chart.
    """
    if not text:
        return ""
    # Strip any characters outside standard printable ASCII
    cleaned = re.sub(r"[^\x20-\x7E]", "", str(text))
    # Normalize multiple whitespaces
    return re.sub(r"\s+", " ", cleaned).strip()

def generate_trade_chart(symbol, side, entry_price, sl_price, tp_price, timeframe="1H", strategy_name="AI Quantitative Confluence"):
    """
    Generates a dark-mode TradingView style PNG chart with Entry, SL, TP lines.
    Returns the absolute path to the generated image file.
    """
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")
    pair_display = f"{sym_clean}/USDT"
    side_clean = side.upper()
    is_long = side_clean in ["BUY", "LONG"]

    candles = fetch_candles_for_snapshot(sym_clean, bar=timeframe, limit=45)
    if len(candles) < 15:
        # Fallback dummy candles if network unreachable
        base = entry_price if entry_price > 0 else 100.0
        candles = []
        for i in range(30):
            p = base * (1.0 + (i - 15) * 0.002)
            candles.append({"time": f"T{i}", "open": p*0.998, "high": p*1.004, "low": p*0.996, "close": p*1.001, "volume": 100})

    n = len(candles)
    indices = np.arange(n)

    opens = np.array([c["open"] for c in candles])
    highs = np.array([c["high"] for c in candles])
    lows = np.array([c["low"] for c in candles])
    closes = np.array([c["close"] for c in candles])
    vwap_vals = compute_vwap(candles)

    # Styling constants
    BG_COLOR = "#0B0E14"
    CARD_COLOR = "#121721"
    GRID_COLOR = "#1E2533"
    TEXT_COLOR = "#E2E8F0"
    DIM_TEXT = "#8B949E"
    BULL_COLOR = "#00C087"
    BEAR_COLOR = "#FF4D6A"
    ENTRY_COLOR = "#F59E0B"
    SL_COLOR = "#EF4444"
    TP_COLOR = "#10B981"
    VWAP_COLOR = "#38BDF8"

    fig, ax = plt.subplots(figsize=(12, 6.75), dpi=130, facecolor=BG_COLOR)
    ax.set_facecolor(CARD_COLOR)

    # Bullish vs Bearish masks
    bull_mask = closes >= opens
    bear_mask = ~bull_mask

    # Plot Wicks
    ax.vlines(indices[bull_mask], lows[bull_mask], highs[bull_mask], color=BULL_COLOR, linewidth=1.2, alpha=0.9)
    ax.vlines(indices[bear_mask], lows[bear_mask], highs[bear_mask], color=BEAR_COLOR, linewidth=1.2, alpha=0.9)

    # Plot Bodies
    body_width = 0.62
    ax.bar(indices[bull_mask], closes[bull_mask] - opens[bull_mask], bottom=opens[bull_mask], width=body_width, color=BULL_COLOR, alpha=0.95)
    ax.bar(indices[bear_mask], opens[bear_mask] - closes[bear_mask], bottom=closes[bear_mask], width=body_width, color=BEAR_COLOR, alpha=0.95)

    # Plot Institutional VWAP
    ax.plot(indices, vwap_vals, color=VWAP_COLOR, linewidth=1.4, linestyle="--", label="Inst. VWAP", alpha=0.85)

    # Price Limits for Y Axis
    all_prices = list(highs) + list(lows) + [entry_price]
    if sl_price and sl_price > 0:
        all_prices.append(sl_price)
    if tp_price and tp_price > 0:
        all_prices.append(tp_price)

    min_p = min(all_prices)
    max_p = max(all_prices)
    p_range = max(max_p - min_p, 0.0001)
    y_bottom = min_p - (p_range * 0.08)
    y_top = max_p + (p_range * 0.12)
    ax.set_ylim(y_bottom, y_top)
    ax.set_xlim(-1, n + 6)

    # Shaded Risk/Reward Zones
    if entry_price > 0 and sl_price and tp_price:
        if is_long:
            # Profit zone above entry to TP
            ax.axhspan(entry_price, tp_price, xmin=0.6, xmax=1.0, color=TP_COLOR, alpha=0.12)
            # Risk zone below entry to SL
            ax.axhspan(sl_price, entry_price, xmin=0.6, xmax=1.0, color=SL_COLOR, alpha=0.14)
        else:
            # Profit zone below entry to TP
            ax.axhspan(tp_price, entry_price, xmin=0.6, xmax=1.0, color=TP_COLOR, alpha=0.12)
            # Risk zone above entry to SL
            ax.axhspan(entry_price, sl_price, xmin=0.6, xmax=1.0, color=SL_COLOR, alpha=0.14)

    # Horizontal Order Reference Lines
    x_line_start = n - 20
    x_line_end = n + 5

    # Entry Line
    if entry_price > 0:
        ax.hlines(entry_price, x_line_start, x_line_end, colors=ENTRY_COLOR, linewidth=1.8, linestyle="-")
        ax.text(x_line_end, entry_price, f" ENTRY ${entry_price:,.4f}", color=ENTRY_COLOR, fontsize=9.5, fontweight="bold", verticalalignment="center")

    # Stop Loss Line
    if sl_price and sl_price > 0:
        ax.hlines(sl_price, x_line_start, x_line_end, colors=SL_COLOR, linewidth=1.8, linestyle="-.")
        ax.text(x_line_end, sl_price, f" SL ${sl_price:,.4f}", color=SL_COLOR, fontsize=9.5, fontweight="bold", verticalalignment="center")

    # Take Profit Line
    if tp_price and tp_price > 0:
        ax.hlines(tp_price, x_line_start, x_line_end, colors=TP_COLOR, linewidth=1.8, linestyle="-.")
        ax.text(x_line_end, tp_price, f" TP ${tp_price:,.4f}", color=TP_COLOR, fontsize=9.5, fontweight="bold", verticalalignment="center")

    # Formatting Grids and Spines
    ax.grid(True, color=GRID_COLOR, linestyle=":", linewidth=0.6, alpha=0.6)
    for spine in ax.spines.values():
        spine.set_color(GRID_COLOR)

    # X-Axis Ticks (Times)
    step = max(1, n // 7)
    tick_pos = indices[::step]
    tick_labels = [candles[i]["time"] for i in tick_pos]
    ax.set_xticks(tick_pos)
    ax.set_xticklabels(tick_labels, color=DIM_TEXT, fontsize=8.5)
    ax.tick_params(colors=DIM_TEXT, which="both")
    ax.yaxis.tick_right()
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("$%g"))

    # Title & Metadata
    side_tag = "LONG [BUY]" if is_long else "SHORT [SELL]"
    r_dist = abs(entry_price - sl_price) if (sl_price and sl_price > 0) else 1.0
    reward_dist = abs(tp_price - entry_price) if (tp_price and tp_price > 0) else 1.0
    rr_ratio = (reward_dist / r_dist) if r_dist > 0 else 2.5

    clean_strategy = sanitize_chart_text(strategy_name) or "AI Quantitative Confluence"
    title_text = f"{pair_display} ({timeframe}) - {side_tag} (R:R 1:{rr_ratio:.2f})"
    clean_title = sanitize_chart_text(title_text)
    ax.set_title(clean_title, color=TEXT_COLOR, fontsize=13, fontweight="bold", pad=12, loc="left")

    # Subtitle / Strategy Tag
    ax.text(0.0, 1.02, f"Strategy: {clean_strategy} | Powered by Akademi Crypto AI Desk",
            transform=ax.transAxes, color=DIM_TEXT, fontsize=8.5, verticalalignment="bottom")

    # Brand Watermark in bottom right
    ax.text(0.98, 0.03, "AKADEMI CRYPTO MISSION CONTROL", transform=ax.transAxes,
            color=DIM_TEXT, fontsize=8, alpha=0.35, horizontalalignment="right")

    plt.tight_layout()

    # Save to disk
    timestamp_tag = int(time.time())
    img_filename = f"chart_{sym_clean}_{side_clean}_{timestamp_tag}.png"
    img_path = os.path.join(CHARTS_DIR, img_filename)
    fig.savefig(img_path, facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)

    return img_path

def send_telegram_photo(photo_path, caption=None, chat_id=None):
    """
    Sends a photo to Telegram using multipart/form-data.
    """
    token, default_chat_id = telegram_notifier.get_telegram_config()
    target_chat = chat_id or default_chat_id

    if not token or not target_chat:
        print("[Telegram Photo Warning] Token or Chat ID not configured.")
        return None

    if not os.path.exists(photo_path):
        print(f"[Telegram Photo Warning] Photo file not found: {photo_path}")
        return None

    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"

    # Read binary photo
    with open(photo_path, "rb") as f:
        file_bytes = f.read()

    filename = os.path.basename(photo_path)

    # Build multipart body
    body = bytearray()

    # Field: chat_id
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'.encode("utf-8"))
    body.extend(f"{target_chat}\r\n".encode("utf-8"))

    # Field: caption (Strict 1024 char limit for Telegram sendPhoto)
    if caption:
        safe_caption = caption
        if len(safe_caption) > 1020:
            safe_caption = safe_caption[:1015] + "..."
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="caption"\r\n\r\n'.encode("utf-8"))
        body.extend(f"{safe_caption}\r\n".encode("utf-8"))

        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="parse_mode"\r\n\r\n'.encode("utf-8"))
        body.extend(b"HTML\r\n")

    # Field: photo file
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="photo"; filename="{filename}"\r\n'.encode("utf-8"))
    body.extend(b"Content-Type: image/png\r\n\r\n")
    body.extend(file_bytes)
    body.extend(b"\r\n")

    # End boundary
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    headers = {
        "User-Agent": "TelegramTradingDeskBot/1.0",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body))
    }

    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=18, context=SSL_CTX) as resp:
            raw_res = resp.read().decode("utf-8")
            return json.loads(raw_res)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        print(f"[Telegram Photo Warning] sendPhoto failed ({e.code}): {err_body}. Retrying photo without HTML parse_mode...")
        try:
            # Fallback 1: Resend photo with pure clean plain text (no parse_mode)
            clean_caption = re.sub(r"<[^>]+>", "", caption)[:1000] if caption else None
            fb_body = bytearray()
            fb_body.extend(f"--{boundary}\r\n".encode("utf-8"))
            fb_body.extend(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'.encode("utf-8"))
            fb_body.extend(f"{target_chat}\r\n".encode("utf-8"))
            if clean_caption:
                fb_body.extend(f"--{boundary}\r\n".encode("utf-8"))
                fb_body.extend(f'Content-Disposition: form-data; name="caption"\r\n\r\n'.encode("utf-8"))
                fb_body.extend(f"{clean_caption}\r\n".encode("utf-8"))
            fb_body.extend(f"--{boundary}\r\n".encode("utf-8"))
            fb_body.extend(f'Content-Disposition: form-data; name="photo"; filename="{filename}"\r\n'.encode("utf-8"))
            fb_body.extend(b"Content-Type: image/png\r\n\r\n")
            fb_body.extend(file_bytes)
            fb_body.extend(b"\r\n")
            fb_body.extend(f"--{boundary}--\r\n".encode("utf-8"))
            
            fb_headers = {
                "User-Agent": "TelegramTradingDeskBot/1.0",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(fb_body))
            }
            req_fb = urllib.request.Request(url, data=fb_body, headers=fb_headers, method="POST")
            with urllib.request.urlopen(req_fb, timeout=18, context=SSL_CTX) as fb_resp:
                return json.loads(fb_resp.read().decode("utf-8"))
        except Exception as fb_err:
            print(f"[Telegram Photo Error] Fallback sendPhoto failed: {fb_err}")
            if caption:
                telegram_notifier.send_telegram_msg(caption, chat_id_override=target_chat)
            return None
    except Exception as e:
        print(f"[Telegram Photo Error] Failed to upload chart image: {e}")
        # Fallback to plain text caption
        if caption:
            telegram_notifier.send_telegram_msg(caption, chat_id_override=target_chat)
        return None

if __name__ == "__main__":
    print("\n=======================================================")
    print("       📸 CHART SNAPSHOT GENERATOR SELF-TEST")
    print("=======================================================")
    test_path = generate_trade_chart(
        symbol="BTC",
        side="LONG",
        entry_price=79686.0,
        sl_price=78492.0,
        tp_price=83443.0,
        timeframe="1H",
        strategy_name="3-Touch Support + 4H Trend Alignment"
    )
    print(f"✅ Generated Chart PNG: {test_path}")
    print(f"Ukuran File: {os.path.getsize(test_path):,} bytes")
    
    # Try sending to Telegram
    caption = (
        "📸 <b>[TEST SNAPSHOT CHART] BTC/USDT LONG</b>\n"
        "• Entry : <code>$79,686.00</code>\n"
        "• SL    : <code>$78,492.00</code>\n"
        "• TP    : <code>$83,443.00</code>\n"
        "• R:R   : <code>1 : 3.15</code>\n"
        "<i>Chart visual terkirim otomatis ke Telegram!</i>"
    )
    res = send_telegram_photo(test_path, caption=caption)
    if res and res.get("ok"):
        print("🚀 Foto Chart Visual BERHASIL terkirim ke Telegram!")
    else:
        print(f"Telegram response: {res}")
    print("=======================================================\n")

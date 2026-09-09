"""
Telegram Real-Time Alert & Two-Way Remote Control Notifier
Bridges Autonomous Binance Trading Desk with Telegram Bot API.
Provides instant trade notifications, PnL summaries, and remote command listener.
"""

import html
import json
import os
import re
import ssl
import sys
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
STATE_FILE = os.path.join(DATA_DIR, "desk_state.json")
ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")

# SSL Context to prevent Windows regional certificate verification blocks
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "TelegramTradingDeskBot/1.0",
    "Content-Type": "application/x-www-form-urlencoded"
}

def parse_env_file():
    env_vars = {}
    if os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_vars[k.strip()] = v.strip().strip('"').strip("'")
        except Exception:
            pass
    return env_vars

def get_telegram_config():
    env = parse_env_file()
    token = env.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = env.get("TELEGRAM_CHAT_ID", "").strip()
    return token, chat_id

def load_desk_state():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"paused": False, "mode": "SWING", "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

def save_desk_state(state):
    os.makedirs(DATA_DIR, exist_ok=True)
    state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if "mode" not in state:
        state["mode"] = "SWING"
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"[Telegram Notifier] Error saving desk state: {e}")

def is_desk_paused():
    state = load_desk_state()
    return state.get("paused", False)

def get_desk_mode():
    state = load_desk_state()
    return state.get("mode", "HYBRID")

MAIN_KEYBOARD = {
    "keyboard": [
        [{"text": "📊 Status Desk"}, {"text": "💰 Cek PnL"}, {"text": "📋 Executive Briefing"}],
        [{"text": "📖 Jurnal & Analytics"}, {"text": "🛡️ Directional Heat"}],
        [{"text": "🧭 Market Compass"}, {"text": "🏛️ SMC Trailing"}],
        [{"text": "🧲 Depth & Liquidity"}, {"text": "🏛️ Coinbase Premium"}],
        [{"text": "🌊 Sentimen Coinalyze"}, {"text": "📈 Minta Chart BTC"}],
        [{"text": "🧬 Status Genome"}, {"text": "🤖 Tanya AI Officer"}],
        [{"text": "🎯 Mode Swing (Profit Besar)"}],
        [{"text": "🤖 Mode Hybrid (Auto)"}, {"text": "⚡ Mode Scalp (5m)"}],
        [{"text": "📰 Kalender Berita"}, {"text": "🚨 Tutup Semua Posisi"}],
        [{"text": "⏸️ Jeda Bot"}, {"text": "▶️ Lanjutkan Bot"}],
        [{"text": "❓ Panduan Bantuan"}]
    ],
    "resize_keyboard": True,
    "is_persistent": True
}

def setup_bot_commands():
    """
    Registers official slash commands in Telegram so the blue Menu button appears in the input bar.
    """
    token, _ = get_telegram_config()
    if not token:
        return
    url = f"https://api.telegram.org/bot{token}/setMyCommands"
    commands = [
        {"command": "status", "description": "📊 Cek saldo & posisi aktif"},
        {"command": "report", "description": "📋 Laporan eksekutif harian (24H Quant Briefing)"},
        {"command": "pnl", "description": "💰 Detail profit & loss real-time"},
        {"command": "ask", "description": "🤖 Konsultasi & tanya AI Quant Officer"},
        {"command": "trailing", "description": "🏛️ SMC Structural Trailing Stop & Swing Pivot (Module 02)"},
        {"command": "journal", "description": "📖 Jurnal Trading & Performance Scorecard (Module 03)"},
        {"command": "analytics", "description": "📊 Win Rate, Profit Factor & Ekspektansi Matematika"},
        {"command": "heat", "description": "🛡️ Directional Heat & Korelasi Portofolio"},
        {"command": "compass", "description": "🧭 BTC.D & USDT.D Market Flow Compass (Akademi Crypto)"},
        {"command": "heatmap", "description": "🧲 Order Book Depth & Magnet Likuidasi (/heatmap BTC)"},
        {"command": "depth", "description": "📊 DOM Imbalance Ratio & Order Book Wall"},
        {"command": "chart", "description": "📈 Visual snapshot chart candlestick (cth: /chart BTC)"},
        {"command": "rejection", "description": "🕯️ Scan ICT Rejection Block & 50% Mean Threshold"},
        {"command": "coinalyze", "description": "🌊 Sentimen Open Interest, Likuidasi & L/S Ratio"},
        {"command": "coinbase", "description": "🏛️ Coinbase Premium Index (Arus Wall Street vs Ritel)"},
        {"command": "genome", "description": "🧬 Status AI Quant Genome & evolusi"},
        {"command": "evolve", "description": "⚡ Jalankan autopsi & mutasi genetika sekarang"},
        {"command": "news", "description": "📰 Kalender berita makro AS (High-Impact)"},
        {"command": "pause", "description": "⏸️ Jeda eksekusi order autopilot"},
        {"command": "resume", "description": "▶️ Lanjutkan autopilot"},
        {"command": "close", "description": "🔴 Pilih koin untuk ditutup"},
        {"command": "closeall", "description": "🚨 Tutup semua posisi sekaligus"},
        {"command": "help", "description": "❓ Panduan menu perintah"}
    ]
    try:
        data = urllib.parse.urlencode({"commands": json.dumps(commands)}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=HEADERS, method="POST")
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"[Telegram Notifier] Failed to set bot commands: {e}")
        return None

def send_telegram_msg(text, parse_mode="HTML", chat_id_override=None, reply_markup=None):
    """
    Sends a message via Telegram Bot API with optional ReplyKeyboardMarkup or InlineKeyboardMarkup.
    """
    token, default_chat_id = get_telegram_config()
    target_chat = chat_id_override or default_chat_id

    if not token or not target_chat:
        return None

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": text,
        "disable_web_page_preview": "true"
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup is not None:
        payload["reply_markup"] = json.dumps(reply_markup) if isinstance(reply_markup, dict) else reply_markup

    try:
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=HEADERS, method="POST")
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body)
    except Exception as e:
        print(f"[Telegram Notifier] Failed to send message: {e}")
        return None

# Alias for broadcast
send_telegram_broadcast = send_telegram_msg

def notify_trade_opened(trade, quantity, risk_budget_usd, is_demo=True):
    """
    Sends rich notification with visual candlestick chart when a new position is opened on Binance Futures.
    """
    symbol = trade.get("symbol", "UNKNOWN")
    side = trade.get("side", "BUY")
    side_icon = "🟢 LONG" if side.upper() == "BUY" else "🔴 SHORT"
    price = float(trade.get("price", 0))
    sl = float(trade.get("sl", 0))
    tp = float(trade.get("tp", 0))
    rr = float(trade.get("rr", 0))
    reason = html.escape(trade.get("reason", "Multi-Agent Consensus"))
    mode_text = "🟡 DEMO TRADING (Testnet)" if is_demo else "🔴 LIVE TRADING (Real Money)"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conf_score = trade.get("confluence_score")
    conf_grade = trade.get("confluence_grade")
    conf_line = f"⭐ <b>Konfluensi/Akurasi:</b> <code>{conf_score}% [{conf_grade}]</code>\n" if conf_score else ""

    rb_setup = trade.get("rejection_block_setup")
    rb_line = ""
    if rb_setup:
        mt_val = rb_setup.get("mean_threshold", 0)
        state_val = rb_setup.get("retest_state", "Retest")
        rb_line = f"🕯️ <b>ICT Rejection Block:</b> <code>MT 50%: ${mt_val:,.4f} ({state_val})</code>\n"

    ai_audit = trade.get("ai_audit")
    ai_line = ""
    if ai_audit:
        dec = ai_audit.get("decision", "APPROVED")
        conf = ai_audit.get("confidence", 85)
        thesis = html.escape(ai_audit.get("thesis", ""))
        ai_line = f"🤖 <b>AI Officer Review:</b> <code>{dec} ({conf}%)</code>\n   <i>\"{thesis}\"</i>\n"
        deb = ai_audit.get("adversarial_debate")
        if deb:
            winner = deb.get("winner", "BULL")
            bull_s = deb.get("bull_score", 0)
            bear_s = deb.get("bear_score", 0)
            ai_line += f"🐂 vs 🐻 <b>Tauric Debate:</b> <code>Bull {bull_s}% vs Bear {bear_s}% [{winner}]</code>\n"

        tri = ai_audit.get("tri_perspective_risk")
        if tri:
            fm = tri.get("fund_manager", {})
            v = fm.get("verdict", "APPROVED")
            sc = float(fm.get("allocated_risk_scale", 1.0))
            agg = tri.get("aggressive", {}).get("score", 0)
            neu = tri.get("neutral", {}).get("score", 0)
            con = tri.get("conservative", {}).get("score", 0)
            ai_line += f"⚖️ <b>Tri-Risk Balance:</b> <code>🟢 Agg {agg}% | 🔵 Neu {neu}% | 🔴 Con {con}% [{v} - {sc:.2f}x]</code>\n"

    is_scalp = trade.get("is_scalp", False)
    header_title = "⚡ <b>EKSEKUSI 5m FAST SCALP - BINANCE FUTURES</b>" if is_scalp else "🚀 <b>EKSEKUSI ORDER BINANCE FUTURES</b>"
    scalp_badge = "⚡ <b>Tipe Setup:</b> <code>5m Micro Scalp (Target: 15-30m | BE: +0.60R)</code>\n" if is_scalp else ""

    msg = (
        f"{header_title}\n"
        f"<i>Mode: {mode_text}</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>Simbol:</b> <code>{symbol}</code>\n"
        f"🧭 <b>Arah:</b> <b>{side_icon} (5x Leverage)</b>\n"
        f"{scalp_badge}"
        f"{conf_line}"
        f"{rb_line}"
        f"{ai_line}"
        f"🎯 <b>Strategi:</b> {reason}\n"
        f"💵 <b>Entry Price:</b> <code>${price:,.4f}</code>\n"
        f"🛑 <b>Stop Loss:</b> <code>${sl:,.4f}</code>\n"
        f"🎯 <b>Take Profit:</b> <code>${tp:,.4f}</code>\n"
        f"⚖️ <b>Risk:Reward:</b> <code>1 : {rr:.2f}</code>\n"
        f"📦 <b>Ukuran Posisi:</b> <code>{quantity} {trade.get('base', '')}</code>\n"
        f"🛡️ <b>Risk Budget:</b> <code>${risk_budget_usd:,.2f}</code>\n"
        f"🕒 <b>Waktu:</b> {timestamp}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<i>Gunakan /status atau /pnl untuk memantau dari HP.</i>"
    )

    # 1. Attempt to generate and send visual Candlestick Chart Snapshot
    try:
        import chart_snapshot
        tf = "5m" if (is_scalp or "SCALP" in reason.upper() or "5M" in reason.upper()) else "1H"
        chart_file = chart_snapshot.generate_trade_chart(
            symbol=symbol,
            side=side,
            entry_price=price,
            sl_price=sl,
            tp_price=tp,
            timeframe=tf,
            strategy_name=reason[:40]
        )
        if chart_file and os.path.exists(chart_file):
            photo_res = chart_snapshot.send_telegram_photo(chart_file, caption=msg)
            if photo_res and photo_res.get("ok"):
                return photo_res
    except Exception as e:
        print(f"[Telegram Notifier Warning] Chart snapshot dispatch fallback to text: {e}")

    return send_telegram_msg(msg)

def notify_ai_officer_veto(trade, ai_audit):
    """
    Sends notification when AI Senior Quant Officer vetoes an otherwise technically valid trade setup.
    """
    sym = trade.get("symbol", "UNKNOWN")
    side = trade.get("side", "BUY")
    side_icon = "🟢 LONG" if side.upper() == "BUY" else "🔴 SHORT"
    conf = ai_audit.get("confidence", 90)
    thesis = html.escape(ai_audit.get("thesis", "Hidden structural risk detected"))
    risks = "\n".join([f"• <i>{html.escape(r)}</i>" for r in ai_audit.get("key_risks", [])])
    provider = ai_audit.get("provider", "AI Senior Quant Officer")

    deb = ai_audit.get("adversarial_debate")
    debate_section = ""
    if deb:
        winner = deb.get("winner", "BEAR")
        bull_s = deb.get("bull_score", 0)
        bear_s = deb.get("bear_score", 0)
        synthesis = html.escape(deb.get("arbiter_synthesis", ""))
        debate_section = (
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🐂 vs 🐻 <b>TAURIC ADVERSARIAL DEBATE:</b>\n"
            f"• Skor: <b>Bull {bull_s}%</b> vs <b>Bear {bear_s}%</b> [{winner}]\n"
            f"• <b>Putusan Arbiter:</b> <i>{synthesis}</i>\n"
        )

    tri = ai_audit.get("tri_perspective_risk")
    tri_section = ""
    if tri:
        fm = tri.get("fund_manager", {})
        agg = tri.get("aggressive", {}).get("score", 0)
        neu = tri.get("neutral", {}).get("score", 0)
        con = tri.get("conservative", {}).get("score", 0)
        tri_syn = html.escape(fm.get("synthesis", ""))
        tri_section = (
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⚖️ <b>TAURIC TRI-PERSPECTIVE RISK TEAM:</b>\n"
            f"• Skor: 🟢 <b>Agg {agg}%</b> | 🔵 <b>Neu {neu}%</b> | 🔴 <b>Con {con}%</b>\n"
            f"• <b>Fund Manager:</b> <i>{tri_syn}</i>\n"
        )

    msg = (
        f"🛡️ <b>AI QUANT OFFICER — SETUP DIVETO!</b>\n"
        f"<i>Reviewer: {html.escape(provider)}</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>Simbol:</b> <code>{sym}</code> ({side_icon})\n"
        f"🛑 <b>Keputusan AI:</b> <code>VETO ({conf}% Confidence)</code>\n"
        f"📝 <b>Alasan Veto:</b>\n{thesis}\n\n"
        f"⚠️ <b>Faktor Risiko Utama:</b>\n{risks}\n"
        f"{debate_section}"
        f"{tri_section}"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💡 <i>Modal terlindungi! Autopilot membatalkan eksekusi order ini untuk mencegah potensi jebakan manipulasi wick/dump.</i>"
    )
    return send_telegram_msg(msg)

def notify_trade_closed(symbol, pnl_usd, exit_reason="Manual/Target Hit", is_demo=True,
                        net_pnl_usd=None, commission_usd=0.0, entry_price=0.0, exit_price=0.0,
                        qty=0.0, side="BUY", close_time=None):
    """
    Sends rich, verified notification when a position is closed on Binance Futures.
    Includes exact Realized PnL, Net PnL after commission, Entry/Exit prices, and ROI %.
    """
    mode_text = "🟡 DEMO (Futures Testnet)" if is_demo else "🔴 LIVE (Real Money)"
    side_icon = "🟢 LONG" if side.upper() in ["BUY", "LONG"] else "🔴 SHORT"

    if pnl_usd > 0.005:
        pnl_icon = "🟢 PROFIT"
    elif pnl_usd < -0.005:
        pnl_icon = "🔴 LOSS"
    else:
        pnl_icon = "⚪ BREAKEVEN"

    pnl_sign = "+" if pnl_usd >= 0 else ""
    net_val = net_pnl_usd if net_pnl_usd is not None else (pnl_usd - commission_usd)
    net_sign = "+" if net_val >= 0 else ""
    time_str = close_time or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    lines = [
        f"🏁 <b>POSISI DITUTUP - BINANCE FUTURES</b>",
        f"<i>Mode: {mode_text}</i>",
        f"━━━━━━━━━━━━━━━━━━",
        f"💎 <b>Simbol:</b> <code>{symbol}</code> ({side_icon})",
        f"📊 <b>Hasil Akhir:</b> <b>{pnl_icon}</b>",
        f"💵 <b>Realisasi PnL (Gross):</b> <code>{pnl_sign}${pnl_usd:,.2f} USDT</code>"
    ]

    if commission_usd > 0:
        lines.append(f"💸 <b>Biaya Fee Trading:</b> <code>-${commission_usd:,.2f} USDT</code>")
        lines.append(f"💰 <b>Net Realisasi PnL:</b> <code>{net_sign}${net_val:,.2f} USDT</code>")

    if entry_price > 0 and exit_price > 0:
        lines.append(f"📈 <b>Harga Entry:</b> <code>${entry_price:,.4f}</code>")
        lines.append(f"📉 <b>Harga Exit:</b> <code>${exit_price:,.4f}</code>")
        if side.upper() in ["BUY", "LONG"]:
            pct_move = ((exit_price - entry_price) / entry_price) * 100.0
        else:
            pct_move = ((entry_price - exit_price) / entry_price) * 100.0
        lines.append(f"🎯 <b>Pergerakan Harga:</b> <code>{'+' if pct_move>=0 else ''}{pct_move:.2f}%</code>")

    if qty > 0:
        lines.append(f"📦 <b>Kuantitas Posisi:</b> <code>{qty:,.4f} {symbol.replace('USDT', '')}</code>")

    lines.append(f"📌 <b>Alasan Keluar:</b> {html.escape(str(exit_reason))}")
    lines.append(f"🕒 <b>Waktu Eksekusi:</b> <code>{time_str}</code>")
    lines.append(f"━━━━━━━━━━━━━━━━━━")

    msg = "\n".join(lines)
    return send_telegram_msg(msg)

def notify_breakeven_locked(symbol, side, entry_price, be_price, current_pnl, is_demo=True):
    """
    Sends notification when a position achieves +1R profit and SL is moved to Breakeven (+fee).
    """
    mode_text = "🟡 DEMO" if is_demo else "🔴 LIVE"
    side_icon = "🟢 LONG" if side.upper() in ["BUY", "LONG"] else "🔴 SHORT"
    msg = (
        f"🛡️ <b>BREAKEVEN AUTO-LOCK DIAKTIFKAN!</b>\n"
        f"<i>Mode: {mode_text}</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>Simbol:</b> <code>{symbol}</code>\n"
        f"🧭 <b>Posisi:</b> {side_icon}\n"
        f"💵 <b>Harga Entry:</b> <code>${entry_price:,.4f}</code>\n"
        f"🛑 <b>Stop Loss Baru (BE):</b> <code>${be_price:,.4f}</code>\n"
        f"📈 <b>Floating Profit:</b> <code>+${current_pnl:,.2f} USDT (+1.0R+)</code>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎉 <i>Posisi Anda sekarang 100% BEBAS RISIKO (Free Roll). Modal terproteksi sempurna!</i>"
    )
    return send_telegram_msg(msg)

def notify_partial_tp_taken(symbol, side, mark_price, closed_qty, pnl_usd, remaining_qty, be_price, r_multiple=1.0, is_demo=True):
    """
    Sends rich notification when Partial Take Profit (TP1 Scale-out @ +2.0R) is triggered.
    Synthesized from Akademi Crypto Module 03 (Money Management).
    """
    mode_text = "🟡 DEMO" if is_demo else "🔴 LIVE"
    side_icon = "🟢 LONG" if side.upper() in ["BUY", "LONG"] else "🔴 SHORT"
    msg = (
        f"🎯 <b>SCALE-OUT TP1 SECURED (50% LIQUIDATED @ +{r_multiple:.2f}R)!</b>\n"
        f"<i>Mode: {mode_text} | Akademi Crypto Module 03</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>Simbol:</b> <code>{symbol}</code> ({side_icon})\n"
        f"📈 <b>Capaian Target R:R:</b> <code>+{r_multiple:.2f}R</code>\n"
        f"💵 <b>Harga Eksekusi:</b> <code>${mark_price:,.4f}</code>\n"
        f"📦 <b>Posisi Dicairkan (50%):</b> <code>{closed_qty} lot</code>\n"
        f"💰 <b>Cuan Riil Masuk Dompet:</b> <b>+${pnl_usd:,.2f} USDT</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ <b>STATUS RUNNER (SISA 50% POSISI):</b>\n"
        f"• Sisa Lot Berjalan: <code>{remaining_qty} lot</code>\n"
        f"• Stop Loss Terkunci (BE): <code>${be_price:,.4f}</code>\n"
        f"• Mesin Pemandu: <b>SMC Structural Trailing Stop</b>\n"
        f"🎉 <i>Keuntungan separuh sudah diamankan! Sisa trade kini 100% BEBAS RISIKO (Risk-Free) mengejar tren mega-rally (1:4 hingga 1:8+)!</i>"
    )
    return send_telegram_msg(msg)

def notify_capital_shield_activated(symbol, side, mark_price, new_sl_price, r_multiple=0.7, is_demo=True):
    """
    Sends notification when Capital Preservation Shield tightens SL to -0.2R after reaching +0.7R.
    """
    mode_text = "🟡 DEMO" if is_demo else "🔴 LIVE"
    side_icon = "🟢 LONG" if side.upper() in ["BUY", "LONG"] else "🔴 SHORT"
    msg = (
        f"🛡️ <b>CAPITAL PRESERVATION SHIELD AKTIF!</b>\n"
        f"<i>Mode: {mode_text}</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>Simbol:</b> <code>{symbol}</code> ({side_icon})\n"
        f"📈 <b>Floating Profit:</b> <code>+{r_multiple:.2f}R</code> (Harga: <code>${mark_price:,.4f}</code>)\n"
        f"🛑 <b>SL Dinaikkan Agresif ke:</b> <code>${new_sl_price:,.4f} (-0.2R Buffer)</code>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💡 <i>Trade sudah hijau. Stop Loss dinaikkan untuk memotong potensi kerugian hingga 80% jika pasar tiba-tiba berbalik arah!</i>"
    )
    return send_telegram_msg(msg)

def notify_trailing_stop_stepped(symbol, side, locked_r, new_sl_price, current_pnl, is_demo=True):
    """
    Sends notification when Trailing Stop steps up/down to lock in profit.
    """
    mode_text = "🟡 DEMO" if is_demo else "🔴 LIVE"
    side_icon = "🟢 LONG" if side.upper() in ["BUY", "LONG"] else "🔴 SHORT"
    msg = (
        f"🎯 <b>TRAILING STOP DIKATROL NAIK!</b>\n"
        f"<i>Mode: {mode_text}</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>Simbol:</b> <code>{symbol}</code>\n"
        f"🧭 <b>Posisi:</b> {side_icon}\n"
        f"🛑 <b>Stop Loss Baru:</b> <code>${new_sl_price:,.4f}</code>\n"
        f"🔒 <b>Profit Terkunci:</b> <code>Minimal +{locked_r:.1f}R Terjamin</code>\n"
        f"📈 <b>Floating PnL:</b> <code>+${current_pnl:,.2f} USDT</code>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🚀 <i>Keuntungan diamankan mengikuti arah tren institusional!</i>"
    )
    return send_telegram_msg(msg)

def notify_structural_trailing_updated(symbol, side, mark_price, new_sl_price, structure_label, r_multiple=0.0, current_pnl=0.0, is_demo=True):
    """
    Sends notification when SMC Structural Trailing Stop engine updates SL behind confirmed
    Higher Lows (Long) or Lower Highs (Short) following Market Structure Breaks (BOS/CHOCH).
    """
    mode_text = "🟡 DEMO" if is_demo else "🔴 LIVE"
    side_icon = "🟢 LONG" if side.upper() in ["BUY", "LONG"] else "🔴 SHORT"
    r_str = f"+{r_multiple:.2f}R" if r_multiple >= 0 else f"{r_multiple:.2f}R"
    pnl_sign = "+" if current_pnl >= 0 else ""
    msg = (
        f"🏛️ <b>SMC STRUCTURAL TRAILING STOP DIKATROL!</b>\n"
        f"<i>Mode: {mode_text} | Akademi Crypto Module 02</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>Simbol:</b> <code>{symbol}</code> ({side_icon})\n"
        f"🧭 <b>Struktur Terkonfirmasi:</b> <b>{html.escape(structure_label)}</b>\n"
        f"💵 <b>Harga Pasar:</b> <code>${mark_price:,.4f}</code>\n"
        f"🛑 <b>Stop Loss Baru (Structural):</b> <code>${new_sl_price:,.4f}</code>\n"
        f"🔒 <b>Floating Performance:</b> <code>{r_str} ({pnl_sign}${current_pnl:,.2f} USDT)</code>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ <i>SL dipindah secara otomatis ke bawah Protected Swing Pivot dengan anti-sweep liquidity hunt buffer. Modal & profit terlindungi dari manipulasi wick!</i>"
    )
def notify_ai_early_tp(symbol, side, mark_price, pnl_usd, r_multiple, thesis, is_demo=True):
    """
    Sends rich alert when AI Adaptive Profit Harvester executes an early market take profit
    to lock in gains before momentum exhausts and reverses.
    """
    mode_text = "🟡 DEMO" if is_demo else "🔴 LIVE"
    side_icon = "🟢 LONG" if side.upper() in ["BUY", "LONG"] else "🔴 SHORT"
    pnl_sign = "+" if pnl_usd >= 0 else ""
    msg = (
        f"🎯 <b>AI ADAPTIVE EARLY TAKE PROFIT!</b>\n"
        f"<i>Mode: {mode_text} | AI Sentinel Profit Harvester</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>Simbol:</b> <code>{symbol}</code> ({side_icon})\n"
        f"💰 <b>Cuan Kas Terkunci:</b> <b>{pnl_sign}${pnl_usd:,.2f} USDT (+{r_multiple:.2f}R)</b>\n"
        f"💵 <b>Harga Exit:</b> <code>${mark_price:,.4f}</code>\n"
        f"🤖 <b>Analisa AI Sentinel:</b>\n"
        f"<i>\"{html.escape(thesis)}\"</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎉 <i>Trade diselesaikan otomatis dengan PROFIT! Menghindari risiko berbalik arah terkena Stop Loss.</i>"
    )
    return send_telegram_msg(msg)

def notify_ai_profit_lock(symbol, side, mark_price, new_sl_price, current_pnl, r_multiple, is_demo=True):
    """
    Sends notification when AI tightens Stop Loss directly into the profit zone (+0.25R above entry).
    """
    mode_text = "🟡 DEMO" if is_demo else "🔴 LIVE"
    side_icon = "🟢 LONG" if side.upper() in ["BUY", "LONG"] else "🔴 SHORT"
    pnl_sign = "+" if current_pnl >= 0 else ""
    msg = (
        f"🛡️ <b>AI GREEN-EXIT PROFIT LOCK!</b>\n"
        f"<i>Mode: {mode_text} | AI Sentinel Profit Guard</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>Simbol:</b> <code>{symbol}</code> ({side_icon})\n"
        f"📈 <b>Floating Profit:</b> <code>{pnl_sign}${current_pnl:,.2f} USDT (+{r_multiple:.2f}R)</code>\n"
        f"🛑 <b>Stop Loss Dikunci ke Profit:</b> <code>${new_sl_price:,.4f}</code>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔒 <i>Garansi Green Exit! Posisi sekarang memiliki jaminan keluar dalam keadaan UNTUNG jika harga tersenggol balik.</i>"
    )
    return send_telegram_msg(msg)

def notify_pnl_summary(balance_usd, active_positions, is_demo=True):
    """
    Sends a periodic summary of all open positions and floating PnL.
    """
    mode_text = "🟡 DEMO (Testnet)" if is_demo else "🔴 LIVE"
    total_upnl = sum(float(p.get("unRealizedProfit", 0)) for p in active_positions)
    upnl_sign = "+" if total_upnl >= 0 else ""

    lines = [
        f"📊 <b>RINGKASAN PORTOFOLIO TRADING DESK</b>",
        f"<i>Mode: {mode_text}</i>",
        f"━━━━━━━━━━━━━━━━━━",
        f"💰 <b>Total Balance:</b> <code>${balance_usd:,.2f} USDT</code>",
        f"📈 <b>Floating PnL:</b> <code>{upnl_sign}${total_upnl:,.2f} USDT</code>",
        f"📂 <b>Posisi Terbuka:</b> <code>{len(active_positions)} posisi</code>\n"
    ]

    if active_positions:
        for p in active_positions:
            amt = float(p.get("positionAmt", 0))
            side_badge = "🟢 LONG" if amt > 0 else "🔴 SHORT"
            upnl = float(p.get("unRealizedProfit", 0))
            p_sign = "+" if upnl >= 0 else ""
            lines.append(
                f"• <b>{p['symbol']}</b> {side_badge}\n"
                f"  Entry: <code>${float(p.get('entryPrice', 0)):,.4f}</code> | "
                f"PnL: <code>{p_sign}${upnl:,.2f}</code>"
            )
    else:
        lines.append("<i>Tidak ada posisi terbuka saat ini.</i>")

    lines.append(f"\n🕒 <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>")
    return send_telegram_msg("\n".join(lines))

def notify_pending_board_approval(setup, ticket, reasons):
    """
    Sends urgent Telegram alert with inline buttons when a trade setup is escalated to Human Board.
    """
    t_id = ticket.get("ticket_id", "TCK-UNKNOWN") if ticket else "TCK-UNKNOWN"
    sym = setup.get("symbol", "BTCUSDT")
    side = setup.get("side", "BUY")
    price = setup.get("price", 0.0)
    strat = setup.get("strategy_name", "Quantitative Scalp")
    reasons_text = "\n".join([f"  • {r}" for r in reasons])

    msg = (
        f"👑 <b>[ESKALASI OTORISASI DEWAN DIREKSI]</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Tiket: <code>{t_id}</code>\n"
        f"Aset : <b>{sym} ({side})</b> @ ${price:,.4f}\n"
        f"Strategi : <i>{strat}</i>\n\n"
        f"⚠️ <b>Pemicu Otorisasi Dewan:</b>\n"
        f"{reasons_text}\n\n"
        f"<i>Silakan tinjau dan klik tombol persetujuan di bawah ini:</i>"
    )
    inline_kb = [
        [
            {"text": "✅ SETUJUI SEKARANG", "callback_data": f"boardappr_{t_id}"},
            {"text": "❌ TOLAK / VETO", "callback_data": f"boardrej_{t_id}"}
        ]
    ]
    return send_telegram_msg(msg, reply_markup={"inline_keyboard": inline_kb})


def notify_daily_executive_briefing(user_email=None, is_demo=True):
    """
    Daily Executive Quant Briefing:
    Calculates 24-hour performance (Realized PnL, Win Rate, Profit Factor, Closed Trades),
    dominance quadrant, and current wallet balance for Telegram distribution.
    """
    try:
        import trade_journal
        import dominance_compass
        import binance_client

        mode_text = "🟡 DEMO (Testnet)" if is_demo else "🔴 LIVE"
        ledger = trade_journal.load_journal()
        now = datetime.now()

        recent_trades = []
        for t in ledger:
            c_at = t.get("closed_at")
            if c_at:
                try:
                    dt = datetime.strptime(c_at, "%Y-%m-%d %H:%M:%S")
                    if (now - dt).total_seconds() <= 86400:
                        recent_trades.append(t)
                except Exception:
                    pass

        if not recent_trades and ledger:
            recent_trades = ledger[-5:]

        n_trades = len(recent_trades)
        wins = [t for t in recent_trades if float(t.get("net_pnl_usd", t.get("pnl_usd", 0))) > 0]
        losses = [t for t in recent_trades if float(t.get("net_pnl_usd", t.get("pnl_usd", 0))) <= 0]
        win_rate = (len(wins) / n_trades * 100.0) if n_trades > 0 else 0.0
        tot_pnl = sum(float(t.get("net_pnl_usd", t.get("pnl_usd", 0))) for t in recent_trades)
        sum_wins = sum(float(t.get("net_pnl_usd", 0)) for t in wins)
        sum_losses = abs(sum(float(t.get("net_pnl_usd", 0)) for t in losses))
        profit_factor = (sum_wins / sum_losses) if sum_losses > 0 else (99.0 if sum_wins > 0 else 0.0)

        bal = binance_client.send_signed_request("/fapi/v2/balance", method="GET", is_demo=is_demo, user_email=user_email)
        usdt_bal = next((float(b.get("balance", 0)) for b in (bal or []) if b.get("asset") == "USDT"), 5160.20)

        try:
            comp = dominance_compass.get_dominance_compass()
            compass_title = comp.get("regime_title", "N/A")
        except Exception:
            compass_title = "N/A"

        pnl_sign = "+" if tot_pnl >= 0 else ""
        pnl_badge = "🟢 PROFITABLE" if tot_pnl > 0 else ("🔴 DEFICIT" if tot_pnl < 0 else "⚪ BREAKEVEN")

        msg = (
            f"🏛️ <b>EXECUTIVE QUANT BRIEFING (24H RECAP)</b>\n"
            f"<i>Mode: {mode_text} | Status: {pnl_badge}</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Total Ekuitas Dompet:</b> <code>${usdt_bal:,.2f} USDT</code>\n"
            f"💵 <b>Net PnL 24 Jam      :</b> <code>{pnl_sign}${tot_pnl:,.2f} USDT</code>\n"
            f"🎯 <b>Win Rate (24H)      :</b> <code>{win_rate:.1f}% ({len(wins)}W / {len(losses)}L)</code>\n"
            f"📊 <b>Profit Factor       :</b> <code>{profit_factor:.2f}</code>\n"
            f"📂 <b>Total Closed Trades :</b> <code>{n_trades} trade</code>\n"
            f"🧭 <b>Market Compass      :</b> <i>{compass_title}</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 <i>Dicatat otomatis pada: {now.strftime('%Y-%m-%d %H:%M:%S')} WIB</i>"
        )
        return send_telegram_msg(msg)
    except Exception as e:
        print(f"[Daily Briefing Error] {e}")
        return False

class TelegramCommandListener(threading.Thread):
    """
    Background daemon thread that listens for incoming Telegram commands via getUpdates long-polling.
    """
    def __init__(self, user_email=None, is_demo=True):
        super().__init__(daemon=True)
        self.user_email = user_email
        self.is_demo = is_demo
        self.running = True
        self.offset = 0

    def run(self):
        token, auth_chat_id = get_telegram_config()
        if not token or not auth_chat_id:
            print("[Telegram Listener] Token atau Chat ID belum dikonfigurasi di .env. Remote control pasif.")
            return

        print(f"[Telegram Listener] ✅ Aktif mendengarkan perintah dari Chat ID: {auth_chat_id}")
        send_telegram_msg("🤖 <b>Trading Desk Remote Control Online</b>\nKirim /help untuk melihat menu perintah.")

        while self.running:
            try:
                updates = self._fetch_updates(token)
                if updates and updates.get("ok"):
                    for item in updates.get("result", []):
                        self.offset = item["update_id"] + 1
                        msg = item.get("message")
                        if not msg:
                            continue

                        sender_chat_id = str(msg.get("chat", {}).get("id", ""))
                        text = msg.get("text", "").strip()

                        # Security Check: Reject commands from unauthorized users
                        if sender_chat_id != auth_chat_id:
                            print(f"[Telegram Listener] ⚠️ Perintah diabaikan dari chat_id tidak dikenal: {sender_chat_id}")
                            continue

                        if text.startswith("/"):
                            self._handle_command(text, sender_chat_id)
            except Exception as e:
                time.sleep(5)

            time.sleep(1)

    def _fetch_updates(self, token):
        url = f"https://api.telegram.org/bot{token}/getUpdates?offset={self.offset}&timeout=10"
        try:
            req = urllib.request.Request(url, headers=HEADERS, method="GET")
            with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            return None

    def run(self):
        token, auth_chat_id = get_telegram_config()
        if not token or not auth_chat_id:
            print("[Telegram Listener] Token atau Chat ID belum dikonfigurasi di .env. Remote control pasif.")
            return

        # Register official menu commands in Telegram UI
        setup_bot_commands()

        print(f"[Telegram Listener] ✅ Aktif mendengarkan perintah dari Chat ID: {auth_chat_id}")
        send_telegram_msg(
            "🤖 <b>Trading Desk Remote Control Online</b>\n"
            "Gunakan tombol di bawah layar atau menu untuk mengontrol desk secara instan.",
            reply_markup=MAIN_KEYBOARD
        )

        while self.running:
            try:
                updates = self._fetch_updates(token)
                if updates and updates.get("ok"):
                    for item in updates.get("result", []):
                        self.offset = item["update_id"] + 1

                        # 1. Handle Inline Button Clicks (Callback Queries)
                        cb = item.get("callback_query")
                        if cb:
                            self._handle_callback(cb, token, auth_chat_id)
                            continue

                        # 2. Handle Text Messages & Commands
                        msg = item.get("message")
                        if not msg:
                            continue

                        sender_chat_id = str(msg.get("chat", {}).get("id", ""))
                        text = msg.get("text", "").strip()

                        # Security Check: Reject commands from unauthorized users
                        if sender_chat_id != auth_chat_id:
                            print(f"[Telegram Listener] ⚠️ Perintah diabaikan dari chat_id tidak dikenal: {sender_chat_id}")
                            continue

                        # Map Text Button Presses to Commands
                        cmd_map = {
                            "📊 Status Desk": "/status",
                            "📊 Status": "/status",
                            "💰 Cek PnL": "/pnl",
                            "💰 PnL": "/pnl",
                            "📖 Jurnal & Analytics": "/journal",
                            "📖 Jurnal": "/journal",
                            "📊 Jurnal": "/journal",
                            "📊 Analytics": "/journal",
                            "🛡️ Directional Heat": "/heat",
                            "🛡️ Heat": "/heat",
                            "🛡️ Korelasi": "/heat",
                            "🧭 Market Compass": "/compass",
                            "🧭 Compass": "/compass",
                            "🧭 Dominance": "/compass",
                            "🧲 Depth & Liquidity": "/heatmap BTC",
                            "🧲 Liquidity": "/heatmap BTC",
                            "🧲 Heatmap": "/heatmap BTC",
                            "🧲 Depth": "/heatmap BTC",
                            "📈 Minta Chart BTC": "/chart BTC",
                            "🌊 Sentimen Coinalyze": "/coinalyze BTC",
                            "🌊 Sentimen Pasar": "/coinalyze BTC",
                            "🏛️ SMC Trailing": "/trailing",
                            "🏛️ Trailing": "/trailing",
                            "🏛️ SMC": "/trailing",
                            "🏛️ Coinbase Premium": "/coinbase",
                            "🏛️ Coinbase": "/coinbase",
                            "🧬 Status Genome": "/genome",
                            "🤖 Mode Hybrid (Auto)": "/hybrid",
                            "⚡ Mode Scalp (5m)": "/scalp",
                            "🎯 Mode Swing (1H)": "/swing",
                            "📰 Kalender Berita": "/news",
                            "⏸️ Jeda Bot": "/pause",
                            "⏸️ Pause": "/pause",
                            "▶️ Lanjutkan Bot": "/resume",
                            "▶️ Resume": "/resume",
                            "🚨 Tutup Semua Posisi": "/closeall",
                            "🚨 Close All": "/closeall",
                            "🤖 Tanya AI Officer": "/ask",
                            "🤖 Tanya AI": "/ask",
                            "🤖 AI Officer": "/ask",
                            "📋 Executive Briefing": "/report",
                            "📋 Briefing": "/report",
                            "📋 Laporan Harian": "/report",
                            "📋 Report": "/report",
                            "❓ Panduan Bantuan": "/help",
                            "❓ Bantuan": "/help"
                        }
                        effective_cmd = cmd_map.get(text, text)

                        if effective_cmd.startswith("/"):
                            self._handle_command(effective_cmd, sender_chat_id)
            except Exception as e:
                time.sleep(3)

            time.sleep(1)

    def _fetch_updates(self, token):
        url = f"https://api.telegram.org/bot{token}/getUpdates?offset={self.offset}&timeout=10"
        try:
            req = urllib.request.Request(url, headers=HEADERS, method="GET")
            with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            return None

    def _handle_callback(self, cb, token, auth_chat_id):
        cb_id = cb.get("id")
        sender_chat_id = str(cb.get("message", {}).get("chat", {}).get("id", ""))

        if sender_chat_id != auth_chat_id:
            return

        # Acknowledge callback immediately to dismiss Telegram button spinner
        try:
            ans_url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
            payload = urllib.parse.urlencode({"callback_query_id": cb_id}).encode("utf-8")
            req = urllib.request.Request(ans_url, data=payload, headers=HEADERS, method="POST")
            urllib.request.urlopen(req, timeout=5, context=SSL_CTX)
        except Exception:
            pass

        data = cb.get("data", "")
        if data.startswith("close_"):
            sym = data.replace("close_", "")
            self._handle_command(f"/close {sym}", sender_chat_id)
        elif data.startswith("scaleout_"):
            sym = data.replace("scaleout_", "")
            self._handle_command(f"/scaleout {sym}", sender_chat_id)
        elif data == "closeall":
            self._handle_command("/closeall", sender_chat_id)
        elif data == "refresh_status":
            self._handle_command("/status", sender_chat_id)
        elif data == "refresh_trailing":
            self._handle_command("/trailing", sender_chat_id)
        elif data == "refresh_heat":
            self._handle_command("/heat", sender_chat_id)
        elif data == "refresh_compass":
            self._handle_command("/compass", sender_chat_id)
        elif data.startswith("depth_"):
            sym = data.replace("depth_", "")
            self._handle_command(f"/heatmap {sym}", sender_chat_id)
        elif data == "refresh_depth":
            self._handle_command("/heatmap BTC", sender_chat_id)
        elif data == "refresh_journal":
            self._handle_command("/journal", sender_chat_id)
        elif data.startswith("journal_"):
            tf_arg = data.replace("journal_", "")
            self._handle_command(f"/journal {tf_arg}", sender_chat_id)
        elif data == "refresh_pnl":
            self._handle_command("/pnl", sender_chat_id)
        elif data == "force_evolve":
            self._handle_command("/evolve", sender_chat_id)
        elif data == "refresh_genome":
            self._handle_command("/genome", sender_chat_id)
        elif data.startswith("boardappr_"):
            t_id = data.replace("boardappr_", "")
            self._handle_command(f"/board_approve {t_id}", sender_chat_id)
        elif data.startswith("boardrej_"):
            t_id = data.replace("boardrej_", "")
            self._handle_command(f"/board_reject {t_id}", sender_chat_id)
        elif data == "refresh_firm":
            self._handle_command("/firm", sender_chat_id)
        elif data == "refresh_tickets":
            self._handle_command("/tickets", sender_chat_id)

    def _handle_command(self, cmd_text, chat_id):
        # Lazy import sibling tools to avoid circular dependencies
        import binance_client
        import trading_desk

        parts = cmd_text.split()
        command = parts[0].lower().split("@")[0]

        if command in ["/start", "/help"]:
            reply = (
                f"🤖 <b>AKADEMI CRYPTO - TRADING DESK COMMAND CENTER</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Gunakan tombol di bawah atau ketik perintah:\n"
                f"• <code>/status</code> : Cek saldo akun, status autopilot, & posisi aktif\n"
                f"• <code>/pnl</code> : Rincian floating PnL setiap koin\n"
                f"• <code>/ask [pertanyaan]</code> : 🤖 Tanya & konsultasi dengan AI Quant Officer (cth: <code>/ask analisa btc hari ini</code>)\n"
                f"• <code>/trailing</code> : 🏛️ SMC Structural Trailing Stop & Swing Pivot (Akademi Crypto Module 02)\n"
                f"• <code>/journal [all|24h|7d]</code> : 📖 Jurnal Trading & Performance Scorecard (Akademi Crypto Module 03)\n"
                f"• <code>/analytics</code> : 📊 Analisis kuantitatif Win Rate, Profit Factor & Payoff Ratio\n"
                f"• <code>/heat</code> : 🛡️ Directional Heat & Batas Korelasi Portofolio (Akademi Crypto Module 03)\n"
                f"• <code>/compass</code> : 🧭 BTC.D & USDT.D Market Flow Compass (Akademi Crypto Module 01)\n"
                f"• <code>/sentiment</code> : 🧭 Fear & Greed Index, Rotasi Sektor Narasi, & Trending Virality\n"
                f"• <code>/heatmap [koin]</code> : 🧲 Liquidity Heatmap & Order Book Depth Imbalance (cth: <code>/heatmap btc</code>, <code>/depth sol</code>)\n"
                f"• <code>/chart [koin] [tf]</code> : Snapshot visual candlestick chart (cth: <code>/chart btc</code>, <code>/chart sol 5m</code>)\n"
                f"• <code>/coinalyze [koin]</code> : Sentimen Open Interest, Likuidasi 4H, & L/S Ratio (cth: <code>/coinalyze btc</code>, <code>/coinalyze doge</code>)\n"
                f"• <code>/coinbase</code> : Coinbase Premium Index (Arus Wall Street vs Ritel global - cth: <code>/coinbase</code>, <code>/coinbase eth</code>)\n"
                f"• <code>/genome</code> : Status AI Quant Genome & performa mutasi\n"
                f"• <code>/evolve</code> : Jalankan autopsi performa & mutasi mandiri sekarang\n"
                f"• <code>/news</code> : Kalender berita makro ekonomi AS (High-Impact)\n"
                f"• <code>/pause</code> : Jeda eksekusi order autopilot baru\n"
                f"• <code>/resume</code> : Lanjutkan kembali autopilot\n"
                f"• <code>/close</code> : Pilih koin untuk ditutup via tombol interaktif\n"
                f"• <code>/closeall</code> : ⚠️ Tutup seluruh posisi aktif secara instan\n"
                f"• <code>/help</code> : Panduan menu ini\n"
            )
            send_telegram_msg(reply, chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)

        elif command in ["/ask", "/ai", "/officer", "🤖 tanya ai officer"]:
            if len(parts) < 2:
                send_telegram_msg(
                    "🤖 <b>AI SENIOR QUANT OFFICER READY</b>\n"
                    "Silakan ajukan pertanyaan pasar, evaluasi portofolio, atau analisa koin!\n\n"
                    "<b>Contoh penggunaan:</b>\n"
                    "• <code>/ask kenapa kamu buka posisi LINK?</code>\n"
                    "• <code>/ask bagaimana kondisi Bitcoin dan sentimen saat ini?</code>\n"
                    "• <code>/ask apakah aman trading sebelum rilis berita malam ini?</code>",
                    chat_id_override=chat_id,
                    reply_markup=MAIN_KEYBOARD
                )
                return

            query = " ".join(parts[1:])
            send_telegram_msg("🤔 <i>AI Senior Quant Officer sedang menganalisis data pasar & portofolio...</i>", chat_id_override=chat_id)
            try:
                import ai_risk_officer
                bal = trading_desk.get_account_balance(self.user_email, self.is_demo)
                positions = trading_desk.get_active_positions(self.user_email, self.is_demo)
                mode = get_desk_mode()
                ctx = {
                    "balance_usd": bal,
                    "positions": positions,
                    "mode": mode
                }
                try:
                    import macro_news_shield
                    is_blk, blk_r, next_ev = macro_news_shield.audit_news_blackout(buffer_minutes=30)
                    ctx["news_shield"] = {"is_blackout": is_blk, "status": "BLACKOUT" if is_blk else "SAFE", "reason": blk_r}
                except Exception:
                    pass

                answer = ai_risk_officer.answer_trader_query(query, ctx)
                reply = (
                    f"🤖 <b>AI QUANT OFFICER BRIEFING</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"❓ <i>\"{html.escape(query)}\"</i>\n\n"
                    f"{answer}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"💡 <i>Akademi Crypto AI Co-Pilot</i>"
                )
                send_telegram_msg(reply, chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)
            except Exception as e:
                send_telegram_msg(f"⚠️ Gagal mendapatkan jawaban AI: {e}", chat_id_override=chat_id)

        elif command == "/status":
            bal = trading_desk.get_account_balance(self.user_email, self.is_demo)
            positions = trading_desk.get_active_positions(self.user_email, self.is_demo)
            paused = is_desk_paused()
            mode = get_desk_mode()
            genome = trading_desk.load_genome()
            status_tag = "⏸️ <b>DIJEDA (PAUSED)</b>" if paused else "▶️ <b>BERJALAN (ACTIVE)</b>"

            heat_info = ""
            try:
                import portfolio_guard
                audit = portfolio_guard.audit_portfolio_heat(positions, bal)
                heat_info = (
                    f"Directional Heat: <code>{audit['long_count']}/{audit['max_same_direction']} Longs | "
                    f"{audit['short_count']}/{audit['max_same_direction']} Shorts</code>\n"
                    f"Status Risiko: <b>{audit['heat_status']}</b>\n"
                )
            except Exception:
                pass

            comp_info = ""
            try:
                import dominance_compass
                c_data = dominance_compass.get_dominance_compass()
                comp_info = f"Market Compass: <b>{c_data['regime_code']}</b> (BTC.D {c_data['btc_d']}%, USDT.D {c_data['usdt_d']}%)\n"
            except Exception:
                pass

            if mode == "HYBRID":
                mode_str = "🤖 HYBRID (Dual-Engine: 5m Scalp + 1H Swing)"
            elif mode == "SCALP":
                mode_str = "⚡ SCALP (5m Micro-Structure)"
            else:
                mode_str = "🎯 SWING (1H / 4H Macro Confluence)"

            reply = (
                f"🖥️ <b>STATUS TRADING DESK</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Status Autopilot: {status_tag}\n"
                f"Mode Operasi: <b>{mode_str}</b>\n"
                f"Mode Akun: {'🟡 DEMO (Testnet)' if self.is_demo else '🔴 LIVE'}\n"
                f"Saldo Equity: <code>${bal:,.2f} USDT</code>\n"
                f"Posisi Terbuka: <code>{len(positions)} posisi</code>\n"
                f"{heat_info}"
                f"{comp_info}"
                f"Genetic Rule: Gen {genome.get('generation', 5)} (Min R:R 1:{genome.get('parameters', {}).get('min_risk_reward', 3.0)})\n"
                f"Max Risk Per Trade: {genome.get('parameters', {}).get('max_risk_per_trade_pct', 1.5)}%\n"
            )

            # Build Inline Action Buttons
            inline_kb = []
            # Add position close & scale-out buttons
            for p in positions:
                sym = p["symbol"]
                upnl = float(p.get("unRealizedProfit", 0))
                p_sign = "+" if upnl >= 0 else ""
                inline_kb.append([
                    {"text": f"🔴 Tutup {sym} ({p_sign}${upnl:.2f})", "callback_data": f"close_{sym}"},
                    {"text": f"🎯 TP 50% {sym}", "callback_data": f"scaleout_{sym}"}
                ])

            # Utility buttons
            inline_kb.append([
                {"text": "🔄 Refresh", "callback_data": "refresh_status"},
                {"text": "🏛️ SMC Trailing", "callback_data": "refresh_trailing"},
                {"text": "📖 Jurnal", "callback_data": "refresh_journal"}
            ])
            inline_kb.append([
                {"text": "🛡️ Cek Heat", "callback_data": "refresh_heat"},
                {"text": "🧭 Compass", "callback_data": "refresh_compass"},
                {"text": "🧲 Liquidity", "callback_data": "depth_BTC"}
            ])
            inline_kb.append([
                {"text": "💰 PnL", "callback_data": "refresh_pnl"}
            ])
            if positions:
                inline_kb.append([{"text": "🚨 Tutup Seluruh Posisi", "callback_data": "closeall"}])

            send_telegram_msg(reply, chat_id_override=chat_id, reply_markup={"inline_keyboard": inline_kb})

        elif command in ["/journal", "/analytics", "/scorecard", "/jurnal"]:
            tf = parts[1].lower() if len(parts) > 1 else "all"
            try:
                import trade_journal
                report_msg = trade_journal.format_telegram_journal(tf)
                inline_kb = [
                    [
                        {"text": "📅 24 Jam", "callback_data": "journal_24h"},
                        {"text": "📈 7 Hari", "callback_data": "journal_7d"},
                        {"text": "🏆 Semua (All)", "callback_data": "journal_all"}
                    ],
                    [
                        {"text": "🔄 Refresh", "callback_data": f"journal_{tf}"},
                        {"text": "📊 Status Desk", "callback_data": "refresh_status"}
                    ]
                ]
                send_telegram_msg(report_msg, chat_id_override=chat_id, reply_markup={"inline_keyboard": inline_kb})
            except Exception as e:
                send_telegram_msg(f"⚠️ Gagal memuat Jurnal Trading: {e}", chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)

        elif command in ["/report", "/briefing", "/daily", "📋 executive briefing", "📋 briefing", "📋 laporan harian", "📋 report"]:
            try:
                notify_daily_executive_briefing(self.user_email, self.is_demo)
            except Exception as e:
                send_telegram_msg(f"⚠️ Gagal memuat Executive Briefing: {e}", chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)

        elif command in ["/rejection", "/reversal", "/wick", "🕯️ rejection block"]:
            try:
                import rejection_block_engine
                import market_eyes
                msg_lines = [
                    "🕯️ <b>ICT REJECTION BLOCK REVERSAL RADAR</b>\n"
                    "<i>Smart Money Mean Threshold (50% Wick) Scanner</i>\n"
                    "━━━━━━━━━━━━━━━━━━"
                ]
                for c_sym in ["BTC", "ETH", "SOL"]:
                    pair = f"{c_sym}USDT"
                    candles = market_eyes.fetch_candles(c_sym, bar="1H", limit=40)
                    intel = rejection_block_engine.get_rejection_block_intelligence(pair, candles)
                    cur_p = candles[-1]["close"] if candles else 0
                    msg_lines.append(f"\n💎 <b>{pair}</b> (1H: <code>${cur_p:,.2f}</code>)")
                    if intel["is_retesting_now"] and intel["retest_setup"]:
                        setup = intel["retest_setup"]
                        side_ico = "🟢 LONG" if setup["side"] == "LONG" else "🔴 SHORT"
                        msg_lines.append(
                            f"🔥 <b>ACTIVE RETEST:</b> {side_ico}\n"
                            f"• State: <code>{setup['retest_state']}</code>\n"
                            f"• MT 50%: <code>${setup['mean_threshold']:,.4f}</code>\n"
                            f"• Target R:R: <code>1 : {setup['rr_ratio']:.1f}</code>\n"
                            f"• SL: <code>${setup['sl_price']:,.4f}</code> | TP: <code>${setup['tp2_price']:,.4f}</code>"
                        )
                    elif intel["blocks"]:
                        top_b = intel["blocks"][0]
                        side_txt = "🟢 Bullish" if top_b["side"] == "LONG" else "🔴 Bearish"
                        msg_lines.append(
                            f"• Latest: <b>{side_txt}</b> ({top_b['status']})\n"
                            f"• Zona Sumbu: <code>${top_b['block_low']:,.2f} - ${top_b['block_high']:,.2f}</code>\n"
                            f"• MT 50%: <code>${top_b['mean_threshold']:,.2f}</code> (Wick: {top_b['wick_ratio']*100:.1f}%)"
                        )
                    else:
                        msg_lines.append("• <i>Tidak ada Rejection Block aktif saat ini.</i>")
                msg_lines.append("\n━━━━━━━━━━━━━━━━━━\n🕒 <i>" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "</i>")
                send_telegram_msg("\n".join(msg_lines), chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)
            except Exception as e:
                send_telegram_msg(f"⚠️ Gagal memuat Rejection Block: {e}", chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)

        elif command in ["/heat", "/correlation", "/korelasi"]:
            try:
                import portfolio_guard
                positions = trading_desk.get_active_positions(self.user_email, self.is_demo)
                bal = trading_desk.get_account_balance(self.user_email, self.is_demo)
                heat_msg = portfolio_guard.format_telegram_portfolio_heat(positions, bal)
                send_telegram_msg(heat_msg, chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)
            except Exception as e:
                send_telegram_msg(f"⚠️ Gagal memuat Directional Heat: {e}", chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)

        elif command in ["/compass", "/dominance", "/btcd", "/usdtd", "/kompas"]:
            try:
                import dominance_compass
                comp = dominance_compass.get_dominance_compass()
                report_msg = dominance_compass.format_telegram_compass(comp)
                send_telegram_msg(report_msg, chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)
            except Exception as e:
                send_telegram_msg(f"⚠️ Gagal memuat Market Compass: {e}", chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)

        elif command in ["/trailing", "/smc", "/structure"]:
            try:
                import market_structure
                import trade_manager
                positions = trading_desk.get_active_positions(self.user_email, self.is_demo)
                meta = trade_manager.load_trade_metadata()
                trailing_msg = market_structure.format_telegram_market_structure(positions, meta)
                inline_kb = [
                    [
                        {"text": "🔄 Refresh", "callback_data": "refresh_trailing"},
                        {"text": "📊 Status Desk", "callback_data": "refresh_status"}
                    ],
                    [
                        {"text": "📖 Jurnal", "callback_data": "refresh_journal"},
                        {"text": "🛡️ Directional Heat", "callback_data": "refresh_heat"}
                    ]
                ]
                send_telegram_msg(trailing_msg, chat_id_override=chat_id, reply_markup={"inline_keyboard": inline_kb})
            except Exception as e:
                send_telegram_msg(f"⚠️ Gagal memuat SMC Structural Trailing: {e}", chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)

        elif command == "/pnl":
            bal = trading_desk.get_account_balance(self.user_email, self.is_demo)
            positions = trading_desk.get_active_positions(self.user_email, self.is_demo)
            notify_pnl_summary(bal, positions, is_demo=self.is_demo)

        elif command == "/pause":
            state = load_desk_state()
            state["paused"] = True
            save_desk_state(state)
            send_telegram_msg(
                "⏸️ <b>Trading Desk berhasil dijeda!</b>\nTidak ada order baru yang akan dibuka sampai Anda menekan '▶️ Lanjutkan Bot'.",
                chat_id_override=chat_id,
                reply_markup=MAIN_KEYBOARD
            )

        elif command == "/resume":
            state = load_desk_state()
            state["paused"] = False
            save_desk_state(state)
            send_telegram_msg(
                "▶️ <b>Trading Desk dilanjutkan kembali!</b>\nSiklus pemindaian dan eksekusi autopilot aktif.",
                chat_id_override=chat_id,
                reply_markup=MAIN_KEYBOARD
            )

        elif command in ["/hybrid", "/auto", "🤖 mode hybrid (auto)"]:
            state = load_desk_state()
            state["mode"] = "HYBRID"
            save_desk_state(state)
            send_telegram_msg(
                "🤖 <b>MODE HYBRID DUAL-ENGINE AKTIF! (AUTO SWING + SCALP)</b>\n\n"
                "• <b>Otomatis & Mandiri</b>: Agent aktif memindai peluang <b>1H Swing</b> dan <b>5m Fast Scalping</b> secara bersamaan!\n"
                "• <b>Prioritas Scalp</b>: Begitu terdeteksi pergerakan kilat 5m (Volume Surge, VWAP 2σ, Sweep FVG), scalp akan otomatis dieksekusi ke slot kosong tanpa perlu disuruh.\n"
                "• <b>Proteksi Khusus</b>: Trade scalp otomatis memakai Fast Breakeven (+0.7R) dan 45-Minute Time-Stop.\n\n"
                "<i>Trading Desk kini berburu setup jangka pendek dan menengah secara penuh autopilot.</i>",
                chat_id_override=chat_id,
                reply_markup=MAIN_KEYBOARD
            )

        elif command in ["/scalp", "⚡ mode scalp (5m)"]:
            state = load_desk_state()
            state["mode"] = "SCALP"
            save_desk_state(state)
            send_telegram_msg(
                "⚡ <b>MODE FAST SCALPER AKTIF! (5m / 15m)</b>\n\n"
                "• Timeframe: <b>5m Micro-Structure</b>\n"
                "• Setup: <b>Rejection Block, Liquidity Sweep, VWAP 2σ, Volume Surge</b>\n"
                "• Target Durasi: <b>15 - 30 Menit</b>\n"
                "• Breakeven Kilat: <b>+0.60R (Free Roll)</b>\n"
                "• Time-Stop: <b>Maksimal 20 Menit</b> (tutup otomatis jika stagnan)\n"
                "• Risk Budget: <b>0.35% – 0.50% (Micro-Kelly)</b>\n\n"
                "<i>Agent memindai 10 koin teratas setiap 1 menit. Kirim <code>/scalpscan</code> untuk memindai setup sekarang!</i>",
                chat_id_override=chat_id,
                reply_markup=MAIN_KEYBOARD
            )

        elif command in ["/scalpscan", "/scan5m"]:
            send_telegram_msg("⚡ <i>Memindai 10 koin teratas pada timeframe 5m...</i>", chat_id_override=chat_id)
            try:
                import fast_scalper
                setups = fast_scalper.scan_all_scalp_opportunities()
                if not setups:
                    send_telegram_msg(
                        "ℹ️ <b>Belum ada setup scalping 5m yang valid saat ini.</b>\n"
                        "Semua koin sedang berada di fase konsolidasi atau belum menyentuh Mean Threshold / Liquidity Pool.",
                        chat_id_override=chat_id,
                        reply_markup=MAIN_KEYBOARD
                    )
                else:
                    msg = f"⚡ <b>DITEMUKAN {len(setups)} PELUANG SCALPING 5M!</b>\n━━━━━━━━━━━━━━━━━━\n"
                    for s in setups[:5]:
                        side_emoji = "🟢 LONG" if s["side"] == "LONG" else "🔴 SHORT"
                        msg += (
                            f"💎 <b>{s['symbol']}</b> | {side_emoji}\n"
                            f"• Strategi: <code>{s['strategy']}</code>\n"
                            f"• Entry: <code>${s['entry']:,.4f}</code>\n"
                            f"• Stop Loss: <code>${s['sl']:,.4f}</code>\n"
                            f"• Take Profit: <code>${s['tp']:,.4f}</code> (R:R 1:{s['rr_ratio']:.2f})\n"
                            f"• Target: <code>{s.get('target_duration', '15-30m')}</code>\n"
                            f"• Alasan: <i>{s['reason']}</i>\n"
                            f"──────────────────\n"
                        )
                    send_telegram_msg(msg, chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)
            except Exception as e:
                send_telegram_msg(f"⚠️ Error saat memindai scalp: {e}", chat_id_override=chat_id)

        elif command in ["/swing", "🎯 mode swing (1h)", "🎯 mode swing (profit besar)"]:
            state = load_desk_state()
            state["mode"] = "SWING"
            save_desk_state(state)
            send_telegram_msg(
                "🎯 <b>MODE SWING PROFIT BESAR AKTIF! (1H / 4H)</b>\n\n"
                "• <b>Fokus</b>: Menangkap tren besar (Big-Profit Wave) dengan ekspektansi matematis maksimal!\n"
                "• <b>Timeframe</b>: 1H & 4H Macro Confluence (SMC, Wyckoff, FVG, Volume Profile)\n"
                "• <b>Target R:R</b>: <b>1:3.00 – 1:5.00+</b> (High Reward/Risk Ratio)\n"
                "• <b>Breakeven</b>: <b>+1.0R</b> (Terkunci bebas risiko jika sudah untung)\n"
                "• <b>Trailing Stop Dinamis</b>: <b>+2.0R, +3.0R, +4.0R+</b> (Mengunci floating profit besar)\n"
                "• <b>Time Stop</b>: <b>Nonaktif</b> (Trade swing diberikan ruang bernapas penuh tanpa batas 45 menit)\n"
                "• <b>Status Scalper</b>: 5m Micro Scalper dinonaktifkan sementara.\n\n"
                "<i>Trading Desk kini beroperasi secara disiplin menangkap ekspansi tren institusional!</i>",
                chat_id_override=chat_id,
                reply_markup=MAIN_KEYBOARD
            )

        elif command in ["/chart", "📈 minta chart btc"]:
            raw_sym = parts[1].upper() if len(parts) > 1 else "BTC"
            sym_clean = raw_sym.replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")
            tf = parts[2].lower() if len(parts) > 2 else "1H"
            send_telegram_msg(f"🎨 Merender candlestick snapshot untuk <b>{sym_clean}/USDT</b> ({tf.upper()})...", chat_id_override=chat_id)
            try:
                import chart_snapshot
                candles = chart_snapshot.fetch_candles_for_snapshot(sym_clean, bar=tf, limit=45)
                cur_price = candles[-1]["close"] if candles else 0.0
                chart_file = chart_snapshot.generate_trade_chart(
                    symbol=sym_clean,
                    side="BUY",
                    entry_price=cur_price,
                    sl_price=cur_price * 0.985,
                    tp_price=cur_price * 1.035,
                    timeframe=tf,
                    strategy_name=f"Market Snapshot ({sym_clean})"
                )
                if chart_file and os.path.exists(chart_file):
                    caption = (
                        f"📊 <b>CANDLESTICK CHART SNAPSHOT: {sym_clean}/USDT</b>\n"
                        f"🕒 Timeframe: <code>{tf.upper()}</code> | Harga Terakhir: <code>${cur_price:,.4f}</code>\n"
                        f"📈 VWAP & R:R Projection (Akademi Crypto Mission Control)\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"<i>Tips: Ketik <code>/chart eth 5m</code> atau <code>/chart sol 1h</code> untuk koin & tf lain.</i>"
                    )
                    res = chart_snapshot.send_telegram_photo(chart_file, caption=caption, chat_id=chat_id)
                    if not (res and res.get("ok")):
                        send_telegram_msg("⚠️ Gagal mengirim foto chart ke Telegram.", chat_id_override=chat_id)
                else:
                    send_telegram_msg("⚠️ Gagal membuat file gambar chart.", chat_id_override=chat_id)
            except Exception as e:
                send_telegram_msg(f"⚠️ Error saat membuat chart: {e}", chat_id_override=chat_id)

        elif command in ["/coinglass", "/coinalyze", "/oi"]:
            raw_sym = parts[1].upper() if len(parts) > 1 else "BTC"
            sym_clean = raw_sym.replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")
            try:
                import coinglass_derivatives
                d_intel = coinglass_derivatives.get_derivatives_intelligence(sym_clean)
                report_msg = coinglass_derivatives.format_telegram_report(d_intel)
                send_telegram_msg(report_msg, chat_id_override=chat_id)
            except Exception as e:
                send_telegram_msg(f"⚠️ Gagal memuat data CoinGlass untuk {sym_clean}: {e}", chat_id_override=chat_id)

        elif command in ["/sentiment", "/narrative", "/fng", "🧭 sentiment & narrative"]:
            send_telegram_msg("🧭 <i>Memindai sentimen sosial, Fear & Greed, dan rotasi narasi...</i>", chat_id_override=chat_id)
            try:
                import sentiment_narrative_scanner
                summary = sentiment_narrative_scanner.get_market_sentiment_narrative_summary()
                fng = summary.get("fear_and_greed", {})
                rot = summary.get("narrative_rotation", {})
                vir = summary.get("social_virality", {})
                lead = rot.get("leading_sector", {})

                fng_score = fng.get("score", 50)
                fng_icon = "🟢" if fng_score >= 55 else ("🔴" if fng_score <= 45 else "⚪")

                sector_lines = []
                for s in rot.get("sectors", [])[:5]:
                    sign = "+" if s["avg_change_24h"] >= 0 else ""
                    sector_lines.append(f"• {s['icon']} <b>{s['title']}</b>: <code>{sign}{s['avg_change_24h']:.2f}%</code> (vs BTC {s['relative_strength_vs_btc']:+.1f}%)")

                trend_symbols = ", ".join([f"<code>{t['symbol']}</code>" for t in vir.get("trending_tokens", [])[:6]]) or "-"

                msg = (
                    f"🧭 <b>CRYPTO SENTIMENT & NARRATIVE SCANNER</b>\n"
                    f"<i>Tauric Research Analyst Protocol</i>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"{fng_icon} <b>Fear & Greed Index:</b> <code>{fng_score}/100 [{fng.get('classification')}]</code>\n"
                    f"💡 <i>Contrarian Signal: {fng.get('contrarian_note')}</i>\n\n"
                    f"🌟 <b>Sektor Pemimpin Rotasi Modal:</b>\n"
                    f"👉 {lead.get('icon')} <b>{lead.get('title')}</b> (24h: <code>{lead.get('avg_change_24h'):+.2f}%</code>)\n\n"
                    f"📊 <b>Peringkat Rotasi Narasi (24h):</b>\n" + "\n".join(sector_lines) + f"\n\n"
                    f"🔥 <b>Trending Search Virality:</b>\n"
                    f"{trend_symbols}\n"
                    f"📌 <i>Fase: {vir.get('virality_stage')} ({vir.get('stage_note')})</i>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🕒 <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} WIB</i>"
                )
                send_telegram_msg(msg, chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)
            except Exception as e:
                send_telegram_msg(f"⚠️ Gagal memindai sentimen: {e}", chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)

        elif command in ["/coinbase", "/premium", "🏛️ coinbase premium"]:
            sym_arg = parts[1].upper() if len(parts) > 1 else "ALL"
            try:
                import coinbase_premium
                report_msg = coinbase_premium.format_telegram_report(sym_arg)
                send_telegram_msg(report_msg, chat_id_override=chat_id)
            except Exception as e:
                send_telegram_msg(f"⚠️ Gagal memuat data Coinbase Premium: {e}", chat_id_override=chat_id)

        elif command in ["/heatmap", "/depth", "/orderbook", "/liquidity", "🧲 depth & liquidity"]:
            raw_sym = parts[1].upper() if len(parts) > 1 else "BTC"
            sym_clean = raw_sym.replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")
            try:
                import liquidity_heatmap
                report_msg = liquidity_heatmap.format_telegram_liquidity_report(sym_clean)
                inline_kb = [
                    [
                        {"text": "🪙 BTC", "callback_data": "depth_BTC"},
                        {"text": "⚡ ETH", "callback_data": "depth_ETH"},
                        {"text": "🔗 LINK", "callback_data": "depth_LINK"},
                        {"text": "☀️ SOL", "callback_data": "depth_SOL"}
                    ],
                    [
                        {"text": f"🔄 Refresh {sym_clean}", "callback_data": f"depth_{sym_clean}"},
                        {"text": "📊 Status Desk", "callback_data": "refresh_status"}
                    ]
                ]
                send_telegram_msg(report_msg, chat_id_override=chat_id, reply_markup={"inline_keyboard": inline_kb})
            except Exception as e:
                send_telegram_msg(f"⚠️ Gagal memuat Liquidity Heatmap untuk {sym_clean}: {e}", chat_id_override=chat_id)

        elif command in ["/genome", "🧬 status genome"]:
            try:
                import self_improve
                status_text = self_improve.format_telegram_genome_status()
                inline_kb = [
                    [{"text": "⚡ Paksa Mutasi & Autopsi Sekarang", "callback_data": "force_evolve"}],
                    [{"text": "🔄 Refresh Genome", "callback_data": "refresh_genome"}]
                ]
                send_telegram_msg(status_text, chat_id_override=chat_id, reply_markup={"inline_keyboard": inline_kb})
            except Exception as e:
                send_telegram_msg(f"⚠️ Gagal memuat status genome: {e}", chat_id_override=chat_id)

        elif command == "/evolve":
            send_telegram_msg("🧬 Menjalankan autopsi performa & evolusi algoritma genetika...", chat_id_override=chat_id)
            try:
                import self_improve
                mutated, gen = self_improve.evolve_agent()
                if mutated:
                    send_telegram_msg(f"✅ <b>Evolusi Berhasil!</b>\nAgent ditingkatkan ke <b>Generasi {gen}</b> dengan penyesuaian parameter.", chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)
                else:
                    send_telegram_msg(f"ℹ️ <b>Genome Stabil (Gen {gen})</b>\nParameter saat ini sudah optimal dan memenuhi target fitness.", chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)
            except Exception as e:
                send_telegram_msg(f"⚠️ Error saat evolusi: {e}", chat_id_override=chat_id)

        elif command in ["/news", "📰 kalender berita"]:
            try:
                import macro_news_shield
                agenda_msg = macro_news_shield.format_telegram_news_agenda()
                send_telegram_msg(agenda_msg, chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)
            except Exception as e:
                send_telegram_msg(f"⚠️ Gagal memuat kalender berita: {e}", chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)

        elif command in ["/firm", "/paperclip", "🏢 paperclip firm"]:
            try:
                import paperclip_orchestrator
                summary = paperclip_orchestrator.get_firm_summary()
                q = summary.get("quota_tracker", {})
                cb = summary.get("circuit_breaker_active", False)
                cb_str = "🚨 AKTIF (PAUSED)" if cb else "✅ NORMAL (RUNNING)"
                counts = summary.get("stage_counts", {})
                
                msg = (
                    f"🏢 <b>PAPERCLIP AUTONOMOUS TRADING FIRM</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"• <b>Status Operasional</b>: {cb_str}\n"
                    f"• <b>Free Tier Quota</b>: <code>{q.get('free_requests_used', 0)} / {q.get('free_requests_limit', 1500)} req</code> (100% Rp 0)\n"
                    f"• <b>Agen Terdaftar</b>: <b>{len(summary.get('org_chart', []))} Agen</b>\n\n"
                    f"📋 <b>Papan Delegasi Tiket (Kanban)</b>:\n"
                    f"  🔍 Discovered : <b>{counts.get('DISCOVERED', 0)}</b>\n"
                    f"  ⚔️ Debating   : <b>{counts.get('DEBATING', 0)}</b>\n"
                    f"  🛡️ Risk Audit : <b>{counts.get('RISK_AUDIT', 0)}</b>\n"
                    f"  👑 Pending Board : <b>{counts.get('PENDING_BOARD', 0)}</b> ⚠️\n"
                    f"  ⚡ Executed   : <b>{counts.get('EXECUTED', 0) + counts.get('CLOSED', 0)}</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"<i>Gunakan <code>/tickets</code> untuk melihat tiket aktif.</i>"
                )
                inline_kb = [
                    [
                        {"text": "📋 Cek Tiket", "callback_data": "refresh_tickets"},
                        {"text": "🔄 Refresh Firm", "callback_data": "refresh_firm"}
                    ]
                ]
                send_telegram_msg(msg, chat_id_override=chat_id, reply_markup={"inline_keyboard": inline_kb})
            except Exception as e:
                send_telegram_msg(f"⚠️ Gagal memuat data Paperclip Firm: {e}", chat_id_override=chat_id)

        elif command in ["/tickets", "📋 daftar tiket"]:
            try:
                import paperclip_orchestrator
                tickets = paperclip_orchestrator.load_tickets()
                active_t = [t for t in tickets if t.get("stage") != "CLOSED" and t.get("stage") != "VETOED"][:5]
                if not active_t:
                    send_telegram_msg("📋 <b>Tidak ada tiket aktif di pipeline saat ini.</b>", chat_id_override=chat_id)
                else:
                    msg = "📋 <b>DAFTAR TIKET AKTIF (PAPERCLIP KANBAN)</b>\n━━━━━━━━━━━━━━━━━━\n"
                    for t in active_t:
                        stg = t.get("stage")
                        msg += (
                            f"• <b>{t['ticket_id']}</b>: {t['symbol']} ({t['side']})\n"
                            f"  Strategi : <i>{t.get('strategy', '-')}</i>\n"
                            f"  Tahap    : <code>{stg}</code>\n"
                        )
                        if stg == "PENDING_BOARD":
                            msg += f"  👉 <i>Gunakan: /board_approve {t['ticket_id']} atau /board_reject {t['ticket_id']}</i>\n"
                        msg += "──────────────────\n"
                    send_telegram_msg(msg, chat_id_override=chat_id)
            except Exception as e:
                send_telegram_msg(f"⚠️ Gagal memuat tiket: {e}", chat_id_override=chat_id)

        elif command == "/board_approve" and len(parts) > 1:
            t_id = parts[1]
            try:
                import paperclip_orchestrator
                t = paperclip_orchestrator.board_approve_ticket(t_id, board_user=f"Telegram ({chat_id})", note="Disetujui via Telegram")
                if t:
                    send_telegram_msg(f"👑 <b>[DISETUJUI DEWAN DIREKSI]</b>\nTiket <code>{t_id}</code> disetujui! Sinyal diteruskan ke Execution Desk.", chat_id_override=chat_id)
                else:
                    send_telegram_msg(f"⚠️ Tiket <code>{t_id}</code> tidak ditemukan.", chat_id_override=chat_id)
            except Exception as e:
                send_telegram_msg(f"⚠️ Gagal menyetujui tiket: {e}", chat_id_override=chat_id)

        elif command == "/board_reject" and len(parts) > 1:
            t_id = parts[1]
            try:
                import paperclip_orchestrator
                t = paperclip_orchestrator.board_reject_ticket(t_id, board_user=f"Telegram ({chat_id})", reason="Ditolak via Telegram")
                if t:
                    send_telegram_msg(f"🚫 <b>[DITOLAK DEWAN DIREKSI]</b>\nTiket <code>{t_id}</code> telah diveto.", chat_id_override=chat_id)
                else:
                    send_telegram_msg(f"⚠️ Tiket <code>{t_id}</code> tidak ditemukan.", chat_id_override=chat_id)
            except Exception as e:
                send_telegram_msg(f"⚠️ Gagal menolak tiket: {e}", chat_id_override=chat_id)

        elif command in ["/halt", "/circuit_breaker"]:
            try:
                import paperclip_orchestrator
                res = paperclip_orchestrator.toggle_circuit_breaker(reason=f"Telegram switch by {chat_id}")
                act = res.get("circuit_breaker_active", False)
                if act:
                    send_telegram_msg("🚨 <b>SAKLAR DARURAT DIAKTIFKAN!</b>\nSeluruh aktivitas eksekusi agen dipause.", chat_id_override=chat_id)
                else:
                    send_telegram_msg("▶️ <b>SAKLAR DARURAT DINONAKTIFKAN!</b>\nAktivitas agen kembali beroperasi normal.", chat_id_override=chat_id)
            except Exception as e:
                send_telegram_msg(f"⚠️ Gagal mengubah saklar darurat: {e}", chat_id_override=chat_id)

        elif command == "/close":
            positions = trading_desk.get_active_positions(self.user_email, self.is_demo)
            if len(parts) < 2:
                if not positions:
                    send_telegram_msg("ℹ️ Tidak ada posisi terbuka saat ini.", chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)
                    return

                inline_kb = [
                    [{"text": f"🔴 Tutup {p['symbol']} ({'+' if float(p.get('unRealizedProfit', 0))>=0 else ''}${float(p.get('unRealizedProfit', 0)):.2f})", "callback_data": f"close_{p['symbol']}"}]
                    for p in positions
                ]
                inline_kb.append([{"text": "🚨 Tutup Semua Posisi Sekaligus", "callback_data": "closeall"}])
                send_telegram_msg("👇 <b>Pilih posisi yang ingin Anda tutup di market:</b>", chat_id_override=chat_id, reply_markup={"inline_keyboard": inline_kb})
                return

            raw_sym = parts[1].upper()
            target_sym = raw_sym if raw_sym.endswith("USDT") else f"{raw_sym}USDT"
            match = next((p for p in positions if p["symbol"] == target_sym), None)

            if not match:
                send_telegram_msg(f"⚠️ Posisi terbuka untuk <code>{target_sym}</code> tidak ditemukan.", chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)
                return

            amt = float(match.get("positionAmt", 0))
            close_side = "SELL" if amt > 0 else "BUY"
            qty = abs(amt)

            send_telegram_msg(f"⏳ Menutup posisi <code>{target_sym}</code> ({qty} lots)...", chat_id_override=chat_id)
            res = binance_client.send_signed_request(
                "/fapi/v1/order",
                method="POST",
                params={
                    "symbol": target_sym,
                    "side": close_side,
                    "type": "MARKET",
                    "quantity": qty,
                    "reduceOnly": "true"
                },
                is_demo=self.is_demo,
                user_email=self.user_email
            )
            if res and res.get("orderId"):
                upnl = float(match.get("unRealizedProfit", 0))
                send_telegram_msg(
                    f"✅ Posisi <code>{target_sym}</code> berhasil ditutup di market!\nEstimasi PnL: <code>{'+' if upnl>=0 else ''}${upnl:,.2f} USDT</code>",
                    chat_id_override=chat_id,
                    reply_markup=MAIN_KEYBOARD
                )
            else:
                send_telegram_msg(f"❌ Gagal menutup posisi <code>{target_sym}</code>: {res}", chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)

        elif command in ["/scaleout", "/tp50", "/partialtp"]:
            import trade_manager
            positions = trading_desk.get_active_positions(self.user_email, self.is_demo)
            if len(parts) < 2:
                if not positions:
                    send_telegram_msg("ℹ️ Tidak ada posisi terbuka untuk di-scale out.", chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)
                    return

                inline_kb = [
                    [{"text": f"🎯 Scale-Out 50% {p['symbol']} ({'+' if float(p.get('unRealizedProfit', 0))>=0 else ''}${float(p.get('unRealizedProfit', 0)):.2f})", "callback_data": f"scaleout_{p['symbol']}"}]
                    for p in positions
                ]
                send_telegram_msg("👇 <b>Pilih posisi yang ingin Anda ambil profit 50% (Scale-Out):</b>\n<i>Sisa 50% posisi akan dikunci ke Breakeven & dituntun SMC Trailing.</i>", chat_id_override=chat_id, reply_markup={"inline_keyboard": inline_kb})
                return

            raw_sym = parts[1].upper()
            target_sym = raw_sym if raw_sym.endswith("USDT") else f"{raw_sym}USDT"
            send_telegram_msg(f"⏳ Mengeksekusi Scale-Out 50% untuk <code>{target_sym}</code>...", chat_id_override=chat_id)
            res = trade_manager.execute_manual_partial_tp(target_sym, user_email=self.user_email, is_demo=self.is_demo)
            if res.get("success"):
                send_telegram_msg(
                    f"✅ <b>SCALE-OUT 50% BERHASIL!</b>\n"
                    f"💎 <code>{target_sym}</code>: {res['closed_qty']} lot dicairkan (+${res['est_pnl_usd']:,.2f} USDT)\n"
                    f"🛡️ Sisa {res['remaining_qty']} lot dikunci ke BE @ ${res['be_price']:,.4f} sebagai <b>Free Runner</b>!",
                    chat_id_override=chat_id,
                    reply_markup=MAIN_KEYBOARD
                )
            else:
                send_telegram_msg(f"⚠️ Gagal scale-out: {res.get('error')}", chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)

        elif command == "/closeall":
            positions = trading_desk.get_active_positions(self.user_email, self.is_demo)
            if not positions:
                send_telegram_msg("ℹ️ Tidak ada posisi terbuka yang perlu ditutup.", chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)
                return

            send_telegram_msg(f"🚨 <b>Menutup seluruh ({len(positions)}) posisi terbuka...</b>", chat_id_override=chat_id)
            for p in positions:
                sym = p["symbol"]
                amt = float(p.get("positionAmt", 0))
                close_side = "SELL" if amt > 0 else "BUY"
                qty = abs(amt)
                binance_client.send_signed_request(
                    "/fapi/v1/order",
                    method="POST",
                    params={
                        "symbol": sym,
                        "side": close_side,
                        "type": "MARKET",
                        "quantity": qty,
                        "reduceOnly": "true"
                    },
                    is_demo=self.is_demo,
                    user_email=self.user_email
                )
                time.sleep(0.5)

            send_telegram_msg("✅ <b>Semua posisi berhasil dilikuidasi ke USDT.</b>", chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)

        else:
            send_telegram_msg("❓ Perintah tidak dikenal. Ketik <code>/help</code> atau gunakan tombol di bawah.", chat_id_override=chat_id, reply_markup=MAIN_KEYBOARD)

_listener_instance = None

def start_command_listener(user_email=None, is_demo=True):
    """
    Starts the Telegram command listener daemon thread if configured.
    """
    global _listener_instance
    token, chat_id = get_telegram_config()
    if not token or not chat_id:
        return None

    if _listener_instance is None or not _listener_instance.is_alive():
        _listener_instance = TelegramCommandListener(user_email=user_email, is_demo=is_demo)
        _listener_instance.start()
    return _listener_instance

def print_setup_instructions():
    print("""
=======================================================
   📱 PANDUAN PENGATURAN TELEGRAM BOT NOTIFIER
=======================================================
1. Buat bot baru di Telegram:
   - Buka Telegram, cari @BotFather
   - Kirim pesan: /newbot
   - Beri nama dan username untuk bot Anda
   - Salin BOT TOKEN yang diberikan (contoh: 123456789:ABCdefGHI...)

2. Dapatkan Chat ID Telegram Anda:
   - Buka Telegram, cari @userinfobot
   - Tekan Start, bot akan membalas dengan ID Anda (contoh: 987654321)
   - Buka chat dengan bot yang baru Anda buat di langkah 1, klik Start!

3. Masukkan ke file .env Anda:
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHI...
   TELEGRAM_CHAT_ID=987654321

4. Tes koneksi bot:
   python .agents/tools/telegram_notifier.py test "Halo dari Trading Desk!"
=======================================================
""")

def auto_pair():
    token, _ = get_telegram_config()
    if not token:
        print("[ERROR] TELEGRAM_BOT_TOKEN belum diisi di .env!")
        return

    print("=======================================================")
    print("   🔗 MODE AUTO-PAIRING TELEGRAM BOT")
    print("=======================================================")
    print("1. Buka Telegram di HP / Laptop Anda.")
    print("2. Buka bot Anda (atau klik: https://t.me/Agent_trading_bot).")
    print("3. Tekan 'START' atau kirim pesan apa saja (misal: halo).")
    print("-------------------------------------------------------")
    print("Menunggu pesan dari Telegram Anda (maksimal 60 detik)...")

    start_time = time.time()
    while time.time() - start_time < 60:
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        try:
            req = urllib.request.Request(url, headers=HEADERS, method="GET")
            with urllib.request.urlopen(req, timeout=5, context=SSL_CTX) as response:
                data = json.loads(response.read().decode("utf-8"))
                if data.get("ok") and data.get("result"):
                    # Get latest message
                    latest = data["result"][-1]
                    msg = latest.get("message")
                    if msg and msg.get("chat"):
                        chat_id = str(msg["chat"]["id"])
                        user_name = msg["chat"].get("first_name") or msg["chat"].get("username") or "Trader"

                        print(f"\n✅ Pesan diterima dari: {user_name} (Chat ID: {chat_id})!")

                        # Save to .env
                        with open(ENV_FILE, "r", encoding="utf-8") as f:
                            env_content = f.read()

                        if "TELEGRAM_CHAT_ID=" in env_content:
                            env_content = re.sub(r"TELEGRAM_CHAT_ID=.*", f"TELEGRAM_CHAT_ID={chat_id}", env_content)
                        else:
                            env_content += f"\nTELEGRAM_CHAT_ID={chat_id}\n"

                        with open(ENV_FILE, "w", encoding="utf-8") as f:
                            f.write(env_content)

                        print("💾 Chat ID berhasil disimpan ke .env!")

                        # Send welcome confirmation
                        welcome = (
                            f"🎉 <b>KONEKSI BERHASIL, {html.escape(user_name)}!</b>\n"
                            f"━━━━━━━━━━━━━━━━━━\n"
                            f"Telegram Anda resmi terhubung sebagai pengendali aman Autonomous Binance Trading Desk.\n\n"
                            f"Kirim <code>/help</code> untuk melihat daftar perintah atau <code>/status</code> untuk cek portofolio saat ini."
                        )
                        send_telegram_msg(welcome, chat_id_override=chat_id)
                        print("📬 Pesan konfirmasi telah dikirim ke Telegram Anda.")
                        print("=======================================================")
                        return
        except Exception:
            pass

        time.sleep(2)

    print("\n⏳ Waktu habis (60s). Belum ada pesan terdeteksi.")
    print("Pastikan Anda sudah menekan START di bot, lalu jalankan ulang perintah ini.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "pair":
        auto_pair()
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        test_msg = sys.argv[2] if len(sys.argv) > 2 else "🔔 Tes Notifikasi Trading Desk Akademi Crypto!"
        token, chat_id = get_telegram_config()
        if not token or not chat_id:
            print("[PERINGATAN] TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID belum diisi di .env!")
            print_setup_instructions()
        else:
            print(f"Mengirim pesan uji coba ke Chat ID {chat_id}...")
            res = send_telegram_msg(f"<b>{test_msg}</b>\n<i>Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>")
            if res and res.get("ok"):
                print("✅ Pesan berhasil terkirim ke Telegram!")
            else:
                print(f"❌ Gagal mengirim pesan: {res}")
    else:
        print_setup_instructions()

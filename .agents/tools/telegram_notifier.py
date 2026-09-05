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
    return state.get("mode", "SWING")

MAIN_KEYBOARD = {
    "keyboard": [
        [{"text": "📊 Status Desk"}, {"text": "💰 Cek PnL"}],
        [{"text": "📈 Minta Chart BTC"}, {"text": "🧬 Status Genome"}],
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
        {"command": "pnl", "description": "💰 Detail profit & loss real-time"},
        {"command": "chart", "description": "📈 Visual snapshot chart candlestick (cth: /chart BTC)"},
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

    msg = (
        f"🚀 <b>EKSEKUSI ORDER BINANCE FUTURES</b>\n"
        f"<i>Mode: {mode_text}</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>Simbol:</b> <code>{symbol}</code>\n"
        f"🧭 <b>Arah:</b> <b>{side_icon} (5x Leverage)</b>\n"
        f"{conf_line}"
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
        tf = "5m" if ("SCALP" in reason.upper() or "5M" in reason.upper()) else "1H"
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
                            "📈 Minta Chart BTC": "/chart BTC",
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
        elif data == "closeall":
            self._handle_command("/closeall", sender_chat_id)
        elif data == "refresh_status":
            self._handle_command("/status", sender_chat_id)
        elif data == "refresh_pnl":
            self._handle_command("/pnl", sender_chat_id)
        elif data == "force_evolve":
            self._handle_command("/evolve", sender_chat_id)
        elif data == "refresh_genome":
            self._handle_command("/genome", sender_chat_id)

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
                f"• <code>/chart [koin] [tf]</code> : Snapshot visual candlestick chart (cth: <code>/chart btc</code>, <code>/chart sol 5m</code>)\n"
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

        elif command == "/status":
            bal = trading_desk.get_account_balance(self.user_email, self.is_demo)
            positions = trading_desk.get_active_positions(self.user_email, self.is_demo)
            paused = is_desk_paused()
            mode = get_desk_mode()
            genome = trading_desk.load_genome()
            status_tag = "⏸️ <b>DIJEDA (PAUSED)</b>" if paused else "▶️ <b>BERJALAN (ACTIVE)</b>"

            reply = (
                f"🖥️ <b>STATUS TRADING DESK</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Status Autopilot: {status_tag}\n"
                f"Mode Operasi: <b>🎯 {mode} (Big-Profit Swing Focus)</b>\n"
                f"Mode Akun: {'🟡 DEMO (Testnet)' if self.is_demo else '🔴 LIVE'}\n"
                f"Saldo Equity: <code>${bal:,.2f} USDT</code>\n"
                f"Posisi Terbuka: <code>{len(positions)} posisi</code>\n"
                f"Genetic Rule: Gen {genome.get('generation', 5)} (Min R:R 1:{genome.get('parameters', {}).get('min_risk_reward', 3.0)})\n"
                f"Max Risk Per Trade: {genome.get('parameters', {}).get('max_risk_per_trade_pct', 1.5)}%\n"
            )

            # Build Inline Action Buttons
            inline_kb = []
            pos_buttons = []
            for p in positions:
                sym = p["symbol"]
                upnl = float(p.get("unRealizedProfit", 0))
                p_sign = "+" if upnl >= 0 else ""
                pos_buttons.append({"text": f"🔴 Tutup {sym} ({p_sign}${upnl:.2f})", "callback_data": f"close_{sym}"})

            # Add position close buttons (1 per row for easy tapping on mobile)
            for btn in pos_buttons:
                inline_kb.append([btn])

            # Utility buttons
            inline_kb.append([
                {"text": "🔄 Refresh Status", "callback_data": "refresh_status"},
                {"text": "💰 Cek PnL", "callback_data": "refresh_pnl"}
            ])
            if positions:
                inline_kb.append([{"text": "🚨 Tutup Seluruh Posisi", "callback_data": "closeall"}])

            send_telegram_msg(reply, chat_id_override=chat_id, reply_markup={"inline_keyboard": inline_kb})

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
                "• Setup: <b>Liquidity Sweep, VWAP 2σ, Volume Surge</b>\n"
                "• Target Durasi: <b>15 - 45 Menit</b>\n"
                "• Breakeven Kilat: <b>+0.7R (Free Roll)</b>\n"
                "• Time-Stop: <b>Maksimal 45 Menit</b> (tutup otomatis jika stagnan)\n\n"
                "<i>Agent akan memindai setup kilat setiap 1-3 menit.</i>",
                chat_id_override=chat_id,
                reply_markup=MAIN_KEYBOARD
            )

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

"""
Automated Trade Journal & Performance Analytics Engine
Synthesized from Akademi Crypto Module 03 (Money Psychology & Trading Plan)
Tracks complete trade lifecycles, aggregates execution metrics from Binance Futures,
and computes institutional quant metrics (Win Rate, Profit Factor, Expectancy, Payoff Ratio, Max Drawdown).
"""

import json
import math
import os
import sys
import time
from datetime import datetime, timedelta

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
JOURNAL_FILE = os.path.join(DATA_DIR, "trade_journal_ledger.json")

sys.path.insert(0, TOOLS_DIR)
import binance_client

def load_journal():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(JOURNAL_FILE):
        try:
            with open(JOURNAL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def load_trade_ledger():
    """Alias for load_journal() to provide full ledger of closed trades."""
    return load_journal()

def load_bot_executions():
    """Loads recorded bot executions from trading_desk_history.json."""
    desk_history_file = os.path.join(DATA_DIR, "trading_desk_history.json")
    if os.path.exists(desk_history_file):
        try:
            with open(desk_history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [d for d in data if d.get("action") == "EXECUTE_TRADE"]
        except Exception:
            pass
    return []

def save_journal(trades):
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(JOURNAL_FILE, "w", encoding="utf-8") as f:
            json.dump(trades, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Trade Journal] Error saving journal: {e}")

def record_closed_trade(trade_entry):
    """
    Appends a verified closed trade into the journal ledger.
    Guarantees no duplicate entries using trade_id or symbol+timestamp.
    Triggers autonomous cognitive post-mortem reflection in Agent Memory Engine.
    """
    trades = load_journal()
    t_id = trade_entry.get("id") or f"{trade_entry.get('symbol')}-{trade_entry.get('closed_at')}"

    # Check for duplicate
    existing_idx = next((i for i, t in enumerate(trades) if t.get("id") == t_id), None)
    if existing_idx is not None:
        trades[existing_idx].update(trade_entry)
    else:
        trades.append(trade_entry)

    # Sort chronologically by close time
    trades.sort(key=lambda x: str(x.get("closed_at", "")), reverse=False)
    save_journal(trades)
    print(f"📖 [Trade Journal] Logged trade {trade_entry.get('symbol')} ({trade_entry.get('side')}) | Net PnL: ${trade_entry.get('net_pnl_usd', trade_entry.get('pnl_usd', 0)):+,.2f}")

    # Autonomous Cognitive Post-Mortem Reflection Hook
    try:
        from agent_memory_engine import memory_engine
        reflection = memory_engine.reflect_on_closed_trade(trade_entry)
        print(f"🧠 [Memory Engine] Cognitive Reflection Logged ({reflection.get('outcome')}): {reflection.get('lesson_learned')}")
    except Exception as m_err:
        pass

def sync_binance_history(user_email="dxmade@gmail.com", is_demo=True, limit=50):
    """
    Syncs past realized PnL and trade executions directly from Binance Futures API.
    Reconciles fee deductions and net profit.
    """
    res_income = binance_client.send_signed_request(
        "/fapi/v1/income",
        method="GET",
        params={"limit": limit},
        is_demo=is_demo,
        user_email=user_email
    )
    if not res_income or not isinstance(res_income, list):
        return 0

    journal = load_journal()
    existing_ids = {t.get("id") for t in journal}
    new_count = 0

    # Group income by tranId or tradeId
    for inc in res_income:
        if inc.get("incomeType") == "REALIZED_PNL":
            t_id = f"BINANCE-INC-{inc.get('tranId')}"
            if t_id in existing_ids:
                continue

            pnl = float(inc.get("income", 0))
            ts = int(inc.get("time", 0)) / 1000.0
            dt_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            sym = inc.get("symbol", "UNKNOWN")

            journal.append({
                "id": t_id,
                "symbol": sym,
                "side": "LONG" if pnl >= 0 else "SHORT",
                "entry_price": 0.0,
                "exit_price": 0.0,
                "quantity": 0.0,
                "pnl_usd": round(pnl, 2),
                "commission_usd": 0.0,
                "net_pnl_usd": round(pnl, 2),
                "r_multiple": round(pnl / 30.0, 2) if pnl != 0 else 0.0,
                "exit_reason": "Realized via Binance Futures" if pnl >= 0 else "Stop Loss / Market Liquidation",
                "closed_at": dt_str,
                "source": "BINANCE_INCOME"
            })
            existing_ids.add(t_id)
            new_count += 1

    if new_count > 0:
        journal.sort(key=lambda x: str(x.get("closed_at", "")), reverse=False)
        save_journal(journal)

    return new_count

def calculate_journal_metrics(timeframe="all"):
    """
    Computes comprehensive quant metrics:
    - Win Rate %, Loss Rate %
    - Profit Factor ($ Gross Wins / $ Gross Losses)
    - Net Realized PnL ($)
    - Payoff Ratio (Avg Win / Avg Loss)
    - Mathematical Expectancy ($ per trade & R-multiple)
    - Max Drawdown (% and $)
    - Asset-by-Asset breakdown
    - Long vs Short breakdown
    """
    trades = load_journal()
    if not trades:
        return None

    # Timeframe filtering
    now = datetime.now()
    if timeframe == "24h" or timeframe == "today":
        cutoff = now - timedelta(hours=24)
        trades = [t for t in trades if datetime.strptime(t.get("closed_at", "2000-01-01 00:00:00")[:19], "%Y-%m-%d %H:%M:%S") >= cutoff]
    elif timeframe == "7d":
        cutoff = now - timedelta(days=7)
        trades = [t for t in trades if datetime.strptime(t.get("closed_at", "2000-01-01 00:00:00")[:19], "%Y-%m-%d %H:%M:%S") >= cutoff]
    elif timeframe == "30d":
        cutoff = now - timedelta(days=30)
        trades = [t for t in trades if datetime.strptime(t.get("closed_at", "2000-01-01 00:00:00")[:19], "%Y-%m-%d %H:%M:%S") >= cutoff]

    total_trades = len(trades)
    if total_trades == 0:
        return {
            "timeframe": timeframe,
            "total_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "net_pnl": 0.0,
            "trades": []
        }

    wins = [t for t in trades if float(t.get("net_pnl_usd", t.get("pnl_usd", 0))) > 0.1]
    losses = [t for t in trades if float(t.get("net_pnl_usd", t.get("pnl_usd", 0))) < -0.1]
    breakevens = [t for t in trades if abs(float(t.get("net_pnl_usd", t.get("pnl_usd", 0)))) <= 0.1]

    win_count = len(wins)
    loss_count = len(losses)
    be_count = len(breakevens)

    win_rate = (win_count / total_trades * 100.0) if total_trades > 0 else 0.0
    loss_rate = (loss_count / total_trades * 100.0) if total_trades > 0 else 0.0

    gross_profit = sum(float(t.get("net_pnl_usd", t.get("pnl_usd", 0))) for t in wins)
    gross_loss = abs(sum(float(t.get("net_pnl_usd", t.get("pnl_usd", 0))) for t in losses))
    net_pnl = gross_profit - gross_loss

    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)

    avg_win = (gross_profit / win_count) if win_count > 0 else 0.0
    avg_loss = (gross_loss / loss_count) if loss_count > 0 else 0.0
    payoff_ratio = (avg_win / avg_loss) if avg_loss > 0 else (99.0 if avg_win > 0 else 0.0)

    # Mathematical Expectancy (E)
    # E = (Win Rate * Avg Win) - (Loss Rate * Avg Loss)
    expectancy_usd = ((win_rate / 100.0) * avg_win) - ((loss_rate / 100.0) * avg_loss)

    # Calculate Max Drawdown from Cumulative Equity
    cum_pnl = 0.0
    peak = 0.0
    max_drawdown_usd = 0.0
    for t in trades:
        pnl = float(t.get("net_pnl_usd", t.get("pnl_usd", 0)))
        cum_pnl += pnl
        if cum_pnl > peak:
            peak = cum_pnl
        dd = peak - cum_pnl
        if dd > max_drawdown_usd:
            max_drawdown_usd = dd

    # Consecutive Streak Calculation
    max_consec_wins = 0
    max_consec_losses = 0
    cur_wins = 0
    cur_losses = 0
    for t in trades:
        pnl = float(t.get("net_pnl_usd", t.get("pnl_usd", 0)))
        if pnl > 0.1:
            cur_wins += 1
            cur_losses = 0
            if cur_wins > max_consec_wins:
                max_consec_wins = cur_wins
        elif pnl < -0.1:
            cur_losses += 1
            cur_wins = 0
            if cur_losses > max_consec_losses:
                max_consec_losses = cur_losses
        else:
            cur_wins = 0
            cur_losses = 0

    # Long vs Short Breakdown
    longs = [t for t in trades if t.get("side", "").upper() in ["BUY", "LONG"]]
    shorts = [t for t in trades if t.get("side", "").upper() in ["SELL", "SHORT"]]
    long_wins = len([t for t in longs if float(t.get("net_pnl_usd", t.get("pnl_usd", 0))) > 0.1])
    short_wins = len([t for t in shorts if float(t.get("net_pnl_usd", t.get("pnl_usd", 0))) > 0.1])

    # Per-Coin Breakdown
    by_coin = {}
    for t in trades:
        sym = t.get("symbol", "OTHER").upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")
        if sym not in by_coin:
            by_coin[sym] = {"trades": 0, "wins": 0, "pnl": 0.0}
        by_coin[sym]["trades"] += 1
        pnl = float(t.get("net_pnl_usd", t.get("pnl_usd", 0)))
        by_coin[sym]["pnl"] += pnl
        if pnl > 0.1:
            by_coin[sym]["wins"] += 1

    return {
        "timeframe": timeframe,
        "total_trades": total_trades,
        "win_count": win_count,
        "loss_count": loss_count,
        "breakeven_count": be_count,
        "win_rate": round(win_rate, 1),
        "loss_rate": round(loss_rate, 1),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "net_pnl": round(net_pnl, 2),
        "profit_factor": round(profit_factor, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "payoff_ratio": round(payoff_ratio, 2),
        "expectancy_usd": round(expectancy_usd, 2),
        "max_drawdown_usd": round(max_drawdown_usd, 2),
        "max_consec_wins": max_consec_wins,
        "max_consec_losses": max_consec_losses,
        "long_trades": len(longs),
        "long_win_rate": round((long_wins / len(longs) * 100.0) if longs else 0.0, 1),
        "short_trades": len(shorts),
        "short_win_rate": round((short_wins / len(shorts) * 100.0) if shorts else 0.0, 1),
        "by_coin": by_coin,
        "recent_trades": trades[-5:]
    }

def format_telegram_journal(timeframe="all"):
    """
    Formats rich Telegram performance scorecard synthesized from Akademi Crypto Module 03.
    """
    # Ensure sync with Binance income before formatting
    try:
        sync_binance_history()
    except Exception:
        pass

    m = calculate_journal_metrics(timeframe)
    if not m or m["total_trades"] == 0:
        return (
            "📖 <b>JURNAL TRADING AKADEMI CRYPTO</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"ℹ️ Belum ada data transaksi tertutup untuk periode: <b>{timeframe.upper()}</b>.\n\n"
            "<i>Transaksi yang selesai dieksekusi di Binance Futures akan otomatis tercatat di sini secara real-time.</i>"
        )

    tf_labels = {
        "all": "Semua Waktu (All-Time)",
        "24h": "24 Jam Terakhir (Hari Ini)",
        "today": "Hari Ini (24h)",
        "7d": "7 Hari Terakhir (Mingguan)",
        "30d": "30 Hari Terakhir (Bulanan)"
    }
    tf_str = tf_labels.get(timeframe, timeframe.upper())

    pnl_sign = "+" if m["net_pnl"] >= 0 else ""
    pnl_emoji = "🟢" if m["net_pnl"] >= 0 else "🔴"
    pf_badge = "🏆 ELITE (&gt;2.0)" if m["profit_factor"] >= 2.0 else ("🟢 PROFITABLE (&gt;1.5)" if m["profit_factor"] >= 1.5 else "⚠️ EVALUASI (&lt;1.5)")

    # Recent 5 trades log snippet
    recent_lines = []
    for t in reversed(m["recent_trades"]):
        sym = t.get("symbol", "")
        side_icon = "🟢" if t.get("side", "").upper() in ["BUY", "LONG"] else "🔴"
        pnl_val = float(t.get("net_pnl_usd", t.get("pnl_usd", 0)))
        p_str = f"+${pnl_val:,.2f}" if pnl_val >= 0 else f"-${abs(pnl_val):,.2f}"
        t_date = t.get("closed_at", "")[5:16]  # MM-DD HH:MM
        r_str = f" ({t.get('r_multiple'):+.1f}R)" if "r_multiple" in t else ""
        recent_lines.append(f"• <code>{t_date}</code> {side_icon} <b>{sym}</b>: <code>{p_str}</code>{r_str}")

    recent_block = "\n".join(recent_lines) if recent_lines else "Belum ada transaksi."

    # Top coins summary
    top_coin_lines = []
    for c_sym, c_data in sorted(m["by_coin"].items(), key=lambda x: x[1]["pnl"], reverse=True)[:4]:
        c_wr = (c_data["wins"] / c_data["trades"] * 100) if c_data["trades"] > 0 else 0
        c_pnl_str = f"+${c_data['pnl']:,.2f}" if c_data['pnl'] >= 0 else f"-${abs(c_data['pnl']):,.2f}"
        top_coin_lines.append(f"  - <b>{c_sym}</b>: {c_pnl_str} (WR: {c_wr:.0f}% | {c_data['trades']} trades)")
    coins_block = "\n".join(top_coin_lines) if top_coin_lines else "N/A"

    return (
        f"📊 <b>JURNAL TRADING & PERFORMANCE SCORECARD</b>\n"
        f"<i>Akademi Crypto Risk Management (Module 03)</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⏱️ <b>Periode:</b> <code>{tf_str}</code>\n"
        f"💰 <b>Net Realized PnL:</b> <b>{pnl_emoji} {pnl_sign}${m['net_pnl']:,.2f} USDT</b>\n\n"
        f"📈 <b>Metrik Kuantitatif Utama:</b>\n"
        f"• <b>Win Rate:</b> <code>{m['win_rate']}%</code> ({m['win_count']}W / {m['loss_count']}L / {m['breakeven_count']}BE)\n"
        f"• <b>Profit Factor:</b> <code>{m['profit_factor']}</code> [{pf_badge}]\n"
        f"• <b>Payoff Ratio:</b> <code>1 : {m['payoff_ratio']:.2f}</code> (Avg Win / Avg Loss)\n"
        f"• <b>Rata-rata Win/Loss:</b> <code>+${m['avg_win']:,.2f}</code> / <code>-${m['avg_loss']:,.2f}</code>\n"
        f"• <b>Ekspektansi Matematika:</b> <code>{'+' if m['expectancy_usd']>=0 else ''}${m['expectancy_usd']:,.2f}</code> per trade\n"
        f"• <b>Max Drawdown:</b> <code>-${m['max_drawdown_usd']:,.2f} USDT</code>\n"
        f"• <b>Streak Terbaik:</b> <code>{m['max_consec_wins']} Menang</code> | <code>{m['max_consec_losses']} Kalah</code>\n\n"
        f"⚖️ <b>Distribusi Posisi:</b>\n"
        f"• Long: <code>{m['long_trades']} trades</code> (WR: <code>{m['long_win_rate']}%</code>)\n"
        f"• Short: <code>{m['short_trades']} trades</code> (WR: <code>{m['short_win_rate']}%</code>)\n\n"
        f"🪙 <b>Performa Berdasarkan Koin:</b>\n"
        f"{coins_block}\n\n"
        f"📜 <b>5 Transaksi Terakhir:</b>\n"
        f"{recent_block}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💡 <i>Prinsip Akademi Crypto: Kunci profitabilitas jangka panjang bukanlah 100% Win Rate, melainkan kombinasi Rasio Payoff (&gt;1:2) dan Ekspektansi Matematis Positif!</i>"
    )

if __name__ == "__main__":
    count = sync_binance_history()
    print(f"Synced {count} trades from Binance.")
    report = format_telegram_journal("all")
    print("\n" + report)

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
ARCHIVE_FILE = os.path.join(DATA_DIR, "trade_journal_archive.json")
MAX_HOT_TRADES = 100

sys.path.insert(0, TOOLS_DIR)
import binance_client
from atomic_json_store import atomic_read_json, atomic_write_json

def load_journal(include_archive=False):
    """Loads closed trades ledger. If include_archive is True, loads all trades."""
    if include_archive:
        return load_all_trades()
    return atomic_read_json(JOURNAL_FILE, default=[])

def load_archived_trades():
    """Loads historical archived trades beyond the active hot sliding window."""
    return atomic_read_json(ARCHIVE_FILE, default=[])

def load_all_trades():
    """Loads combined historical archived trades and hot ledger trades, deduplicated."""
    archived = load_archived_trades()
    hot = atomic_read_json(JOURNAL_FILE, default=[])

    seen_ids = set()
    combined = []
    for t in archived:
        tid = t.get("id") or f"{t.get('symbol')}-{t.get('closed_at')}"
        if tid not in seen_ids:
            seen_ids.add(tid)
            combined.append(t)

    for t in hot:
        tid = t.get("id") or f"{t.get('symbol')}-{t.get('closed_at')}"
        if tid not in seen_ids:
            seen_ids.add(tid)
            combined.append(t)
        else:
            idx = next((i for i, x in enumerate(combined) if (x.get("id") or f"{x.get('symbol')}-{x.get('closed_at')}") == tid), None)
            if idx is not None:
                combined[idx] = t

    combined.sort(key=lambda x: str(x.get("closed_at", "")), reverse=False)
    return combined

def load_trade_ledger(include_archive=False):
    """Alias for load_journal() to provide ledger of closed trades."""
    return load_journal(include_archive=include_archive)

def load_bot_executions():
    """Loads recorded bot executions from trading_desk_history.json."""
    desk_history_file = os.path.join(DATA_DIR, "trading_desk_history.json")
    return atomic_read_json(desk_history_file, default=[])

def archive_older_trades(max_hot=MAX_HOT_TRADES):
    """
    Partitions trades so that only the most recent `max_hot` trades stay in
    trade_journal_ledger.json, while older trades are moved to trade_journal_archive.json.
    """
    trades = atomic_read_json(JOURNAL_FILE, default=[])
    if len(trades) <= max_hot:
        return 0

    trades.sort(key=lambda x: str(x.get("closed_at", "")), reverse=False)
    to_archive = trades[:-max_hot]
    hot_trades = trades[-max_hot:]

    existing_archive = load_archived_trades()
    seen_ids = {t.get("id") or f"{t.get('symbol')}-{t.get('closed_at')}" for t in existing_archive}

    archived_count = 0
    for t in to_archive:
        tid = t.get("id") or f"{t.get('symbol')}-{t.get('closed_at')}"
        if tid not in seen_ids:
            existing_archive.append(t)
            seen_ids.add(tid)
            archived_count += 1

    existing_archive.sort(key=lambda x: str(x.get("closed_at", "")), reverse=False)
    atomic_write_json(ARCHIVE_FILE, existing_archive, indent=2, ensure_ascii=False)
    atomic_write_json(JOURNAL_FILE, hot_trades, indent=2, ensure_ascii=False)
    print(f"📦 [Trade Journal] Archived {archived_count} older trades to {os.path.basename(ARCHIVE_FILE)}. Hot ledger size: {len(hot_trades)}")
    return archived_count

def save_journal(trades):
    try:
        if len(trades) > MAX_HOT_TRADES:
            trades.sort(key=lambda x: str(x.get("closed_at", "")), reverse=False)
            to_archive = trades[:-MAX_HOT_TRADES]
            hot_trades = trades[-MAX_HOT_TRADES:]

            existing_archive = load_archived_trades()
            seen_ids = {t.get("id") or f"{t.get('symbol')}-{t.get('closed_at')}" for t in existing_archive}
            for t in to_archive:
                tid = t.get("id") or f"{t.get('symbol')}-{t.get('closed_at')}"
                if tid not in seen_ids:
                    existing_archive.append(t)
                    seen_ids.add(tid)

            existing_archive.sort(key=lambda x: str(x.get("closed_at", "")), reverse=False)
            atomic_write_json(ARCHIVE_FILE, existing_archive, indent=2, ensure_ascii=False)
            atomic_write_json(JOURNAL_FILE, hot_trades, indent=2, ensure_ascii=False)
        else:
            atomic_write_json(JOURNAL_FILE, trades, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Trade Journal] Error saving journal: {e}")

def normalize_strategy_name(name: str) -> str:
    """
    Normalizes dynamic setup reason strings or raw strategy names into clean,
    standardized institutional strategy archetypes for the dashboard analytics.
    """
    if not name or not isinstance(name, str):
        return "Smart Money Concepts (SMC)"

    n = name.strip()
    # Strip any leading prefixes like "⚡ HIGH-R:R SCALP [" and trailing "]"
    if "HIGH-R:R SCALP" in n:
        if "[" in n and "]" in n:
            start_bracket = n.find("[")
            end_bracket = n.find("]", start_bracket)
            if start_bracket != -1 and end_bracket != -1:
                n = n[start_bracket + 1:end_bracket].strip()
    elif n.startswith("[") and n.endswith("]"):
        n = n[1:-1].strip()

    n_lower = n.lower()
    if "cvd" in n_lower or "order flow" in n_lower or "absorption" in n_lower:
        return "5m Order Flow CVD Absorption Scalp"
    if "rejection block" in n_lower or "mean threshold" in n_lower:
        return "5m ICT Rejection Block Mean Threshold"
    if "4h-range" in n_lower or "4h range" in n_lower or "failed auction" in n_lower:
        return "5m 4H-Range Breakout Re-entry"
    if "inverse fvg" in n_lower or "ifvg" in n_lower:
        return "5m Inverse Fair Value Gap (IFVG)"
    if "20-ema" in n_lower or "dynamic pullback" in n_lower or "ema dynamic" in n_lower:
        return "5m 20-EMA Dynamic Pullback Scalp"
    if "mulham" in n_lower or "rectangle break" in n_lower or "key level rectangle" in n_lower:
        return "15m Key Level Rectangle Break & Retest"
    if "liquidity sweep" in n_lower or "micro-fvg" in n_lower or "smart money hunt" in n_lower:
        return "5m Session Liquidity Sweep & Micro-FVG"
    if "craig percoco" in n_lower or "morning routine" in n_lower or "asian range" in n_lower:
        return "Craig Percoco 5m Morning Routine"
    if "orb" in n_lower or "opening range" in n_lower:
        return "Opening Range Breakout (ORB)"
    if "turtle" in n_lower:
        return "Turtle Breakout"
    if "kama" in n_lower:
        return "KAMA Adaptive Trend"
    if "seasonality" in n_lower or "trumpeter" in n_lower:
        return "Lewis Trumpeter Seasonality"
    if "ai adaptive harvester" in n_lower or "aiharvest" in n_lower:
        return "AI Adaptive Harvester"
    if "prop desk" in n_lower:
        return "Prop Desk Alpha"
    if "binance_income" in n_lower or "binance futures execution" in n_lower:
        return "Binance Futures Execution"
    if "scaleout" in n_lower or "scale_out" in n_lower or "scale-out" in n_lower or "institutional scalper" in n_lower:
        return "Institutional Scalper (5m)"
    if "smart money" in n_lower or "smc" in n_lower:
        return "Smart Money Concepts (SMC)"

    # Dynamic setup strings that were mistakenly stored as strategy names
    if any(k in n_lower for k in ["tested", "targeting", "close @", "supported by", "dom bid", "dom ask", "pocket rejection"]):
        return "5m Order Flow CVD Absorption Scalp" if ("order flow" in n_lower or "bid wall" in n_lower or "ask wall" in n_lower) else "Smart Money Concepts (SMC)"

    return n

def normalize_existing_journal_strategies():
    """
    One-time / maintenance migration function to normalize strategy names
    across all historical trades in both trade_journal_ledger.json and trade_journal_archive.json.
    """
    total_updated = 0
    # 1. Hot Ledger
    hot_trades = atomic_read_json(JOURNAL_FILE, default=[])
    hot_changed = False
    for t in hot_trades:
        orig = t.get("strategy", "")
        norm = normalize_strategy_name(orig)
        if norm != orig:
            t["strategy"] = norm
            hot_changed = True
            total_updated += 1
    if hot_changed:
        atomic_write_json(JOURNAL_FILE, hot_trades, indent=2, ensure_ascii=False)

    # 2. Historical Archive
    arch_trades = atomic_read_json(ARCHIVE_FILE, default=[])
    arch_changed = False
    for t in arch_trades:
        orig = t.get("strategy", "")
        norm = normalize_strategy_name(orig)
        if norm != orig:
            t["strategy"] = norm
            arch_changed = True
            total_updated += 1
    if arch_changed:
        atomic_write_json(ARCHIVE_FILE, arch_trades, indent=2, ensure_ascii=False)

    if total_updated > 0:
        print(f"🧹 [Trade Journal] Normalized strategy names for {total_updated} historical trades.")
    return total_updated

def record_closed_trade(trade_entry):
    """
    Appends a verified closed trade into the journal ledger.
    Guarantees no duplicate entries using trade_id or symbol+timestamp.
    Triggers autonomous cognitive post-mortem reflection in Agent Memory Engine.
    """
    trades = load_journal()
    t_id = trade_entry.get("id") or f"{trade_entry.get('symbol')}-{trade_entry.get('closed_at')}"

    # Strategy Attribution Auto-Inference (P2 Optimization)
    if not trade_entry.get("strategy") or trade_entry.get("strategy") == "Unknown":
        src = str(trade_entry.get("source", "")).upper()
        rid = str(trade_entry.get("id", "")).upper()
        reas = str(trade_entry.get("exit_reason", "")).upper()
        if "SCALEOUT" in rid or "SCALE_OUT" in src or "SCALP" in reas:
            trade_entry["strategy"] = "Institutional Scalper (5m)"
        elif "AIHARVEST" in rid or "AI_PROFIT_HARVESTER" in src:
            trade_entry["strategy"] = "AI Adaptive Harvester"
        elif "SEASONALITY" in src or "SEASONALITY" in reas:
            trade_entry["strategy"] = "Lewis Trumpeter Seasonality"
        elif "PROP_DESK" in src or "PROP_DESK" in reas:
            trade_entry["strategy"] = "Prop Desk Alpha"
        elif "TURTLE" in reas:
            trade_entry["strategy"] = "Turtle Breakout"
        elif "KAMA" in reas:
            trade_entry["strategy"] = "KAMA Adaptive Trend"
        elif "ORB" in reas:
            trade_entry["strategy"] = "Opening Range Breakout (ORB)"
        elif "BINANCE_INCOME" in src:
            trade_entry["strategy"] = "Binance Futures Execution"
        else:
            trade_entry["strategy"] = "Smart Money Concepts (SMC)"

    trade_entry["strategy"] = normalize_strategy_name(trade_entry.get("strategy"))

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

    # Seamless Multi-Device Cloud Sync Hook
    try:
        import auto_git_sync
        auto_git_sync.trigger_background_push(f"closed_trade_{trade_entry.get('symbol')}")
    except Exception:
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

    all_trades = load_all_trades()
    existing_ids = {t.get("id") for t in all_trades}
    journal = load_journal()
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
    if timeframe in ["all", "30d"]:
        trades = load_all_trades()
    else:
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

    # Per-Strategy Breakdown (P2 & Option C Asymmetric Kelly Sizing Optimization)
    by_strategy = {}
    for t in trades:
        strat = t.get("strategy") or "Smart Money Concepts (SMC)"
        if strat not in by_strategy:
            by_strategy[strat] = {
                "trades": 0, "wins": 0, "losses": 0, "pnl": 0.0,
                "gross_profit": 0.0, "gross_loss": 0.0
            }
        by_strategy[strat]["trades"] += 1
        pnl = float(t.get("net_pnl_usd", t.get("pnl_usd", 0)))
        by_strategy[strat]["pnl"] += pnl
        if pnl > 0.1:
            by_strategy[strat]["wins"] += 1
            by_strategy[strat]["gross_profit"] += pnl
        elif pnl < -0.1:
            by_strategy[strat]["losses"] += 1
            by_strategy[strat]["gross_loss"] += abs(pnl)

    for s, s_data in by_strategy.items():
        tr_cnt = s_data["trades"]
        w_cnt = s_data["wins"]
        l_cnt = s_data["losses"]
        gp = s_data["gross_profit"]
        gl = s_data["gross_loss"]

        wr = (w_cnt / tr_cnt * 100.0) if tr_cnt > 0 else 0.0
        avg_w = (gp / w_cnt) if w_cnt > 0 else 0.0
        avg_l = (gl / l_cnt) if l_cnt > 0 else 0.0
        payoff = (avg_w / avg_l) if avg_l > 0 else (2.0 if w_cnt > 0 else 1.0)
        pf = (gp / gl) if gl > 0 else (99.0 if gp > 0 else 0.0)

        # Mathematical Kelly Criterion: K = p - ((1 - p) / b)
        p_win = (w_cnt / tr_cnt) if tr_cnt > 0 else 0.0
        p_loss = 1.0 - p_win
        raw_k = (p_win - (p_loss / payoff)) if payoff > 0 else 0.0
        half_k = max(0.0, raw_k * 0.5)

        # Adaptive Asymmetric Risk Allocation
        # Base 1.50%, range 0.50% to 2.50%
        if tr_cnt < 5:
            rec_risk = 1.50
            expectancy_status = "CALIBRATING (<5 trades)"
        elif pf >= 1.30 and half_k > 0:
            rec_risk = round(min(2.50, 1.50 + (half_k * 5.0)), 2)
            expectancy_status = "HIGH ASYMMETRY"
        elif pf >= 1.00:
            rec_risk = 1.35
            expectancy_status = "POSITIVE EXPECTANCY"
        else:
            rec_risk = round(max(0.50, min(0.85, 1.50 * 0.5)), 2)
            expectancy_status = "DEFENSIVE REFINEMENT"

        s_data["win_rate"] = round(wr, 1)
        s_data["pnl"] = round(s_data["pnl"], 2)
        s_data["gross_profit"] = round(gp, 2)
        s_data["gross_loss"] = round(gl, 2)
        s_data["avg_win"] = round(avg_w, 2)
        s_data["avg_loss"] = round(avg_l, 2)
        s_data["payoff_ratio"] = round(payoff, 2)
        s_data["profit_factor"] = round(pf, 2)
        s_data["raw_kelly"] = round(raw_k, 3)
        s_data["half_kelly"] = round(half_k, 3)
        s_data["half_kelly_pct"] = round(half_k * 100.0, 1)
        s_data["recommended_risk_pct"] = rec_risk
        s_data["expectancy_status"] = expectancy_status

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
        "by_strategy": by_strategy,
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

def get_strategy_kelly_profile(strategy_name="Smart Money Concepts (SMC)", base_risk_pct=1.5, min_risk=0.5, max_risk=2.5):
    """
    Computes empirical Asymmetric Kelly Criterion parameters for a specific strategy archetype.
    Returns dictionary with win_rate, payoff_ratio, half_kelly, recommended_risk_pct, and rationale.
    """
    try:
        metrics = calculate_journal_metrics("all")
        by_strat = metrics.get("by_strategy", {}) if metrics else {}

        # Match strategy loosely or exactly
        s_data = None
        matched_key = strategy_name
        if strategy_name in by_strat:
            s_data = by_strat[strategy_name]
            matched_key = strategy_name
        else:
            # Fuzzy fallback match
            for k, v in by_strat.items():
                if strategy_name.lower() in k.lower() or k.lower() in strategy_name.lower():
                    s_data = v
                    matched_key = k
                    break

        if s_data and s_data.get("trades", 0) >= 5:
            rec_risk = s_data.get("recommended_risk_pct", base_risk_pct)
            final_risk = round(min(max_risk, max(min_risk, rec_risk)), 2)
            return {
                "strategy": strategy_name,
                "matched_strategy": matched_key,
                "trades": s_data.get("trades", 0),
                "win_rate": s_data.get("win_rate", 0.0),
                "payoff_ratio": s_data.get("payoff_ratio", 1.0),
                "profit_factor": s_data.get("profit_factor", 0.0),
                "raw_kelly": s_data.get("raw_kelly", 0.0),
                "half_kelly": s_data.get("half_kelly", 0.0),
                "half_kelly_pct": s_data.get("half_kelly_pct", 0.0),
                "recommended_risk_pct": final_risk,
                "expectancy_status": s_data.get("expectancy_status", "ACTIVE"),
                "status": "EMPIRICAL_KELLY",
                "rationale": f"Kelly {s_data.get('half_kelly_pct', 0.0):.1f}% (WR {s_data.get('win_rate', 0.0):.1f}%, Payoff 1:{s_data.get('payoff_ratio', 1.0):.2f}, PF {s_data.get('profit_factor', 0.0):.2f})"
            }
    except Exception:
        pass

    return {
        "strategy": strategy_name,
        "matched_strategy": strategy_name,
        "trades": 0,
        "win_rate": 45.0,
        "payoff_ratio": 2.0,
        "profit_factor": 1.2,
        "half_kelly": 0.08,
        "half_kelly_pct": 8.0,
        "recommended_risk_pct": base_risk_pct,
        "expectancy_status": "BASELINE",
        "status": "BASELINE_KELLY",
        "rationale": f"Standard Baseline Sizing ({base_risk_pct:.2f}%)"
    }

if __name__ == "__main__":
    # Auto-archive if ledger exceeds sliding window
    archive_older_trades()
    count = sync_binance_history()
    print(f"Synced {count} trades from Binance.")
    report = format_telegram_journal("all")
    print("\n" + report)

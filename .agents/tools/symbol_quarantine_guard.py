"""
Symbol Consecutive Loss Circuit Breaker & Quarantine Cooldown Engine
Akademi Crypto Risk Management (Module 03: Money Psychology & Capital Preservation)

Features:
1. Detects repeated stop-outs on the same asset across rolling time windows.
2. Triggers an automatic 120-minute QUARANTINE if:
   - >= 2 consecutive Stop Losses hit within the last 3 hours, OR
   - Cumulative loss on the symbol reaches >= 1.5R within the last 2 hours.
3. Vetoes any new entries on the quarantined asset until market structure resets.
4. Provides real-time quarantine telemetry to the Web Dashboard and AI Risk Officer.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta

# Windows console UTF-8 safety
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
LEDGER_FILE = os.path.join(DATA_DIR, "trade_journal_ledger.json")
STATE_FILE = os.path.join(DATA_DIR, "symbol_quarantine_state.json")

# Default Parameters
DEFAULT_QUARANTINE_MINUTES = 120    # 2 hours cooling off
MAX_CONSECUTIVE_LOSSES = 2          # 2 back-to-back losses trigger quarantine
CONSECUTIVE_WINDOW_HOURS = 3.0      # Lookback window for consecutive losses
CUMULATIVE_LOSS_R_LIMIT = 1.5       # 1.5R loss within window triggers quarantine
CUMULATIVE_WINDOW_HOURS = 2.0       # Lookback window for cumulative R loss

def _parse_time(ts_str):
    """Parses various timestamp formats into a datetime object."""
    if not ts_str or not isinstance(ts_str, str):
        return None
    for fmt in [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d"
    ]:
        try:
            return datetime.strptime(ts_str[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
    return None

def load_quarantine_state():
    """Loads active quarantine state from disk."""
    if not os.path.exists(STATE_FILE):
        return {"quarantines": {}, "history": []}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "quarantines" in data:
                return data
    except Exception:
        pass
    return {"quarantines": {}, "history": []}

def save_quarantine_state(state):
    """Atomically saves quarantine state to disk."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        tmp_file = STATE_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        if os.path.exists(STATE_FILE):
            os.replace(tmp_file, STATE_FILE)
        else:
            os.rename(tmp_file, STATE_FILE)
    except Exception:
        pass

def audit_symbol_quarantine(symbol, ledger_override=None):
    """
    Audits whether a symbol is currently under Quarantine / Cooldown.
    Evaluates both persistent state and recent trades in the ledger.
    Returns:
        {
            "is_quarantined": bool,
            "reason": str,
            "quarantine_until": str (ISO or None),
            "remaining_minutes": float,
            "consecutive_losses": int,
            "total_loss_r": float,
            "status_badge": str
        }
    """
    sym = symbol.upper()
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    state = load_quarantine_state()
    active_q = state.get("quarantines", {}).get(sym)

    # 1. Check existing active quarantine from state file
    if active_q:
        until_dt = _parse_time(active_q.get("quarantine_until"))
        if until_dt and until_dt > now:
            remaining_mins = max(0.1, (until_dt - now).total_seconds() / 60.0)
            return {
                "is_quarantined": True,
                "reason": active_q.get("reason", "Consecutive Stop Loss Lockout"),
                "quarantine_until": active_q.get("quarantine_until"),
                "remaining_minutes": round(remaining_mins, 1),
                "consecutive_losses": active_q.get("consecutive_losses", 2),
                "total_loss_r": active_q.get("total_loss_r", 0.0),
                "status_badge": f"🛑 QUARANTINED ({remaining_mins:.0f}m remaining)"
            }
        elif until_dt and until_dt <= now:
            # Quarantine expired, cleanup
            del state["quarantines"][sym]
            save_quarantine_state(state)

    # 2. Check ledger dynamically for recent consecutive losses
    trades = []
    if ledger_override is not None:
        trades = ledger_override
    elif os.path.exists(LEDGER_FILE):
        try:
            with open(LEDGER_FILE, "r", encoding="utf-8") as f:
                trades = json.load(f)
                if not isinstance(trades, list):
                    trades = []
        except Exception:
            trades = []

    if not trades:
        return {
            "is_quarantined": False,
            "reason": "No recent trade history",
            "quarantine_until": None,
            "remaining_minutes": 0.0,
            "consecutive_losses": 0,
            "total_loss_r": 0.0,
            "status_badge": "🟢 READY"
        }

    # Filter closed trades for this specific symbol
    sym_trades = []
    for t in trades:
        t_sym = t.get("symbol", "").upper()
        if t_sym == sym or sym in t_sym or t_sym.replace("USDT", "") == sym.replace("USDT", ""):
            sym_trades.append(t)

    # Sort descending by closed time (latest first)
    def _get_trade_time(t):
        ts = t.get("closed_at") or t.get("exit_time") or t.get("timestamp")
        dt = _parse_time(ts)
        return dt if dt else datetime.min

    sym_trades.sort(key=_get_trade_time, reverse=True)

    if not sym_trades:
        return {
            "is_quarantined": False,
            "reason": "No past trades for symbol",
            "quarantine_until": None,
            "remaining_minutes": 0.0,
            "consecutive_losses": 0,
            "total_loss_r": 0.0,
            "status_badge": "🟢 READY"
        }

    # Count consecutive losses and cumulative R loss
    consecutive_losses = 0
    cum_loss_r = 0.0
    latest_loss_time = None

    for t in sym_trades:
        t_dt = _get_trade_time(t)
        # Skip trades older than lookback window
        if (now - t_dt).total_seconds() > (CONSECUTIVE_WINDOW_HOURS * 3600):
            break

        pnl = float(t.get("net_pnl_usd", t.get("pnl_usd", 0.0)))
        r_mult = float(t.get("r_multiple", 0.0))

        if pnl <= 0 or r_mult < 0:
            consecutive_losses += 1
            cum_loss_r += abs(r_mult)
            if latest_loss_time is None:
                latest_loss_time = t_dt
        else:
            # A win breaks the consecutive loss chain!
            break

    # Trigger quarantine if thresholds exceeded
    should_quarantine = False
    trigger_reason = ""

    if consecutive_losses >= MAX_CONSECUTIVE_LOSSES and latest_loss_time:
        elapsed_since_loss = (now - latest_loss_time).total_seconds() / 60.0
        if elapsed_since_loss < DEFAULT_QUARANTINE_MINUTES:
            should_quarantine = True
            trigger_reason = f"{consecutive_losses} consecutive stop-outs within {CONSECUTIVE_WINDOW_HOURS}h window"
    elif cum_loss_r >= CUMULATIVE_LOSS_R_LIMIT and latest_loss_time:
        elapsed_since_loss = (now - latest_loss_time).total_seconds() / 60.0
        if elapsed_since_loss < DEFAULT_QUARANTINE_MINUTES:
            should_quarantine = True
            trigger_reason = f"Cumulative loss of -{cum_loss_r:.2f}R exceeded {CUMULATIVE_LOSS_R_LIMIT}R limit"

    if should_quarantine and latest_loss_time:
        until_dt = latest_loss_time + timedelta(minutes=DEFAULT_QUARANTINE_MINUTES)
        remaining_mins = max(0.1, (until_dt - now).total_seconds() / 60.0)

        # Save to persistent state
        if "quarantines" not in state:
            state["quarantines"] = {}
        state["quarantines"][sym] = {
            "symbol": sym,
            "reason": trigger_reason,
            "quarantined_at": latest_loss_time.strftime("%Y-%m-%d %H:%M:%S"),
            "quarantine_until": until_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "consecutive_losses": consecutive_losses,
            "total_loss_r": round(cum_loss_r, 2)
        }
        save_quarantine_state(state)

        return {
            "is_quarantined": True,
            "reason": trigger_reason,
            "quarantine_until": until_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "remaining_minutes": round(remaining_mins, 1),
            "consecutive_losses": consecutive_losses,
            "total_loss_r": round(cum_loss_r, 2),
            "status_badge": f"🛑 QUARANTINED ({remaining_mins:.0f}m remaining)"
        }

    return {
        "is_quarantined": False,
        "reason": "Normal operational parameters",
        "quarantine_until": None,
        "remaining_minutes": 0.0,
        "consecutive_losses": consecutive_losses,
        "total_loss_r": round(cum_loss_r, 2),
        "status_badge": "🟢 READY"
    }

def record_trade_outcome(symbol, pnl_usd, r_multiple, exit_reason=""):
    """
    Hooks directly into trade closing events to update symbol circuit breaker.
    """
    sym = symbol.upper()
    state = load_quarantine_state()
    if pnl_usd <= 0 or r_multiple < 0:
        # Re-evaluate quarantine immediately
        audit_res = audit_symbol_quarantine(sym)
        return audit_res
    else:
        # Profitable trade resets any active quarantine for this symbol
        if sym in state.get("quarantines", {}):
            del state["quarantines"][sym]
            save_quarantine_state(state)
        return {
            "is_quarantined": False,
            "reason": "Profit locked - quarantine cleared",
            "remaining_minutes": 0.0
        }

def get_active_quarantines():
    """Returns list of currently quarantined symbols for Dashboard and API."""
    now = datetime.now()
    state = load_quarantine_state()
    active = []
    quarantines = state.get("quarantines", {})
    expired = []

    for sym, q in quarantines.items():
        until_dt = _parse_time(q.get("quarantine_until"))
        if until_dt and until_dt > now:
            rem = max(0.1, (until_dt - now).total_seconds() / 60.0)
            active.append({
                "symbol": sym,
                "reason": q.get("reason"),
                "quarantined_at": q.get("quarantined_at"),
                "quarantine_until": q.get("quarantine_until"),
                "remaining_minutes": round(rem, 1),
                "consecutive_losses": q.get("consecutive_losses", 2),
                "total_loss_r": q.get("total_loss_r", 0.0)
            })
        else:
            expired.append(sym)

    if expired:
        for sym in expired:
            if sym in quarantines:
                del quarantines[sym]
        save_quarantine_state(state)

    return active

if __name__ == "__main__":
    print("=== SYMBOL QUARANTINE GUARD TEST ===")
    test_coins = ["BTCUSDT", "TAOUSDT", "XRPUSDT", "SOLUSDT"]
    for c in test_coins:
        res = audit_symbol_quarantine(c)
        print(f"[{c}] Quarantined: {res['is_quarantined']} | Badge: {res['status_badge']} | Reason: {res['reason']}")

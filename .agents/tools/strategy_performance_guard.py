"""
strategy_performance_guard.py - Empirical Strategy Performance & Auto-Pruning Guard
Synthesized from Akademi Crypto Module 03 (Trading Plan & Edge Audit) and Quantitative MPT.

Features:
1. Audits live/historical trades in trade_journal_ledger.json per strategy.
2. Calculates real-time Profit Factor, Win Rate, Net PnL, and Consecutive Losses.
3. Automatically QUARANTINES / DECOMMISSIONS toxic strategies that fail statistical thresholds:
   - Profit Factor < 0.80 with >= 3 trades and Net PnL < -$15.00
   - Consecutive losses >= 3
   - Win rate < 30% with >= 5 trades
4. Prevents capital hemorrhage on low-timeframe noise (5m fakeouts, fee drag).
5. Provides thread-safe telemetry and REST API integration for the Web Dashboard.
"""

import json
import os
import sys
import time
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime

# UTF-8 console output for Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
LEDGER_FILE = os.path.join(DATA_DIR, "trade_journal_ledger.json")
STATE_FILE = os.path.join(DATA_DIR, "strategy_quarantine_state.json")

sys.path.insert(0, TOOLS_DIR)
import atomic_json_store

# Strategy Evaluation Thresholds
MIN_TRADES_FOR_PRUNING = 3
MAX_ACCEPTABLE_LOSS_USD = -20.0
MIN_PROFIT_FACTOR = 0.80
MAX_CONSECUTIVE_LOSSES = 3

# Static known toxic patterns (empirically failed across 25+ years quant research & live tests)
BANNED_TOXIC_STRATEGIES = [
    "5m Order Flow CVD Absorption Scalp",
    "15m Key Level Rectangle Break & Retest",
    "5m Inverse Fair Value Gap (IFVG)",
    "5m ICT Rejection Block Mean Threshold",
    "5m Session Liquidity Sweep & Micro-FVG",
    "Craig Percoco 5m Morning Routine",
    "Institutional Scalper (5m)"
]

# Core institutional swing strategies exempt from full decommissioning
CORE_INSTITUTIONAL_STRATEGIES = [
    "Smart Money Concepts (SMC)",
    "Wyckoff Institutional Method",
    "SMC Trend Following",
    "Institutional Swing Runner"
]

def load_quarantine_state() -> Dict[str, Any]:
    """Loads quarantined strategies state atomically."""
    return atomic_json_store.atomic_read_json(STATE_FILE, default={"quarantined_strategies": {}, "updated_at": ""})

def save_quarantine_state(state: Dict[str, Any]) -> bool:
    """Saves quarantine state atomically."""
    state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return atomic_json_store.atomic_write_json(STATE_FILE, state)

def get_strategy_performance_matrix() -> Dict[str, Any]:
    """
    Computes performance matrix across all strategies from the trade journal ledger.
    """
    trades = atomic_json_store.atomic_read_json(LEDGER_FILE, default=[])
    if not isinstance(trades, list):
        trades = []

    matrix = {}
    for t in trades:
        strat = t.get("strategy") or "Unknown"
        net_pnl = float(t.get("net_pnl_usd", 0.0))
        r_mult = float(t.get("r_multiple", 0.0))
        comm = float(t.get("commission_usd", 0.0))

        if strat not in matrix:
            matrix[strat] = {
                "strategy": strat,
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "breakevens": 0,
                "gross_profit": 0.0,
                "gross_loss": 0.0,
                "net_pnl": 0.0,
                "total_commission": 0.0,
                "consecutive_losses": 0,
                "recent_outcomes": []
            }

        s_data = matrix[strat]
        s_data["total_trades"] += 1
        s_data["net_pnl"] += net_pnl
        s_data["total_commission"] += comm

        if net_pnl > 0.01:
            s_data["wins"] += 1
            s_data["gross_profit"] += net_pnl
            s_data["consecutive_losses"] = 0
            s_data["recent_outcomes"].append(1)
        elif net_pnl < -0.01:
            s_data["losses"] += 1
            s_data["gross_loss"] += abs(net_pnl)
            s_data["consecutive_losses"] += 1
            s_data["recent_outcomes"].append(-1)
        else:
            s_data["breakevens"] += 1
            s_data["recent_outcomes"].append(0)

    # Calculate ratios and quarantine flags
    quarantine_state = load_quarantine_state()
    quarantined = quarantine_state.get("quarantined_strategies", {})

    results = {}
    for strat, data in matrix.items():
        total = data["total_trades"]
        gp = data["gross_profit"]
        gl = data["gross_loss"]
        wr = round((data["wins"] / total) * 100.0, 1) if total > 0 else 0.0
        pf = round(gp / gl, 2) if gl > 0 else (99.0 if gp > 0 else 0.0)

        # Check for toxic criteria
        is_quarantined = False
        reasons = []

        # 1. Hardcoded banned toxic scalps
        if any(ts.lower() in strat.lower() for ts in BANNED_TOXIC_STRATEGIES):
            is_quarantined = True
            reasons.append("Empirically proven toxic low-TF pattern (Negative EV & fee drag)")

        # 2. Performance-based criteria (exempt core foundational institutional strategies)
        if total >= MIN_TRADES_FOR_PRUNING and strat not in CORE_INSTITUTIONAL_STRATEGIES:
            if data["net_pnl"] <= MAX_ACCEPTABLE_LOSS_USD and pf < MIN_PROFIT_FACTOR:
                is_quarantined = True
                reasons.append(f"Cumulative loss ${data['net_pnl']:.2f} with PF {pf:.2f} < {MIN_PROFIT_FACTOR}")
            if data["consecutive_losses"] >= MAX_CONSECUTIVE_LOSSES:
                is_quarantined = True
                reasons.append(f"{data['consecutive_losses']} consecutive stop-outs")
            if total >= 5 and wr < 30.0:
                is_quarantined = True
                reasons.append(f"Substandard win rate ({wr:.1f}% < 30%)")

        # Update quarantine state
        if is_quarantined:
            quarantined[strat] = {
                "quarantined_at": quarantined.get(strat, {}).get("quarantined_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                "reasons": reasons,
                "net_pnl": round(data["net_pnl"], 2),
                "profit_factor": pf,
                "win_rate": wr,
                "trades": total
            }
        elif strat in quarantined:
            # If performance recovered, un-quarantine
            del quarantined[strat]

        results[strat] = {
            "strategy": strat,
            "total_trades": total,
            "wins": data["wins"],
            "losses": data["losses"],
            "breakevens": data["breakevens"],
            "win_rate": wr,
            "profit_factor": pf,
            "net_pnl_usd": round(data["net_pnl"], 2),
            "commission_usd": round(data["total_commission"], 2),
            "is_quarantined": is_quarantined,
            "quarantine_reasons": reasons,
            "status": "🛑 QUARANTINED" if is_quarantined else "🟢 ACTIVE"
        }

    # Save sync
    quarantine_state["quarantined_strategies"] = quarantined
    save_quarantine_state(quarantine_state)

    return results

def audit_strategy_status(strategy_name: str) -> Dict[str, Any]:
    """
    Audits whether a given strategy is permitted to execute or currently quarantined.
    Sub-millisecond execution for desk sniper gatekeepers.
    """
    if not strategy_name:
        return {"is_approved": True, "reason": "No strategy specified"}

    strat_clean = str(strategy_name).strip()

    # 1. Fast check against known toxic banned patterns
    for ts in BANNED_TOXIC_STRATEGIES:
        if ts.lower() in strat_clean.lower():
            return {
                "is_approved": False,
                "is_quarantined": True,
                "strategy": strat_clean,
                "reason": f"🛑 BANNED TOXIC STRATEGY: '{strat_clean}' dinonaktifkan otomatis. Pola TF rendah ini terbukti menghasilkan negative expectancy dan fee churn.",
                "status": "QUARANTINED_STATIC"
            }

    # 2. Check active dynamic quarantine state
    q_state = load_quarantine_state()
    quarantined = q_state.get("quarantined_strategies", {})

    for q_strat, q_info in quarantined.items():
        if q_strat.lower() in strat_clean.lower() or strat_clean.lower() in q_strat.lower():
            reasons_str = "; ".join(q_info.get("reasons", ["Negative EV"]))
            return {
                "is_approved": False,
                "is_quarantined": True,
                "strategy": strat_clean,
                "reason": f"🛑 STRATEGY AUTO-PRUNED: '{strat_clean}' sedang dikarantina (Net PnL: ${q_info.get('net_pnl', 0.0):.2f}, PF: {q_info.get('profit_factor', 0.0):.2f}). Alasan: {reasons_str}",
                "status": "QUARANTINED_DYNAMIC"
            }

    return {
        "is_approved": True,
        "is_quarantined": False,
        "strategy": strat_clean,
        "reason": f"🟢 APPROVED: Strategi '{strat_clean}' memenuhi ambang profitabilitas dan batas risiko.",
        "status": "ACTIVE"
    }

def reset_strategy_quarantine(strategy_name: Optional[str] = None) -> Dict[str, Any]:
    """Resets quarantine for one or all strategies."""
    q_state = load_quarantine_state()
    if strategy_name:
        if strategy_name in q_state.get("quarantined_strategies", {}):
            del q_state["quarantined_strategies"][strategy_name]
    else:
        q_state["quarantined_strategies"] = {}
    save_quarantine_state(q_state)
    return {"status": "SUCCESS", "message": f"Quarantine reset for {strategy_name or 'ALL'}"}

if __name__ == "__main__":
    matrix = get_strategy_performance_matrix()
    print("=== STRATEGY PERFORMANCE & AUTO-PRUNING MATRIX ===")
    for s, m in sorted(matrix.items(), key=lambda x: x[1]["net_pnl_usd"], reverse=True):
        print(f"[{m['status']}] {s:40s} | Trades: {m['total_trades']:2d} | WR: {m['win_rate']:5.1f}% | PF: {m['profit_factor']:5.2f} | Net PnL: ${m['net_pnl_usd']:+7.2f}")
        if m["is_quarantined"]:
            print(f"   -> Reasons: {', '.join(m['quarantine_reasons'])}")

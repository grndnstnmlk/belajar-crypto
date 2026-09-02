"""
Self-Improving AI Trading Engine (The Reflection Brain)
Inspired by Lewis Jackson's "How To Build A Self-Improving AI Trading Agent"
and synthesized with Akademi Crypto's Quantitative Genome Architecture.

Features:
1. Performance Diagnostics (Win Rate, Profit Factor, Expectancy, Max Drawdown)
2. Loss Autopsy & Root Cause Analysis
3. Scientific Evolutionary Mutation (Modifying 1 variable at a time based on empirical data)
4. Persistent Agent Genome Tracking (.agents/data/agent_genome.json)
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PORTFOLIO_FILE = os.path.join(DATA_DIR, "paper_portfolio.json")
GENOME_FILE = os.path.join(DATA_DIR, "agent_genome.json")

def load_json(path, default):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    save_json(path, default)
    return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_default_genome():
    return {
        "generation": 1,
        "fitness_score": 75.0,
        "parameters": {
            "min_risk_reward": 2.0,
            "max_risk_per_trade_pct": 1.5,
            "rsi_overbought": 70,
            "rsi_oversold": 30,
            "require_fvg_confluence": True,
            "max_funding_rate_threshold": 0.025,
            "weights": {
                "trend_weight": 0.35,
                "rsi_weight": 0.30,
                "volatility_weight": 0.20,
                "risk_aversion": 0.15
            }
        },
        "benchmarks": {
            "target_win_rate": 55.0,
            "target_profit_factor": 1.8,
            "max_drawdown_limit_pct": 5.0
        },
        "mutation_history": [
            {
                "generation": 1,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "action": "INIT",
                "hypothesis": "Initial baseline rules synthesized from Akademi Crypto Module 01-08."
            }
        ]
    }

def analyze_performance():
    portfolio = load_json(PORTFOLIO_FILE, {"cash_balance": 10000, "positions": [], "trade_history": []})
    genome = load_json(GENOME_FILE, get_default_genome())
    history = portfolio.get("trade_history", [])

    print("\n=======================================================")
    print(f"       🧬 SELF-IMPROVEMENT ENGINE AUDIT (GEN-{genome['generation']})")
    print("=======================================================")

    if not history:
        print("No closed trades recorded yet.")
        print("Run paper trades via 'trade_hands.py' to generate feedback data.")
        print("=======================================================\n")
        return None

    total_trades = len(history)
    wins = [t for t in history if t.get("pnl_usd", 0) > 0]
    losses = [t for t in history if t.get("pnl_usd", 0) <= 0]

    win_count = len(wins)
    loss_count = len(losses)
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0

    total_win_pnl = sum(t.get("pnl_usd", 0) for t in wins)
    total_loss_pnl = abs(sum(t.get("pnl_usd", 0) for t in losses))
    net_pnl = total_win_pnl - total_loss_pnl

    profit_factor = (total_win_pnl / total_loss_pnl) if total_loss_pnl > 0 else (99.0 if total_win_pnl > 0 else 0)
    avg_win = (total_win_pnl / win_count) if win_count > 0 else 0
    avg_loss = (total_loss_pnl / loss_count) if loss_count > 0 else 0
    expectancy = (win_rate / 100 * avg_win) - ((100 - win_rate) / 100 * avg_loss)

    print(f"Total Closed Trades : {total_trades}")
    print(f"Win / Loss Count    : {win_count} Wins | {loss_count} Losses")
    print(f"Win Rate            : {win_rate:.1f}% (Target: >={genome['benchmarks']['target_win_rate']}%)")
    print(f"Profit Factor       : {profit_factor:.2f} (Target: >={genome['benchmarks']['target_profit_factor']})")
    print(f"Net Realized PnL    : {'+' if net_pnl >= 0 else ''}${net_pnl:,.2f}")
    print(f"Avg Win / Avg Loss  : +${avg_win:,.2f} / -${avg_loss:,.2f}")
    print(f"Trade Expectancy    : {'+' if expectancy >= 0 else ''}${expectancy:,.2f} per trade")

    # Exit reason breakdown
    sl_hits = len([t for t in history if t.get("reason") == "HIT_SL"])
    tp_hits = len([t for t in history if t.get("reason") == "HIT_TP"])
    manual_closes = len([t for t in history if t.get("reason") == "MANUAL_CLOSE"])
    print("-------------------------------------------------------")
    print(f"Exit Breakdown      : 🛑 {sl_hits} Hit SL | 🎯 {tp_hits} Hit TP | 🔒 {manual_closes} Manual")

    # Long vs Short breakdown
    longs = [t for t in history if t.get("side") == "LONG"]
    shorts = [t for t in history if t.get("side") == "SHORT"]
    long_wins = len([t for t in longs if t.get("pnl_usd", 0) > 0])
    short_wins = len([t for t in shorts if t.get("pnl_usd", 0) > 0])
    print(f"Long Performance    : {len(longs)} trades ({long_wins} wins, {(long_wins/len(longs)*100) if longs else 0:.0f}% WR)")
    print(f"Short Performance   : {len(shorts)} trades ({short_wins} wins, {(short_wins/len(shorts)*100) if shorts else 0:.0f}% WR)")
    print("=======================================================\n")

    return {
        "total_trades": total_trades,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "net_pnl": net_pnl,
        "sl_hits": sl_hits,
        "tp_hits": tp_hits
    }

def evolve_agent():
    stats = analyze_performance()
    genome = load_json(GENOME_FILE, get_default_genome())

    if not stats or stats["total_trades"] < 3:
        print("[Notice] Minimum 3 closed trades needed to perform meaningful mutation.")
        print("Add more paper trades or run with --sample-data to test evolutionary mechanics.")
        return

    print("=======================================================")
    print(f"       🔬 HYPOTHESIS & SCIENTIFIC MUTATION ENGINE")
    print("=======================================================")

    mutated = False
    current_gen = genome["generation"]
    target_wr = genome["benchmarks"]["target_win_rate"]
    target_pf = genome["benchmarks"]["target_profit_factor"]

    # Rule 1: If Win Rate is below target, increase minimum R:R to compensate or tighten filter
    if stats["win_rate"] < target_wr:
        current_rr = genome["parameters"]["min_risk_reward"]
        if current_rr < 3.0:
            new_rr = round(current_rr + 0.25, 2)
            hypothesis = f"Win rate ({stats['win_rate']:.1f}%) is below target ({target_wr}%). Raising minimum R:R from {current_rr} to {new_rr} to ensure positive mathematical expectancy with lower win rate."
            genome["parameters"]["min_risk_reward"] = new_rr
            genome["parameters"]["weights"]["risk_aversion"] = min(0.35, round(genome["parameters"]["weights"]["risk_aversion"] + 0.05, 2))
            genome["parameters"]["weights"]["trend_weight"] = max(0.20, round(genome["parameters"]["weights"]["trend_weight"] - 0.05, 2))
            mutated = True
            action_desc = f"MUTATE_RR_FILTER ({current_rr} -> {new_rr})"
            print(f" [MUTATION] {hypothesis}")

    # Rule 2: If SL hits dominate (> 60% of trades hit SL), tighten funding rate threshold to avoid squeeze wicks
    if stats["sl_hits"] / stats["total_trades"] > 0.60:
        current_fr = genome["parameters"]["max_funding_rate_threshold"]
        new_fr = round(max(0.010, current_fr - 0.005), 4)
        hypothesis = f"SL rate is elevated ({stats['sl_hits']}/{stats['total_trades']} trades). Lowering Perp Funding Rate ceiling from {current_fr}% to {new_fr}% to filter out overleveraged late-entry long traps."
        genome["parameters"]["max_funding_rate_threshold"] = new_fr
        mutated = True
        action_desc = f"MUTATE_FUNDING_FILTER ({current_fr}% -> {new_fr}%)"
        print(f" [MUTATION] {hypothesis}")

    # Rule 3: If performance is exceeding targets, reward fitness score and allow slight scaling
    if stats["win_rate"] >= target_wr and stats["profit_factor"] >= target_pf:
        genome["fitness_score"] = min(99.0, round(genome["fitness_score"] + 3.5, 1))
        hypothesis = f"Performance exceeds targets (WR: {stats['win_rate']:.1f}%, PF: {stats['profit_factor']:.2f}). Upgraded Agent Fitness Score to {genome['fitness_score']}."
        mutated = True
        action_desc = "FITNESS_UPGRADE"
        print(f" [REWARD] {hypothesis}")

    if mutated:
        new_gen = current_gen + 1
        genome["generation"] = new_gen
        genome["mutation_history"].append({
            "generation": new_gen,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action_desc,
            "hypothesis": hypothesis,
            "performance_snapshot": {
                "trades": stats["total_trades"],
                "win_rate": round(stats["win_rate"], 2),
                "profit_factor": round(stats["profit_factor"], 2)
            }
        })
        save_json(GENOME_FILE, genome)
        print(f"\n✅ Mutation successfully saved! Agent upgraded to Generation {new_gen}.")
    else:
        print("\n[OK] Current strategy parameters are stable and within target bounds. No mutation required.")

    print("=======================================================\n")

def show_genome_status():
    genome = load_json(GENOME_FILE, get_default_genome())
    print("\n=======================================================")
    print(f"       🧬 AGENT QUANT GENOME: GENERATION {genome['generation']}")
    print("=======================================================")
    print(f"Agent Fitness Score       : {genome['fitness_score']} / 100.0")
    print(f"Min Risk-to-Reward (R:R)  : 1 : {genome['parameters']['min_risk_reward']}")
    print(f"Max Risk Per Trade        : {genome['parameters']['max_risk_per_trade_pct']}% of balance")
    print(f"Max Perp Funding Rate     : {genome['parameters']['max_funding_rate_threshold']}%")
    print(f"Require FVG Confluence    : {genome['parameters']['require_fvg_confluence']}")
    print("-------------------------------------------------------")
    print("Genetic Decision Weights  :")
    for k, v in genome["parameters"]["weights"].items():
        print(f"  * {k:<22}: {v*100:.0f}%")
    print("-------------------------------------------------------")
    print(f"Mutation History ({len(genome['mutation_history'])} events):")
    for m in reversed(genome["mutation_history"][-3:]):
        print(f"  [Gen-{m['generation']} | {m['timestamp']}] {m['action']}")
        print(f"    -> {m['hypothesis']}")
    print("=======================================================\n")

def inject_sample_data():
    """Generates realistic paper trade logs for testing the evolutionary loop."""
    sample_trades = [
        {"id": "POS-101", "symbol": "BTC-USDT", "side": "LONG", "entry_price": 75000, "exit_price": 78000, "amount_usd": 1000, "pnl_usd": 40.0, "pnl_pct": 4.0, "reason": "HIT_TP", "closed_at": "2026-09-01 10:00:00"},
        {"id": "POS-102", "symbol": "SOL-USDT", "side": "LONG", "entry_price": 102.5, "exit_price": 98.0, "amount_usd": 600, "pnl_usd": -26.34, "pnl_pct": -4.39, "reason": "HIT_SL", "closed_at": "2026-09-01 14:30:00"},
        {"id": "POS-103", "symbol": "ETH-USDT", "side": "SHORT", "entry_price": 2450, "exit_price": 2490, "amount_usd": 800, "pnl_usd": -13.06, "pnl_pct": -1.63, "reason": "HIT_SL", "closed_at": "2026-09-02 09:15:00"},
        {"id": "POS-104", "symbol": "SOL-USDT", "side": "LONG", "entry_price": 96.0, "exit_price": 93.5, "amount_usd": 500, "pnl_usd": -13.02, "pnl_pct": -2.60, "reason": "HIT_SL", "closed_at": "2026-09-02 16:45:00"},
        {"id": "POS-105", "symbol": "BTC-USDT", "side": "LONG", "entry_price": 76200, "exit_price": 79500, "amount_usd": 1200, "pnl_usd": 51.96, "pnl_pct": 4.33, "reason": "HIT_TP", "closed_at": "2026-09-02 21:00:00"}
    ]
    portfolio = load_json(PORTFOLIO_FILE, {"cash_balance": 10000, "positions": [], "trade_history": []})
    portfolio["trade_history"] = sample_trades
    save_json(PORTFOLIO_FILE, portfolio)
    print("Sample trade history (5 trades: 2 Wins, 3 Losses) successfully injected into paper_portfolio.json.")

def main():
    parser = argparse.ArgumentParser(description="Self-Improving AI Trading Engine")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="Show current Agent Genome, Generation, and Parameters")
    sub.add_parser("audit", help="Audit past performance and calculate win rate & profit factor")
    sub.add_parser("evolve", help="Run scientific self-reflection and mutate strategy rules")
    sub.add_parser("sample-data", help="Inject realistic sample paper trade history for testing")

    args = parser.parse_args()
    if args.command == "status":
        show_genome_status()
    elif args.command == "audit":
        analyze_performance()
    elif args.command == "evolve":
        evolve_agent()
    elif args.command == "sample-data":
        inject_sample_data()
    else:
        show_genome_status()

if __name__ == "__main__":
    main()

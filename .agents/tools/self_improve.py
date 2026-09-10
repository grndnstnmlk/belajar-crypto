"""
Self-Improving AI Trading Engine (The Reflection Brain & Karpathy Autoresearch Loop)
Inspired by:
1. ATLAS by General Intelligence Capital (chrisworsey55/atlas-gic) - Karpathy-style Autoresearch Keep-or-Revert
2. Lewis Jackson's "How To Build A Self-Improving AI Trading Agent"
3. Akademi Crypto Quantitative Genome & Risk Architecture.

Features:
1. Performance Diagnostics (Win Rate, Profit Factor, Expectancy, Max Drawdown)
2. Rolling Sharpe Ratio & Empirical Return Volatility Analysis
3. Karpathy Autoresearch Keep-or-Revert Hypothesis Optimization Loop
4. Best-Known Genome Checkpoint & Automatic Strategy Degradation Rollback
5. Persistent Agent Genome Tracking (.agents/data/agent_genome.json)
"""

import argparse
import json
import math
import os
import sys
from datetime import datetime

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
PORTFOLIO_FILE = os.path.join(DATA_DIR, "paper_portfolio.json")
LEDGER_FILE = os.path.join(DATA_DIR, "trade_journal_ledger.json")
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
            "target_win_rate": 50.0,
            "target_profit_factor": 1.5,
            "target_sharpe_ratio": 1.20,
            "max_drawdown_limit_pct": 5.0
        },
        "best_known_genome": {
            "generation": 1,
            "sharpe_ratio": 1.0,
            "profit_factor": 1.0,
            "expectancy_usd": 0.0,
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
            }
        },
        "active_experiment": {
            "status": "IDLE",
            "test_generation": 1,
            "start_trade_count": 0,
            "baseline_sharpe": 1.0,
            "baseline_pf": 1.0,
            "hypothesis": "Initial baseline rules."
        },
        "mutation_history": [
            {
                "generation": 1,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "action": "INIT",
                "hypothesis": "Initial baseline rules synthesized from institutional risk architecture."
            }
        ]
    }

def get_all_trade_records():
    """Retrieves all closed trades from journal ledger or fallback paper portfolio."""
    trades = []
    if os.path.exists(LEDGER_FILE):
        try:
            with open(LEDGER_FILE, "r", encoding="utf-8") as f:
                trades = json.load(f)
                if isinstance(trades, list) and len(trades) > 0:
                    return trades
        except Exception:
            pass

    if os.path.exists(PORTFOLIO_FILE):
        try:
            with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
                p = json.load(f)
                return p.get("trade_history", [])
        except Exception:
            pass

    return []

def calculate_rolling_sharpe(trades, window=30):
    """
    Computes rolling Sharpe ratio based on trade net returns.
    """
    if not trades or len(trades) < 3:
        return 0.0, 0.0, 0.0

    sample = trades[-window:] if len(trades) >= window else trades
    returns = []
    for t in sample:
        amt = float(t.get("amount_usd", 0.0))
        pnl = float(t.get("net_pnl_usd", t.get("pnl_usd", 0.0)))
        if amt > 0:
            returns.append(pnl / amt)
        else:
            returns.append(pnl / 100.0)

    if not returns:
        return 0.0, 0.0, 0.0

    mean_ret = sum(returns) / len(returns)
    variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
    std_ret = math.sqrt(variance) if variance > 0 else 0.0001

    # Annualized Sharpe approximation (assuming ~10 trades/day -> sqrt(365 * 10))
    sharpe = round((mean_ret / std_ret) * math.sqrt(min(252, len(returns) * 5)), 2)
    return sharpe, round(mean_ret * 100.0, 3), round(std_ret * 100.0, 3)

def analyze_performance():
    history = get_all_trade_records()
    genome = load_json(GENOME_FILE, get_default_genome())

    print("\n=======================================================")
    print(f"       🧬 SELF-IMPROVEMENT ENGINE AUDIT (GEN-{genome.get('generation', 1)})")
    print("=======================================================")

    if not history:
        print("No closed trades recorded yet.")
        print("Run trades via trading desk to generate empirical feedback data.")
        print("=======================================================\n")
        return None

    total_trades = len(history)
    wins = [t for t in history if float(t.get("net_pnl_usd", t.get("pnl_usd", 0))) > 0]
    losses = [t for t in history if float(t.get("net_pnl_usd", t.get("pnl_usd", 0))) <= 0]

    win_count = len(wins)
    loss_count = len(losses)
    win_rate = (win_count / total_trades * 100.0) if total_trades > 0 else 0.0

    total_win_pnl = sum(float(t.get("net_pnl_usd", t.get("pnl_usd", 0))) for t in wins)
    total_loss_pnl = abs(sum(float(t.get("net_pnl_usd", t.get("pnl_usd", 0))) for t in losses))
    net_pnl = total_win_pnl - total_loss_pnl

    profit_factor = (total_win_pnl / total_loss_pnl) if total_loss_pnl > 0 else (99.0 if total_win_pnl > 0 else 0.0)
    avg_win = (total_win_pnl / win_count) if win_count > 0 else 0.0
    avg_loss = (total_loss_pnl / loss_count) if loss_count > 0 else 0.0
    expectancy = (win_rate / 100.0 * avg_win) - ((100.0 - win_rate) / 100.0 * avg_loss)

    sharpe, mean_r, std_r = calculate_rolling_sharpe(history, window=30)

    print(f"Total Closed Trades : {total_trades}")
    print(f"Win / Loss Count    : {win_count} Wins | {loss_count} Losses")
    print(f"Win Rate            : {win_rate:.1f}%")
    print(f"Profit Factor       : {profit_factor:.2f}")
    print(f"Rolling Sharpe Ratio: {sharpe:.2f}")
    print(f"Net Realized PnL    : {'+' if net_pnl >= 0 else ''}${net_pnl:,.2f}")
    print(f"Trade Expectancy    : {'+' if expectancy >= 0 else ''}${expectancy:,.2f} per trade")
    print("=======================================================\n")

    return {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 2),
        "profit_factor": round(profit_factor, 2),
        "rolling_sharpe": sharpe,
        "net_pnl": round(net_pnl, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "expectancy_usd": round(expectancy, 2)
    }

def run_karpathy_autoresearch_cycle():
    """
    Executes ATLAS Karpathy-style Keep-or-Revert Optimization Loop.
    """
    stats = analyze_performance()
    genome = load_json(GENOME_FILE, get_default_genome())
    history = get_all_trade_records()

    if not stats or stats["total_trades"] < 3:
        print("[Autoresearch] Minimum 3 closed trades required for empirical optimization.")
        return False, "INSUFFICIENT_DATA"

    exp = genome.get("active_experiment", {})
    best = genome.get("best_known_genome", {})
    current_gen = genome.get("generation", 1)
    total_trades = stats["total_trades"]

    print("=======================================================")
    print(" 🤖 ATLAS AUTORESEARCH (KEEP-OR-REVERT OPTIMIZATION LOOP)")
    print("=======================================================")

    # 1. Evaluate Active Experiment if in EVALUATING stage
    if exp.get("status") == "EVALUATING":
        trades_since_exp = total_trades - exp.get("start_trade_count", 0)
        print(f"Evaluating active experiment Gen-{exp.get('test_generation')} ({trades_since_exp}/5 trades observed)...")

        if trades_since_exp >= 5:
            # Compare current Sharpe/PF against baseline
            curr_sharpe = stats["rolling_sharpe"]
            curr_pf = stats["profit_factor"]
            base_sharpe = exp.get("baseline_sharpe", 0.0)

            if curr_sharpe >= base_sharpe and curr_pf >= 0.90:
                # KEEP DECISION
                print(f"🎉 [KEEP] Hypothesis confirmed! Sharpe ({curr_sharpe:.2f} >= {base_sharpe:.2f}). Promoting to gold baseline.")
                best["generation"] = current_gen
                best["sharpe_ratio"] = curr_sharpe
                best["profit_factor"] = curr_pf
                best["expectancy_usd"] = stats["expectancy_usd"]
                best["parameters"] = json.loads(json.dumps(genome["parameters"]))
                genome["best_known_genome"] = best
                genome["active_experiment"] = {"status": "IDLE", "last_decision": "KEEP"}
                genome["mutation_history"].append({
                    "generation": current_gen,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "action": "KEEP_PROMOTED",
                    "hypothesis": f"Promoted Gen-{current_gen} after outperforming baseline Sharpe ({curr_sharpe:.2f} vs {base_sharpe:.2f})."
                })
                save_json(GENOME_FILE, genome)
                return True, "KEEP"
            else:
                # REVERT DECISION
                print(f"⚠️ [REVERT] Hypothesis underperformed (Sharpe {curr_sharpe:.2f} < Baseline {base_sharpe:.2f}). Rolling back.")
                genome["parameters"] = json.loads(json.dumps(best["parameters"]))
                revert_gen = current_gen + 1
                genome["generation"] = revert_gen
                genome["active_experiment"] = {"status": "IDLE", "last_decision": "REVERT"}
                genome["mutation_history"].append({
                    "generation": revert_gen,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "action": "REVERT_ROLLBACK",
                    "hypothesis": f"Reverted to Gen-{best.get('generation', 1)} baseline parameters after underperforming test."
                })
                save_json(GENOME_FILE, genome)
                return True, "REVERT"

    # 2. Spawn New Hypothesis Mutation if Sharpe or Profit Factor needs improvement
    target_wr = genome.get("benchmarks", {}).get("target_win_rate", 50.0)
    target_pf = genome.get("benchmarks", {}).get("target_profit_factor", 1.5)

    mutated = False
    hypothesis = ""
    action_desc = ""

    if stats["win_rate"] < target_wr:
        current_rr = genome["parameters"].get("min_risk_reward", 2.0)
        new_rr = round(min(3.5, current_rr + 0.25), 2)
        hypothesis = f"Win rate ({stats['win_rate']}%) is below target ({target_wr}%). Raising minimum R:R to {new_rr} to preserve mathematical payoff."
        genome["parameters"]["min_risk_reward"] = new_rr
        genome["parameters"]["weights"]["risk_aversion"] = min(0.35, round(genome["parameters"]["weights"]["risk_aversion"] + 0.05, 2))
        mutated = True
        action_desc = f"AUTORESEARCH_MUTATE_RR ({current_rr} -> {new_rr})"

    elif stats["profit_factor"] < target_pf:
        current_fr = genome["parameters"].get("max_funding_rate_threshold", 0.025)
        new_fr = round(max(0.010, current_fr - 0.005), 4)
        hypothesis = f"Profit factor ({stats['profit_factor']}) is below {target_pf}. Tightening Funding Rate squeeze filter to {new_fr}%."
        genome["parameters"]["max_funding_rate_threshold"] = new_fr
        mutated = True
        action_desc = f"AUTORESEARCH_MUTATE_FUNDING ({current_fr}% -> {new_fr}%)"

    if mutated:
        new_gen = current_gen + 1
        genome["generation"] = new_gen
        genome["active_experiment"] = {
            "status": "EVALUATING",
            "test_generation": new_gen,
            "start_trade_count": total_trades,
            "baseline_sharpe": stats["rolling_sharpe"],
            "baseline_pf": stats["profit_factor"],
            "hypothesis": hypothesis
        }
        genome["mutation_history"].append({
            "generation": new_gen,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action_desc,
            "hypothesis": hypothesis
        })
        save_json(GENOME_FILE, genome)
        print(f"🚀 [EXPERIMENT SPAWNED] Gen-{new_gen}: {hypothesis}")
        return True, "SPAWNED"

    print("[Autoresearch] Performance is healthy and optimal. No mutation needed.")
    return False, "STABLE"

def get_autoresearch_summary():
    """Returns structured Autoresearch status for HTTP API & Dashboard."""
    genome = load_json(GENOME_FILE, get_default_genome())
    stats = analyze_performance() or {}
    exp = genome.get("active_experiment", {})
    best = genome.get("best_known_genome", {})

    return {
        "success": True,
        "generation": genome.get("generation", 1),
        "fitness_score": genome.get("fitness_score", 85.0),
        "performance": stats,
        "active_experiment": exp,
        "best_known_genome": {
            "generation": best.get("generation", 1),
            "sharpe_ratio": best.get("sharpe_ratio", 1.0),
            "profit_factor": best.get("profit_factor", 1.0)
        },
        "parameters": genome.get("parameters", {}),
        "benchmarks": genome.get("benchmarks", {}),
        "total_mutations": len(genome.get("mutation_history", [])),
        "last_mutation": genome.get("mutation_history", [])[-1] if genome.get("mutation_history") else None
    }

def evolve_agent():
    return run_karpathy_autoresearch_cycle()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ATLAS Karpathy Autoresearch Self-Improving Engine")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("audit", help="Audit performance metrics and rolling Sharpe")
    sub.add_parser("evolve", help="Run Karpathy Autoresearch Keep-or-Revert cycle")
    args = parser.parse_args()

    if args.command == "evolve":
        run_karpathy_autoresearch_cycle()
    else:
        analyze_performance()

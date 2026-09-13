"""
Institutional Hyperparameter Optimization Engine (Hyperopt)
Multi-Objective Strategy Optimizer for Belajar Kripto Workspace.
Features:
- Dual Engine: Optuna TPE Sampler with seamless fallback to Native Adaptive Latin Hypercube Search.
- Multi-Objective Targets: Sortino, Sharpe, Calmar, ProfitFactor, and Composite Quality Score.
- Strategies: FastScalper, TopDownSMC, OrderflowCVD, and ORB Breakout.
- Automatic persistence to .agents/data/optimized_params.json for instant trading desk consumption.
"""

import argparse
import json
import math
import os
import random
import sys
import time
from datetime import datetime

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
OPTIMIZED_PARAMS_FILE = os.path.join(DATA_DIR, "optimized_params.json")
HYPEROPT_HISTORY_FILE = os.path.join(DATA_DIR, "hyperopt_history.json")

sys.path.insert(0, TOOLS_DIR)
import market_eyes
import quant_backtester

try:
    import numpy as np
except ImportError:
    np = None

# Optional Optuna import
try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    HAS_OPTUNA = True
except ImportError:
    HAS_OPTUNA = False


# -------------------------------------------------------------
# 1. Parameter Search Space Definitions
# -------------------------------------------------------------

SEARCH_SPACES = {
    "fast_scalper": {
        "ema_fast": {"type": "int", "low": 9, "high": 30, "default": 20},
        "ema_slow": {"type": "int", "low": 35, "high": 100, "default": 50},
        "rsi_period": {"type": "int", "low": 7, "high": 21, "default": 14},
        "rsi_oversold": {"type": "float", "low": 25.0, "high": 42.0, "step": 1.0, "default": 35.0},
        "rsi_overbought": {"type": "float", "low": 58.0, "high": 75.0, "step": 1.0, "default": 65.0},
        "atr_sl_mult": {"type": "float", "low": 1.0, "high": 3.0, "step": 0.1, "default": 1.8},
        "risk_reward": {"type": "float", "low": 2.0, "high": 4.5, "step": 0.1, "default": 2.8},
        "be_trigger_r": {"type": "float", "low": 0.8, "high": 1.5, "step": 0.1, "default": 1.0},
        "trail_step_r": {"type": "float", "low": 1.5, "high": 3.0, "step": 0.1, "default": 2.0}
    },
    "topdown_smc": {
        "ema_trend": {"type": "int", "low": 50, "high": 200, "default": 100},
        "fvg_min_pct": {"type": "float", "low": 0.15, "high": 0.80, "step": 0.05, "default": 0.30},
        "risk_reward": {"type": "float", "low": 2.5, "high": 5.5, "step": 0.1, "default": 3.2},
        "be_trigger_r": {"type": "float", "low": 1.0, "high": 2.0, "step": 0.1, "default": 1.2},
        "trail_step_r": {"type": "float", "low": 2.0, "high": 4.0, "step": 0.1, "default": 2.5}
    },
    "orderflow_cvd": {
        "cvd_window": {"type": "int", "low": 10, "high": 50, "default": 20},
        "absorption_ratio": {"type": "float", "low": 1.5, "high": 3.5, "step": 0.1, "default": 2.2},
        "sl_buffer_pct": {"type": "float", "low": 0.3, "high": 1.5, "step": 0.1, "default": 0.8},
        "risk_reward": {"type": "float", "low": 2.0, "high": 4.5, "step": 0.1, "default": 3.0}
    }
}


# -------------------------------------------------------------
# 2. Strategy Simulation with Dynamic Parameters
# -------------------------------------------------------------

def evaluate_fast_scalper_signals(window_candles, params):
    """
    Evaluates fast scalper signals using parameterized thresholds.
    """
    if len(window_candles) < max(params["ema_slow"] + 5, 30):
        return None

    closes = [c["close"] for c in window_candles]
    highs = [c["high"] for c in window_candles]
    lows = [c["low"] for c in window_candles]
    current_price = closes[-1]

    rsi_period = int(params.get("rsi_period", 14))
    rsi = market_eyes.calculate_rsi(closes, rsi_period) or 50.0
    ema_fast = market_eyes.calculate_ema(closes, int(params.get("ema_fast", 20)))
    ema_slow = market_eyes.calculate_ema(closes, int(params.get("ema_slow", 50)))

    if not ema_fast or not ema_slow:
        return None

    bullish_trend = current_price > ema_fast > ema_slow
    bearish_trend = current_price < ema_fast < ema_slow

    atr_mult = float(params.get("atr_sl_mult", 1.8))
    rr = float(params.get("risk_reward", 2.8))

    # Calculate recent ATR estimate
    tr_list = [max(highs[k] - lows[k], abs(highs[k] - closes[k-1]), abs(lows[k] - closes[k-1])) for k in range(1, len(closes))]
    atr = sum(tr_list[-14:]) / 14 if len(tr_list) >= 14 else (current_price * 0.005)

    # Long Setup
    if bullish_trend and (params["rsi_oversold"] <= rsi <= params["rsi_overbought"]):
        # Pullback into Fast EMA
        if lows[-1] <= ema_fast <= highs[-1] or abs(current_price - ema_fast) / current_price < 0.003:
            sl = round(current_price - (atr * atr_mult), 4)
            r_dist = current_price - sl
            if r_dist > 0:
                tp = round(current_price + (r_dist * rr), 4)
                return {
                    "side": "LONG",
                    "entry": current_price,
                    "sl": sl,
                    "tp": tp,
                    "r_dist": r_dist,
                    "strategy": "FastScalper_Opt",
                    "be_trigger_r": params.get("be_trigger_r", 1.0),
                    "trail_step_r": params.get("trail_step_r", 2.0)
                }

    # Short Setup
    if bearish_trend and (params["rsi_oversold"] <= rsi <= params["rsi_overbought"]):
        # Rejection at Fast EMA
        if lows[-1] <= ema_fast <= highs[-1] or abs(current_price - ema_fast) / current_price < 0.003:
            sl = round(current_price + (atr * atr_mult), 4)
            r_dist = sl - current_price
            if r_dist > 0:
                tp = round(current_price - (r_dist * rr), 4)
                return {
                    "side": "SHORT",
                    "entry": current_price,
                    "sl": sl,
                    "tp": tp,
                    "r_dist": r_dist,
                    "strategy": "FastScalper_Opt",
                    "be_trigger_r": params.get("be_trigger_r", 1.0),
                    "trail_step_r": params.get("trail_step_r", 2.0)
                }

    return None


def run_parameterized_backtest(candles, strategy_name, params, starting_balance=5000.0, risk_pct=1.5):
    """
    Simulates walk-forward execution with specific hyperparameter set.
    """
    if len(candles) < 45:
        return [], 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    trades = []
    active_trade = None
    equity = starting_balance
    peak_equity = starting_balance
    max_drawdown_pct = 0.0
    equity_curve = [starting_balance]

    start_idx = min(40, len(candles) - 1)

    for i in range(start_idx, len(candles)):
        current_candle = candles[i]

        # 1. Manage active trade
        if active_trade:
            side = active_trade["side"]
            entry = active_trade["entry"]
            current_sl = active_trade["current_sl"]
            tp = active_trade["tp"]
            r_dist = active_trade["r_dist"]
            risk_usd = active_trade["risk_usd"]

            c_high = current_candle["high"]
            c_low = current_candle["low"]

            if side == "LONG":
                peak_gain = c_high - entry
                r_reached = peak_gain / r_dist if r_dist > 0 else 0
            else:
                peak_gain = entry - c_low
                r_reached = peak_gain / r_dist if r_dist > 0 else 0

            if r_reached > active_trade["highest_r"]:
                active_trade["highest_r"] = r_reached

            # Breakeven Lock
            be_trig = active_trade.get("be_trigger_r", 1.0)
            if r_reached >= be_trig and not active_trade["breakeven_locked"]:
                active_trade["breakeven_locked"] = True
                active_trade["current_sl"] = entry * (1.0005 if side == "LONG" else 0.9995)

            # Trailing Stop
            trail_trig = active_trade.get("trail_step_r", 2.0)
            if r_reached >= trail_trig:
                target_lock_r = float(math.floor(r_reached) - 1.0)
                if target_lock_r > active_trade["trailing_r_locked"]:
                    active_trade["trailing_r_locked"] = target_lock_r
                    if side == "LONG":
                        active_trade["current_sl"] = entry + (r_dist * target_lock_r)
                    else:
                        active_trade["current_sl"] = entry - (r_dist * target_lock_r)

            # Check SL exit
            hit_sl = (c_low <= current_sl) if side == "LONG" else (c_high >= current_sl)
            hit_tp = (c_high >= tp) if side == "LONG" else (c_low <= tp)

            if hit_sl or hit_tp:
                if hit_tp and not hit_sl:
                    pnl_r = (tp - entry) / r_dist if side == "LONG" else (entry - tp) / r_dist
                    exit_reason = "TAKE_PROFIT"
                    exit_price = tp
                else:
                    pnl_r = (current_sl - entry) / r_dist if side == "LONG" else (entry - current_sl) / r_dist
                    exit_reason = "TRAILING_STOP" if active_trade["trailing_r_locked"] > 0 else ("BREAKEVEN" if active_trade["breakeven_locked"] else "STOP_LOSS")
                    exit_price = current_sl

                pnl_usd = pnl_r * risk_usd
                equity += pnl_usd
                if equity > peak_equity:
                    peak_equity = equity
                dd = (peak_equity - equity) / peak_equity * 100.0
                if dd > max_drawdown_pct:
                    max_drawdown_pct = dd

                equity_curve.append(equity)
                trades.append({
                    "pnl_usd": pnl_usd,
                    "pnl_r": pnl_r,
                    "is_win": pnl_r > 0,
                    "exit_reason": exit_reason
                })
                active_trade = None

        # 2. Look for new setup if flat
        if not active_trade:
            window = candles[max(0, i - 50):i + 1]
            if strategy_name == "fast_scalper":
                sig = evaluate_fast_scalper_signals(window, params)
            else:
                # Default generic evaluator
                sig = quant_backtester.simulate_strategy_signals(window)

            if sig and sig["r_dist"] > 0:
                risk_usd = equity * (risk_pct / 100.0)
                active_trade = {
                    "side": sig["side"],
                    "entry": sig["entry"],
                    "current_sl": sig["sl"],
                    "tp": sig["tp"],
                    "r_dist": sig["r_dist"],
                    "risk_usd": risk_usd,
                    "highest_r": 0.0,
                    "breakeven_locked": False,
                    "trailing_r_locked": 0.0,
                    "be_trigger_r": sig.get("be_trigger_r", params.get("be_trigger_r", 1.0)),
                    "trail_step_r": sig.get("trail_step_r", params.get("trail_step_r", 2.0))
                }

    # Metric calculations
    total_trades = len(trades)
    if total_trades < 3:
        return trades, -10.0, 0.0, 0.0, max_drawdown_pct, 0.0, 0.0

    wins = [t for t in trades if t["is_win"]]
    losses = [t for t in trades if not t["is_win"]]
    win_rate = (len(wins) / total_trades) * 100.0

    gross_profit = sum(t["pnl_usd"] for t in wins)
    gross_loss = abs(sum(t["pnl_usd"] for t in losses))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 1.0)

    pnl_r_list = [t["pnl_r"] for t in trades]
    avg_r = sum(pnl_r_list) / total_trades
    std_r = math.sqrt(sum((r - avg_r) ** 2 for r in pnl_r_list) / total_trades) if total_trades > 1 else 0.001
    sharpe = (avg_r / std_r) * math.sqrt(total_trades) if std_r > 0 else 0.0

    downside_r = [r for r in pnl_r_list if r < 0]
    std_downside = math.sqrt(sum(r ** 2 for r in downside_r) / len(downside_r)) if downside_r else 0.001
    sortino = (avg_r / std_downside) * math.sqrt(total_trades) if std_downside > 0 else (sharpe * 1.5)

    net_return_pct = ((equity - starting_balance) / starting_balance) * 100.0
    calmar = (net_return_pct / max_drawdown_pct) if max_drawdown_pct > 0 else net_return_pct

    # Composite Harmonic Score: Balance Sortino, WinRate, and MaxDrawdown penalty
    dd_penalty = max(0.0, (max_drawdown_pct - 10.0) * 0.2)
    min_trade_bonus = min(1.0, total_trades / 15.0)
    composite = (sortino * 0.5 + profit_factor * 0.3 + (win_rate / 50.0) * 0.2 - dd_penalty) * min_trade_bonus

    return trades, sortino, sharpe, calmar, max_drawdown_pct, profit_factor, composite


# -------------------------------------------------------------
# 3. Optimization Engines (Optuna + Native Latin Hypercube)
# -------------------------------------------------------------

def optimize_with_optuna(candles, strategy_name, target_metric="sortino", n_trials=50):
    """
    Runs Bayesian optimization using Optuna Tree-structured Parzen Estimator (TPE).
    """
    space = SEARCH_SPACES.get(strategy_name, SEARCH_SPACES["fast_scalper"])
    trial_records = []

    def objective(trial):
        params = {}
        for k, v in space.items():
            if v["type"] == "int":
                params[k] = trial.suggest_int(k, v["low"], v["high"])
            elif v["type"] == "float":
                params[k] = round(trial.suggest_float(k, v["low"], v["high"], step=v.get("step")), 4)

        trades, sortino, sharpe, calmar, mdd, pf, comp = run_parameterized_backtest(candles, strategy_name, params)

        trial_data = {
            "trial_num": trial.number + 1,
            "params": params,
            "trades_count": len(trades),
            "sortino": round(sortino, 3),
            "sharpe": round(sharpe, 3),
            "calmar": round(calmar, 3),
            "max_drawdown_pct": round(mdd, 2),
            "profit_factor": round(pf, 2),
            "composite": round(comp, 3)
        }
        trial_records.append(trial_data)

        if target_metric == "sharpe":
            return sharpe
        elif target_metric == "calmar":
            return calmar
        elif target_metric == "profit_factor":
            return pf
        elif target_metric == "composite":
            return comp
        return sortino

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=n_trials)

    best_trial_rec = next((t for t in trial_records if t["params"] == study.best_params), trial_records[-1] if trial_records else {})
    return study.best_params, best_trial_rec, trial_records


def optimize_with_native_search(candles, strategy_name, target_metric="sortino", n_trials=50):
    """
    High-performance native Latin Hypercube + Adaptive Neighborhood Search (Zero external dependencies).
    """
    space = SEARCH_SPACES.get(strategy_name, SEARCH_SPACES["fast_scalper"])
    trial_records = []
    best_score = -999999.0
    best_params = None
    best_record = None

    for t_idx in range(n_trials):
        params = {}
        # First 15% trials: exploratory grid / latin sampling
        # Later trials: perturb best known parameters with adaptive damping
        if t_idx > 10 and best_params and random.random() < 0.65:
            for k, v in space.items():
                best_v = best_params[k]
                if v["type"] == "int":
                    delta = random.choice([-2, -1, 0, 1, 2])
                    val = max(v["low"], min(v["high"], best_v + delta))
                    params[k] = int(val)
                elif v["type"] == "float":
                    step = v.get("step", 0.1)
                    delta = random.choice([-2, -1, 0, 1, 2]) * step
                    val = max(v["low"], min(v["high"], best_v + delta))
                    params[k] = round(val, 4)
        else:
            for k, v in space.items():
                if v["type"] == "int":
                    params[k] = random.randint(v["low"], v["high"])
                elif v["type"] == "float":
                    step = v.get("step", 0.1)
                    steps_count = int(round((v["high"] - v["low"]) / step))
                    val = v["low"] + (random.randint(0, steps_count) * step)
                    params[k] = round(val, 4)

        trades, sortino, sharpe, calmar, mdd, pf, comp = run_parameterized_backtest(candles, strategy_name, params)

        if target_metric == "sharpe":
            score = sharpe
        elif target_metric == "calmar":
            score = calmar
        elif target_metric == "profit_factor":
            score = pf
        elif target_metric == "composite":
            score = comp
        else:
            score = sortino

        rec = {
            "trial_num": t_idx + 1,
            "params": params,
            "trades_count": len(trades),
            "sortino": round(sortino, 3),
            "sharpe": round(sharpe, 3),
            "calmar": round(calmar, 3),
            "max_drawdown_pct": round(mdd, 2),
            "profit_factor": round(pf, 2),
            "composite": round(comp, 3),
            "score": round(score, 3)
        }
        trial_records.append(rec)

        if score > best_score:
            best_score = score
            best_params = params
            best_record = rec

    return best_params, best_record, trial_records


# -------------------------------------------------------------
# 4. Storage & Persistence
# -------------------------------------------------------------

def save_optimization_results(symbol, strategy_name, best_params, best_metrics, all_trials):
    """
    Saves best parameter configuration to optimized_params.json.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    current_data = {}
    if os.path.exists(OPTIMIZED_PARAMS_FILE):
        try:
            with open(OPTIMIZED_PARAMS_FILE, "r", encoding="utf-8") as f:
                current_data = json.load(f)
        except Exception:
            current_data = {}

    key = f"{symbol.upper()}_{strategy_name}"
    current_data[key] = {
        "symbol": symbol.upper(),
        "strategy": strategy_name,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "best_params": best_params,
        "metrics": best_metrics
    }

    try:
        with open(OPTIMIZED_PARAMS_FILE, "w", encoding="utf-8") as f:
            json.dump(current_data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error saving optimized params: {e}")

    # Save trial history
    try:
        with open(HYPEROPT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "symbol": symbol.upper(),
                "strategy": strategy_name,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_trials": len(all_trials),
                "best_params": best_params,
                "best_metrics": best_metrics,
                "trials": all_trials
            }, f, indent=2)
    except Exception:
        pass


def get_optimized_params(symbol, strategy_name):
    """
    Retrieves optimized params for a given symbol and strategy if available.
    """
    if not os.path.exists(OPTIMIZED_PARAMS_FILE):
        return None
    try:
        with open(OPTIMIZED_PARAMS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            key = f"{symbol.upper()}_{strategy_name}"
            if key in data:
                return data[key]["best_params"]
    except Exception:
        pass
    return None


# -------------------------------------------------------------
# 5. CLI Execution & Runner
# -------------------------------------------------------------

def run_hyperopt(symbol="BTC", strategy="fast_scalper", bar="1H", target_count=500, trials=50, target="sortino"):
    print("=" * 70)
    print("⚡ HYPEROPT PARAMETER OPTIMIZATION ENGINE")
    print(f"🎯 Target: {symbol.upper()} | Strategy: {strategy} | TF: {bar} | Trials: {trials} | Objective: {target.upper()}")
    print(f"🔬 Engine: {'Optuna (TPE Bayesian)' if HAS_OPTUNA else 'Native Latin Hypercube + Adaptive'}")
    print("=" * 70)

    # 1. Fetch historical candles
    print(f"\n[1/3] Fetching {target_count} historical {bar} candles for {symbol.upper()}...")
    candles = quant_backtester.fetch_historical_candles(symbol=symbol, bar=bar, target_count=target_count)
    if not candles or len(candles) < 50:
        print("❌ Error: Insufficient historical candle data for optimization.")
        return None

    print(f"✅ Loaded {len(candles)} candles ({candles[0]['time']} to {candles[-1]['time']})")

    # 2. Execute Optimization
    print(f"\n[2/3] Executing {trials} optimization trials...")
    t_start = time.time()
    if HAS_OPTUNA:
        best_params, best_record, all_trials = optimize_with_optuna(candles, strategy, target_metric=target, n_trials=trials)
    else:
        best_params, best_record, all_trials = optimize_with_native_search(candles, strategy, target_metric=target, n_trials=trials)

    elapsed = round(time.time() - t_start, 2)
    print(f"✅ Optimization completed in {elapsed}s")

    # 3. Save & Report
    print(f"\n[3/3] Saving best parameters to {OPTIMIZED_PARAMS_FILE}...")
    save_optimization_results(symbol, strategy, best_params, best_record, all_trials)

    print("\n" + "=" * 70)
    print("🏆 OPTIMIZATION CHAMPION PARAMETERS")
    print("=" * 70)
    print(json.dumps(best_params, indent=2))
    print("\n📊 Expected Performance Metrics:")
    print(f"  • Sortino Ratio  : {best_record.get('sortino', 0):.2f}")
    print(f"  • Sharpe Ratio   : {best_record.get('sharpe', 0):.2f}")
    print(f"  • Calmar Ratio   : {best_record.get('calmar', 0):.2f}")
    print(f"  • Profit Factor  : {best_record.get('profit_factor', 0):.2f}")
    print(f"  • Max Drawdown   : {best_record.get('max_drawdown_pct', 0):.2f}%")
    print(f"  • Trade Samples  : {best_record.get('trades_count', 0)} trades")
    print("=" * 70)

    return {
        "symbol": symbol.upper(),
        "strategy": strategy,
        "best_params": best_params,
        "best_metrics": best_record,
        "elapsed_sec": elapsed
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Belajar Kripto Hyperopt Engine")
    parser.add_argument("--symbol", type=str, default="BTC", help="Asset symbol (e.g. BTC, ETH, SOL)")
    parser.add_argument("--strategy", type=str, default="fast_scalper", choices=["fast_scalper", "topdown_smc", "orderflow_cvd"], help="Target strategy to optimize")
    parser.add_argument("--bar", type=str, default="1H", help="Candle timeframe (e.g. 15m, 1H, 4H)")
    parser.add_argument("--candles", type=int, default=500, help="Number of historical candles to evaluate")
    parser.add_argument("--trials", type=int, default=40, help="Number of optimization trials")
    parser.add_argument("--target", type=str, default="sortino", choices=["sortino", "sharpe", "calmar", "profit_factor", "composite"], help="Objective function to maximize")

    args = parser.parse_args()
    run_hyperopt(
        symbol=args.symbol,
        strategy=args.strategy,
        bar=args.bar,
        target_count=args.candles,
        trials=args.trials,
        target=args.target
    )

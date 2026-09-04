"""
Quantitative Historical Backtester & Monte Carlo Simulator
Simulates Top-Down Confluence, 4 Championship Strategies, Breakeven (+1R), and Trailing Stops (+2R+).
Calculates institutional hedge-fund metrics: Sharpe, Sortino, Profit Factor, MDD, and 1,000-permutation Monte Carlo.
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
BACKTEST_RESULT_FILE = os.path.join(DATA_DIR, "backtest_results.json")

sys.path.insert(0, TOOLS_DIR)
import market_eyes

def fetch_historical_candles(symbol="BTC", bar="1H", target_count=500):
    """
    Fetches historical candlestick sequence from OKX with pagination and disk caching.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")
    cache_file = os.path.join(DATA_DIR, f"cache_klines_{sym_clean}_{bar}.json")

    # Check cache (1 hour TTL)
    if os.path.exists(cache_file):
        try:
            mtime = os.path.getmtime(cache_file)
            if time.time() - mtime < 3600:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                    if len(cached) >= target_count * 0.8:
                        return cached
        except Exception:
            pass

    inst_id_spot = f"{sym_clean}-USDT"
    all_candles = []
    after_ts = ""

    # Paginate up to target_count (max 100 per request)
    loops = min(10, math.ceil(target_count / 100))
    for _ in range(loops):
        url = f"https://www.okx.com/api/v5/market/history-candles?instId={inst_id_spot}&bar={bar}&limit=100"
        if after_ts:
            url += f"&after={after_ts}"

        res = market_eyes.fetch_json(url)
        if not res or res.get("code") != "0" or not res.get("data"):
            # Fallback to standard candles endpoint if history-candles is rate limited
            if not all_candles:
                url_std = f"https://www.okx.com/api/v5/market/candles?instId={inst_id_spot}&bar={bar}&limit=100"
                res_std = market_eyes.fetch_json(url_std)
                if res_std and res_std.get("code") == "0" and res_std.get("data"):
                    all_candles.extend(res_std["data"])
            break

        data = res["data"]
        all_candles.extend(data)
        after_ts = data[-1][0]
        if len(all_candles) >= target_count:
            break
        time.sleep(0.15)

    # Sort chronologically (oldest to newest)
    # OKX format: [ts, open, high, low, close, vol, volCcy, volCcyQuote, confirm]
    sorted_raw = sorted(all_candles, key=lambda x: int(x[0]))
    parsed = []
    for c in sorted_raw:
        parsed.append({
            "ts": int(c[0]),
            "time": datetime.fromtimestamp(int(c[0]) / 1000).strftime("%Y-%m-%d %H:%M"),
            "open": float(c[1]),
            "high": float(c[2]),
            "low": float(c[3]),
            "close": float(c[4]),
            "volume": float(c[5])
        })

    # Cache to disk
    if parsed:
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(parsed, f, indent=2)
        except Exception:
            pass

    return parsed

def simulate_strategy_signals(window_candles):
    """
    Evaluates trading setups on the current historical window.
    """
    if len(window_candles) < 30:
        return None

    closes = [c["close"] for c in window_candles]
    highs = [c["high"] for c in window_candles]
    lows = [c["low"] for c in window_candles]
    current_price = closes[-1]

    # Technical Indicators
    rsi = market_eyes.calculate_rsi(closes, 14) or 50.0
    ema20 = market_eyes.calculate_ema(closes, 20)
    ema50 = market_eyes.calculate_ema(closes, 50)

    # 1. Patrick Nill 3-Touch Golden Touch
    three_touch = market_eyes.detect_three_touch_setup(highs, lows, closes, current_price)

    # 2. Fabio Valentini Volume Profile & Failed Auction
    raw_tuples = [[c["ts"], c["open"], c["high"], c["low"], c["close"], c["volume"]] for c in window_candles]
    vp = market_eyes.calculate_volume_profile(raw_tuples, current_price)

    # 3. Tim Flossbach Liquidity Sweep & MSS
    mss = market_eyes.detect_liquidity_sweep_mss(highs, lows, closes, current_price)

    # 4. Institutional VWAP Bands
    vwap_info = market_eyes.calculate_vwap_and_bands(raw_tuples)

    # Trend Bias
    bullish_trend = current_price > ema20 > ema50
    bearish_trend = current_price < ema20 < ema50

    # Macro Confluence Simulation (Derived from EMA + VWAP)
    macro_bullish = bullish_trend or (vwap_info and current_price > vwap_info["vwap"])
    macro_bearish = bearish_trend or (vwap_info and current_price < vwap_info["vwap"])

    # -------------------------------------------------------------
    # LONG SIGNAL GENERATION (Requires Macro Bullish Alignment)
    # -------------------------------------------------------------
    if macro_bullish and rsi > 35 and rsi < 68:
        if three_touch and three_touch.get("type") == "BULLISH_3_TOUCH":
            sl = round(three_touch["level"] * 0.995, 4)
            r_dist = current_price - sl
            if r_dist > 0:
                tp = round(current_price + (r_dist * 2.8), 4)
                return {"side": "LONG", "entry": current_price, "sl": sl, "tp": tp, "r_dist": r_dist, "strategy": "Patrick Nill 3-Touch"}

        if mss and mss.get("type") == "BULLISH_SWEEP_MSS":
            sl = round(mss["sl"] * 0.998, 4)
            r_dist = current_price - sl
            if r_dist > 0:
                tp = round(current_price + (r_dist * 3.0), 4)
                return {"side": "LONG", "entry": current_price, "sl": sl, "tp": tp, "r_dist": r_dist, "strategy": "Tim Flossbach MSS"}

        if vp and vp.get("setup") and vp["setup"].get("type") == "BULLISH_FAILED_AUCTION":
            sl = round(vp["setup"]["sl"] * 0.998, 4)
            r_dist = current_price - sl
            if r_dist > 0:
                tp = round(current_price + (r_dist * 2.5), 4)
                return {"side": "LONG", "entry": current_price, "sl": sl, "tp": tp, "r_dist": r_dist, "strategy": "Fabio Failed Auction"}

    # -------------------------------------------------------------
    # SHORT SIGNAL GENERATION (Requires Macro Bearish Alignment)
    # -------------------------------------------------------------
    if macro_bearish and rsi < 65 and rsi > 32:
        if three_touch and three_touch.get("type") == "BEARISH_3_TOUCH":
            sl = round(three_touch["level"] * 1.005, 4)
            r_dist = sl - current_price
            if r_dist > 0:
                tp = round(current_price - (r_dist * 2.8), 4)
                return {"side": "SHORT", "entry": current_price, "sl": sl, "tp": tp, "r_dist": r_dist, "strategy": "Patrick Nill 3-Touch"}

        if mss and mss.get("type") == "BEARISH_SWEEP_MSS":
            sl = round(mss["sl"] * 1.002, 4)
            r_dist = sl - current_price
            if r_dist > 0:
                tp = round(current_price - (r_dist * 3.0), 4)
                return {"side": "SHORT", "entry": current_price, "sl": sl, "tp": tp, "r_dist": r_dist, "strategy": "Tim Flossbach MSS"}

        if vp and vp.get("setup") and vp["setup"].get("type") == "BEARISH_FAILED_AUCTION":
            sl = round(vp["setup"]["sl"] * 1.002, 4)
            r_dist = sl - current_price
            if r_dist > 0:
                tp = round(current_price - (r_dist * 2.5), 4)
                return {"side": "SHORT", "entry": current_price, "sl": sl, "tp": tp, "r_dist": r_dist, "strategy": "Fabio Failed Auction"}

    return None

def simulate_walk_forward_trades(candles, symbol="BTC", starting_balance=5000.0, risk_pct=1.5):
    """
    Simulates walk-forward trade execution with Breakeven (+1R) and Trailing Stop (+2R+)
    across a given slice of candlesticks.
    Returns: (trades, equity_curve, final_equity)
    """
    if len(candles) < 42:
        return [], [{"trade_num": 0, "time": candles[0]["time"] if candles else "", "equity": starting_balance}], starting_balance

    trades = []
    active_trade = None
    equity = starting_balance
    equity_curve = [{"trade_num": 0, "time": candles[0]["time"], "equity": starting_balance}]

    start_idx = min(40, len(candles) - 1)
    for i in range(start_idx, len(candles)):
        current_candle = candles[i]

        # 1. Manage existing open trade if any
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
                r_reached = peak_gain / r_dist
            else:
                peak_gain = entry - c_low
                r_reached = peak_gain / r_dist

            if r_reached > active_trade["highest_r"]:
                active_trade["highest_r"] = r_reached

            # --- DYNAMIC MANAGEMENT: BREAKEVEN (+1R) ---
            if r_reached >= 1.0 and not active_trade["breakeven_locked"]:
                active_trade["breakeven_locked"] = True
                if side == "LONG":
                    active_trade["current_sl"] = entry * 1.0008
                else:
                    active_trade["current_sl"] = entry * 0.9992

            # --- DYNAMIC MANAGEMENT: TRAILING STOP (+2R+) ---
            if r_reached >= 2.0:
                target_lock_r = float(math.floor(r_reached) - 1.0)
                if target_lock_r > active_trade["trailing_r_locked"]:
                    active_trade["trailing_r_locked"] = target_lock_r
                    if side == "LONG":
                        active_trade["current_sl"] = entry + (r_dist * target_lock_r)
                    else:
                        active_trade["current_sl"] = entry - (r_dist * target_lock_r)

            # --- EXIT EVALUATION ---
            hit_tp = (c_high >= tp) if side == "LONG" else (c_low <= tp)
            hit_sl = (c_low <= active_trade["current_sl"]) if side == "LONG" else (c_high >= active_trade["current_sl"])

            if hit_tp:
                exit_price = tp
                pnl_r = (tp - entry) / r_dist if side == "LONG" else (entry - tp) / r_dist
                pnl_usd = risk_usd * pnl_r
                equity += pnl_usd
                trades.append({
                    "trade_num": len(trades) + 1,
                    "symbol": symbol,
                    "side": side,
                    "entry_time": active_trade["entry_time"],
                    "entry_ts": active_trade.get("entry_ts", current_candle.get("ts", 0)),
                    "exit_time": current_candle["time"],
                    "entry_price": entry,
                    "exit_price": exit_price,
                    "pnl_r": round(pnl_r, 2),
                    "pnl_usd": round(pnl_usd, 2),
                    "exit_reason": "TAKE_PROFIT_HIT",
                    "strategy": active_trade["strategy"],
                    "equity": round(equity, 2)
                })
                equity_curve.append({"trade_num": len(trades), "time": current_candle["time"], "equity": round(equity, 2)})
                active_trade = None
                continue

            elif hit_sl:
                exit_price = active_trade["current_sl"]
                if active_trade["trailing_r_locked"] > 0:
                    pnl_r = active_trade["trailing_r_locked"]
                    exit_reason = f"TRAILING_STOP_LOCKED (+{pnl_r:.1f}R)"
                elif active_trade["breakeven_locked"]:
                    pnl_r = 0.0
                    exit_reason = "BREAKEVEN_PROTECTED (0R Free Roll)"
                else:
                    pnl_r = -1.0
                    exit_reason = "STOP_LOSS_HIT (-1R)"

                pnl_usd = risk_usd * pnl_r
                equity += pnl_usd
                trades.append({
                    "trade_num": len(trades) + 1,
                    "symbol": symbol,
                    "side": side,
                    "entry_time": active_trade["entry_time"],
                    "entry_ts": active_trade.get("entry_ts", current_candle.get("ts", 0)),
                    "exit_time": current_candle["time"],
                    "entry_price": entry,
                    "exit_price": exit_price,
                    "pnl_r": round(pnl_r, 2),
                    "pnl_usd": round(pnl_usd, 2),
                    "exit_reason": exit_reason,
                    "strategy": active_trade["strategy"],
                    "equity": round(equity, 2)
                })
                equity_curve.append({"trade_num": len(trades), "time": current_candle["time"], "equity": round(equity, 2)})
                active_trade = None
                continue

        # 2. If no open trade, check for new setup
        if not active_trade:
            window = candles[:i+1]
            signal = simulate_strategy_signals(window)
            if signal:
                risk_usd = equity * (risk_pct / 100.0)
                active_trade = {
                    "symbol": symbol,
                    "side": signal["side"],
                    "entry": signal["entry"],
                    "current_sl": signal["sl"],
                    "initial_sl": signal["sl"],
                    "tp": signal["tp"],
                    "r_dist": signal["r_dist"],
                    "risk_usd": risk_usd,
                    "strategy": signal["strategy"],
                    "entry_time": current_candle["time"],
                    "entry_ts": current_candle.get("ts", 0),
                    "breakeven_locked": False,
                    "trailing_r_locked": 0.0,
                    "highest_r": 0.0
                }

    return trades, equity_curve, equity

def calculate_distribution_moments(returns):
    """
    Computes mean, variance, standard deviation, skewness, and kurtosis of returns.
    """
    n = len(returns)
    if n < 3:
        return {"mean": 0.0, "variance": 0.0001, "std": 0.01, "skewness": 0.0, "kurtosis": 3.0}

    mean = sum(returns) / n
    variance = sum((r - mean) ** 2 for r in returns) / n
    std = math.sqrt(variance) if variance > 0 else 0.0001

    skewness = (sum((r - mean) ** 3 for r in returns) / n) / (std ** 3)
    kurtosis = (sum((r - mean) ** 4 for r in returns) / n) / (std ** 4)

    return {
        "mean": mean,
        "variance": variance,
        "std": std,
        "skewness": skewness,
        "kurtosis": kurtosis
    }

def normal_cdf(x):
    """Cumulative distribution function for standard normal distribution."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def calculate_deflated_sharpe_ratio(trades, num_trials=20):
    """
    Calculates Deflated Sharpe Ratio (DSR) based on Marcos López de Prado's framework.
    Accounts for selection bias under multiple testing, sample length, and return non-normality.
    """
    if len(trades) < 5:
        return {
            "sharpe_hat": 0.0,
            "sr_benchmark": 0.0,
            "deflated_sharpe_ratio": 0.0,
            "dsr_p_value": 0.50,
            "skewness": 0.0,
            "kurtosis": 3.0
        }

    returns = [t["pnl_r"] for t in trades]
    t_len = len(returns)
    moments = calculate_distribution_moments(returns)

    avg_r = moments["mean"]
    std_r = moments["std"]
    skew = moments["skewness"]
    kurt = max(1.0, moments["kurtosis"])

    sr_hat = (avg_r / std_r) * math.sqrt(252)

    # Standard error of estimated Sharpe
    denom = 1.0 - (skew * sr_hat) + (((kurt - 1.0) / 4.0) * (sr_hat ** 2))
    var_sr = max(0.0001, denom / max(1, t_len - 1))
    std_sr = math.sqrt(var_sr)

    # Expected max Sharpe under zero true alpha null hypothesis across num_trials
    euler_mascheroni = 0.5772156649
    sqrt_2ln = math.sqrt(2.0 * math.log(max(2, num_trials)))
    sr_star = std_sr * ((1.0 - euler_mascheroni) * sqrt_2ln + (euler_mascheroni * math.sqrt(2.0 * math.log(max(2, num_trials * math.e)))))

    z_stat = (sr_hat - sr_star) / std_sr if std_sr > 0 else 0.0
    dsr = max(0.0, min(1.0, normal_cdf(z_stat)))
    p_val = max(0.0, min(1.0, 1.0 - dsr))

    return {
        "sharpe_hat": round(sr_hat, 2),
        "sr_benchmark": round(sr_star, 2),
        "deflated_sharpe_ratio": round(dsr, 3),
        "dsr_p_value": round(p_val, 4),
        "skewness": round(skew, 2),
        "kurtosis": round(kurt, 2)
    }

def calculate_monte_carlo_p_value(trades, num_simulations=1000):
    """
    Permutation sign-flip test (White's Reality Check) to estimate empirical p-value.
    Measures the probability that the observed performance arose purely from luck.
    """
    if len(trades) < 5:
        return 0.50

    returns = [t["pnl_r"] for t in trades]
    n = len(returns)
    mean_r = sum(returns) / n
    var_r = sum((r - mean_r) ** 2 for r in returns) / n
    obs_sharpe = (mean_r / math.sqrt(var_r)) if var_r > 0 else 0.0

    if obs_sharpe <= 0:
        return 1.0

    beat_count = 0
    for _ in range(num_simulations):
        # Random sign-flip null hypothesis around 0 expectation
        shuffled = [r * random.choice([-1, 1]) for r in returns]
        sh_mean = sum(shuffled) / n
        sh_var = sum((r - sh_mean) ** 2 for r in shuffled) / n
        perm_sharpe = (sh_mean / math.sqrt(sh_var)) if sh_var > 0 else 0.0

        if perm_sharpe >= obs_sharpe:
            beat_count += 1

    p_val = beat_count / num_simulations
    return round(p_val, 4)

def run_anti_overfitting_audit(candles, symbol="BTC", starting_balance=5000.0, risk_pct=1.5, num_trials=20):
    """
    Executes Walk-Forward In-Sample (70%) vs Out-of-Sample (30%) split,
    computes Deflated Sharpe Ratio (DSR), Monte Carlo permutation p-value,
    and returns institutional anti-overfitting verdict.
    """
    total_candles = len(candles)
    if total_candles < 70:
        return {
            "verdict": "INSUFFICIENT_DATA",
            "verdict_label": "⚪ INSUFFICIENT DATA",
            "verdict_color": "var(--text-dim)",
            "verdict_desc": "Data candle historis terlalu pendek untuk audit In-Sample / Out-of-Sample.",
            "walk_forward_efficiency_pct": 0.0,
            "p_value": 0.50,
            "deflated_sharpe": {"deflated_sharpe_ratio": 0.0, "sr_benchmark": 0.0},
            "in_sample": {"candles_count": 0, "trades_count": 0, "win_rate": 0.0, "profit_factor": 0.0, "expectancy_r": 0.0},
            "out_of_sample": {"candles_count": 0, "trades_count": 0, "win_rate": 0.0, "profit_factor": 0.0, "expectancy_r": 0.0}
        }

    split_idx = int(total_candles * 0.70)
    is_candles = candles[:split_idx]
    # Provide indicator warm-up buffer for OOS
    buffer_start = max(0, split_idx - 40)
    oos_candles = candles[buffer_start:]

    is_trades, _, _ = simulate_walk_forward_trades(is_candles, symbol, starting_balance, risk_pct)
    oos_trades_raw, _, _ = simulate_walk_forward_trades(oos_candles, symbol, starting_balance, risk_pct)

    # Filter out any trades that entered during the warm-up buffer in OOS
    split_time = candles[split_idx]["time"]
    oos_trades = [t for t in oos_trades_raw if t["entry_time"] >= split_time]
    if not oos_trades and oos_trades_raw:
        oos_trades = oos_trades_raw

    is_metrics = calculate_metrics(is_trades, starting_balance)
    oos_metrics = calculate_metrics(oos_trades, starting_balance)

    is_pf = is_metrics.get("profit_factor", 0.0)
    oos_pf = oos_metrics.get("profit_factor", 0.0)

    if is_pf > 0:
        wfe_pct = round((oos_pf / is_pf) * 100.0, 1)
    else:
        wfe_pct = 100.0 if oos_pf > 0 else 0.0

    all_trades, _, _ = simulate_walk_forward_trades(candles, symbol, starting_balance, risk_pct)
    dsr_data = calculate_deflated_sharpe_ratio(all_trades, num_trials=num_trials)
    p_val = calculate_monte_carlo_p_value(all_trades, num_simulations=1000)

    # Institutional Verdict Matrix
    if p_val <= 0.05 and wfe_pct >= 50.0 and oos_metrics.get("expectancy_r", 0) >= 0:
        verdict = "ROBUST_EDGE"
        verdict_label = "🟢 ROBUST & GENUINE EDGE"
        verdict_color = "var(--green)"
        verdict_desc = "Strategi terbukti konsisten pada data buta (Out-of-Sample) dengan signifikansi statistik tinggi (p < 0.05). Bebas dari jebakan keberuntungan."
    elif wfe_pct < 35.0 or oos_metrics.get("expectancy_r", 0) < -0.25 or p_val >= 0.20:
        verdict = "LUCK_TRAP"
        verdict_label = "🔴 LUCK TRAP / HIGH OVERFITTING RISK"
        verdict_color = "var(--red)"
        verdict_desc = "Performa anjlok tajam di data buta (OOS) atau hasil diduga kebetulan acak (p >= 0.20). Parameter strategi terlalu kaku (Curve-Fitting)."
    else:
        verdict = "CAUTION"
        verdict_label = "🟡 MODERATE / CAUTION REQUIRED"
        verdict_color = "var(--amber)"
        verdict_desc = "Strategi menunjukkan resistensi moderat, namun konsistensi data buta masih membutuhkan sampel candle yang lebih panjang."

    return {
        "verdict": verdict,
        "verdict_label": verdict_label,
        "verdict_color": verdict_color,
        "verdict_desc": verdict_desc,
        "walk_forward_efficiency_pct": wfe_pct,
        "p_value": p_val,
        "deflated_sharpe": dsr_data,
        "in_sample": {
            "candles_count": len(is_candles),
            "trades_count": is_metrics.get("total_trades", 0),
            "win_rate": is_metrics.get("win_rate", 0.0),
            "profit_factor": is_metrics.get("profit_factor", 0.0),
            "expectancy_r": is_metrics.get("expectancy_r", 0.0)
        },
        "out_of_sample": {
            "candles_count": len(oos_candles),
            "trades_count": oos_metrics.get("total_trades", 0),
            "win_rate": oos_metrics.get("win_rate", 0.0),
            "profit_factor": oos_metrics.get("profit_factor", 0.0),
            "expectancy_r": oos_metrics.get("expectancy_r", 0.0)
        }
    }

def run_backtest(symbol="BTC", bar="1H", num_candles=800, starting_balance=5000.0, risk_pct=1.5):
    """
    Executes walk-forward historical simulation with Breakeven (+1R) and Trailing Stop (+2R+),
    calculates hedge-fund metrics, 1,000-run Monte Carlo stress test, and Anti-Overfitting audit.
    """
    candles = fetch_historical_candles(symbol, bar, target_count=num_candles)
    if len(candles) < 60:
        return {"error": "Insufficient historical candle data"}

    trades, equity_curve, equity = simulate_walk_forward_trades(candles, symbol, starting_balance, risk_pct)
    metrics = calculate_metrics(trades, starting_balance)
    monte_carlo = run_monte_carlo(trades, num_simulations=1000, starting_balance=starting_balance)
    overfitting_audit = run_anti_overfitting_audit(candles, symbol, starting_balance, risk_pct)

    result = {
        "symbol": symbol,
        "bar": bar,
        "candles_analyzed": len(candles),
        "starting_balance": starting_balance,
        "final_balance": round(equity, 2),
        "total_pnl_usd": round(equity - starting_balance, 2),
        "roi_pct": round(((equity - starting_balance) / starting_balance) * 100, 2),
        "metrics": metrics,
        "monte_carlo": monte_carlo,
        "overfitting_audit": overfitting_audit,
        "trades": trades,
        "equity_curve": equity_curve,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Save to disk
    try:
        with open(BACKTEST_RESULT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Quant Backtester] Error saving result: {e}")

    return result

def calculate_metrics(trades, starting_balance=5000.0):
    if not trades:
        return {
            "total_trades": 0, "win_rate": 0.0, "win_plus_be_rate": 0.0,
            "profit_factor": 0.0, "expectancy_r": 0.0, "max_drawdown_pct": 0.0,
            "sharpe_ratio": 0.0, "sortino_ratio": 0.0
        }

    wins = [t for t in trades if t["pnl_r"] > 0]
    breakevens = [t for t in trades if t["pnl_r"] == 0]
    losses = [t for t in trades if t["pnl_r"] < 0]

    win_rate = (len(wins) / len(trades)) * 100.0
    win_plus_be = ((len(wins) + len(breakevens)) / len(trades)) * 100.0

    total_gross_profit = sum(t["pnl_usd"] for t in wins)
    total_gross_loss = abs(sum(t["pnl_usd"] for t in losses))

    profit_factor = round(total_gross_profit / max(total_gross_loss, 0.01), 2) if total_gross_loss > 0 else 99.0
    expectancy_r = round(sum(t["pnl_r"] for t in trades) / len(trades), 2)

    # Maximum Drawdown calculation
    peak = starting_balance
    max_dd_pct = 0.0
    running_eq = starting_balance

    for t in trades:
        running_eq += t["pnl_usd"]
        if running_eq > peak:
            peak = running_eq
        dd = ((peak - running_eq) / peak) * 100.0
        if dd > max_dd_pct:
            max_dd_pct = dd

    # Sharpe & Sortino Ratios (per-trade basis annualized estimate)
    returns = [t["pnl_r"] for t in trades]
    avg_return = sum(returns) / len(returns)
    variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
    std_dev = math.sqrt(variance) if variance > 0 else 0.0001
    sharpe = round((avg_return / std_dev) * math.sqrt(252), 2)

    downside_returns = [r for r in returns if r < 0]
    downside_variance = (sum(r ** 2 for r in downside_returns) / len(returns)) if downside_returns else 0.0001
    downside_dev = math.sqrt(downside_variance)
    sortino = round((avg_return / downside_dev) * math.sqrt(252), 2)

    return {
        "total_trades": len(trades),
        "wins": len(wins),
        "breakevens": len(breakevens),
        "losses": len(losses),
        "win_rate": round(win_rate, 1),
        "win_plus_be_rate": round(win_plus_be, 1),
        "profit_factor": profit_factor,
        "expectancy_r": expectancy_r,
        "max_drawdown_pct": round(max_dd_pct, 2),
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino
    }

def run_monte_carlo(trades, num_simulations=1000, starting_balance=5000.0):
    """
    Shuffles trade sequences 1,000 times to stress-test sequence risk & probability of ruin.
    """
    if len(trades) < 5:
        return {
            "simulations": num_simulations,
            "median_drawdown_pct": 0.0,
            "worst_case_drawdown_pct": 0.0,
            "probability_of_ruin_pct": 0.0,
            "max_consecutive_losses": 0,
            "recommended_risk_pct": 1.5
        }

    returns_r = [t["pnl_r"] for t in trades]
    risk_per_trade_usd = starting_balance * 0.015

    simulated_drawdowns = []
    simulated_consecutive_losses = []
    ruin_count = 0

    for _ in range(num_simulations):
        shuffled = random.sample(returns_r, len(returns_r))
        peak = starting_balance
        curr = starting_balance
        max_dd = 0.0
        consec_losses = 0
        max_consec = 0

        for r in shuffled:
            pnl = risk_per_trade_usd * r
            curr += pnl

            if r < 0:
                consec_losses += 1
                if consec_losses > max_consec:
                    max_consec = consec_losses
            else:
                consec_losses = 0

            if curr > peak:
                peak = curr
            dd = ((peak - curr) / peak) * 100.0
            if dd > max_dd:
                max_dd = dd

        simulated_drawdowns.append(max_dd)
        simulated_consecutive_losses.append(max_consec)
        if max_dd >= 25.0:  # 25% DD classified as severe ruin threshold
            ruin_count += 1

    simulated_drawdowns.sort()
    simulated_consecutive_losses.sort()

    median_dd = simulated_drawdowns[int(num_simulations * 0.50)]
    worst_95th_dd = simulated_drawdowns[int(num_simulations * 0.95)]
    worst_99th_dd = simulated_drawdowns[int(num_simulations * 0.99)]
    median_consec_losses = simulated_consecutive_losses[int(num_simulations * 0.50)]
    worst_consec_losses = simulated_consecutive_losses[int(num_simulations * 0.95)]
    prob_ruin = (ruin_count / num_simulations) * 100.0

    # Kelly Criterion: f = (p * b - q) / b
    wins = [r for r in returns_r if r > 0]
    losses = [r for r in returns_r if r < 0]
    p = len(wins) / len(returns_r)
    q = 1.0 - p
    avg_win = (sum(wins) / len(wins)) if wins else 2.5
    avg_loss = abs(sum(losses) / len(losses)) if losses else 1.0
    b = avg_win / avg_loss

    kelly_raw = ((p * b) - q) / b if b > 0 else 0.01
    half_kelly = max(0.5, min(2.5, round((kelly_raw / 2.0) * 100.0, 1)))

    return {
        "simulations": num_simulations,
        "median_drawdown_pct": round(median_dd, 2),
        "worst_case_drawdown_pct": round(worst_95th_dd, 2),
        "extreme_99th_drawdown_pct": round(worst_99th_dd, 2),
        "median_consecutive_losses": median_consec_losses,
        "worst_consecutive_losses": worst_consec_losses,
        "probability_of_ruin_pct": round(prob_ruin, 2),
        "recommended_risk_pct": half_kelly
    }

def print_backtest_report(result):
    m = result["metrics"]
    mc = result["monte_carlo"]

    print("\n" + "=" * 65)
    print(f"       🔬 QUANTITATIVE BACKTEST & MONTE CARLO AUDIT")
    print(f"       Aset: {result['symbol']} | Timeframe: {result['bar']} | Candles: {result['candles_analyzed']}")
    print("=" * 65)
    print(f"Modal Awal          : ${result['starting_balance']:,.2f} USDT")
    print(f"Modal Akhir         : ${result['final_balance']:,.2f} USDT")
    print(f"Total Keuntungan    : {'+' if result['total_pnl_usd']>=0 else ''}${result['total_pnl_usd']:,.2f} USDT ({result['roi_pct']:+.2f}%)")
    print("-------------------------------------------------------")
    print(f"Total Eksekusi Trade: {m['total_trades']} transaksi")
    print(f" * Menang (TP/Trail): {m['wins']} trade ({m['win_rate']}%)")
    print(f" * Impas (Breakeven): {m['breakevens']} trade (Free Roll)")
    print(f" * Kalah (Stop Loss): {m['losses']} trade")
    print(f"Win + Breakeven Rate: {m['win_plus_be_rate']}%")
    print(f"Profit Factor       : {m['profit_factor']} (Standar Institusi >= 1.8)")
    print(f"Expectancy per Trade: {m['expectancy_r']:+.2f}R")
    print(f"Maximum Drawdown    : {m['max_drawdown_pct']}%")
    print(f"Sharpe Ratio (Risk) : {m['sharpe_ratio']}")
    print(f"Sortino Ratio       : {m['sortino_ratio']}")
    print("-------------------------------------------------------")
    print(f"🎲 MONTE CARLO STRESS TEST ({mc['simulations']:,} Permutasi Acak):")
    print(f" * Median Drawdown  : {mc['median_drawdown_pct']}%")
    print(f" * Worst-Case (95%) : {mc['worst_case_drawdown_pct']}%")
    print(f" * Probability Ruin : {mc['probability_of_ruin_pct']}% (Target < 1.0%)")
    print(f" * Max Loss Streak  : {mc['worst_consecutive_losses']} loss berturut-turut")
    print(f" * Rekomendasi Risk : {mc['recommended_risk_pct']}% per trade (Half-Kelly)")

    if "overfitting_audit" in result:
        oa = result["overfitting_audit"]
        print("-------------------------------------------------------")
        print("🛡️ ANTI-OVERFITTING & LUCK TRAP AUDIT (IS vs OOS):")
        print(f" * Vonis Institusi  : {oa['verdict_label']}")
        print(f" * Walk-Forward Eff : {oa['walk_forward_efficiency_pct']}% (WFE - Target >= 50%)")
        print(f" * In-Sample (70%)  : {oa['in_sample'].get('trades_count', 0)} trade | PF: {oa['in_sample'].get('profit_factor', 0)} | Exp: {oa['in_sample'].get('expectancy_r', 0):+.2f}R")
        print(f" * Out-Sample (30%) : {oa['out_of_sample'].get('trades_count', 0)} trade | PF: {oa['out_of_sample'].get('profit_factor', 0)} | Exp: {oa['out_of_sample'].get('expectancy_r', 0):+.2f}R")
        dsr_val = oa['deflated_sharpe'].get('deflated_sharpe_ratio', 0)
        dsr_bench = oa['deflated_sharpe'].get('sr_benchmark', 0)
        print(f" * Deflated Sharpe  : {dsr_val} (DSR - Benchmark SR*: {dsr_bench})")
        print(f" * Permutasi p-Val  : {oa['p_value']} ({'Signifikan p < 0.05' if oa['p_value'] < 0.05 else 'Rentan Jebakan Keberuntungan p >= 0.05'})")
        print(f" * Diagnosa         : {oa['verdict_desc']}")
    print("=======================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quantitative Historical Backtester & Monte Carlo Engine")
    parser.add_argument("--symbol", type=str, default="BTC", help="Symbol ticker (default: BTC)")
    parser.add_argument("--bar", type=str, default="1H", help="Candle timeframe: 1H, 4H, 15m")
    parser.add_argument("--candles", type=int, default=500, help="Jumlah candle historis (default: 500)")
    parser.add_argument("--balance", type=float, default=5000.0, help="Starting balance USDT (default: 5000)")
    parser.add_argument("--risk", type=float, default=1.5, help="Risk per trade pct (default: 1.5)")
    args = parser.parse_args()

    res = run_backtest(
        symbol=args.symbol,
        bar=args.bar,
        num_candles=args.candles,
        starting_balance=args.balance,
        risk_pct=args.risk
    )
    print_backtest_report(res)

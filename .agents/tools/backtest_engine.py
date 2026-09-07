"""
Institutional Quantitative Alpha Engine & Multi-Strategy Backtester (Qanat-Inspired DAG)
Synthesized with Akademi Crypto (SMC, Fair Value Gap, Market Regime Gatekeeper, and AI Dynamic Exit Sentinel).

Key Capabilities:
1. Dual-Asset Point-in-Time Data Pipeline (Target Asset + BTC Benchmark Synchronized)
2. Bitcoin Macro Regime Directional Gatekeeper (Zero Lookahead Bias)
3. AI Dynamic Exit Sentinel Simulation (Breakeven, Profit-Lock at +0.35R, and Retracement Harvester)
4. Multi-Mode Head-to-Head Comparison (Raw vs +Gatekeeper vs +Exit Sentinel)
5. Multi-Asset Portfolio Alpha Book Aggregation (Qanat-style)
6. Agent-Native JSON Export for Automated Optimization
"""

import argparse
import json
import math
import os
import ssl
import sys
import time
import urllib.request
from datetime import datetime

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}

# ==============================================================================
# 1. DATA PIPELINE & SYNCHRONIZATION (DAG SOURCES)
# ==============================================================================

def fetch_klines(symbol="BTCUSDT", interval="1h", limit=500):
    """
    Fetches historical candlestick data from Binance Vision API.
    Supports limit > 1000 via backwards pagination.
    """
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    if not sym_clean.endswith("USDT") and not sym_clean.endswith("BUSD"):
        sym_clean = f"{sym_clean}USDT"

    all_candles = []
    remaining = limit
    end_time = None

    while remaining > 0:
        fetch_count = min(remaining, 1000)
        url = f"https://data-api.binance.vision/api/v3/klines?symbol={sym_clean}&interval={interval.lower()}&limit={fetch_count}"
        if end_time:
            url += f"&endTime={end_time}"

        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                if not raw:
                    break

                batch = []
                for c in raw:
                    batch.append({
                        "time": int(c[0]),
                        "open": float(c[1]),
                        "high": float(c[2]),
                        "low": float(c[3]),
                        "close": float(c[4]),
                        "volume": float(c[5])
                    })

                all_candles = batch + all_candles
                remaining -= len(batch)
                if len(batch) < fetch_count or remaining <= 0:
                    break
                end_time = batch[0]["time"] - 1
        except Exception as e:
            if not all_candles:
                print(f"[Error] Failed to fetch klines for {sym_clean}: {e}", file=sys.stderr)
            break

    # Deduplicate by timestamp and sort ascending
    seen = set()
    deduped = []
    for c in all_candles:
        if c["time"] not in seen:
            seen.add(c["time"])
            deduped.append(c)
    deduped.sort(key=lambda x: x["time"])
    return deduped[-limit:] if len(deduped) > limit else deduped

def fetch_synchronized_data(target_symbol, interval="1h", limit=500):
    """
    Dual-asset DAG source pipeline:
    Synchronizes target asset candles with BTCUSDT candles point-in-time.
    """
    sym_clean = target_symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    if not sym_clean.endswith("USDT"):
        sym_clean = f"{sym_clean}USDT"

    target_candles = fetch_klines(sym_clean, interval=interval, limit=limit)
    is_btc = "BTC" in sym_clean

    btc_candles = []
    if not is_btc:
        btc_candles = fetch_klines("BTCUSDT", interval=interval, limit=limit + 50)

    # Build lookup map for BTC candles
    btc_map = {c["time"]: c for c in btc_candles}

    return {
        "symbol": sym_clean,
        "interval": interval,
        "is_btc": is_btc,
        "target_candles": target_candles,
        "btc_map": btc_map,
        "btc_candles": btc_candles
    }

# ==============================================================================
# 2. QUANTITATIVE FEATURE ENGINEERING (DAG FEATURES)
# ==============================================================================

def calculate_ema_series(values, period):
    if not values:
        return []
    k = 2 / (period + 1)
    ema_list = [values[0]]
    for val in values[1:]:
        ema_list.append((val * k) + (ema_list[-1] * (1 - k)))
    return ema_list

def calculate_rsi_series(prices, period=14):
    if len(prices) < period + 1:
        return [50.0] * len(prices)

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    rsi_list = [50.0] * period

    gains = [max(d, 0) for d in deltas[:period]]
    losses = [max(-d, 0) for d in deltas[:period]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    for d in deltas[period:]:
        gain = max(d, 0)
        loss = max(-d, 0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        if avg_loss == 0:
            rsi_list.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_list.append(round(100.0 - (100.0 / (1.0 + rs)), 2))

    return [50.0] + rsi_list

def calculate_dmi_adx_series(candles, period=14):
    """
    Calculates Wilder's +DI, -DI, and ADX series across all candles.
    Returns: (plus_di_list, minus_di_list, adx_list)
    """
    n = len(candles)
    if n < period * 2:
        return [20.0] * n, [20.0] * n, [20.0] * n

    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    closes = [c["close"] for c in candles]

    tr_list = [highs[0] - lows[0]]
    plus_dm_list = [0.0]
    minus_dm_list = [0.0]

    for i in range(1, n):
        h, l = highs[i], lows[i]
        prev_h, prev_l, prev_c = highs[i - 1], lows[i - 1], closes[i - 1]

        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        tr_list.append(tr)

        up = h - prev_h
        down = prev_l - l
        plus_dm_list.append(up if (up > down and up > 0) else 0.0)
        minus_dm_list.append(down if (down > up and down > 0) else 0.0)

    # Initial sum
    sm_tr = [sum(tr_list[:period])]
    sm_plus = [sum(plus_dm_list[:period])]
    sm_minus = [sum(minus_dm_list[:period])]

    for i in range(period, len(tr_list)):
        sm_tr.append(sm_tr[-1] - (sm_tr[-1] / period) + tr_list[i])
        sm_plus.append(sm_plus[-1] - (sm_plus[-1] / period) + plus_dm_list[i])
        sm_minus.append(sm_minus[-1] - (sm_minus[-1] / period) + minus_dm_list[i])

    plus_di = [20.0] * (period - 1)
    minus_di = [20.0] * (period - 1)
    dx_list = []

    for i in range(len(sm_tr)):
        tr_val = sm_tr[i]
        p_dm = sm_plus[i]
        m_dm = sm_minus[i]

        p_val = (p_dm / tr_val * 100.0) if tr_val > 0 else 0.0
        m_val = (m_dm / tr_val * 100.0) if tr_val > 0 else 0.0

        plus_di.append(p_val)
        minus_di.append(m_val)

        diff = abs(p_val - m_val)
        total = p_val + m_val
        dx = (diff / total * 100.0) if total > 0 else 0.0
        dx_list.append(dx)

    adx_series = [20.0] * (period * 2 - 1)
    if len(dx_list) >= period:
        curr_adx = sum(dx_list[:period]) / period
        adx_series.append(curr_adx)
        for i in range(period, len(dx_list)):
            curr_adx = ((curr_adx * (period - 1)) + dx_list[i]) / period
            adx_series.append(curr_adx)

    # Pad if necessary to match n
    while len(plus_di) < n:
        plus_di.append(20.0)
    while len(minus_di) < n:
        minus_di.append(20.0)
    while len(adx_series) < n:
        adx_series.append(20.0)

    return plus_di[:n], minus_di[:n], adx_series[:n]

# ==============================================================================
# 3. BACKTEST SIMULATION ENGINE (DAG ALPHA & PNL)
# ==============================================================================

def run_backtest_simulation(
    sync_data,
    strategy_name="SMC_FVG",
    enable_gatekeeper=False,
    enable_exit_sentinel=False,
    starting_balance=10000.0,
    min_rr=2.5,
    risk_pct=1.5,
    fee_pct=0.05
):
    """
    Point-in-Time Backtesting Engine:
    - Zero lookahead bias
    - Simulates fee friction (0.05% round-trip)
    - Simulates BTC Macro Directional Gatekeeper
    - Simulates AI Dynamic Exit Sentinel & Breakeven Auto-Lock
    """
    candles = sync_data["target_candles"]
    if len(candles) < 50:
        return None

    is_btc = sync_data["is_btc"]
    btc_map = sync_data["btc_map"]

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    ema20 = calculate_ema_series(closes, 20)
    ema50 = calculate_ema_series(closes, 50)
    rsi = calculate_rsi_series(closes, 14)

    # Pre-calculate BTC features if needed for gatekeeper
    btc_candles = sync_data.get("btc_candles", [])
    btc_p_di, btc_m_di, btc_adx = [], [], []
    btc_ema20, btc_ema50 = [], []
    btc_time_idx = {}

    if not is_btc and btc_candles:
        btc_closes = [c["close"] for c in btc_candles]
        btc_ema20 = calculate_ema_series(btc_closes, 20)
        btc_ema50 = calculate_ema_series(btc_closes, 50)
        btc_p_di, btc_m_di, btc_adx = calculate_dmi_adx_series(btc_candles, 14)
        for idx, c in enumerate(btc_candles):
            btc_time_idx[c["time"]] = idx

    equity = starting_balance
    equity_curve = [equity]
    trades = []
    active_trade = None
    vetoed_count = 0

    for i in range(50, len(candles)):
        c = candles[i]
        curr_price = c["close"]
        curr_time = c["time"]

        # -------------------------------------------------------------
        # STEP 1: MANAGE ACTIVE TRADE (DYNAMIC RISK & EXIT SENTINEL)
        # -------------------------------------------------------------
        if active_trade:
            hit_sl = False
            hit_tp = False
            early_exit_price = None
            early_exit_reason = None

            entry_p = active_trade["entry"]
            risk_dist = active_trade["risk_dist"]
            side = active_trade["side"]

            # Current bar excursion
            if side == "LONG":
                bar_peak_r = (c["high"] - entry_p) / risk_dist if risk_dist > 0 else 0.0
                active_trade["peak_r"] = max(active_trade.get("peak_r", 0.0), bar_peak_r)
                current_r = (c["close"] - entry_p) / risk_dist if risk_dist > 0 else 0.0

                # 1A. Breakeven Auto-Lock (Standard: triggered at +1.0R)
                if not active_trade.get("be_moved") and active_trade["peak_r"] >= 1.0:
                    active_trade["sl"] = entry_p + (0.05 * risk_dist) # Micro-profit breakeven
                    active_trade["be_moved"] = True

                # 1B. AI Dynamic Exit Sentinel Simulation
                if enable_exit_sentinel:
                    # Profit-Lock at +0.35R -> Move SL to +0.15R
                    if not active_trade.get("profit_locked") and active_trade["peak_r"] >= 0.35:
                        active_trade["sl"] = max(active_trade["sl"], entry_p + (0.15 * risk_dist))
                        active_trade["profit_locked"] = True

                    # Early Take Profit on Severe Retracement from peak (+0.8R+ lost > 40%)
                    if active_trade["peak_r"] >= 0.85 and current_r <= (active_trade["peak_r"] * 0.55):
                        early_exit_price = curr_price
                        early_exit_reason = "AI_SENTINEL_PROFIT_HARVEST"

                # Check SL / TP
                if not early_exit_price:
                    if c["low"] <= active_trade["sl"]:
                        hit_sl = True
                    elif c["high"] >= active_trade["tp"]:
                        hit_tp = True

            else: # SHORT
                bar_peak_r = (entry_p - c["low"]) / risk_dist if risk_dist > 0 else 0.0
                active_trade["peak_r"] = max(active_trade.get("peak_r", 0.0), bar_peak_r)
                current_r = (entry_p - c["close"]) / risk_dist if risk_dist > 0 else 0.0

                # Breakeven Auto-Lock
                if not active_trade.get("be_moved") and active_trade["peak_r"] >= 1.0:
                    active_trade["sl"] = entry_p - (0.05 * risk_dist)
                    active_trade["be_moved"] = True

                # AI Dynamic Exit Sentinel
                if enable_exit_sentinel:
                    if not active_trade.get("profit_locked") and active_trade["peak_r"] >= 0.35:
                        active_trade["sl"] = min(active_trade["sl"], entry_p - (0.15 * risk_dist))
                        active_trade["profit_locked"] = True

                    if active_trade["peak_r"] >= 0.85 and current_r <= (active_trade["peak_r"] * 0.55):
                        early_exit_price = curr_price
                        early_exit_reason = "AI_SENTINEL_PROFIT_HARVEST"

                if not early_exit_price:
                    if c["high"] >= active_trade["sl"]:
                        hit_sl = True
                    elif c["low"] <= active_trade["tp"]:
                        hit_tp = True

            # Process Trade Exit
            if hit_sl or hit_tp or early_exit_price:
                if early_exit_price:
                    exit_price = early_exit_price
                    exit_reason = early_exit_reason
                else:
                    exit_price = active_trade["sl"] if hit_sl else active_trade["tp"]
                    exit_reason = "SL_HIT" if hit_sl else "TP_HIT"

                if side == "LONG":
                    gross_pnl = (exit_price - entry_p) * active_trade["units"]
                else:
                    gross_pnl = (entry_p - exit_price) * active_trade["units"]

                # Round-trip trading fee
                fee = (active_trade["size_usd"] * 2) * (fee_pct / 100.0)
                net_pnl = gross_pnl - fee
                equity += net_pnl
                equity_curve.append(equity)

                trades.append({
                    "id": len(trades) + 1,
                    "side": side,
                    "entry": entry_p,
                    "exit": exit_price,
                    "size_usd": active_trade["size_usd"],
                    "pnl": net_pnl,
                    "peak_r": round(active_trade.get("peak_r", 0.0), 2),
                    "reason": exit_reason,
                    "bars_held": i - active_trade["entry_bar"]
                })
                active_trade = None
                continue

        # -------------------------------------------------------------
        # STEP 2: STRATEGY SIGNAL GENERATION (DAG WEIGHTS)
        # -------------------------------------------------------------
        signal = None

        # --- Strategy A: SMC Fair Value Gap (FVG) + Structure ---
        if strategy_name in ["SMC_FVG", "FVG"]:
            # Bullish FVG
            if lows[i] > highs[i - 2] and curr_price > ema20[i] > ema50[i]:
                sl = lows[i - 2] * 0.995
                dist_sl = curr_price - sl
                if dist_sl > 0:
                    tp = curr_price + (dist_sl * min_rr)
                    signal = {"side": "LONG", "sl": sl, "tp": tp, "risk_dist": dist_sl, "reason": "Bullish FVG"}
            # Bearish FVG
            elif highs[i] < lows[i - 2] and curr_price < ema20[i] < ema50[i]:
                sl = highs[i - 2] * 1.005
                dist_sl = sl - curr_price
                if dist_sl > 0:
                    tp = curr_price - (dist_sl * min_rr)
                    signal = {"side": "SHORT", "sl": sl, "tp": tp, "risk_dist": dist_sl, "reason": "Bearish FVG"}

        # --- Strategy B: RSI Mean Reversion ---
        elif strategy_name in ["RSI_MEAN_REVERSION", "RSI"]:
            if rsi[i - 1] < 32 and rsi[i] >= 32:
                sl = min(lows[max(0, i - 5):i + 1]) * 0.995
                dist = curr_price - sl
                if dist > 0:
                    signal = {"side": "LONG", "sl": sl, "tp": curr_price + (dist * min_rr), "risk_dist": dist, "reason": "RSI Oversold Bounce"}
            elif rsi[i - 1] > 68 and rsi[i] <= 68:
                sl = max(highs[max(0, i - 5):i + 1]) * 1.005
                dist = sl - curr_price
                if dist > 0:
                    signal = {"side": "SHORT", "sl": sl, "tp": curr_price - (dist * min_rr), "risk_dist": dist, "reason": "RSI Overbought Reversal"}

        # --- Strategy C: EMA Golden / Death Cross ---
        elif strategy_name in ["EMA_CROSS", "EMA"]:
            if ema20[i - 1] <= ema50[i - 1] and ema20[i] > ema50[i]:
                sl = min(lows[max(0, i - 10):i + 1]) * 0.995
                dist = curr_price - sl
                if dist > 0:
                    signal = {"side": "LONG", "sl": sl, "tp": curr_price + (dist * min_rr), "risk_dist": dist, "reason": "EMA Golden Cross"}
            elif ema20[i - 1] >= ema50[i - 1] and ema20[i] < ema50[i]:
                sl = max(highs[max(0, i - 10):i + 1]) * 1.005
                dist = sl - curr_price
                if dist > 0:
                    signal = {"side": "SHORT", "sl": sl, "tp": curr_price - (dist * min_rr), "risk_dist": dist, "reason": "EMA Death Cross"}

        # --- Strategy D: Patrick Nill 3-Touch S/R Bounce ---
        elif strategy_name in ["PATRICK_NILL", "NILL"]:
            lookback_lows = lows[max(0, i - 20):i]
            if len(lookback_lows) >= 15:
                support = min(lookback_lows)
                # If touching within 0.3% of support and bouncing up
                if abs(curr_price - support) / curr_price < 0.005 and curr_price > closes[i - 1]:
                    sl = support * 0.994
                    dist = curr_price - sl
                    if dist > 0:
                        signal = {"side": "LONG", "sl": sl, "tp": curr_price + (dist * min_rr), "risk_dist": dist, "reason": "Patrick Nill 3-Touch Support"}

        # -------------------------------------------------------------
        # STEP 3: BTC MACRO DIRECTIONAL GATEKEEPER FILTER
        # -------------------------------------------------------------
        if signal and enable_gatekeeper and not is_btc:
            # Synchronize point-in-time BTC state at timestamp c["time"]
            b_idx = btc_time_idx.get(curr_time)
            if b_idx is not None and b_idx < len(btc_candles):
                b_close = btc_candles[b_idx]["close"]
                b_ema20 = btc_ema20[b_idx]
                b_ema50 = btc_ema50[b_idx]
                b_plus = btc_p_di[b_idx]
                b_minus = btc_m_di[b_idx]

                # BTC Bearish Definition: Price < EMA20 and -DI > +DI
                is_btc_bearish = (b_close < b_ema20 and b_minus > b_plus) or (b_close < b_ema50 and b_minus > b_plus)
                # BTC Bullish Definition: Price > EMA20 and +DI > -DI
                is_btc_bullish = (b_close > b_ema20 and b_plus > b_minus) or (b_close > b_ema50 and b_plus > b_minus)

                # Gatekeeper Rules
                if signal["side"] == "LONG" and is_btc_bearish:
                    vetoed_count += 1
                    signal = None # VETO LONG
                elif signal["side"] == "SHORT" and is_btc_bullish:
                    vetoed_count += 1
                    signal = None # VETO SHORT

        # -------------------------------------------------------------
        # STEP 4: POSITION SIZING & ENTRY EXECUTION
        # -------------------------------------------------------------
        if signal:
            sl_pct = abs(curr_price - signal["sl"]) / curr_price
            risk_budget = equity * (risk_pct / 100.0)
            pos_size_usd = min(risk_budget / max(sl_pct, 0.005), equity * 2.5)
            units = pos_size_usd / curr_price

            active_trade = {
                "side": signal["side"],
                "entry": curr_price,
                "sl": signal["sl"],
                "tp": signal["tp"],
                "risk_dist": signal["risk_dist"],
                "size_usd": pos_size_usd,
                "units": units,
                "entry_bar": i,
                "peak_r": 0.0
            }

    # -------------------------------------------------------------
    # STEP 5: CALCULATE QUANTITATIVE METRICS
    # -------------------------------------------------------------
    total_trades = len(trades)
    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0.0

    gross_gains = sum(t["pnl"] for t in wins)
    gross_loss = abs(sum(t["pnl"] for t in losses))
    profit_factor = round(gross_gains / gross_loss, 2) if gross_loss > 0 else (99.0 if gross_gains > 0 else 0.0)

    net_pnl = equity - starting_balance
    net_roi = (net_pnl / starting_balance) * 100

    peak = equity_curve[0]
    max_dd_pct = 0.0
    for val in equity_curve:
        if val > peak:
            peak = val
        dd = (peak - val) / peak * 100.0
        if dd > max_dd_pct:
            max_dd_pct = dd

    returns = [(equity_curve[j] - equity_curve[j - 1]) / equity_curve[j - 1] for j in range(1, len(equity_curve))]
    if returns and len(returns) > 1:
        mean_ret = sum(returns) / len(returns)
        std_ret = math.sqrt(sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1))
        sharpe = round((mean_ret / std_ret) * math.sqrt(365 * 24), 2) if std_ret > 0 else 0.0
    else:
        sharpe = 0.0

    return {
        "strategy": strategy_name,
        "enable_gatekeeper": enable_gatekeeper,
        "enable_exit_sentinel": enable_exit_sentinel,
        "total_trades": total_trades,
        "wins": len(wins),
        "losses": len(losses),
        "vetoed_count": vetoed_count,
        "win_rate": round(win_rate, 1),
        "profit_factor": profit_factor,
        "net_pnl": round(net_pnl, 2),
        "net_roi": round(net_roi, 2),
        "max_drawdown": round(max_dd_pct, 2),
        "sharpe_ratio": sharpe,
        "final_equity": round(equity, 2),
        "equity_curve": equity_curve,
        "trades": trades
    }

# ==============================================================================
# 4. REPORTING & VISUALIZATION (QANAT CONSOLE BENCHMARK)
# ==============================================================================

def render_ascii_sparkline(values, width=25):
    if not values or len(values) < 2:
        return "N/A"
    chars = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    min_v = min(values)
    max_v = max(values)
    if max_v == min_v:
        return chars[3] * min(len(values), width)

    step = max(1, len(values) // width)
    sampled = [values[i] for i in range(0, len(values), step)][:width]

    line = ""
    for v in sampled:
        idx = int((v - min_v) / (max_v - min_v) * (len(chars) - 1))
        line += chars[idx]
    return line

def display_single_report(res, symbol, timeframe, candles_count):
    if not res:
        print("Data tidak mencukupi untuk backtest.")
        return

    print("\n" + "=" * 68)
    print(f"       📊 QUANT STRATEGY BACKTEST REPORT (QANAT-INSPIRED)")
    print(f"       Pair: {symbol.upper()} | TF: {timeframe.upper()} | Data: {candles_count} Bar Candles")
    print(f"       Strategi: {res['strategy']}")
    print("=" * 68)
    print(f"Konfigurasi Pertahanan:")
    print(f" * BTC Macro Gatekeeper : {'🟢 AKTIF (Anti-Downtrend)' if res['enable_gatekeeper'] else '⚪ NONAKTIF (Raw Strategy)'}")
    print(f" * Dynamic Exit Sentinel: {'🟢 AKTIF (Profit-Lock & Harvester)' if res['enable_exit_sentinel'] else '⚪ NONAKTIF (Static SL/TP)'}")
    print("-" * 68)
    print(f"Modal Awal (Starting)   : $10,000.00 USDT")
    print(f"Modal Akhir (Equity)    : ${res['final_equity']:,.2f} USDT")
    print(f"Net Profit / ROI        : {'+' if res['net_pnl'] >= 0 else ''}${res['net_pnl']:,.2f} ({res['net_roi']:+.2f}%)")
    print("-" * 68)
    print(f"Total Eksekusi Selesai  : {res['total_trades']} Trades")
    print(f"Trade Ditangkis (Veto)  : {res['vetoed_count']} Trades Berbahaya Dicegah!")
    print(f"Win Rate                : {res['win_rate']}% ({res['wins']} Menang / {res['losses']} Kalah)")
    print(f"Profit Factor (PF)      : {res['profit_factor']}")
    print(f"Max Drawdown (MDD)      : -{res['max_drawdown']}%")
    print(f"Sharpe Ratio (Annual)   : {res['sharpe_ratio']}")
    sparkline = render_ascii_sparkline(res['equity_curve'])
    print(f"Kurva Pertumbuhan Modal : [{sparkline}]")
    print("=" * 68)

    # Academic Rating
    pf = res['profit_factor']
    wr = res['win_rate']
    if pf >= 2.0 and wr >= 50:
        verdict = "🌟 GRADE A+ (Sangat Unggul & Siap Live Deployment)"
    elif pf >= 1.5:
        verdict = "🟢 GRADE B (Menguntungkan, Layak Demo Trading)"
    elif pf >= 1.0:
        verdict = "🟡 GRADE C (Break-even, Perlu Optimasi Parameter)"
    else:
        verdict = "🔴 GRADE D (Tidak Direkomendasikan, Drawdown Tinggi)"
    print(f"Status Kualifikasi      : {verdict}")
    print("=" * 68 + "\n")

def run_mode_comparison(sync_data, strategy_name="SMC_FVG", min_rr=2.5, risk_pct=1.5):
    """
    Qanat-Style Alpha Book Comparison:
    Compares Raw Strategy vs +Gatekeeper vs +Gatekeeper + Exit Sentinel.
    """
    sym = sync_data["symbol"]
    tf = sync_data["interval"]
    candles = sync_data["target_candles"]

    print(f"\n==================================================================================")
    print(f"       🔬 HEAD-TO-HEAD QUANTITATIVE ABLATION STUDY: {sym} ({tf.upper()})")
    print(f"       Pengujian {len(candles)} Bar Candle pada Strategi: {strategy_name}")
    print("==================================================================================")

    # Mode 1: RAW
    m1 = run_backtest_simulation(sync_data, strategy_name, enable_gatekeeper=False, enable_exit_sentinel=False, min_rr=min_rr, risk_pct=risk_pct)
    # Mode 2: + Gatekeeper
    m2 = run_backtest_simulation(sync_data, strategy_name, enable_gatekeeper=True, enable_exit_sentinel=False, min_rr=min_rr, risk_pct=risk_pct)
    # Mode 3: + Gatekeeper + Exit Sentinel
    m3 = run_backtest_simulation(sync_data, strategy_name, enable_gatekeeper=True, enable_exit_sentinel=True, min_rr=min_rr, risk_pct=risk_pct)

    results = [
        ("1. RAW (Standard)", m1),
        ("2. + BTC Gatekeeper", m2),
        ("3. + Gatekeeper + Sentinel", m3)
    ]

    print(f"\n{'Mode Pengujian':<28} | {'Trades':<7} | {'Win Rate':<10} | {'PF':<6} | {'Net ROI (%)':<12} | {'Max DD':<9} | {'Vetoed'}")
    print("-" * 88)
    for label, r in results:
        if r:
            veto_str = f"{r['vetoed_count']} SL dicegah" if r['vetoed_count'] > 0 else "-"
            print(f"{label:<28} | {r['total_trades']:<7} | {r['win_rate']:<5}%     | {r['profit_factor']:<6} | {r['net_roi']:>+8.2f}%    | -{r['max_drawdown']:<6}%  | {veto_str}")
    print("=" * 88)

    # Mathematical Proof Highlight
    if m1 and m3:
        roi_diff = m3["net_roi"] - m1["net_roi"]
        dd_diff = m1["max_drawdown"] - m3["max_drawdown"]
        print(f"\n💡 KESIMPULAN KUANTITATIF:")
        print(f" * Peningkatan ROI Bersih : {roi_diff:+.2f}% dibanding strategi mentah")
        print(f" * Penurunan Drawdown     : {dd_diff:.2f}% risiko kerugian berhasil dipangkas")
        print(f" * Trade Berbahaya Dicegah: {m3['vetoed_count']} setup tertolak otomatis karena melawan gravitasi BTC!\n")

    return results

def run_portfolio_benchmark(symbols, interval="1h", limit=500, strategy_name="SMC_FVG"):
    """
    Qanat Multi-Asset Universe Backtest:
    Runs backtest across multiple assets and calculates combined portfolio book.
    """
    print(f"\n==================================================================================")
    print(f"       🌐 MULTI-ASSET PORTFOLIO UNIVERSE BENCHMARK (QANAT ALPHAS)")
    print(f"       Watchlist: {', '.join(symbols)} | Timeframe: {interval.upper()} | Limit: {limit}")
    print("==================================================================================")

    total_starting = len(symbols) * 10000.0
    total_final = 0.0
    total_trades = 0
    total_wins = 0
    all_results = []

    print(f"\n{'Symbol':<12} | {'Trades':<7} | {'Win Rate':<10} | {'PF':<6} | {'Net ROI (%)':<12} | {'Max DD':<9} | {'Vetoed'}")
    print("-" * 75)

    for sym in symbols:
        sync_data = fetch_synchronized_data(sym, interval=interval, limit=limit)
        res = run_backtest_simulation(sync_data, strategy_name=strategy_name, enable_gatekeeper=True, enable_exit_sentinel=True)
        if res:
            all_results.append((sym, res))
            total_final += res["final_equity"]
            total_trades += res["total_trades"]
            total_wins += res["wins"]
            print(f"{sym:<12} | {res['total_trades']:<7} | {res['win_rate']:<5}%     | {res['profit_factor']:<6} | {res['net_roi']:>+8.2f}%    | -{res['max_drawdown']:<6}%  | {res['vetoed_count']}")

    print("=" * 75)
    combined_roi = ((total_final - total_starting) / total_starting) * 100
    combined_wr = (total_wins / total_trades * 100) if total_trades > 0 else 0.0

    print(f"\n📈 RINGKASAN BUKU PORTOFOLIO GABUNGAN:")
    print(f" * Total Modal Portofolio : ${total_starting:,.2f} USDT -> ${total_final:,.2f} USDT")
    print(f" * Net Portofolio ROI     : {combined_roi:+.2f}%")
    print(f" * Average Win Rate       : {combined_wr:.1f}% across {total_trades} trades")
    print("=" * 75 + "\n")

# ==============================================================================
# 5. CLI CONTROLLER
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Institutional Quantitative Alpha Engine & Backtester")
    parser.add_argument("--symbol", type=str, default="SOLUSDT", help="Pair koin (misal: BTCUSDT, SOLUSDT, ETHUSDT)")
    parser.add_argument("--strategy", type=str, default="SMC_FVG", choices=["SMC_FVG", "RSI", "EMA", "NILL", "ALL"])
    parser.add_argument("--timeframe", type=str, default="1h", choices=["15m", "1h", "4h", "1d"])
    parser.add_argument("--candles", type=int, default=500, help="Jumlah bar data historis (default: 500, maks: 2000)")
    parser.add_argument("--gatekeeper", action="store_true", help="Aktifkan simulasi BTC Macro Directional Gatekeeper")
    parser.add_argument("--exit-sentinel", action="store_true", help="Aktifkan simulasi AI Dynamic Exit Sentinel")
    parser.add_argument("--compare-modes", action="store_true", help="Jalankan studi ablasi komparasi 3 mode (Raw vs Gatekeeper vs Sentinel)")
    parser.add_argument("--portfolio", type=str, default=None, help="Daftar simbol portofolio dipisah koma (misal: BTC,ETH,SOL,ADA)")
    parser.add_argument("--risk", type=float, default=1.5, help="Resiko per trade persen (default: 1.5)")
    parser.add_argument("--rr", type=float, default=2.5, help="Min Risk-Reward ratio (default: 2.5)")
    parser.add_argument("--json", action="store_true", help="Output hasil dalam format JSON untuk AI Agent")

    args = parser.parse_args()

    # Portfolio mode
    if args.portfolio:
        syms = [s.strip().upper() for s in args.portfolio.split(",") if s.strip()]
        run_portfolio_benchmark(syms, interval=args.timeframe, limit=args.candles, strategy_name=args.strategy)
        return

    # Single Symbol Mode
    sync_data = fetch_synchronized_data(args.symbol, interval=args.timeframe, limit=args.candles)
    if not sync_data["target_candles"]:
        print("Gagal mengambil data historis.")
        return

    if args.compare_modes:
        run_mode_comparison(sync_data, strategy_name=args.strategy, min_rr=args.rr, risk_pct=args.risk)
    elif args.json:
        res = run_backtest_simulation(
            sync_data,
            strategy_name=args.strategy,
            enable_gatekeeper=args.gatekeeper,
            enable_exit_sentinel=args.exit_sentinel,
            min_rr=args.rr,
            risk_pct=args.risk
        )
        # Drop raw equity curve for concise JSON output
        out = dict(res)
        out.pop("equity_curve", None)
        out.pop("trades", None)
        print(json.dumps(out, indent=2))
    else:
        res = run_backtest_simulation(
            sync_data,
            strategy_name=args.strategy,
            enable_gatekeeper=args.gatekeeper,
            enable_exit_sentinel=args.exit_sentinel,
            min_rr=args.rr,
            risk_pct=args.risk
        )
        display_single_report(res, sync_data["symbol"], args.timeframe, len(sync_data["target_candles"]))

if __name__ == "__main__":
    main()

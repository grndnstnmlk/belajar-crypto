"""
Institutional Quant Backtester & Alpha Strategy Engine (Vibe-Trading Adapted)
Synthesized with Akademi Crypto (SMC, Fair Value Gap, Wyckoff, and Risk Management).
Simulates historical trades, fee friction, Sharpe ratio, and Max Drawdown without Docker.
"""

import argparse
import json
import math
import os
import ssl
import sys
import urllib.request
from datetime import datetime

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
GENOME_FILE = os.path.join(DATA_DIR, "agent_genome.json")

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_klines(symbol="BTCUSDT", interval="1h", limit=300):
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={sym_clean}&interval={interval.lower()}&limit={limit}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            candles = []
            for c in raw:
                candles.append({
                    "time": int(c[0]),
                    "open": float(c[1]),
                    "high": float(c[2]),
                    "low": float(c[3]),
                    "close": float(c[4]),
                    "volume": float(c[5])
                })
            return candles
    except Exception as e:
        print(f"[Error] Failed to fetch klines from Binance Vision: {e}", file=sys.stderr)
        return []

def calculate_rsi(prices, period=14):
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

def calculate_ema_series(values, period):
    if not values:
        return []
    k = 2 / (period + 1)
    ema_list = [values[0]]
    for val in values[1:]:
        ema_list.append((val * k) + (ema_list[-1] * (1 - k)))
    return ema_list

def run_backtest(candles, strategy_name="SMC_FVG", starting_balance=10000.0, min_rr=2.25, risk_pct=1.5, fee_pct=0.05):
    if len(candles) < 50:
        return None

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    ema20 = calculate_ema_series(closes, 20)
    ema50 = calculate_ema_series(closes, 50)
    rsi = calculate_rsi(closes, 14)

    equity = starting_balance
    equity_curve = [equity]
    trades = []
    active_trade = None

    for i in range(50, len(candles)):
        c = candles[i]
        curr_price = c["close"]

        # 1. Manage Active Trade
        if active_trade:
            hit_sl = False
            hit_tp = False

            if active_trade["side"] == "LONG":
                # Trailing Breakeven Trigger
                if not active_trade.get("be_moved") and c["high"] >= active_trade["entry"] + active_trade["risk_dist"]:
                    active_trade["sl"] = active_trade["entry"]
                    active_trade["be_moved"] = True

                if c["low"] <= active_trade["sl"]:
                    hit_sl = True
                elif c["high"] >= active_trade["tp"]:
                    hit_tp = True
            else: # SHORT
                # Trailing Breakeven Trigger
                if not active_trade.get("be_moved") and c["low"] <= active_trade["entry"] - active_trade["risk_dist"]:
                    active_trade["sl"] = active_trade["entry"]
                    active_trade["be_moved"] = True

                if c["high"] >= active_trade["sl"]:
                    hit_sl = True
                elif c["low"] <= active_trade["tp"]:
                    hit_tp = True

            if hit_sl or hit_tp:
                exit_price = active_trade["sl"] if hit_sl else active_trade["tp"]
                if active_trade["side"] == "LONG":
                    gross_pnl = (exit_price - active_trade["entry"]) * active_trade["units"]
                else:
                    gross_pnl = (active_trade["entry"] - exit_price) * active_trade["units"]

                # Deduct Round-trip trading fee
                fee = (active_trade["size_usd"] * 2) * (fee_pct / 100.0)
                net_pnl = gross_pnl - fee
                equity += net_pnl
                equity_curve.append(equity)

                trades.append({
                    "id": len(trades) + 1,
                    "side": active_trade["side"],
                    "entry": active_trade["entry"],
                    "exit": exit_price,
                    "size_usd": active_trade["size_usd"],
                    "pnl": net_pnl,
                    "reason": "SL_HIT" if hit_sl else "TP_HIT",
                    "bars_held": i - active_trade["entry_bar"]
                })
                active_trade = None
                continue

        # 2. Strategy Signal Generation (if no active trade)
        signal = None
        # --- Strategy 1: SMC Fair Value Gap (FVG) + EMA Trend ---
        if strategy_name in ["SMC_FVG", "FVG"]:
            # Bullish FVG: Low of candle[i] > High of candle[i-2]
            if lows[i] > highs[i - 2] and curr_price > ema20[i] > ema50[i]:
                # Invalidation SL below gap wick
                sl = lows[i - 2] * 0.995
                dist_sl = curr_price - sl
                if dist_sl > 0:
                    tp = curr_price + (dist_sl * min_rr)
                    signal = {"side": "LONG", "sl": sl, "tp": tp, "risk_dist": dist_sl}
            # Bearish FVG: High of candle[i] < Low of candle[i-2]
            elif highs[i] < lows[i - 2] and curr_price < ema20[i] < ema50[i]:
                sl = highs[i - 2] * 1.005
                dist_sl = sl - curr_price
                if dist_sl > 0:
                    tp = curr_price - (dist_sl * min_rr)
                    signal = {"side": "SHORT", "sl": sl, "tp": tp, "risk_dist": dist_sl}

        # --- Strategy 2: RSI Mean Reversion ---
        elif strategy_name in ["RSI_MEAN_REVERSION", "RSI"]:
            # Long: RSI in extreme oversold (< 35) bouncing back
            if rsi[i - 1] < 35 and rsi[i] >= 35:
                sl = min(lows[max(0, i - 4):i + 1]) * 0.995
                dist = curr_price - sl
                if dist > 0:
                    signal = {"side": "LONG", "sl": sl, "tp": curr_price + (dist * min_rr), "risk_dist": dist}
            # Short: RSI in extreme overbought (> 65) turning down
            elif rsi[i - 1] > 65 and rsi[i] <= 65:
                sl = max(highs[max(0, i - 4):i + 1]) * 1.005
                dist = sl - curr_price
                if dist > 0:
                    signal = {"side": "SHORT", "sl": sl, "tp": curr_price - (dist * min_rr), "risk_dist": dist}

        # --- Strategy 3: EMA Golden / Death Cross ---
        elif strategy_name in ["EMA_CROSS", "EMA"]:
            if ema20[i - 1] <= ema50[i - 1] and ema20[i] > ema50[i]:
                sl = min(lows[i - 10:i + 1]) * 0.995
                dist = curr_price - sl
                if dist > 0:
                    signal = {"side": "LONG", "sl": sl, "tp": curr_price + (dist * min_rr)}
            elif ema20[i - 1] >= ema50[i - 1] and ema20[i] < ema50[i]:
                sl = max(highs[i - 10:i + 1]) * 1.005
                dist = sl - curr_price
                if dist > 0:
                    signal = {"side": "SHORT", "sl": sl, "tp": curr_price - (dist * min_rr)}

        # Open trade if signal valid
        if signal:
            sl_pct = abs(curr_price - signal["sl"]) / curr_price
            risk_budget = equity * (risk_pct / 100.0)
            pos_size_usd = min(risk_budget / max(sl_pct, 0.005), equity * 2.5)
            units = pos_size_usd / curr_price

            risk_dist = abs(curr_price - signal["sl"])
            active_trade = {
                "side": signal["side"],
                "entry": curr_price,
                "sl": signal["sl"],
                "tp": signal["tp"],
                "risk_dist": risk_dist,
                "size_usd": pos_size_usd,
                "units": units,
                "entry_bar": i
            }

    # 3. Calculate Performance Metrics
    total_trades = len(trades)
    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0.0

    gross_gains = sum(t["pnl"] for t in wins)
    gross_loss = abs(sum(t["pnl"] for t in losses))
    profit_factor = round(gross_gains / gross_loss, 2) if gross_loss > 0 else (99.0 if gross_gains > 0 else 0.0)

    net_pnl = equity - starting_balance
    net_roi = (net_pnl / starting_balance) * 100

    # Max Drawdown
    peak = equity_curve[0]
    max_dd_pct = 0.0
    for val in equity_curve:
        if val > peak:
            peak = val
        dd = (peak - val) / peak * 100.0
        if dd > max_dd_pct:
            max_dd_pct = dd

    # Sharpe Ratio Approximation
    returns = [(equity_curve[j] - equity_curve[j - 1]) / equity_curve[j - 1] for j in range(1, len(equity_curve))]
    if returns and len(returns) > 1:
        mean_ret = sum(returns) / len(returns)
        std_ret = math.sqrt(sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1))
        sharpe = round((mean_ret / std_ret) * math.sqrt(365 * 24), 2) if std_ret > 0 else 0.0
    else:
        sharpe = 0.0

    return {
        "strategy": strategy_name,
        "total_trades": total_trades,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 1),
        "profit_factor": profit_factor,
        "net_pnl": round(net_pnl, 2),
        "net_roi": round(net_roi, 2),
        "max_drawdown": round(max_dd_pct, 2),
        "sharpe_ratio": sharpe,
        "final_equity": round(equity, 2),
        "equity_curve": equity_curve
    }

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

def display_report(res, symbol, timeframe, candles_count):
    if not res:
        print("Data tidak mencukupi untuk backtest.")
        return

    print("\n" + "=" * 65)
    print(f"       📊 QUANT STRATEGY BACKTEST REPORT (VIBE-TRADING)")
    print(f"       Pair: {symbol.upper()} | TF: {timeframe.upper()} | Data: {candles_count} Bar Candles")
    print(f"       Strategi: {res['strategy']}")
    print("=" * 65)
    print(f"Modal Awal (Starting) : $10,000.00 USDT")
    print(f"Modal Akhir (Equity)  : ${res['final_equity']:,.2f} USDT")
    print(f"Net Profit / ROI      : {'+' if res['net_pnl'] >= 0 else ''}${res['net_pnl']:,.2f} ({res['net_roi']:+.2f}%)")
    print("-" * 65)
    print(f"Total Transaksi Selesai: {res['total_trades']} Trades")
    print(f"Win Rate              : {res['win_rate']}% ({res['wins']} Menang / {res['losses']} Kalah)")
    print(f"Profit Factor (PF)    : {res['profit_factor']}")
    print(f"Max Drawdown (MDD)    : -{res['max_drawdown']}%")
    print(f"Sharpe Ratio (Annual) : {res['sharpe_ratio']}")
    sparkline = render_ascii_sparkline(res['equity_curve'])
    print(f"Grafik Pertumbuhan    : [{sparkline}]")
    print("=" * 65)

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
    print(f"Status Kualifikasi    : {verdict}")
    print("=" * 65 + "\n")

def compare_all_strategies(candles, symbol, timeframe):
    strategies = ["SMC_FVG", "RSI_MEAN_REVERSION", "EMA_CROSS"]
    results = []

    print(f"\nMenjalankan simulasi komparasi {len(strategies)} strategi pada {len(candles)} candle data...")
    for st in strategies:
        r = run_backtest(candles, strategy_name=st)
        if r:
            results.append(r)

    print("\n" + "=" * 76)
    print(f"       🏆 STRATEGY ALPHA ZOO BENCHMARK: {symbol.upper()} ({timeframe.upper()})")
    print("=" * 76)
    print(f"{'Strategi':<18} | {'Win Rate':<10} | {'Profit Factor':<14} | {'Net ROI (%)':<12} | {'Max DD':<8}")
    print("-" * 76)
    for r in results:
        print(f"{r['strategy']:<18} | {r['win_rate']:<5}%     | {r['profit_factor']:<14} | {r['net_roi']:>+8.2f}%    | -{r['max_drawdown']}%")
    print("=" * 76)

    # Suggest best strategy
    if results:
        best = max(results, key=lambda x: x["profit_factor"] * (x["win_rate"] / 50.0))
        print(f"\n💡 Strategi Terbaik untuk {symbol.upper()} saat ini: {best['strategy']} (PF: {best['profit_factor']}, ROI: {best['net_roi']:+.2f}%)")
    print("=" * 76 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Vibe-Trading Quant Backtester")
    parser.add_argument("--symbol", type=str, default="SOLUSDT", help="Pair koin (misal: BTCUSDT, SOLUSDT, ETHUSDT)")
    parser.add_argument("--strategy", type=str, default="SMC_FVG", choices=["SMC_FVG", "RSI", "EMA", "ALL", "all"])
    parser.add_argument("--timeframe", type=str, default="1h", choices=["15m", "1h", "4h", "1d"])
    parser.add_argument("--candles", type=int, default=300, help="Jumlah bar data historis (maks: 1000)")
    parser.add_argument("--risk", type=float, default=1.5, help="Resiko per trade persen (default: 1.5)")
    parser.add_argument("--rr", type=float, default=2.25, help="Min Risk-Reward ratio (default: 2.25)")

    args = parser.parse_args()
    sym_clean = args.symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    if not sym_clean.endswith("USDT"):
        sym_clean = f"{sym_clean}USDT"

    print(f"\nMengunduh {args.candles} data candle {sym_clean} ({args.timeframe}) dari Binance Vision...")
    candles = fetch_klines(sym_clean, interval=args.timeframe, limit=args.candles)
    if not candles:
        print("Gagal mengambil data historis.")
        return

    if args.strategy.upper() == "ALL":
        compare_all_strategies(candles, sym_clean, args.timeframe)
    else:
        st_name = "SMC_FVG" if args.strategy.upper() in ["SMC_FVG", "FVG"] else ("RSI_MEAN_REVERSION" if args.strategy.upper() == "RSI" else "EMA_CROSS")
        res = run_backtest(candles, strategy_name=st_name, min_rr=args.rr, risk_pct=args.risk)
        display_report(res, sym_clean, args.timeframe, len(candles))

if __name__ == "__main__":
    main()

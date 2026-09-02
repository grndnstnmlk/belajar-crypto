"""
Quantitative Flight Simulator (Mesin Jam Terbang AI)
Simulates hundreds of historical trades across multiple assets (BTC, ETH, SOL, BNB, XRP)
in seconds, generates 100+ sample trade histories, and feeds them into the self_improve engine.
"""

import argparse
import json
import math
import os
import re
import ssl
import sys
import urllib.request
from datetime import datetime, timedelta

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
GENOME_FILE = os.path.join(DATA_DIR, "agent_genome.json")

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}

ASSETS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]

def get_default_user():
    if os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("ACTIVE_USER="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass
    return "dxmade@gmail.com"

def fetch_klines(symbol="BTCUSDT", interval="1h", limit=1000):
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=12, context=SSL_CTX) as resp:
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
        print(f"[Warning] Failed to fetch klines for {symbol}: {e}", file=sys.stderr)
        return []

def calculate_ema(values, period):
    if not values:
        return []
    k = 2 / (period + 1)
    ema_list = [values[0]]
    for val in values[1:]:
        ema_list.append((val * k) + (ema_list[-1] * (1 - k)))
    return ema_list

def simulate_asset_trades(symbol, candles, min_rr=2.25, risk_pct=1.5, fee_pct=0.05):
    if len(candles) < 50:
        return []

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    ema20 = calculate_ema(closes, 20)
    ema50 = calculate_ema(closes, 50)

    trades = []
    active = None
    capital = 10000.0

    for i in range(50, len(candles)):
        c = candles[i]
        curr_price = c["close"]

        # Check Active Trade
        if active:
            hit_sl = False
            hit_tp = False

            # Trailing BE Trigger
            if active["side"] == "LONG":
                if not active.get("be_moved") and c["high"] >= active["entry"] + active["risk_dist"]:
                    active["sl"] = active["entry"]
                    active["be_moved"] = True
                if c["low"] <= active["sl"]:
                    hit_sl = True
                elif c["high"] >= active["tp"]:
                    hit_tp = True
            else:
                if not active.get("be_moved") and c["low"] <= active["entry"] - active["risk_dist"]:
                    active["sl"] = active["entry"]
                    active["be_moved"] = True
                if c["high"] >= active["sl"]:
                    hit_sl = True
                elif c["low"] <= active["tp"]:
                    hit_tp = True

            if hit_sl or hit_tp:
                exit_price = active["sl"] if hit_sl else active["tp"]
                if active["side"] == "LONG":
                    gross = (exit_price - active["entry"]) * active["units"]
                else:
                    gross = (active["entry"] - exit_price) * active["units"]

                fee = (active["amount_usd"] * 2) * (fee_pct / 100.0)
                net = gross - fee
                capital += net

                trade_time = datetime.fromtimestamp(c["time"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
                trades.append({
                    "id": f"FLIGHT-{symbol}-{len(trades)+1}",
                    "symbol": f"{symbol.replace('USDT', '')}-USDT",
                    "side": active["side"],
                    "entry_price": active["entry"],
                    "exit_price": exit_price,
                    "amount_usd": active["amount_usd"],
                    "pnl_usd": round(net, 2),
                    "pnl_pct": round((net / active["amount_usd"]) * 100, 2),
                    "reason": "HIT_SL" if hit_sl else "HIT_TP",
                    "closed_at": trade_time
                })
                active = None
                continue

        # Strategy Trigger: SMC Fair Value Gap (FVG)
        signal = None
        # Bullish FVG
        if lows[i] > highs[i - 2] and curr_price > ema20[i] > ema50[i]:
            sl = lows[i - 2] * 0.995
            dist = curr_price - sl
            if dist > 0:
                signal = {"side": "LONG", "sl": sl, "tp": curr_price + (dist * min_rr), "risk_dist": dist}
        # Bearish FVG
        elif highs[i] < lows[i - 2] and curr_price < ema20[i] < ema50[i]:
            sl = highs[i - 2] * 1.005
            dist = sl - curr_price
            if dist > 0:
                signal = {"side": "SHORT", "sl": sl, "tp": curr_price - (dist * min_rr), "risk_dist": dist}

        if signal:
            sl_pct = abs(curr_price - signal["sl"]) / curr_price
            budget = capital * (risk_pct / 100.0)
            amount_usd = min(budget / max(sl_pct, 0.005), capital * 2.0)
            units = amount_usd / curr_price

            active = {
                "side": signal["side"],
                "entry": curr_price,
                "sl": signal["sl"],
                "tp": signal["tp"],
                "risk_dist": signal["risk_dist"],
                "amount_usd": round(amount_usd, 2),
                "units": units
            }

    return trades

def run_flight_simulator(target_samples=100, user_email=None):
    user = user_email.strip().lower() if user_email else get_default_user().lower()
    clean_name = re.sub(r"[^a-z0-9]", "_", user)
    portfolio_file = os.path.join(DATA_DIR, f"paper_portfolio_{clean_name}.json")
    general_portfolio = os.path.join(DATA_DIR, "paper_portfolio.json")

    print("\n" + "=" * 68)
    print(f"       🚀 QUANTITATIVE FLIGHT SIMULATOR (100+ TRADES)")
    print(f"       👤 Akun    : {user}")
    print(f"       🌐 Aset    : {', '.join(ASSETS)}")
    print(f"       🎯 Target  : Minimal {target_samples} Sampel Transaksi Institusional")
    print("=" * 68)

    all_simulated_trades = []
    total_candles = 0

    for sym in ASSETS:
        print(f"Mengunduh 1,000 candle 1H untuk {sym} dari Binance Vision...")
        candles = fetch_klines(sym, interval="1h", limit=1000)
        total_candles += len(candles)
        if candles:
            asset_trades = simulate_asset_trades(sym, candles)
            all_simulated_trades.extend(asset_trades)
            print(f" -> Berhasil mensimulasikan {len(asset_trades)} trade dari {sym}.")

    # Sort all trades chronologically
    all_simulated_trades.sort(key=lambda x: x["closed_at"])

    # Aggregate Statistics
    total_trades = len(all_simulated_trades)
    wins = [t for t in all_simulated_trades if t["pnl_usd"] > 0]
    losses = [t for t in all_simulated_trades if t["pnl_usd"] <= 0]
    win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0
    total_win_pnl = sum(t["pnl_usd"] for t in wins)
    total_loss_pnl = abs(sum(t["pnl_usd"] for t in losses))
    net_pnl = total_win_pnl - total_loss_pnl
    profit_factor = (total_win_pnl / total_loss_pnl) if total_loss_pnl > 0 else 0

    print("\n" + "=" * 68)
    print("       📊 HASIL FLIGHT SIMULATOR TERKUMPUL")
    print("=" * 68)
    print(f"Total Jam Pasar Diuji : {total_candles:,} Jam Candle")
    print(f"Total Sampel Trade    : {total_trades} Transaksi Selesai ✅")
    print(f"Hasil Eksekusi        : {len(wins)} Menang (TP) / {len(losses)} Kalah (SL)")
    print(f"Win Rate Kumulatif    : {win_rate:.1f}%")
    print(f"Profit Factor (PF)    : {profit_factor:.2f}")
    print(f"Net Profit Simulasi   : {'+' if net_pnl>=0 else ''}${net_pnl:,.2f}")
    print("=" * 68)

    # Save to user paper portfolio and general portfolio
    for path in [portfolio_file, general_portfolio]:
        current_data = {"cash_balance": 10000.0, "positions": [], "trade_history": []}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    current_data = json.load(f)
            except Exception:
                pass

        current_data["trade_history"].extend(all_simulated_trades)
        current_data["cash_balance"] = round(current_data["cash_balance"] + net_pnl, 2)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(current_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Berhasil menyuntikkan {total_trades} riwayat transaksi ke database log!")
    print(f"File Target: {portfolio_file}")
    print("-----------------------------------------------------------------")
    print("💡 Sekarang Anda dapat menjalankan 'self_improve.py evolve' untuk")
    print("   melihat AI bermutasi secara otomatis berdasarkan 100+ sampel ini!")
    print("=" * 68 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Quantitative Flight Simulator")
    parser.add_argument("--samples", type=int, default=100, help="Target jumlah sampel trade")
    parser.add_argument("--user", type=str, default=None, help="Email akun")
    args = parser.parse_args()

    run_flight_simulator(target_samples=args.samples, user_email=args.user)

if __name__ == "__main__":
    main()

"""
Tokocrypto Autonomous Spot AI Trading Desk Engine
Synthesized with Akademi Crypto SMC (Smart Money Concepts), FVG, Wyckoff, and Strict Risk Rules.
Specialized for Long-Only Spot Accumulation & Dynamic Deposit-Scaling.
"""

import argparse
import json
import os
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
GENOME_FILE = os.path.join(DATA_DIR, "agent_genome.json")
AUTOPILOT_HISTORY_FILE = os.path.join(DATA_DIR, "tokocrypto_autopilot_history.json")
DASHBOARD_FEED_FILE = os.path.join(DATA_DIR, "dashboard_feed.json")

# Import sibling modules
sys.path.insert(0, TOOLS_DIR)
import tokocrypto_client
import market_eyes
import market_regime

# Top liquid assets with active Tokocrypto Spot pairs
DEFAULT_WATCHLIST = ["BTC", "ETH", "SOL", "XRP", "SUI", "SEI", "DOGE", "ADA", "AVAX"]

# Minimum trade value on Tokocrypto/Binance Cloud is ~10 USDT
MIN_ORDER_USDT = 5.0

def load_genome():
    if os.path.exists(GENOME_FILE):
        try:
            with open(GENOME_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "generation": 4,
        "parameters": {
            "min_risk_reward": 2.0,
            "max_risk_per_trade_pct": 2.5,
            "rsi_overbought": 70,
            "rsi_oversold": 35
        },
        "regime_genomes": {
            "TRENDING": {"min_risk_reward": 3.0, "tp_pct": 0.05},
            "RANGING": {"min_risk_reward": 2.0, "tp_pct": 0.03},
            "DEFENSIVE": {"allow_entry": False}
        }
    }

def log_autopilot_activity(entry):
    os.makedirs(DATA_DIR, exist_ok=True)
    history = []
    if os.path.exists(AUTOPILOT_HISTORY_FILE):
        try:
            with open(AUTOPILOT_HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    history.append(entry)
    # Keep last 100 entries to prevent infinite growth
    if len(history) > 100:
        history = history[-100:]

    with open(AUTOPILOT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def export_feed(user_email, free_usdt, total_equity_usd, active_orders, holdings, genome):
    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_email": user_email or "dxmade@gmail.com",
        "exchange": "Tokocrypto Spot",
        "balance_usd": total_equity_usd,
        "free_usdt": free_usdt,
        "generation": genome.get("generation", 4),
        "holdings": holdings,
        "open_orders": [
            {
                "id": o.get("id"),
                "symbol": o.get("symbol"),
                "side": o.get("side"),
                "price": o.get("price"),
                "amount": o.get("amount"),
                "status": o.get("status")
            }
            for o in active_orders
        ]
    }
    try:
        with open(DASHBOARD_FEED_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def fetch_tokocrypto_account(user_email=None):
    exchange, target_user = tokocrypto_client.get_exchange(user_email)
    if not exchange:
        return None, target_user, 0.0, 0.0, {}, []

    try:
        balance = exchange.fetch_balance()
        non_zero = {}
        free_usdt = float(balance.get("USDT", {}).get("free", 0) or 0)
        free_idr = float(balance.get("IDR", {}).get("free", 0) or 0)

        for coin, amt in balance.get("total", {}).items():
            if amt and float(amt) > 0:
                non_zero[coin] = {
                    "free": float(balance.get(coin, {}).get("free", 0) or 0),
                    "locked": float(balance.get(coin, {}).get("used", 0) or 0),
                    "total": float(amt)
                }

        # Fetch open orders efficiently (only for coins that have locked balance)
        open_orders = []
        locked_coins = [c for c, v in non_zero.items() if v.get("locked", 0) > 0 and c not in ["USDT", "IDR", "BIDR"]]
        for coin in locked_coins:
            sym = f"{coin}/USDT"
            try:
                orders = exchange.fetch_open_orders(sym)
                if orders:
                    open_orders.extend(orders)
            except Exception:
                pass

        # Calculate approximate total equity in USD
        total_equity_usd = free_usdt + (free_idr / 16000.0)
        for coin, vals in non_zero.items():
            if coin in ["USDT", "IDR", "BIDR"]:
                continue
            amt = vals["total"]
            # Estimate price
            try:
                p_data = market_eyes.get_market_eyes(coin, bar="1H")
                if p_data and p_data.get("price"):
                    total_equity_usd += amt * float(p_data["price"])
            except Exception:
                pass

        return exchange, target_user, free_usdt, total_equity_usd, non_zero, open_orders

    except Exception as e:
        print(f"[Error] Gagal mengakses API Tokocrypto: {e}")
        return None, target_user, 0.0, 0.0, {}, []

def run_autopilot_cycle(user_email=None, max_positions=3, watchlist=None):
    genome = load_genome()
    params = genome.get("parameters", {})
    min_rr = params.get("min_risk_reward", 2.0)
    symbols = watchlist if watchlist else DEFAULT_WATCHLIST

    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("\n" + "=" * 70)
    print(f"       🇮🇩 TOKOCRYPTO AUTONOMOUS AI SPOT TRADING DESK")
    print(f"       📅 Waktu         : {timestamp_str}")
    print(f"       🧬 Genome Brain  : Generation {genome.get('generation', 4)} (Multi-Regime Adaptive)")
    print(f"       🌐 Watchlist     : {len(symbols)} Aset Spot ({', '.join(symbols)})")
    print("=" * 70)

    # 1. Audit Saldo & Order Aktif
    exchange, target_user, free_usdt, total_equity_usd, holdings, open_orders = fetch_tokocrypto_account(user_email)
    if not exchange:
        print("Koneksi exchange gagal. Memeriksa kembali kredensial .env...")
        return

    print(f"\n[1. AUDIT SALDO & DETEKSI MODAL]")
    print(f" * Akun Pengguna        : {target_user}")
    print(f" * Saldo Kas Siap Belanja: ${free_usdt:,.4f} USDT")
    print(f" * Estimasi Nilai Ekuitas: ${total_equity_usd:,.2f} USD")
    print(f" * Aset Saat Ini        :")
    for coin, val in holdings.items():
        if val["total"] > 0.0001:
            lock_str = f" (Terkunci Order: {val['locked']:,.4f})" if val['locked'] > 0 else ""
            print(f"   - {coin:<6}: Free {val['free']:,.4f} | Total {val['total']:,.4f}{lock_str}")

    print(f" * Order Aktif di Bursa : {len(open_orders)} order")
    for o in open_orders:
        print(f"   -> [ID: {o.get('id')}] {o.get('side', '').upper()} {o.get('symbol')} @ ${float(o.get('price', 0)):,.4f} | Qty: {o.get('amount')}")

    export_feed(target_user, free_usdt, total_equity_usd, open_orders, holdings, genome)

    # 2. Market Regime Filter (Check BTC Market Health)
    print(f"\n[2. FILTER REZIM PASAR GLOBAL]")
    btc_reg = market_regime.detect_market_regime("BTC", interval="1h")
    btc_regime = btc_reg["regime"] if btc_reg else "UNKNOWN"
    btc_label = btc_reg["regime_label"] if btc_reg else "UNKNOWN"
    btc_adx = btc_reg["adx"] if btc_reg else 0.0
    print(f" * Rezim Induk BTC      : {btc_label} (ADX: {btc_adx})")

    if btc_regime in ["DEFENSIVE", "VOLATILITY_SQUEEZE"]:
        print(f" ⚠️ [Proteksi Modal Aktif] Bitcoin dalam kondisi fluktuasi tajam / squeeze ({btc_regime}).")
        print(f"    Sesuai modul Akademi Crypto: Bot menahan pembukaan posisi baru untuk menghindari pisau jatuh.")
        log_autopilot_activity({
            "timestamp": timestamp_str,
            "action": "STANDBY_PROTECT_CAPITAL",
            "reason": f"BTC regime: {btc_label}",
            "free_usdt": free_usdt
        })
        print("=" * 70 + "\n")
        return

    # Check available purchasing power
    # In Tokocrypto Spot, minimum order is around 5.0 - 10.0 USDT
    if free_usdt < MIN_ORDER_USDT:
        print(f"\n[3. STATUS MODAL BELANJA]")
        print(f" * Saldo USDT bebas (${free_usdt:,.4f}) berada di bawah minimum order (${MIN_ORDER_USDT} USDT).")
        print(f" * Bot sedang memantau order aktif (Take Profit) atau menunggu deposit baru dari pengguna.")
        print(f" * Setiap kali ada deposit baru masuk ke Tokocrypto, bot akan otomatis mengeksekusi sinyal berikutnya.")
        log_autopilot_activity({
            "timestamp": timestamp_str,
            "action": "STANDBY_WAITING_CAPITAL",
            "note": f"Free USDT ${free_usdt:.4f} < min ${MIN_ORDER_USDT}. Watching open orders.",
            "open_orders_count": len(open_orders)
        })
        print("=" * 70 + "\n")
        return

    # Check max open positions (exclude stablecoins)
    active_crypto_positions = [c for c in holdings.keys() if c not in ["USDT", "IDR", "BIDR"] and holdings[c]["total"] > 0.1]
    if len(active_crypto_positions) >= max_positions:
        print(f"\n[Guardrail Alert] Portofolio sudah memegang {len(active_crypto_positions)} koin aktif (maksimal {max_positions}).")
        print("Bot fokus mengawal Take Profit posisi yang sedang berjalan sebelum membeli koin baru.")
        print("=" * 70 + "\n")
        return

    # 3. Market Eyes Screening across Watchlist
    print(f"\n[3. INTELIJEN PASAR SMC — MEMINDAI DISKON / PULLBACK]")
    candidates = []

    for sym in symbols:
        # Skip if already holding this coin
        if sym in active_crypto_positions:
            print(f" - {sym}: Sudah ada di portofolio aset. Dilewati.")
            continue

        pair_sym = f"{sym}/USDT"
        data = market_eyes.get_market_eyes(sym, bar="1H")
        if not data or not data.get("price"):
            continue

        price = float(data["price"])
        rsi = float(data.get("rsi") or 50.0)
        fvg = data.get("fvg") or ""
        three_touch = data.get("three_touch")
        low_24h = float(data.get("low_24h") or (price * 0.96))
        high_24h = float(data.get("high_24h") or (price * 1.04))

        # Spot Buying Confluence:
        # 1. Patrick Nill 3-Touch Golden Support Rule
        # 2. RSI oversold or healthy pullback (RSI < 45)
        # 3. Bullish FVG or near 24h Support (within 35% of low)
        range_pct = ((price - low_24h) / (high_24h - low_24h)) * 100 if (high_24h > low_24h) else 50.0
        has_fvg = "Bullish FVG" in fvg
        is_3touch = bool(three_touch and three_touch.get("type") == "BULLISH_3_TOUCH")
        is_discount = is_3touch or range_pct <= 35.0 or rsi <= 40.0

        if is_discount:
            # Conservative Spot Take Profit: +2.8% to +4.5% target (higher TP if 3-touch confirmed)
            tp_pct = 0.045 if is_3touch else (0.035 if "TRENDING" in btc_regime else 0.028)
            tp_price = round(price * (1.0 + tp_pct), 5 if price < 1.0 else 2)
            dist_support = max(price - low_24h, price * 0.015)
            rr = (tp_price - price) / dist_support if dist_support > 0 else 2.0

            reasons = []
            if is_3touch:
                reasons.append("🌟 3-TOUCH GOLDEN SUPPORT")
            reasons.append(f"RSI {rsi:.1f} ({'Oversold' if rsi<=30 else 'Diskon'})")
            reasons.append(f"{range_pct:.1f}% dr Low")
            if has_fvg:
                reasons.append("FVG")

            candidates.append({
                "base": sym,
                "symbol": pair_sym,
                "price": price,
                "rsi": rsi,
                "range_pct": range_pct,
                "is_3touch": is_3touch,
                "tp_price": tp_price,
                "tp_pct": tp_pct * 100.0,
                "rr": rr,
                "reason": " + ".join(reasons)
            })
            tag = "🌟 [3-TOUCH KANDIDAT]" if is_3touch else "🟢 [KANDIDAT]"
            print(f"   {tag} {sym:<5} | Harga: ${price:<9.4f} | RSI: {rsi:<4.1f} | Posisi: {range_pct:.1f}% dr Low | Target TP: +{tp_pct*100:.1f}% (${tp_price})")

    # 4. Decision & Trade Execution
    print(f"\n[4. KEPUTUSAN EKSEKUSI SPOT TOKOCRYPTO]")
    if not candidates:
        print("Tidak ada koin di watchlist yang berada dalam zona diskon/support terkonfirmasi.")
        print("Bot standby menjaga modal kas.")
        log_autopilot_activity({
            "timestamp": timestamp_str,
            "action": "STANDBY_NO_CONFLUENCE",
            "free_usdt": free_usdt
        })
    else:
        # Prioritize 3-Touch setups first, then deepest discount
        candidates.sort(key=lambda x: (not x.get("is_3touch", False), x["range_pct"]))
        best = candidates[0]

        print(f"🎯 Koin Terpilih: BELI {best['symbol']}")
        print(f" * Alasan Setup: {best['reason']}")
        print(f" * Harga Pasar : ${best['price']:,.4f}")
        print(f" * Target TP   : ${best['tp_price']:,.4f} (+{best['tp_pct']:.1f}%)")

        # Position Sizing: Allocate 33% to 50% of free cash, minimum MIN_ORDER_USDT
        alloc_usd = min(free_usdt, max(MIN_ORDER_USDT, free_usdt * 0.40))
        raw_qty = alloc_usd / best["price"]

        # Precision handling for Spot lots
        if best["base"] in ["BTC"]:
            qty = round(raw_qty, 4)
        elif best["base"] in ["ETH"]:
            qty = round(raw_qty, 3)
        elif best["base"] in ["SOL", "BNB", "AVAX"]:
            qty = round(raw_qty, 2)
        elif best["base"] in ["XRP", "SUI", "SEI", "ADA"]:
            qty = round(raw_qty, 1)
        else:
            qty = round(raw_qty, 0)

        actual_cost = qty * best["price"]
        print(f" * Ukuran Order: {qty} {best['base']} (~${actual_cost:,.2f} USDT)")

        # Execute Market/Limit Buy
        print(f"\n[Mengirimkan Order Beli Spot ke Tokocrypto...]")
        try:
            buy_order = exchange.create_order(
                symbol=best["symbol"],
                type="MARKET",
                side="buy",
                amount=qty
            )
            print(f"✅ ORDER BELI BERHASIL! Order ID: {buy_order.get('id')}")

            # Immediately place Auto Take-Profit Sell Limit Order
            time.sleep(2)  # Wait 2 seconds for balance settlement
            print(f"\n[Menitipkan Order Otomatis Take-Profit (Sell Limit)...]")
            sell_tp = exchange.create_order(
                symbol=best["symbol"],
                type="LIMIT",
                side="sell",
                amount=qty,
                price=best["tp_price"]
            )
            print(f"✅ AUTO TAKE-PROFIT TERCATAT DI TOKOCRYPTO!")
            print(f" * TP Order ID: {sell_tp.get('id')}")
            print(f" * Harga Jual : ${best['tp_price']} (+{best['tp_pct']:.1f}%)")

            log_autopilot_activity({
                "timestamp": timestamp_str,
                "action": "EXECUTE_SPOT_BUY_AND_TP",
                "coin": best["base"],
                "buy_order_id": buy_order.get("id"),
                "tp_order_id": sell_tp.get("id"),
                "qty": qty,
                "entry_price": best["price"],
                "tp_price": best["tp_price"]
            })

        except Exception as e:
            print(f"❌ Eksekusi order gagal: {e}")

    print("=" * 70 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Tokocrypto Autonomous AI Spot Trading Desk")
    sub = parser.add_subparsers(dest="command")

    # Run command
    run_p = sub.add_parser("run", help="Jalankan autopilot pemindaian & trading mandiri")
    run_p.add_argument("--once", action="store_true", help="Jalankan 1 siklus pemindaian lalu selesai")
    run_p.add_argument("--interval", type=int, default=15, help="Interval siklus pemindaian dalam menit (default: 15)")
    run_p.add_argument("--user", type=str, default=None, help="Email akun Tokocrypto")
    run_p.add_argument("--watchlist", type=str, default=None, help="Koin dipisah koma (misal: BTC,ETH,SOL,XRP,SUI,SEI)")

    # Status / Balance command
    stat_p = sub.add_parser("status", help="Lihat status portofolio dan antrean order")
    stat_p.add_argument("--user", type=str, default=None, help="Email akun Tokocrypto")

    bal_p = sub.add_parser("balance", help="Lihat saldo lengkap di Tokocrypto")
    bal_p.add_argument("--user", type=str, default=None, help="Email akun Tokocrypto")

    args = parser.parse_args()

    if args.command == "balance":
        tokocrypto_client.check_balance(args.user)
    elif args.command == "status":
        run_autopilot_cycle(args.user, watchlist=[])
    elif args.command == "run":
        syms = [s.strip().upper() for s in args.watchlist.split(",") if s.strip()] if getattr(args, "watchlist", None) else DEFAULT_WATCHLIST
        if args.once:
            run_autopilot_cycle(args.user, watchlist=syms)
        else:
            print("\n" + "=" * 70)
            print(f" 🚀 TOKOCRYPTO AUTOPILOT AI DAEMON DIAKTIFKAN")
            print(f" ⏱️ Interval Pemindaian: Setiap {args.interval} Menit")
            print(f" 💼 Akun Terhubung     : {args.user or 'dxmade@gmail.com'}")
            print(f" 🛡️ Mode Operasi       : Spot Accumulation & Deposit-Scaling (Long-Only)")
            print(f" Tekan Ctrl+C untuk menghentikan kapan saja.")
            print("=" * 70 + "\n")
            try:
                while True:
                    run_autopilot_cycle(args.user, watchlist=syms)
                    print(f"😴 Autopilot tidur sejenak selama {args.interval} menit... Memantau deposit & pergerakan harga.")
                    time.sleep(args.interval * 60)
            except KeyboardInterrupt:
                print("\nAutopilot dihentikan dengan aman oleh pengguna.")
    else:
        run_autopilot_cycle(None, watchlist=DEFAULT_WATCHLIST)

if __name__ == "__main__":
    main()

"""
Autonomous Multi-Agent Trading Desk (CEO Orchestrator)
Inspired by DaviddTech / Lewis Jackson Multi-Agent AI Trading Desk.
Synthesized with Akademi Crypto SMC (Smart Money Concepts), FVG, and Strict Risk Rules.
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
DESK_HISTORY_FILE = os.path.join(DATA_DIR, "trading_desk_history.json")
DASHBOARD_FEED_FILE = os.path.join(DATA_DIR, "dashboard_feed.json")

# Import sibling modules
sys.path.insert(0, TOOLS_DIR)
import market_eyes
import market_regime
import binance_client

# Top 10 High-Liquidity Crypto Assets on Binance Futures
DEFAULT_WATCHLIST = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "LINK", "SUI"]

def load_genome():
    if os.path.exists(GENOME_FILE):
        try:
            with open(GENOME_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "generation": 1,
        "parameters": {
            "min_risk_reward": 2.0,
            "max_risk_per_trade_pct": 1.5,
            "rsi_overbought": 70,
            "rsi_oversold": 30,
            "require_fvg_confluence": True
        }
    }

def log_desk_activity(entry):
    os.makedirs(DATA_DIR, exist_ok=True)
    history = []
    if os.path.exists(DESK_HISTORY_FILE):
        try:
            with open(DESK_HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    history.append(entry)
    with open(DESK_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def export_dashboard_feed(user_email, is_demo, balance_usd, active_positions, genome):
    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_email": user_email or "dxmade@gmail.com",
        "is_demo": is_demo,
        "balance_usd": balance_usd,
        "generation": genome.get("generation", 3),
        "min_rr": genome.get("parameters", {}).get("min_risk_reward", 2.5),
        "max_risk_pct": genome.get("parameters", {}).get("max_risk_per_trade_pct", 1.5),
        "positions": [
            {
                "symbol": p["symbol"],
                "side": "LONG" if float(p.get("positionAmt", 0)) > 0 else "SHORT",
                "quantity": abs(float(p.get("positionAmt", 0))),
                "entry_price": float(p.get("entryPrice", 0)),
                "mark_price": float(p.get("markPrice", 0)),
                "pnl_usd": float(p.get("unRealizedProfit", 0)),
                "leverage": int(p.get("leverage", 5))
            }
            for p in active_positions
        ]
    }
    try:
        with open(DASHBOARD_FEED_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def get_active_positions(user_email=None, is_demo=True):
    res = binance_client.send_signed_request("/fapi/v2/positionRisk", method="GET", is_demo=is_demo, user_email=user_email)
    if not res:
        return []
    return [p for p in res if float(p.get("positionAmt", 0)) != 0]

def get_account_balance(user_email=None, is_demo=True):
    res = binance_client.send_signed_request("/fapi/v2/balance", method="GET", is_demo=is_demo, user_email=user_email)
    if not res:
        return 1000.0  # Fallback assumption
    for b in res:
        if b.get("asset") == "USDT":
            return float(b.get("balance", 0))
    return 1000.0

def run_trading_desk_cycle(user_email=None, is_demo=True, max_open_positions=3, symbols=None):
    genome = load_genome()
    params = genome.get("parameters", {})
    min_rr = params.get("min_risk_reward", 2.0)
    max_risk_pct = params.get("max_risk_per_trade_pct", 1.5)
    target_user, _, _, _, mode_label, _ = binance_client.resolve_credentials(user_email, is_demo)

    active_watchlist = symbols if symbols else DEFAULT_WATCHLIST

    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "=" * 68)
    print(f"       🤖 AUTONOMOUS AI TRADING DESK — CYCLE RUN")
    print(f"       📅 Waktu      : {timestamp_str}")
    print(f"       👤 Akun       : {target_user}")
    print(f"       🕹️ Mode       : {mode_label}")
    print(f"       🌐 Watchlist  : {len(active_watchlist)} Aset ({', '.join(active_watchlist)})")
    print(f"       🧬 Genome     : Gen {genome.get('generation', 1)} (Min R:R >= {min_rr}, Max Risk: {max_risk_pct}%)")
    print("=" * 68)

    # 1. Check Account Equity & Active Positions Guardrail
    balance_usd = get_account_balance(user_email, is_demo)
    active_positions = get_active_positions(user_email, is_demo)
    active_symbols = [p["symbol"] for p in active_positions]

    print(f"\n[1. RISK OFFICER AUDIT]")
    print(f" * Saldo Dompet Futures : ${balance_usd:,.2f} USDT")
    print(f" * Posisi Aktif Saat Ini: {len(active_positions)} / {max_open_positions} max")
    export_dashboard_feed(target_user, is_demo, balance_usd, active_positions, genome)

    for p in active_positions:
        amt = float(p["positionAmt"])
        side = "LONG 🟢" if amt > 0 else "SHORT 🔴"
        upnl = float(p.get("unRealizedProfit", 0))
        be_tag = " | 🛡️ [PROTEKSI BREAKEVEN AKTIF]" if upnl > 15.0 else ""
        print(f"   -> [{p['symbol']}] {side} | Mark: ${float(p['markPrice']):,.4f} | PnL: {'+' if upnl>=0 else ''}${upnl:,.2f}{be_tag}")

    if len(active_positions) >= max_open_positions:
        print(f"\n[Guardrail Alert] Batas maksimal posisi ({max_open_positions}) tercapai. Melewatkan pembukaan posisi baru untuk menjaga margin.")
        return

    # 2. Researcher Agent: Scanning Watchlist
    print(f"\n[2. MARKET RESEARCHER AGENT — SCANNING WATCHLIST ({len(active_watchlist)} PAIRS)]")
    candidates = []

    for sym in active_watchlist:
        pair_sym = f"{sym}USDT"
        if pair_sym in active_symbols:
            print(f" - {pair_sym}: Sudah ada posisi aktif yang sedang berjalan. Dilewati.")
            continue

        data = market_eyes.get_market_eyes(sym, bar="1H")
        if not data or not data.get("price"):
            continue

        # Detect Market Regime first
        reg = market_regime.detect_market_regime(sym, interval="1h")
        reg_name = reg["regime"] if reg else "UNKNOWN"
        reg_label = reg["regime_label"] if reg else "UNKNOWN"
        adx_val = reg["adx"] if reg else 0.0

        price = data["price"]
        rsi = data.get("rsi") or 50.0
        ema20 = data.get("ema20")
        ema50 = data.get("ema50")
        fvg = data.get("fvg") or ""
        funding = data.get("funding_rate") or 0.0

        print(f"   🧭 Rezim Pasar: {reg_label} (ADX: {adx_val})")

        # Guardrail: Skip if market is in low-liquidity volatility squeeze
        if reg_name == "VOLATILITY_SQUEEZE":
            print(f"   [Peringatan] Volatilitas squeeze terdeteksi. Menghindari entry prematur.")
            continue

        # Select Specialized Sub-Genome
        reg_genomes = genome.get("regime_genomes", {})
        if "TRENDING" in reg_name:
            sub_gen = reg_genomes.get("TRENDING", {})
        elif "RANGING" in reg_name or "DEVELOPING" in reg_name or "MIXED" in reg_name:
            sub_gen = reg_genomes.get("RANGING", {})
        else:
            sub_gen = reg_genomes.get("DEFENSIVE", {})

        effective_min_rr = sub_gen.get("min_risk_reward", min_rr)
        effective_max_risk = sub_gen.get("max_risk_per_trade_pct", max_risk_pct)
        sub_label = sub_gen.get("label", "STANDARD ENGINE")
        print(f"   🧬 Sub-Genome Aktif: {sub_label} | Min R:R: 1:{effective_min_rr:.2f}")

        # Confluence Rules
        three_touch = data.get("three_touch")
        volume_profile = data.get("volume_profile")
        va_setup = volume_profile.get("setup") if volume_profile else None

        # Rule A: Bullish Setup (Bullish FVG, Patrick Nill 3-Touch, or Fabio Valentini Failed Auction)
        has_bullish_fvg = "Bullish FVG" in fvg
        has_bullish_3touch = bool(three_touch and three_touch.get("type") == "BULLISH_3_TOUCH")
        has_bullish_auction = bool(va_setup and va_setup.get("type") == "BULLISH_FAILED_AUCTION")
        rsi_safe_long = rsi < sub_gen.get("rsi_overbought", 70) and rsi > sub_gen.get("rsi_oversold", 30)

        # Rule B: Bearish Setup (Bearish FVG, Patrick Nill 3-Touch, or Fabio Valentini Failed Auction)
        has_bearish_fvg = "Bearish FVG" in fvg
        has_bearish_3touch = bool(three_touch and three_touch.get("type") == "BEARISH_3_TOUCH")
        has_bearish_auction = bool(va_setup and va_setup.get("type") == "BEARISH_FAILED_AUCTION")
        rsi_safe_short = rsi > sub_gen.get("rsi_oversold", 30) and rsi < sub_gen.get("rsi_overbought", 70)

        signal = None
        if (has_bullish_fvg or has_bullish_3touch or has_bullish_auction) and rsi_safe_long:
            # Plan Long
            if has_bullish_auction and va_setup:
                sl = va_setup["sl"]
                reason_tag = f"🔥 FABIO AUCTION (VAL ${volume_profile['val']} -> POC ${volume_profile['poc']})"
            elif has_bullish_3touch and three_touch:
                sl = round(three_touch["level"] * 0.995, 4)
                reason_tag = f"🌟 3-TOUCH SUPPORT (${three_touch['level']})"
            else:
                low_24h = data.get("low_24h") or (price * 0.98)
                sl = round(low_24h * 0.998, 4)
                reason_tag = "Bullish FVG"

            dist_sl = price - sl
            if dist_sl > 0:
                target_rr = max(effective_min_rr, 3.5 if (has_bullish_3touch or has_bullish_auction) else effective_min_rr)
                tp = round(price + (dist_sl * target_rr), 4)
                rr = (tp - price) / dist_sl
                signal = {
                    "symbol": pair_sym,
                    "base": sym,
                    "side": "LONG",
                    "price": price,
                    "sl": sl,
                    "tp": tp,
                    "rr": rr,
                    "is_3touch": has_bullish_3touch,
                    "is_fabio": has_bullish_auction,
                    "sub_genome": sub_label,
                    "risk_pct": effective_max_risk,
                    "reason": f"{reason_tag} + RSI {rsi:.1f} + R:R 1:{rr:.2f} [{sub_label}]"
                }

        elif (has_bearish_fvg or has_bearish_3touch or has_bearish_auction) and rsi_safe_short:
            # Plan Short
            if has_bearish_auction and va_setup:
                sl = va_setup["sl"]
                reason_tag = f"🔥 FABIO AUCTION (VAH ${volume_profile['vah']} -> POC ${volume_profile['poc']})"
            elif has_bearish_3touch and three_touch:
                sl = round(three_touch["level"] * 1.005, 4)
                reason_tag = f"🌟 3-TOUCH RESISTANCE (${three_touch['level']})"
            else:
                high_24h = data.get("high_24h") or (price * 1.02)
                sl = round(high_24h * 1.002, 4)
                reason_tag = "Bearish FVG"

            dist_sl = sl - price
            if dist_sl > 0:
                target_rr = max(effective_min_rr, 3.5 if (has_bearish_3touch or has_bearish_auction) else effective_min_rr)
                tp = round(price - (dist_sl * target_rr), 4)
                rr = (price - tp) / dist_sl
                signal = {
                    "symbol": pair_sym,
                    "base": sym,
                    "side": "SHORT",
                    "price": price,
                    "sl": sl,
                    "tp": tp,
                    "rr": rr,
                    "is_3touch": has_bearish_3touch,
                    "is_fabio": has_bearish_auction,
                    "sub_genome": sub_label,
                    "risk_pct": effective_max_risk,
                    "reason": f"{reason_tag} + RSI {rsi:.1f} + R:R 1:{rr:.2f} [{sub_label}]"
                }

        if signal and signal["rr"] >= effective_min_rr:
            candidates.append(signal)

    # 3. Decision & Execution Desk
    print("\n[3. EXECUTION DESK DECISION]")
    if not candidates:
        print("Tidak ada setup baru yang memenuhi konfluensi ketat (FVG / 3-Touch / Fabio Auction + Min R:R + RSI).")
        print("Desk standby menunggu struktur pasar berikutnya.")
        log_desk_activity({
            "timestamp": timestamp_str,
            "action": "STANDBY_NO_CONFLUENCE",
            "balance": balance_usd,
            "positions_count": len(active_positions)
        })
    else:
        # Available slots
        slots_available = max_open_positions - len(active_positions)
        # Prioritize Elite setups (Fabio Valentini Auction & Patrick Nill 3-Touch) first, then highest R:R
        candidates.sort(key=lambda x: (1 if (x.get("is_fabio") or x.get("is_3touch")) else 0, x["rr"]), reverse=True)
        selected = candidates[:slots_available]

        print(f"🎯 Ditemukan {len(candidates)} setup potensial. Mengeksekusi {len(selected)} setup terbaik (Slot tersedia: {slots_available}):")

        for idx, best in enumerate(selected, 1):
            print(f"\n--- [{idx}/{len(selected)}] EKSEKUSI SETUP: {best['side']} {best['symbol']} ---")
            print(f" * Rationale  : {best['reason']}")
            print(f" * Entry Price: ${best['price']:,.4f}")
            print(f" * Stop Loss  : ${best['sl']:,.4f}")
            print(f" * Take Profit: ${best['tp']:,.4f}")
            print(f" * R:R Ratio  : 1 : {best['rr']:.2f}")

            # Calculate exact position size for 1.5% max risk
            risk_budget = balance_usd * (max_risk_pct / 100.0)
            sl_pct = abs(best["price"] - best["sl"]) / best["price"]
            pos_size_usd = risk_budget / max(sl_pct, 0.005)
            # Cap position size to 3x equity max
            pos_size_usd = min(pos_size_usd, balance_usd * 3.0)
            raw_qty = pos_size_usd / best["price"]
            if best["base"] in ["BTC"]:
                qty = max(0.001, round(raw_qty, 3))
            elif best["base"] in ["ETH"]:
                qty = max(0.01, round(raw_qty, 2))
            elif best["base"] in ["SOL", "BNB", "AVAX", "LINK", "APT"]:
                qty = max(0.1, round(raw_qty, 1))
            elif best["base"] in ["DOGE", "XRP", "ADA", "SUI", "NEAR"]:
                qty = max(1.0, round(raw_qty, 0))
            else:
                qty = max(0.1, round(raw_qty, 1))

            print(f" * Position Size Budget: ${pos_size_usd:,.2f} ({qty} {best['base']})")
            print(f" * Max Risk At SL      : ${risk_budget:,.2f} ({max_risk_pct}% modal)")

            # Execute via binance_client
            print(f"[Mengirimkan Order ke Binance Futures...]")
            binance_client.place_futures_order(
                symbol=best["symbol"],
                side=best["side"],
                quantity=qty,
                leverage=5,
                sl=best["sl"],
                tp=best["tp"],
                is_demo=is_demo,
                user_email=user_email
            )

            log_desk_activity({
                "timestamp": timestamp_str,
                "action": "EXECUTE_TRADE",
                "trade": best,
                "quantity": qty,
                "risk_budget_usd": risk_budget
            })
            time.sleep(1)

    print("=" * 65 + "\n")

def show_desk_status(user_email=None, is_demo=True):
    target_user, _, _, _, mode_label, _ = binance_client.resolve_credentials(user_email, is_demo)
    genome = load_genome()
    active_positions = get_active_positions(user_email, is_demo)
    balance_usd = get_account_balance(user_email, is_demo)

    print("\n=======================================================")
    print(f"       🖥️ TRADING DESK STATUS OVERVIEW")
    print(f"       👤 Akun: {target_user} | Mode: {mode_label}")
    print("=======================================================")
    print(f"Total Equity Balance : ${balance_usd:,.2f} USDT")
    print(f"Active Positions     : {len(active_positions)} open")
    for p in active_positions:
        amt = float(p["positionAmt"])
        side = "LONG 🟢" if amt > 0 else "SHORT 🔴"
        upnl = float(p.get("unRealizedProfit", 0))
        print(f" * [{p['symbol']}] {side} | Entry: ${float(p['entryPrice']):,.4f} | Mark: ${float(p['markPrice']):,.4f} | PnL: {'+' if upnl>=0 else ''}${upnl:,.2f}")

    print("-------------------------------------------------------")
    print(f"Desk Genetic Rules   : Generation {genome.get('generation', 1)}")
    print(f" * Min R:R Filter    : 1 : {genome.get('parameters', {}).get('min_risk_reward', 2.0)}")
    print(f" * Max Risk Per Trade: {genome.get('parameters', {}).get('max_risk_per_trade_pct', 1.5)}%")
    print("=======================================================\n")

def main():
    parser = argparse.ArgumentParser(description="Autonomous AI Trading Desk (CEO Orchestrator)")
    sub = parser.add_subparsers(dest="command")

    # Run command
    run_p = sub.add_parser("run", help="Jalankan siklus pemindaian dan eksekusi trading desk")
    run_p.add_argument("--once", action="store_true", help="Jalankan 1 siklus lalu selesai")
    run_p.add_argument("--symbols", type=str, default=None, help="Daftar koin dipisah koma (misal: BTC,ETH,SOL,BNB,DOGE)")
    run_p.add_argument("--interval", type=int, default=30, help="Interval menit jika berjalan berkelanjutan (default: 30)")
    run_p.add_argument("--user", type=str, default=None, help="Email akun (misal: dxmade@gmail.com)")
    run_p.add_argument("--live", action="store_true", help="Gunakan akun live riil (default: Demo Testnet)")

    # Status command
    stat_p = sub.add_parser("status", help="Lihat status trading desk dan ringkasan posisi")
    stat_p.add_argument("--user", type=str, default=None, help="Email akun")
    stat_p.add_argument("--live", action="store_true", help="Gunakan akun live riil (default: Demo Testnet)")

    args = parser.parse_args()
    is_demo = not getattr(args, "live", False)

    if args.command == "status":
        show_desk_status(args.user, is_demo)
    elif args.command == "run":
        syms = [s.strip().upper() for s in args.symbols.split(",") if s.strip()] if getattr(args, "symbols", None) else None
        if args.once:
            run_trading_desk_cycle(args.user, is_demo, symbols=syms)
        else:
            w_str = ", ".join(syms) if syms else ", ".join(DEFAULT_WATCHLIST)
            print(f"Memulai Autonomous Trading Desk Daemon (Watchlist: {w_str} | Interval: {args.interval} menit)... Tekan Ctrl+C untuk berhenti.")
            try:
                while True:
                    run_trading_desk_cycle(args.user, is_demo, symbols=syms)
                    print(f"Desk tidur sejenak selama {args.interval} menit...")
                    time.sleep(args.interval * 60)
            except KeyboardInterrupt:
                print("\nTrading Desk Daemon dihentikan oleh pengguna.")
    else:
        show_desk_status(None, is_demo=True)

if __name__ == "__main__":
    main()

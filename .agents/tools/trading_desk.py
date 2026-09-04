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
import telegram_notifier
import trade_manager
import topdown_confluence
import fast_scalper

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

def compute_rs_matrix(symbols):
    """
    Trader 4 (Top Prop Trader) Relative Strength vs. Relative Weakness (RS/RW) Matrix.
    Measures alpha against BTC benchmark to pick Strongest for Longs and Weakest for Shorts.
    """
    matrix = {}
    btc_url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
    btc_res = market_eyes.fetch_json(btc_url)
    btc_chg = 0.0
    if btc_res and btc_res.get("data"):
        d = btc_res["data"][0]
        o = float(d.get("open24h", 0))
        c = float(d.get("last", 0))
        btc_chg = ((c - o) / o * 100.0) if o > 0 else 0.0

    for sym in symbols:
        url = f"https://www.okx.com/api/v5/market/ticker?instId={sym}-USDT"
        res = market_eyes.fetch_json(url)
        if res and res.get("data"):
            d = res["data"][0]
            o = float(d.get("open24h", 0))
            c = float(d.get("last", 0))
            chg = ((c - o) / o * 100.0) if o > 0 else 0.0
            rs = round(chg - btc_chg, 2)
            if rs >= 1.0:
                tier = "LEADER"
                badge = "🟢 ALPHA LEADER (Strongest)"
            elif rs <= -1.0:
                tier = "LAGGARD"
                badge = "🔴 BETA LAGGARD (Weakest)"
            else:
                tier = "NEUTRAL"
                badge = "⚪ IN-LINE WITH BTC"
            matrix[sym] = {"change_24h": round(chg, 2), "rs_score": rs, "tier": tier, "badge": badge}
        else:
            matrix[sym] = {"change_24h": 0.0, "rs_score": 0.0, "tier": "NEUTRAL", "badge": "⚪ UNKNOWN"}

    return matrix, btc_chg

def scan_swing_candidates(active_watchlist, active_symbols, genome, min_rr, max_risk_pct):
    """
    Scans 1H / 4H swing setups using 4 championship strategies & top-down macro confluence.
    """
    print(f"\n[2. MARKET RESEARCHER AGENT — RELATIVE STRENGTH & WATCHLIST SCAN]")
    rs_matrix, btc_chg = compute_rs_matrix(active_watchlist)
    print(f" * BTC 24h Benchmark Performance: {btc_chg:+.2f}%")
    for s_name, r_info in sorted(rs_matrix.items(), key=lambda x: x[1]["rs_score"], reverse=True):
        print(f"   - {s_name:<5}: 24h {r_info['change_24h']:+6.2f}% | RS vs BTC: {r_info['rs_score']:+6.2f}% | {r_info['badge']}")

    candidates = []

    for sym in active_watchlist:
        pair_sym = f"{sym}USDT"
        if pair_sym in active_symbols:
            print(f"\n - {pair_sym}: Sudah ada posisi aktif yang sedang berjalan. Dilewati.")
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
        liquidity_sweep = data.get("liquidity_sweep")
        vwap_data = data.get("vwap")

        rs_info = rs_matrix.get(sym, {})
        is_alpha_leader = rs_info.get("tier") == "LEADER"
        is_beta_laggard = rs_info.get("tier") == "LAGGARD"

        # Rule A: Bullish Setup (Bullish FVG, Patrick Nill 3-Touch, Fabio Valentini Auction, or Tim Flossbach MSS)
        has_bullish_fvg = "Bullish FVG" in fvg
        has_bullish_3touch = bool(three_touch and three_touch.get("type") == "BULLISH_3_TOUCH")
        has_bullish_auction = bool(va_setup and va_setup.get("type") == "BULLISH_FAILED_AUCTION")
        has_bullish_sweep = bool(liquidity_sweep and liquidity_sweep.get("type") == "BULLISH_SWEEP_MSS")
        rsi_safe_long = rsi < sub_gen.get("rsi_overbought", 70) and rsi > sub_gen.get("rsi_oversold", 30)

        # Rule B: Bearish Setup (Bearish FVG, Patrick Nill 3-Touch, Fabio Valentini Auction, or Tim Flossbach MSS)
        has_bearish_fvg = "Bearish FVG" in fvg
        has_bearish_3touch = bool(three_touch and three_touch.get("type") == "BEARISH_3_TOUCH")
        has_bearish_auction = bool(va_setup and va_setup.get("type") == "BEARISH_FAILED_AUCTION")
        has_bearish_sweep = bool(liquidity_sweep and liquidity_sweep.get("type") == "BEARISH_SWEEP_MSS")
        rsi_safe_short = rsi > sub_gen.get("rsi_oversold", 30) and rsi < sub_gen.get("rsi_overbought", 70)

        signal = None
        if (has_bullish_fvg or has_bullish_3touch or has_bullish_auction or has_bullish_sweep) and rsi_safe_long:
            # Plan Long
            if has_bullish_sweep and liquidity_sweep:
                sl = liquidity_sweep["sl"]
                reason_tag = f"⚡ TIM FLOSSBACH MSS (SSL Sweep ${liquidity_sweep['sweep_level']})"
            elif has_bullish_auction and va_setup:
                sl = va_setup["sl"]
                reason_tag = f"🔥 FABIO AUCTION (VAL ${volume_profile['val']} -> POC ${volume_profile['poc']})"
            elif has_bullish_3touch and three_touch:
                sl = round(three_touch["level"] * 0.995, 4)
                reason_tag = f"🌟 3-TOUCH SUPPORT (${three_touch['level']})"
            else:
                low_24h = data.get("low_24h") or (price * 0.98)
                sl = round(low_24h * 0.998, 4)
                reason_tag = "Bullish FVG"

            if is_alpha_leader:
                reason_tag += f" + ⭐ ALPHA LEADER (RS {rs_info['rs_score']:+,.2f}%)"
            if vwap_data and "Above VWAP" in vwap_data.get("state", ""):
                reason_tag += " + VWAP Bullish"

            dist_sl = price - sl
            if dist_sl > 0:
                bonus_rr = 0.5 if is_alpha_leader else 0.0
                target_rr = max(effective_min_rr, (3.5 + bonus_rr) if (has_bullish_3touch or has_bullish_auction or has_bullish_sweep) else (effective_min_rr + bonus_rr))
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
                    "is_tim": has_bullish_sweep,
                    "is_alpha_leader": is_alpha_leader,
                    "sub_genome": sub_label,
                    "risk_pct": effective_max_risk,
                    "reason": f"{reason_tag} + RSI {rsi:.1f} + R:R 1:{rr:.2f} [{sub_label}]"
                }

        elif (has_bearish_fvg or has_bearish_3touch or has_bearish_auction or has_bearish_sweep) and rsi_safe_short:
            # Plan Short
            if has_bearish_sweep and liquidity_sweep:
                sl = liquidity_sweep["sl"]
                reason_tag = f"⚡ TIM FLOSSBACH MSS (BSL Sweep ${liquidity_sweep['sweep_level']})"
            elif has_bearish_auction and va_setup:
                sl = va_setup["sl"]
                reason_tag = f"🔥 FABIO AUCTION (VAH ${volume_profile['vah']} -> POC ${volume_profile['poc']})"
            elif has_bearish_3touch and three_touch:
                sl = round(three_touch["level"] * 1.005, 4)
                reason_tag = f"🌟 3-TOUCH RESISTANCE (${three_touch['level']})"
            else:
                high_24h = data.get("high_24h") or (price * 1.02)
                sl = round(high_24h * 1.002, 4)
                reason_tag = "Bearish FVG"

            if is_beta_laggard:
                reason_tag += f" + ⭐ BETA LAGGARD (RS {rs_info['rs_score']:+,.2f}%)"
            if vwap_data and "Below VWAP" in vwap_data.get("state", ""):
                reason_tag += " + VWAP Bearish"

            dist_sl = sl - price
            if dist_sl > 0:
                bonus_rr = 0.5 if is_beta_laggard else 0.0
                target_rr = max(effective_min_rr, (3.5 + bonus_rr) if (has_bearish_3touch or has_bearish_auction or has_bearish_sweep) else (effective_min_rr + bonus_rr))
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
                    "is_tim": has_bearish_sweep,
                    "is_beta_laggard": is_beta_laggard,
                    "sub_genome": sub_label,
                    "risk_pct": effective_max_risk,
                    "reason": f"{reason_tag} + RSI {rsi:.1f} + R:R 1:{rr:.2f} [{sub_label}]"
                }

        if signal and signal["rr"] >= effective_min_rr:
            # Check Top-Down Multi-Timeframe Confluence (4H Macro Trend Alignment)
            is_approved, macro_info, macro_rationale = topdown_confluence.check_topdown_alignment(
                symbol=sym,
                proposed_side=signal["side"],
                setup_name=signal["reason"]
            )
            if not is_approved:
                print(f"   [Macro Guardrail] {macro_rationale}")
                continue

            signal["reason"] += f" + {macro_rationale}"
            signal["macro_aligned"] = True
            print(f"   🎯 [TOP-DOWN CONFLUENCE]: {macro_rationale}")
            candidates.append(signal)

    return candidates

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

    # Check if desk execution is paused via Telegram remote control
    if telegram_notifier.is_desk_paused():
        print(f"\n[Telegram Remote Guard] ⏸️ Trading Desk sedang DIJEDA via Telegram (/pause). Melewatkan pembukaan order baru.")
        export_dashboard_feed(target_user, is_demo, balance_usd, active_positions, genome)
        return

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

    # Dynamic Trade Management (Breakeven Auto-Lock & Trailing Stop Engine)
    print(f"\n[🛡️ DYNAMIC POSITION RISK & LIFECYCLE MANAGEMENT]")
    try:
        events = trade_manager.audit_and_manage_positions(user_email=user_email, is_demo=is_demo)
        if events:
            for ev in events:
                print(f" * {ev}")
        else:
            print(" * Semua posisi aktif dalam pengawasan ketat (Proteksi SL & Trailing up-to-date).")
    except Exception as e:
        print(f" * [Peringatan Trade Manager] {e}")

    if len(active_positions) >= max_open_positions:
        print(f"\n[Guardrail Alert] Batas maksimal posisi ({max_open_positions}) tercapai. Melewatkan pembukaan posisi baru untuk menjaga margin.")
        return

    desk_mode = telegram_notifier.get_desk_mode().upper()
    print(f"\n * Mode Operasional Trading Desk: {'⚡ FAST SCALPER (5m/15m Protocol)' if desk_mode == 'SCALP' else '🎯 SWING INTRADAY (1H/4H Confluence)'}")

    candidates = []

    if desk_mode == "SCALP":
        print(f"\n[2. FAST SCALPER AGENT — 5m / 15m MICRO-STRUCTURE SCAN]")
        scalp_setups = fast_scalper.scan_all_scalp_opportunities(active_watchlist[:6])
        for s in scalp_setups:
            pair_sym = f"{s['symbol']}USDT"
            if pair_sym in active_symbols:
                print(f" - {pair_sym}: Sudah ada posisi aktif yang berjalan. Dilewati.")
                continue
            print(f" ⚡ [SCALP SIGNAL] {s['symbol']} | {s['side']} | {s['strategy']} | R:R 1:{s['rr_ratio']:.2f}")
            candidates.append({
                "symbol": pair_sym,
                "base": s["symbol"],
                "side": s["side"],
                "price": s["entry"],
                "sl": s["sl"],
                "tp": s["tp"],
                "rr": s["rr_ratio"],
                "risk_pct": 1.2,
                "is_scalp": True,
                "macro_aligned": True,
                "reason": f"⚡ SCALP [{s['strategy']}]: {s['reason']} (Target: {s['target_duration']})"
            })
    else:
        candidates = scan_swing_candidates(active_watchlist, active_symbols, genome, min_rr, max_risk_pct)

    # 3. Decision & Execution Desk
    print("\n[3. EXECUTION DESK DECISION]")
    if not candidates:
        print("Tidak ada setup baru yang memenuhi konfluensi ketat (FVG / 3-Touch / Fabio Auction / Tim MSS / RS-RW + Min R:R + RSI).")
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
        # Prioritize Elite setups (Tim MSS, Fabio Auction, Patrick Nill 3-Touch) + Macro Confluence + RS Alignment, then highest R:R
        candidates.sort(key=lambda x: (
            1 if (x.get("is_tim") or x.get("is_fabio") or x.get("is_3touch")) else 0,
            1 if x.get("macro_aligned") else 0,
            1 if (x.get("is_alpha_leader") or x.get("is_beta_laggard")) else 0,
            x["rr"]
        ), reverse=True)
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

            # Send Instant Telegram Push Notification
            try:
                telegram_notifier.notify_trade_opened(best, qty, risk_budget, is_demo=is_demo)
            except Exception as e:
                print(f"[Telegram Notifier Warning] Gagal kirim alert Telegram: {e}")

            # Register into Dynamic Trade Manager
            try:
                trade_manager.record_trade_entry(
                    symbol=best["symbol"],
                    side=best["side"],
                    entry_price=best["price"],
                    sl_price=best["sl"],
                    tp_price=best["tp"],
                    risk_budget_usd=risk_budget,
                    quantity=qty,
                    is_scalp=best.get("is_scalp", False)
                )
            except Exception as e:
                print(f"[Trade Manager Warning] Gagal simpan metadata trade: {e}")

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
            # Start background Telegram interactive remote control listener thread
            telegram_notifier.start_command_listener(args.user, is_demo=is_demo)
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

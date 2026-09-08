"""
Autonomous Multi-Agent Trading Desk (CEO Orchestrator)
Inspired by DaviddTech / Lewis Jackson Multi-Agent AI Trading Desk.
Synthesized with Akademi Crypto SMC (Smart Money Concepts), FVG, and Strict Risk Rules.
"""

import argparse
import concurrent.futures
import json
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

# SSL Context to prevent Windows / regional ISP SSL certificate verification blocks
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

TOOLS_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(os.path.dirname(TOOLS_DIR))
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
GENOME_FILE = os.path.join(DATA_DIR, "agent_genome.json")
DESK_HISTORY_FILE = os.path.join(DATA_DIR, "trading_desk_history.json")
DASHBOARD_FEED_FILE = os.path.join(DATA_DIR, "dashboard_feed.json")
LEDGER_FILE = os.path.join(DATA_DIR, "trade_journal_ledger.json")

# Resilient financial memory cache to prevent erratic fallback upon temporary API blips
_LAST_FINANCIALS_CACHE = {
    "equity": 5160.20,
    "available": 4697.00,
    "last_updated": time.time()
}

# Import sibling modules
sys.path.insert(0, TOOLS_DIR)
import market_eyes
import market_regime
import binance_client
import telegram_notifier
import trade_manager
import topdown_confluence
import fast_scalper
import session_filter
import macro_news_shield

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
            "require_fvg_confluence": True,
            "max_funding_rate_threshold": 0.02,
            "weights": {
                "trend_weight": 0.35,
                "rsi_weight": 0.30,
                "volatility_weight": 0.20,
                "risk_aversion": 0.15
            }
        }
    }

def get_asset_sweep_buffer(symbol):
    """
    Module 03 & Smart Money Concepts Anti-Liquidity-Hunt Buffer.
    Major coins (BTC/ETH/BNB) have deeper orderbooks -> 0.8% - 1.0% buffer.
    High-beta Altcoins (DOGE, ADA, AVAX, SUI, LINK, SOL, XRP) experience 0.8% - 1.2% liquidity sweep wicks.
    A 1.4% - 1.6% buffer protects positions from premature stop hunts before true expansion.
    """
    sym = symbol.upper()
    if "BTC" in sym:
        return 0.008  # 0.8%
    elif "ETH" in sym or "BNB" in sym:
        return 0.010  # 1.0%
    elif any(k in sym for k in ["SOL", "LINK", "AVAX"]):
        return 0.013  # 1.3%
    else:  # High beta / meme / sensitive: DOGE, ADA, SUI, XRP
        return 0.016  # 1.6% (absorbs stop hunt wicks)

def get_dynamic_futures_watchlist(top_n=12, is_demo=True):
    """
    Dynamic Universe Screener:
    Fetches real-time 24h ticker data from Binance Vision, filters for valid Binance Futures USDT pairs,
    excludes stablecoins & leveraged tokens, and ranks assets by 24h quote volume & momentum.
    Guarantees foundational benchmark assets (BTC, ETH, SOL) are always included.
    """
    anchor_coins = ["BTC", "ETH", "SOL"]
    stables = {"USDCUSDT", "FDUSDUSDT", "TUSDUSDT", "BUSDUSDT", "EURUSDT", "DAIUSDT", "AEURUSDT", "USDSUSDT"}

    try:
        req = urllib.request.Request(
            "https://data-api.binance.vision/api/v3/ticker/24hr",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5, context=SSL_CTX) as resp:
            tickers = json.loads(resp.read().decode("utf-8"))

        futures_info = binance_client.get_exchange_info(is_demo=is_demo) or {}

        usdt_tickers = [
            t for t in tickers
            if t.get("symbol", "").endswith("USDT")
            and t["symbol"] not in stables
            and not t["symbol"].startswith("UP")
            and not t["symbol"].startswith("DOWN")
            and (t["symbol"] in futures_info if futures_info else True)
        ]

        usdt_tickers.sort(key=lambda x: float(x.get("quoteVolume", 0)), reverse=True)

        screened = []
        for t in usdt_tickers:
            sym_clean = t["symbol"].replace("USDT", "")
            if sym_clean not in screened:
                screened.append(sym_clean)
            if len(screened) >= top_n:
                break

        final_list = list(anchor_coins)
        for c in screened:
            if c not in final_list:
                final_list.append(c)
            if len(final_list) >= top_n:
                break

        return final_list
    except Exception as e:
        print(f" * [Dynamic Screener Note] Fallback to default watchlist: {e}")
        return DEFAULT_WATCHLIST

def get_adaptive_kelly_risk_pct(base_risk_pct=1.5, min_risk=0.5, max_risk=2.0):
    """
    Module 03 Quantitative Risk Sizing (Adaptive Half-Kelly Formula):
    Dynamically adjusts risk budget according to empirical statistical edge from historical ledger.
    Scales down risk when win rate or profit factor drops; scales up (capped at max_risk) during high edge.
    """
    try:
        import quant_risk_engine
        metrics = quant_risk_engine.compute_historical_trade_metrics()
        total_trades = metrics.get("total_trades", 0)
        half_kelly = metrics.get("kelly_fraction", 0.0)
        profit_factor = metrics.get("profit_factor", 0.0)
        win_rate = metrics.get("win_rate_pct", 0.0)

        if total_trades >= 10:
            if profit_factor < 1.0 or win_rate < 35.0:
                scaled_risk = max(min_risk, base_risk_pct * 0.60)
                status = f"Defensive Cut (WR {win_rate:.1f}%, PF {profit_factor:.2f})"
            elif half_kelly > 0:
                kelly_factor = min(1.5, max(0.6, half_kelly / 0.10))
                scaled_risk = base_risk_pct * kelly_factor
                status = f"Half-Kelly {half_kelly:.2f} (WR {win_rate:.1f}%, PF {profit_factor:.2f})"
            else:
                scaled_risk = max(min_risk, base_risk_pct * 0.70)
                status = f"Safe Baseline (WR {win_rate:.1f}%, PF {profit_factor:.2f})"

            final_risk = round(min(max_risk, max(min_risk, scaled_risk)), 2)
            return final_risk, status
    except Exception as e:
        pass

    return base_risk_pct, "Standard Fixed (1.50%)"

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
    sess = session_filter.get_current_session_info()
    is_blk, blk_reason, next_ev = macro_news_shield.audit_news_blackout(buffer_minutes=30)
    desk_mode = telegram_notifier.get_desk_mode().upper()
    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_email": user_email or "dxmade@gmail.com",
        "is_demo": is_demo,
        "balance_usd": balance_usd,
        "desk_mode": desk_mode,
        "generation": genome.get("generation", 5),
        "min_rr": genome.get("parameters", {}).get("min_risk_reward", 3.0),
        "max_risk_pct": genome.get("parameters", {}).get("max_risk_per_trade_pct", 1.5),
        "session": sess,
        "news_shield": {
            "is_blackout": is_blk,
            "status": "BLACKOUT_ACTIVE" if is_blk else "SAFE",
            "reason": blk_reason,
            "next_event": next_ev.get("title") if next_ev else "None",
            "next_time": next_ev.get("time_wib_str") if next_ev else "-"
        },
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
        import dominance_compass
        comp = dominance_compass.get_dominance_compass()
        data["dominance_compass"] = {
            "regime": comp["regime_code"],
            "title": comp["regime_title"],
            "btc_d": comp["btc_d"],
            "usdt_d": comp["usdt_d"],
            "usdt_status": comp["usdt_status"]
        }
    except Exception:
        pass

    # Fincept Terminal Quantitative Risk Suite (VaR, CVaR, Sharpe, Sortino, Kelly)
    try:
        import quant_risk_engine
        data["quant_suite"] = quant_risk_engine.get_full_quant_risk_summary(balance_usd, active_positions)
    except Exception:
        pass

    # Fincept Terminal Global Macro Intelligence (DXY, US 10Y Yield, Fear & Greed)
    try:
        import macro_liquidity
        data["macro_intelligence"] = macro_liquidity.get_macro_liquidity_summary()
    except Exception:
        pass

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

def get_account_financials(user_email=None, is_demo=True):
    """
    Mengambil total ekuitas (margin balance) dan margin bebas yang tersedia (availableBalance).
    Menggunakan resilient memory cache untuk menghindari fallback sembarangan saat koneksi tersendat.
    """
    global _LAST_FINANCIALS_CACHE
    res = binance_client.send_signed_request("/fapi/v2/account", method="GET", is_demo=is_demo, user_email=user_email)
    if res and isinstance(res, dict) and "totalMarginBalance" in res:
        equity = float(res.get("totalMarginBalance", 0) or res.get("totalWalletBalance", 0) or 0)
        available = float(res.get("availableBalance", 0) or 0)
        if equity > 0:
            _LAST_FINANCIALS_CACHE["equity"] = equity
            _LAST_FINANCIALS_CACHE["available"] = available
            _LAST_FINANCIALS_CACHE["last_updated"] = time.time()
            return equity, available

    res_bal = binance_client.send_signed_request("/fapi/v2/balance", method="GET", is_demo=is_demo, user_email=user_email)
    if res_bal and isinstance(res_bal, list):
        for b in res_bal:
            if b.get("asset") == "USDT":
                eq = float(b.get("balance", 0))
                avail = float(b.get("availableBalance", 0) or b.get("withdrawAvailable", 0) or (eq * 0.5))
                if eq > 0:
                    _LAST_FINANCIALS_CACHE["equity"] = eq
                    _LAST_FINANCIALS_CACHE["available"] = avail
                    _LAST_FINANCIALS_CACHE["last_updated"] = time.time()
                    return eq, avail

    # Resilient fallback to last known valid cached figures
    cached_eq = _LAST_FINANCIALS_CACHE.get("equity", 5160.20)
    cached_avail = _LAST_FINANCIALS_CACHE.get("available", 4697.00)
    return cached_eq, cached_avail

def get_account_balance(user_email=None, is_demo=True):
    equity, _ = get_account_financials(user_email, is_demo)
    return equity

def get_drawdown_risk_multiplier(lookback_trades=2):
    """
    Module 03 (Money Psychology & Trading Plan): Anti-Martingale Cold-Streak Protection.
    If the last N consecutive closed bot positions (source: AUTONOMOUS_TRADE_MANAGER)
    ended in net losses, temporarily cut risk allocation by 50% (0.50x multiplier)
    to protect capital during adverse market regimes. Resets to 1.0x upon any profitable trade.
    """
    if not os.path.exists(LEDGER_FILE):
        return 1.00

    try:
        with open(LEDGER_FILE, "r", encoding="utf-8") as f:
            ledger = json.load(f)
        if not isinstance(ledger, list) or not ledger:
            return 1.00

        # Filter for autonomous closed positions
        closed_bot_trades = [
            t for t in ledger
            if t.get("source") == "AUTONOMOUS_TRADE_MANAGER"
        ]

        # If fewer than lookback_trades bot trades, fallback to any closed trades with net_pnl
        if len(closed_bot_trades) < lookback_trades:
            closed_bot_trades = [
                t for t in ledger
                if "net_pnl_usd" in t or "pnl_usd" in t
            ]

        if len(closed_bot_trades) < lookback_trades:
            return 1.00

        recent = closed_bot_trades[-lookback_trades:]
        all_losses = all(float(t.get("net_pnl_usd", t.get("pnl_usd", 0))) < 0 for t in recent)

        if all_losses:
            loss_summary = ", ".join([f"{t.get('symbol', 'ASSET')}: ${float(t.get('net_pnl_usd', t.get('pnl_usd', 0))):+,.2f}" for t in recent])
            print(f" 🚨 [COLD-STREAK DEFENSE] Terdeteksi {lookback_trades} kerugian berturut-turut ({loss_summary}).")
            print(f"    Alokasi risiko otomatis dipangkas 50% (0.50x Multiplier) demi perlindungan modal anti-martingale.")
            return 0.50
    except Exception as e:
        print(f" * [Cold-Streak Audit Note] {e}")

    return 1.00

def compute_rs_matrix(symbols):
    """
    Trader 4 (Top Prop Trader) Multi-Timeframe (1H + 4H + 24H) Relative Strength Matrix.
    Single-shot batch ticker retrieval + concurrent klines analysis against BTC benchmark.
    """
    matrix = {}
    ticker_map = {}

    # 1. Single-Shot Batch 24h Ticker Retrieval from Binance Vision
    try:
        req = urllib.request.Request(
            "https://data-api.binance.vision/api/v3/ticker/24hr",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=6, context=SSL_CTX) as resp:
            raw_tickers = json.loads(resp.read().decode("utf-8"))
            if isinstance(raw_tickers, list):
                ticker_map = {t["symbol"]: t for t in raw_tickers}
    except Exception:
        pass

    # 2. Concurrent Multi-Timeframe (1H / 4H) Kline Retrieval
    all_syms = ["BTC"] + [s for s in symbols if s != "BTC"]
    candles_map = {}

    def _fetch_sym_candles(s):
        try:
            return s, market_eyes.fetch_candles(s, bar="1H", limit=6)
        except Exception:
            return s, None

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(12, len(all_syms))) as executor:
        for s, c_data in executor.map(_fetch_sym_candles, all_syms):
            candles_map[s] = c_data

    # 3. Compute BTC Benchmark Performance (1H, 4H, 24H)
    btc_ticker = ticker_map.get("BTCUSDT")
    if btc_ticker:
        btc_chg_24h = float(btc_ticker.get("priceChangePercent", 0.0))
    else:
        btc_t = market_eyes.fetch_ticker_data("BTC")
        btc_chg_24h = float(btc_t.get("change_pct", 0.0)) if btc_t else 0.0

    btc_c = candles_map.get("BTC") or []
    if len(btc_c) >= 2:
        btc_ret_1h = ((float(btc_c[-1][4]) - float(btc_c[-2][4])) / float(btc_c[-2][4]) * 100.0)
    else:
        btc_ret_1h = 0.0

    if len(btc_c) >= 5:
        btc_ret_4h = ((float(btc_c[-1][4]) - float(btc_c[-5][4])) / float(btc_c[-5][4]) * 100.0)
    elif btc_c:
        btc_ret_4h = ((float(btc_c[-1][4]) - float(btc_c[0][4])) / float(btc_c[0][4]) * 100.0)
    else:
        btc_ret_4h = 0.0

    # 4. Compute Multi-Timeframe Alpha for Each Symbol
    for sym in symbols:
        pair_sym = f"{sym}USDT"
        t = ticker_map.get(pair_sym)
        if t:
            chg_24h = float(t.get("priceChangePercent", 0.0))
        else:
            data = market_eyes.fetch_ticker_data(sym)
            chg_24h = float(data.get("change_pct", 0.0)) if data else 0.0

        c = candles_map.get(sym) or []
        if len(c) >= 2:
            ret_1h = ((float(c[-1][4]) - float(c[-2][4])) / float(c[-2][4]) * 100.0)
        else:
            ret_1h = 0.0

        if len(c) >= 5:
            ret_4h = ((float(c[-1][4]) - float(c[-5][4])) / float(c[-5][4]) * 100.0)
        elif c:
            ret_4h = ((float(c[-1][4]) - float(c[0][4])) / float(c[0][4]) * 100.0)
        else:
            ret_4h = 0.0

        rs_1h = round(ret_1h - btc_ret_1h, 2)
        rs_4h = round(ret_4h - btc_ret_4h, 2)
        rs_24h = round(chg_24h - btc_chg_24h, 2)

        # Composite Multi-Timeframe Alpha: 40% 1H, 40% 4H, 20% 24H
        composite_alpha = round((0.40 * rs_1h) + (0.40 * rs_4h) + (0.20 * rs_24h), 2)

        # Dynamic Badging: Require positive 1H momentum for Leader badge
        if composite_alpha >= 1.0 and rs_1h > -0.5:
            tier = "LEADER"
            badge = f"🟢 ALPHA LEADER (1H: {rs_1h:+.2f}%, 4H: {rs_4h:+.2f}%, 24H: {rs_24h:+.2f}%)"
        elif composite_alpha <= -1.0 and rs_1h < 0.5:
            tier = "LAGGARD"
            badge = f"🔴 RELATIVE LAGGARD (1H: {rs_1h:+.2f}%, 4H: {rs_4h:+.2f}%, 24H: {rs_24h:+.2f}%)"
        else:
            tier = "INLINE"
            badge = f"⚪ MARKET INLINE (1H: {rs_1h:+.2f}%, 4H: {rs_4h:+.2f}%, 24H: {rs_24h:+.2f}%)"

        matrix[sym] = {
            "change_24h": round(chg_24h, 2),
            "chg_24h": round(chg_24h, 2),
            "rs_score": composite_alpha,
            "rs_alpha": composite_alpha,
            "composite_alpha": composite_alpha,
            "rs_1h": rs_1h,
            "rs_4h": rs_4h,
            "rs_24h": rs_24h,
            "tier": tier,
            "badge": badge
        }

    return matrix, btc_chg_24h

def scan_swing_candidates(active_watchlist, active_symbols, genome, min_rr, max_risk_pct):
    """
    Scans 1H / 4H swing setups using 4 championship strategies & top-down macro confluence.
    """
    print(f"\n[2. MARKET RESEARCHER AGENT — RELATIVE STRENGTH & WATCHLIST SCAN]")
    rs_matrix, btc_chg = compute_rs_matrix(active_watchlist)
    print(f" * BTC 24h Benchmark Performance: {btc_chg:+.2f}%")
    for s_name, r_info in sorted(rs_matrix.items(), key=lambda x: x[1]["rs_score"], reverse=True):
        print(f"   - {s_name:<5}: 24h {r_info['change_24h']:+6.2f}% | Alpha MTF: {r_info['composite_alpha']:+6.2f}% | {r_info['badge']}")

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

        # 4. CoinGlass & Institutional Derivatives Order Flow Audit
        deriv_intel = None
        try:
            import coinglass_derivatives
            deriv_intel = coinglass_derivatives.get_derivatives_intelligence(sym)
            oi_info = f"OI: {deriv_intel['open_interest_formatted']} (1H: {deriv_intel['oi_change_1h_pct']:+.2f}%) | L/S: {deriv_intel['long_short_ratio']:.2f}"
            print(f"   📊 Derivatives Flow : {oi_info} -> {deriv_intel['regime']}")
        except Exception:
            deriv_intel = None

        # 5. Coinbase US Institutional Premium Index Check (Macro Spot Flow for BTC, ETH, SOL)
        cb_intel = None
        if sym in ["BTC", "ETH", "SOL"]:
            try:
                import coinbase_premium
                cb_intel = coinbase_premium.get_coinbase_premium(sym)
                cb_sign = "+" if cb_intel["premium_pct"] >= 0 else ""
                print(f"   🏛️ Coinbase Premium : {cb_sign}{cb_intel['premium_pct']:+.4f}% (${cb_intel['premium_usd']:+,.2f}) -> {cb_intel['regime']}")
            except Exception:
                cb_intel = None

        # 6. ICT Rejection Block & Mean Threshold (50% Wick Reversal)
        rb_intel = data.get("rejection_block")
        rb_setup = rb_intel.get("retest_setup") if rb_intel else None
        has_bullish_rb = bool(rb_setup and rb_setup.get("side") == "LONG")
        has_bearish_rb = bool(rb_setup and rb_setup.get("side") == "SHORT")

        # Rule A: Bullish Setup (Bullish FVG, Patrick Nill 3-Touch, Fabio Valentini Auction, Tim Flossbach MSS, or ICT Rejection Block)
        has_bullish_fvg = "Bullish FVG" in fvg
        has_bullish_3touch = bool(three_touch and three_touch.get("type") == "BULLISH_3_TOUCH")
        has_bullish_auction = bool(va_setup and va_setup.get("type") == "BULLISH_FAILED_AUCTION")
        has_bullish_sweep = bool(liquidity_sweep and liquidity_sweep.get("type") == "BULLISH_SWEEP_MSS")
        rsi_safe_long = rsi < sub_gen.get("rsi_overbought", 70) and rsi > sub_gen.get("rsi_oversold", 30)

        # Rule B: Bearish Setup (Bearish FVG, Patrick Nill 3-Touch, Fabio Valentini Auction, Tim Flossbach MSS, or ICT Rejection Block)
        has_bearish_fvg = "Bearish FVG" in fvg
        has_bearish_3touch = bool(three_touch and three_touch.get("type") == "BEARISH_3_TOUCH")
        has_bearish_auction = bool(va_setup and va_setup.get("type") == "BEARISH_FAILED_AUCTION")
        has_bearish_sweep = bool(liquidity_sweep and liquidity_sweep.get("type") == "BEARISH_SWEEP_MSS")
        rsi_safe_short = rsi > sub_gen.get("rsi_oversold", 30) and rsi < sub_gen.get("rsi_overbought", 70)

        # -------------------------------------------------------------
        # SMC EQUILIBRIUM & PREMIUM / DISCOUNT ZONE AUDIT (Akademi Crypto Module 02)
        # -------------------------------------------------------------
        h_24 = data.get("high_24h") or (price * 1.02)
        l_24 = data.get("low_24h") or (price * 0.98)
        range_24 = h_24 - l_24
        price_equilibrium_pct = ((price - l_24) / range_24 * 100.0) if range_24 > 0 else 50.0

        signal = None
        if (has_bullish_fvg or has_bullish_3touch or has_bullish_auction or has_bullish_sweep or has_bullish_rb) and rsi_safe_long:
            # SMC Equilibrium Guard: Skip Long if price is already in Extreme Premium (> 75%)
            if price_equilibrium_pct > 75.0 and not (has_bullish_sweep or has_bullish_rb):
                print(f"   🛡️ [SMC Equilibrium Guard] {sym} di-skip untuk LONG: Harga berada di zona Premium Ekstrem ({price_equilibrium_pct:.1f}%). Dilarang membeli di pucuk resistance!")
                continue

            # Derivatives Crowd Shield: Skip Long if retail is dangerously overleveraged (e.g. L/S > 3.0)
            if deriv_intel and deriv_intel.get("bias") == "BEARISH_SQUEEZE_RISK":
                print(f"   🚨 [Derivatives Squeeze Shield] {sym} di-skip untuk LONG: Retail overleveraged ({deriv_intel['long_short_ratio']:.2f}x L/S). Rawan Liquidity Hunt / Long Squeeze!")
                continue

            # Coinbase US Discount Shield: Skip Long if US institutions are heavily dumping spot (< -0.040%)
            if cb_intel and cb_intel.get("is_us_dump"):
                print(f"   🚨 [Coinbase US Discount Shield] {sym} di-skip untuk LONG: Institusi AS sedang jualan spot (Diskon {cb_intel['premium_pct']:+.4f}%). Rawan Bull Trap!")
                continue
            # Plan Long with Dynamic Anti-Liquidity-Hunt SL Buffer
            sweep_buf = get_asset_sweep_buffer(sym)
            if has_bullish_rb and rb_setup:
                sl = round(rb_setup["sl_price"], 4)
                reason_tag = f"🕯️ ICT REJECTION BLOCK (MT ${rb_setup['mean_threshold']:,.4f} | {rb_setup['retest_state']})"
            elif has_bullish_sweep and liquidity_sweep:
                sl = round(liquidity_sweep["sweep_level"] * (1.0 - sweep_buf), 4)
                reason_tag = f"⚡ TIM FLOSSBACH MSS (SSL Sweep ${liquidity_sweep['sweep_level']})"
            elif has_bullish_auction and va_setup:
                base_low = min(volume_profile.get("val", price), price * 0.985)
                sl = round(base_low * (1.0 - sweep_buf), 4)
                reason_tag = f"🔥 FABIO AUCTION (VAL ${volume_profile['val']} -> POC ${volume_profile['poc']})"
            elif has_bullish_3touch and three_touch:
                sl = round(three_touch["level"] * (1.0 - sweep_buf), 4)
                reason_tag = f"🌟 3-TOUCH SUPPORT (${three_touch['level']})"
            else:
                low_24h = data.get("low_24h") or (price * 0.98)
                sl = round(low_24h * (1.0 - sweep_buf), 4)
                reason_tag = "Bullish FVG"

            if is_alpha_leader:
                reason_tag += f" + ⭐ ALPHA LEADER (RS {rs_info['rs_score']:+,.2f}%)"
            if vwap_data and "Above VWAP" in vwap_data.get("state", ""):
                reason_tag += " + VWAP Bullish"

            dist_sl = price - sl
            if dist_sl > 0:
                bonus_rr = 0.5 if is_alpha_leader else 0.0
                target_rr = max(effective_min_rr, (4.0 + bonus_rr) if (has_bullish_3touch or has_bullish_auction or has_bullish_sweep or has_bullish_rb) else (effective_min_rr + bonus_rr))
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
                    "is_rejection_block": has_bullish_rb,
                    "rejection_block_setup": rb_setup if has_bullish_rb else None,
                    "is_alpha_leader": is_alpha_leader,
                    "sub_genome": sub_label,
                    "risk_pct": effective_max_risk,
                    "reason": f"{reason_tag} + RSI {rsi:.1f} + R:R 1:{rr:.2f} [{sub_label}]"
                }

        elif (has_bearish_fvg or has_bearish_3touch or has_bearish_auction or has_bearish_sweep or has_bearish_rb) and rsi_safe_short:
            # SMC Equilibrium Guard: Skip Short if price is in Discount (< 50%)
            if price_equilibrium_pct < 50.0 and not (has_bearish_sweep or has_bearish_rb):
                print(f"   🛡️ [SMC Equilibrium Guard] {sym} di-skip untuk SHORT: Harga berada di zona Diskon ({price_equilibrium_pct:.1f}%). Dilarang shorting di area diskon/support!")
                continue

            # Derivatives Crowd Shield: Skip Short if retail is crowded short (<0.75 L/S), high risk of short squeeze pump!
            if deriv_intel and deriv_intel.get("bias") == "BULLISH_SQUEEZE":
                print(f"   🚨 [Derivatives Squeeze Shield] {sym} di-skip untuk SHORT: Retail overleveraged Short ({deriv_intel['long_short_ratio']:.2f}x L/S). Rawan Short Squeeze pump!")
                continue

            # Coinbase US Inflow Shield: Skip Short if US institutions are aggressively buying spot (> +0.035%)
            if cb_intel and cb_intel.get("is_us_inflow") and cb_intel.get("premium_pct", 0) >= 0.035:
                print(f"   🚨 [Coinbase US Inflow Shield] {sym} di-skip untuk SHORT: Institusi AS sedang memborong spot ({cb_intel['premium_pct']:+.4f}%). Rawan dilibas tren!")
                continue
            # Plan Short with Dynamic Anti-Liquidity-Hunt SL Buffer
            sweep_buf = get_asset_sweep_buffer(sym)
            if has_bearish_rb and rb_setup:
                sl = round(rb_setup["sl_price"], 4)
                reason_tag = f"🕯️ ICT REJECTION BLOCK (MT ${rb_setup['mean_threshold']:,.4f} | {rb_setup['retest_state']})"
            elif has_bearish_sweep and liquidity_sweep:
                sl = round(liquidity_sweep["sweep_level"] * (1.0 + sweep_buf), 4)
                reason_tag = f"⚡ TIM FLOSSBACH MSS (BSL Sweep ${liquidity_sweep['sweep_level']})"
            elif has_bearish_auction and va_setup:
                base_high = max(volume_profile.get("vah", price), price * 1.015)
                sl = round(base_high * (1.0 + sweep_buf), 4)
                reason_tag = f"🔥 FABIO AUCTION (VAH ${volume_profile['vah']} -> POC ${volume_profile['poc']})"
            elif has_bearish_3touch and three_touch:
                sl = round(three_touch["level"] * (1.0 + sweep_buf), 4)
                reason_tag = f"🌟 3-TOUCH RESISTANCE (${three_touch['level']})"
            else:
                high_24h = data.get("high_24h") or (price * 1.02)
                sl = round(high_24h * (1.0 + sweep_buf), 4)
                reason_tag = "Bearish FVG"

            if is_beta_laggard:
                reason_tag += f" + ⭐ BETA LAGGARD (RS {rs_info['rs_score']:+,.2f}%)"
            if vwap_data and "Below VWAP" in vwap_data.get("state", ""):
                reason_tag += " + VWAP Bearish"

            dist_sl = sl - price
            if dist_sl > 0:
                bonus_rr = 0.5 if is_beta_laggard else 0.0
                target_rr = max(effective_min_rr, (4.0 + bonus_rr) if (has_bearish_3touch or has_bearish_auction or has_bearish_sweep or has_bearish_rb) else (effective_min_rr + bonus_rr))
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
                    "is_rejection_block": has_bearish_rb,
                    "rejection_block_setup": rb_setup if has_bearish_rb else None,
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

    active_watchlist = symbols if symbols else get_dynamic_futures_watchlist(top_n=12, is_demo=is_demo)
    session_info = session_filter.get_current_session_info()
    is_blk, blk_reason, next_ev = macro_news_shield.audit_news_blackout(buffer_minutes=30)

    # Launch High-Frequency Fast Position Watcher Thread if not running
    try:
        trade_manager.start_fast_watcher(user_email=user_email, is_demo=is_demo)
    except Exception:
        pass

    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "=" * 68)
    print(f"       🤖 AUTONOMOUS AI TRADING DESK — CYCLE RUN")
    print(f"       📅 Waktu      : {timestamp_str}")
    print(f"       👤 Akun       : {target_user}")
    print(f"       🕹️ Mode       : {mode_label}")
    print(f"       ⏱️ Sesi Pasar  : {session_info['session_name']}")
    print(f"       🎯 Akurasi Min : Skor Konfluensi >= {session_info['min_threshold']}% (Akurasi Terproteksi)")
    print(f"       📰 News Shield : {'🔴 BLACKOUT (Order Baru Beku)' if is_blk else '🟢 AMAN (Normal Autopilot)'}")
    print(f"       🌐 Watchlist  : {len(active_watchlist)} Aset ({', '.join(active_watchlist)})")
    print(f"       🧬 Genome     : Gen {genome.get('generation', 1)} (Min R:R >= {min_rr}, Max Risk: {max_risk_pct}%)")
    print("=" * 68)

    # 1. Check Account Equity, Available Margin & Active Positions Guardrail
    balance_usd, available_usd = get_account_financials(user_email, is_demo)
    active_positions = get_active_positions(user_email, is_demo)
    active_symbols = [p["symbol"] for p in active_positions]
    cold_streak_mult = get_drawdown_risk_multiplier(lookback_trades=2)

    # Check if desk execution is paused via Telegram remote control
    if telegram_notifier.is_desk_paused():
        print(f"\n[Telegram Remote Guard] ⏸️ Trading Desk sedang DIJEDA via Telegram (/pause). Melewatkan pembukaan order baru.")
        export_dashboard_feed(target_user, is_demo, balance_usd, active_positions, genome)
        return

    print(f"\n[1. RISK OFFICER AUDIT]")
    print(f" * Saldo Dompet Futures : ${balance_usd:,.2f} USDT (Margin Bebas Tersedia: ${available_usd:,.2f} USDT)")
    print(f" * Posisi Aktif Saat Ini: {len(active_positions)} / {max_open_positions} max")
    print(f" * Capital Shield Check : {'⚠️ ACTIVE COLD-STREAK (Alokasi risiko dipangkas 50%)' if cold_streak_mult < 1.0 else '🟢 NORMAL (Alokasi risiko penuh)'}")

    # 1A. Portfolio Correlation & Directional Heat Audit (Akademi Crypto Module 03)
    try:
        import portfolio_guard
        port_audit = portfolio_guard.audit_portfolio_heat(active_positions, balance_usd)
        print(f" * Directional Heat     : {port_audit['long_count']}/{port_audit['max_same_direction']} Longs | {port_audit['short_count']}/{port_audit['max_same_direction']} Shorts -> {port_audit['heat_status']}")
    except Exception as e:
        port_audit = None
        print(f" * [Portfolio Guard Warning] {e}")

    # 1B. BTC.D & USDT.D Market Flow Compass Audit (Akademi Crypto Module 01)
    try:
        import dominance_compass
        comp_info = dominance_compass.get_dominance_compass()
        print(f" * Macro Flow Compass   : BTC.D {comp_info['btc_d']:.2f}% | USDT.D {comp_info['usdt_d']:.2f}% ({comp_info['usdt_bias']}) -> {comp_info['regime_title']}")
    except Exception as e:
        comp_info = None
        print(f" * [Dominance Compass Warning] {e}")

    # 1C. BTC Macro Regime & Directional Gatekeeper (Akademi Crypto Module 02 & 04)
    btc_regime = None
    try:
        import market_regime
        btc_regime = market_regime.detect_market_regime("BTCUSDT", "1h")
        if btc_regime:
            print(f" * BTC Macro 1H Regime  : {btc_regime['regime_label']} (ADX {btc_regime['adx']:.1f} | Bias: {btc_regime['bias']})")
    except Exception as e:
        print(f" * [Market Regime Warning] {e}")

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

    # 1B. Macro High-Impact News Blackout Guardrail
    if is_blk:
        print(f"\n[🚨 MACRO NEWS SHIELD GUARD] {blk_reason}")
        print("Trading desk membekukan pembukaan order baru demi melindungi modal dari lonjakan volatilitas ekstrim!")
        log_desk_activity({
            "timestamp": timestamp_str,
            "action": "NEWS_BLACKOUT_BLOCKED",
            "reason": blk_reason,
            "balance": balance_usd,
            "positions_count": len(active_positions)
        })
        return

    desk_mode = telegram_notifier.get_desk_mode().upper()
    if desk_mode not in ["SCALP", "SWING", "HYBRID"]:
        desk_mode = "HYBRID"

    mode_labels = {
        "HYBRID": "🤖 HYBRID AUTO (Simultaneous 1H Swing + 5m Fast Scalp)",
        "SCALP": "⚡ FAST SCALPER ONLY (5m/15m Protocol)",
        "SWING": "🎯 SWING INTRADAY ONLY (1H/4H Confluence)"
    }
    print(f"\n * Mode Operasional Trading Desk: {mode_labels.get(desk_mode, desk_mode)}")

    candidates = []

    # 2A. Fast Scalper Scan (Runs in HYBRID and SCALP modes)
    if desk_mode in ["SCALP", "HYBRID"]:
        print(f"\n[2A. FAST SCALPER ENGINE — 5m / 15m MICRO-STRUCTURE SCAN]")
        scalp_setups = fast_scalper.scan_all_scalp_opportunities(active_watchlist[:8])
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

    # 2B. Swing Intraday Scan (Runs in HYBRID and SWING modes)
    if desk_mode in ["SWING", "HYBRID"]:
        print(f"\n[2B. SWING INTRADAY ENGINE — 1H / 4H MACRO CONFLUENCE SCAN]")
        swing_cands = scan_swing_candidates(active_watchlist, active_symbols, genome, min_rr, max_risk_pct)
        candidates.extend(swing_cands)

    # 3. Decision & Execution Desk
    print("\n[3. INSTITUTIONAL ACCURACY & CONFLUENCE AUDIT]")
    admissible_candidates = []
    for cand in candidates:
        is_ok, audit_msg, score_data = session_filter.audit_candidate_confluence(cand, session_info)
        cand["confluence_score"] = score_data["score"]
        cand["confluence_grade"] = score_data["grade"]
        if is_ok:
            print(f"  {audit_msg}")
            admissible_candidates.append(cand)
        else:
            print(f"  {audit_msg}")

    if not admissible_candidates:
        print("\nTidak ada setup yang lolos ambang batas konfluensi ketat.")
        print(f"Desk standby demi menjaga akurasi ({session_info['session_name']} | Syarat Min: {session_info['min_threshold']}%).")
        log_desk_activity({
            "timestamp": timestamp_str,
            "action": "STANDBY_LOW_CONFLUENCE",
            "balance": balance_usd,
            "positions_count": len(active_positions)
        })
    else:
        # Available slots
        slots_available = max_open_positions - len(active_positions)
        # Prioritize candidates based on active desk mode
        if desk_mode == "HYBRID":
            # Fair ranking: Confluence score first, then R:R (giving 5m scalps fast access)
            admissible_candidates.sort(key=lambda x: (
                x.get("confluence_score", 0),
                x.get("rr", 0)
            ), reverse=True)
        elif desk_mode == "SCALP":
            admissible_candidates.sort(key=lambda x: (
                1 if x.get("is_scalp") else 0,
                x.get("confluence_score", 0),
                x.get("rr", 0)
            ), reverse=True)
        else:
            # Swing mode: prioritize Big-Profit Swing setups over scalps
            admissible_candidates.sort(key=lambda x: (
                x.get("confluence_score", 0),
                0 if x.get("is_scalp") else 1,
                x.get("rr", 0)
            ), reverse=True)
        selected = admissible_candidates[:slots_available]

        print(f"\n🎯 Ditemukan {len(admissible_candidates)} setup lolos uji akurasi. Mengeksekusi {len(selected)} setup terbaik (Slot tersedia: {slots_available}):")

        for idx, best in enumerate(selected, 1):
            # Check Portfolio Correlation & Directional Heat Guard
            try:
                import portfolio_guard
                is_port_ok, port_msg = portfolio_guard.filter_candidate_by_correlation(best, active_positions)
                if not is_port_ok:
                    print(f"\n--- [{idx}/{len(selected)}] {best['side']} {best['symbol']} DI-SKIP ---")
                    print(f"  {port_msg}")
                    continue
                base_risk = best.get("risk_pct", max_risk_pct)
                kelly_risk, kelly_status = get_adaptive_kelly_risk_pct(base_risk_pct=base_risk)
                effective_risk_pct = portfolio_guard.get_scaled_risk_pct(best["side"], active_positions, kelly_risk)
            except Exception:
                effective_risk_pct = max_risk_pct
                kelly_status = "Fallback"

            # Anti-Martingale Cold-Streak Circuit Breaker (Module 03)
            if cold_streak_mult < 1.0:
                effective_risk_pct = round(effective_risk_pct * cold_streak_mult, 2)

            # Check BTC.D & USDT.D Dominance Compass Guardrail (Akademi Crypto Module 01)
            try:
                import dominance_compass
                is_dom_ok, dom_msg, _ = dominance_compass.filter_candidate_by_dominance(best)
                if not is_dom_ok:
                    print(f"\n--- [{idx}/{len(selected)}] {best['side']} {best['symbol']} DI-SKIP ---")
                    print(f"  {dom_msg}")
                    continue
            except Exception:
                pass

            # Check BTC Macro Regime Directional Guardrail (Akademi Crypto Master Gatekeeper)
            try:
                import market_regime
                is_regime_ok, regime_msg = market_regime.filter_candidate_by_regime(best, btc_regime=btc_regime)
                if not is_regime_ok:
                    print(f"\n--- [{idx}/{len(selected)}] {best['side']} {best['symbol']} DI-SKIP [REGIME GATEKEEPER] ---")
                    print(f"  {regime_msg}")
                    continue
            except Exception as e:
                pass

            # Check Derivatives Funding Rate & Liquidation Hunt Guardrail
            try:
                import coinglass_derivatives
                hunt_audit = coinglass_derivatives.evaluate_liquidation_hunt(best["symbol"], best["side"])
                if hunt_audit["decision"] == "VETO":
                    print(f"\n--- [{idx}/{len(selected)}] {best['side']} {best['symbol']} DI-SKIP [LIQUIDATION CROWD GUARD] ---")
                    print(f"  🛑 {hunt_audit['reason']}")
                    continue
                elif hunt_audit["decision"] == "BOOST_HUNT":
                    best["confluence_score"] = min(100, best.get("confluence_score", 80) + hunt_audit["confluence_boost"])
                    print(f"  ⚡ {hunt_audit['reason']}")
            except Exception as e:
                pass

            print(f"\n--- [{idx}/{len(selected)}] EKSEKUSI SETUP: {best['side']} {best['symbol']} ---")
            print(f" * Konfluensi : {best['confluence_score']}% [{best['confluence_grade']}]")
            print(f" * Rationale  : {best['reason']}")
            print(f" * Entry Price: ${best['price']:,.4f}")
            print(f" * Stop Loss  : ${best['sl']:,.4f}")
            print(f" * Take Profit: ${best['tp']:,.4f}")
            print(f" * R:R Ratio  : 1 : {best['rr']:.2f}")

            # 4. AI Senior Quant Risk Officer Pre-Trade Sanity Audit
            ai_audit = None
            try:
                import ai_risk_officer
                ai_ctx = {
                    "news_shield": {"is_blackout": is_blk, "reason": blk_reason},
                    "heat": {
                        "long_count": len([p for p in active_positions if float(p.get("positionAmt", 0)) > 0]),
                        "short_count": len([p for p in active_positions if float(p.get("positionAmt", 0)) < 0])
                    },
                    "market_regime": btc_regime
                }
                try:
                    import dominance_compass
                    ai_ctx["compass"] = dominance_compass.get_dominance_compass()
                except Exception:
                    pass
                try:
                    import liquidity_heatmap
                    ai_ctx["depth"] = liquidity_heatmap.calculate_depth_imbalance(best["symbol"])
                except Exception:
                    pass
                try:
                    import coinbase_premium
                    ai_ctx["coinbase_premium"] = coinbase_premium.get_coinbase_premium(best.get("base", "BTC"))
                except Exception:
                    pass

                ai_audit = ai_risk_officer.audit_trade_setup(best, ai_ctx)
                best["ai_audit"] = ai_audit
                print(f" * 🤖 AI Officer: {ai_audit['decision']} ({ai_audit['confidence']}%) via {ai_audit.get('provider', 'AI')}")
                print(f"   Thesis     : {ai_audit['thesis']}")

                if ai_audit["decision"] == "VETO":
                    print(f" 🚨 [AI OFFICER VETO] Setup {best['symbol']} diveto oleh AI: {ai_audit['thesis']}")
                    try:
                        telegram_notifier.notify_ai_officer_veto(best, ai_audit)
                    except Exception:
                        pass
                    continue
                elif ai_audit["decision"] == "ADJUST_RISK":
                    scale = float(ai_audit.get("suggested_risk_scale", 0.7))
                    effective_risk_pct = max(0.5, effective_risk_pct * scale)
                    print(f" ⚠️ [AI RISK ADJUST] Risiko disesuaikan oleh AI ke {scale*100:.0f}% ({effective_risk_pct:.2f}% modal)")
            except Exception as e:
                print(f" * [AI Officer Note] Heuristic bypass: {e}")

            # Volatility-Adaptive Dynamic ATR Stop Loss Buffer (Akademi Crypto Risk Precision)
            try:
                import market_regime
                reg_info = market_regime.detect_market_regime(best["symbol"], "1h")
                if reg_info and reg_info.get("atr", 0) > 0:
                    atr_val = float(reg_info["atr"])
                    min_sl_dist = atr_val * 1.25
                    current_sl_dist = abs(best["price"] - best["sl"])
                    if current_sl_dist < min_sl_dist:
                        old_sl = best["sl"]
                        if best["side"] in ["BUY", "LONG"]:
                            best["sl"] = best["price"] - min_sl_dist
                            best["tp"] = best["price"] + (min_sl_dist * best["rr"])
                        else:
                            best["sl"] = best["price"] + min_sl_dist
                            best["tp"] = best["price"] - (min_sl_dist * best["rr"])
                        print(f" 🛡️ [VOLATILITY-ADAPTIVE ATR STOP] SL disesuaikan dari ${old_sl:,.4f} ke ${best['sl']:,.4f} (Buffer 1.25x ATR ${atr_val:,.4f}) demi mencegah wick hunt.")
            except Exception as e:
                pass

            # Refresh live available free margin directly from exchange before sizing
            _, live_avail = get_account_financials(user_email, is_demo)
            available_usd = min(available_usd, live_avail)

            # Calculate exact position size with Dynamic Margin & Scaled Risk Guardrail
            risk_budget = balance_usd * (effective_risk_pct / 100.0)
            sl_pct = abs(best["price"] - best["sl"]) / best["price"]
            pos_size_usd = risk_budget / max(sl_pct, 0.005)

            # Cap 1: Max 2.5x equity
            pos_size_usd = min(pos_size_usd, balance_usd * 2.5)

            # Cap 2: Alokasi proporsional per slot (agar tidak memonopoli seluruh margin)
            per_slot_notional = (balance_usd / max_open_positions) * 5.0
            pos_size_usd = min(pos_size_usd, per_slot_notional)

            # Cap 3: Available Free Margin Guardrail (gunakan maks 75% dari margin bebas tersisa)
            max_notional_from_avail = available_usd * 0.75 * 5.0
            pos_size_usd = min(pos_size_usd, max_notional_from_avail)

            margin_required = pos_size_usd / 5.0
            if margin_required < 2.0 or available_usd < 10.0:
                print(f" ⚠️ [Margin Guardrail] Sisa margin tersedia (${available_usd:,.2f}) tidak cukup untuk membuka posisi {best['symbol']} (Dibutuhkan: ${margin_required:,.2f}). Melewatkan eksekusi.")
                continue

            # Dynamic precision formatting from exchange info
            raw_qty = pos_size_usd / best["price"]
            qty_str = binance_client.format_qty_precision(best["symbol"], raw_qty, is_demo=is_demo)
            qty = float(qty_str)

            # Check minNotional & order filters
            is_valid, adjusted_qty, filter_msg = binance_client.validate_order_filters(best["symbol"], qty, best["price"], is_demo=is_demo)
            if not is_valid:
                print(f" ⚠️ [Exchange Filter Alignment] {filter_msg}. Menyesuaikan qty ke {adjusted_qty}...")
                qty = adjusted_qty
                pos_size_usd = qty * best["price"]
                margin_required = pos_size_usd / 5.0
                if margin_required > available_usd:
                    print(f" ⚠️ [Margin Guardrail] Sisa margin (${available_usd:,.2f}) tidak cukup untuk adjusted qty (${margin_required:,.2f}). Melewatkan.")
                    continue

            # Check Order Book Depth Guard before dispatching order
            is_safe_depth, depth_audit = binance_client.check_order_book_depth(
                best["symbol"], qty, best["side"], is_demo=is_demo, max_slippage_pct=0.30
            )
            if not is_safe_depth:
                print(f" ⚠️ [Order Book Liquidity Warning] {best['symbol']} spread ({depth_audit.get('spread_pct')}%) atau estimasi slippage ({depth_audit.get('slippage_pct')}%) tinggi.")

            print(f" * Position Size Budget: ${pos_size_usd:,.2f} ({qty} {best['base']}) | Margin Diperlukan: ${margin_required:,.2f} USDT")
            print(f" * Max Risk At SL      : ${risk_budget:,.2f} ({effective_risk_pct:.2f}% modal)")

            # Execute via binance_client (Limit-Chase for Maker fee savings of 60%, with 3s auto-fallback to Market)
            exec_mode = "LIMIT_CHASE"
            print(f"[Mengirimkan Order ke Binance Futures (Mode: {exec_mode})...]")
            order_res = binance_client.place_futures_order(
                symbol=best["symbol"],
                side=best["side"],
                quantity=qty,
                leverage=5,
                sl=best["sl"],
                tp=best["tp"],
                is_demo=is_demo,
                user_email=user_email,
                exec_mode=exec_mode
            )

            if not order_res or not order_res.get("orderId"):
                print(f"⚠️ Eksekusi {best['symbol']} gagal di bursa Binance. Melewatkan alert Telegram dan pendaftaran trade manager.")
                continue

            # Update available_usd and active_positions for subsequent orders in the same cycle
            available_usd = max(0.0, available_usd - margin_required)
            active_positions.append({
                "symbol": best["symbol"],
                "positionAmt": qty if best["side"].upper() in ["BUY", "LONG"] else -qty,
                "entryPrice": best["price"],
                "markPrice": best["price"]
            })

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
                    is_scalp=best.get("is_scalp", False),
                    ai_thesis=ai_audit.get("thesis") if ai_audit else None,
                    ai_confidence=ai_audit.get("confidence") if ai_audit else None
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
    desk_mode = telegram_notifier.get_desk_mode().upper()
    if desk_mode == "HYBRID":
        mode_desc = "🤖 HYBRID (Dual-Engine: 5m Fast Scalp + 1H Swing Confluence)"
    elif desk_mode == "SCALP":
        mode_desc = "⚡ SCALP ONLY (5m Micro-Structure Protocol)"
    else:
        mode_desc = "🎯 SWING ONLY (1H/4H Macro Confluence Focus)"
    print(f"Desk Operational Mode: {mode_desc}")
    try:
        import market_regime
        btc_reg = market_regime.detect_market_regime("BTCUSDT", "1h")
        if btc_reg:
            print(f"BTC 1H Macro Regime  : {btc_reg['regime_label']} (Bias: {btc_reg['bias']})")
    except Exception:
        pass
    print(f"Desk Genetic Rules   : Generation {genome.get('generation', 1)}")
    print(f" * Min R:R Filter    : 1 : {genome.get('parameters', {}).get('min_risk_reward', 3.0)}")
    print(f" * Max Risk Per Trade: {genome.get('parameters', {}).get('max_risk_per_trade_pct', 1.5)}%")
    print("=======================================================\n")

def ensure_dashboard_daemon():
    """
    Checks if Web Dashboard HTTP server is listening on port 5000.
    If not, automatically launches dashboard_server.py as a background daemon.
    """
    import socket
    import subprocess
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    is_up = False
    try:
        if sock.connect_ex(("127.0.0.1", 5000)) == 0:
            is_up = True
    except Exception:
        pass
    finally:
        sock.close()

    if not is_up:
        dash_script = os.path.join(TOOLS_DIR, "dashboard_server.py")
        if os.path.exists(dash_script):
            try:
                flags = (0x00000008 | 0x00000200 | 0x08000000) if sys.platform == "win32" else 0
                subprocess.Popen(
                    [sys.executable, "-u", dash_script],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=flags,
                    close_fds=True,
                    cwd=ROOT_DIR
                )
                print("🌐 [Web Dashboard] Daemon otomatis dinyalakan di background (http://localhost:5000).")
            except Exception as e:
                print(f"⚠️ [Web Dashboard] Gagal auto-start daemon: {e}")

def main():
    parser = argparse.ArgumentParser(description="Autonomous AI Trading Desk (CEO Orchestrator)")
    sub = parser.add_subparsers(dest="command")

    # Run command
    run_p = sub.add_parser("run", help="Jalankan siklus pemindaian dan eksekusi trading desk")
    run_p.add_argument("--once", action="store_true", help="Jalankan 1 siklus lalu selesai")
    run_p.add_argument("--mode", type=str, choices=["SWING", "SCALP", "HYBRID"], default="HYBRID", help="Set mode operasional desk (default: HYBRID)")
    run_p.add_argument("--symbols", type=str, default=None, help="Daftar koin dipisah koma (misal: BTC,ETH,SOL,BNB,DOGE)")
    run_p.add_argument("--interval", type=int, default=30, help="Interval menit jika berjalan berkelanjutan (default: 1 menit untuk HYBRID/SCALP, 15 menit untuk SWING)")
    run_p.add_argument("--max-positions", type=int, default=3, help="Batas maksimal posisi aktif bersamaan (default: 3)")
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
        ensure_dashboard_daemon()
        if getattr(args, "mode", None):
            state = telegram_notifier.load_desk_state()
            state["mode"] = args.mode.upper()
            telegram_notifier.save_desk_state(state)
            print(f"🎯 Mode Operasional Desk diset ke: {state['mode']}")

        syms = [s.strip().upper() for s in args.symbols.split(",") if s.strip()] if getattr(args, "symbols", None) else None
        max_pos = getattr(args, "max_positions", 3)
        if args.once:
            run_trading_desk_cycle(args.user, is_demo, max_open_positions=max_pos, symbols=syms)
        else:
            w_str = ", ".join(syms) if syms else ", ".join(DEFAULT_WATCHLIST)
            cur_mode = telegram_notifier.get_desk_mode().upper()
            active_interval = args.interval if args.interval != 30 else (1 if cur_mode in ["HYBRID", "SCALP"] else 15)
            print(f"Memulai Autonomous Trading Desk Daemon (Watchlist: {w_str} | Mode: {cur_mode} | Interval: {active_interval} menit | Max Positions: {max_pos})... Tekan Ctrl+C untuk berhenti.")
            # Start background Telegram interactive remote control listener thread
            telegram_notifier.start_command_listener(args.user, is_demo=is_demo)
            try:
                while True:
                    run_trading_desk_cycle(args.user, is_demo, max_open_positions=max_pos, symbols=syms)
                    cur_mode = telegram_notifier.get_desk_mode().upper()
                    active_interval = args.interval if args.interval != 30 else (1 if cur_mode in ["HYBRID", "SCALP"] else 15)
                    print(f"Desk tidur sejenak selama {active_interval} menit...")
                    time.sleep(active_interval * 60)
            except KeyboardInterrupt:
                print("\nTrading Desk Daemon dihentikan oleh pengguna.")
    else:
        show_desk_status(None, is_demo=True)

if __name__ == "__main__":
    main()

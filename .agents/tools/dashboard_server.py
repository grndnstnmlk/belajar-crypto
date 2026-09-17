"""
Web Visual Mission Control HTTP Server & API Bridge
Serves dashboard.html, real-time klines with calculated VWAP/Volume Profile,
and provides two-way remote control endpoints for Binance Futures.
"""

import http.server
import json
import os
import socketserver
import ssl
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PORT = 5000
TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
ROOT_DIR = os.path.dirname(os.path.dirname(TOOLS_DIR))
DASHBOARD_HTML_PATH = os.path.join(ROOT_DIR, "dashboard.html")

sys.path.insert(0, TOOLS_DIR)
import binance_client
import market_eyes
import quant_backtester
import telegram_notifier
import topdown_confluence
import trade_manager
import session_filter
import macro_news_shield
import market_structure
import dominance_compass
import portfolio_guard
import coinbase_premium
import coinglass_derivatives
import trade_journal
import liquidity_heatmap
import ai_risk_officer
import market_radar
import threading

try:
    import hyperopt_optimizer
except ImportError:
    hyperopt_optimizer = None

try:
    import adaptive_ml_engine
except ImportError:
    adaptive_ml_engine = None

try:
    import pairlist_pipeline
except ImportError:
    pairlist_pipeline = None

try:
    import dex_pump_radar
except ImportError:
    dex_pump_radar = None

try:
    import onchain_whale_tracker
except ImportError:
    onchain_whale_tracker = None

try:
    import dex_futures_bridge
except ImportError:
    dex_futures_bridge = None

_hyperopt_state = {
    "is_running": False,
    "last_run": None,
    "last_result": None,
    "error": None
}

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}

# -----------------------------------------------------------------------------
# DEX & WHALE RADAR AUTOMATED TELEGRAM WATCHER + AUTO-BRIDGE ENGINE
# -----------------------------------------------------------------------------
_notified_dex_tokens = set()
_notified_whale_alerts = set()
_last_circuit_breaker_alert = 0.0

def _run_dex_whale_alert_watcher():
    """Periodically scans DEX pumps & Whale swaps and executes Auto-Bridge with Black Swan protection."""
    global _last_circuit_breaker_alert
    time.sleep(15)  # initial delay on startup
    while True:
        try:
            time.sleep(60)
            
            # 0. Check Black Swan Circuit Breaker
            is_shock = False
            bridge_engine = dex_futures_bridge.get_bridge_engine() if dex_futures_bridge else None
            if bridge_engine:
                is_shock, cb_reason, cb_metrics = bridge_engine.check_black_swan_circuit_breaker()
                if is_shock and (time.time() - _last_circuit_breaker_alert > 1800):
                    _last_circuit_breaker_alert = time.time()
                    try:
                        telegram_notifier.notify_black_swan_circuit_breaker({
                            "reason": cb_reason,
                            "btc_15m_return_pct": cb_metrics.get("btc_15m_return_pct", 0.0),
                            "btc_5m_return_pct": cb_metrics.get("btc_5m_return_pct", 0.0),
                            "btc_price": cb_metrics.get("btc_current_price", 0.0)
                        })
                    except Exception:
                        pass

            # 1. Evaluate DEX Pump Breakouts & Auto-Bridge
            if dex_pump_radar and not is_shock:
                try:
                    radar = dex_pump_radar.DexPumpRadar()
                    state = radar.scan_all_trending_pumps()
                    for token in (state.get("tokens") or [])[:5]:
                        addr = token.get("token_address")
                        alpha = token.get("alpha_score", 0)
                        sec = token.get("security") or {}
                        safety = sec.get("safety_score", token.get("safety_score", 0))
                        
                        # Check Futures bridge mapping
                        mapped_futures = bridge_engine.normalize_to_futures_symbol(token.get("symbol")) if bridge_engine else None
                        if mapped_futures:
                            token["bridged_futures_contract"] = mapped_futures

                        if addr and addr not in _notified_dex_tokens and alpha >= 65 and safety >= 72:
                            _notified_dex_tokens.add(addr)
                            telegram_notifier.notify_dex_pump_alert(token)

                        # Auto-Bridge execution to Binance Futures 20x
                        if bridge_engine and mapped_futures and alpha >= 70 and safety >= 75:
                            bridge_res = bridge_engine.evaluate_and_bridge_token(token)
                            if bridge_res.get("bridged"):
                                try:
                                    telegram_notifier.notify_auto_bridge_execution({
                                        "token": token.get("symbol"),
                                        "contract": mapped_futures,
                                        "alpha_score": alpha,
                                        "safety_score": safety,
                                        "leverage": 20,
                                        "mark_price": token.get("price_usd", 0.0)
                                    })
                                except Exception:
                                    pass
                except Exception:
                    pass

            # 2. Evaluate Whale Swaps & Inflows
            if onchain_whale_tracker:
                try:
                    tracker = onchain_whale_tracker.OnChainWhaleTracker()
                    w_state = tracker.run_full_scan()
                    for alert in (w_state.get("recent_whale_alerts") or [])[:3]:
                        sig_key = f"{alert.get('symbol')}:{alert.get('action')}:{round(alert.get('volume_5m_usd', 0), -3)}"
                        if sig_key not in _notified_whale_alerts:
                            _notified_whale_alerts.add(sig_key)
                            telegram_notifier.notify_whale_inflow_alert(alert)
                except Exception:
                    pass

            if len(_notified_dex_tokens) > 200:
                _notified_dex_tokens.clear()
            if len(_notified_whale_alerts) > 200:
                _notified_whale_alerts.clear()
        except Exception:
            pass

_dex_whale_watcher_thread = threading.Thread(target=_run_dex_whale_alert_watcher, daemon=True, name="DexWhaleAlertWatcher")
_dex_whale_watcher_thread.start()

_feed_cache = None
_last_feed_fetch_time = 0
_intel_cache = None
_last_intel_fetch_time = 0

def get_live_watchlist_rs():
    """
    Fetches real-time market prices & calculates Relative Strength (RS vs BTC)
    using unified single-pass market_radar cache.
    """
    try:
        return market_radar.get_live_watchlist_rs()
    except Exception:
        target_coins = ["BTC", "ETH", "SOL", "LINK", "BNB", "DOGE", "ADA", "SUI", "AVAX", "XRP"]
        return [
            {"symbol": c, "pair": f"{c}USDT", "price": 0.0, "change_24h": 0.0, "rs_score": 0.0, "is_leader": True, "rs_rank": i+1}
            for i, c in enumerate(target_coins)
        ]

def get_dashboard_feed_data(force_refresh=False):
    global _feed_cache, _last_feed_fetch_time
    now = time.time()
    if not force_refresh and _feed_cache is not None and (now - _last_feed_fetch_time) < 2.5:
        return _feed_cache

    feed_path = os.path.join(DATA_DIR, "dashboard_feed.json")
    feed = {}
    if os.path.exists(feed_path):
        try:
            with open(feed_path, "r", encoding="utf-8") as f:
                feed = json.load(f)
        except Exception:
            pass

    # Merge with active trades meta
    meta = trade_manager.load_trade_metadata()
    state = telegram_notifier.load_desk_state()

    # Fetch and combine positions from BOTH Binance Futures and MetaTrader 5
    pos_list = []
    binance_bal = 0.0
    mt5_bal = 0.0

    # 1. Fetch Binance Futures Positions & Balance
    try:
        balance = binance_client.send_signed_request("/fapi/v2/balance", method="GET", is_demo=True)
        if balance and isinstance(balance, list):
            for b in balance:
                if b.get("asset") == "USDT":
                    binance_bal = float(b.get("balance", 0))
                    feed["binance_balance_usd"] = binance_bal
                    break

        b_pos = binance_client.send_signed_request("/fapi/v2/positionRisk", method="GET", is_demo=True)
        if b_pos and isinstance(b_pos, list):
            active_b = [p for p in b_pos if float(p.get("positionAmt", 0)) != 0]
            for p in active_b:
                sym = p["symbol"]
                amt = float(p.get("positionAmt", 0))
                side = "LONG" if amt > 0 else "SHORT"
                entry_p = float(p.get("entryPrice", 0))
                mark_p = float(p.get("markPrice", 0))
                upnl = float(p.get("unRealizedProfit", 0))
                t_meta = meta.get(sym, {})
                r_dist = max(float(t_meta.get("r_distance", entry_p * 0.015)), 0.0001)
                gain = (mark_p - entry_p) if side == "LONG" else (entry_p - mark_p)
                r_mult = round(gain / r_dist, 2)

                # Get candidate SMC structural stop
                has_smc, smc_sl, smc_label = market_structure.get_protected_structural_stop(
                    sym, "BUY" if side == "LONG" else "SELL", entry_p, t_meta.get("current_sl"), bar="15m"
                )

                pos_list.append({
                    "symbol": sym,
                    "side": side,
                    "quantity": abs(amt),
                    "entry_price": entry_p,
                    "mark_price": mark_p,
                    "pnl_usd": upnl,
                    "r_multiple": r_mult,
                    "highest_r": t_meta.get("highest_r_reached", 0.0),
                    "leverage": int(p.get("leverage", 5)),
                    "breakeven_locked": t_meta.get("breakeven_locked", False),
                    "capital_shield_locked": t_meta.get("capital_shield_locked", False),
                    "tp1_taken": t_meta.get("tp1_taken", False),
                    "tp1_pnl_usd": t_meta.get("tp1_pnl_usd", 0.0),
                    "is_runner": t_meta.get("is_runner", False),
                    "trailing_r": t_meta.get("trailing_r_locked", 0.0),
                    "sl": t_meta.get("current_sl"),
                    "tp": t_meta.get("tp"),
                    "structural_level": t_meta.get("structural_level") or smc_label,
                    "candidate_smc_sl": smc_sl if has_smc else None,
                    "has_candidate_smc": has_smc,
                    "sweep_buffer_pct": round(market_structure.get_asset_sweep_buffer(sym) * 100.0, 1),
                    "ai_thesis": t_meta.get("ai_thesis"),
                    "ai_confidence": t_meta.get("ai_confidence"),
                    "opened_at": t_meta.get("opened_at", ""),
                    "backend": "BINANCE"
                })
    except Exception as e:
        pass

    # 2. Fetch MetaTrader 5 (MT5) Positions & Account (if running)
    try:
        import mt5_client
        if mt5_client.ensure_mt5_connected():
            mt5_acc = mt5_client.get_account_summary()
            if mt5_acc.get("connected"):
                mt5_bal = float(mt5_acc.get("balance", 100000.0))
                feed["mt5_balance_usd"] = mt5_bal
                feed["mt5_equity_usd"] = float(mt5_acc.get("equity", 100000.0))
                feed["mt5_login"] = mt5_acc.get("login")
                feed["mt5_server"] = mt5_acc.get("server")

                mt5_positions = mt5_client.get_open_positions()
                if mt5_positions:
                    for p in mt5_positions:
                        sym = p["symbol"]
                        amt = float(p["volume"])
                        side = "LONG" if p["side"] == "BUY" else "SHORT"
                        entry_p = float(p["price_open"])
                        mark_p = float(p["price_current"])
                        upnl = float(p["profit_usd"])
                        ticket = p["ticket"]
                        t_meta = meta.get(f"MT5_{ticket}", meta.get(sym, {}))
                        init_sl = float(t_meta.get("initial_sl") or p["sl"] or (entry_p * 0.99 if side == "LONG" else entry_p * 1.01))
                        r_dist = max(abs(entry_p - init_sl), entry_p * 0.001)
                        gain = (mark_p - entry_p) if side == "LONG" else (entry_p - mark_p)
                        r_mult = round(gain / r_dist, 2)
                        
                        pos_list.append({
                            "symbol": sym,
                            "side": side,
                            "quantity": amt,
                            "entry_price": entry_p,
                            "mark_price": mark_p,
                            "pnl_usd": upnl,
                            "r_multiple": r_mult,
                            "highest_r": t_meta.get("highest_r_reached", r_mult),
                            "leverage": int(mt5_acc.get("leverage", 100)),
                            "breakeven_locked": t_meta.get("breakeven_locked", False),
                            "capital_shield_locked": False,
                            "tp1_taken": False,
                            "tp1_pnl_usd": 0.0,
                            "is_runner": False,
                            "trailing_r": t_meta.get("trailing_r_locked", 0.0),
                            "sl": p["sl"],
                            "tp": p["tp"],
                            "ticket": ticket,
                            "structural_level": "MT5 Stop / Broker Order",
                            "backend": "MT5"
                        })
    except Exception as e:
        pass

    feed["positions"] = pos_list
    feed["balance_usd"] = binance_bal if binance_bal > 0 else (mt5_bal if mt5_bal > 0 else 4628.0)
    feed["execution_backend"] = "Dual (Binance + MT5)" if (binance_bal > 0 and mt5_bal > 0) else ("MetaTrader 5 (Demo)" if mt5_bal > 0 else "Binance Futures (Demo)")

    # Directional heat overview
    bal_val = feed.get("balance_usd", 100000.0)
    try:
        cur_pos = feed.get("positions", [])
        feed["heat"] = portfolio_guard.audit_portfolio_heat(cur_pos, bal_val)
    except Exception:
        pass

    cur_mode = state.get("mode", "SWING").upper()
    feed["is_paused"] = state.get("paused", False)
    feed["mode"] = cur_mode
    feed["timeframes"] = {
        "active_mode": cur_mode,
        "scalp": "5m",
        "swing": "1H",
        "macro": "4H",
        "scan_interval": "60s (Fast Cycle)" if cur_mode in ["HYBRID", "SCALP"] else "15m",
        "summary": "Dual-Engine: 5m Fast Scalp (Target 15-45m) + 1H Swing (1:3.0+ R:R)" if cur_mode == "HYBRID" else ("5m Micro-Structure Protocol" if cur_mode == "SCALP" else "1H / 4H Macro Confluence")
    }
    feed["session"] = session_filter.get_current_session_info()
    is_blk, blk_reason, next_ev = macro_news_shield.audit_news_blackout(buffer_minutes=30)
    feed["news_shield"] = {
        "is_blackout": is_blk,
        "status": "BLACKOUT_ACTIVE" if is_blk else "SAFE",
        "reason": blk_reason,
        "next_event": next_ev.get("title") if next_ev else "None",
        "next_time": next_ev.get("time_wib_str") if next_ev else "-"
    }
    # Macro Market Regime & Derivatives Flow
    try:
        import market_regime
        feed["btc_regime"] = market_regime.detect_market_regime("BTCUSDT", "1h")
    except Exception as e:
        feed["btc_regime"] = {"error": str(e)}

    try:
        feed["derivatives_sentiment"] = coinglass_derivatives.get_derivatives_intelligence("BTC")
    except Exception as e:
        feed["derivatives_sentiment"] = {"error": str(e)}

    # RS Radar Live Watchlist (Prices & Relative Strength vs BTC)
    feed["watchlist"] = get_live_watchlist_rs()

    # Tauric Adversarial Debates (Bull vs Bear)
    try:
        import adversarial_debate
        feed["recent_debates"] = adversarial_debate.load_debate_history(limit=5)
    except Exception:
        feed["recent_debates"] = []

    # Tauric Tri-Perspective Risk Balancing (TradingAgents Protocol)
    try:
        import tri_perspective_risk
        feed["recent_tri_risk"] = tri_perspective_risk.load_tri_risk_history(limit=5)
    except Exception:
        feed["recent_tri_risk"] = []

    # Tauric Sentiment & Social Narrative Scanner
    try:
        import sentiment_narrative_scanner
        feed["sentiment_narrative"] = sentiment_narrative_scanner.get_market_sentiment_narrative_summary()
    except Exception:
        feed["sentiment_narrative"] = {}

    # Paperclip Autonomous Trading Firm Telemetry
    try:
        import paperclip_orchestrator
        feed["paperclip_summary"] = paperclip_orchestrator.get_firm_summary()
    except Exception:
        feed["paperclip_summary"] = {}

    # Nautilus Pre-Trade Risk Engine Telemetry
    try:
        import nautilus_risk_engine
        _, is_daily_halted, dd_info = nautilus_risk_engine.calculate_today_realized_drawdown(current_balance=feed.get("balance_usd", 5000.0))
        feed["nautilus_risk_guard"] = {
            "status": "CIRCUIT_BREAKER_HALTED" if is_daily_halted else "ACTIVE_SAFE",
            "daily_drawdown_info": dd_info,
            "max_spread_pct": nautilus_risk_engine.MAX_ALLOWED_SPREAD_PCT,
            "min_free_margin_ratio": nautilus_risk_engine.MIN_FREE_MARGIN_RATIO,
            "taker_fee_pct": nautilus_risk_engine.ESTIMATED_TAKER_FEE_PCT,
            "maker_fee_pct": nautilus_risk_engine.ESTIMATED_MAKER_FEE_PCT,
            "baseline_slippage_pct": nautilus_risk_engine.DEFAULT_SLIPPAGE_PCT
        }
    except Exception:
        feed["nautilus_risk_guard"] = {"status": "ACTIVE_SAFE"}

    # ATLAS GIC - Soros Reflexivity & Karpathy Autoresearch Telemetry
    try:
        import soros_reflexivity_engine
        feed["soros_reflexivity"] = soros_reflexivity_engine.get_soros_reflexivity_index("BTC")
    except Exception:
        feed["soros_reflexivity"] = {}

    try:
        import self_improve
        feed["autoresearch"] = self_improve.get_autoresearch_summary()
    except Exception:
        feed["autoresearch"] = {}

    feed["last_sync"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    _feed_cache = feed
    _last_feed_fetch_time = now
    return feed

def get_market_intelligence_data(force_refresh=False):
    global _intel_cache, _last_intel_fetch_time
    now = time.time()
    if not force_refresh and _intel_cache is not None and (now - _last_intel_fetch_time) < 3.0:
        return _intel_cache

    try:
        compass = dominance_compass.get_dominance_compass()
    except Exception as e:
        compass = {"error": str(e)}

    try:
        balance = 5000.0
        bal_res = binance_client.send_signed_request("/fapi/v2/balance", method="GET", is_demo=True)
        if bal_res:
            for b in bal_res:
                if b.get("asset") == "USDT":
                    balance = float(b.get("balance", 5000.0))
        pos_res = binance_client.send_signed_request("/fapi/v2/positionRisk", method="GET", is_demo=True)
        active_pos = [p for p in (pos_res or []) if float(p.get("positionAmt", 0)) != 0]
        heat = portfolio_guard.audit_portfolio_heat(active_pos, balance)
    except Exception as e:
        heat = {"error": str(e)}

    try:
        cb_prem = coinbase_premium.get_coinbase_premium_index("BTC")
    except Exception as e:
        cb_prem = {"error": str(e)}

    try:
        derivs = coinglass_derivatives.get_coinglass_sentiment_summary("BTC")
    except Exception as e:
        derivs = {"error": str(e)}

    try:
        liq = liquidity_heatmap.get_liquidity_intelligence("BTC")
    except Exception as e:
        liq = {"error": str(e)}

    # Fincept Terminal Global Macro Intelligence
    try:
        import macro_liquidity
        macro_intel = macro_liquidity.get_macro_liquidity_summary()
    except Exception as e:
        macro_intel = {"error": str(e)}

    # Fincept Terminal Institutional Quant Risk Engine
    try:
        import quant_risk_engine
        quant_risk = quant_risk_engine.get_full_quant_risk_summary(balance_usd=balance, active_positions=active_pos)
    except Exception as e:
        quant_risk = {"error": str(e)}

    # ICT Rejection Block Intelligence (Mean Threshold 50% Wick Reversals)
    try:
        import rejection_block_engine
        rb_btc = market_eyes.fetch_candles("BTC", bar="1H", limit=40)
        rb_intel = rejection_block_engine.get_rejection_block_intelligence("BTCUSDT", rb_btc)
    except Exception as e:
        rb_intel = {"error": str(e)}

    try:
        import fast_scalper
        active_scalps = fast_scalper.scan_all_scalp_opportunities(["BTC", "ETH", "SOL"])
    except Exception:
        active_scalps = []

    try:
        import sentiment_narrative_scanner
        sentiment_intel = sentiment_narrative_scanner.get_market_sentiment_narrative_summary()
    except Exception as e:
        sentiment_intel = {"error": str(e)}

    # Agent Cognitive Memory Engine (rohitg00/agentmemory)
    try:
        import agent_memory_engine
        memory_summary = agent_memory_engine.memory_engine.get_memory_summary()
    except Exception as e:
        memory_summary = {"error": str(e)}

    res_data = {
        "compass": compass,
        "heat": heat,
        "coinbase_premium": cb_prem,
        "derivatives": derivs,
        "liquidity": liq,
        "macro": macro_intel,
        "quant_risk": quant_risk,
        "rejection_blocks": rb_intel,
        "active_scalps": active_scalps,
        "sentiment_narrative": sentiment_intel,
        "memory_summary": memory_summary,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    _intel_cache = res_data
    _last_intel_fetch_time = now
    return res_data

def get_journal_data():
    """
    Aggregates quantitative trade journal data (Akademi Crypto Module 03):
    - Scorecard (Win Rate, Profit Factor, Expectancy, Payoff Ratio, Max Drawdown)
    - Closed Trades Ledger
    - Bot Execution Signals from Trading Desk
    """
    try:
        metrics = trade_journal.calculate_journal_metrics("all")
        ledger = trade_journal.load_trade_ledger()
        executions = trade_journal.load_bot_executions()
    except Exception as e:
        return {"error": str(e)}

    return {
        "metrics": metrics,
        "ledger": ledger,
        "executions": executions,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def get_chart_data(symbol="BTC", bar="1H"):
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")
    raw_candles = market_radar.fetch_candles(sym_clean, bar=bar, limit=120)

    if not raw_candles or len(raw_candles) < 5:
        return {"error": "Failed to fetch candlestick feed"}

    candles = []
    closes = []

    for c in raw_candles:
        # candle format: [ts_ms, open, high, low, close, vol, quoteVol]
        ts_sec = int(int(c[0]) / 1000)
        o = float(c[1])
        h = float(c[2])
        l = float(c[3])
        cl = float(c[4])
        v = float(c[5])
        closes.append(cl)
        candles.append({
            "time": ts_sec,
            "open": o,
            "high": h,
            "low": l,
            "close": cl,
            "volume": v
        })

    current_price = closes[-1] if closes else 0.0

    # Calculate VWAP & Bands
    vwap_series = []
    upper_band_series = []
    lower_band_series = []

    cum_vol = 0.0
    cum_pv = 0.0
    cum_pv_sq = 0.0

    for c in candles:
        typical = (c["high"] + c["low"] + c["close"]) / 3.0
        v = c["volume"]
        cum_vol += v
        cum_pv += typical * v
        cum_pv_sq += (typical ** 2) * v

        if cum_vol > 0:
            vw = cum_pv / cum_vol
            variance = max(0.0, (cum_pv_sq / cum_vol) - (vw ** 2))
            std_dev = (variance ** 0.5)
            vwap_series.append({"time": c["time"], "value": round(vw, 4)})
            upper_band_series.append({"time": c["time"], "value": round(vw + std_dev, 4)})
            lower_band_series.append({"time": c["time"], "value": round(vw - std_dev, 4)})

    # Calculate Volume Profile (POC, VAH, VAL)
    vp = market_eyes.calculate_volume_profile(raw_candles, current_price)

    # 4H Macro Confluence
    macro = topdown_confluence.analyze_macro_structure(sym_clean)

    # FVG Detection
    fvg_zones = []
    for i in range(len(candles) - 1, max(1, len(candles) - 15), -1):
        if candles[i]["low"] > candles[i - 2]["high"]:
            fvg_zones.append({
                "type": "BULLISH_FVG",
                "top": candles[i]["low"],
                "bottom": candles[i - 2]["high"],
                "time": candles[i - 1]["time"]
            })
        elif candles[i]["high"] < candles[i - 2]["low"]:
            fvg_zones.append({
                "type": "BEARISH_FVG",
                "top": candles[i - 2]["low"],
                "bottom": candles[i]["high"],
                "time": candles[i - 1]["time"]
            })

    return {
        "symbol": sym_clean,
        "bar": bar,
        "current_price": current_price,
        "candles": candles,
        "vwap": vwap_series,
        "upper_band": upper_band_series,
        "lower_band": lower_band_series,
        "volume_profile": {
            "vah": vp["vah"] if vp else None,
            "poc": vp["poc"] if vp else None,
            "val": vp["val"] if vp else None
        },
        "macro": macro,
        "fvg_zones": fvg_zones[:3]
    }

class MissionControlHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for seamless local development
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/" or path == "/dashboard" or path == "/index.html":
            if os.path.exists(DASHBOARD_HTML_PATH):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(DASHBOARD_HTML_PATH, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"dashboard.html not found.")
            return

        elif path == "/api/feed":
            data = get_dashboard_feed_data()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/watchlist":
            data = get_live_watchlist_rs()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/dex-radar" or path == "/api/dex_radar":
            import dex_pump_radar
            data = dex_pump_radar.get_latest_dex_radar_state()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/debate":
            import adversarial_debate
            data = adversarial_debate.load_debate_history(limit=15)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/tri_risk":
            import tri_perspective_risk
            data = tri_perspective_risk.load_tri_risk_history(limit=15)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/sentiment":
            import sentiment_narrative_scanner
            data = sentiment_narrative_scanner.get_market_sentiment_narrative_summary()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/paperclip/firm":
            import paperclip_orchestrator
            data = paperclip_orchestrator.get_firm_summary()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/paperclip/tickets":
            import paperclip_orchestrator
            data = paperclip_orchestrator.load_tickets()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/pipeline/macro-onchain" or path == "/api/openbb/pipeline":
            try:
                import open_quant_pipeline
                data = open_quant_pipeline.get_unified_quant_pipeline()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/orderflow":
            try:
                import orderflow_cvd_scalper
                sym = params.get("symbol", ["BTC"])[0]
                data = orderflow_cvd_scalper.get_orderflow_summary(sym)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/orb":
            try:
                import orb_scalper
                sym = params.get("symbol", ["BTC"])[0]
                data = orb_scalper.get_orb_summary(sym)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/klines":
            sym = params.get("symbol", ["BTC"])[0]
            bar = params.get("bar", ["1H"])[0]
            data = get_chart_data(sym, bar)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/backtest":
            sym = params.get("symbol", ["BTC"])[0]
            bar = params.get("bar", ["1H"])[0]
            try:
                candles = int(params.get("candles", params.get("limit", [500]))[0])
            except ValueError:
                candles = 500
            data = quant_backtester.run_backtest(sym, bar=bar, num_candles=candles)
            data.setdefault("success", True)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/market_intelligence":
            data = get_market_intelligence_data()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/journal":
            data = get_journal_data()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/liquidity_depth":
            sym = params.get("symbol", ["BTC"])[0]
            try:
                data = liquidity_heatmap.get_liquidity_intelligence(sym)
            except Exception as e:
                data = {"error": str(e)}
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/strategy/institutional_suite":
            sym = params.get("symbol", ["BTC"])[0]
            bar = params.get("bar", ["1h"])[0]
            try:
                import institutional_quant_strategies
                data = institutional_quant_strategies.scan_all_institutional_strategies(sym, bar=bar)
                data["success"] = True
            except Exception as e:
                data = {"success": False, "error": str(e)}
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/strategy/session_adaptive":
            try:
                import session_adaptive_strategy
                reg = session_adaptive_strategy.get_active_24h_regime()
                data = {"success": True, "active_regime": reg}
            except Exception as e:
                data = {"success": False, "error": str(e)}
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/strategy/crypto_autopilot":
            sym = params.get("symbol", ["BTC"])[0]
            try:
                import crypto_automation_strategies
                data = crypto_automation_strategies.scan_all_crypto_automation_strategies(sym)
                data["success"] = True
            except Exception as e:
                data = {"success": False, "error": str(e)}
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/strategy/prop_desk":
            sym = params.get("symbol", ["BTC"])[0]
            try:
                import prop_desk_strategies
                data = prop_desk_strategies.scan_all_prop_desk_strategies(sym)
                data["success"] = True
            except Exception as e:
                data = {"success": False, "error": str(e)}
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/seasonality/status":
            try:
                import hedge_fund_seasonality_engine
                data = hedge_fund_seasonality_engine.get_dashboard_seasonality_payload()
                data["success"] = True
            except Exception as e:
                data = {"success": False, "error": str(e), "status": "ERROR"}
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/seasonality/evaluate":
            sym = params.get("symbol", ["BTC"])[0]
            try:
                import hedge_fund_seasonality_engine
                data = hedge_fund_seasonality_engine.calculate_seasonality_confluence(sym)
                data["success"] = True
            except Exception as e:
                data = {"success": False, "error": str(e)}
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/risk/pre_trade_audit":
            import nautilus_risk_engine
            sym = params.get("symbol", ["BTC"])[0]
            side = params.get("side", ["BUY"])[0]
            try:
                price = float(params.get("price", [65000.0])[0])
                sl = float(params.get("sl", [64000.0])[0])
                tp = float(params.get("tp", [67000.0])[0])
            except ValueError:
                price, sl, tp = 65000.0, 64000.0, 67000.0
            data = nautilus_risk_engine.validate_pre_trade_order(sym, side, price, sl, tp)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/memory/insights":
            try:
                import agent_memory_engine
                q_sym = params.get("symbol", [None])[0]
                q_query = params.get("query", [None])[0]
                
                if q_query or q_sym:
                    results = agent_memory_engine.memory_engine.hybrid_search(
                        query=q_query or f"{q_sym or ''} setup analysis",
                        symbol=q_sym,
                        limit=6
                    )
                    data = {
                        "success": True,
                        "query": q_query,
                        "symbol": q_sym,
                        "results": results,
                        "summary": agent_memory_engine.memory_engine.get_memory_summary()
                    }
                else:
                    data = {
                        "success": True,
                        "summary": agent_memory_engine.memory_engine.get_memory_summary()
                    }
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/memory/sync_journal":
            try:
                import agent_memory_engine
                res = agent_memory_engine.memory_engine.sync_with_trade_journal()
                data = {
                    "success": True,
                    "result": res,
                    "summary": agent_memory_engine.memory_engine.get_memory_summary()
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/memory/tiered":
            try:
                import agent_memory_engine
                q_sym = params.get("symbol", ["BTC"])[0]
                q_tier = params.get("tier", ["L1"])[0]
                q_setup = params.get("setup", ["SMC Order Block Retest"])[0]
                
                tiered_data = agent_memory_engine.memory_engine.get_tiered_context(symbol=q_sym, tier=q_tier, setup_type=q_setup)
                prompt_text = agent_memory_engine.memory_engine.format_prompt_context(symbol=q_sym, setup_type=q_setup, max_tier=q_tier)
                
                data = {
                    "success": True,
                    "symbol": q_sym,
                    "tier": q_tier,
                    "context": tiered_data,
                    "formatted_prompt": prompt_text
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/macro/fred":
            try:
                import fred_macro_intel
                data = fred_macro_intel.get_macro_liquidity_regime()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "macro_intel": data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/smc/fomo_analysis":
            try:
                import fomo_smc_engine
                q_sym = params.get("symbol", ["BTC"])[0]
                q_bar = params.get("bar", ["1h"])[0]
                q_side = params.get("side", ["BUY"])[0]
                data = fomo_smc_engine.audit_fomo_smc_setup(symbol=q_sym, bar=q_bar, side=q_side)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "analysis": data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/quant/volatility":
            try:
                import timeseries_quant_forecaster
                q_sym = params.get("symbol", ["BTC"])[0]
                q_bar = params.get("bar", ["1h"])[0]
                vol_data = timeseries_quant_forecaster.get_asset_volatility_profile(q_sym, bar=q_bar)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "volatility_profile": vol_data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/adapter/multisource":
            try:
                import multi_source_adapter
                q_sym = params.get("symbol", ["BTC"])[0]
                adapter_data = multi_source_adapter.get_multi_source_summary(q_sym)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "adapter_summary": adapter_data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/quant/autoresearch":
            try:
                import self_improve
                data = self_improve.get_autoresearch_summary()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/quant/reflexivity":
            try:
                import soros_reflexivity_engine
                q_sym = params.get("symbol", ["BTC"])[0]
                data = soros_reflexivity_engine.get_soros_reflexivity_index(q_sym)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "reflexivity": data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/mt5/account":
            try:
                import mt5_client
                data = mt5_client.get_account_summary()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "account": data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/mt5/positions":
            try:
                import mt5_client
                data = mt5_client.get_open_positions()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "positions": data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
        elif path == "/api/transaction_costs":
            try:
                import transaction_cost_guard
                data = transaction_cost_guard.get_transaction_cost_summary()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "transaction_costs": data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/alpha_benchmark":
            try:
                import benchmark_alpha_tracker
                data = benchmark_alpha_tracker.calculate_alpha_metrics()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "alpha_benchmark": data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/monte_carlo/simulate":
            try:
                import monte_carlo_risk_simulator
                q_iter = int(params.get("iterations", [1000])[0])
                data = monte_carlo_risk_simulator.run_monte_carlo_simulation(iterations=q_iter)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "monte_carlo": data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/regime/adaptive":
            try:
                import regime_adaptive_switcher
                q_sym = params.get("symbol", ["BTCUSDT"])[0]
                q_int = params.get("interval", ["1h"])[0]
                data = regime_adaptive_switcher.analyze_regime_state(symbol=q_sym, interval=q_int)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "regime_adaptive": data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/orderbook/sniping":
            try:
                import orderbook_delta_sniper
                q_sym = params.get("symbol", ["BTCUSDT"])[0]
                data = orderbook_delta_sniper.analyze_orderbook_and_delta(symbol=q_sym)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "orderbook_sniping": data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/portfolio/beta_hedge":
            try:
                import portfolio_beta_hedger
                data = portfolio_beta_hedger.evaluate_and_execute_portfolio_hedge(is_demo=True)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "beta_hedge": data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/derivatives/oi_archetype":
            try:
                import coinglass_derivatives
                q_sym = params.get("symbol", ["BTC"])[0]
                data = coinglass_derivatives.get_oi_archetype_and_liquidation_magnets(symbol=q_sym)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "oi_archetype": data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/tv_screener/futures":
            try:
                import tv_screener_adapter
                top_n = int(params.get("top_n", [30])[0])
                data = tv_screener_adapter.scan_binance_futures_universe(top_n=top_n)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "screener_data": data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/tv_screener/summary":
            try:
                import tv_screener_adapter
                q_sym = params.get("symbol", ["BTC"])[0]
                data = tv_screener_adapter.get_tradingview_technical_summary(symbol=q_sym)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "technical_summary": data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/tv_screener/dex_gems":
            try:
                import tv_screener_adapter
                top_n = int(params.get("top_n", [15])[0])
                data = tv_screener_adapter.scan_dex_and_altcoin_gems(top_n=top_n)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "dex_gems": data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/osint/forensics":
            try:
                import crypto_osint_forensics_hub
                hub = crypto_osint_forensics_hub.CryptoOSINTForensicsHub()
                refresh = params.get("refresh", ["false"])[0].lower() == "true"
                intel_file = os.path.join(DATA_DIR, "osint_forensics_intel.json")
                if refresh or not os.path.exists(intel_file):
                    data = hub.run_full_intel_cycle()
                else:
                    with open(intel_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "osint_intel": data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/osint/graph":
            try:
                graph_file = os.path.join(DATA_DIR, "osint_graph_export.json")
                if os.path.exists(graph_file):
                    with open(graph_file, "r", encoding="utf-8") as f:
                        graph_data = json.load(f)
                else:
                    import crypto_osint_forensics_hub
                    hub = crypto_osint_forensics_hub.CryptoOSINTForensicsHub()
                    report = hub.run_full_intel_cycle()
                    graph_data = report.get("flowsint_graph_preview", {})
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "graph": graph_data}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/hyperopt/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "state": _hyperopt_state}).encode("utf-8"))
            return

        elif path == "/api/hyperopt/results":
            res_file = os.path.join(DATA_DIR, "optimized_params.json")
            hist_file = os.path.join(DATA_DIR, "hyperopt_history.json")
            params_data = {}
            hist_data = {}
            if os.path.exists(res_file):
                try:
                    with open(res_file, "r", encoding="utf-8") as f:
                        params_data = json.load(f)
                except Exception:
                    pass
            if os.path.exists(hist_file):
                try:
                    with open(hist_file, "r", encoding="utf-8") as f:
                        hist_data = json.load(f)
                except Exception:
                    pass
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "optimized_params": params_data,
                "latest_history": hist_data
            }).encode("utf-8"))
            return

        elif path == "/api/ml/status":
            try:
                q_sym = params.get("symbol", ["BTC"])[0]
                q_bar = params.get("bar", ["1h"])[0]
                if adaptive_ml_engine:
                    ml_data = adaptive_ml_engine.evaluate_live_market_ml(symbol=q_sym, bar=q_bar)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True, "ml_profile": ml_data}, ensure_ascii=False).encode("utf-8"))
                else:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": "adaptive_ml_engine not available"}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/pairlist/active":
            try:
                if pairlist_pipeline:
                    data = pairlist_pipeline.get_pairlist_telemetry()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True, "pairlist_data": data}, ensure_ascii=False).encode("utf-8"))
                else:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": "pairlist_pipeline not available"}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path in ("/api/dex-radar", "/api/dex_radar"):
            try:
                state_f = os.path.join(DATA_DIR, "dex_radar_state.json")
                if os.path.exists(state_f):
                    with open(state_f, "r", encoding="utf-8") as f:
                        data = json.load(f)
                elif dex_pump_radar:
                    scanner = dex_pump_radar.DexPumpRadar()
                    data = scanner.run_full_scan()
                else:
                    data = {"status": "NO_DATA", "tokens": []}
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ERROR", "error": str(e)}).encode("utf-8"))
            return

        elif path in ("/api/whale-tracker", "/api/whale_tracker"):
            try:
                state_f = os.path.join(DATA_DIR, "whale_tracker_state.json")
                if os.path.exists(state_f):
                    with open(state_f, "r", encoding="utf-8") as f:
                        data = json.load(f)
                elif onchain_whale_tracker:
                    tracker = onchain_whale_tracker.OnChainWhaleTracker()
                    data = tracker.run_full_scan()
                else:
                    data = {"status": "NO_DATA", "live_whale_flows": []}
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ERROR", "error": str(e)}).encode("utf-8"))
            return

        elif path in ("/api/whale-tracker/top-pnl", "/api/whale_tracker/top_pnl"):
            try:
                if onchain_whale_tracker:
                    tracker = onchain_whale_tracker.OnChainWhaleTracker()
                    leaderboard = tracker.get_top_pnl_leaderboard()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True, "leaderboard": leaderboard}, ensure_ascii=False).encode("utf-8"))
                else:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b'{"success": false, "error": "Whale tracker unavailable"}')
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path in ("/api/whale-tracker/auto-discover", "/api/whale_tracker/auto_discover"):
            try:
                if onchain_whale_tracker:
                    tracker = onchain_whale_tracker.OnChainWhaleTracker()
                    discovered = tracker.discover_top_pnl_whales(limit=8)
                    if discovered and telegram_notifier:
                        try:
                            telegram_notifier.notify_smart_money_discovered(discovered[0])
                        except Exception:
                            pass
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True, "discovered": discovered, "count": len(discovered)}, ensure_ascii=False).encode("utf-8"))
                else:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b'{"success": false, "error": "Whale tracker unavailable"}')
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path in ("/api/dex-bridge/status", "/api/dex_bridge/status"):
            try:
                if dex_futures_bridge:
                    engine = dex_futures_bridge.get_bridge_engine()
                    data = engine.get_status_payload()
                else:
                    data = {"status": "UNAVAILABLE", "auto_bridge_enabled": False}
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ERROR", "error": str(e)}).encode("utf-8"))
            return

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len) if content_len > 0 else b"{}"

        try:
            payload = json.loads(post_body.decode("utf-8"))
        except Exception:
            payload = {}

        if path == "/api/whale-tracker/add":
            try:
                addr = payload.get("address")
                lbl = payload.get("label", "Custom Whale")
                chn = payload.get("chain", "solana")
                cat = payload.get("category", "SMART_MONEY")
                if not addr:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b'{"success": false, "error": "Missing address"}')
                    return
                
                tracker = onchain_whale_tracker.OnChainWhaleTracker() if onchain_whale_tracker else None
                if tracker:
                    res = tracker.add_custom_wallet(addr, lbl, chn, cat)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps(res).encode("utf-8"))
                else:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b'{"success": false, "error": "Whale tracker unavailable"}')
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path in ("/api/whale-tracker/auto-discover", "/api/whale_tracker/auto_discover"):
            try:
                if onchain_whale_tracker:
                    tracker = onchain_whale_tracker.OnChainWhaleTracker()
                    limit = int(payload.get("limit", 8))
                    discovered = tracker.discover_top_pnl_whales(limit=limit)
                    if discovered and telegram_notifier:
                        try:
                            telegram_notifier.notify_smart_money_discovered(discovered[0])
                        except Exception:
                            pass
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True, "discovered": discovered, "count": len(discovered)}, ensure_ascii=False).encode("utf-8"))
                else:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b'{"success": false, "error": "Whale tracker unavailable"}')
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/dex-radar/notify_test":
            try:
                sample_token = {
                    "symbol": payload.get("symbol", "SOL_ALPHA"),
                    "name": payload.get("name", "Solana Alpha Breakout"),
                    "chain": payload.get("chain", "SOLANA"),
                    "price_usd": float(payload.get("price_usd", 0.0452)),
                    "volume_5m": float(payload.get("volume_5m", 38500)),
                    "liquidity_usd": float(payload.get("liquidity_usd", 92000)),
                    "alpha_score": int(payload.get("alpha_score", 88)),
                    "safety_score": int(payload.get("safety_score", 94)),
                    "rug_risk": "SAFE_AUDITED",
                    "dex_url": payload.get("dex_url", "https://dexscreener.com/solana")
                }
                res = telegram_notifier.notify_dex_pump_alert(sample_token)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "telegram_response": res}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/whale-tracker/notify_test":
            try:
                sample_whale = {
                    "symbol": payload.get("symbol", "RAY"),
                    "chain": payload.get("chain", "SOLANA"),
                    "action": payload.get("action", "WHALE_BUY_SWEEP"),
                    "volume_5m_usd": float(payload.get("volume_5m_usd", 64500)),
                    "avg_ticket_usd": float(payload.get("avg_ticket_usd", 12800)),
                    "sentiment": payload.get("sentiment", "AGGRESSIVE_ACCUMULATION"),
                    "dex_url": payload.get("dex_url", "https://dexscreener.com/solana")
                }
                res = telegram_notifier.notify_whale_inflow_alert(sample_whale)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "telegram_response": res}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path in ("/api/dex-bridge/toggle", "/api/dex_bridge/toggle"):
            try:
                engine = dex_futures_bridge.get_bridge_engine() if dex_futures_bridge else None
                if engine:
                    en = payload.get("enabled", None)
                    res_state = engine.toggle_bridge(en)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True, "auto_bridge_enabled": res_state}).encode("utf-8"))
                else:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b'{"success": false, "error": "Bridge engine unavailable"}')
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path in ("/api/dex-bridge/circuit_breaker_test", "/api/dex_bridge/circuit_breaker_test"):
            try:
                shock_sample = {
                    "reason": "MANUAL_TEST_FLASH_CRASH_SHOCK",
                    "btc_15m_return_pct": -3.45,
                    "btc_5m_return_pct": -1.82,
                    "btc_price": 64200.50
                }
                res = telegram_notifier.notify_black_swan_circuit_breaker(shock_sample)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "telegram_response": res}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path in ("/api/dex-bridge/bridge_test", "/api/dex_bridge/bridge_test"):
            try:
                token_sample = {
                    "symbol": payload.get("symbol", "PEPE"),
                    "name": "Pepe Meme Alpha",
                    "chain": "ETHEREUM",
                    "price_usd": 0.0000104,
                    "volume_5m": 125000,
                    "liquidity_usd": 450000,
                    "alpha_score": 85,
                    "safety_score": 92,
                    "net_whale_flow_usd": 15400
                }
                engine = dex_futures_bridge.get_bridge_engine() if dex_futures_bridge else None
                if engine:
                    res = engine.evaluate_and_bridge_token(token_sample)
                    if res.get("bridged"):
                        telegram_notifier.notify_auto_bridge_execution({
                            "token": "PEPE",
                            "contract": res.get("futures_contract", "1000PEPEUSDT"),
                            "alpha_score": 85,
                            "safety_score": 92,
                            "leverage": 20,
                            "mark_price": 0.0000104
                        })
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True, "bridge_result": res}).encode("utf-8"))
                else:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b'{"success": false, "error": "Bridge engine unavailable"}')
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        if path == "/api/memory/reflect":
            try:
                import agent_memory_engine
                reflection = agent_memory_engine.memory_engine.reflect_on_closed_trade(payload)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "reflection": reflection}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/mt5/trade":
            try:
                import mt5_client
                sym = payload.get("symbol", "BTC")
                side = payload.get("side", "BUY")
                vol = payload.get("volume")
                risk = float(payload.get("risk_usd", 50.0))
                sl = payload.get("sl")
                tp = payload.get("tp")
                comment = payload.get("comment", "BelajarKripto Desk")
                
                res = mt5_client.place_signal_order(
                    symbol=sym,
                    side=side,
                    volume=vol,
                    risk_usd=risk,
                    sl_price=sl,
                    tp_price=tp,
                    comment=comment
                )
                self.send_response(200 if res.get("success") else 400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/mt5/close":
            try:
                import mt5_client
                ticket = int(payload.get("ticket", 0))
                res = mt5_client.close_position_by_ticket(ticket)
                self.send_response(200 if res.get("success") else 400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        if path == "/api/action/close":
            sym = payload.get("symbol")
            ticket = payload.get("ticket")
            backend = payload.get("backend")

            # Check if this is an MT5 position
            if backend == "MT5" or ticket:
                try:
                    import mt5_client
                    t_id = int(ticket) if ticket else 0
                    if not t_id and sym:
                        # Find ticket by symbol
                        mt5_open = mt5_client.get_open_positions()
                        for p in mt5_open:
                            if p.get("symbol") == sym:
                                t_id = p.get("ticket")
                                break
                    if t_id:
                        res = mt5_client.close_position_by_ticket(t_id)
                        if res.get("success"):
                            self.send_response(200)
                            self.send_header("Content-Type", "application/json")
                            self.end_headers()
                            self.wfile.write(json.dumps({"success": True, "message": f"MT5 #{t_id} closed"}).encode("utf-8"))
                            return
                        else:
                            self.send_response(200)
                            self.send_header("Content-Type", "application/json")
                            self.end_headers()
                            self.wfile.write(json.dumps({"success": False, "error": f"MT5 Error: {res.get('error')}"}).encode("utf-8"))
                            return
                except Exception as e:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": f"MT5 Exception: {str(e)}"}).encode("utf-8"))
                    return

            if not sym:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "Missing symbol or ticket"}')
                return

            target_sym = sym.upper() if sym.upper().endswith("USDT") else f"{sym.upper()}USDT"
            pos = binance_client.send_signed_request("/fapi/v2/positionRisk", method="GET", is_demo=True)
            match = next((p for p in (pos or []) if p["symbol"] == target_sym and float(p.get("positionAmt", 0)) != 0), None)

            if not match:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'{"error": "Position not found"}')
                return

            amt = float(match.get("positionAmt", 0))
            close_side = "SELL" if amt > 0 else "BUY"
            res = binance_client.send_signed_request(
                "/fapi/v1/order",
                method="POST",
                params={
                    "symbol": target_sym,
                    "side": close_side,
                    "type": "MARKET",
                    "quantity": abs(amt),
                    "reduceOnly": "true"
                },
                is_demo=True
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "result": res}).encode("utf-8"))
            return

        elif path == "/api/action/closeall":
            closed_count = 0
            errors = []

            # 1. Close MT5 positions
            try:
                import mt5_client
                mt5_res = mt5_client.close_all_positions()
                for r in mt5_res:
                    if r.get("success"):
                        closed_count += 1
                    else:
                        errors.append(f"MT5 #{r.get('ticket')}: {r.get('error')}")
            except Exception as e:
                errors.append(f"MT5: {str(e)}")

            # 2. Close Binance Futures positions
            try:
                pos = binance_client.send_signed_request("/fapi/v2/positionRisk", method="GET", is_demo=True)
                active = [p for p in (pos or []) if float(p.get("positionAmt", 0)) != 0]
                for p in active:
                    amt = float(p.get("positionAmt", 0))
                    side = "SELL" if amt > 0 else "BUY"
                    res = binance_client.send_signed_request(
                        "/fapi/v1/order",
                        method="POST",
                        params={
                            "symbol": p["symbol"],
                            "side": side,
                            "type": "MARKET",
                            "quantity": abs(amt),
                            "reduceOnly": "true"
                        },
                        is_demo=True
                    )
                    if res and not res.get("code"):
                        closed_count += 1
                    else:
                        errors.append(f"Binance {p['symbol']}: {res.get('msg', 'Error')}")
            except Exception as e:
                errors.append(f"Binance: {str(e)}")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "closed_count": closed_count,
                "errors": errors
            }).encode("utf-8"))
            return

        elif path == "/api/action/lock_be":
            sym = payload.get("symbol")
            if not sym:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "Missing symbol"}')
                return

            target_sym = sym.upper() if sym.upper().endswith("USDT") else f"{sym.upper()}USDT"
            pos = binance_client.send_signed_request("/fapi/v2/positionRisk", method="GET", is_demo=True)
            match = next((p for p in (pos or []) if p["symbol"] == target_sym and float(p.get("positionAmt", 0)) != 0), None)

            if not match:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'{"error": "Position not found"}')
                return

            amt = float(match.get("positionAmt", 0))
            side = "BUY" if amt > 0 else "SELL"
            entry_p = float(match.get("entryPrice", 0))
            be_p = trade_manager.calculate_breakeven_price(target_sym, side, entry_p)
            success, algo_res = trade_manager.update_binance_stop_loss(target_sym, side, be_p, is_demo=True)

            if success:
                meta = trade_manager.load_trade_metadata()
                if target_sym in meta:
                    meta[target_sym]["breakeven_locked"] = True
                    meta[target_sym]["current_sl"] = be_p
                    trade_manager.save_trade_metadata(meta)
                try:
                    telegram_notifier.notify_breakeven_locked(
                        symbol=target_sym,
                        side=side,
                        entry_price=entry_p,
                        be_price=be_p,
                        current_pnl=float(match.get("unRealizedProfit", 0)),
                        is_demo=True
                    )
                except Exception:
                    pass

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": success, "be_price": be_p}).encode("utf-8"))
            return

        elif path == "/api/action/partial_tp":
            sym = payload.get("symbol")
            if not sym:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"success": false, "error": "Missing symbol"}')
                return

            res = trade_manager.execute_manual_partial_tp(sym, is_demo=True)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        elif path == "/api/action/sync_binance":
            try:
                new_trades = trade_journal.sync_binance_history(is_demo=True, limit=50)
                total_trades = len(trade_journal.load_trade_ledger())
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "new_trades": new_trades,
                    "total_trades": total_trades
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": str(e)
                }).encode("utf-8"))
            return

        elif path == "/api/ai/ask":
            query = payload.get("query", "")
            if not query:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "Query parameter missing"}')
                return

            try:
                feed = get_dashboard_feed_data()
                ctx = {
                    "balance_usd": feed.get("balance_usd", 5000.0),
                    "positions": feed.get("positions", []),
                    "mode": feed.get("mode", "HYBRID"),
                    "news_shield": feed.get("news_shield", {})
                }
                ans = ai_risk_officer.answer_trader_query(query, ctx)
                creds = ai_risk_officer.get_ai_credentials()
                res = {"success": True, "answer": ans, "provider": creds.get("provider")}
            except Exception as e:
                res = {"success": False, "error": str(e)}

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/action/closeall":
            pos = binance_client.send_signed_request("/fapi/v2/positionRisk", method="GET", is_demo=True)
            active = [p for p in (pos or []) if float(p.get("positionAmt", 0)) != 0]
            for p in active:
                amt = float(p.get("positionAmt", 0))
                binance_client.send_signed_request(
                    "/fapi/v1/order",
                    method="POST",
                    params={
                        "symbol": p["symbol"],
                        "side": "SELL" if amt > 0 else "BUY",
                        "type": "MARKET",
                        "quantity": abs(amt),
                        "reduceOnly": "true"
                    },
                    is_demo=True
                )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "closed_count": len(active)}).encode("utf-8"))
            return

        elif path == "/api/hyperopt/run":
            if _hyperopt_state["is_running"]:
                self.send_response(429)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Hyperopt optimization is already running"}).encode("utf-8"))
                return

            sym = payload.get("symbol", "BTC")
            strat = payload.get("strategy", "fast_scalper")
            bar = payload.get("bar", "1H")
            trials = int(payload.get("trials", 40))
            target = payload.get("target", "sortino")

            def _bg_run():
                global _hyperopt_state
                _hyperopt_state["is_running"] = True
                _hyperopt_state["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                _hyperopt_state["error"] = None
                try:
                    if hyperopt_optimizer:
                        res = hyperopt_optimizer.run_hyperopt(
                            symbol=sym,
                            strategy=strat,
                            bar=bar,
                            target_count=500,
                            trials=trials,
                            target=target
                        )
                        _hyperopt_state["last_result"] = res
                    else:
                        _hyperopt_state["error"] = "hyperopt_optimizer module not available"
                except Exception as ex:
                    _hyperopt_state["error"] = str(ex)
                finally:
                    _hyperopt_state["is_running"] = False

            t = threading.Thread(target=_bg_run, daemon=True)
            t.start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "message": f"Optimization started in background for {sym} ({strat}) with {trials} trials",
                "symbol": sym,
                "strategy": strat
            }).encode("utf-8"))
            return

        elif path == "/api/ml/retrain":
            sym = payload.get("symbol", "BTC")
            bar = payload.get("bar", "1h")
            count = int(payload.get("candles", 500))

            def _bg_retrain():
                if adaptive_ml_engine:
                    adaptive_ml_engine.train_and_cache_model(symbol=sym, bar=bar, candle_count=count)

            t = threading.Thread(target=_bg_retrain, daemon=True)
            t.start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "message": f"Rolling ML retraining started in background for {sym} [{bar}] ({count} candles)",
                "symbol": sym,
                "bar": bar
            }).encode("utf-8"))
            return

        elif path == "/api/pairlist/refresh":
            top_n = int(payload.get("top_n", 8))

            def _bg_pairlist():
                if pairlist_pipeline:
                    pipeline = pairlist_pipeline.DynamicPairlistPipeline()
                    pipeline.execute()

            t = threading.Thread(target=_bg_pairlist, daemon=True)
            t.start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "message": "Dynamic Pairlist Pipeline execution triggered in background"
            }).encode("utf-8"))
            return

        elif path == "/api/action/toggle_pause":
            state = telegram_notifier.load_desk_state()
            new_paused = not state.get("paused", False)
            state["paused"] = new_paused
            telegram_notifier.save_desk_state(state)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "is_paused": new_paused}).encode("utf-8"))
            return

        elif path == "/api/action/set_mode":
            state = telegram_notifier.load_desk_state()
            requested_mode = (payload.get("mode") or "").upper()
            modes_cycle = ["HYBRID", "SCALP", "SWING"]
            if requested_mode in modes_cycle:
                new_mode = requested_mode
            else:
                curr = state.get("mode", "HYBRID").upper()
                next_idx = (modes_cycle.index(curr) + 1) % len(modes_cycle) if curr in modes_cycle else 0
                new_mode = modes_cycle[next_idx]

            state["mode"] = new_mode
            state["strategy_focus"] = "FAST_SCALP_HYBRID" if new_mode == "HYBRID" else ("FAST_SCALP" if new_mode == "SCALP" else "SWING_INTRADAY")
            telegram_notifier.save_desk_state(state)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "mode": new_mode}).encode("utf-8"))
            return
        elif path == "/api/action/sync_binance":
            try:
                count = trade_journal.sync_binance_history(limit=1000)
                total = len(trade_journal.load_journal())
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "new_trades": count, "total_trades": total}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path in ("/api/paperclip/action", "/api/firm/heartbeat", "/api/firm/action"):
            try:
                import paperclip_orchestrator
                action_type = payload.get("action", "trigger_heartbeat" if "heartbeat" in path else "board_approve")
                ticket_id = payload.get("ticket_id")
                note = payload.get("note", "Dashboard Board Action")
                user = payload.get("user", "Chairman (Web Board)")

                res = {"success": False, "error": "Unknown action"}
                if action_type == "board_approve" and ticket_id:
                    t = paperclip_orchestrator.board_approve_ticket(ticket_id, board_user=user, note=note)
                    res = {"success": True, "ticket": t}
                elif action_type == "board_reject" and ticket_id:
                    t = paperclip_orchestrator.board_reject_ticket(ticket_id, board_user=user, reason=note)
                    res = {"success": True, "ticket": t}
                elif action_type == "toggle_circuit_breaker":
                    cb = paperclip_orchestrator.toggle_circuit_breaker(reason=note)
                    res = {"success": True, "circuit_breaker": cb}
                elif action_type == "create_ticket":
                    sym = payload.get("symbol", "SOLUSDT")
                    strat = payload.get("strategy", "Mulham Rectangle Scalper (M15)")
                    side = payload.get("side", "BUY")
                    t = paperclip_orchestrator.create_ticket(sym, strat, side, created_by=user, payload=payload.get("payload", {}))
                    res = {"success": True, "ticket": t}
                elif action_type == "trigger_heartbeat":
                    agent_id = payload.get("agent_id", "market_eyes_screener")
                    paperclip_orchestrator.record_agent_heartbeat(agent_id)
                    res = {"success": True, "agent_id": agent_id}

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path in ("/api/webhook/tradingview", "/api/action/manual_entry", "/api/order/manual_entry"):
            """
            TradingView External Signal Gateway:
            Receives JSON alerts from TradingView Pine Script / Alerts.
            Validates with internal Risk Guardrails (News, Dominance, Heat) before execution.
            """
            try:
                raw_sym = payload.get("symbol") or payload.get("ticker")
                raw_action = (payload.get("action") or payload.get("side") or payload.get("order_action") or "").upper()
                price = float(payload.get("price") or payload.get("close") or 0.0)
                sl = float(payload.get("sl") or payload.get("stop_loss") or 0.0)
                tp = float(payload.get("tp") or payload.get("take_profit") or 0.0)
                strategy = payload.get("strategy") or "TradingView Alert"
                is_demo = payload.get("is_demo", True)

                if not raw_sym or not raw_action:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": "Missing symbol or action in TradingView payload"}).encode("utf-8"))
                    return

                clean_sym = str(raw_sym).split(":")[-1].replace("/", "").replace("-", "").replace("_", "").upper().strip()
                for suffix in [".PERP", ".P", "PERP"]:
                    if clean_sym.endswith(suffix):
                        clean_sym = clean_sym[:-len(suffix)]
                        break
                if clean_sym.endswith("USDT"):
                    base_sym = clean_sym[:-4]
                else:
                    base_sym = clean_sym
                target_sym = f"{base_sym}USDT"
                side = "BUY" if raw_action in ["BUY", "LONG"] else "SELL"

                # 1. Check News Blackout Guardrail
                is_blk, blk_reason, _ = macro_news_shield.audit_news_blackout(buffer_minutes=30)
                if is_blk:
                    self.send_response(423)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": f"Macro News Blackout Active: {blk_reason}"}).encode("utf-8"))
                    return

                # 2. Check Active Positions & Directional Heat
                pos = binance_client.send_signed_request("/fapi/v2/positionRisk", method="GET", is_demo=is_demo)
                active_positions = [p for p in (pos or []) if float(p.get("positionAmt", 0)) != 0]
                if len(active_positions) >= 3:
                    self.send_response(429)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": "Max open positions (3) reached. Margin guarded."}).encode("utf-8"))
                    return

                # 3. Check live price if not provided
                if price <= 0:
                    ticker_data = market_eyes.fetch_ticker_data(base_sym)
                    price = float(ticker_data.get("price", 0.0)) if ticker_data else 0.0

                if price <= 0:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": f"Unable to fetch live price for {target_sym}"}).encode("utf-8"))
                    return

                # Dynamic SL if not given
                r_dist = abs(price - sl) if sl > 0 else 0.0
                if sl <= 0 or r_dist <= 0:
                    buf = market_structure.get_asset_sweep_buffer(target_sym)
                    sl = round(price * (1.0 - buf) if side == "BUY" else price * (1.0 + buf), 4)
                    r_dist = abs(price - sl)

                # Dynamic TP if not given (Min 1:2.5 R:R)
                if tp <= 0:
                    tp = round(price + (r_dist * 2.5) if side == "BUY" else price - (r_dist * 2.5), 4)

                # 4. Financials & Position Sizing
                import trading_desk
                bal_usd, avail_usd = trading_desk.get_account_financials(is_demo=is_demo)
                kelly_risk, _ = trading_desk.get_adaptive_kelly_risk_pct(base_risk_pct=1.5)
                cold_mult = trading_desk.get_drawdown_risk_multiplier(lookback_trades=2)
                eff_risk = round(kelly_risk * cold_mult, 2)

                risk_budget = bal_usd * (eff_risk / 100.0)
                sl_pct = abs(price - sl) / price
                pos_usd = min(risk_budget / max(sl_pct, 0.005), avail_usd * 0.75 * 5.0)
                raw_qty = pos_usd / price
                qty = float(binance_client.format_qty_precision(target_sym, raw_qty, is_demo=is_demo))
                is_valid_f, adj_qty, _ = binance_client.validate_order_filters(target_sym, qty, price, is_demo=is_demo)
                if not is_valid_f and adj_qty > 0:
                    qty = adj_qty

                # 5. Place Futures Order via Limit-Chase (Maker fee savings)
                order_res = binance_client.place_futures_order(
                    symbol=target_sym,
                    side=side,
                    quantity=qty,
                    leverage=int(data.get("leverage") or os.getenv("DEFAULT_LEVERAGE", 20)),
                    sl=sl,
                    tp=tp,
                    is_demo=is_demo,
                    exec_mode="LIMIT_CHASE"
                )

                if order_res and order_res.get("orderId"):
                    trade_manager.record_trade_entry(
                        symbol=target_sym,
                        side=side,
                        entry_price=price,
                        sl_price=sl,
                        tp_price=tp,
                        risk_budget_usd=risk_budget,
                        quantity=qty,
                        is_scalp=True,
                        ai_thesis=f"External TradingView Webhook: {strategy}"
                    )
                    try:
                        telegram_notifier.notify_trade_opened(
                            {
                                "symbol": target_sym,
                                "side": "LONG" if side == "BUY" else "SHORT",
                                "price": price,
                                "sl": sl,
                                "tp": tp,
                                "rr": abs(tp - price) / r_dist if r_dist > 0 else 2.5,
                                "reason": f"📡 TRADINGVIEW WEBHOOK: {strategy}"
                            },
                            quantity=qty,
                            risk_budget_usd=risk_budget,
                            is_demo=is_demo
                        )
                    except Exception:
                        pass

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": True,
                        "orderId": order_res.get("orderId"),
                        "symbol": target_sym,
                        "side": side,
                        "quantity": qty,
                        "price": price,
                        "sl": sl,
                        "tp": tp,
                        "strategy": strategy
                    }).encode("utf-8"))
                    return
                else:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": "Order placement rejected by Binance"}).encode("utf-8"))
                    return
            except Exception as tv_err:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(tv_err)}).encode("utf-8"))
                return

        self.send_response(404)
        self.end_headers()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address):
        """Silently suppress Windows client socket drops (WinError 10053/10054/BrokenPipe)."""
        exc_type, exc_val, _ = sys.exc_info()
        if exc_type in (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            return
        if hasattr(exc_val, "winerror") and exc_val.winerror in (10053, 10054, 10038):
            return
        super().handle_error(request, client_address)

def kill_stale_port_holder(port):
    """Kills any previous stale process listening on the dashboard port."""
    try:
        import subprocess
        out = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode('utf-8', errors='ignore')
        my_pid = os.getpid()
        for line in out.splitlines():
            if "LISTENING" in line:
                parts = line.strip().split()
                pid = int(parts[-1])
                if pid != my_pid:
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
                    time.sleep(0.5)
    except Exception:
        pass

def run_server(port=PORT):
    os.chdir(ROOT_DIR)
    kill_stale_port_holder(port)
    try:
        with ThreadedTCPServer(("", port), MissionControlHandler) as httpd:
            print("=" * 65)
            print(f"       🖥️  MISSION CONTROL DASHBOARD SERVER ONLINE")
            print(f"       🌐  URL: http://localhost:{port}")
            print(f"       📊  Feed: http://localhost:{port}/api/feed")
            print("=" * 65)
            httpd.serve_forever()
    except OSError as e:
        if "Address already in use" in str(e) or e.errno == 10048:
            kill_stale_port_holder(port)
            time.sleep(1)
            with ThreadedTCPServer(("", port), MissionControlHandler) as httpd:
                httpd.serve_forever()
        else:
            raise e

if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else PORT
    run_server(p)

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

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}

_feed_cache = None
_last_feed_fetch_time = 0

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

    # Get fresh positions and balance if available (Prioritize MT5 if connected)
    try:
        import mt5_client
        mt5_acc = mt5_client.get_account_summary()
        if mt5_acc.get("connected"):
            feed["balance_usd"] = float(mt5_acc.get("balance", 100000.0))
            feed["equity_usd"] = float(mt5_acc.get("equity", 100000.0))
            feed["execution_backend"] = "MetaTrader 5 (Demo)"
            feed["mt5_login"] = mt5_acc.get("login")
            feed["mt5_server"] = mt5_acc.get("server")
            
            mt5_positions = mt5_client.get_open_positions()
            if mt5_positions:
                pos_list = []
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
                        "backend": "MT5"
                    })
                feed["positions"] = pos_list
        else:
            balance = binance_client.send_signed_request("/fapi/v2/balance", method="GET", is_demo=True)
            if balance:
                for b in balance:
                    if b.get("asset") == "USDT":
                        feed["balance_usd"] = float(b.get("balance", 0))

            pos = binance_client.send_signed_request("/fapi/v2/positionRisk", method="GET", is_demo=True)
            if pos:
                active = [p for p in pos if float(p.get("positionAmt", 0)) != 0]
                pos_list = []
                for p in active:
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
                        "opened_at": t_meta.get("opened_at", "")
                    })
                feed["positions"] = pos_list
    except Exception:
        pass

    # Directional heat overview
    bal_val = feed.get("balance_usd", 100000.0)
    try:
        cur_pos = feed.get("positions", [])
        feed["heat"] = portfolio_guard.audit_portfolio_heat(cur_pos, bal_val)
    except Exception:
        pass

    cur_mode = state.get("mode", "HYBRID").upper()
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

def get_market_intelligence_data():
    """
    Aggregates live market intelligence:
    - 2D Compass (BTC.D, USDT.D, Quadrant)
    - Directional Heat (Long/Short ratio, cap)
    - Coinbase Premium Index (Wall St vs Retail)
    - Coinalyze / Coinglass Derivatives
    """
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

    return {
        "compass": compass,
        "heat": heat,
        "coinbase_premium": cb_prem,
        "derivatives": derivs,
        "liquidity": liq,
        "macro": macro_intel,
        "quant_risk": quant_risk,
        "rejection_block": rb_intel,
        "active_scalps": active_scalps,
        "sentiment_narrative": sentiment_intel,
        "agent_memory": memory_summary,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

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

        elif path == "/api/paperclip/action":
            try:
                import paperclip_orchestrator
                action_type = payload.get("action")
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

        elif path == "/api/webhook/tradingview":
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
                    leverage=5,
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

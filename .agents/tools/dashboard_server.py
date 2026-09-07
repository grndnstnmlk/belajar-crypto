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

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}

_feed_cache = None
_last_feed_fetch_time = 0

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

    # Get fresh positions and balance if available
    try:
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

            # Directional heat overview
            bal_val = feed.get("balance_usd", 5000.0)
            try:
                feed["heat"] = portfolio_guard.audit_portfolio_heat(active, bal_val)
            except Exception:
                pass
    except Exception:
        pass

    feed["is_paused"] = state.get("paused", False)
    feed["mode"] = state.get("mode", "SWING")
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

    return {
        "compass": compass,
        "heat": heat,
        "coinbase_premium": cb_prem,
        "derivatives": derivs,
        "liquidity": liq,
        "macro": macro_intel,
        "quant_risk": quant_risk,
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
    raw_candles = market_eyes.fetch_candles(sym_clean, bar=bar, limit=120)

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
                    "mode": feed.get("mode", "SWING"),
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
            requested_mode = payload.get("mode")
            if requested_mode in ["SCALP", "SWING"]:
                new_mode = requested_mode
            else:
                new_mode = "SCALP" if state.get("mode", "SWING") == "SWING" else "SWING"
            state["mode"] = new_mode
            telegram_notifier.save_desk_state(state)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "mode": new_mode}).encode("utf-8"))
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

        self.send_response(404)
        self.end_headers()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

def run_server(port=PORT):
    os.chdir(ROOT_DIR)
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
            print(f"Port {port} sedang digunakan. Mencoba port {port+1}...")
            run_server(port + 1)
        else:
            raise e

if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else PORT
    run_server(p)

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

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}

def get_dashboard_feed_data():
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
            feed["positions"] = [
                {
                    "symbol": p["symbol"],
                    "side": "LONG" if float(p.get("positionAmt", 0)) > 0 else "SHORT",
                    "quantity": abs(float(p.get("positionAmt", 0))),
                    "entry_price": float(p.get("entryPrice", 0)),
                    "mark_price": float(p.get("markPrice", 0)),
                    "pnl_usd": float(p.get("unRealizedProfit", 0)),
                    "leverage": int(p.get("leverage", 5)),
                    "breakeven_locked": meta.get(p["symbol"], {}).get("breakeven_locked", False),
                    "trailing_r": meta.get(p["symbol"], {}).get("trailing_r_locked", 0.0),
                    "sl": meta.get(p["symbol"], {}).get("current_sl"),
                    "tp": meta.get(p["symbol"], {}).get("tp")
                }
                for p in active
            ]
    except Exception:
        pass

    feed["is_paused"] = state.get("paused", False)
    feed["last_sync"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return feed

def get_chart_data(symbol="BTC", bar="1H"):
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")
    inst_id_spot = f"{sym_clean}-USDT"
    candles_url = f"https://www.okx.com/api/v5/market/candles?instId={inst_id_spot}&bar={bar}&limit=120"
    res = market_eyes.fetch_json(candles_url)

    if not res or res.get("code") != "0" or not res.get("data"):
        return {"error": "Failed to fetch candlestick feed"}

    raw_candles = list(reversed(res["data"]))
    candles = []
    closes = []

    for c in raw_candles:
        # OKX candle format: [ts, open, high, low, close, vol, volCcy, volCcyQuote, confirm]
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
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path in ["/", "/index.html", "/dashboard"]:
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
                candles = int(params.get("candles", [500])[0])
            except ValueError:
                candles = 500
            data = quant_backtester.run_backtest(sym, bar=bar, num_candles=candles)
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

        self.send_response(404)
        self.end_headers()

def run_server(port=PORT):
    os.chdir(ROOT_DIR)
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", port), MissionControlHandler) as httpd:
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

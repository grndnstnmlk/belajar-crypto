"""
Binance Demo & Live Futures Trading Client (Multi-Account Enabled)
Supports Binance Futures Testnet (Demo Trading) & Live USDⓈ-M Futures.
Bypasses regional SSL blocks via native HTTPS HMAC-SHA256 engine.
"""

import argparse
from decimal import Decimal, ROUND_DOWN
import hashlib
import hmac
import json
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(TOOLS_DIR)), ".env")

# SSL Context to prevent Windows regional certificate verification blocks
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded"
}

_EXCHANGE_INFO_CACHE = {}

def sanitize_email_suffix(email):
    return re.sub(r"[^a-zA-Z0-9]", "_", email.upper())

def parse_env_file():
    env_vars = {}
    if os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_vars[k.strip()] = v.strip().strip('"').strip("'")
        except Exception:
            pass
    return env_vars

def resolve_credentials(user_email=None, is_demo=True):
    env_vars = parse_env_file()
    active_user = env_vars.get("ACTIVE_USER", "dxmade@gmail.com")
    target_user = user_email.strip() if user_email else active_user
    suffix = sanitize_email_suffix(target_user)

    if is_demo:
        key = env_vars.get(f"BINANCE_DEMO_API_KEY_{suffix}") or env_vars.get("BINANCE_DEMO_API_KEY")
        secret = env_vars.get(f"BINANCE_DEMO_API_SECRET_{suffix}") or env_vars.get("BINANCE_DEMO_API_SECRET")
        base_url = "https://testnet.binancefuture.com"
        mode_label = "🟡 DEMO TRADING (Futures Testnet - Bebas Risiko)"
    else:
        key = env_vars.get(f"BINANCE_API_KEY_{suffix}") or env_vars.get("BINANCE_API_KEY")
        secret = env_vars.get(f"BINANCE_API_SECRET_{suffix}") or env_vars.get("BINANCE_API_SECRET")
        base_url = "https://fapi.binance.com"
        mode_label = "🔴 LIVE TRADING (Uang Riil)"

    proxy = env_vars.get("BINANCE_PROXY")
    return target_user, key, secret, base_url, mode_label, proxy

SERVER_TIME_OFFSETS = {}

def get_server_time_offset(base_url):
    global SERVER_TIME_OFFSETS
    if base_url in SERVER_TIME_OFFSETS:
        return SERVER_TIME_OFFSETS[base_url]
    try:
        url = f"{base_url}/fapi/v1/time"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=5, context=SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            st = int(data.get("serverTime", 0))
            if st:
                offset = st - int(time.time() * 1000)
                SERVER_TIME_OFFSETS[base_url] = offset
                return offset
    except Exception:
        pass
    return 0

def get_exchange_info(symbol=None, is_demo=True, force_refresh=False):
    """
    Retrieves and caches Binance Futures symbol specifications (LOT_SIZE, PRICE_FILTER, MIN_NOTIONAL).
    Caches to disk for 24 hours to eliminate REST latency overhead.
    """
    global _EXCHANGE_INFO_CACHE
    target_user, key, secret, base_url, mode_label, proxy = resolve_credentials(None, is_demo)
    cache_key = "demo" if is_demo else "live"

    # 1. In-memory cache
    if not force_refresh and cache_key in _EXCHANGE_INFO_CACHE:
        data = _EXCHANGE_INFO_CACHE[cache_key]
        if symbol:
            return data.get(symbol.upper().replace("-", "").replace("/", "").replace("_", ""))
        return data

    # 2. Disk cache (< 24h)
    os.makedirs(DATA_DIR, exist_ok=True)
    disk_file = os.path.join(DATA_DIR, f"binance_exchange_info_{cache_key}.json")
    if not force_refresh and os.path.exists(disk_file):
        try:
            mtime = os.path.getmtime(disk_file)
            if time.time() - mtime < 86400:
                with open(disk_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    _EXCHANGE_INFO_CACHE[cache_key] = data
                    if symbol:
                        return data.get(symbol.upper().replace("-", "").replace("/", "").replace("_", ""))
                    return data
        except Exception:
            pass

    # 3. Fetch from Binance
    try:
        url = f"{base_url}/fapi/v1/exchangeInfo"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8, context=SSL_CTX) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            parsed_symbols = {}
            for s in raw.get("symbols", []):
                sym_name = s.get("symbol")
                status = s.get("status")
                price_prec = int(s.get("pricePrecision", 2))
                qty_prec = int(s.get("quantityPrecision", 2))

                tick_size = "0.01"
                min_price = "0.01"
                max_price = "1000000"
                min_qty = "0.001"
                step_size = "0.001"
                min_notional = "5.0"

                for f in s.get("filters", []):
                    f_type = f.get("filterType")
                    if f_type == "PRICE_FILTER":
                        tick_size = f.get("tickSize", tick_size)
                        min_price = f.get("minPrice", min_price)
                        max_price = f.get("maxPrice", max_price)
                    elif f_type == "LOT_SIZE":
                        min_qty = f.get("minQty", min_qty)
                        step_size = f.get("stepSize", step_size)
                    elif f_type == "MIN_NOTIONAL":
                        min_notional = f.get("notional", min_notional)

                parsed_symbols[sym_name] = {
                    "symbol": sym_name,
                    "status": status,
                    "pricePrecision": price_prec,
                    "quantityPrecision": qty_prec,
                    "tickSize": tick_size,
                    "minPrice": min_price,
                    "maxPrice": max_price,
                    "minQty": min_qty,
                    "stepSize": step_size,
                    "minNotional": float(min_notional)
                }

            _EXCHANGE_INFO_CACHE[cache_key] = parsed_symbols
            try:
                with open(disk_file, "w", encoding="utf-8") as f:
                    json.dump(parsed_symbols, f, indent=2)
            except Exception:
                pass

            if symbol:
                return parsed_symbols.get(symbol.upper().replace("-", "").replace("/", "").replace("_", ""))
            return parsed_symbols
    except Exception as e:
        print(f"[ExchangeInfo Warning] Gagal fetch exchange info: {e}", file=sys.stderr)
        if symbol:
            return None
        return {}

def send_signed_request(endpoint, method="GET", params=None, is_demo=True, user_email=None, retries=3, backoff_base=0.3):
    target_user, key, secret, base_url, mode_label, proxy = resolve_credentials(user_email, is_demo)
    if not key or not secret:
        print("\n=======================================================")
        print(f" ⚠️ KREDENSIAL BINANCE BELUM DISET UNTUK: {target_user}")
        print("=======================================================")
        suffix = sanitize_email_suffix(target_user)
        key_name = f"BINANCE_DEMO_API_KEY_{suffix}" if is_demo else f"BINANCE_API_KEY_{suffix}"
        secret_name = f"BINANCE_DEMO_API_SECRET_{suffix}" if is_demo else f"BINANCE_API_SECRET_{suffix}"
        print(f"Buka file .env dan masukkan:\n  {key_name}=your_key\n  {secret_name}=your_secret")
        print("=======================================================\n")
        return None

    last_error = None
    for attempt in range(1, retries + 1):
        p = params.copy() if params else {}
        offset = get_server_time_offset(base_url)
        p["timestamp"] = int(time.time() * 1000) + offset
        p["recvWindow"] = 15000

        query_str = urllib.parse.urlencode(p)
        signature = hmac.new(secret.encode("utf-8"), query_str.encode("utf-8"), hashlib.sha256).hexdigest()
        signed_query = f"{query_str}&signature={signature}"

        req_headers = HEADERS.copy()
        req_headers["X-MBX-APIKEY"] = key

        if method == "GET":
            url = f"{base_url}{endpoint}?{signed_query}"
            req = urllib.request.Request(url, headers=req_headers, method="GET")
        elif method == "DELETE":
            url = f"{base_url}{endpoint}?{signed_query}"
            req = urllib.request.Request(url, headers=req_headers, method="DELETE")
        else:
            url = f"{base_url}{endpoint}"
            post_data = signed_query.encode("utf-8")
            req = urllib.request.Request(url, data=post_data, headers=req_headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="ignore")
            if e.code in [429, 500, 502, 503, 504] and attempt < retries:
                sleep_time = backoff_base * (2 ** (attempt - 1))
                print(f"[Binance HTTP {e.code}] Percobaan {attempt}/{retries} gagal. Retrying dalam {sleep_time:.2f}s...", file=sys.stderr)
                time.sleep(sleep_time)
                continue
            print(f"[Binance HTTP Error {e.code}] {err_msg}", file=sys.stderr)
            return None
        except Exception as e:
            last_error = e
            if attempt < retries:
                sleep_time = backoff_base * (2 ** (attempt - 1))
                print(f"[Network Error] {e}. Percobaan {attempt}/{retries} gagal. Retrying dalam {sleep_time:.2f}s...", file=sys.stderr)
                time.sleep(sleep_time)
                continue
            print(f"[Network Error] {last_error}", file=sys.stderr)
            return None

    return None

def check_balance(user_email=None, is_demo=True):
    target_user, _, _, _, mode_label, _ = resolve_credentials(user_email, is_demo)
    print("\n=======================================================")
    print(f"       BINANCE FUTURES WALLET AUDIT")
    print(f"       👤 Akun    : {target_user}")
    print(f"       🕹️ Mode    : {mode_label}")
    print("=======================================================")

    res = send_signed_request("/fapi/v2/balance", method="GET", is_demo=is_demo, user_email=user_email)
    if res is None:
        return

    non_zero = [b for b in res if float(b.get("balance", 0)) > 0]
    if not non_zero:
        print("✅ KONEKSI API BERHASIL TERHUBUNG KE SERVER BINANCE!")
        print("Status: Akun Demo terautentikasi (Saldo saat ini masih 0.00).")
        print("\n💡 CARA KLAIM SALDO DEMO GRATIS (HINGGA 15,000 USDT):")
        print("1. Buka website: https://testnet.binancefuture.com")
        print("2. Login dengan akun Anda.")
        print("3. Di bagian bawah saldo, klik tombol 'Faucet' untuk mengisi saldo demo gratis!")
    else:
        print(f"{'Aset':<10} | {'Total Saldo':<18} | {'Tersedia (Free)':<18} | {'Floating PnL':<15}")
        print("-" * 68)
        for b in non_zero:
            asset = b.get("asset")
            bal = float(b.get("balance", 0))
            avail = float(b.get("withdrawAvailable", 0))
            upnl = float(b.get("crossUnPnl", 0))
            print(f"{asset:<10} | ${bal:<17,.2f} | ${avail:<17,.2f} | {'+' if upnl>=0 else ''}${upnl:<14,.2f}")

    print("=======================================================\n")

def get_ticker(symbol="BTCUSDT"):
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    print(f"\nMengambil harga live Binance untuk pair: {sym_clean}...")
    url = f"https://data-api.binance.vision/api/v3/ticker/24hr?symbol={sym_clean}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=6, context=SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            last_p = float(data.get("lastPrice", 0))
            bid_p = float(data.get("bidPrice", 0))
            ask_p = float(data.get("askPrice", 0))
            change_p = float(data.get("priceChangePercent", 0))
            vol_usd = float(data.get("quoteVolume", 0))

            print(f"Harga Pasar Binance [{sym_clean}]: ${last_p:,.4f}")
            print(f"  * 24h Perubahan : {change_p:+.2f}%")
            print(f"  * 24h Volume USD: ${vol_usd/1_000_000:,.2f} Juta USDT")
            print(f"  * Best Bid / Ask: ${bid_p:,.4f} / ${ask_p:,.4f}")
            return last_p
    except Exception as e:
        print(f"Gagal mengambil ticker dari Binance: {e}")
        return None

def set_leverage(symbol, leverage, is_demo=True, user_email=None):
    params = {"symbol": symbol, "leverage": int(leverage)}
    res = send_signed_request("/fapi/v1/leverage", method="POST", params=params, is_demo=is_demo, user_email=user_email)
    if res and res.get("leverage"):
        print(f"✅ Leverage untuk {symbol} berhasil disetel ke {res.get('leverage')}x")
        return True
    return False

def get_positions(user_email=None, is_demo=True):
    target_user, _, _, _, mode_label, _ = resolve_credentials(user_email, is_demo)
    print("\n=======================================================")
    print(f"       📊 POSISI AKTIF BINANCE FUTURES")
    print(f"       👤 Akun: {target_user} | Mode: {mode_label}")
    print("=======================================================")

    res = send_signed_request("/fapi/v2/positionRisk", method="GET", is_demo=is_demo, user_email=user_email)
    if res is None:
        return

    active = [p for p in res if float(p.get("positionAmt", 0)) != 0]
    if not active:
        print("Tidak ada posisi aktif yang sedang terbuka.")
    else:
        for p in active:
            amt = float(p.get("positionAmt", 0))
            side = "LONG 🟢" if amt > 0 else "SHORT 🔴"
            entry = float(p.get("entryPrice", 0))
            mark = float(p.get("markPrice", 0))
            liq = float(p.get("liquidationPrice", 0))
            upnl = float(p.get("unRealizedProfit", 0))
            lev = p.get("leverage")

            print(f" * [{p['symbol']}] {side} | Ukuran: {abs(amt)} | Lev: {lev}x")
            print(f"   Entry: ${entry:,.4f} | Mark: ${mark:,.4f} | Liq: ${liq:,.4f}")
            print(f"   Floating PnL: {'+' if upnl>=0 else ''}${upnl:,.2f}")
    print("=======================================================\n")

def get_precision_from_step(step_str):
    s = str(step_str)
    if "." in s:
        decimals = s.split(".")[1].rstrip("0")
        return len(decimals)
    return 0

def format_price_precision(symbol, price, is_demo=True):
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    info = get_exchange_info(sym_clean, is_demo=is_demo)

    if info and "tickSize" in info:
        try:
            tick = Decimal(str(info["tickSize"]))
            p = Decimal(str(price))
            rounded = (p // tick) * tick
            dec_places = get_precision_from_step(info["tickSize"])
            if dec_places == 0:
                return str(int(rounded))
            return f"{rounded:.{dec_places}f}"
        except Exception:
            pass

    # Fallback heuristic
    if "BTC" in sym_clean:
        return f"{price:.1f}"
    elif any(k in sym_clean for k in ["ETH", "BNB", "SOL", "AVAX", "LINK"]):
        return f"{price:.2f}"
    elif any(k in sym_clean for k in ["XRP", "ADA", "DOGE", "SUI", "NEAR"]):
        return f"{price:.4f}"
    else:
        return f"{price:.2f}"

def format_qty_precision(symbol, qty, is_demo=True):
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    info = get_exchange_info(sym_clean, is_demo=is_demo)

    if info and "stepSize" in info:
        try:
            step = Decimal(str(info["stepSize"]))
            q = Decimal(str(qty))
            rounded = (q // step) * step
            min_q = Decimal(str(info.get("minQty", "0.001")))
            if rounded < min_q:
                rounded = min_q
            dec_places = get_precision_from_step(info["stepSize"])
            if dec_places == 0:
                return str(int(rounded))
            return f"{rounded:.{dec_places}f}"
        except Exception:
            pass

    # Fallback heuristic
    if "BTC" in sym_clean:
        return f"{max(0.001, float(qty)):.3f}"
    elif "ETH" in sym_clean:
        return f"{max(0.01, float(qty)):.3f}"
    elif any(k in sym_clean for k in ["SOL", "BNB", "AVAX", "LINK"]):
        return f"{max(0.1, float(qty)):.2f}"
    elif any(k in sym_clean for k in ["XRP", "ADA", "DOGE", "SUI", "NEAR"]):
        return f"{max(1.0, float(qty)):.1f}"
    else:
        return f"{max(0.1, float(qty)):.2f}"

def validate_order_filters(symbol, qty, price, is_demo=True):
    """
    Validates that quantity, price, and notional meet Binance Futures exchange constraints.
    Returns: (is_valid: bool, adjusted_qty: float, message: str)
    """
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    info = get_exchange_info(sym_clean, is_demo=is_demo)
    if not info:
        return True, qty, "OK (Exchange info bypass)"

    min_notional = float(info.get("minNotional", 5.0))
    notional = float(qty) * float(price)
    if notional < min_notional:
        required_qty = (min_notional / float(price)) * 1.05
        formatted_qty = format_qty_precision(sym_clean, required_qty, is_demo=is_demo)
        return False, float(formatted_qty), f"Notional ${notional:.2f} di bawah batas minimum ${min_notional:.2f}. Disarankan: {formatted_qty} {sym_clean}"

    return True, qty, "OK"

def check_order_book_depth(symbol, quantity, side="BUY", is_demo=True, max_slippage_pct=0.30):
    """
    Audits order book depth for the specified symbol before order execution.
    Calculates spread percentage and estimated slippage impact.
    Returns: (is_safe: bool, details: dict)
    """
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    target_user, _, _, base_url, _, _ = resolve_credentials(None, is_demo)

    url = f"{base_url}/fapi/v1/depth?symbol={sym_clean}&limit=10"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=5, context=SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            bids = data.get("bids", [])
            asks = data.get("asks", [])
            if not bids or not asks:
                return True, {"warning": "Empty book", "slippage_pct": 0.0, "spread_pct": 0.0, "is_safe": True}

            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])
            spread_pct = ((best_ask - best_bid) / best_bid) * 100.0

            qty_needed = float(quantity)
            target_levels = asks if side.upper() in ["BUY", "LONG"] else bids
            cum_qty = 0.0
            cum_cost = 0.0

            for p_str, q_str in target_levels:
                level_price = float(p_str)
                level_qty = float(q_str)
                fill_qty = min(level_qty, qty_needed - cum_qty)
                cum_qty += fill_qty
                cum_cost += fill_qty * level_price
                if cum_qty >= qty_needed:
                    break

            if cum_qty > 0:
                vwap = cum_cost / cum_qty
                ref_price = best_ask if side.upper() in ["BUY", "LONG"] else best_bid
                slippage_pct = abs(vwap - ref_price) / ref_price * 100.0
            else:
                slippage_pct = 0.0

            is_safe = slippage_pct <= max_slippage_pct and spread_pct <= 0.35
            return is_safe, {
                "best_bid": best_bid,
                "best_ask": best_ask,
                "spread_pct": round(spread_pct, 4),
                "slippage_pct": round(slippage_pct, 4),
                "is_safe": is_safe
            }
    except Exception as e:
        return True, {"warning": str(e), "slippage_pct": 0.0, "spread_pct": 0.0, "is_safe": True}

def cancel_existing_algo_orders_for_symbol(symbol, is_demo=True, user_email=None):
    """
    Cancels any existing open conditional / algo orders for the symbol
    to prevent Binance Error -4130 (An open stop or take profit order with GTE and closePosition is existing).
    """
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    try:
        open_algos = send_signed_request("/fapi/v1/openAlgoOrders", method="GET", is_demo=is_demo, user_email=user_email)
        if open_algos and isinstance(open_algos, list):
            for o in open_algos:
                if o.get("symbol") == sym_clean:
                    algo_id = o.get("algoId")
                    if algo_id:
                        send_signed_request("/fapi/v1/algoOrder", method="DELETE", params={"algoId": algo_id}, is_demo=is_demo, user_email=user_email)
    except Exception:
        pass

def place_futures_order(symbol, side, quantity, leverage=5, sl=None, tp=None, is_demo=True, user_email=None, exec_mode="MARKET"):
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    target_user, _, _, _, mode_label, _ = resolve_credentials(user_email, is_demo)

    side_clean = "BUY" if side.upper() in ["LONG", "BUY"] else "SELL"
    pos_label = "LONG 🟢" if side_clean == "BUY" else "SHORT 🔴"

    # Format quantity with dynamic exchange info
    formatted_qty = format_qty_precision(sym_clean, quantity, is_demo=is_demo)

    print("\n=======================================================")
    print(f"       ⚡ EKSEKUSI ORDER BINANCE FUTURES")
    print(f"       👤 Akun: {target_user} | Mode: {mode_label}")
    print("=======================================================")
    print(f"Pair: {sym_clean} | Posisi: {pos_label} | Qty: {formatted_qty} | Leverage: {leverage}x | Exec Mode: {exec_mode}")

    # 1. Set Leverage
    set_leverage(sym_clean, leverage, is_demo, user_email)

    order_id = None
    avg_price = 0.0
    res = None

    # 2. Execution Logic (Limit Chase vs Market)
    if exec_mode.upper() == "LIMIT_CHASE":
        is_safe, depth_info = check_order_book_depth(sym_clean, formatted_qty, side_clean, is_demo=is_demo)
        best_price = depth_info.get("best_bid" if side_clean == "BUY" else "best_ask")
        if best_price:
            price_str = format_price_precision(sym_clean, best_price, is_demo=is_demo)
            limit_params = {
                "symbol": sym_clean,
                "side": side_clean,
                "type": "LIMIT",
                "timeInForce": "GTC",
                "quantity": str(formatted_qty),
                "price": price_str
            }
            print(f"⏳ [LIMIT CHASE] Menempatkan Maker Order @ ${price_str} (Potensi Hemat Fee 60%)...")
            limit_res = send_signed_request("/fapi/v1/order", method="POST", params=limit_params, is_demo=is_demo, user_email=user_email)
            if limit_res and limit_res.get("orderId"):
                chase_id = limit_res.get("orderId")
                for _ in range(4):
                    time.sleep(0.75)
                    q_res = send_signed_request("/fapi/v1/order", method="GET", params={"symbol": sym_clean, "orderId": chase_id}, is_demo=is_demo, user_email=user_email)
                    if q_res and q_res.get("status") == "FILLED":
                        res = q_res
                        order_id = chase_id
                        avg_price = float(res.get("avgPrice", 0) or res.get("price", 0) or best_price)
                        print(f"🎉 [MAKER FILL SUKSES] Order terisi di antrean Maker @ ${avg_price:,.4f}!")
                        break

                if not order_id:
                    print("⚠️ [LIMIT CHASE UNFILLED] 3s belum terisi. Membatalkan Maker Order & mengonversi ke Market...")
                    send_signed_request("/fapi/v1/order", method="DELETE", params={"symbol": sym_clean, "orderId": chase_id}, is_demo=is_demo, user_email=user_email)

    if not order_id:
        order_params = {
            "symbol": sym_clean,
            "side": side_clean,
            "type": "MARKET",
            "quantity": str(formatted_qty)
        }
        res = send_signed_request("/fapi/v1/order", method="POST", params=order_params, is_demo=is_demo, user_email=user_email, retries=3)
        if not res or not res.get("orderId"):
            print(f"❌ Gagal mengeksekusi order utama: {res}")
            return None

        order_id = res.get("orderId")
        avg_price = float(res.get("avgPrice", 0) or res.get("price", 0) or 0)
        print(f"\n✅ ORDER UTAMA TERISI! Order ID: {order_id} @ ${avg_price:,.4f}")

    # Cancel previous conflicting algo orders for this symbol before placing fresh SL/TP
    if sl or tp:
        cancel_existing_algo_orders_for_symbol(sym_clean, is_demo=is_demo, user_email=user_email)

    # 3. Attach Stop Loss via Algo Order API with dynamic precision & auto-retry
    opp_side = "SELL" if side_clean == "BUY" else "BUY"
    if sl:
        sl_str = format_price_precision(sym_clean, sl, is_demo=is_demo)
        sl_params = {
            "algoType": "CONDITIONAL",
            "symbol": sym_clean,
            "side": opp_side,
            "type": "STOP_MARKET",
            "triggerPrice": sl_str,
            "closePosition": "true"
        }
        sl_res = send_signed_request("/fapi/v1/algoOrder", method="POST", params=sl_params, is_demo=is_demo, user_email=user_email, retries=3)
        if sl_res and sl_res.get("algoId"):
            print(f"🛑 Stop Loss dipasang di harga ${sl_str} (Algo ID: {sl_res.get('algoId')})")
        else:
            print(f"⚠️ Respon SL: {sl_res}")

    # 4. Attach Take Profit via Algo Order API with dynamic precision & auto-retry
    if tp:
        tp_str = format_price_precision(sym_clean, tp, is_demo=is_demo)
        tp_params = {
            "algoType": "CONDITIONAL",
            "symbol": sym_clean,
            "side": opp_side,
            "type": "TAKE_PROFIT_MARKET",
            "triggerPrice": tp_str,
            "closePosition": "true"
        }
        tp_res = send_signed_request("/fapi/v1/algoOrder", method="POST", params=tp_params, is_demo=is_demo, user_email=user_email, retries=3)
        if tp_res and tp_res.get("algoId"):
            print(f"🎯 Take Profit dipasang di harga ${tp_str} (Algo ID: {tp_res.get('algoId')})")
        else:
            print(f"⚠️ Respon TP: {tp_res}")

    print("=======================================================\n")
    return res

def get_open_orders(symbol=None, is_demo=True, user_email=None):
    target_user, _, _, _, mode_label, _ = resolve_credentials(user_email, is_demo)
    print("\n=======================================================")
    print(f"       📋 DAFTAR PENDING ORDERS (BINANCE FUTURES)")
    print(f"       👤 Akun: {target_user} | Mode: {mode_label}")
    print("=======================================================")

    params = {}
    if symbol:
        params["symbol"] = symbol.upper().replace("-", "").replace("/", "").replace("_", "")

    res = send_signed_request("/fapi/v1/openOrders", method="GET", params=params, is_demo=is_demo, user_email=user_email)
    if res is None:
        return

    if not res:
        print("Tidak ada order pending.")
    else:
        for o in res:
            side = o.get("side")
            orig_type = o.get("type")
            stop_price = o.get("stopPrice")
            price = o.get("price")
            print(f" * Order ID: {o.get('orderId')} | {o.get('symbol')} {side} [{orig_type}]")
            print(f"   Trigger/Harga: ${stop_price or price} | Qty: {o.get('origQty')}")
    print("=======================================================\n")

def cancel_all_orders(symbol, is_demo=True, user_email=None):
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    params = {"symbol": sym_clean}
    res = send_signed_request("/fapi/v1/allOpenOrders", method="DELETE", params=params, is_demo=is_demo, user_email=user_email)
    if res and res.get("code") == 200:
        print(f"✅ Semua open orders untuk {sym_clean} berhasil dibatalkan.")
    else:
        print(f"Hasil pembatalan: {res}")

def main():
    parser = argparse.ArgumentParser(description="Binance Futures Client (Demo & Live)")
    sub = parser.add_subparsers(dest="command")

    # Balance
    b_p = sub.add_parser("balance", help="Lihat saldo akun Binance Futures")
    b_p.add_argument("--user", type=str, default=None, help="Email akun")
    b_p.add_argument("--live", action="store_true", help="Gunakan akun live riil (default: Demo)")

    # Positions
    pos_p = sub.add_parser("positions", help="Lihat posisi aktif yang sedang terbuka")
    pos_p.add_argument("--user", type=str, default=None, help="Email akun")
    pos_p.add_argument("--live", action="store_true", help="Gunakan akun live riil (default: Demo)")

    # Orders
    ord_p = sub.add_parser("orders", help="Lihat pending order")
    ord_p.add_argument("--symbol", type=str, default=None, help="Pair (misal: BTCUSDT)")
    ord_p.add_argument("--user", type=str, default=None, help="Email akun")
    ord_p.add_argument("--live", action="store_true", help="Gunakan akun live riil (default: Demo)")

    # Ticker (Public)
    t_p = sub.add_parser("ticker", help="Lihat harga pasar live")
    t_p.add_argument("--symbol", type=str, default="BTCUSDT", help="Pair (misal: BTCUSDT, SOLUSDT)")

    # Trade (Futures)
    trade_p = sub.add_parser("trade", help="Buka posisi Futures Long/Short")
    trade_p.add_argument("--symbol", type=str, required=True, help="Pair (misal: BTCUSDT, SOLUSDT)")
    trade_p.add_argument("--side", type=str, required=True, choices=["LONG", "SHORT", "long", "short"])
    trade_p.add_argument("--qty", type=float, required=True, help="Ukuran posisi (jumlah koin)")
    trade_p.add_argument("--leverage", type=int, default=5, help="Leverage (default: 5)")
    trade_p.add_argument("--sl", type=float, default=None, help="Stop Loss price")
    trade_p.add_argument("--tp", type=float, default=None, help="Take Profit target price")
    trade_p.add_argument("--mode", type=str, default="MARKET", choices=["MARKET", "LIMIT_CHASE"], help="Mode eksekusi (MARKET atau LIMIT_CHASE)")
    trade_p.add_argument("--user", type=str, default=None, help="Email akun")
    trade_p.add_argument("--live", action="store_true", help="Gunakan akun live riil (default: Demo)")

    # Specs (Dynamic Exchange Info)
    spec_p = sub.add_parser("specs", help="Lihat spesifikasi presisi & filter bursa untuk simbol tertentu")
    spec_p.add_argument("--symbol", type=str, required=True, help="Pair (misal: BTCUSDT, DOGEUSDT)")
    spec_p.add_argument("--live", action="store_true", help="Gunakan akun live riil (default: Demo)")

    # Depth (Order Book Guard)
    dep_p = sub.add_parser("depth", help="Cek ketebalan buku pesanan dan estimasi slippage")
    dep_p.add_argument("--symbol", type=str, required=True, help="Pair (misal: BTCUSDT)")
    dep_p.add_argument("--qty", type=float, default=0.1, help="Kuantitas simulasi")
    dep_p.add_argument("--side", type=str, default="BUY", choices=["BUY", "SELL"])
    dep_p.add_argument("--live", action="store_true", help="Gunakan akun live riil (default: Demo)")

    # Cancel All
    can_p = sub.add_parser("cancel", help="Batalkan semua order pending untuk suatu pair")
    can_p.add_argument("--symbol", type=str, required=True, help="Pair (misal: BTCUSDT)")
    can_p.add_argument("--user", type=str, default=None, help="Email akun")
    can_p.add_argument("--live", action="store_true", help="Gunakan akun live riil (default: Demo)")

    args = parser.parse_args()
    is_demo = not getattr(args, "live", False)

    if args.command == "balance":
        check_balance(args.user, is_demo=is_demo)
    elif args.command == "positions":
        get_positions(args.user, is_demo=is_demo)
    elif args.command == "orders":
        get_open_orders(args.symbol, is_demo=is_demo, user_email=args.user)
    elif args.command == "ticker":
        get_ticker(args.symbol)
    elif args.command == "specs":
        info = get_exchange_info(args.symbol, is_demo=is_demo)
        print(f"\n=======================================================")
        print(f"       SPEC FOR {args.symbol} (Binance Futures)")
        print(f"=======================================================")
        if info:
            for k, v in info.items():
                print(f"  * {k:<20}: {v}")
        else:
            print("  Data spesifikasi simbol tidak ditemukan.")
        print("=======================================================\n")
    elif args.command == "depth":
        is_safe, details = check_order_book_depth(args.symbol, args.qty, side=args.side, is_demo=is_demo)
        print(f"\n=======================================================")
        print(f"       ORDER BOOK DEPTH AUDIT: {args.symbol}")
        print(f"=======================================================")
        print(f"  * Status Eksekusi Aman : {'✅ SAFE' if is_safe else '⚠️ HIGH SLIPPAGE'}")
        for k, v in details.items():
            print(f"  * {k:<20}: {v}")
        print("=======================================================\n")
    elif args.command == "trade":
        place_futures_order(args.symbol, args.side, args.qty, args.leverage, args.sl, args.tp, is_demo=is_demo, user_email=args.user, exec_mode=args.mode)
    elif args.command == "cancel":
        cancel_all_orders(args.symbol, is_demo=is_demo, user_email=args.user)
    else:
        check_balance(None, is_demo=True)

if __name__ == "__main__":
    main()

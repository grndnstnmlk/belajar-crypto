"""
Binance Demo & Live Futures Trading Client (Multi-Account Enabled)
Supports Binance Futures Testnet (Demo Trading) & Live USDⓈ-M Futures.
Bypasses regional SSL blocks via native HTTPS HMAC-SHA256 engine.
"""

import argparse
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

ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")

# SSL Context to prevent Windows regional certificate verification blocks
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded"
}

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

def send_signed_request(endpoint, method="GET", params=None, is_demo=True, user_email=None):
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

    if params is None:
        params = {}

    offset = get_server_time_offset(base_url)
    params["timestamp"] = int(time.time() * 1000) + offset
    params["recvWindow"] = 15000

    query_str = urllib.parse.urlencode(params)
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
        print(f"[Binance HTTP Error {e.code}] {err_msg}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[Network Error] {e}", file=sys.stderr)
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

def format_price_precision(symbol, price):
    sym = symbol.upper()
    if "BTC" in sym:
        return f"{price:.1f}"
    elif any(k in sym for k in ["ETH", "BNB", "SOL", "AVAX", "LINK"]):
        return f"{price:.2f}"
    elif any(k in sym for k in ["XRP", "ADA", "DOGE", "SUI", "NEAR"]):
        return f"{price:.4f}"
    else:
        return f"{price:.2f}"

def place_futures_order(symbol, side, quantity, leverage=5, sl=None, tp=None, is_demo=True, user_email=None):
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    target_user, _, _, _, mode_label, _ = resolve_credentials(user_email, is_demo)

    side_clean = "BUY" if side.upper() in ["LONG", "BUY"] else "SELL"
    pos_label = "LONG 🟢" if side_clean == "BUY" else "SHORT 🔴"

    print("\n=======================================================")
    print(f"       ⚡ EKSEKUSI ORDER BINANCE FUTURES")
    print(f"       👤 Akun: {target_user} | Mode: {mode_label}")
    print("=======================================================")
    print(f"Pair: {sym_clean} | Posisi: {pos_label} | Qty: {quantity} | Leverage: {leverage}x")

    # 1. Set Leverage
    set_leverage(sym_clean, leverage, is_demo, user_email)

    # 2. Main Market Order
    order_params = {
        "symbol": sym_clean,
        "side": side_clean,
        "type": "MARKET",
        "quantity": str(quantity)
    }
    res = send_signed_request("/fapi/v1/order", method="POST", params=order_params, is_demo=is_demo, user_email=user_email)
    if not res or not res.get("orderId"):
        print(f"❌ Gagal mengeksekusi order utama: {res}")
        return

    order_id = res.get("orderId")
    avg_price = float(res.get("avgPrice", 0) or res.get("price", 0) or 0)
    print(f"\n✅ ORDER UTAMA TERISI! Order ID: {order_id} @ ${avg_price:,.4f}")

    # 3. Attach Stop Loss via Algo Order API
    opp_side = "SELL" if side_clean == "BUY" else "BUY"
    if sl:
        sl_str = format_price_precision(sym_clean, sl)
        sl_params = {
            "algoType": "CONDITIONAL",
            "symbol": sym_clean,
            "side": opp_side,
            "type": "STOP_MARKET",
            "triggerPrice": sl_str,
            "closePosition": "true"
        }
        sl_res = send_signed_request("/fapi/v1/algoOrder", method="POST", params=sl_params, is_demo=is_demo, user_email=user_email)
        if sl_res and sl_res.get("algoId"):
            print(f"🛑 Stop Loss dipasang di harga ${sl_str} (Algo ID: {sl_res.get('algoId')})")
        else:
            print(f"⚠️ Respon SL: {sl_res}")

    # 4. Attach Take Profit via Algo Order API
    if tp:
        tp_str = format_price_precision(sym_clean, tp)
        tp_params = {
            "algoType": "CONDITIONAL",
            "symbol": sym_clean,
            "side": opp_side,
            "type": "TAKE_PROFIT_MARKET",
            "triggerPrice": tp_str,
            "closePosition": "true"
        }
        tp_res = send_signed_request("/fapi/v1/algoOrder", method="POST", params=tp_params, is_demo=is_demo, user_email=user_email)
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
    trade_p.add_argument("--user", type=str, default=None, help="Email akun")
    trade_p.add_argument("--live", action="store_true", help="Gunakan akun live riil (default: Demo)")

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
    elif args.command == "trade":
        place_futures_order(args.symbol, args.side, args.qty, args.leverage, args.sl, args.tp, is_demo=is_demo, user_email=args.user)
    elif args.command == "cancel":
        cancel_all_orders(args.symbol, is_demo=is_demo, user_email=args.user)
    else:
        check_balance(None, is_demo=True)

if __name__ == "__main__":
    main()

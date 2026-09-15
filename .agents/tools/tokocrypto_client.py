"""
Tokocrypto Spot Trading Client (Multi-Account Enabled)
Supports isolated API credentials per user email (e.g. dxmade@gmail.com).
Regulated by Bappebti / OJK Indonesia.
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib3

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

urllib3.disable_warnings()
ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")

def sanitize_email_suffix(email):
    """Converts user@gmail.com -> USER_GMAIL_COM"""
    cleaned = re.sub(r"[^a-zA-Z0-9]", "_", email.upper())
    return cleaned

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

def get_all_configured_users():
    env_vars = parse_env_file()
    active = env_vars.get("ACTIVE_USER", "dxmade@gmail.com")
    users = set()
    if active:
        users.add(active)

    pattern = re.compile(r"^TOKOCRYPTO_API_KEY_(.+)$")
    for k in env_vars.keys():
        m = pattern.match(k)
        if m:
            suffix = m.group(1).lower()
            if "_gmail_com" in suffix:
                email = suffix.replace("_gmail_com", "@gmail.com")
            else:
                email = suffix.replace("_", ".")
            users.add(email)
    return list(sorted(users)), active

def resolve_credentials(user_email=None):
    env_vars = parse_env_file()
    active_user = env_vars.get("ACTIVE_USER", "dxmade@gmail.com")
    target_user = user_email.strip() if user_email else active_user

    suffix = sanitize_email_suffix(target_user)
    key_var = f"TOKOCRYPTO_API_KEY_{suffix}"
    secret_var = f"TOKOCRYPTO_API_SECRET_{suffix}"

    api_key = env_vars.get(key_var)
    api_secret = env_vars.get(secret_var)

    # Fallback to general keys if target matches active user
    if (not api_key or not api_secret) and (not user_email or user_email.lower() == active_user.lower()):
        api_key = env_vars.get("TOKOCRYPTO_API_KEY")
        api_secret = env_vars.get("TOKOCRYPTO_API_SECRET")

    return target_user, api_key, api_secret

def get_exchange(user_email=None):
    import ccxt
    target_user, api_key, api_secret = resolve_credentials(user_email)
    if not api_key or not api_secret or "masukkan_" in api_key:
        print("\n=======================================================")
        print(f" ⚠️ KREDENSIAL TOKOCRYPTO BELUM DISET UNTUK: {target_user}")
        print("=======================================================")
        suffix = sanitize_email_suffix(target_user)
        print("Buka file .env dan isi API Key untuk akun ini:")
        print(f"  TOKOCRYPTO_API_KEY_{suffix}=your_key")
        print(f"  TOKOCRYPTO_API_SECRET_{suffix}=your_secret")
        print("=======================================================\n")
        return None, target_user

    exchange = ccxt.tokocrypto({
        "apiKey": api_key,
        "secret": api_secret,
        "enableRateLimit": True,
        "options": {
            "defaultType": "spot",
            "adjustForTimeDifference": True
        }
    })
    if hasattr(exchange, "session") and exchange.session:
        exchange.session.verify = False
    return exchange, target_user

def check_balance(user_email=None):
    exchange, target_user = get_exchange(user_email)
    print("\n=======================================================")
    print(f"       🇮🇩 TOKOCRYPTO SPOT ASSET BALANCE")
    print(f"       👤 Akun Terpilih: {target_user}")
    print("=======================================================")
    if not exchange:
        return

    try:
        balance = exchange.fetch_balance()
        non_zero = {}
        for coin, amount in balance.get("total", {}).items():
            if amount and float(amount) > 0:
                non_zero[coin] = {
                    "free": float(balance.get(coin, {}).get("free", 0) or 0),
                    "locked": float(balance.get(coin, {}).get("used", 0) or 0),
                    "total": float(amount)
                }

        if not non_zero:
            print(f"✅ KONEKSI BERHASIL TERHUBUNG KE AKUN: {target_user}!")
            print("Status: Akun Anda valid & terautentikasi (Saldo saat ini masih 0.00).")
            print("Silakan lakukan deposit Rupiah (IDR) atau USDT untuk mulai trading.")
        else:
            print(f"{'Aset':<10} | {'Saldo Bebas (Free)':<20} | {'Terkunci (Order)':<18} | {'Total':<18}")
            print("-" * 72)
            for coin, val in non_zero.items():
                print(f"{coin:<10} | {val['free']:<20.8f} | {val['locked']:<18.8f} | {val['total']:<18.8f}")
    except Exception as e:
        print(f"Gagal mengambil saldo dari Tokocrypto untuk {target_user}: {e}")
    print("=======================================================\n")

def get_ticker(symbol="BTC/USDT"):
    sym_clean = symbol.upper().replace("-", "/").replace("_", "/")
    pair_depth = sym_clean.replace("/", "_")

    print(f"\nMengambil harga live Tokocrypto untuk pair: {sym_clean}...")
    url = f"https://www.tokocrypto.com/open/v1/market/depth?symbol={pair_depth}&limit=5"
    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("code") == 0 and data.get("data"):
                bids = data["data"].get("bids", [])
                asks = data["data"].get("asks", [])
                best_bid = float(bids[0][0]) if bids else 0
                best_ask = float(asks[0][0]) if asks else 0
                mid = (best_bid + best_ask) / 2 if (best_bid and best_ask) else (best_bid or best_ask)

                print(f"Harga Pasar Tokocrypto [{sym_clean}]: ${mid:,.4f}")
                print(f"  * Best Bid (Antrean Beli Tertinggi): ${best_bid:,.4f}")
                print(f"  * Best Ask (Antrean Jual Terendah) : ${best_ask:,.4f}")
                return mid
    except Exception as e:
        print(f"Gagal mengambil harga untuk {sym_clean}: {e}")
    return None

def get_open_orders(symbol="BTC/USDT", user_email=None):
    exchange, target_user = get_exchange(user_email)
    print("\n=======================================================")
    print(f"       📋 DAFTAR OPEN ORDERS ({symbol})")
    print(f"       👤 Akun Terpilih: {target_user}")
    print("=======================================================")
    if not exchange:
        return

    sym_clean = symbol.upper().replace("-", "/").replace("_", "/")
    try:
        orders = exchange.fetch_open_orders(sym_clean)
        if not orders:
            print(f"Tidak ada order terbuka / pending untuk {sym_clean} pada akun {target_user}.")
        else:
            for o in orders:
                side = o.get("side", "").upper()
                print(f" * Order ID: {o.get('id')} | {side} {o.get('symbol')}")
                print(f"   Harga: {o.get('price')} | Jumlah: {o.get('amount')} | Terisi: {o.get('filled')}")
    except Exception as e:
        print(f"Gagal mengambil open orders: {e}")
    print("=======================================================\n")

def place_order(symbol, side, quantity, price=None, order_type="LIMIT", user_email=None):
    exchange, target_user = get_exchange(user_email)
    if not exchange:
        return

    sym_clean = symbol.upper().replace("-", "/").replace("_", "/")
    side_clean = "buy" if side.upper() in ["BUY", "BELI", "LONG"] else "sell"
    type_clean = order_type.lower()

    print(f"\n[KONFIRMASI EKSEKUSI TOKOCRYPTO - AKUN: {target_user}]")
    print(f"Pair: {sym_clean} | Aksi: {side_clean.upper()} | Jumlah: {quantity} | Tipe: {type_clean.upper()} | Harga: {price or 'MARKET'}")

    try:
        order = exchange.create_order(
            symbol=sym_clean,
            type=type_clean,
            side=side_clean,
            amount=quantity,
            price=price
        )
        print("\n=======================================================")
        print(f"       ✅ ORDER SPOT BERHASIL DI TOKOCRYPTO [{target_user}]!")
        print("=======================================================")
        print(f"Order ID : {order.get('id')}")
        print(f"Status   : {order.get('status')}")
        print(f"Filled   : {order.get('filled')} / {order.get('amount')}")
        print("=======================================================")
    except Exception as e:
        print(f"\n❌ Gagal mengirim order untuk {target_user}: {e}")

def cancel_order(order_id, symbol="SUI/IDR", user_email=None):
    exchange, target_user = get_exchange(user_email)
    if not exchange:
        return
    sym_clean = symbol.upper().replace("-", "/").replace("_", "/")
    print(f"\n[MEMBATALKAN ORDER {order_id} ({sym_clean}) - AKUN: {target_user}]...")
    try:
        res = exchange.cancel_order(order_id, sym_clean)
        print("\n=======================================================")
        print(f"       ✅ ORDER BERHASIL DIBATALKAN [{target_user}]!")
        print(f"Order ID : {order_id}")
        print("Saldo Rupiah Anda telah dikembalikan ke status Free (Siap digunakan).")
        print("=======================================================\n")
        return True
    except Exception as e:
        print(f"\n❌ Gagal membatalkan order: {e}\n")
        return False

def list_users():
    users, active = get_all_configured_users()
    print("\n=======================================================")
    print("       👥 DAFTAR AKUN TERKONFIGURASI DI .env")
    print("=======================================================")
    for u in users:
        is_active = " [AKTIF DEFAULT]" if u.lower() == active.lower() else ""
        print(f" * {u}{is_active}")
    print("-------------------------------------------------------")
    print("Gunakan flag --user <email> untuk memilih akun secara spesifik.")
    print("=======================================================\n")

def main():
    parser = argparse.ArgumentParser(description="Tokocrypto Multi-Account Spot Client")
    sub = parser.add_subparsers(dest="command")

    # Users list
    sub.add_parser("users", help="Daftar akun yang terkonfigurasi")

    # Balance
    b_p = sub.add_parser("balance", help="Lihat saldo akun Tokocrypto")
    b_p.add_argument("--user", type=str, default=None, help="Email akun (misal: dxmade@gmail.com)")

    # Orders
    orders_p = sub.add_parser("orders", help="Lihat order aktif / pending")
    orders_p.add_argument("--symbol", type=str, default="BTC/USDT", help="Pair koin (default: BTC/USDT)")
    orders_p.add_argument("--user", type=str, default=None, help="Email akun")

    # Cancel
    cancel_p = sub.add_parser("cancel", help="Batalkan order aktif")
    cancel_p.add_argument("--id", type=str, required=True, help="Order ID yang ingin dibatalkan")
    cancel_p.add_argument("--symbol", type=str, default="SUI/IDR", help="Pair koin (default: SUI/IDR)")
    cancel_p.add_argument("--user", type=str, default=None, help="Email akun")

    # Ticker (Public)
    t_p = sub.add_parser("ticker", help="Lihat harga pasar live di Tokocrypto")
    t_p.add_argument("--symbol", type=str, default="BTC/USDT", help="Pair koin (contoh: BTC/USDT, SOL/USDT)")

    # Trade
    trade_p = sub.add_parser("trade", help="Kirim order Beli atau Jual ke Tokocrypto")
    trade_p.add_argument("--symbol", type=str, required=True, help="Pair (misal: BTC/USDT)")
    trade_p.add_argument("--side", type=str, required=True, choices=["BUY", "SELL", "buy", "sell"])
    trade_p.add_argument("--qty", type=float, required=True, help="Jumlah koin")
    trade_p.add_argument("--price", type=float, default=None, help="Harga limit")
    trade_p.add_argument("--type", type=str, default="LIMIT", choices=["LIMIT", "MARKET", "limit", "market"])
    trade_p.add_argument("--user", type=str, default=None, help="Email akun")

    args = parser.parse_args()
    if args.command == "balance":
        check_balance(args.user)
    elif args.command == "users":
        list_users()
    elif args.command == "orders":
        get_open_orders(args.symbol, args.user)
    elif args.command == "cancel":
        cancel_order(args.id, args.symbol, args.user)
    elif args.command == "ticker":
        get_ticker(args.symbol)
    elif args.command == "trade":
        place_order(args.symbol, args.side, args.qty, args.price, args.type, args.user)
    else:
        check_balance()

if __name__ == "__main__":
    main()

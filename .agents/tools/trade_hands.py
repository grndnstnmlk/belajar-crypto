"""
Trade Hands (Tangan Agent) - Institutional Paper Trading & Order Execution Engine
Supports Multi-Account Portfolio Isolation per User Email.
"""

import argparse
import json
import os
import re
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

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
}

def get_default_user():
    if os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("ACTIVE_USER="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass
    return "dxmade@gmail.com"

def get_portfolio_path(user_email=None):
    os.makedirs(DATA_DIR, exist_ok=True)
    user = user_email.strip().lower() if user_email else get_default_user().lower()
    clean_name = re.sub(r"[^a-z0-9]", "_", user)
    return os.path.join(DATA_DIR, f"paper_portfolio_{clean_name}.json"), user

def get_live_price(symbol):
    base = symbol.upper().replace("-USDT", "").replace("USDT", "")
    inst_id = f"{base}-USDT"
    url = f"https://www.okx.com/api/v5/market/ticker?instId={inst_id}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("code") == "0" and data.get("data"):
                return float(data["data"][0].get("last", 0))
    except Exception as e:
        print(f"[Warning] Failed to get live price for {inst_id}: {e}", file=sys.stderr)
    return None

def load_portfolio(user_email=None):
    path, user = get_portfolio_path(user_email)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f), user
        except Exception:
            pass

    default_state = {
        "user_email": user,
        "initial_balance": 10000.0,
        "cash_balance": 10000.0,
        "positions": [],
        "trade_history": [],
        "created_at": datetime.now().isoformat()
    }
    save_portfolio(default_state, user_email)
    return default_state, user

def save_portfolio(data, user_email=None):
    path, _ = get_portfolio_path(user_email)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def open_position(symbol, side, amount_usd, sl, tp=None, entry=None, user_email=None):
    portfolio, user = load_portfolio(user_email)
    side = side.upper()
    if side not in ["LONG", "SHORT"]:
        print("Error: Side must be LONG or SHORT.")
        return

    base = symbol.upper().replace("-USDT", "").replace("USDT", "")
    inst_id = f"{base}-USDT"

    if not entry or entry <= 0:
        entry = get_live_price(inst_id)
        if not entry:
            print(f"Error: Unable to fetch live market price for {inst_id}.")
            return

    if portfolio["cash_balance"] < amount_usd:
        print(f"Error: Insufficient cash balance in {user}'s account. Available: ${portfolio['cash_balance']:,.2f}")
        return

    if side == "LONG" and sl >= entry:
        print(f"Error: For LONG positions, Stop Loss (${sl:,.4f}) must be BELOW Entry Price (${entry:,.4f}).")
        return
    if side == "SHORT" and sl <= entry:
        print(f"Error: For SHORT positions, Stop Loss (${sl:,.4f}) must be ABOVE Entry Price (${entry:,.4f}).")
        return

    units = amount_usd / entry
    pos_id = f"POS-{int(time.time())}"

    new_pos = {
        "id": pos_id,
        "symbol": inst_id,
        "side": side,
        "entry_price": entry,
        "amount_usd": amount_usd,
        "units": units,
        "stop_loss": sl,
        "take_profit": tp,
        "opened_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    portfolio["cash_balance"] -= amount_usd
    portfolio["positions"].append(new_pos)
    save_portfolio(portfolio, user)

    print("\n=======================================================")
    print(f"       ✅ TRADE EXECUTED: {side} {inst_id}")
    print(f"       👤 Akun Portofolio: {user}")
    print("=======================================================")
    print(f"Position ID      : {pos_id}")
    print(f"Entry Price      : ${entry:,.4f}")
    print(f"Position Size    : ${amount_usd:,.2f} ({units:,.4f} tokens)")
    print(f"Stop Loss        : ${sl:,.4f} ({abs(entry - sl) / entry * 100:.2f}% distance)")
    if tp:
        rr = abs(tp - entry) / abs(entry - sl)
        print(f"Take Profit      : ${tp:,.4f} (R:R 1 : {rr:.2f})")
    print(f"Remaining Cash   : ${portfolio['cash_balance']:,.2f}")
    print("=======================================================\n")

def update_positions(user_email=None):
    portfolio, user = load_portfolio(user_email)
    if not portfolio["positions"]:
        print(f"No active positions to update for {user}.")
        return

    active_positions = []
    closed_any = False

    print("\n=======================================================")
    print(f"       🔄 LIVE POSITION AUDIT & TP/SL CHECK [{user}]")
    print("=======================================================")

    for pos in portfolio["positions"]:
        current_price = get_live_price(pos["symbol"])
        if not current_price:
            active_positions.append(pos)
            continue

        entry = pos["entry_price"]
        sl = pos["stop_loss"]
        tp = pos.get("take_profit")
        side = pos["side"]

        hit_sl = (side == "LONG" and current_price <= sl) or (side == "SHORT" and current_price >= sl)
        hit_tp = tp and ((side == "LONG" and current_price >= tp) or (side == "SHORT" and current_price <= tp))

        if hit_sl or hit_tp:
            trigger = "STOP LOSS TRIGGERED 🛑" if hit_sl else "TAKE PROFIT TRIGGERED 🎯"
            exit_price = sl if hit_sl else tp
            if side == "LONG":
                pnl = (exit_price - entry) * pos["units"]
            else:
                pnl = (entry - exit_price) * pos["units"]

            return_cash = pos["amount_usd"] + pnl
            portfolio["cash_balance"] += return_cash
            closed_any = True

            history_entry = {
                "id": pos["id"],
                "symbol": pos["symbol"],
                "side": side,
                "entry_price": entry,
                "exit_price": exit_price,
                "amount_usd": pos["amount_usd"],
                "pnl_usd": pnl,
                "pnl_pct": (pnl / pos["amount_usd"]) * 100,
                "reason": "HIT_SL" if hit_sl else "HIT_TP",
                "closed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            portfolio["trade_history"].append(history_entry)

            print(f"[{trigger}] {side} {pos['symbol']} @ ${exit_price:,.4f}")
            print(f" -> Realized P&L: {'+' if pnl >= 0 else ''}${pnl:,.2f} ({history_entry['pnl_pct']:+.2f}%)")
        else:
            if side == "LONG":
                unrealized = (current_price - entry) * pos["units"]
            else:
                unrealized = (entry - current_price) * pos["units"]
            unrealized_pct = (unrealized / pos["amount_usd"]) * 100
            print(f"[ACTIVE] {side} {pos['symbol']} | Live: ${current_price:,.4f} | Floating PnL: {'+' if unrealized >= 0 else ''}${unrealized:,.2f} ({unrealized_pct:+.2f}%)")
            active_positions.append(pos)

    portfolio["positions"] = active_positions
    if closed_any:
        save_portfolio(portfolio, user)
        print("Updated portfolio saved.")
    print("=======================================================\n")

def close_position_manual(symbol_or_id, user_email=None):
    portfolio, user = load_portfolio(user_email)
    target = None
    remaining = []

    for pos in portfolio["positions"]:
        if pos["id"] == symbol_or_id or pos["symbol"].upper() == symbol_or_id.upper() or pos["symbol"].startswith(symbol_or_id.upper()):
            target = pos
        else:
            remaining.append(pos)

    if not target:
        print(f"Error: Position '{symbol_or_id}' not found in {user}'s portfolio.")
        return

    current_price = get_live_price(target["symbol"])
    if not current_price:
        print(f"Error: Could not retrieve market price to close {target['symbol']}.")
        return

    entry = target["entry_price"]
    side = target["side"]
    if side == "LONG":
        pnl = (current_price - entry) * target["units"]
    else:
        pnl = (entry - current_price) * target["units"]

    return_cash = target["amount_usd"] + pnl
    portfolio["cash_balance"] += return_cash
    portfolio["positions"] = remaining

    history_entry = {
        "id": target["id"],
        "symbol": target["symbol"],
        "side": side,
        "entry_price": entry,
        "exit_price": current_price,
        "amount_usd": target["amount_usd"],
        "pnl_usd": pnl,
        "pnl_pct": (pnl / target["amount_usd"]) * 100,
        "reason": "MANUAL_CLOSE",
        "closed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    portfolio["trade_history"].append(history_entry)
    save_portfolio(portfolio, user)

    print("\n=======================================================")
    print(f"       🔒 MANUAL CLOSE EXECUTED: {target['symbol']} [{user}]")
    print("=======================================================")
    print(f"Exit Price       : ${current_price:,.4f}")
    print(f"Realized P&L     : {'+' if pnl >= 0 else ''}${pnl:,.2f} ({history_entry['pnl_pct']:+.2f}%)")
    print(f"New Cash Balance : ${portfolio['cash_balance']:,.2f}")
    print("=======================================================\n")

def show_status(user_email=None):
    portfolio, user = load_portfolio(user_email)
    cash = portfolio["cash_balance"]
    unrealized_total = 0.0

    print("\n=======================================================")
    print(f"       📊 PAPER TRADING PORTFOLIO STATUS")
    print(f"       👤 Akun Terpilih: {user}")
    print("=======================================================")
    print(f"Cash Balance     : ${cash:,.2f}")

    if portfolio["positions"]:
        print(f"\n--- Open Positions ({len(portfolio['positions'])}) ---")
        for pos in portfolio["positions"]:
            price = get_live_price(pos["symbol"]) or pos["entry_price"]
            if pos["side"] == "LONG":
                upnl = (price - pos["entry_price"]) * pos["units"]
            else:
                upnl = (pos["entry_price"] - price) * pos["units"]
            unrealized_total += upnl
            upnl_pct = (upnl / pos["amount_usd"]) * 100
            print(f" * [{pos['id']}] {pos['side']} {pos['symbol']}")
            print(f"   Entry: ${pos['entry_price']:,.4f} | Live: ${price:,.4f} | SL: ${pos['stop_loss']:,.4f} | TP: ${pos.get('take_profit') or 0:,.4f}")
            print(f"   Size : ${pos['amount_usd']:,.2f} | PnL: {'+' if upnl >= 0 else ''}${upnl:,.2f} ({upnl_pct:+.2f}%)")
    else:
        print("\nNo open positions.")

    total_equity = cash + sum(p["amount_usd"] for p in portfolio["positions"]) + unrealized_total
    print("-------------------------------------------------------")
    print(f"Total Equity     : ${total_equity:,.2f}")
    total_realized = sum(h["pnl_usd"] for h in portfolio["trade_history"])
    win_trades = [h for h in portfolio["trade_history"] if h["pnl_usd"] > 0]
    total_closed = len(portfolio["trade_history"])
    win_rate = (len(win_trades) / total_closed * 100) if total_closed > 0 else 0.0

    print(f"Realized P&L     : {'+' if total_realized >= 0 else ''}${total_realized:,.2f}")
    print(f"Total Trades     : {total_closed} closed | Win Rate: {win_rate:.1f}%")
    print("=======================================================\n")

def reset_portfolio(balance=10000.0, user_email=None):
    _, user = load_portfolio(user_email)
    default_state = {
        "user_email": user,
        "initial_balance": balance,
        "cash_balance": balance,
        "positions": [],
        "trade_history": [],
        "created_at": datetime.now().isoformat()
    }
    save_portfolio(default_state, user)
    print(f"Portfolio untuk {user} berhasil di-reset ke saldo awal ${balance:,.2f} USDT.")

def main():
    parser = argparse.ArgumentParser(description="Trade Hands - Multi-Account Paper Execution Engine")
    sub = parser.add_subparsers(dest="command")

    # Status
    s_p = sub.add_parser("status", help="Lihat status portofolio")
    s_p.add_argument("--user", type=str, default=None, help="Email akun")

    # Open
    open_p = sub.add_parser("open", help="Buka posisi")
    open_p.add_argument("--symbol", type=str, required=True, help="Coin symbol (e.g. BTC, ETH, SOL)")
    open_p.add_argument("--side", type=str, required=True, choices=["LONG", "SHORT", "long", "short"])
    open_p.add_argument("--amount", type=float, required=True, help="Ukuran posisi USD")
    open_p.add_argument("--sl", type=float, required=True, help="Stop Loss price")
    open_p.add_argument("--tp", type=float, default=None, help="Take Profit target price")
    open_p.add_argument("--entry", type=float, default=None, help="Custom entry price")
    open_p.add_argument("--user", type=str, default=None, help="Email akun")

    # Update
    u_p = sub.add_parser("update", help="Update live prices dan eksekusi SL/TP")
    u_p.add_argument("--user", type=str, default=None, help="Email akun")

    # Close
    close_p = sub.add_parser("close", help="Tutup posisi manual")
    close_p.add_argument("--id", type=str, required=True, help="Position ID atau symbol")
    close_p.add_argument("--user", type=str, default=None, help="Email akun")

    # Reset
    reset_p = sub.add_parser("reset", help="Reset portfolio akun")
    reset_p.add_argument("--balance", type=float, default=10000.0, help="Saldo awal USD")
    reset_p.add_argument("--user", type=str, default=None, help="Email akun")

    args = parser.parse_args()
    if args.command == "status":
        show_status(args.user)
    elif args.command == "open":
        open_position(args.symbol, args.side, args.amount, args.sl, args.tp, args.entry, args.user)
    elif args.command == "update":
        update_positions(args.user)
    elif args.command == "close":
        close_position_manual(args.id, args.user)
    elif args.command == "reset":
        reset_portfolio(args.balance, args.user)
    else:
        show_status(None)

if __name__ == "__main__":
    main()

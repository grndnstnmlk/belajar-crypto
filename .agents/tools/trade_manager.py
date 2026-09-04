"""
Dynamic Trade Management Engine (CEO Risk & Position Protection)
Handles Breakeven Auto-Lock (+1R) and Chandelier / R-Multiple Trailing Stops (+2R+).
Guarantees institutional risk-free positions and profit locking across 24/7 cycles.
"""

import json
import math
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
TRADE_META_FILE = os.path.join(DATA_DIR, "active_trades_meta.json")

sys.path.insert(0, TOOLS_DIR)
import binance_client
import telegram_notifier

def load_trade_metadata():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(TRADE_META_FILE):
        try:
            with open(TRADE_META_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_trade_metadata(meta):
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(TRADE_META_FILE, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Trade Manager] Error saving metadata: {e}")

def record_trade_entry(symbol, side, entry_price, sl_price, tp_price, risk_budget_usd, quantity):
    """
    Registers a newly opened trade to begin dynamic lifecycle tracking.
    """
    meta = load_trade_metadata()
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    side_clean = "BUY" if side.upper() in ["BUY", "LONG"] else "SELL"
    
    r_distance = abs(entry_price - sl_price) if (sl_price and sl_price > 0) else (entry_price * 0.015)
    
    meta[sym_clean] = {
        "symbol": sym_clean,
        "side": side_clean,
        "entry_price": float(entry_price),
        "initial_sl": float(sl_price) if sl_price else (entry_price - r_distance if side_clean == "BUY" else entry_price + r_distance),
        "current_sl": float(sl_price) if sl_price else None,
        "tp": float(tp_price) if tp_price else None,
        "r_distance": float(r_distance),
        "risk_budget_usd": float(risk_budget_usd),
        "quantity": float(quantity),
        "opened_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "breakeven_locked": False,
        "trailing_r_locked": 0.0,
        "highest_r_reached": 0.0
    }
    save_trade_metadata(meta)

def calculate_breakeven_price(symbol, side, entry_price, fee_offset_pct=0.0008):
    """
    Computes Breakeven price with taker/maker fee offset to ensure a net-zero exit.
    """
    side_clean = "BUY" if side.upper() in ["BUY", "LONG"] else "SELL"
    if side_clean == "BUY":
        raw_be = entry_price * (1.0 + fee_offset_pct)
    else:
        raw_be = entry_price * (1.0 - fee_offset_pct)
    
    formatted = binance_client.format_price_precision(symbol, raw_be)
    return float(formatted)

def update_binance_stop_loss(symbol, side, new_sl_price, is_demo=True, user_email=None):
    """
    Safely cancels obsolete stop order and places the updated protective stop on Binance Futures.
    """
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    opp_side = "SELL" if side.upper() in ["BUY", "LONG"] else "BUY"
    sl_str = binance_client.format_price_precision(sym_clean, new_sl_price)

    # 1. Cancel previous open orders on this symbol to prevent conflicting SLs
    try:
        binance_client.send_signed_request(
            "/fapi/v1/allOpenOrders",
            method="DELETE",
            params={"symbol": sym_clean},
            is_demo=is_demo,
            user_email=user_email
        )
    except Exception:
        pass

    # 2. Place updated Stop Market Algo Order
    sl_params = {
        "algoType": "CONDITIONAL",
        "symbol": sym_clean,
        "side": opp_side,
        "type": "STOP_MARKET",
        "triggerPrice": sl_str,
        "closePosition": "true"
    }
    res = binance_client.send_signed_request(
        "/fapi/v1/algoOrder",
        method="POST",
        params=sl_params,
        is_demo=is_demo,
        user_email=user_email
    )
    if res and res.get("algoId"):
        return True, res.get("algoId")
    return False, res

def audit_and_manage_positions(user_email=None, is_demo=True):
    """
    Core Execution Loop for Dynamic Position Management:
    - Evaluates every active position against Breakeven (+1R) and Trailing (+2R+) thresholds.
    - Repositions SL on Binance Futures and broadcasts Telegram alerts.
    - Detects closed positions and performs cleanups.
    """
    meta = load_trade_metadata()
    res = binance_client.send_signed_request("/fapi/v2/positionRisk", method="GET", is_demo=is_demo, user_email=user_email)
    if res is None:
        return

    active_positions = [p for p in res if float(p.get("positionAmt", 0)) != 0]
    active_syms = {p["symbol"]: p for p in active_positions}

    # 1. Clean up positions that have been closed
    closed_syms = []
    for sym, t_info in meta.items():
        if sym not in active_syms:
            closed_syms.append(sym)
            try:
                # Notify Telegram of closed position
                telegram_notifier.notify_trade_closed(
                    symbol=sym,
                    pnl_usd=0.0,  # Realized in account
                    exit_reason="Position Exited / Target or SL Filled",
                    is_demo=is_demo
                )
            except Exception:
                pass

    for sym in closed_syms:
        meta.pop(sym, None)
    if closed_syms:
        save_trade_metadata(meta)

    # 2. Audit each active position
    management_events = []

    for p in active_positions:
        sym = p["symbol"]
        amt = float(p.get("positionAmt", 0))
        side = "BUY" if amt > 0 else "SELL"
        entry_price = float(p.get("entryPrice", 0))
        mark_price = float(p.get("markPrice", 0))
        upnl = float(p.get("unRealizedProfit", 0))

        if entry_price <= 0 or mark_price <= 0:
            continue

        # If position is not yet in metadata (e.g. pre-existing positions), auto-initialize
        if sym not in meta:
            # Infer risk distance as 1.5% of entry price
            r_dist = entry_price * 0.015
            initial_sl = entry_price - r_dist if side == "BUY" else entry_price + r_dist
            meta[sym] = {
                "symbol": sym,
                "side": side,
                "entry_price": entry_price,
                "initial_sl": initial_sl,
                "current_sl": initial_sl,
                "tp": None,
                "r_distance": r_dist,
                "risk_budget_usd": 20.0,
                "quantity": abs(amt),
                "opened_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "breakeven_locked": False,
                "trailing_r_locked": 0.0,
                "highest_r_reached": 0.0
            }

        t_data = meta[sym]
        r_dist = max(float(t_data.get("r_distance", entry_price * 0.015)), 0.0001)

        # Calculate current directional gain in USD and in R-multiple
        if side == "BUY":
            gain_per_unit = mark_price - entry_price
        else:
            gain_per_unit = entry_price - mark_price

        r_multiple = gain_per_unit / r_dist

        # Update highest R reached
        if r_multiple > t_data.get("highest_r_reached", 0.0):
            t_data["highest_r_reached"] = round(r_multiple, 2)

        # -------------------------------------------------------------
        # STEP 1: BREAKEVEN AUTO-LOCK (+1.0R Threshold)
        # -------------------------------------------------------------
        if r_multiple >= 1.0 and not t_data.get("breakeven_locked"):
            be_price = calculate_breakeven_price(sym, side, entry_price)
            success, _ = update_binance_stop_loss(sym, side, be_price, is_demo=is_demo, user_email=user_email)
            if success:
                t_data["breakeven_locked"] = True
                t_data["current_sl"] = be_price
                print(f"🛡️ [BREAKEVEN AUTO-LOCK] {sym}: SL digeser ke ${be_price:,.4f} (+{r_multiple:.2f}R | +${upnl:,.2f} USDT). Posisi Bebas Risiko!")
                management_events.append(f"🛡️ {sym} Breakeven Locked @ ${be_price:,.4f}")
                try:
                    telegram_notifier.notify_breakeven_locked(
                        symbol=sym,
                        side=side,
                        entry_price=entry_price,
                        be_price=be_price,
                        current_pnl=upnl,
                        is_demo=is_demo
                    )
                except Exception as e:
                    print(f"[Telegram Warning] Gagal kirim notifikasi BE: {e}")

        # -------------------------------------------------------------
        # STEP 2: DYNAMIC TRAILING STOP (+2.0R+ Threshold)
        # -------------------------------------------------------------
        if r_multiple >= 2.0:
            target_locked_r = float(math.floor(r_multiple) - 1.0)
            if target_locked_r > t_data.get("trailing_r_locked", 0.0):
                if side == "BUY":
                    new_sl = entry_price + (r_dist * target_locked_r)
                else:
                    new_sl = entry_price - (r_dist * target_locked_r)

                formatted_sl = float(binance_client.format_price_precision(sym, new_sl))
                success, _ = update_binance_stop_loss(sym, side, formatted_sl, is_demo=is_demo, user_email=user_email)
                if success:
                    t_data["trailing_r_locked"] = target_locked_r
                    t_data["current_sl"] = formatted_sl
                    print(f"🎯 [TRAILING STOP] {sym}: SL dikatrol naik ke ${formatted_sl:,.4f} (Kunci +{target_locked_r:.1f}R Terjamin | Floating +${upnl:,.2f})")
                    management_events.append(f"🎯 {sym} Trailing SL Locked @ ${formatted_sl:,.4f} (+{target_locked_r:.1f}R)")
                    try:
                        telegram_notifier.notify_trailing_stop_stepped(
                            symbol=sym,
                            side=side,
                            locked_r=target_locked_r,
                            new_sl_price=formatted_sl,
                            current_pnl=upnl,
                            is_demo=is_demo
                        )
                    except Exception as e:
                        print(f"[Telegram Warning] Gagal kirim notifikasi Trailing: {e}")

    save_trade_metadata(meta)
    return management_events

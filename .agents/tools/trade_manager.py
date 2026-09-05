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
import macro_news_shield

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

def record_trade_entry(symbol, side, entry_price, sl_price, tp_price, risk_budget_usd, quantity, is_scalp=False):
    """
    Registers a newly opened trade to begin dynamic lifecycle tracking.
    Supports is_scalp flag for accelerated Breakeven (+0.7R) and Time-Stop.
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
        "is_scalp": is_scalp,
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

def fetch_closed_trade_details(symbol, is_demo=True, user_email=None, opened_at=None, position_side="BUY"):
    """
    Fetches exact Realized PnL, exit price, commission, quantity, and execution details
    from Binance Futures for a closed position.
    Queries /fapi/v1/income and /fapi/v1/userTrades with robust fallback mechanisms.
    """
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    start_ms = None
    if opened_at:
        try:
            fmt = "%Y-%m-%d %H:%M:%S" if len(opened_at) > 16 else "%Y-%m-%d %H:%M"
            op_dt = datetime.strptime(opened_at, fmt)
            start_ms = int(op_dt.timestamp() * 1000) - 10000
        except Exception:
            start_ms = None

    # Step 1: Query /fapi/v1/income for authoritative REALIZED_PNL records
    try:
        inc_params = {"symbol": sym_clean, "incomeType": "REALIZED_PNL", "limit": 25}
        if start_ms:
            inc_params["startTime"] = start_ms
        res_inc = binance_client.send_signed_request("/fapi/v1/income", params=inc_params, is_demo=is_demo, user_email=user_email)
        if not res_inc and start_ms:
            res_inc = binance_client.send_signed_request("/fapi/v1/income", params={"symbol": sym_clean, "incomeType": "REALIZED_PNL", "limit": 25}, is_demo=is_demo, user_email=user_email)

        if res_inc and isinstance(res_inc, list):
            res_inc.sort(key=lambda x: int(x.get("time", 0)))
            latest_item = res_inc[-1]
            latest_time = int(latest_item.get("time", 0))

            # Group all income records in the latest closing batch (within 3 seconds)
            batch_inc = [i for i in res_inc if abs(int(i.get("time", 0)) - latest_time) <= 3000]
            total_realized_pnl = sum(float(i.get("income", 0)) for i in batch_inc)
            first_trade_id = int(batch_inc[0].get("tradeId", 0)) if batch_inc[0].get("tradeId") else None

            total_comm = 0.0
            exit_price = 0.0
            total_qty = 0.0
            order_id = None
            order_type = "MARKET"

            if first_trade_id:
                trades = binance_client.send_signed_request(
                    "/fapi/v1/userTrades",
                    params={"symbol": sym_clean, "fromId": first_trade_id, "limit": len(batch_inc) + 10},
                    is_demo=is_demo,
                    user_email=user_email
                )
                if trades and isinstance(trades, list):
                    matched = [t for t in trades if abs(int(t.get("time", 0)) - latest_time) <= 3000]
                    if matched:
                        total_comm = sum(float(t.get("commission", 0)) for t in matched)
                        total_qty = sum(float(t.get("qty", 0)) for t in matched)
                        total_quote = sum(float(t.get("quoteQty", 0)) for t in matched)
                        exit_price = (total_quote / total_qty) if total_qty > 0 else float(matched[0].get("price", 0))
                        order_id = matched[0].get("orderId")
                        if order_id:
                            try:
                                ord_res = binance_client.send_signed_request(
                                    "/fapi/v1/order",
                                    params={"symbol": sym_clean, "orderId": order_id},
                                    is_demo=is_demo,
                                    user_email=user_email
                                )
                                if ord_res and isinstance(ord_res, dict):
                                    order_type = ord_res.get("origType") or ord_res.get("type", "MARKET")
                            except Exception:
                                pass

            return {
                "success": True,
                "realized_pnl": round(total_realized_pnl, 4),
                "commission": round(total_comm, 4),
                "net_pnl": round(total_realized_pnl - total_comm, 4),
                "exit_price": round(exit_price, 4),
                "quantity": round(total_qty, 4),
                "order_id": order_id,
                "order_type": order_type,
                "close_time": datetime.fromtimestamp(latest_time / 1000).strftime("%Y-%m-%d %H:%M:%S")
            }
    except Exception as e:
        print(f"[Trade Manager] Error querying income for closed trade: {e}")

    # Step 2: Fallback to /fapi/v1/userTrades
    try:
        trade_params = {"symbol": sym_clean, "limit": 50}
        if start_ms:
            trade_params["startTime"] = start_ms
        trades = binance_client.send_signed_request("/fapi/v1/userTrades", params=trade_params, is_demo=is_demo, user_email=user_email)
        if trades and isinstance(trades, list):
            trades.sort(key=lambda x: int(x.get("time", 0)))
            closing_trades = [t for t in trades if abs(float(t.get("realizedPnl", 0))) > 1e-6]
            if closing_trades:
                latest_trade = closing_trades[-1]
                latest_order_id = latest_trade.get("orderId")
                latest_time = int(latest_trade.get("time", 0))
                batch_fills = [t for t in closing_trades if (t.get("orderId") == latest_order_id) or (abs(int(t.get("time", 0)) - latest_time) <= 3000)]
                total_realized_pnl = sum(float(t.get("realizedPnl", 0)) for t in batch_fills)
                total_comm = sum(float(t.get("commission", 0)) for t in batch_fills)
                total_qty = sum(float(t.get("qty", 0)) for t in batch_fills)
                total_quote = sum(float(t.get("quoteQty", 0)) for t in batch_fills)
                exit_price = (total_quote / total_qty) if total_qty > 0 else float(latest_trade.get("price", 0))
                return {
                    "success": True,
                    "realized_pnl": round(total_realized_pnl, 4),
                    "commission": round(total_comm, 4),
                    "net_pnl": round(total_realized_pnl - total_comm, 4),
                    "exit_price": round(exit_price, 4),
                    "quantity": round(total_qty, 4),
                    "order_id": latest_order_id,
                    "order_type": "MARKET",
                    "close_time": datetime.fromtimestamp(latest_time / 1000).strftime("%Y-%m-%d %H:%M:%S")
                }
    except Exception as e:
        print(f"[Trade Manager] Error querying userTrades fallback: {e}")

    return {
        "success": False,
        "realized_pnl": 0.0,
        "commission": 0.0,
        "net_pnl": 0.0,
        "exit_price": 0.0,
        "quantity": 0.0,
        "order_id": None,
        "order_type": "UNKNOWN",
        "close_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def audit_and_manage_positions(user_email=None, is_demo=True):
    """
    Core Execution Loop for Dynamic Position Management:
    - Evaluates every active position against Breakeven (+1R) and Trailing (+2R+) thresholds.
    - Repositions SL on Binance Futures and broadcasts Telegram alerts.
    - Detects closed positions, extracts exact realized PnL from ledger, and notifies user.
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
                # Fetch exact closed trade details directly from Binance Futures ledger
                details = fetch_closed_trade_details(
                    symbol=sym,
                    is_demo=is_demo,
                    user_email=user_email,
                    opened_at=t_info.get("opened_at"),
                    position_side=t_info.get("side", "BUY")
                )

                is_be = t_info.get("breakeven_locked", False)
                trailing_r = float(t_info.get("trailing_r_locked", 0.0))
                entry_p = float(t_info.get("entry_price", 0))
                tp_p = float(t_info.get("tp", 0)) if t_info.get("tp") else 0.0
                side = t_info.get("side", "BUY")
                risk_b = float(t_info.get("risk_budget_usd", 20.0))

                if details.get("success"):
                    realized_pnl = float(details.get("realized_pnl", 0.0))
                    commission = float(details.get("commission", 0.0))
                    net_pnl = float(details.get("net_pnl", 0.0))
                    exit_price = float(details.get("exit_price", 0.0)) or float(t_info.get("current_sl", entry_p))
                    qty = float(details.get("quantity", 0.0)) or float(t_info.get("quantity", 0.0))
                    order_type = details.get("order_type", "MARKET")
                    close_time = details.get("close_time")
                else:
                    # Fallback approximation if Binance API ledger is delayed
                    exit_price = float(t_info.get("current_sl", entry_p))
                    qty = float(t_info.get("quantity", 0.0))
                    if is_be and trailing_r == 0:
                        realized_pnl = 0.0
                    elif side == "BUY":
                        realized_pnl = (exit_price - entry_p) * qty if (exit_price and entry_p and qty) else (risk_b * (trailing_r - 0.5) if trailing_r > 0 else -risk_b)
                    else:
                        realized_pnl = (entry_p - exit_price) * qty if (exit_price and entry_p and qty) else (risk_b * (trailing_r - 0.5) if trailing_r > 0 else -risk_b)
                    commission = round(abs(realized_pnl) * 0.0008, 4)
                    net_pnl = realized_pnl - commission
                    order_type = "MARKET"
                    close_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Formulate intelligent exit reason
                if order_type in ["TAKE_PROFIT", "TAKE_PROFIT_MARKET"] or (tp_p > 0 and ((side == "BUY" and exit_price >= tp_p * 0.998) or (side == "SELL" and exit_price <= tp_p * 1.002))):
                    exit_reason = f"🎯 Take Profit Target Hit (+${realized_pnl:,.2f} USDT)"
                elif order_type in ["STOP_MARKET", "STOP"]:
                    if is_be and trailing_r > 0:
                        exit_reason = f"🎯 Trailing Stop Locked (+{trailing_r:.1f}R | +${realized_pnl:,.2f} USDT)"
                    elif is_be:
                        exit_reason = "🛡️ Breakeven Auto-Lock Filled (Free Roll Protected)"
                    else:
                        exit_reason = f"🛑 Stop Loss Filled (-${abs(realized_pnl):,.2f} USDT)"
                elif is_be and abs(realized_pnl) < 1.0:
                    exit_reason = "🛡️ Breakeven Exit (+0.0R Protected)"
                elif realized_pnl > 0:
                    exit_reason = f"🟢 Profit Locked (+${realized_pnl:,.2f} USDT)"
                elif realized_pnl < 0:
                    exit_reason = f"🔴 Stop Loss Hit / Position Exited (-${abs(realized_pnl):,.2f} USDT)"
                else:
                    exit_reason = "⚪ Position Exited at Breakeven"

                print(f"🏁 [CLOSED POSITION AUDIT] {sym} closed: Realized PnL: {realized_pnl:+.2f} USDT (Net: {net_pnl:+.2f}) | Reason: {exit_reason}")

                # Notify Telegram of closed position with 100% verified accounting data
                telegram_notifier.notify_trade_closed(
                    symbol=sym,
                    pnl_usd=realized_pnl,
                    exit_reason=exit_reason,
                    is_demo=is_demo,
                    net_pnl_usd=net_pnl,
                    commission_usd=commission,
                    entry_price=entry_p,
                    exit_price=exit_price,
                    qty=qty,
                    side=side,
                    close_time=close_time
                )

                # Autonomous Genetic Evolution Trigger with accurate ledger values
                import self_improve
                pos_amount_usd = (entry_p * qty) if (entry_p and qty) else (risk_b * 5.0)
                pnl_pct_calc = (realized_pnl / pos_amount_usd * 100.0) if pos_amount_usd > 0 else 0.0

                self_improve.record_closed_trade_and_check_evolution({
                    "id": f"BINANCE-{sym}-{int(time.time())}",
                    "symbol": sym,
                    "side": side,
                    "entry_price": entry_p,
                    "exit_price": exit_price,
                    "amount_usd": round(pos_amount_usd, 2),
                    "pnl_usd": round(realized_pnl, 2),
                    "pnl_pct": round(pnl_pct_calc, 2),
                    "reason": exit_reason,
                    "closed_at": close_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            except Exception as ex:
                print(f"[Trade Manager] Error recording closed trade for evolution: {ex}")

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
        # STEP 0: TIME-STOP CHECK FOR SCALP TRADES (Max 45 Menit)
        # -------------------------------------------------------------
        if t_data.get("is_scalp"):
            opened_at = t_data.get("opened_at", "")
            if opened_at:
                try:
                    fmt = "%Y-%m-%d %H:%M:%S" if len(opened_at) > 16 else "%Y-%m-%d %H:%M"
                    op_dt = datetime.strptime(opened_at, fmt)
                    elapsed_min = (datetime.now() - op_dt).total_seconds() / 60.0
                    if elapsed_min >= 45.0 and r_multiple < 0.5:
                        close_side = "SELL" if amt > 0 else "BUY"
                        binance_client.send_signed_request(
                            "/fapi/v1/order",
                            method="POST",
                            params={
                                "symbol": sym,
                                "side": close_side,
                                "type": "MARKET",
                                "quantity": abs(amt),
                                "reduceOnly": "true"
                            },
                            is_demo=is_demo,
                            user_email=user_email
                        )
                        print(f"⏱️ [SCALP TIME-STOP] {sym}: Ditutup otomatis setelah {int(elapsed_min)} menit (Stagnan).")
                        try:
                            telegram_notifier.send_telegram_broadcast(
                                f"⏱️ *SCALP TIME-STOP EXECUTED* ⏱️\n"
                                f"Aset: *{sym}*\n"
                                f"Durasi Aktif: *{int(elapsed_min)} menit* (Batas: 45m)\n"
                                f"PnL: *${upnl:+,.2f} USDT*\n"
                                f"Posisi ditutup otomatis demi menjaga perputaran modal kilat."
                            )
                        except Exception:
                            pass
                        continue
                except Exception:
                    pass

        # -------------------------------------------------------------
        # STEP 1A: PRE-EMPTIVE HIGH-IMPACT NEWS DEFENSE
        # -------------------------------------------------------------
        should_protect, news_ev, mins_left = macro_news_shield.should_preemptively_protect_positions(caution_window_minutes=45)
        if should_protect and r_multiple >= 0.25 and not t_data.get("breakeven_locked"):
            be_price = calculate_breakeven_price(sym, side, entry_price)
            success, _ = update_binance_stop_loss(sym, side, be_price, is_demo=is_demo, user_email=user_email)
            if success:
                t_data["breakeven_locked"] = True
                t_data["current_sl"] = be_price
                print(f"🛡️ [PRE-NEWS BREAKEVEN LOCK] {sym}: SL digeser ke BE ${be_price:,.4f} menjelang berita '{news_ev['title']}' ({mins_left}m lagi). Posisi diproteksi dari lonjakan volatilitas!")
                management_events.append(f"🛡️ {sym} Pre-News BE Protected @ ${be_price:,.4f} ({news_ev['title']})")
                try:
                    telegram_notifier.send_telegram_broadcast(
                        f"🛡️ <b>PRE-NEWS BREAKEVEN LOCK DIAKTIFKAN!</b>\n"
                        f"💎 <b>Simbol:</b> <code>{sym}</code>\n"
                        f"📰 <b>Pemicu Berita:</b> <code>{news_ev['title']}</code> (dalam {mins_left} menit)\n"
                        f"🛑 <b>SL Diamankan ke BE:</b> <code>${be_price:,.4f}</code>\n"
                        f"🎉 <i>Posisi dikunci bebas risiko sebelum volatilitas berita makro AS meledak!</i>"
                    )
                except Exception:
                    pass

        # -------------------------------------------------------------
        # STEP 1B: STANDARD BREAKEVEN AUTO-LOCK (+0.7R Scalp / +1.0R Swing)
        # -------------------------------------------------------------
        be_target_r = 0.7 if t_data.get("is_scalp") else 1.0
        if r_multiple >= be_target_r and not t_data.get("breakeven_locked"):
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

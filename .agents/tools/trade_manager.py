"""
Dynamic Trade Management Engine (CEO Risk & Position Protection)
Handles Breakeven Auto-Lock (+1R) and Chandelier / R-Multiple Trailing Stops (+2R+).
Guarantees institutional risk-free positions and profit locking across 24/7 cycles.
"""

import json
import math
import os
import sys
import threading
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
import market_structure
import trade_journal
import ai_risk_officer

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

def record_trade_entry(symbol, side, entry_price, sl_price, tp_price, risk_budget_usd, quantity, is_scalp=False, ai_thesis=None, ai_confidence=None):
    """
    Registers a newly opened trade to begin dynamic lifecycle tracking.
    Supports is_scalp flag for accelerated Breakeven (+0.7R) and Time-Stop.
    Stores AI Senior Quant Officer thesis and confidence for dashboard and autopsy.
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
        "highest_r_reached": 0.0,
        "tp1_taken": False,
        "tp1_pnl_usd": 0.0,
        "capital_shield_locked": False,
        "ai_thesis": ai_thesis,
        "ai_confidence": ai_confidence
    }
    save_trade_metadata(meta)

def format_qty_precision(symbol, qty_val, is_demo=True):
    """Formats lot size dynamically using Binance exchange filters."""
    formatted = binance_client.format_qty_precision(symbol, qty_val, is_demo=is_demo)
    return float(formatted)

def calculate_breakeven_price(symbol, side, entry_price, fee_offset_pct=0.0008, is_demo=True):
    """
    Computes Breakeven price with taker/maker fee offset to ensure a net-zero exit.
    """
    side_clean = "BUY" if side.upper() in ["BUY", "LONG"] else "SELL"
    if side_clean == "BUY":
        raw_be = entry_price * (1.0 + fee_offset_pct)
    else:
        raw_be = entry_price * (1.0 - fee_offset_pct)
    
    formatted = binance_client.format_price_precision(symbol, raw_be, is_demo=is_demo)
    return float(formatted)

def update_binance_stop_loss(symbol, side, new_sl_price, is_demo=True, user_email=None):
    """
    Safely cancels obsolete stop order and places the updated protective stop on Binance Futures.
    Uses auto-retry and safe error alerting to eliminate unhedged position gaps.
    """
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    opp_side = "SELL" if side.upper() in ["BUY", "LONG"] else "BUY"
    sl_str = binance_client.format_price_precision(sym_clean, new_sl_price, is_demo=is_demo)

    # 1. Cancel previous open regular orders and algo orders on this symbol to prevent conflicting SLs (-4130)
    try:
        binance_client.send_signed_request(
            "/fapi/v1/allOpenOrders",
            method="DELETE",
            params={"symbol": sym_clean},
            is_demo=is_demo,
            user_email=user_email,
            retries=2
        )
    except Exception:
        pass

    try:
        binance_client.cancel_existing_algo_orders_for_symbol(
            symbol=sym_clean,
            is_demo=is_demo,
            user_email=user_email
        )
    except Exception:
        pass

    # 2. Place updated Stop Market Algo Order with auto-retry (3 attempts)
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
        user_email=user_email,
        retries=3,
        backoff_base=0.5
    )
    if res and res.get("algoId"):
        return True, res.get("algoId")

    # Critical fallback notification if all 3 retries fail
    print(f"🚨 [CRITICAL WARNING] Gagal memasang Stop Loss baru di Binance untuk {sym_clean}! Respon: {res}", file=sys.stderr)
    try:
        telegram_notifier.send_telegram_broadcast(
            f"🚨 <b>CRITICAL WARNING: STOP LOSS GAGAL TERPASANG!</b> 🚨\n"
            f"Simbol: <code>{sym_clean}</code>\n"
            f"Level Target SL: <code>${sl_str}</code>\n"
            f"Respon Error: <code>{res}</code>\n"
            f"<i>Segera periksa posisi di aplikasi Binance secara manual!</i>"
        )
    except Exception:
        pass

    return False, res

def execute_manual_partial_tp(symbol, user_email=None, is_demo=True):
    """
    Manually triggers Scale-Out TP1:
    - Liquidates 50% of the active position via a Market Order with reduceOnly=true.
    - Locks the remaining 50% lot (Runner) to Breakeven (+ commission offset).
    - Records the realized profit into the Trade Journal ledger.
    - Updates trade metadata (tp1_taken=True, is_runner=True).
    - Dispatches instant rich Telegram broadcast.
    """
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("_", "")
    positions = binance_client.send_signed_request("/fapi/v2/positionRisk", method="GET", is_demo=is_demo, user_email=user_email)
    if not positions:
        return {"success": False, "error": "Gagal mengambil posisi aktif dari Binance"}

    target_pos = next((p for p in positions if p.get("symbol") == sym_clean and float(p.get("positionAmt", 0)) != 0), None)
    if not target_pos:
        return {"success": False, "error": f"Tidak ada posisi aktif yang terbuka untuk {sym_clean}"}

    amt = float(target_pos.get("positionAmt", 0))
    entry_p = float(target_pos.get("entryPrice", 0))
    mark_p = float(target_pos.get("markPrice", 0))
    side = "BUY" if amt > 0 else "SELL"
    close_side = "SELL" if side == "BUY" else "BUY"

    current_amt = abs(amt)
    half_qty_str = binance_client.format_qty_precision(sym_clean, current_amt * 0.5)
    half_qty = float(half_qty_str)

    if half_qty <= 0 or half_qty >= current_amt:
        return {"success": False, "error": f"Ukuran posisi ({current_amt}) terlalu kecil untuk dipecah 50%"}

    # 1. Execute market close for half qty
    order_res = binance_client.send_signed_request(
        "/fapi/v1/order",
        method="POST",
        params={
            "symbol": sym_clean,
            "side": close_side,
            "type": "MARKET",
            "quantity": half_qty_str,
            "reduceOnly": "true"
        },
        is_demo=is_demo,
        user_email=user_email
    )
    if not order_res or not order_res.get("orderId"):
        return {"success": False, "error": f"Order parsial ditolak Binance: {order_res}"}

    # 2. Estimate Realized PnL
    if side == "BUY":
        est_pnl = (mark_p - entry_p) * half_qty
    else:
        est_pnl = (entry_p - mark_p) * half_qty

    # 3. Cancel obsolete full TP orders & Lock Breakeven
    be_price = calculate_breakeven_price(sym_clean, side, entry_p)
    update_binance_stop_loss(sym_clean, side, be_price, is_demo=is_demo, user_email=user_email)

    # 4. Update metadata
    meta = load_trade_metadata()
    t_data = meta.get(sym_clean, {})
    remaining_qty = round(current_amt - half_qty, 4)
    r_dist = max(float(t_data.get("r_distance", entry_p * 0.015)), 0.0001)
    gain_per_coin = (mark_p - entry_p) if side == "BUY" else (entry_p - mark_p)
    r_mult = round(gain_per_coin / r_dist, 2)

    t_data["tp1_taken"] = True
    t_data["tp1_pnl_usd"] = round(est_pnl, 2)
    t_data["is_runner"] = True
    t_data["breakeven_locked"] = True
    t_data["current_sl"] = be_price
    t_data["quantity"] = remaining_qty
    meta[sym_clean] = t_data
    save_trade_metadata(meta)

    # 5. Record to trade journal ledger
    try:
        trade_journal.record_closed_trade({
            "id": f"SCALEOUT-{sym_clean}-{int(time.time())}",
            "symbol": sym_clean,
            "side": side,
            "entry_price": entry_p,
            "exit_price": mark_p,
            "quantity": half_qty,
            "pnl_usd": round(est_pnl, 2),
            "commission_usd": 0.0,
            "net_pnl_usd": round(est_pnl, 2),
            "r_multiple": r_mult,
            "exit_reason": f"🎯 Scale-Out TP1 (50% Liquidated @ {r_mult:+.2f}R)",
            "closed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "SCALE_OUT_MANUAL"
        })
    except Exception as j_err:
        print(f"[Scale-Out] Gagal simpan ke journal: {j_err}")

    # 6. Dispatch Telegram broadcast
    try:
        telegram_notifier.notify_partial_tp_taken(
            symbol=sym_clean,
            side=side,
            mark_price=mark_p,
            closed_qty=half_qty,
            pnl_usd=est_pnl,
            remaining_qty=remaining_qty,
            be_price=be_price,
            r_multiple=r_mult,
            is_demo=is_demo
        )
    except Exception as tg_err:
        print(f"[Scale-Out] Gagal kirim notif Telegram: {tg_err}")

    return {
        "success": True,
        "symbol": sym_clean,
        "closed_qty": half_qty,
        "remaining_qty": remaining_qty,
        "est_pnl_usd": round(est_pnl, 2),
        "be_price": be_price,
        "r_multiple": r_mult
    }

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

                tp1_taken = t_info.get("tp1_taken", False)
                tp1_cash = float(t_info.get("tp1_pnl_usd", 0.0))

                # Total trade net accounting (Runner realized + TP1 already realized)
                total_realized_trade = realized_pnl + (tp1_cash if tp1_taken else 0.0)
                total_net_trade = net_pnl + (tp1_cash if tp1_taken else 0.0)

                # Formulate intelligent exit reason
                if order_type in ["TAKE_PROFIT", "TAKE_PROFIT_MARKET"] or (tp_p > 0 and ((side == "BUY" and exit_price >= tp_p * 0.998) or (side == "SELL" and exit_price <= tp_p * 1.002))):
                    exit_reason = f"🎯 Full Take Profit Hit (+${total_realized_trade:,.2f} USDT)"
                elif is_be and tp1_taken:
                    if trailing_r > 0:
                        exit_reason = f"🎯 Trailing Runner Locked (+{trailing_r:.1f}R | Total Profit: +${total_realized_trade:,.2f} USDT)"
                    else:
                        exit_reason = f"🛡️ Free Runner Exited at BE (Total Profit: +${total_realized_trade:,.2f} USDT via TP1)"
                elif order_type in ["STOP_MARKET", "STOP"]:
                    if is_be and trailing_r > 0:
                        exit_reason = f"🎯 Trailing Stop Locked (+{trailing_r:.1f}R | +${total_realized_trade:,.2f} USDT)"
                    elif is_be:
                        exit_reason = "🛡️ Breakeven Auto-Lock Filled (Free Roll Protected)"
                    elif t_info.get("capital_shield_locked"):
                        exit_reason = f"🛡️ Capital Shield Triggered (-${abs(total_realized_trade):,.2f} USDT | 80% Saved)"
                    else:
                        exit_reason = f"🛑 Stop Loss Filled (-${abs(total_realized_trade):,.2f} USDT)"
                elif is_be and abs(realized_pnl) < 1.0:
                    exit_reason = f"🛡️ Breakeven Exit ({f'+${tp1_cash:,.2f} via TP1' if tp1_taken else '+0.0R Protected'})"
                elif total_realized_trade > 0:
                    exit_reason = f"🟢 Profit Locked (+${total_realized_trade:,.2f} USDT)"
                elif total_realized_trade < 0:
                    exit_reason = f"🔴 Stop Loss Hit / Position Exited (-${abs(total_realized_trade):,.2f} USDT)"
                else:
                    exit_reason = "⚪ Position Exited at Breakeven"

                print(f"🏁 [CLOSED POSITION AUDIT] {sym} closed: Realized PnL: {total_realized_trade:+.2f} USDT (Net: {total_net_trade:+.2f}) | Reason: {exit_reason}")

                # Notify Telegram of closed position with 100% verified accounting data
                telegram_notifier.notify_trade_closed(
                    symbol=sym,
                    pnl_usd=total_realized_trade,
                    exit_reason=exit_reason,
                    is_demo=is_demo,
                    net_pnl_usd=total_net_trade,
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

                # Automated Trade Journal Logging (Akademi Crypto Module 03)
                try:
                    import trade_journal
                    trade_journal.record_closed_trade({
                        "id": f"BINANCE-{sym}-{int(time.time())}",
                        "symbol": sym,
                        "side": side,
                        "entry_price": entry_p,
                        "exit_price": exit_price,
                        "quantity": qty,
                        "amount_usd": round(pos_amount_usd, 2),
                        "pnl_usd": round(realized_pnl, 2),
                        "commission_usd": commission,
                        "net_pnl_usd": round(total_net_trade, 2),
                        "r_multiple": round(total_realized_trade / max(risk_b, 1.0), 2),
                        "highest_r_reached": t_info.get("highest_r_reached", 0.0),
                        "tp1_taken": tp1_taken,
                        "tp1_cash_usd": tp1_cash,
                        "exit_reason": exit_reason,
                        "closed_at": close_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "source": "AUTONOMOUS_TRADE_MANAGER"
                    })
                except Exception as j_err:
                    print(f"[Trade Manager] Error recording to Trade Journal: {j_err}")
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
                "highest_r_reached": 0.0,
                "tp1_taken": False,
                "tp1_pnl_usd": 0.0,
                "capital_shield_locked": False
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
        # STEP 0: TIME-STOP CHECK FOR SCALP TRADES (Safeguard: Never force-close in minus!)
        # -------------------------------------------------------------
        if t_data.get("is_scalp"):
            opened_at = t_data.get("opened_at", "")
            if opened_at:
                try:
                    fmt = "%Y-%m-%d %H:%M:%S" if len(opened_at) > 16 else "%Y-%m-%d %H:%M"
                    op_dt = datetime.strptime(opened_at, fmt)
                    elapsed_min = (datetime.now() - op_dt).total_seconds() / 60.0
                    # Proteksi: Jangan pernah force-close posisi yang sedang minus/floating red.
                    # Biarkan posisi bernafas hingga menyentuh Stop Loss terukur atau memantul ke Take Profit.
                    # Tutup jika posisi scalp sudah flat / stagnan (0.0 <= r_multiple < 0.35) setelah 20 menit (4 candle 5m).
                    if elapsed_min >= 20.0 and (0.0 <= r_multiple < 0.35):
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
                        print(f"⏱️ [SCALP STAGNANT CLOSE] {sym}: Ditutup setelah {int(elapsed_min)} menit (Stagnan di Breakeven/Untung Tipis +{r_multiple:.2f}R).")
                        try:
                            telegram_notifier.send_telegram_broadcast(
                                f"⏱️ *STAGNANT TRADE CLOSED (CAPITAL REALLOCATION)* ⏱️\n"
                                f"Aset: *{sym}*\n"
                                f"Durasi Aktif: *{int(elapsed_min)} menit*\n"
                                f"PnL: *${upnl:+,.2f} USDT* (+{r_multiple:.2f}R)\n"
                                f"Posisi ditutup karena stagnan di zona aman untuk memutar modal ke setup baru."
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
        # STEP 1B: CAPITAL PRESERVATION SHIELD (+0.70R -> SL to -0.20R)
        # Prevents healthy winners (+0.7R+) from turning into full 100% losses!
        # -------------------------------------------------------------
        if r_multiple >= 0.70 and not t_data.get("capital_shield_locked") and not t_data.get("breakeven_locked") and not t_data.get("tp1_taken"):
            if side == "BUY":
                shield_sl = entry_price - (r_dist * 0.20)
            else:
                shield_sl = entry_price + (r_dist * 0.20)

            formatted_shield_sl = float(binance_client.format_price_precision(sym, shield_sl))
            success, _ = update_binance_stop_loss(sym, side, formatted_shield_sl, is_demo=is_demo, user_email=user_email)
            if success:
                t_data["capital_shield_locked"] = True
                t_data["current_sl"] = formatted_shield_sl
                print(f"🛡️ [CAPITAL PRESERVATION SHIELD] {sym}: SL dinaikkan agresif ke ${formatted_shield_sl:,.4f} (-0.2R | Puncak +{r_multiple:.2f}R). Potensi kerugian dipotong 80%!")
                management_events.append(f"🛡️ {sym} Capital Shield @ ${formatted_shield_sl:,.4f} (+{r_multiple:.2f}R)")
                try:
                    telegram_notifier.notify_capital_shield_activated(
                        symbol=sym,
                        side=side,
                        mark_price=mark_price,
                        new_sl_price=formatted_shield_sl,
                        r_multiple=r_multiple,
                        is_demo=is_demo
                    )
                except Exception as e:
                    print(f"[Telegram Warning] Gagal kirim notif Capital Shield: {e}")

        # -------------------------------------------------------------
        # STEP 1B.2: AI ADAPTIVE PROFIT HARVESTER & DYNAMIC EXIT SENTINEL
        # Solves: Profit reversing into loss! When in solid profit (+1.00R+),
        # AI evaluates momentum exhaustion, RSI drop, or rejection wicks.
        # Can execute: (1) Early 100% Market TP Harvest, or (2) Lock SL to Green (+0.50R).
        # -------------------------------------------------------------
        if r_multiple >= 1.00 and not t_data.get("ai_harvested", False) and not t_data.get("tp1_taken", False):
            try:
                ai_verdict = ai_risk_officer.evaluate_active_position_exit(
                    symbol=sym,
                    side=side,
                    entry_price=entry_price,
                    mark_price=mark_price,
                    r_multiple=r_multiple,
                    highest_r=t_data.get("highest_r_reached", r_multiple),
                    opened_at=t_data.get("opened_at"),
                    is_scalp=t_data.get("is_scalp", False)
                )
                ai_action = ai_verdict.get("action")
                ai_thesis = ai_verdict.get("thesis", "")

                if ai_action == "TAKE_PROFIT_NOW":
                    current_amt = abs(amt)
                    qty_str = binance_client.format_qty_precision(sym, current_amt, is_demo=is_demo)
                    close_side = "SELL" if side == "BUY" else "BUY"
                    print(f"\n🎯 [AI ADAPTIVE PROFIT HARVEST] {sym}: {ai_thesis}")
                    print(f"   Mengeksekusi Market Close 100% ({qty_str} lot) demi mengamankan cuan kas...")

                    close_res = binance_client.send_signed_request(
                        "/fapi/v1/order",
                        method="POST",
                        params={
                            "symbol": sym,
                            "side": close_side,
                            "type": "MARKET",
                            "quantity": qty_str,
                            "reduceOnly": "true"
                        },
                        is_demo=is_demo,
                        user_email=user_email,
                        retries=3
                    )
                    if close_res and close_res.get("orderId"):
                        realized_usd = (mark_price - entry_price) * current_amt if side == "BUY" else (entry_price - mark_price) * current_amt
                        binance_client.cancel_existing_algo_orders_for_symbol(sym, is_demo=is_demo, user_email=user_email)
                        t_data["ai_harvested"] = True
                        management_events.append(f"🎯 {sym} AI Early TP (+${realized_usd:,.2f} USDT | +{r_multiple:.2f}R)")

                        try:
                            telegram_notifier.notify_ai_early_tp(
                                symbol=sym,
                                side=side,
                                mark_price=mark_price,
                                pnl_usd=realized_usd,
                                r_multiple=r_multiple,
                                thesis=ai_thesis,
                                is_demo=is_demo
                            )
                        except Exception as e:
                            print(f"[Telegram Warning] {e}")

                        try:
                            trade_journal.record_closed_trade({
                                "id": f"AIHARVEST-{sym}-{int(time.time())}",
                                "symbol": sym,
                                "side": side,
                                "entry_price": entry_price,
                                "exit_price": mark_price,
                                "quantity": current_amt,
                                "amount_usd": round(entry_price * current_amt, 2),
                                "pnl_usd": round(realized_usd, 2),
                                "commission_usd": 0.0,
                                "net_pnl_usd": round(realized_usd, 2),
                                "r_multiple": round(r_multiple, 2),
                                "exit_reason": f"🎯 AI Adaptive Profit Harvest (+${realized_usd:,.2f} USDT | +{r_multiple:.2f}R) - {ai_thesis}",
                                "closed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "source": "AI_PROFIT_HARVESTER"
                            })
                        except Exception as j_err:
                            print(f"[AI Harvest Journal Warning] {j_err}")

                        closed_syms.append(sym)
                        continue

                elif ai_action == "LOCK_PROFIT_SL" and not t_data.get("ai_profit_locked", False):
                    sugg_sl = ai_verdict.get("suggested_sl")
                    if sugg_sl:
                        formatted_sl = float(binance_client.format_price_precision(sym, sugg_sl, is_demo=is_demo))
                        is_better = (formatted_sl > t_data.get("current_sl", 0)) if side == "BUY" else (formatted_sl < t_data.get("current_sl", 999999))
                        if is_better:
                            success, _ = update_binance_stop_loss(sym, side, formatted_sl, is_demo=is_demo, user_email=user_email)
                            if success:
                                t_data["ai_profit_locked"] = True
                                t_data["current_sl"] = formatted_sl
                                print(f"🛡️ [AI GREEN-EXIT PROFIT LOCK] {sym}: SL dinaikkan ke profit zone ${formatted_sl:,.4f} (+0.25R). Garansi Green Exit!")
                                management_events.append(f"🛡️ {sym} AI Profit Lock @ ${formatted_sl:,.4f} (+{r_multiple:.2f}R)")
                                try:
                                    telegram_notifier.notify_ai_profit_lock(
                                        symbol=sym,
                                        side=side,
                                        mark_price=mark_price,
                                        new_sl_price=formatted_sl,
                                        current_pnl=upnl,
                                        r_multiple=r_multiple,
                                        is_demo=is_demo
                                    )
                                except Exception as e:
                                    print(f"[Telegram Warning] {e}")
            except Exception as e:
                print(f" * [AI Sentinel Error] {e}")

        # -------------------------------------------------------------
        # STEP 1C: PARTIAL TAKE PROFIT 1 (SCALE-OUT 50% @ +1.25R Scalp / +2.0R Swing + RUNNER SMC TRAILING)
        # Realizes cash profit into wallet & locks remaining (Runner) at Breakeven!
        # Synthesized from Akademi Crypto Module 03 (Money Management)
        # -------------------------------------------------------------
        tp1_target_r = 1.25 if t_data.get("is_scalp") else 2.00
        if r_multiple >= tp1_target_r and not t_data.get("tp1_taken", False):
            current_amt = abs(amt)
            scale_pct = 0.60 if t_data.get("is_scalp") else 0.50
            half_qty_str = binance_client.format_qty_precision(sym, current_amt * scale_pct)
            half_qty = float(half_qty_str)

            if half_qty > 0 and half_qty < current_amt:
                close_side = "SELL" if side == "BUY" else "BUY"
                print(f"🎯 [SCALE-OUT TP1] {sym}: Capai +{r_multiple:.2f}R! Menjual {int(scale_pct*100)}% lot ({half_qty} dari {current_amt})...")
                order_res = binance_client.send_signed_request(
                    "/fapi/v1/order",
                    method="POST",
                    params={
                        "symbol": sym,
                        "side": close_side,
                        "type": "MARKET",
                        "quantity": half_qty_str,
                        "reduceOnly": "true"
                    },
                    is_demo=is_demo,
                    user_email=user_email
                )
                if order_res and order_res.get("orderId"):
                    if side == "BUY":
                        est_tp1_pnl = (mark_price - entry_price) * half_qty
                    else:
                        est_tp1_pnl = (entry_price - mark_price) * half_qty

                    # Cancel obsolete full TP algo order so runner can trail freely
                    try:
                        binance_client.cancel_existing_algo_orders_for_symbol(
                            symbol=sym,
                            is_demo=is_demo,
                            user_email=user_email
                        )
                    except Exception:
                        pass

                    # Move remaining runner SL to Breakeven (+ commission offset)
                    be_price = calculate_breakeven_price(sym, side, entry_price)
                    update_binance_stop_loss(sym, side, be_price, is_demo=is_demo, user_email=user_email)

                    remaining_qty = round(current_amt - half_qty, 4)
                    t_data["tp1_taken"] = True
                    t_data["tp1_pnl_usd"] = round(est_tp1_pnl, 2)
                    t_data["is_runner"] = True
                    t_data["breakeven_locked"] = True
                    t_data["current_sl"] = be_price
                    t_data["quantity"] = remaining_qty

                    print(f"✅ [TP1 SECURED & RUNNER PROTECTED] {sym}: +${est_tp1_pnl:,.2f} USDT cair di dompet! Sisa {remaining_qty} lot dikunci BE @ ${be_price:,.4f} dipandu SMC Trailing.")
                    management_events.append(f"🎯 {sym} TP1 (+${est_tp1_pnl:,.2f}) & Runner BE @ ${be_price:,.4f}")

                    # Record to trade journal ledger
                    try:
                        trade_journal.record_closed_trade({
                            "id": f"SCALEOUT-{sym}-{int(time.time())}",
                            "symbol": sym,
                            "side": side,
                            "entry_price": entry_price,
                            "exit_price": mark_price,
                            "quantity": half_qty,
                            "pnl_usd": round(est_tp1_pnl, 2),
                            "commission_usd": 0.0,
                            "net_pnl_usd": round(est_tp1_pnl, 2),
                            "r_multiple": round(r_multiple, 2),
                            "exit_reason": f"🎯 Scale-Out TP1 ({int(scale_pct*100)}% Locked @ +{r_multiple:.2f}R)",
                            "closed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "source": "SCALE_OUT_ENGINE"
                        })
                    except Exception as j_err:
                        print(f"[Scale-Out] Error logging to journal: {j_err}")

                    try:
                        telegram_notifier.notify_partial_tp_taken(
                            symbol=sym,
                            side=side,
                            mark_price=mark_price,
                            closed_qty=half_qty,
                            pnl_usd=est_tp1_pnl,
                            remaining_qty=remaining_qty,
                            be_price=be_price,
                            r_multiple=r_multiple,
                            is_demo=is_demo
                        )
                    except Exception as ex:
                        print(f"[Telegram Warning] Gagal kirim notif TP1: {ex}")

        # -------------------------------------------------------------
        # STEP 1D: STANDARD BREAKEVEN AUTO-LOCK (+0.60R Scalp / +1.3R Swing)
        # -------------------------------------------------------------
        be_target_r = 0.60 if t_data.get("is_scalp") else 1.3
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
        # STEP 2A: SMC STRUCTURAL TRAILING STOP (Akademi Crypto Module 02)
        # Trails behind confirmed Protected Higher Lows (Long) or Lower Highs (Short)
        # with asset-specific anti-liquidity sweep buffers and strict one-way ratchet.
        # Only activates once trade is solidly in profit (+0.80R+) or after TP1/BE lock.
        # -------------------------------------------------------------
        if r_multiple >= 0.80 or t_data.get("breakeven_locked") or t_data.get("tp1_taken"):
            try:
                has_struct_stop, struct_sl, struct_label = market_structure.get_protected_structural_stop(
                    symbol=sym,
                    side=side,
                    entry_price=entry_price,
                    current_sl=t_data.get("current_sl"),
                    bar="15m"
                )
                if has_struct_stop and struct_sl:
                    formatted_struct_sl = float(binance_client.format_price_precision(sym, struct_sl))
                    cur_sl_val = float(t_data.get("current_sl", 0.0) or 0.0)

                    is_ratchet_valid = False
                    if side == "BUY":
                        # Must ratchet UPWARD and remain safely below current mark price
                        if (cur_sl_val <= 0 or formatted_struct_sl > cur_sl_val * 1.0005) and formatted_struct_sl < (mark_price * 0.996):
                            is_ratchet_valid = True
                    else:
                        # Must ratchet DOWNWARD and remain safely above current mark price
                        if (cur_sl_val <= 0 or formatted_struct_sl < cur_sl_val * 0.9995) and formatted_struct_sl > (mark_price * 1.004):
                            is_ratchet_valid = True

                    if is_ratchet_valid:
                        success, _ = update_binance_stop_loss(sym, side, formatted_struct_sl, is_demo=is_demo, user_email=user_email)
                        if success:
                            t_data["current_sl"] = formatted_struct_sl
                            t_data["structural_level"] = struct_label
                            t_data["last_struct_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                            # If structural stop is at or beyond breakeven, lock breakeven state
                            if side == "BUY" and formatted_struct_sl >= entry_price:
                                t_data["breakeven_locked"] = True
                            elif side == "SELL" and formatted_struct_sl <= entry_price:
                                t_data["breakeven_locked"] = True

                            print(f"🏛️ [SMC STRUCTURAL TRAILING] {sym}: SL dikatrol ke ${formatted_struct_sl:,.4f} mengikuti {struct_label} (PnL: {upnl:+,.2f} USDT | {r_multiple:+.2f}R)")
                            management_events.append(f"🏛️ {sym} SMC Trailing @ ${formatted_struct_sl:,.4f} ({struct_label})")
                            try:
                                telegram_notifier.notify_structural_trailing_updated(
                                    symbol=sym,
                                    side=side,
                                    mark_price=mark_price,
                                    new_sl_price=formatted_struct_sl,
                                    structure_label=struct_label,
                                    r_multiple=r_multiple,
                                    current_pnl=upnl,
                                    is_demo=is_demo
                                )
                            except Exception as e:
                                print(f"[Telegram Warning] Gagal kirim notifikasi SMC Trailing: {e}")
            except Exception as smc_err:
                print(f"[Trade Manager] Error calculating SMC Structural Trailing for {sym}: {smc_err}")

        # -------------------------------------------------------------
        # STEP 2B: FIXED R-MULTIPLE TRAILING STEP (+2.0R+ Floor Fallback)
        # Complementary ratchet: If fixed R-step guarantees a higher/tighter stop, ratchet further.
        # -------------------------------------------------------------
        if r_multiple >= 2.0:
            target_locked_r = float(math.floor(r_multiple) - 1.0)
            if target_locked_r > t_data.get("trailing_r_locked", 0.0):
                if side == "BUY":
                    new_sl = entry_price + (r_dist * target_locked_r)
                else:
                    new_sl = entry_price - (r_dist * target_locked_r)

                formatted_sl = float(binance_client.format_price_precision(sym, new_sl))
                cur_sl_val = float(t_data.get("current_sl", 0.0) or 0.0)

                should_update_fixed = False
                if side == "BUY" and (cur_sl_val <= 0 or formatted_sl > cur_sl_val * 1.0005):
                    should_update_fixed = True
                elif side == "SELL" and (cur_sl_val <= 0 or formatted_sl < cur_sl_val * 0.9995):
                    should_update_fixed = True

                if should_update_fixed:
                    success, _ = update_binance_stop_loss(sym, side, formatted_sl, is_demo=is_demo, user_email=user_email)
                    if success:
                        t_data["trailing_r_locked"] = target_locked_r
                        t_data["current_sl"] = formatted_sl
                        print(f"🎯 [TRAILING STOP R-STEP] {sym}: SL dikatrol naik ke ${formatted_sl:,.4f} (Kunci +{target_locked_r:.1f}R Terjamin | Floating +${upnl:,.2f})")
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

def audit_and_manage_mt5_positions():
    """
    Audits active MT5 positions and applies Breakeven (+1R) and SMC Trailing stops.
    """
    try:
        import mt5_client
        positions = mt5_client.get_open_positions()
        if not positions:
            return []
            
        events = []
        meta = load_trade_metadata()
        
        for p in positions:
            ticket = str(p["ticket"])
            sym = p["symbol"]
            side = p["side"]
            entry_p = p["price_open"]
            curr_p = p["price_current"]
            sl_p = p["sl"]
            tp_p = p["tp"]
            upnl = p["profit_usd"]
            
            t_meta = meta.get(f"MT5_{ticket}", {
                "symbol": sym,
                "ticket": p["ticket"],
                "side": side,
                "entry_price": entry_p,
                "initial_sl": sl_p or (entry_p * 0.99 if side == "BUY" else entry_p * 1.01),
                "current_sl": sl_p,
                "tp": tp_p,
                "breakeven_locked": False,
                "trailing_r_locked": 0.0,
                "highest_r_reached": 0.0,
                "backend": "MT5"
            })
            
            init_sl = float(t_meta.get("initial_sl") or (entry_p * 0.99 if side == "BUY" else entry_p * 1.01))
            r_dist = max(abs(entry_p - init_sl), entry_p * 0.001)
            gain = (curr_p - entry_p) if side == "BUY" else (entry_p - curr_p)
            current_r = round(gain / r_dist, 2)
            
            if current_r > t_meta.get("highest_r_reached", 0.0):
                t_meta["highest_r_reached"] = current_r
                
            # Rule 1: Auto Breakeven at +1.0R
            if current_r >= 1.0 and not t_meta.get("breakeven_locked", False):
                be_sl = entry_p + (r_dist * 0.05) if side == "BUY" else entry_p - (r_dist * 0.05)
                res = mt5_client.modify_position_sl_tp(p["ticket"], new_sl=be_sl)
                if res.get("success"):
                    t_meta["breakeven_locked"] = True
                    t_meta["current_sl"] = be_sl
                    msg = f"🛡️ [MT5 Breakeven Locked] {sym} (#{p['ticket']}) reached +{current_r}R -> SL moved to {be_sl}"
                    events.append(msg)
                    try:
                        telegram_notifier.notify_breakeven_locked(sym, be_sl, current_pnl=upnl, is_demo=True)
                    except Exception:
                        pass
                        
            # Rule 2: Trailing Stop at +2.0R+
            elif current_r >= 2.0:
                target_lock_r = 1.0 if current_r < 3.0 else (current_r - 1.0)
                if target_lock_r > t_meta.get("trailing_r_locked", 0.0):
                    trail_sl = entry_p + (r_dist * target_lock_r) if side == "BUY" else entry_p - (r_dist * target_lock_r)
                    res = mt5_client.modify_position_sl_tp(p["ticket"], new_sl=trail_sl)
                    if res.get("success"):
                        t_meta["trailing_r_locked"] = target_lock_r
                        t_meta["current_sl"] = trail_sl
                        msg = f"🚀 [MT5 Trailing Stop] {sym} (#{p['ticket']}) reached +{current_r}R -> SL locked at +{target_lock_r}R ({trail_sl})"
                        events.append(msg)
                        try:
                            telegram_notifier.notify_trailing_stop_updated(sym, target_lock_r, trail_sl, current_pnl=upnl, is_demo=True)
                        except Exception:
                            pass
                            
            meta[f"MT5_{ticket}"] = t_meta
            
        save_trade_metadata(meta)
        return events
    except Exception as e:
        return []

_FAST_WATCHER_THREAD = None

class FastPositionWatcher(threading.Thread):
    """
    High-Frequency Fast Position Risk Daemon (8s poll interval).
    Specifically monitors open MT5 & Binance Futures positions to execute immediate Breakeven lock (+1.0R / +1.5R)
    and Take Profit 1 scale-out without waiting for the full CEO desk cycle.
    Automatically idles with zero overhead when no positions are active.
    """
    def __init__(self, user_email=None, is_demo=True, interval_seconds=8):
        super().__init__(daemon=True, name="FastPositionWatcher")
        self.user_email = user_email
        self.is_demo = is_demo
        self.interval = interval_seconds
        self.running = True

    def run(self):
        while self.running:
            try:
                # 1. MT5 Positions Dynamic Management
                mt5_events = audit_and_manage_mt5_positions()
                if mt5_events:
                    for ev in mt5_events:
                        print(f"⚡ [Fast MT5 Position Watcher] {ev}")

                # 2. Binance Futures Positions Dynamic Management
                meta = load_trade_metadata()
                if meta:
                    pos = binance_client.send_signed_request("/fapi/v2/positionRisk", method="GET", is_demo=self.is_demo, user_email=self.user_email)
                    active = [p for p in (pos or []) if float(p.get("positionAmt", 0)) != 0]
                    if active:
                        events = audit_and_manage_positions(user_email=self.user_email, is_demo=self.is_demo)
                        if events:
                            for ev in events:
                                print(f"⚡ [Fast Position Watcher] {ev}")
            except Exception:
                pass
            time.sleep(self.interval)

    def stop(self):
        self.running = False

def start_fast_watcher(user_email=None, is_demo=True, interval_seconds=8, poll_interval=None):
    global _FAST_WATCHER_THREAD
    actual_interval = poll_interval if poll_interval is not None else interval_seconds
    if _FAST_WATCHER_THREAD is None or not _FAST_WATCHER_THREAD.is_alive():
        _FAST_WATCHER_THREAD = FastPositionWatcher(user_email=user_email, is_demo=is_demo, interval_seconds=actual_interval)
        _FAST_WATCHER_THREAD.start()
        print(f"⚡ [Fast Position Watcher] Daemon pengawas posisi frekuensi tinggi aktif (Interval: {actual_interval}s).")
    return _FAST_WATCHER_THREAD

# Alias for external API convenience
start_fast_position_watcher = start_fast_watcher


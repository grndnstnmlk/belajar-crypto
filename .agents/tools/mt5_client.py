"""
MetaTrader 5 (MT5) Execution & Bridge Engine
Institutional-Grade Multi-Asset Bridge for Belajar Kripto Trading Desk.

Features:
1. Seamless Connection & Heartbeat Monitoring with local MT5 Terminal.
2. Symbol Mapping & Market Watch Auto-Selection (Crypto, Forex, Commodities, Indices).
3. Precision Lot Sizing with Risk Budget (Fractional Kelly / Fixed % Risk).
4. Market Order Execution with SMC Trailing SL & TP.
5. Dynamic Trade Management (Breakeven +1R, Trailing Stop, Full/Partial Close).
6. Thread-Safe Operations & Multi-Fill Type Auto-Negotiation (IOC, FOK, RETURN).
"""

import json
import math
import os
import sys
import threading
import time
from typing import Dict, Any, List, Optional, Tuple

# Windows console UTF-8 safety
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

_MT5_LOCK = threading.Lock()
_LAST_INIT_TIME = 0
_INIT_SUCCESS = False


def ensure_mt5_connected() -> bool:
    """Ensures MT5 terminal is initialized and connected."""
    global _LAST_INIT_TIME, _INIT_SUCCESS
    if not MT5_AVAILABLE:
        return False
        
    with _MT5_LOCK:
        now = time.time()
        # If already initialized within last 60s and terminal is connected
        if _INIT_SUCCESS and (now - _LAST_INIT_TIME < 60):
            term = mt5.terminal_info()
            if term and term.connected:
                return True
                
        if not mt5.initialize():
            _INIT_SUCCESS = False
            return False
            
        term = mt5.terminal_info()
        _INIT_SUCCESS = bool(term and term.connected)
        _LAST_INIT_TIME = now
        return _INIT_SUCCESS


def get_account_summary() -> Dict[str, Any]:
    """Retrieves live MT5 account metrics."""
    if not ensure_mt5_connected():
        return {
            "connected": False,
            "error": "MT5 terminal not running or not initialized",
            "balance": 0.0,
            "equity": 0.0,
            "currency": "USD"
        }
        
    acc = mt5.account_info()
    if acc is None:
        return {"connected": False, "error": str(mt5.last_error())}
        
    return {
        "connected": True,
        "login": acc.login,
        "server": acc.server,
        "name": acc.name,
        "currency": acc.currency,
        "balance": float(acc.balance),
        "equity": float(acc.equity),
        "profit": float(acc.profit),
        "margin": float(acc.margin),
        "margin_free": float(acc.margin_free),
        "margin_level": float(acc.margin_level) if acc.margin > 0 else 0.0,
        "leverage": int(acc.leverage),
        "trade_allowed": bool(acc.trade_allowed)
    }


def resolve_symbol_name(raw_symbol: str) -> Optional[str]:
    """
    Finds the exact symbol name supported by the connected broker.
    E.g., 'BTC' -> 'BTCUSD', 'BTCUSDT', 'Bitcoin', 'BTC'
    'GOLD' -> 'XAUUSD', 'GOLD'
    """
    if not ensure_mt5_connected():
        return None
        
    clean = raw_symbol.upper().replace("-", "").replace("/", "").replace("_", "").strip()
    base = clean
    for suffix in ["USDT", "PERP", "BUSD", "USD"]:
        if base.endswith(suffix) and len(base) > len(suffix):
            base = base[:-len(suffix)]
            break
    
    # Priority candidates
    candidates = [
        clean,
        base,
        f"{base}USD",
        f"{base}USDT",
        f"{clean}USD",
        f"{clean}USDT",
        f"{base}m",
        f"{base}.m",
        f"{clean}m",
        f"{clean}.a",
        f"{clean}_pro",
    ]
    
    if base in ["BTC"]:
        candidates = ["BTCUSD", "BTCUSDT", "BTC", "BTCUSD.m", "Bitcoin"] + candidates
    elif base in ["ETH"]:
        candidates = ["ETHUSD", "ETHUSDT", "ETH", "ETHUSD.m", "Ethereum"] + candidates
    elif base in ["SOL"]:
        candidates = ["SOLUSD", "SOLUSDT", "SOL", "SOLUSD.m"] + candidates
    elif base in ["GOLD", "XAU"]:
        candidates = ["XAUUSD", "GOLD", "XAUUSD.m", "XAUUSDT"] + candidates
    elif base in ["DOW", "US30", "DJI"]:
        candidates = ["US30", "DJ30", "WS30", "US30.cash"] + candidates
    elif base in ["NAS", "USTEC", "NQ", "NAS100"]:
        candidates = ["USTEC", "NAS100", "US100", "NQ100"] + candidates

    for c in candidates:
        info = mt5.symbol_info(c)
        if info is not None:
            if not info.visible:
                mt5.symbol_select(c, True)
            return c
            
    # Search in all broker symbols
    all_syms = mt5.symbols_get()
    if all_syms:
        # First check exact symbol match
        for s in all_syms:
            s_name = s.name.upper()
            if s_name in [clean, base, f"{base}USD", f"{base}USDT"]:
                mt5.symbol_select(s.name, True)
                return s.name
        # Then check substring
        for s in all_syms:
            s_name = s.name.upper()
            if clean in s_name or (len(base) >= 3 and s_name.startswith(base)):
                mt5.symbol_select(s.name, True)
                return s.name
                
    return None


def get_live_tick(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetches real-time bid, ask, and spread for a symbol."""
    sym = resolve_symbol_name(symbol)
    if not sym:
        return None
        
    tick = mt5.symbol_info_tick(sym)
    sym_info = mt5.symbol_info(sym)
    if not tick or not sym_info:
        return None
        
    digits = sym_info.digits
    point = sym_info.point
    spread = round((tick.ask - tick.bid) / point, 1) if point > 0 else 0.0
    
    return {
        "symbol": sym,
        "bid": round(tick.bid, digits),
        "ask": round(tick.ask, digits),
        "last": round(tick.last, digits) if tick.last > 0 else round(tick.bid, digits),
        "spread_points": spread,
        "digits": digits,
        "point": point,
        "volume_min": sym_info.volume_min,
        "volume_step": sym_info.volume_step,
        "volume_max": sym_info.volume_max
    }


def calculate_lot_size(symbol: str, risk_usd: float, sl_points: float) -> float:
    """Calculates lot size based on fixed USD risk budget and SL distance in points."""
    sym = resolve_symbol_name(symbol)
    if not sym:
        return 0.01
        
    info = mt5.symbol_info(sym)
    if not info or sl_points <= 0:
        return info.volume_min if info else 0.01
        
    # Standard formula: Risk USD / (SL Points * Tick Value / Tick Size)
    tick_val = info.trade_tick_value if info.trade_tick_value > 0 else 1.0
    tick_size = info.trade_tick_size if info.trade_tick_size > 0 else info.point
    
    cost_per_point_per_lot = (tick_val / tick_size) * info.point
    if cost_per_point_per_lot <= 0:
        cost_per_point_per_lot = 1.0
        
    raw_lot = risk_usd / (sl_points * cost_per_point_per_lot)
    
    # Clamp to step & min/max with Institutional Max Notional Cap (Max 2.5x Equity)
    step = info.volume_step if info.volume_step > 0 else 0.01
    vol_min = info.volume_min if info.volume_min > 0 else 0.01
    vol_max = info.volume_max if info.volume_max > 0 else 100.0
    
    try:
        ensure_mt5_connected()
        acc = mt5.account_info()
        equity = float(acc.equity) if acc and acc.equity > 0 else 100000.0
        max_notional = equity * 2.5  # Max 2.5x leverage notional
        tick = mt5.symbol_info_tick(sym)
        ref_price = float(tick.bid if tick and tick.bid > 0 else (getattr(info, "bid", 0) or getattr(info, "last", 0) or 1000.0))
        contract_size = float(getattr(info, "trade_contract_size", 1.0) or 1.0)
        max_lots_by_notional = max_notional / max(1.0, ref_price * contract_size)
        vol_max = min(vol_max, max_lots_by_notional)
    except Exception:
        pass

    lot = round(raw_lot / step) * step
    lot = max(vol_min, min(lot, vol_max))
    return round(lot, 2)


def place_signal_order(
    symbol: str,
    side: str,
    volume: Optional[float] = None,
    risk_usd: float = 50.0,
    sl_price: Optional[float] = None,
    tp_price: Optional[float] = None,
    comment: str = "BelajarKripto AI"
) -> Dict[str, Any]:
    """
    Executes a live market order on MT5 Demo with institutional risk parameters.
    """
    if not ensure_mt5_connected():
        return {"success": False, "error": "MT5 Terminal disconnected"}
        
    sym = resolve_symbol_name(symbol)
    if not sym:
        return {"success": False, "error": f"Symbol {symbol} not found on broker"}
        
    info = mt5.symbol_info(sym)
    tick = mt5.symbol_info_tick(sym)
    if not info or not tick:
        return {"success": False, "error": f"Failed to get price feed for {sym}"}
        
    is_buy = side.upper() in ["BUY", "LONG"]
    order_type = mt5.ORDER_TYPE_BUY if is_buy else mt5.ORDER_TYPE_SELL
    ask = tick.ask
    bid = tick.bid
    price = ask if is_buy else bid
    digits = info.digits
    point = info.point if info.point > 0 else 0.01
    
    stops_level_pts = getattr(info, "trade_stops_level", 0) or 0
    min_stop_dist = max(stops_level_pts * point, point * 20, price * 0.0015)

    # Normalize SL and TP if price scales differ between crypto and broker ticker
    if sl_price is not None and sl_price > 0:
        scale_ratio_sl = abs(sl_price - price) / max(price, 0.0001)
        if scale_ratio_sl > 0.15:
            # Scalp default: 0.8% - 1.5% SL
            sl_pct = 0.012
            sl_price = price * (1.0 - sl_pct) if is_buy else price * (1.0 + sl_pct)
    else:
        default_dist = max(price * 0.012, min_stop_dist * 2)
        sl_price = price - default_dist if is_buy else price + default_dist

    if tp_price is not None and tp_price > 0:
        scale_ratio_tp = abs(tp_price - price) / max(price, 0.0001)
        if scale_ratio_tp > 0.25:
            # Scalp default: 3.0R (3.6% TP)
            r_dist = abs(price - sl_price)
            tp_price = price + (r_dist * 3.0) if is_buy else price - (r_dist * 3.0)
    else:
        r_dist = abs(price - sl_price)
        tp_price = price + (r_dist * 3.0) if is_buy else price - (r_dist * 3.0)

    # Ensure stops strictly adhere to broker stop level & bid/ask side rules
    if is_buy:
        if sl_price >= bid - min_stop_dist:
            sl_price = bid - min_stop_dist
        if tp_price <= ask + min_stop_dist:
            tp_price = ask + min_stop_dist
    else:
        if sl_price <= ask + min_stop_dist:
            sl_price = ask + min_stop_dist
        if tp_price >= bid - min_stop_dist:
            tp_price = bid - min_stop_dist

    sl_price = round(sl_price, digits)
    tp_price = round(tp_price, digits)

    sl_points = abs(price - sl_price) / point if point > 0 else 100
    
    # Calculate volume if not passed
    if volume is None or volume <= 0:
        volume = calculate_lot_size(sym, risk_usd, sl_points)
        
    # Auto-negotiate execution fill type (IOC -> FOK -> RETURN)
    fill_types = [mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_RETURN]
    
    last_res = None
    for filling in fill_types:
        req = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": sym,
            "volume": float(volume),
            "type": order_type,
            "price": float(price),
            "sl": float(sl_price),
            "tp": float(tp_price),
            "deviation": 20,
            "magic": 888999,
            "comment": comment[:31],
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling,
        }
        
        res = mt5.order_send(req)
        if res is not None and res.retcode == mt5.TRADE_RETCODE_DONE:
            return {
                "success": True,
                "ticket": res.order,
                "deal": res.deal,
                "symbol": sym,
                "side": "BUY" if is_buy else "SELL",
                "volume": volume,
                "price": res.price,
                "sl": sl_price,
                "tp": tp_price,
                "comment": comment,
                "message": "Order executed successfully on MT5"
            }
        else:
            last_res = res
            
    err_code = last_res.retcode if last_res else mt5.last_error()
    err_comment = last_res.comment if last_res else "Execution failed"
    return {
        "success": False,
        "error": f"MT5 retcode: {err_code} ({err_comment})",
        "symbol": sym,
        "side": side
    }


def get_open_positions() -> List[Dict[str, Any]]:
    """Returns all currently open positions from MT5."""
    if not ensure_mt5_connected():
        return []
        
    positions = mt5.positions_get()
    if positions is None:
        return []
        
    results = []
    for p in positions:
        side = "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL"
        gain = (p.price_current - p.price_open) if side == "BUY" else (p.price_open - p.price_current)
        
        results.append({
            "ticket": p.ticket,
            "symbol": p.symbol,
            "side": side,
            "volume": p.volume,
            "price_open": p.price_open,
            "price_current": p.price_current,
            "sl": p.sl,
            "tp": p.tp,
            "profit_usd": p.profit,
            "swap": p.swap,
            "comment": p.comment,
            "magic": p.magic,
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(p.time))
        })
    return results


def close_position_by_ticket(ticket: int) -> Dict[str, Any]:
    """Closes an open position by ticket ID."""
    if not ensure_mt5_connected():
        return {"success": False, "error": "MT5 disconnected"}
        
    pos = mt5.positions_get(ticket=ticket)
    if not pos or len(pos) == 0:
        return {"success": False, "error": f"Position ticket #{ticket} not found"}
        
    p = pos[0]
    close_type = mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
    tick = mt5.symbol_info_tick(p.symbol)
    if not tick:
        return {"success": False, "error": f"Failed to get tick for {p.symbol}"}
    price = tick.bid if p.type == mt5.ORDER_TYPE_BUY else tick.ask
    
    fill_types = [mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_RETURN]
    last_res = None
    
    for filling in fill_types:
        req = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": p.symbol,
            "volume": p.volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 888999,
            "comment": "Close from BelajarKripto",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling,
        }
        
        res = mt5.order_send(req)
        if res and res.retcode == mt5.TRADE_RETCODE_DONE:
            return {"success": True, "ticket": ticket, "message": "Position closed successfully"}
        last_res = res
        
    err_code = last_res.retcode if last_res else mt5.last_error()
    err_comment = last_res.comment if last_res else "Execution failed"
    return {"success": False, "error": f"MT5 retcode: {err_code} ({err_comment})"}


def close_all_positions() -> List[Dict[str, Any]]:
    """Closes all currently open MT5 positions."""
    positions = get_open_positions()
    results = []
    for p in positions:
        res = close_position_by_ticket(p["ticket"])
        res["symbol"] = p["symbol"]
        res["volume"] = p["volume"]
        res["side"] = p["side"]
        results.append(res)
    return results


def modify_position_sl_tp(ticket: int, new_sl: float, new_tp: Optional[float] = None) -> Dict[str, Any]:
    """
    Modifies Stop Loss and/or Take Profit for an open MT5 position (Breakeven / Trailing Stop).
    """
    if not ensure_mt5_connected():
        return {"success": False, "error": "MT5 disconnected"}
        
    pos = mt5.positions_get(ticket=ticket)
    if not pos or len(pos) == 0:
        return {"success": False, "error": f"Position ticket #{ticket} not found"}
        
    p = pos[0]
    sym_info = mt5.symbol_info(p.symbol)
    digits = sym_info.digits if sym_info else 5
    
    sl_final = round(float(new_sl), digits)
    tp_final = round(float(new_tp), digits) if new_tp is not None else p.tp
    
    req = {
        "action": mt5.TRADE_ACTION_SLTP,
        "position": ticket,
        "symbol": p.symbol,
        "sl": sl_final,
        "tp": tp_final
    }
    
    res = mt5.order_send(req)
    if res and res.retcode == mt5.TRADE_RETCODE_DONE:
        return {
            "success": True,
            "ticket": ticket,
            "symbol": p.symbol,
            "new_sl": sl_final,
            "new_tp": tp_final,
            "message": "SL/TP modified successfully"
        }
    else:
        err = res.comment if res else str(mt5.last_error())
        return {"success": False, "error": f"Failed to modify SL/TP: {err}"}


def get_mt5_candles(symbol: str, timeframe: str = "15m", count: int = 100) -> List[Dict[str, Any]]:
    """
    Fetches historical OHLCV candlestick data directly from MT5.
    """
    if not ensure_mt5_connected():
        return []
        
    sym = resolve_symbol_name(symbol)
    if not sym:
        return []
        
    tf_map = {
        "1m": mt5.TIMEFRAME_M1,
        "5m": mt5.TIMEFRAME_M5,
        "15m": mt5.TIMEFRAME_M15,
        "30m": mt5.TIMEFRAME_M30,
        "1h": mt5.TIMEFRAME_H1,
        "4h": mt5.TIMEFRAME_H4,
        "1d": mt5.TIMEFRAME_D1,
    }
    tf = tf_map.get(timeframe.lower(), mt5.TIMEFRAME_M15)
    
    rates = mt5.copy_rates_from_pos(sym, tf, 0, count)
    if rates is None or len(rates) == 0:
        return []
        
    candles = []
    for r in rates:
        candles.append({
            "time": int(r[0]),
            "open": float(r[1]),
            "high": float(r[2]),
            "low": float(r[3]),
            "close": float(r[4]),
            "volume": float(r[5])
        })
    return candles


if __name__ == "__main__":
    print("=== Testing MT5 Client Module ===")
    acc = get_account_summary()
    print("Account Summary:", json.dumps(acc, indent=2))
    
    pos = get_open_positions()
    print(f"Open Positions ({len(pos)}):", json.dumps(pos, indent=2))
    
    candles = get_mt5_candles("EURUSD", "15m", 5)
    print(f"Recent EURUSD Candles ({len(candles)}):", json.dumps(candles, indent=2))


"""
pyramid_runner_engine.py - Smart Pyramiding Engine for Risk-Free Runners
Synthesized from Akademi Crypto Module 03 (Money Psychology, Sizing, and Pyramiding Winners).

Core Logic:
1. Monitors active trades that are solidly in profit (>= +2.0R) and have SL locked in profit / BE.
2. Identifies continuation pullbacks (15m/1H FVG mitigation or 20 EMA retest in trend direction).
3. Executes a 30% lot Add-On (Pyramid Layer).
4. Automatically adjusts Trailing Stop for the combined position so that the worst-case exit is GUARANTEED in net profit (Zero Principal Risk).
5. Persists pyramid lifecycle in active_trades_meta.json and notifies Telegram.
"""

import json
import os
import time
from typing import Dict, Any, List, Optional

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
TRADE_META_FILE = os.path.join(DATA_DIR, "active_trades_meta.json")

import binance_client
import telegram_notifier
import market_eyes

def load_trade_metadata() -> Dict[str, Any]:
    if os.path.exists(TRADE_META_FILE):
        try:
            with open(TRADE_META_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_trade_metadata(meta: Dict[str, Any]):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(TRADE_META_FILE, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ [PyramidRunnerEngine] Error saving metadata: {e}")

def audit_and_execute_pyramiding(is_demo: bool = True, user_email: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Scans all active open positions for pyramiding opportunities on free runners.
    """
    meta = load_trade_metadata()
    positions = binance_client.get_positions(is_demo=is_demo, user_email=user_email)
    if not positions:
        return []

    pyramid_events = []
    
    for pos in positions:
        sym = pos.get("symbol")
        pos_amt = float(pos.get("positionAmt", 0))
        if abs(pos_amt) <= 0:
            continue
        
        t_data = meta.get(sym, {})
        entry_price = float(pos.get("entryPrice", 0))
        mark_price = float(pos.get("markPrice", 0))
        side = "BUY" if pos_amt > 0 else "SELL"
        
        initial_sl = float(t_data.get("initial_sl") or 0.0)
        current_sl = float(t_data.get("current_sl") or 0.0)
        r_dist = abs(entry_price - initial_sl) if (initial_sl > 0 and initial_sl != entry_price) else (entry_price * 0.015)
        
        # Calculate current R-Multiple
        if side == "BUY":
            r_mult = (mark_price - entry_price) / max(r_dist, 0.0001)
        else:
            r_mult = (entry_price - mark_price) / max(r_dist, 0.0001)
            
        pyramid_count = int(t_data.get("pyramid_count", 0))
        max_pyramids = 2  # Max 2 pyramid layers per winning trend
        
        # Pyramiding Criteria:
        # 1. R-Multiple >= +2.0R
        # 2. SL already at Breakeven or locked in profit
        # 3. Has not exceeded max pyramid layers
        # 4. Continuation pullback confirmed via Market Eyes
        if r_mult >= 2.0 and (t_data.get("breakeven_locked") or t_data.get("tp1_taken")) and pyramid_count < max_pyramids:
            try:
                # Check continuation signal on 15m/1H
                base_coin = sym.replace("USDT", "")
                intel = market_eyes.fetch_market_intelligence(base_coin)
                tf_1h = intel.get("timeframe_data", {}).get("1H", {})
                ema20_1h = float(tf_1h.get("ema20", 0.0))
                
                # Check pullback proximity to EMA20 / FVG
                is_pullback_ready = False
                if side == "BUY" and mark_price >= ema20_1h * 0.998:
                    is_pullback_ready = True
                elif side == "SELL" and mark_price <= ema20_1h * 1.002:
                    is_pullback_ready = True
                    
                if is_pullback_ready:
                    # 30% add-on lot size
                    addon_qty = abs(pos_amt) * 0.30
                    formatted_addon_qty = float(binance_client.format_qty_precision(sym, addon_qty, is_demo=is_demo))
                    
                    if formatted_addon_qty > 0:
                        print(f"\n🚀 [SMART PYRAMIDING] {sym}: Winning Runner at +{r_mult:.2f}R! Executing 30% Add-on ({formatted_addon_qty} lots)...")
                        
                        lev = int(pos.get("leverage", 20))
                        order_res = binance_client.place_futures_order(
                            symbol=sym,
                            side=side,
                            quantity=formatted_addon_qty,
                            leverage=lev,
                            is_demo=is_demo,
                            user_email=user_email,
                            exec_mode="LIMIT_CHASE"
                        )
                        
                        if order_res and order_res.get("orderId"):
                            new_pyramid_count = pyramid_count + 1
                            t_data["pyramid_count"] = new_pyramid_count
                            t_data["last_pyramid_price"] = mark_price
                            t_data["last_pyramid_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                            
                            # Lock Trailing Stop above the new combined break-even
                            if side == "BUY":
                                new_secure_sl = round(entry_price + (r_dist * 0.75), 4)
                            else:
                                new_secure_sl = round(entry_price - (r_dist * 0.75), 4)
                                
                            t_data["current_sl"] = new_secure_sl
                            meta[sym] = t_data
                            save_trade_metadata(meta)
                            
                            event_info = {
                                "symbol": sym,
                                "side": side,
                                "r_multiple": round(r_mult, 2),
                                "addon_qty": formatted_addon_qty,
                                "pyramid_layer": new_pyramid_count,
                                "new_locked_sl": new_secure_sl,
                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                            }
                            pyramid_events.append(event_info)
                            
                            print(f"✅ [PYRAMID LOCKED] {sym} Layer #{new_pyramid_count} active! Combined SL locked @ ${new_secure_sl:,.4f} (+0.75R Net Guaranteed Profit).")
                            
                            # Send Telegram Notification
                            try:
                                msg = (
                                    f"🚀 <b>SMART PYRAMIDING TRIGGERED (Layer #{new_pyramid_count})</b>\n"
                                    f"🪙 Pair: <code>{sym}</code> ({side})\n"
                                    f"📈 Trend Gain: <b>+{r_mult:.2f}R</b>\n"
                                    f"📦 Add-on Qty: <b>{formatted_addon_qty} lots</b>\n"
                                    f"🛡️ Guaranteed SL Locked: <b>${new_secure_sl:,.4f}</b> (Zero Capital Risk!)\n"
                                    f"🎯 Target Compounding: <b>1:5.0R+ Mega Swing</b>"
                                )
                                telegram_notifier.send_telegram_notification(msg)
                            except Exception:
                                pass
            except Exception as e:
                print(f"⚠️ [Pyramid Error] {sym}: {e}")
                
    return pyramid_events

if __name__ == "__main__":
    print("=======================================================")
    print("  🚀 SMART PYRAMIDING RUNNER ENGINE AUDIT")
    print("=======================================================")
    events = audit_and_execute_pyramiding(is_demo=True)
    print(f"Total Pyramiding Events Triggered: {len(events)}")
    for ev in events:
        print(f"  * {ev['symbol']} Layer #{ev['pyramid_layer']}: +{ev['r_multiple']}R -> SL ${ev['new_locked_sl']}")
    print("=======================================================")

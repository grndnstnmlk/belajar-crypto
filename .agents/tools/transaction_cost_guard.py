"""
transaction_cost_guard.py - Transaction Cost & Slippage Memory Engine
Inspired by Open-Finance-Lab/AgenticTrading (transaction_cost_agent_pool & storage).

Core Capabilities:
1. Realized Slippage & Spread Tracking (Basis Points - bps).
2. Taker vs Maker Commission Drag Calculation.
3. Funding Rate Attrition Monitor.
4. Pre-Trade Cost Gatekeeper (Blocks or forces Maker execution if Drag > Threshold).
5. Persistent JSON Telemetry Store (.agents/data/transaction_cost_memory.json).
"""

import json
import os
import time
from typing import Dict, Any, Tuple, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
STORAGE_FILE = os.path.join(DATA_DIR, "transaction_cost_memory.json")

# Default baseline friction models per asset class (bps = Basis Points, 1 bps = 0.01%)
DEFAULT_FRICTION_PROFILES = {
    "BTCUSDT": {"avg_slippage_bps": 1.2, "avg_spread_bps": 0.5, "maker_fee_bps": 2.0, "taker_fee_bps": 5.0, "funding_drag_hourly_bps": 0.1},
    "ETHUSDT": {"avg_slippage_bps": 1.8, "avg_spread_bps": 0.8, "maker_fee_bps": 2.0, "taker_fee_bps": 5.0, "funding_drag_hourly_bps": 0.1},
    "SOLUSDT": {"avg_slippage_bps": 3.5, "avg_spread_bps": 1.5, "maker_fee_bps": 2.0, "taker_fee_bps": 5.0, "funding_drag_hourly_bps": 0.15},
    "BNBUSDT": {"avg_slippage_bps": 2.2, "avg_spread_bps": 1.0, "maker_fee_bps": 1.5, "taker_fee_bps": 4.0, "funding_drag_hourly_bps": 0.1},
    "XRPUSDT": {"avg_slippage_bps": 2.8, "avg_spread_bps": 1.2, "maker_fee_bps": 2.0, "taker_fee_bps": 5.0, "funding_drag_hourly_bps": 0.1},
    "NEARUSDT": {"avg_slippage_bps": 4.2, "avg_spread_bps": 2.0, "maker_fee_bps": 2.0, "taker_fee_bps": 5.0, "funding_drag_hourly_bps": 0.2},
    "SUIUSDT": {"avg_slippage_bps": 5.0, "avg_spread_bps": 2.5, "maker_fee_bps": 2.0, "taker_fee_bps": 5.0, "funding_drag_hourly_bps": 0.25},
    "LINKUSDT": {"avg_slippage_bps": 3.0, "avg_spread_bps": 1.5, "maker_fee_bps": 2.0, "taker_fee_bps": 5.0, "funding_drag_hourly_bps": 0.15},
    "ENAUSDT": {"avg_slippage_bps": 6.5, "avg_spread_bps": 3.2, "maker_fee_bps": 2.0, "taker_fee_bps": 5.0, "funding_drag_hourly_bps": 0.3},
    "TRXUSDT": {"avg_slippage_bps": 2.5, "avg_spread_bps": 1.1, "maker_fee_bps": 2.0, "taker_fee_bps": 5.0, "funding_drag_hourly_bps": 0.1},
    "DEFAULT": {"avg_slippage_bps": 4.0, "avg_spread_bps": 2.0, "maker_fee_bps": 2.0, "taker_fee_bps": 5.0, "funding_drag_hourly_bps": 0.2}
}

def load_memory() -> Dict[str, Any]:
    """Loads transaction cost memory from persistent JSON store."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    
    # Initialize default structure
    init_data = {
        "version": "1.0",
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_executions_tracked": 0,
        "total_fees_saved_usd": 0.0,
        "profiles": DEFAULT_FRICTION_PROFILES.copy(),
        "recent_fills": []
    }
    save_memory(init_data)
    return init_data

def save_memory(data: Dict[str, Any]):
    """Persists transaction cost memory to disk."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        data["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️ [TransactionCostGuard] Failed to save memory: {e}")

def record_fill_telemetry(
    symbol: str,
    side: str,
    signal_price: float,
    fill_price: float,
    quantity: float,
    fee_usd: float,
    is_maker: bool = True
):
    """
    Records a live execution fill to calibrate real-time slippage and fee friction.
    """
    sym = symbol.upper().replace("-", "").replace("/", "")
    mem = load_memory()
    profiles = mem.get("profiles", {})
    
    notional = fill_price * quantity
    if notional <= 0:
        return

    # Calculate slippage in basis points (bps)
    # Long: fill > signal = positive slippage (adverse); Short: fill < signal = positive slippage (adverse)
    if side.upper() in ["BUY", "LONG"]:
        slippage_pct = (fill_price - signal_price) / signal_price if signal_price > 0 else 0.0
    else:
        slippage_pct = (signal_price - fill_price) / signal_price if signal_price > 0 else 0.0
    
    slippage_bps = max(0.0, slippage_pct * 10000.0)
    fee_bps = (fee_usd / notional) * 10000.0 if notional > 0 else 2.0

    # Exponential Moving Average (EMA) update on profile
    prof = profiles.get(sym, profiles.get("DEFAULT", {}).copy())
    alpha = 0.20  # 20% weight on newest fill
    
    prof["avg_slippage_bps"] = round((1 - alpha) * prof.get("avg_slippage_bps", 3.0) + alpha * slippage_bps, 2)
    if is_maker:
        prof["maker_fee_bps"] = round((1 - alpha) * prof.get("maker_fee_bps", 2.0) + alpha * fee_bps, 2)
    else:
        prof["taker_fee_bps"] = round((1 - alpha) * prof.get("taker_fee_bps", 5.0) + alpha * fee_bps, 2)

    profiles[sym] = prof
    mem["profiles"] = profiles
    mem["total_executions_tracked"] = mem.get("total_executions_tracked", 0) + 1
    
    # Calculate fee savings if executed via Maker (Limit-Chase) instead of Taker
    taker_baseline_fee = notional * 0.0005  # 5 bps
    saved = max(0.0, taker_baseline_fee - fee_usd)
    mem["total_fees_saved_usd"] = round(mem.get("total_fees_saved_usd", 0.0) + saved, 2)

    # Keep last 50 fills in log
    fills = mem.get("recent_fills", [])
    fills.append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": sym,
        "side": side,
        "notional_usd": round(notional, 2),
        "slippage_bps": round(slippage_bps, 2),
        "fee_usd": round(fee_usd, 4),
        "is_maker": is_maker
    })
    mem["recent_fills"] = fills[-50:]
    save_memory(mem)

def audit_pre_trade_transaction_drag(
    symbol: str,
    position_notional_usd: float,
    expected_profit_usd: float,
    expected_holding_hours: float = 4.0,
    force_maker: bool = True
) -> Dict[str, Any]:
    """
    Audits friction before entering trade:
    Checks if estimated slippage + entry fee + exit fee + funding rate drag exceeds safety ceiling (15% of expected profit).
    """
    sym = symbol.upper().replace("-", "").replace("/", "")
    mem = load_memory()
    profiles = mem.get("profiles", {})
    prof = profiles.get(sym, profiles.get("DEFAULT", {}))

    # Fee rate selection
    fee_rate_bps = prof.get("maker_fee_bps", 2.0) if force_maker else prof.get("taker_fee_bps", 5.0)
    slippage_bps = prof.get("avg_slippage_bps", 3.0)
    spread_bps = prof.get("avg_spread_bps", 1.5)
    funding_hourly_bps = prof.get("funding_drag_hourly_bps", 0.1)

    # 1. Commission Cost (Round-trip: Entry + Exit)
    round_trip_fee_usd = position_notional_usd * (fee_rate_bps * 2.0 / 10000.0)
    
    # 2. Slippage & Spread Cost
    slippage_usd = position_notional_usd * (slippage_bps / 10000.0)
    spread_usd = position_notional_usd * (spread_bps / 10000.0)

    # 3. Funding Cost
    funding_usd = position_notional_usd * ((funding_hourly_bps * expected_holding_hours) / 10000.0)

    total_friction_usd = round(round_trip_fee_usd + slippage_usd + spread_usd + funding_usd, 2)
    
    # Drag Coefficient: Total Friction / Target Profit
    if expected_profit_usd > 0:
        drag_pct = round((total_friction_usd / expected_profit_usd) * 100.0, 2)
    else:
        drag_pct = 99.9

    is_safe = drag_pct <= 15.0  # Max 15% friction drag allowed
    recommended_mode = "LIMIT_CHASE" if force_maker or drag_pct > 8.0 else "MARKET"

    return {
        "symbol": sym,
        "position_notional_usd": round(position_notional_usd, 2),
        "expected_profit_usd": round(expected_profit_usd, 2),
        "total_friction_usd": total_friction_usd,
        "drag_pct": drag_pct,
        "is_safe": is_safe,
        "recommended_mode": recommended_mode,
        "breakdown": {
            "round_trip_fee_usd": round(round_trip_fee_usd, 2),
            "slippage_usd": round(slippage_usd, 2),
            "spread_usd": round(spread_usd, 2),
            "funding_usd": round(funding_usd, 2)
        },
        "verdict": "🟢 LOW FRICTION (High Edge)" if drag_pct <= 8.0 else ("🟡 ACCEPTABLE FRICTION" if is_safe else "🛑 HIGH FRICTION DRAG (Unfavorable R:R)")
    }

def get_transaction_cost_summary() -> Dict[str, Any]:
    """Returns aggregated telemetry for API feed / Web Dashboard."""
    mem = load_memory()
    profiles = mem.get("profiles", {})
    
    ranking = []
    for sym, p in profiles.items():
        if sym == "DEFAULT":
            continue
        total_friction_bps = p.get("avg_slippage_bps", 0) + (p.get("maker_fee_bps", 0) * 2) + p.get("avg_spread_bps", 0)
        ranking.append({
            "symbol": sym,
            "total_friction_bps": round(total_friction_bps, 1),
            "slippage_bps": p.get("avg_slippage_bps", 0),
            "maker_fee_bps": p.get("maker_fee_bps", 0),
            "spread_bps": p.get("avg_spread_bps", 0)
        })
    
    ranking.sort(key=lambda x: x["total_friction_bps"])
    
    return {
        "total_executions_tracked": mem.get("total_executions_tracked", 0),
        "total_fees_saved_usd": mem.get("total_fees_saved_usd", 0.0),
        "lowest_friction_coins": ranking[:3],
        "highest_friction_coins": ranking[-3:] if len(ranking) >= 3 else [],
        "all_coins_ranking": ranking
    }

if __name__ == "__main__":
    print("=======================================================")
    print("  💰 TRANSACTION COST & SLIPPAGE MEMORY AUDIT")
    print("=======================================================")
    summary = get_transaction_cost_summary()
    print(f"Total Executions Tracked : {summary['total_executions_tracked']}")
    print(f"Total Fees Saved (Maker) : ${summary['total_fees_saved_usd']:,.2f} USDT")
    print("\n[Lowest Friction Assets (Best for Large Sizing)]:")
    for c in summary["lowest_friction_coins"]:
        print(f"  * {c['symbol']:<10}: {c['total_friction_bps']} bps total drag (Slippage: {c['slippage_bps']} bps)")
    
    print("\n[Simulating Pre-Trade Audit for BTC ($3,000 Notional, $150 Target Profit)]:")
    audit = audit_pre_trade_transaction_drag("BTCUSDT", 3000.0, 150.0, force_maker=True)
    print(f"  * Total Friction : ${audit['total_friction_usd']} USDT ({audit['drag_pct']}% of profit)")
    print(f"  * Verdict        : {audit['verdict']}")
    print(f"  * Execution Mode : {audit['recommended_mode']}")
    print("=======================================================")

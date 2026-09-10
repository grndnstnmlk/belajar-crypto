"""
Soros Reflexivity Feedback Engine
Inspired by George Soros's Theory of Reflexivity and ATLAS GIC (General Intelligence Capital).

Features:
1. Crowd Positioning Asymmetry Index (Derivatives Long/Short Ratio + Funding Rate Tension)
2. Reflexive Liquidity Trap & Cascade Estimator (Calculates retail vulnerability vs institutional magnet)
3. Soros Reflexivity Score (0-100) & Feedback Regime Classification
4. Actionable Risk Multiplier & Veto Recommendations for Pre-Trade Gatekeeper
5. In-Memory Thread-Safe 15s Caching
"""

import math
import os
import sys
import threading
import time

# UTF-8 console output for Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

_cache = {}
_cache_lock = threading.Lock()
_CACHE_TTL = 15.0

def get_soros_reflexivity_index(symbol="BTC"):
    """
    Computes real-time Soros Reflexivity Index for a given crypto asset.
    Returns:
    {
        "symbol": "BTCUSDT",
        "reflexivity_score": 78.5,
        "reflexive_regime": "SHORT_SQUEEZE_CASCADE" | "LONG_LIQUIDATION_CASCADE" | "EQUILIBRIUM_FLOW",
        "crowd_asymmetry_pct": 68.2,
        "long_short_ratio": 0.45,
        "funding_rate_pct": -0.0185,
        "vulnerable_party": "RETAIL_SHORTS",
        "reflexive_multiplier": 1.20,
        "is_contrarian_trap": True,
        "recommendation": "FAVOR_LONGS_EXPLOIT_SQUEEZE",
        "thesis": "Extreme crowded short positioning (-0.0185% funding, 0.45 L/S) creates a reflexive upward vacuum.",
        "timestamp": 1741580000
    }
    """
    sym_clean = symbol.upper().replace("USDT", "").replace("-", "").replace("/", "")
    cache_key = f"reflexivity_{sym_clean}"
    now = time.time()

    with _cache_lock:
        if cache_key in _cache:
            entry = _cache[cache_key]
            if now - entry["ts"] < _CACHE_TTL:
                return entry["data"]

    # 1. Fetch derivatives flow & sentiment
    ls_ratio = 1.10
    funding_rate = 0.0100
    total_liq_4h = 25.0
    
    try:
        import coinglass_derivatives
        d_intel = coinglass_derivatives.get_derivatives_intelligence(sym_clean)
        ls_ratio = float(d_intel.get("long_short_ratio", 1.10))
        funding_rate = float(d_intel.get("funding_rate_pct", 0.0100))
        total_liq_4h = float(d_intel.get("liquidations_4h", {}).get("total_vol_usd", 25.0))
    except Exception:
        pass

    # 2. Compute Crowd Asymmetry Index (0 - 100%)
    # Balanced L/S is ~1.0. If L/S is 2.5, long% is 2.5/3.5 = 71.4%. If L/S is 0.4, short% is 1/1.4 = 71.4%
    total_parts = ls_ratio + 1.0
    long_crowd_pct = (ls_ratio / total_parts) * 100.0 if total_parts > 0 else 50.0
    short_crowd_pct = 100.0 - long_crowd_pct
    dominant_crowd_pct = max(long_crowd_pct, short_crowd_pct)

    # 3. Assess Reflexive Tension Score
    # Funding rate stress (normalized: >= +0.03% or <= -0.02% is high stress)
    fr_stress = min(50.0, abs(funding_rate) * 1500.0)
    crowd_stress = max(0.0, (dominant_crowd_pct - 50.0) * 2.0)
    
    reflexivity_score = round(min(100.0, (crowd_stress * 0.6) + (fr_stress * 0.4)), 1)

    # 4. Regime & Vulnerability Classification
    if long_crowd_pct >= 62.0 and funding_rate > 0.015:
        regime = "LONG_LIQUIDATION_VULNERABILITY"
        vulnerable = "RETAIL_LONGS"
        trap_side = "BUY"
        favored_side = "SELL"
        multiplier_for_long = 0.70  # Penalty for buying into crowded long trap
        multiplier_for_short = 1.20 # Reward for shorting with liquidation cascade
        thesis = f"Crowded retail longs ({long_crowd_pct:.1f}%) and high funding (+{funding_rate:.4f}%) create downward cascade gravity."
        rec = "VETO_LATE_LONGS_FAVOR_PULLBACK_SHORTS"
    elif short_crowd_pct >= 60.0 or funding_rate < -0.010:
        regime = "SHORT_SQUEEZE_VULNERABILITY"
        vulnerable = "RETAIL_SHORTS"
        trap_side = "SELL"
        favored_side = "BUY"
        multiplier_for_long = 1.25  # Reward for buying into short squeeze
        multiplier_for_short = 0.60 # Penalty for shorting into crowded short squeeze
        thesis = f"Crowded panic shorts ({short_crowd_pct:.1f}%) and negative funding ({funding_rate:+.4f}%) invite reflexive upward short squeeze."
        rec = "EXPLOIT_SHORT_SQUEEZE_FAVOR_LONGS"
    else:
        regime = "EQUILIBRIUM_FLOW"
        vulnerable = "NONE"
        trap_side = "NONE"
        favored_side = "NEUTRAL"
        multiplier_for_long = 1.0
        multiplier_for_short = 1.0
        thesis = f"Market positioning is balanced (L/S: {ls_ratio:.2f}, Funding: {funding_rate:+.4f}%). Reflexive feedback is low."
        rec = "STANDARD_CONFLUENCE_EXECUTION"

    data = {
        "symbol": f"{sym_clean}USDT",
        "reflexivity_score": reflexivity_score,
        "reflexive_regime": regime,
        "crowd_asymmetry_pct": round(dominant_crowd_pct, 1),
        "long_crowd_pct": round(long_crowd_pct, 1),
        "short_crowd_pct": round(short_crowd_pct, 1),
        "long_short_ratio": round(ls_ratio, 2),
        "funding_rate_pct": round(funding_rate, 4),
        "total_liq_4h_usd": round(total_liq_4h, 2),
        "vulnerable_party": vulnerable,
        "trap_side": trap_side,
        "favored_side": favored_side,
        "multiplier_for_long": multiplier_for_long,
        "multiplier_for_short": multiplier_for_short,
        "thesis": thesis,
        "recommendation": rec,
        "timestamp": int(now)
    }

    with _cache_lock:
        _cache[cache_key] = {"ts": now, "data": data}

    return data

def evaluate_pre_trade_reflexivity(symbol, side):
    """
    Evaluates proposed order against Soros Reflexivity dynamics.
    Returns (is_veto_recommended, scale_multiplier, reason_str)
    """
    intel = get_soros_reflexivity_index(symbol)
    side_u = side.upper()
    
    if side_u in ["BUY", "LONG"]:
        scale = intel["multiplier_for_long"]
        is_veto = (intel["trap_side"] == "BUY" and intel["reflexivity_score"] >= 75.0)
    else:
        scale = intel["multiplier_for_short"]
        is_veto = (intel["trap_side"] == "SELL" and intel["reflexivity_score"] >= 75.0)

    reason = f"Reflexivity Score: {intel['reflexivity_score']}/100 [{intel['reflexive_regime']}] | Scale: {scale}x"
    if is_veto:
        reason += f" | 🚨 CONTRARIAN TRAP VETO: Order matches crowded trap side ({intel['trap_side']})"

    return is_veto, scale, intel

if __name__ == "__main__":
    print("\n=======================================================")
    print("       🧠 SOROS REFLEXIVITY FEEDBACK ENGINE")
    print("=======================================================")
    for sym in ["BTC", "ETH", "SOL"]:
        r = get_soros_reflexivity_index(sym)
        print(f"Asset: {r['symbol']}")
        print(f" * Reflexivity Score : {r['reflexivity_score']}/100 [{r['reflexive_regime']}]")
        print(f" * Crowd Asymmetry   : {r['crowd_asymmetry_pct']}% (L: {r['long_crowd_pct']}% | S: {r['short_crowd_pct']}%)")
        print(f" * Funding Rate      : {r['funding_rate_pct']:+.4f}% | L/S: {r['long_short_ratio']:.2f}")
        print(f" * Thesis            : {r['thesis']}")
        print(f" * Recommendation    : {r['recommendation']}")
        print("-" * 55)

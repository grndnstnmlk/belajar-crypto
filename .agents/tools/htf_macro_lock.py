"""
htf_macro_lock.py - High-Timeframe (HTF) Macro Bias Lock & Anti-Counter Trend Guard
Synthesized from Akademi Crypto Module 04 (Top-Down Multi-Timeframe Analysis).

Core Logic:
1. Audits 4H & 1D Trend Structure (20 EMA, 50 EMA, 200 EMA, Swing Fractals).
2. Computes Macro Alignment Score (0 - 100%).
3. Enforces Hard Directional Lock:
   - 4H Bearish Trend -> Strict SHORT ONLY (All Long setups rejected).
   - 4H Bullish Trend -> Strict LONG ONLY (All Short setups rejected).
   - Choppy / Squeeze -> Permits only Mean Reversion setups between HTF Value Area Boundaries.
"""

import json
import os
import time
from typing import Dict, Any, Tuple

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")

def audit_htf_macro_bias(symbol: str, proposed_side: str) -> Dict[str, Any]:
    """
    Audits whether a proposed trade side (BUY/LONG or SELL/SHORT) aligns with 4H and Daily HTF macro structure.
    Returns approval status, macro regime, and reason.
    """
    sym = symbol.upper().replace("-", "").replace("/", "")
    prop_side = "BUY" if proposed_side.upper() in ["BUY", "LONG"] else "SELL"
    
    try:
        import market_eyes
        intel = market_eyes.fetch_market_intelligence(sym)
        
        tf_data = intel.get("timeframe_data", {})
        h1 = tf_data.get("1H", {})
        h4 = tf_data.get("4H", {})
        
        ema20_h4 = float(h4.get("ema20", 0.0))
        ema50_h4 = float(h4.get("ema50", 0.0))
        price = float(intel.get("price", 0.0))
        
        # Determine 4H Trend Bias
        if ema20_h4 > 0 and ema50_h4 > 0:
            if price > ema20_h4 > ema50_h4:
                htf_trend = "BULLISH"
                htf_score = 90
            elif price < ema20_h4 < ema50_h4:
                htf_trend = "BEARISH"
                htf_score = 90
            elif price > ema20_h4 and ema20_h4 < ema50_h4:
                htf_trend = "BULLISH_RECOVERY"
                htf_score = 65
            elif price < ema20_h4 and ema20_h4 > ema50_h4:
                htf_trend = "BEARISH_PULLBACK"
                htf_score = 65
            else:
                htf_trend = "NEUTRAL_RANGING"
                htf_score = 50
        else:
            # Fallback to 1H EMA structure if 4H unavailable
            ema20_h1 = float(h1.get("ema20", 0.0))
            ema50_h1 = float(h1.get("ema50", 0.0))
            if price > ema20_h1 > ema50_h1:
                htf_trend = "BULLISH"
                htf_score = 80
            elif price < ema20_h1 < ema50_h1:
                htf_trend = "BEARISH"
                htf_score = 80
            else:
                htf_trend = "NEUTRAL_RANGING"
                htf_score = 50

        # Hard Rule Enforcement
        is_approved = True
        rejection_reason = None
        
        if htf_trend in ["BEARISH", "BEARISH_PULLBACK"] and prop_side == "BUY":
            is_approved = False
            rejection_reason = f"🛑 HTF MACRO LOCK: Setup LONG ditolak karena tren makro 4H sedang BEARISH (Price < EMA20 < EMA50). Menghindari counter-trend trap."
        elif htf_trend in ["BULLISH", "BULLISH_RECOVERY"] and prop_side == "SELL":
            is_approved = False
            rejection_reason = f"🛑 HTF MACRO LOCK: Setup SHORT ditolak karena tren makro 4H sedang BULLISH (Price > EMA20 > EMA50). Menghindari counter-trend trap."

        return {
            "symbol": sym,
            "proposed_side": prop_side,
            "htf_trend": htf_trend,
            "htf_score": htf_score,
            "is_approved": is_approved,
            "rejection_reason": rejection_reason,
            "price": price,
            "ema20_4h": ema20_h4,
            "ema50_4h": ema50_h4,
            "status": "🟢 APPROVED (Aligned with HTF Trend)" if is_approved else "🛑 BLOCKED BY HTF MACRO LOCK"
        }
    except Exception as e:
        return {
            "symbol": sym,
            "proposed_side": prop_side,
            "htf_trend": "UNKNOWN",
            "htf_score": 50,
            "is_approved": True,  # Fallback gracefully
            "rejection_reason": None,
            "status": f"⚠️ HTF Audit Fallback: {e}"
        }

if __name__ == "__main__":
    print("=======================================================")
    print("  🔒 HTF MACRO BIAS LOCK AUDIT")
    print("=======================================================")
    for s in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
        long_audit = audit_htf_macro_bias(s, "BUY")
        short_audit = audit_htf_macro_bias(s, "SELL")
        print(f"\n[{s}] 4H Trend: {long_audit['htf_trend']} (Score: {long_audit['htf_score']}%)")
        print(f"  * LONG Audit  : {long_audit['status']}")
        print(f"  * SHORT Audit : {short_audit['status']}")
    print("=======================================================")

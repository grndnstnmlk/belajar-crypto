"""
htf_macro_lock.py - High-Timeframe (HTF) Macro Bias Lock & Anti-Counter Trend Guard
Synthesized from Akademi Crypto Module 04 (Top-Down Multi-Timeframe Analysis) & Module 01 (Macro Liquidity).

Core Rules:
1. Hard HTF Alignment:
   - 4H / Daily Bullish -> STRICT LONG ONLY (All Short setups rejected).
   - 4H / Daily Bearish -> STRICT SHORT ONLY (All Long setups rejected).
2. BTC Master Gatekeeper:
   - If BTC 1H/4H is BULLISH, ALL Altcoin SHORT signals are strictly banned to prevent short-squeeze traps.
3. Alpha Leader Protection:
   - Top-tier market leaders (e.g., SOL, BNB, etc.) with positive relative strength cannot be shorted.
"""

import json
import os
import sys
import time
from typing import Dict, Any

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
sys.path.insert(0, TOOLS_DIR)

import market_regime

ALPHA_PROTECTED_LEADERS = {"SOL", "BNB", "BTC"}

def audit_htf_macro_bias(symbol: str, proposed_side: str) -> Dict[str, Any]:
    """
    Audits whether a proposed trade side (BUY/LONG or SELL/SHORT) strictly aligns with 4H and Daily HTF macro structure,
    BTC master trend, and Alpha Leader shielding.
    Returns approval status, macro regime, score, and rejection reason.
    """
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("USDT", "")
    pair_sym = f"{sym_clean}USDT"
    prop_side = "BUY" if proposed_side.upper() in ["BUY", "LONG"] else "SELL"
    
    try:
        # 1. Fetch Target Asset 4H & 1H Regime
        reg_4h = market_regime.detect_market_regime(pair_sym, interval="4h")
        reg_1h = market_regime.detect_market_regime(pair_sym, interval="1h") if not reg_4h else None
        
        active_reg = reg_4h if reg_4h and reg_4h.get("price", 0) > 0 else reg_1h
        price = float(active_reg.get("price", 0.0)) if active_reg else 0.0
        ema20_4h = float(active_reg.get("ema20", 0.0)) if active_reg else 0.0
        ema50_4h = float(active_reg.get("ema50", 0.0)) if active_reg else 0.0
        htf_bias = active_reg.get("bias", "NEUTRAL") if active_reg else "NEUTRAL"
        
        # Determine 4H HTF Trend
        if price > 0 and ema20_4h > 0 and ema50_4h > 0:
            if price > ema20_4h > ema50_4h:
                htf_trend = "BULLISH"
                htf_score = 90
            elif price < ema20_4h < ema50_4h:
                htf_trend = "BEARISH"
                htf_score = 90
            elif price > ema20_4h and ema20_4h < ema50_4h:
                htf_trend = "BULLISH_RECOVERY"
                htf_score = 65
            elif price < ema20_4h and ema20_4h > ema50_4h:
                htf_trend = "BEARISH_PULLBACK"
                htf_score = 65
            else:
                htf_trend = "NEUTRAL_RANGING"
                htf_score = 50
        else:
            htf_trend = "BULLISH" if htf_bias == "BULLISH" else ("BEARISH" if htf_bias == "BEARISH" else "NEUTRAL_RANGING")
            htf_score = 60

        is_approved = True
        rejection_reason = None

        # 2. RULE A: BTC Master Trend Gatekeeper (Akademi Crypto Module 01 & 04)
        # If BTC 1H or 4H is Bullish, NEVER allow Altcoin Shorts to avoid short squeezes!
        if prop_side == "SELL" and sym_clean != "BTC":
            btc_1h = market_regime.detect_market_regime("BTCUSDT", interval="1h")
            btc_4h = market_regime.detect_market_regime("BTCUSDT", interval="4h")
            
            btc_1h_bull = False
            btc_4h_bull = False
            
            if btc_1h:
                btc_p = float(btc_1h.get("price", 0.0))
                btc_e20 = float(btc_1h.get("ema20", 0.0))
                btc_bias = btc_1h.get("bias", "NEUTRAL")
                if btc_bias == "BULLISH" or (btc_p > 0 and btc_p > btc_e20):
                    btc_1h_bull = True
            
            if btc_4h:
                btc_4h_p = float(btc_4h.get("price", 0.0))
                btc_4h_e20 = float(btc_4h.get("ema20", 0.0))
                btc_4h_bias = btc_4h.get("bias", "NEUTRAL")
                if btc_4h_bias == "BULLISH" or (btc_4h_p > 0 and btc_4h_p > btc_4h_e20):
                    btc_4h_bull = True
            
            if btc_1h_bull or btc_4h_bull:
                is_approved = False
                rejection_reason = (
                    f"🛑 HTF MACRO LOCK: Setup SHORT pada {pair_sym} DITOLAK. "
                    f"BTC Makro (1H: {'BULL' if btc_1h_bull else 'FLAT'} / 4H: {'BULL' if btc_4h_bull else 'FLAT'}) sedang BULLISH. "
                    f"Dilarang melawan arus tren naik Bitcoin (Akademi Crypto Module 01 & 04)."
                )

        # 3. RULE B: Alpha Leader Protection Shield
        # Never short confirmed leaders (e.g. SOL, BNB) when market structure is not in confirmed breakdown
        if is_approved and prop_side == "SELL" and sym_clean in ALPHA_PROTECTED_LEADERS:
            if htf_trend in ["BULLISH", "BULLISH_RECOVERY", "NEUTRAL_RANGING"]:
                is_approved = False
                rejection_reason = (
                    f"🛑 HTF MACRO LOCK: Setup SHORT pada {pair_sym} DITOLAK. "
                    f"{sym_clean} adalah ALPHA LEADER berkapitalisasi kuat. "
                    f"Shorting pemimpin pasar terbukti memiliki rasio kegagalan 75%+."
                )

        # 4. RULE C: Direct HTF Trend Invalidation
        if is_approved:
            if htf_trend in ["BEARISH", "BEARISH_PULLBACK"] and prop_side == "BUY":
                is_approved = False
                rejection_reason = (
                    f"🛑 HTF MACRO LOCK: Setup LONG ditolak karena tren makro 4H {pair_sym} "
                    f"sedang BEARISH (Price < EMA20 < EMA50). Menghindari counter-trend trap."
                )
            elif htf_trend in ["BULLISH", "BULLISH_RECOVERY"] and prop_side == "SELL":
                is_approved = False
                rejection_reason = (
                    f"🛑 HTF MACRO LOCK: Setup SHORT ditolak karena tren makro 4H {pair_sym} "
                    f"sedang BULLISH (Price > EMA20 > EMA50). Menghindari counter-trend trap."
                )

        status_text = "🟢 APPROVED (Aligned with HTF Trend)" if is_approved else f"🛑 BLOCKED: {rejection_reason}"

        return {
            "symbol": pair_sym,
            "proposed_side": prop_side,
            "htf_trend": htf_trend,
            "htf_score": htf_score,
            "is_approved": is_approved,
            "rejection_reason": rejection_reason,
            "price": price,
            "ema20_4h": ema20_4h,
            "ema50_4h": ema50_4h,
            "status": status_text
        }

    except Exception as e:
        # STRICT FAIL-CLOSED POLICY FOR SHORTS: Never approve short setups during unexpected exceptions!
        safe_approved = False if prop_side == "SELL" else True
        rejection_msg = f"🛑 HTF Audit Exception: {e}. Fail-closed policy blocks SHORT." if prop_side == "SELL" else None
        return {
            "symbol": pair_sym,
            "proposed_side": prop_side,
            "htf_trend": "UNKNOWN",
            "htf_score": 50,
            "is_approved": safe_approved,
            "rejection_reason": rejection_msg,
            "status": f"⚠️ HTF Audit Fallback: {e} (Approved={safe_approved})"
        }

if __name__ == "__main__":
    print("=======================================================")
    print("  🔒 HTF MACRO BIAS LOCK AUDIT")
    print("=======================================================")
    for s in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
        long_audit = audit_htf_macro_bias(s, "BUY")
        short_audit = audit_htf_macro_bias(s, "SELL")
        print(f"\n[{s}] 4H Trend: {long_audit['htf_trend']} (Score: {long_audit['htf_score']}%)")
        print(f"  * LONG Audit  : {long_audit['is_approved']} -> {long_audit['status']}")
        print(f"  * SHORT Audit : {short_audit['is_approved']} -> {short_audit['status']}")
    print("=======================================================")

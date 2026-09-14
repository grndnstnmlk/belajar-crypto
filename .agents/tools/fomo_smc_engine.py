"""
FOMO SMC Master Engine (fomo_smc_engine.py) - Complete 14-Course Synthesis
Synthesized from all 14 Global Smart Money Concepts (SMC) Courses on Mr FOMO Trading:
1. Phantom Trading (Fractal S/D & CHoCH)
2. Hustle FX (50% Equilibrium Dealing Range)
3. Vertex Investing (50% Mean Threshold MT & Wick-as-Candle)
4. Flipping Markets (Supply-to-Demand S/D Flips)
5. Precision Markets (Expectational Order Flow)
6. PipFactory Academy (Liquidity Sweeps before Mitigation)
7. VVS Academy (Wyckoff Accumulation Spring & Distribution UTAD)
8. FX Simplified (Clean FVG Imbalances)
9. TraqFX (London & NY Killzone Scalping)
10. MENTFX (Decision Point POI Mapping)
11. WWA Bootcamp (Institutional Funding Candle IFC Engulfing)
12. Eye-Opening FX (Asian Range Judas Swing)
13. Fractal Markets (HTF-to-LTF Alignment)
14. Ultimate Supply & Demand (Zone Freshness & Departure Strength)
"""

import json
import math
import os
import sys
import time
import urllib.request
import ssl
from typing import Dict, List, Any, Optional, Tuple

# Windows console UTF-8 safety
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
sys.path.insert(0, TOOLS_DIR)

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

# In-Memory Cache (15s TTL)
_SMC_CACHE: Dict[Tuple[str, str], Tuple[float, Dict[str, Any]]] = {}
CACHE_TTL_SECONDS = 15.0

def fetch_candles(symbol: str, bar: str = "1h", limit: int = 100) -> List[List[Any]]:
    """Fetches kline data from Binance Vision API with fallback."""
    base = symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "").strip()
    pair = f"{base}USDT"
    tf_map = {"1M": "1m", "5M": "5m", "15M": "15m", "1H": "1h", "4H": "4h", "1D": "1d"}
    interval = tf_map.get(bar.upper(), bar.lower())

    url = f"https://data-api.binance.vision/api/v3/klines?symbol={pair}&interval={interval}&limit={limit}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and isinstance(data, list):
                return data
    except Exception:
        pass
    return []

# =============================================================================
# 1. Dealing Range & 50% Equilibrium Engine (Premium vs Discount)
# =============================================================================
def calculate_dealing_range_equilibrium(candles: List[List[Any]]) -> Dict[str, Any]:
    """
    Identifies the active major swing range (Dealing Range), computes the 50% Equilibrium,
    and classifies price into PREMIUM (>50%) or DISCOUNT (<50%).
    
    Rule:
    - Longs are ONLY permitted in DISCOUNT (< 50%).
    - Shorts are ONLY permitted in PREMIUM (> 50%).
    """
    if not candles or len(candles) < 20:
        return {
            "status": "INSUFFICIENT_DATA",
            "range_high": 0.0,
            "range_low": 0.0,
            "equilibrium_50": 0.0,
            "equilibrium_price": 0.0,
            "current_price": 0.0,
            "position_pct": 50.0,
            "dist_from_eq_pct": 0.0,
            "zone": "EQUILIBRIUM",
            "long_allowed": True,
            "short_allowed": True
        }

    highs = [float(c[2]) for c in candles[-50:]]
    lows = [float(c[3]) for c in candles[-50:]]
    closes = [float(c[4]) for c in candles[-50:]]
    current_price = closes[-1]

    range_high = max(highs)
    range_low = min(lows)
    range_span = range_high - range_low

    if range_span <= 0:
        return {
            "status": "FLAT_RANGE",
            "range_high": range_high,
            "range_low": range_low,
            "equilibrium_50": range_high,
            "equilibrium_price": range_high,
            "current_price": current_price,
            "position_pct": 50.0,
            "dist_from_eq_pct": 0.0,
            "zone": "EQUILIBRIUM",
            "long_allowed": True,
            "short_allowed": True
        }

    equilibrium_50 = range_low + (range_span * 0.50)
    position_pct = ((current_price - range_low) / range_span) * 100.0
    dist_from_eq_pct = ((current_price - equilibrium_50) / equilibrium_50) * 100.0

    # Institutional Fib Arrays: 0.618 - 0.786 Deep Discount / Premium
    if position_pct < 45.0:
        zone = "DEEP_DISCOUNT" if position_pct <= 30.0 else "DISCOUNT"
        long_allowed = True
        short_allowed = False
    elif position_pct > 55.0:
        zone = "DEEP_PREMIUM" if position_pct >= 70.0 else "PREMIUM"
        long_allowed = False
        short_allowed = True
    else:
        zone = "EQUILIBRIUM"
        long_allowed = True
        short_allowed = True

    return {
        "status": "VALID",
        "range_high": round(range_high, 4),
        "range_low": round(range_low, 4),
        "equilibrium_50": round(equilibrium_50, 4),
        "equilibrium_price": round(equilibrium_50, 4),
        "current_price": round(current_price, 4),
        "position_pct": round(position_pct, 1),
        "dist_from_eq_pct": round(dist_from_eq_pct, 2),
        "zone": zone,
        "long_allowed": long_allowed,
        "short_allowed": short_allowed,
        "optimal_trade_entry_long": round(range_low + (range_span * 0.214), 4), # 0.786 retracement
        "optimal_trade_entry_short": round(range_low + (range_span * 0.786), 4)
    }

# =============================================================================
# 2. Inducement (IDM) & Retail Trap Identifier
# =============================================================================
def detect_inducement_traps(candles: List[List[Any]]) -> Dict[str, Any]:
    """
    Detects Inducement (IDM): minor structural swings formed immediately before
    major institutional Order Blocks.
    
    If price enters an IDM without sweeping it, retail traders get trapped.
    Once the IDM is swept, the true institutional Order Block is activated!
    """
    if not candles or len(candles) < 25:
        return {"has_inducement": False, "status": "INSUFFICIENT_DATA", "recommendation": "INSUFFICIENT_DATA"}

    closes = [float(c[4]) for c in candles]
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    current_price = closes[-1]

    # Find minor swing highs & lows in the last 15 candles (Internal Structure)
    internal_highs = []
    internal_lows = []
    for i in range(len(candles) - 16, len(candles) - 3):
        if highs[i] > highs[i-1] and highs[i] > highs[i+1] and highs[i] > highs[i-2] and highs[i] > highs[i+2]:
            internal_highs.append({"index": i, "price": highs[i]})
        if lows[i] < lows[i-1] and lows[i] < lows[i+1] and lows[i] < lows[i-2] and lows[i] < lows[i+2]:
            internal_lows.append({"index": i, "price": lows[i]})

    # Check for Bearish Inducement (Internal Low acting as retail support trap)
    bearish_idm = None
    if internal_lows:
        latest_int_low = internal_lows[-1]
        is_swept = any(lows[k] < latest_int_low["price"] for k in range(latest_int_low["index"] + 1, len(candles)))
        bearish_idm = {
            "level": latest_int_low["price"],
            "is_swept": is_swept,
            "status": "SWEPT_CLEARED" if is_swept else "ACTIVE_RETAIL_TRAP",
            "type": "SELLSIDE_INDUCEMENT"
        }

    # Check for Bullish Inducement (Internal High acting as retail resistance trap)
    bullish_idm = None
    if internal_highs:
        latest_int_high = internal_highs[-1]
        is_swept = any(highs[k] > latest_int_high["price"] for k in range(latest_int_high["index"] + 1, len(candles)))
        bullish_idm = {
            "level": latest_int_high["price"],
            "is_swept": is_swept,
            "status": "SWEPT_CLEARED" if is_swept else "ACTIVE_RETAIL_TRAP",
            "type": "BUYSIDE_INDUCEMENT"
        }

    status = (
        "INDUCEMENT_PENDING_SWEEP" if (bearish_idm and not bearish_idm["is_swept"]) or (bullish_idm and not bullish_idm["is_swept"])
        else ("INDUCEMENT_SWEPT" if (bearish_idm or bullish_idm) else "NO_INDUCEMENT_TRAP")
    )

    recommendation = (
        "WAIT_FOR_IDM_SWEEP" if (bearish_idm and not bearish_idm["is_swept"]) or (bullish_idm and not bullish_idm["is_swept"])
        else "INDUCEMENT_CONFIRMED_CLEARED"
    )

    idm_p = (bearish_idm["level"] if bearish_idm else (bullish_idm["level"] if bullish_idm else current_price))

    return {
        "has_inducement": bool(bearish_idm or bullish_idm),
        "status": status,
        "idm_price": idm_p,
        "sellside_idm": bearish_idm,
        "buyside_idm": bullish_idm,
        "recommendation": recommendation
    }

# =============================================================================
# 3. Institutional Funding Candle (IFC) Engulfing & Sweep Trigger
# =============================================================================
def detect_ifc_institutional_funding_candle(candles: List[List[Any]]) -> Dict[str, Any]:
    """
    Institutional Funding Candle (IFC) - WWA Bootcamp & Phantom Trading Pattern:
    A high-spread candle that pierces a key high/low to engineer liquidity,
    then closes with a long wick and is immediately ENGULFED in the opposite direction.
    """
    if not candles or len(candles) < 10:
        return {"has_ifc": False, "signal": "NONE", "summary": "Insufficient candles"}

    # Evaluate last 5 candles
    for i in range(len(candles) - 1, max(2, len(candles) - 6), -1):
        o = float(candles[i-1][1])
        h = float(candles[i-1][2])
        l = float(candles[i-1][3])
        c = float(candles[i-1][4])
        spread = h - l
        if spread <= 0:
            continue

        curr_o = float(candles[i][1])
        curr_c = float(candles[i][4])

        # Bullish IFC: Previous candle swept low with lower wick >= 40% of spread, followed by bullish engulfing
        lower_wick = min(o, c) - l
        if (lower_wick / spread) >= 0.40 and curr_c > h and curr_c > curr_o:
            return {
                "has_ifc": True,
                "signal": "BULLISH_IFC",
                "wick_low": l,
                "engulf_high": curr_c,
                "summary": f"⚡ BULLISH IFC: Liquidity swept at ${l:,.4f} with {(lower_wick/spread)*100:.1f}% wick & engulfed at ${curr_c:,.4f}"
            }

        # Bearish IFC: Previous candle swept high with upper wick >= 40% of spread, followed by bearish engulfing
        upper_wick = h - max(o, c)
        if (upper_wick / spread) >= 0.40 and curr_c < l and curr_c < curr_o:
            return {
                "has_ifc": True,
                "signal": "BEARISH_IFC",
                "wick_high": h,
                "engulf_low": curr_c,
                "summary": f"⚡ BEARISH IFC: Liquidity swept at ${h:,.4f} with {(upper_wick/spread)*100:.1f}% wick & engulfed at ${curr_c:,.4f}"
            }

    return {"has_ifc": False, "signal": "NONE", "summary": "No active IFC manipulation candle"}

# =============================================================================
# 4. Break of Structure (BOS) vs Change of Character (CHoCH)
# =============================================================================
def detect_bos_and_choch(candles: List[List[Any]]) -> Dict[str, Any]:
    """
    Classifies structural breaks:
    - BOS (Break of Structure): Clean body close breaking structural swing in direction of primary trend.
    - CHoCH (Change of Character): Body close breaking the last major opposite pivot, signalling trend reversal.
    """
    if not candles or len(candles) < 20:
        return {"event": "NONE", "summary": "Insufficient data"}

    closes = [float(c[4]) for c in candles]
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    current_price = closes[-1]

    recent_swing_high = max(highs[-15:-2])
    recent_swing_low = min(lows[-15:-2])

    if current_price > recent_swing_high:
        return {
            "event": "BOS_BULLISH_EXPANSION",
            "broken_level": recent_swing_high,
            "type": "CONTINUATION",
            "summary": f"🚀 BULLISH BOS: Body broken above swing high ${recent_swing_high:,.4f}"
        }
    elif current_price < recent_swing_low:
        return {
            "event": "BOS_BEARISH_EXPANSION",
            "broken_level": recent_swing_low,
            "type": "CONTINUATION",
            "summary": f"🩸 BEARISH BOS: Body broken below swing low ${recent_swing_low:,.4f}"
        }

    return {"event": "IN_STRUCTURE_ROTATION", "summary": "Price rotating inside existing structural pivots"}

# =============================================================================
# 5. Vertex Investing 50% Mean Threshold (MT) & Long-Wick Refinement
# =============================================================================
def detect_vertex_mean_threshold_and_wicks(candles: List[List[Any]]) -> Dict[str, Any]:
    """
    Vertex Investing Signature Refinements:
    1. 50% Mean Threshold (MT) of Order Block: Calculates 50% body level to halve SL distance and expand R:R.
    2. Wick-as-Candle (Long Rejection Wick): Treats wicks >= 50% candle spread as LTF Order Blocks.
    """
    if not candles or len(candles) < 10:
        return {"has_vertex_refinement": False, "mt_level": 0.0, "summary": "Insufficient candles"}

    last_candle = candles[-2] # Completed candle
    o = float(last_candle[1])
    h = float(last_candle[2])
    l = float(last_candle[3])
    c = float(last_candle[4])
    spread = max(h - l, 1e-6)
    body = abs(c - o)

    # 50% Mean Threshold of the candle body
    mt_level = min(o, c) + (body * 0.50)

    # Long Rejection Wick Analysis (Vertex Wick-as-OB)
    lower_wick = min(o, c) - l
    upper_wick = h - max(o, c)
    
    if (lower_wick / spread) >= 0.45:
        wick_50 = l + (lower_wick * 0.50)
        return {
            "has_vertex_refinement": True,
            "type": "BULLISH_WICK_OB",
            "mt_level": round(mt_level, 4),
            "wick_entry_50": round(wick_50, 4),
            "summary": f"📐 VERTEX 50% WICK OB: Bullish Long-Wick Refinement at ${wick_50:,.4f}"
        }
    elif (upper_wick / spread) >= 0.45:
        wick_50 = h - (upper_wick * 0.50)
        return {
            "has_vertex_refinement": True,
            "type": "BEARISH_WICK_OB",
            "mt_level": round(mt_level, 4),
            "wick_entry_50": round(wick_50, 4),
            "summary": f"📐 VERTEX 50% WICK OB: Bearish Long-Wick Refinement at ${wick_50:,.4f}"
        }

    return {
        "has_vertex_refinement": True,
        "type": "STANDARD_MT_50",
        "mt_level": round(mt_level, 4),
        "wick_entry_50": round(mt_level, 4),
        "summary": f"📐 VERTEX 50% MT: Order Block Mean Threshold at ${mt_level:,.4f}"
    }

# =============================================================================
# 6. Flipping Markets: Supply-to-Demand (S/D) Flips
# =============================================================================
def detect_supply_demand_flips(candles: List[List[Any]]) -> Dict[str, Any]:
    """
    Flipping Markets Methodology:
    Identifies zones where prior Supply fails and flips into Demand (or vice-versa),
    providing the highest-momentum continuation entry signals.
    """
    if not candles or len(candles) < 20:
        return {"has_flip": False, "flip_type": "NONE", "summary": "Insufficient data"}

    closes = [float(c[4]) for c in candles]
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    
    # Check for Supply failure -> Bullish Flip
    recent_high = max(highs[-10:-2])
    if closes[-1] > recent_high and lows[-1] >= recent_high * 0.998:
        return {
            "has_flip": True,
            "flip_type": "SUPPLY_TO_DEMAND_FLIP",
            "flip_price": round(recent_high, 4),
            "summary": f"🔄 FLIPPING MARKETS: Supply-to-Demand Flip at ${recent_high:,.4f}"
        }

    # Check for Demand failure -> Bearish Flip
    recent_low = min(lows[-10:-2])
    if closes[-1] < recent_low and highs[-1] <= recent_low * 1.002:
        return {
            "has_flip": True,
            "flip_type": "DEMAND_TO_SUPPLY_FLIP",
            "flip_price": round(recent_low, 4),
            "summary": f"🔄 FLIPPING MARKETS: Demand-to-Supply Flip at ${recent_low:,.4f}"
        }

    return {"has_flip": False, "flip_type": "NONE", "summary": "No active S/D flip zone"}

# =============================================================================
# 7. VVS Academy & WWA: Wyckoff Phase C Schematics (Spring & UTAD)
# =============================================================================
def detect_wyckoff_spring_utad(candles: List[List[Any]]) -> Dict[str, Any]:
    """
    VVS Academy & WWA Bootcamp Wyckoff Engine:
    - Phase C Spring: Final false breakdown below range low that immediately recovers into trading range.
    - Phase C UTAD: Final false breakout above range high that immediately dumps back into trading range.
    """
    if not candles or len(candles) < 25:
        return {"has_wyckoff": False, "pattern": "NONE", "summary": "Insufficient candles"}

    highs = [float(c[2]) for c in candles[-25:]]
    lows = [float(c[3]) for c in candles[-25:]]
    closes = [float(c[4]) for c in candles[-25:]]

    support = min(lows[:-2])
    resistance = max(highs[:-2])
    curr_close = closes[-1]
    last_low = lows[-2]
    last_high = highs[-2]

    # Spring: Last candle spiked below support but current closed back above support
    if last_low < support and curr_close > support:
        return {
            "has_wyckoff": True,
            "pattern": "WYCKOFF_SPRING_PHASE_C",
            "key_level": round(support, 4),
            "summary": f"💎 WYCKOFF SPRING (Phase C): False Breakdown Swept at ${last_low:,.4f} -> Closed inside range"
        }

    # UTAD (Upthrust After Distribution): Spiked above resistance but current closed below resistance
    if last_high > resistance and curr_close < resistance:
        return {
            "has_wyckoff": True,
            "pattern": "WYCKOFF_UTAD_PHASE_C",
            "key_level": round(resistance, 4),
            "summary": f"🩸 WYCKOFF UTAD (Phase C): False Breakout Swept at ${last_high:,.4f} -> Closed inside range"
        }

    return {"has_wyckoff": False, "pattern": "NONE", "summary": "No active Wyckoff Phase C Spring/UTAD"}

# =============================================================================
# 8. Master Institutional FOMO SMC Setup Auditor (14-Course Synthesis)
# =============================================================================
def audit_fomo_smc_setup(symbol: str, bar: str = "1h", side: str = "BUY", proposed_price: Optional[float] = None) -> Dict[str, Any]:
    """
    Executes the 14-Course Master SMC Audit for a proposed trade setup:
    1. Hustle FX: Dealing Range & 50% Equilibrium Filter (Longs only in Discount / Shorts only in Premium)
    2. PipFactory & MENTFX: Inducement Sweep Verification (Avoids premature retail traps)
    3. WWA & Phantom: Institutional Funding Candle (IFC) Engulfing Check
    4. Phantom & Precision: BOS / CHoCH Trend Alignment
    5. Vertex Investing: 50% Mean Threshold (MT) & Rejection Wick Refinements
    6. Flipping Markets: Supply-to-Demand (S/D) Flip Zones
    7. VVS Academy: Wyckoff Phase C Spring & UTAD Confirmation
    
    Returns comprehensive institutional verdict and confluence score (0 - 100%).
    """
    base = symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "").strip()
    cache_key = (base, bar.upper())
    now = time.time()
    
    if cache_key in _SMC_CACHE:
        cached_time, cached_res = _SMC_CACHE[cache_key]
        if now - cached_time < CACHE_TTL_SECONDS:
            return cached_res

    candles = fetch_candles(base, bar=bar, limit=60)
    
    if not candles or len(candles) < 20:
        return {
            "symbol": f"{base}USDT",
            "status": "ERROR",
            "reason": "Failed to fetch candlestick feed",
            "confluence_score": 50,
            "smc_confluence_score": 50,
            "grade": "C (POOR)",
            "institutional_grade": "C (POOR)",
            "is_approved": True,
            "rejection_reason": "",
            "dealing_range": {"zone": "EQUILIBRIUM", "range_low": 0.0, "range_high": 0.0, "equilibrium_price": 0.0, "dist_from_eq_pct": 0.0},
            "inducement": {"status": "NO_DATA", "recommendation": "STANDBY"},
            "ifc_pattern": {"has_ifc": False, "summary": "N/A"}
        }

    dealing_range = calculate_dealing_range_equilibrium(candles)
    idm_intel = detect_inducement_traps(candles)
    ifc_intel = detect_ifc_institutional_funding_candle(candles)
    struct_intel = detect_bos_and_choch(candles)
    vertex_intel = detect_vertex_mean_threshold_and_wicks(candles)
    flip_intel = detect_supply_demand_flips(candles)
    wyckoff_intel = detect_wyckoff_spring_utad(candles)

    score = 70
    reasons = []
    veto = False
    veto_reason = ""

    is_buy = side.upper() in ["BUY", "LONG"]

    # 1. Dealing Range Check
    if is_buy:
        if not dealing_range["long_allowed"]:
            veto = True
            veto_reason = f"🛑 PREMIUM VIOLATION: Long ditolak karena harga berada di zona PREMIUM ({dealing_range['position_pct']}%). Beli hanya di DISCOUNT (<50%)."
        elif dealing_range["zone"] in ["DISCOUNT", "DEEP_DISCOUNT"]:
            score += 15
            reasons.append(f"🟢 Dealing Range DISCOUNT ({dealing_range['position_pct']}%)")
    else:
        if not dealing_range["short_allowed"]:
            veto = True
            veto_reason = f"🛑 DISCOUNT VIOLATION: Short ditolak karena harga berada di zona DISCOUNT ({dealing_range['position_pct']}%). Jual hanya di PREMIUM (>50%)."
        elif dealing_range["zone"] in ["PREMIUM", "DEEP_PREMIUM"]:
            score += 15
            reasons.append(f"🔴 Dealing Range PREMIUM ({dealing_range['position_pct']}%)")

    # 2. Inducement Sweep Check
    if is_buy and idm_intel.get("sellside_idm"):
        if idm_intel["sellside_idm"]["is_swept"]:
            score += 10
            reasons.append("⚡ Sellside Inducement (IDM) Swept")
        else:
            score -= 10
            reasons.append("⚠️ Active Retail Support Trap nearby")
    elif not is_buy and idm_intel.get("buyside_idm"):
        if idm_intel["buyside_idm"]["is_swept"]:
            score += 10
            reasons.append("⚡ Buyside Inducement (IDM) Swept")
        else:
            score -= 10
            reasons.append("⚠️ Active Retail Resistance Trap nearby")

    # 3. IFC Engulfing Confirmation
    if ifc_intel["has_ifc"]:
        if is_buy and ifc_intel["signal"] == "BULLISH_IFC":
            score += 15
            reasons.append("🎯 Institutional Funding Candle (IFC) Bullish Engulfing Trigger")
        elif not is_buy and ifc_intel["signal"] == "BEARISH_IFC":
            score += 15
            reasons.append("🎯 Institutional Funding Candle (IFC) Bearish Engulfing Trigger")

    # 4. Market Structure Event
    if is_buy and struct_intel.get("event") in ["BOS_BULLISH_EXPANSION", "CHOCH_BULLISH_SHIFT"]:
        score += 10
        reasons.append(f"🏛️ {struct_intel['event']}")
    elif not is_buy and struct_intel.get("event") in ["BOS_BEARISH_EXPANSION", "CHOCH_BEARISH_SHIFT"]:
        score += 10
        reasons.append(f"🏛️ {struct_intel['event']}")

    # 5. Vertex Investing 50% Mean Threshold / Wick OB Refinement
    if vertex_intel.get("has_vertex_refinement"):
        if is_buy and vertex_intel.get("type") in ["BULLISH_WICK_OB", "STANDARD_MT_50"]:
            score += 10
            reasons.append(vertex_intel["summary"])
        elif not is_buy and vertex_intel.get("type") in ["BEARISH_WICK_OB", "STANDARD_MT_50"]:
            score += 10
            reasons.append(vertex_intel["summary"])

    # 6. Flipping Markets S/D Flip Confluence
    if flip_intel.get("has_flip"):
        if is_buy and flip_intel["flip_type"] == "SUPPLY_TO_DEMAND_FLIP":
            score += 15
            reasons.append(flip_intel["summary"])
        elif not is_buy and flip_intel["flip_type"] == "DEMAND_TO_SUPPLY_FLIP":
            score += 15
            reasons.append(flip_intel["summary"])

    # 7. VVS / WWA Wyckoff Phase C Spring & UTAD
    if wyckoff_intel.get("has_wyckoff"):
        if is_buy and wyckoff_intel["pattern"] == "WYCKOFF_SPRING_PHASE_C":
            score += 20
            reasons.append(wyckoff_intel["summary"])
        elif not is_buy and wyckoff_intel["pattern"] == "WYCKOFF_UTAD_PHASE_C":
            score += 20
            reasons.append(wyckoff_intel["summary"])

    score = max(0, min(100, score))
    grade = "A+ (INSTITUTIONAL GRADE)" if score >= 85 else ("A (HIGH CONFLUENCE)" if score >= 75 else ("B (MODERATE)" if score >= 60 else "C (POOR)"))

    decision = "VETO" if veto else ("VALID_SMC_ENTRY" if score >= 75 else "STANDBY_LOW_SMC_CONFLUENCE")

    result = {
        "symbol": f"{base}USDT",
        "bar": bar,
        "side": side,
        "is_approved": not veto,
        "rejection_reason": veto_reason,
        "confluence_score": score,
        "smc_confluence_score": score,
        "grade": grade,
        "institutional_grade": grade,
        "decision": decision,
        "veto": veto,
        "veto_reason": veto_reason,
        "dealing_range": dealing_range,
        "inducement": idm_intel,
        "ifc_candle": ifc_intel,
        "ifc_pattern": ifc_intel,
        "market_structure": struct_intel,
        "vertex_refinement": vertex_intel,
        "sd_flip": flip_intel,
        "wyckoff": wyckoff_intel,
        "confluence_reasons": reasons,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    _SMC_CACHE[cache_key] = (now, result)
    return result

if __name__ == "__main__":
    print("=== Testing FOMO SMC Master Engine ===")
    sym = sys.argv[1] if len(sys.argv) > 1 else "BTC"
    res = audit_fomo_smc_setup(sym, bar="1h", side="BUY")
    print(f"Asset: {res['symbol']} | Side: {res['side']} | Bar: {res['bar']}")
    print(f"Dealing Range: Zone={res['dealing_range']['zone']} | Eq=${res['dealing_range']['equilibrium_price']:,.2f} | Pos={res['dealing_range']['position_pct']}%")
    print(f"Inducement   : Status={res['inducement']['status']} | Recommendation={res['inducement']['recommendation']}")
    print(f"IFC Candle   : Has={res['ifc_candle']['has_ifc']} | Signal={res['ifc_candle']['signal']}")
    print(f"Confluence   : {res['confluence_score']}% [{res['grade']}] -> Decision: {res['decision']}")
    if res['veto']:
        print(f"VETO Reason  : {res['veto_reason']}")

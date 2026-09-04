"""
Institutional Trading Sessions & Kill Zones Filter + Confluence Scoring Engine
Synthesized with Akademi Crypto (Smart Money Concepts & Order Flow Execution).

Key Capabilities:
1. Identifies institutional liquidity windows:
   - London Kill Zone (14:00 - 18:00 WIB / 07:00 - 11:00 UTC)
   - New York Kill Zone (19:30 - 23:30 WIB / 12:30 - 16:30 UTC)
   - Asian Accumulation (07:00 - 13:00 WIB / 00:00 - 06:00 UTC)
   - Low-Liquidity Dead Zone (00:00 - 06:30 WIB / 17:00 - 23:30 UTC)
2. Computes strict composite Confluence Score (0 - 100%):
   - Macro HTF Alignment (4H Trend)
   - Key Value Area (FVG Retest, POC/VAL/VAH, 3-Touch)
   - Relative Strength Matrix (Alpha Leader / Beta Laggard)
   - Indicator Confirmation (VWAP Acceptance, RSI divergence)
   - Institutional Session Liquidity Alignment
3. Blocks sub-standard setups (< 75% or < 85% in dead zone) to drastically reduce false signals.
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# WIB is UTC+7
WIB = timezone(timedelta(hours=7))

def get_current_session_info(dt=None):
    """
    Returns current institutional trading session details in WIB and UTC.
    """
    if dt is None:
        dt_utc = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt_utc = dt.replace(tzinfo=WIB).astimezone(timezone.utc)
    else:
        dt_utc = dt.astimezone(timezone.utc)

    dt_wib = dt_utc.astimezone(WIB)
    wib_hour = dt_wib.hour + (dt_wib.minute / 60.0)

    # Check Kill Zones
    # London Kill Zone: 14:00 - 18:00 WIB
    is_london_kz = 14.0 <= wib_hour < 18.0
    # New York Kill Zone: 19.5 (19:30) - 23.5 (23:30) WIB
    is_ny_kz = 19.5 <= wib_hour < 23.5
    # Asian Session: 07:00 - 13:00 WIB
    is_asian = 7.0 <= wib_hour < 13.0
    # Low-Liquidity Dead Zone: 00:00 - 06:50 WIB
    is_dead_zone = (0.0 <= wib_hour < 6.83)

    if is_ny_kz:
        session_name = "🇺🇸 NEW YORK KILL ZONE (Peak Institutional Liquidity)"
        session_code = "NY_KZ"
        bonus_score = 15
        min_threshold = 75
        rationale = "High volume institutional participation during US cash market overlap. Optimal for trend continuation & breakouts."
        high_liquidity = True
    elif is_london_kz:
        session_name = "🇬🇧 LONDON KILL ZONE (European Expansion Window)"
        session_code = "LONDON_KZ"
        bonus_score = 12
        min_threshold = 75
        rationale = "High volatility and institutional liquidity injection. Ideal for trend establishment and sweep-reversals."
        high_liquidity = True
    elif is_asian:
        session_name = "🇯🇵 ASIAN ACCUMULATION SESSION"
        session_code = "ASIA"
        bonus_score = 5
        min_threshold = 78
        rationale = "Range-bound consolidation & liquidity engineering. Standard filter required."
        high_liquidity = False
    elif is_dead_zone:
        session_name = "⚠️ LOW-LIQUIDITY DEAD ZONE (Late NY / Asia Pre-Market)"
        session_code = "DEAD_ZONE"
        bonus_score = 0
        min_threshold = 85  # Much stricter filter during low-liquidity hours
        rationale = "Thin order books, wider spreads, and high fakeout wick risk. Only pristine Grade-A+ setups permitted."
        high_liquidity = False
    else:
        session_name = "🌐 INTER-SESSION DRIFT (Transition Window)"
        session_code = "TRANSITION"
        bonus_score = 8
        min_threshold = 76
        rationale = "Moderate volume between major sessions. Solid confluence required."
        high_liquidity = False

    return {
        "session_name": session_name,
        "session_code": session_code,
        "wib_time": dt_wib.strftime("%Y-%m-%d %H:%M:%S WIB"),
        "utc_time": dt_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "bonus_score": bonus_score,
        "min_threshold": min_threshold,
        "rationale": rationale,
        "high_liquidity": high_liquidity,
        "is_dead_zone": is_dead_zone
    }

def calculate_confluence_score(setup, session_info=None):
    """
    Evaluates multi-variable confluence and returns a 0-100% score and grade.
    
    Score Matrix Breakdown (Max 100 points):
    1. Higher Timeframe Alignment (4H Macro Trend)     : 30 pts
    2. Key Area of Value (FVG / POC / 3-Touch / MSS)   : 25 pts
    3. Relative Strength (Alpha Leader / Beta Laggard) : 15 pts
    4. Execution Precision (R:R Ratio >= 2.5)          : 15 pts
    5. Session Liquidity Bonus (London/NY KZ)          : 15 pts
    """
    if session_info is None:
        session_info = get_current_session_info()

    breakdown = {}
    total_score = 0

    # 1. Macro 4H Confluence (30 pts)
    if setup.get("macro_aligned", False):
        macro_pts = 30
        breakdown["Macro 4H Trend Aligned"] = "+30 pts"
    else:
        macro_pts = 0
        breakdown["Macro 4H Trend"] = "0 pts (Counter-trend or unaligned)"
    total_score += macro_pts

    # 2. Key Level / Smart Money Structure (25 pts)
    struct_pts = 0
    reasons = []
    if setup.get("is_tim"):
        struct_pts += 15
        reasons.append("Tim MSS Liquidity Sweep")
    if setup.get("is_fabio"):
        struct_pts += 15
        reasons.append("Fabio Auction VAH/VAL")
    if setup.get("is_3touch"):
        struct_pts += 15
        reasons.append("Patrick Nill 3-Touch Level")
    if "FVG" in setup.get("reason", "") or setup.get("is_fvg"):
        struct_pts += 12
        reasons.append("Fair Value Gap Retest")
    if setup.get("is_scalp"):
        struct_pts += 12
        reasons.append("5m Micro-Structure Trigger")

    struct_pts = min(25, struct_pts)
    if struct_pts > 0:
        breakdown["Key Level / Structure"] = f"+{struct_pts} pts ({', '.join(reasons[:2])})"
    else:
        breakdown["Key Level / Structure"] = "0 pts (No prominent key level)"
    total_score += struct_pts

    # 3. Relative Strength / RS-RW Matrix (15 pts)
    if setup.get("is_alpha_leader"):
        rs_pts = 15
        breakdown["Relative Strength"] = "+15 pts (Alpha Leader - Outperforming BTC)"
    elif setup.get("is_beta_laggard"):
        rs_pts = 15
        breakdown["Relative Strength"] = "+15 pts (Beta Laggard - Underperforming BTC)"
    elif "RS" in setup.get("reason", ""):
        rs_pts = 10
        breakdown["Relative Strength"] = "+10 pts (Favorable RS alignment)"
    else:
        rs_pts = 5
        breakdown["Relative Strength"] = "+5 pts (Neutral RS)"
    total_score += rs_pts

    # 4. Risk-to-Reward Execution Quality (15 pts)
    rr = float(setup.get("rr", 0.0))
    if rr >= 3.5:
        rr_pts = 15
        breakdown["Risk:Reward Quality"] = f"+15 pts (Exceptional R:R 1:{rr:.2f})"
    elif rr >= 2.5:
        rr_pts = 12
        breakdown["Risk:Reward Quality"] = f"+12 pts (Strong R:R 1:{rr:.2f})"
    elif rr >= 2.0:
        rr_pts = 8
        breakdown["Risk:Reward Quality"] = f"+8 pts (Acceptable R:R 1:{rr:.2f})"
    else:
        rr_pts = 0
        breakdown["Risk:Reward Quality"] = f"0 pts (Subpar R:R 1:{rr:.2f})"
    total_score += rr_pts

    # 5. Session Liquidity Bonus (Max 15 pts)
    session_pts = session_info.get("bonus_score", 0)
    breakdown["Session Liquidity"] = f"+{session_pts} pts ({session_info['session_code']})"
    total_score += session_pts

    total_score = min(100, max(0, total_score))

    # Grade Classification
    if total_score >= 85:
        grade = "A+ (Elite Institutional)"
    elif total_score >= 75:
        grade = "A (High Confluence)"
    elif total_score >= 65:
        grade = "B (Moderate Confluence)"
    else:
        grade = "C (Low Confluence / High Noise)"

    min_required = session_info["min_threshold"]
    is_admissible = (total_score >= min_required)

    return {
        "score": total_score,
        "grade": grade,
        "min_required": min_required,
        "is_admissible": is_admissible,
        "breakdown": breakdown,
        "session": session_info
    }

def audit_candidate_confluence(candidate, session_info=None):
    """
    Convenience evaluator: returns (is_approved: bool, audit_summary: str, score_data: dict)
    """
    if session_info is None:
        session_info = get_current_session_info()

    res = calculate_confluence_score(candidate, session_info)
    sym = candidate.get("symbol", "UNKNOWN")
    side = candidate.get("side", "")

    if res["is_admissible"]:
        summary = (
            f"✅ [CONFLUENCE PASSED: {res['score']}% | Grade {res['grade']}] "
            f"{side} {sym} meets strict threshold ({res['score']}% >= {res['min_required']}%) "
            f"during {session_info['session_name']}."
        )
    else:
        summary = (
            f"🛑 [CONFLUENCE BLOCKED: {res['score']}% | Grade {res['grade']}] "
            f"{side} {sym} fell below required threshold ({res['score']}% < {res['min_required']}%) "
            f"during {session_info['session_name']}. Order filtered out to preserve capital."
        )

    return res["is_admissible"], summary, res

if __name__ == "__main__":
    sess = get_current_session_info()
    print("\n=======================================================")
    print(f"       ⏱️ INSTITUTIONAL SESSION & ACCURACY AUDIT")
    print("=======================================================")
    print(f"Waktu Saat Ini    : {sess['wib_time']}")
    print(f"Sesi Institusional: {sess['session_name']}")
    print(f"Karakteristik     : {sess['rationale']}")
    print(f"Likuiditas Tinggi : {'🟢 YA' if sess['high_liquidity'] else '🟡 MODERAT / RENDAH'}")
    print(f"Ambang Konfluensi : Minimal {sess['min_threshold']}% untuk lolos eksekusi")
    print("=======================================================\n")

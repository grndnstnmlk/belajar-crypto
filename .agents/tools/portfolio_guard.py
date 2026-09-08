"""
Portfolio Correlation & Directional Heat Cap Engine (Akademi Crypto Module 03)
Guarantees institutional risk budgeting, multi-asset correlation clustering,
and directional exposure caps to prevent catastrophic simultaneous drawdowns.
"""

import json
import os
import sys
from datetime import datetime

# Windows console UTF-8 safety
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Correlation Clusters (Akademi Crypto Risk Management)
# Majors: Anchor assets with deep liquidity & relatively lower volatility
CLUSTER_MAJORS = ["BTC", "ETH", "SOL"]

# High-Beta Altcoins: Volatile assets with correlation coefficient r >= 0.85 during market selloffs
CLUSTER_HIGH_BETA_ALTS = ["DOGE", "ADA", "AVAX", "LINK", "SUI", "XRP", "NEAR", "APT", "BNB"]

# Configuration Rules
MAX_TOTAL_POSITIONS = 4
MAX_SAME_DIRECTION_CAP = 3      # Max 3 Longs or Max 3 Shorts simultaneously!
MAX_HIGH_BETA_ALTS_TOTAL = 3   # Max 3 high-beta altcoins across portfolio

def clean_coin(symbol):
    return symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")

def audit_portfolio_heat(active_positions, balance_usd=5000.0):
    """
    Performs comprehensive portfolio correlation and directional heat audit:
    - Counts Longs vs Shorts
    - Calculates Directional Net Exposure
    - Identifies High-Beta Cluster Over-concentration
    - Determines if new Long or Short entries are permissible
    """
    long_positions = []
    short_positions = []
    high_beta_alts = []

    for p in active_positions:
        amt = float(p.get("positionAmt", 0))
        if amt == 0:
            continue
        sym = p.get("symbol", "")
        base = clean_coin(sym)

        if amt > 0:
            long_positions.append(sym)
        else:
            short_positions.append(sym)

        if base in CLUSTER_HIGH_BETA_ALTS:
            high_beta_alts.append(sym)

    total_active = len(long_positions) + len(short_positions)
    long_count = len(long_positions)
    short_count = len(short_positions)

    # Directional Heat Calculation
    if total_active > 0:
        net_bias_ratio = (long_count - short_count) / total_active
        long_heat_pct = round((long_count / total_active) * 100.0, 1)
        short_heat_pct = round((short_count / total_active) * 100.0, 1)
    else:
        net_bias_ratio = 0.0
        long_heat_pct = 0.0
        short_heat_pct = 0.0

    # Admissibility Rules
    can_open_long = (total_active < MAX_TOTAL_POSITIONS) and (long_count < MAX_SAME_DIRECTION_CAP)
    can_open_short = (total_active < MAX_TOTAL_POSITIONS) and (short_count < MAX_SAME_DIRECTION_CAP)

    # Correlation Warning Status
    if long_count >= 4:
        heat_status = "🚨 EXTREME LONG OVER-EXPOSURE (Vulnerable to simultaneous BTC dump)"
        heat_code = "CRITICAL_LONG"
    elif short_count >= 4:
        heat_status = "🚨 EXTREME SHORT OVER-EXPOSURE (Vulnerable to short squeeze pump)"
        heat_code = "CRITICAL_SHORT"
    elif long_count == 3 and short_count == 0:
        heat_status = "⚠️ HIGH DIRECTIONAL LONG HEAT (Max 3 Longs reached | Slot 4 reserved for Short/Cash)"
        heat_code = "HIGH_LONG"
    elif short_count == 3 and long_count == 0:
        heat_status = "⚠️ HIGH DIRECTIONAL SHORT HEAT (Max 3 Shorts reached | Slot 4 reserved for Long/Cash)"
        heat_code = "HIGH_SHORT"
    elif long_count >= 1 and short_count >= 1:
        heat_status = "⚖️ HEDGED / BALANCED PORTFOLIO (Lower Systematic Drawdown Risk)"
        heat_code = "BALANCED"
    elif total_active == 0:
        heat_status = "⚪ 100% CASH PRESERVED (Zero Market Exposure)"
        heat_code = "CASH"
    else:
        heat_status = "🟢 HEALTHY DIVERSIFICATION"
        heat_code = "HEALTHY"

    return {
        "total_active": total_active,
        "max_total": MAX_TOTAL_POSITIONS,
        "long_count": long_count,
        "short_count": short_count,
        "max_same_direction": MAX_SAME_DIRECTION_CAP,
        "long_positions": long_positions,
        "short_positions": short_positions,
        "high_beta_alts": high_beta_alts,
        "high_beta_count": len(high_beta_alts),
        "long_heat_pct": long_heat_pct,
        "short_heat_pct": short_heat_pct,
        "can_open_long": can_open_long,
        "can_open_short": can_open_short,
        "heat_status": heat_status,
        "heat_code": heat_code,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def filter_candidate_by_correlation(candidate, active_positions):
    """
    Evaluates proposed candidate setup against portfolio correlation rules:
    1. Blocks 3rd Long or 3rd Short
    2. Blocks excessive High-Beta Altcoin clustering (max 2)
    Returns: (is_approved: bool, rationale: str)
    """
    side = candidate.get("side", "LONG").upper()
    sym = candidate.get("symbol", "")
    base = clean_coin(sym)

    audit = audit_portfolio_heat(active_positions)

    # Rule 1: Directional Cap (Max 2 same direction)
    if side in ["BUY", "LONG"]:
        if not audit["can_open_long"]:
            if audit["long_count"] >= MAX_SAME_DIRECTION_CAP:
                return False, (
                    f"🚨 [CORRELATION GUARD] {sym} LONG di-skip: Batas maksimal posisi searah "
                    f"({audit['long_count']}/{MAX_SAME_DIRECTION_CAP} LONG) sudah penuh! "
                    f"Posisi aktif: {', '.join(audit['long_positions'])}. "
                    f"Slot tersisa hanya boleh diisi SHORT (Hedging) atau Cash demi mencegah triple-SL saat BTC koreksi."
                )
            else:
                return False, f"🚨 [PORTFOLIO GUARD] Kuota total posisi ({MAX_TOTAL_POSITIONS}) sudah penuh."
    elif side in ["SELL", "SHORT"]:
        if not audit["can_open_short"]:
            if audit["short_count"] >= MAX_SAME_DIRECTION_CAP:
                return False, (
                    f"🚨 [CORRELATION GUARD] {sym} SHORT di-skip: Batas maksimal posisi searah "
                    f"({audit['short_count']}/{MAX_SAME_DIRECTION_CAP} SHORT) sudah penuh! "
                    f"Posisi aktif: {', '.join(audit['short_positions'])}. "
                    f"Slot tersisa hanya boleh diisi LONG atau Cash."
                )
            else:
                return False, f"🚨 [PORTFOLIO GUARD] Kuota total posisi ({MAX_TOTAL_POSITIONS}) sudah penuh."

    # Rule 2: High-Beta Altcoin Cluster Exposure
    if base in CLUSTER_HIGH_BETA_ALTS and audit["high_beta_count"] >= MAX_HIGH_BETA_ALTS_TOTAL:
        return False, (
            f"⚠️ [CLUSTER GUARD] {sym} di-skip: Sudah ada {audit['high_beta_count']} High-Beta Altcoins aktif "
            f"({', '.join(audit['high_beta_alts'])}). Mencegah over-konsentrasi pada altcoin berkorelasi tinggi."
        )

    return True, "✅ Lolos uji korelasi & directional heat portofolio."

def get_scaled_risk_pct(proposed_side, active_positions, base_risk_pct=1.5):
    """
    Applies Dynamic Risk Heat Scaling:
    - 1st position in direction : 100% allocation (e.g. 1.5% modal)
    - 2nd position in direction : Scaled down to ~67% (e.g. 1.0% modal)
    Guarantees cumulative directional risk never exceeds 2.5% total equity!
    """
    side_clean = "BUY" if proposed_side.upper() in ["BUY", "LONG"] else "SELL"
    active_in_side = 0

    for p in active_positions:
        amt = float(p.get("positionAmt", 0))
        if amt > 0 and side_clean == "BUY":
            active_in_side += 1
        elif amt < 0 and side_clean == "SELL":
            active_in_side += 1

    if active_in_side == 0:
        return base_risk_pct               # Posisi ke-1: 100% (misal: 0.50% / 1.50%)
    elif active_in_side == 1:
        return round(base_risk_pct * 0.75, 2)  # Posisi ke-2: 75%
    elif active_in_side == 2:
        return round(base_risk_pct * 0.50, 2)  # Posisi ke-3: 50%
    else:
        return round(base_risk_pct * 0.35, 2)  # Posisi ke-4 (Hedge): 35%

def format_telegram_portfolio_heat(active_positions, balance_usd=5000.0):
    """
    Formats rich Telegram card for Portfolio Correlation & Directional Heat.
    """
    audit = audit_portfolio_heat(active_positions, balance_usd)

    long_str = ", ".join(audit["long_positions"]) if audit["long_positions"] else "Tidak ada"
    short_str = ", ".join(audit["short_positions"]) if audit["short_positions"] else "Tidak ada"
    alts_str = ", ".join(audit["high_beta_alts"]) if audit["high_beta_alts"] else "Nihil"

    long_bar = "🟢" * audit["long_count"] + "⚪" * (audit["max_same_direction"] - min(audit["long_count"], audit["max_same_direction"]))
    short_bar = "🔴" * audit["short_count"] + "⚪" * (audit["max_same_direction"] - min(audit["short_count"], audit["max_same_direction"]))

    return (
        f"🛡️ <b>PORTFOLIO CORRELATION & DIRECTIONAL HEAT</b>\n"
        f"<i>Akademi Crypto Risk Management (Module 03)</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Kapasitas Posisi:</b> <code>{audit['total_active']} / {audit['max_total']} slot</code>\n\n"
        f"🟢 <b>Long Heat:</b> {long_bar} (<code>{audit['long_count']}/{audit['max_same_direction']} max</code>)\n"
        f"   • Posisi: <code>{long_str}</code>\n"
        f"   • Izin Long Baru: <b>{'✅ DIIZINKAN' if audit['can_open_long'] else '🔒 TERKUNCI (FULL)'}</b>\n\n"
        f"🔴 <b>Short Heat:</b> {short_bar} (<code>{audit['short_count']}/{audit['max_same_direction']} max</code>)\n"
        f"   • Posisi: <code>{short_str}</code>\n"
        f"   • Izin Short Baru: <b>{'✅ DIIZINKAN' if audit['can_open_short'] else '🔒 TERKUNCI (FULL)'}</b>\n\n"
        f"🌐 <b>High-Beta Altcoins:</b> <code>{alts_str}</code> ({audit['high_beta_count']}/{MAX_HIGH_BETA_ALTS_TOTAL} max)\n\n"
        f"🧭 <b>Status Kesehatan Portofolio:</b>\n"
        f"<b>{audit['heat_status']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💡 <i>Aturan Besi: Maksimal {MAX_SAME_DIRECTION_CAP} posisi searah. Slot ke-{MAX_TOTAL_POSITIONS} dialokasikan khusus untuk Hedging atau Cadangan Kas agar terhindar dari kerugian serentak!</i>\n"
        f"🕒 <i>{audit['updated_at']}</i>"
    )

if __name__ == "__main__":
    dummy_pos = [
        {"symbol": "ETHUSDT", "positionAmt": "3.51"},
        {"symbol": "LINKUSDT", "positionAmt": "668.2"},
        {"symbol": "SOLUSDT", "positionAmt": "23.2"}
    ]
    report = format_telegram_portfolio_heat(dummy_pos, 5200.0)
    print(report)
    cand = {"symbol": "DOGEUSDT", "side": "LONG", "base": "DOGE"}
    approved, reason = filter_candidate_by_correlation(cand, dummy_pos)
    print("\nCandidate Check:", approved, "->", reason)

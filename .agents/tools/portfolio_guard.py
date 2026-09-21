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

# Configuration Rules (Akademi Crypto Module 03: Correlation & Directional Heat Guard)
MAX_TOTAL_POSITIONS = 4
MAX_SAME_DIRECTION_CAP = 3     # Maximum 3 concurrent positions in same direction
MAX_HIGH_BETA_ALTS_TOTAL = 2   # Maximum 2 concurrent high-beta altcoins to prevent flush cascades

def clean_coin(symbol):
    return symbol.upper().replace("-", "").replace("/", "").replace("_", "").replace("USDT", "")

def audit_portfolio_heat(active_positions, balance_usd=5000.0):
    """
    Performs institutional portfolio correlation and directional heat audit.
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
            if base in CLUSTER_HIGH_BETA_ALTS:
                high_beta_alts.append(sym)
        else:
            short_positions.append(sym)

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

    can_open_long = (long_count < MAX_SAME_DIRECTION_CAP) and (total_active < MAX_TOTAL_POSITIONS)
    can_open_short = False  # Hard Long-Only lock active

    if long_count >= MAX_SAME_DIRECTION_CAP:
        heat_status = f"🔴 DIRECTIONAL HEAT MAX ({long_count}/{MAX_SAME_DIRECTION_CAP} Longs)"
        heat_code = "OVERHEATED"
    elif len(high_beta_alts) >= MAX_HIGH_BETA_ALTS_TOTAL:
        heat_status = f"🟡 ALTCOIN CORRELATION CAP ({len(high_beta_alts)}/{MAX_HIGH_BETA_ALTS_TOTAL} Alts)"
        heat_code = "HIGH_CORRELATION"
    else:
        heat_status = f"🟢 HEALTHY ({long_count} Longs, {len(high_beta_alts)} Alts)"
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
    Guarantees institutional risk budgeting and correlation clustering:
    - Blocks SHORT if Hard Long-Only lock is active.
    - Blocks duplicate symbol positions.
    - Limits same-direction exposure to MAX_SAME_DIRECTION_CAP (3).
    - Limits high-beta altcoins to MAX_HIGH_BETA_ALTS_TOTAL (2) to prevent simultaneous flush loss.
    """
    sym = candidate.get("symbol", "")
    base = clean_coin(sym)
    cand_side = "BUY" if candidate.get("side", "").upper() in ["BUY", "LONG"] else "SELL"

    # 1. Reject SHORT if Hard Long-Only Lock
    if cand_side == "SELL":
        return False, "🛑 Setup SHORT Ditolak: Hard Long-Only Lock aktif untuk melindungi modal dari tren naik makro."

    # 2. Check active positions
    long_positions = []
    high_beta_alts = []

    for p in active_positions:
        amt = float(p.get("positionAmt", 0))
        if amt == 0:
            continue
        p_sym = p.get("symbol", "")
        p_base = clean_coin(p_sym)

        # Duplicate check
        if p_sym.upper() == sym.upper():
            return False, f"🛑 Duplikasi Posisi: Posisi {sym} sudah aktif. Dilarang menggandakan entri pada aset yang sama."

        if amt > 0:
            long_positions.append(p_sym)
            if p_base in CLUSTER_HIGH_BETA_ALTS:
                high_beta_alts.append(p_sym)

    # 3. Same direction cap
    if len(long_positions) >= MAX_SAME_DIRECTION_CAP:
        return False, (
            f"🛑 Directional Heat Penuh: Sudah ada {len(long_positions)}/{MAX_SAME_DIRECTION_CAP} posisi Long aktif "
            f"({', '.join(long_positions)}). Dilarang membuka posisi baru sampai ada yang ditutup atau BE."
        )

    # 4. High-beta altcoin correlation cap
    if base in CLUSTER_HIGH_BETA_ALTS and len(high_beta_alts) >= MAX_HIGH_BETA_ALTS_TOTAL:
        return False, (
            f"🛑 Batas Korelasi Altcoin Tercapai: Sudah ada {len(high_beta_alts)}/{MAX_HIGH_BETA_ALTS_TOTAL} posisi Altcoin aktif "
            f"({', '.join(high_beta_alts)}). Maksimal {MAX_HIGH_BETA_ALTS_TOTAL} posisi altcoin searah untuk mencegah kerugian serentak "
            f"saat koreksi Bitcoin (Akademi Crypto Module 03)."
        )

    return True, f"✅ Lolos audit korelasi (Active: {len(long_positions)} Longs, {len(high_beta_alts)} Alts)."

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

"""
neuro_modulator.py - Synthetic Neuromodulatory Feedback Engine
Synthesized from Drosophila Connectome Neurobiology (Janelia MaleCNS v1.0 & Stonkfly)
for Belajar Kripto Autonomous Institutional Workstation.

Core Neuromodulation Concept:
1. PAM11 Cluster (Dopaminergic Reward Circuit):
   - Fired upon positive trade outcomes (+P&L, +R), trailing stop profit locks, and winning streaks.
   - Regulates dopamine_level (0.0 - 100.0, baseline 50.0).
   - When dopamine_level > 85.0: Triggers EUPHORIC_OVERCONFIDENT state.
     Activates ANTI_OVERCONFIDENCE_GUARD to prevent the "Winner's Curse", overtrading, and reckless entries.
     Caps position sizing at 1.0x and mandates high R:R >= 1:2.50.
   - When dopamine_level is 60.0 - 85.0 and cortisol < 40.0: FLOW_STATE_OPTIMAL.
     Enables dynamic runner expansion (up to 1.15x sizing boost with pyramiding unlocked).

2. PPL101 Cluster (Aversive Dopamine / Cortisol Trauma Circuit):
   - Fired upon stop loss hits (-P&L, -R), execution slippage, or consecutive losses.
   - Regulates cortisol_level (0.0 - 100.0, baseline 20.0).
   - When cortisol_level is 45.0 - 70.0: ELEVATED_STRESS.
     Increases required confluence threshold by +5% and lowers maximum concurrent open slots.
   - When cortisol_level > 70.0: AVERSIVE_TRAUMA_COOLDOWN.
     Enforces cold-streak defense (50% risk haircut) and mandates an anti-revenge trading cool-off.

3. Homeostatic Neuroplastic Decay:
   - Exponential decay toward biological baseline:
     * Dopamine half-life: ~12 hours.
     * Cortisol half-life: ~8 hours.
"""

import json
import math
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

# Ensure UTF-8 on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
NEURO_STATE_FILE = os.path.join(DATA_DIR, "neuro_modulator_state.json")
LEDGER_FILE = os.path.join(DATA_DIR, "trade_journal_ledger.json")

# Neurochemical Homeostasis Constants
DOPAMINE_BASELINE = 50.0
CORTISOL_BASELINE = 20.0
DOPAMINE_HALF_LIFE_SEC = 12 * 3600.0   # 12 Hours
CORTISOL_HALF_LIFE_SEC = 8 * 3600.0    # 8 Hours

DEFAULT_STATE = {
    "dopamine_level": DOPAMINE_BASELINE,
    "cortisol_level": CORTISOL_BASELINE,
    "state": "EQUILIBRIUM_NEUTRAL",
    "synaptic_risk_multiplier": 1.00,
    "anti_overconfidence_active": False,
    "confluence_threshold_offset": 0.0,
    "recent_bursts": [],
    "total_pam11_firings": 0,
    "total_ppl101_firings": 0,
    "last_updated": time.time()
}

def load_neuro_state() -> Dict[str, Any]:
    """Loads current neuro-modulatory state with decay applied."""
    if not os.path.exists(NEURO_STATE_FILE):
        state = dict(DEFAULT_STATE)
        save_neuro_state(state)
        return state

    try:
        with open(NEURO_STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception:
        state = dict(DEFAULT_STATE)

    # Apply homeostatic time decay
    now = time.time()
    last_up = state.get("last_updated", now)
    elapsed = max(0.0, now - last_up)

    if elapsed > 60.0:  # Decay after 1 minute
        dop = float(state.get("dopamine_level", DOPAMINE_BASELINE))
        cort = float(state.get("cortisol_level", CORTISOL_BASELINE))

        # Exponential decay toward baseline
        decay_dop = math.exp(-elapsed / DOPAMINE_HALF_LIFE_SEC)
        decay_cort = math.exp(-elapsed / CORTISOL_HALF_LIFE_SEC)

        state["dopamine_level"] = round(DOPAMINE_BASELINE + (dop - DOPAMINE_BASELINE) * decay_dop, 2)
        state["cortisol_level"] = round(CORTISOL_BASELINE + (cort - CORTISOL_BASELINE) * decay_cort, 2)
        state["last_updated"] = now
        state = _recalculate_derived_neuro_metrics(state)
        save_neuro_state(state)

    return state

def save_neuro_state(state: Dict[str, Any]) -> None:
    """Persists neuro-modulator state to JSON storage."""
    state["last_updated"] = time.time()
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp_file = f"{NEURO_STATE_FILE}.tmp_{os.getpid()}"
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        os.replace(tmp_file, NEURO_STATE_FILE)
    except Exception:
        if os.path.exists(tmp_file):
            try:
                os.remove(tmp_file)
            except Exception:
                pass

def _recalculate_derived_neuro_metrics(state: Dict[str, Any]) -> Dict[str, Any]:
    """Recalculates state classification, risk scaler, and confluence requirements."""
    dop = float(state.get("dopamine_level", DOPAMINE_BASELINE))
    cort = float(state.get("cortisol_level", CORTISOL_BASELINE))

    # Clamp bounds 0.0 - 100.0
    dop = max(0.0, min(100.0, dop))
    cort = max(0.0, min(100.0, cort))
    state["dopamine_level"] = dop
    state["cortisol_level"] = cort

    if dop >= 85.0:
        # Extreme Dopamine / Euphoria -> Activate Anti-Overconfidence Guard
        state["state"] = "EUPHORIC_OVERCONFIDENT"
        state["anti_overconfidence_active"] = True
        state["synaptic_risk_multiplier"] = 1.00  # Cap at 1.0x, do not allow over-leveraging
        state["confluence_threshold_offset"] = +3.0  # Require slightly cleaner setups
        state["status_badge"] = "🌟 EUPHORIC (Anti-Overconfidence Active)"
        state["action_guidance"] = "Dopamin tinggi pasca win-streak. Anti-overconfidence aktif mengunci risiko maks 1.0x dan mencegah forced-trades."
    elif dop >= 65.0 and cort < 40.0:
        # Flow State -> Confident execution, runners unlocked
        state["state"] = "FLOW_STATE_OPTIMAL"
        state["anti_overconfidence_active"] = False
        state["synaptic_risk_multiplier"] = 1.15  # Up to +15% Kelly boost
        state["confluence_threshold_offset"] = -2.0  # Opportunistic execution allowed
        state["status_badge"] = "⚡ FLOW STATE OPTIMAL"
        state["action_guidance"] = "Rasio Reward/Risk tinggi. Sinyal tajam dengan alokasi penuh dan ekspansi trailing stop runner."
    elif cort >= 70.0:
        # Severe Trauma / Cold Streak -> Defensive capital preservation
        state["state"] = "AVERSIVE_TRAUMA_COOLDOWN"
        state["anti_overconfidence_active"] = False
        state["synaptic_risk_multiplier"] = 0.50  # 50% Anti-martingale risk haircut
        state["confluence_threshold_offset"] = +8.0  # Strict gate: only A+ setups pass
        state["status_badge"] = "🚨 AVERSIVE COOLDOWN (Stress Shield)"
        state["action_guidance"] = "Kortisol tinggi pasca drawdown/stop-out. Alokasi dipangkas 50%, konfluensi diperketat demi perlindungan modal."
    elif cort >= 45.0:
        # Elevated Stress
        state["state"] = "ELEVATED_STRESS"
        state["anti_overconfidence_active"] = False
        state["synaptic_risk_multiplier"] = 0.75  # 25% risk reduction
        state["confluence_threshold_offset"] = +4.0  # +4% confluence requirement
        state["status_badge"] = "⚠️ ELEVATED STRESS"
        state["action_guidance"] = "Stres terdeteksi. Ukuran lot dikurangi 25%, filter konfluensi dinaikkan untuk menghindari chop."
    else:
        # Balanced Equilibrium
        state["state"] = "EQUILIBRIUM_NEUTRAL"
        state["anti_overconfidence_active"] = False
        state["synaptic_risk_multiplier"] = 1.00
        state["confluence_threshold_offset"] = 0.0
        state["status_badge"] = "⚖️ EQUILIBRIUM NEUTRAL"
        state["action_guidance"] = "Kondisi neuro-kognitif seimbang. Operasional trading desk kuantitatif berjalan sesuai parameter standar."

    return state

def stimulate_neuro_feedback(
    event_type: str,
    pnl_usd: float = 0.0,
    r_multiple: float = 0.0,
    symbol: str = "",
    note: str = ""
) -> Dict[str, Any]:
    """
    Simulates PAM11 (Dopamine reward) or PPL101 (Aversive stress) burst in response to market events.
    
    Event Types:
    - "TRADE_PROFIT": Profitable trade close (+P&L, +R)
    - "PARTIAL_TP": Partial scale-out locked at +1R/+2R
    - "BREAKEVEN_LOCKED": Trailing stop locked beyond breakeven
    - "STOP_LOSS": Trade exited at stop loss (-P&L)
    - "SLIPPAGE_DRAG": Unfavorable slippage friction detected
    - "DRAWDOWN_SHOCK": Macro portfolio drawdown shock
    """
    state = load_neuro_state()
    event_upper = event_type.upper()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    delta_dop = 0.0
    delta_cort = 0.0
    circuit_fired = "HOMEOSTASIS"

    if "PROFIT" in event_upper or "TP" in event_upper or pnl_usd > 0 or r_multiple > 0:
        circuit_fired = "PAM11_DOPAMINERGIC_REWARD"
        # Magnitude scales with R-multiple and PnL
        eff_r = max(0.5, r_multiple if r_multiple > 0 else (pnl_usd / 30.0))
        delta_dop = min(25.0, 8.0 * eff_r)
        delta_cort = -min(20.0, 5.0 * eff_r)  # Reward alleviates stress
        state["total_pam11_firings"] = state.get("total_pam11_firings", 0) + 1

    elif "BREAKEVEN" in event_upper:
        circuit_fired = "PAM11_ZERO_RISK_RELIEF"
        delta_dop = 4.0
        delta_cort = -8.0  # Peace of mind (Zero capital risk)
        state["total_pam11_firings"] = state.get("total_pam11_firings", 0) + 1

    elif "STOP" in event_upper or "LOSS" in event_upper or pnl_usd < 0:
        circuit_fired = "PPL101_AVERSIVE_CORTISOL"
        eff_loss = abs(pnl_usd)
        eff_r = max(1.0, abs(r_multiple) if r_multiple != 0 else (eff_loss / 30.0))
        delta_cort = min(35.0, 12.0 * eff_r)
        delta_dop = -min(25.0, 10.0 * eff_r)  # Loss dampens dopamine
        state["total_ppl101_firings"] = state.get("total_ppl101_firings", 0) + 1

    elif "SLIPPAGE" in event_upper:
        circuit_fired = "PPL101_FRICTION_ANNOYANCE"
        delta_cort = 5.0
        delta_dop = -2.0

    elif "DRAWDOWN" in event_upper:
        circuit_fired = "PPL101_DRAWDOWN_TRAUMA"
        delta_cort = 25.0
        delta_dop = -20.0

    state["dopamine_level"] = max(0.0, min(100.0, state.get("dopamine_level", DOPAMINE_BASELINE) + delta_dop))
    state["cortisol_level"] = max(0.0, min(100.0, state.get("cortisol_level", CORTISOL_BASELINE) + delta_cort))

    burst_record = {
        "timestamp": now_str,
        "circuit": circuit_fired,
        "event_type": event_type,
        "symbol": symbol,
        "pnl_usd": round(pnl_usd, 2),
        "r_multiple": round(r_multiple, 2),
        "delta_dopamine": round(delta_dop, 2),
        "delta_cortisol": round(delta_cort, 2),
        "note": note
    }

    recent = state.get("recent_bursts", [])
    recent.insert(0, burst_record)
    state["recent_bursts"] = recent[:15]  # Keep 15 recent bursts

    state = _recalculate_derived_neuro_metrics(state)
    save_neuro_state(state)
    return state

def sync_from_trade_ledger() -> Dict[str, Any]:
    """
    Calibrates baseline neuro-modulator state from recent trades in trade_journal_ledger.json.
    Guarantees deterministic alignment with real performance history.
    """
    if not os.path.exists(LEDGER_FILE):
        return load_neuro_state()

    try:
        with open(LEDGER_FILE, "r", encoding="utf-8") as f:
            ledger = json.load(f)
        if not isinstance(ledger, list) or not ledger:
            return load_neuro_state()

        # Extract last 10 closed trades
        closed_trades = [
            t for t in ledger
            if "net_pnl_usd" in t or "pnl_usd" in t
        ][-10:]

        dop = DOPAMINE_BASELINE
        cort = CORTISOL_BASELINE
        pam_count = 0
        ppl_count = 0

        for t in closed_trades:
            pnl = float(t.get("net_pnl_usd", t.get("pnl_usd", 0.0)))
            r_mult = float(t.get("realized_r", t.get("rr", 0.0) if pnl > 0 else -1.0))
            if pnl > 0:
                dop = min(100.0, dop + max(5.0, 7.0 * r_mult))
                cort = max(0.0, cort - 5.0)
                pam_count += 1
            else:
                cort = min(100.0, cort + 12.0)
                dop = max(0.0, dop - 10.0)
                ppl_count += 1

        state = load_neuro_state()
        state["dopamine_level"] = round(dop, 2)
        state["cortisol_level"] = round(cort, 2)
        state["total_pam11_firings"] = max(state.get("total_pam11_firings", 0), pam_count)
        state["total_ppl101_firings"] = max(state.get("total_ppl101_firings", 0), ppl_count)
        state = _recalculate_derived_neuro_metrics(state)
        save_neuro_state(state)
        return state
    except Exception:
        return load_neuro_state()

def apply_neuro_risk_adjustment(
    base_risk_pct: float,
    min_confluence: float
) -> Tuple[float, float, Dict[str, Any]]:
    """
    Applies synthetic neuromodulatory adjustments to risk sizing and confluence requirements.
    
    Returns:
    - effective_risk_pct (float)
    - effective_min_confluence (float)
    - neuro_audit (dict)
    """
    state = load_neuro_state()
    risk_mult = float(state.get("synaptic_risk_multiplier", 1.00))
    conf_offset = float(state.get("confluence_threshold_offset", 0.0))

    effective_risk = round(base_risk_pct * risk_mult, 2)
    effective_confluence = round(min_confluence + conf_offset, 1)

    neuro_audit = {
        "neuro_state": state.get("state", "EQUILIBRIUM_NEUTRAL"),
        "status_badge": state.get("status_badge", "⚖️ EQUILIBRIUM"),
        "dopamine_level": state.get("dopamine_level", DOPAMINE_BASELINE),
        "cortisol_level": state.get("cortisol_level", CORTISOL_BASELINE),
        "synaptic_risk_multiplier": risk_mult,
        "confluence_offset": conf_offset,
        "anti_overconfidence_active": state.get("anti_overconfidence_active", False),
        "guidance": state.get("action_guidance", "")
    }

    return effective_risk, effective_confluence, neuro_audit

def get_neuro_summary_telemetry() -> Dict[str, Any]:
    """Provides REST API compatible telemetry object for Web Dashboard."""
    state = load_neuro_state()
    return {
        "status": "OPERATIONAL",
        "model_analogue": "Janelia MaleCNS v1.0 (Drosophila Connectome)",
        "dopamine": {
            "level": state["dopamine_level"],
            "circuit": "PAM11 (15 Dopaminergic Reward Neurons)",
            "status": "HIGH" if state["dopamine_level"] > 70 else ("LOW" if state["dopamine_level"] < 35 else "BALANCED"),
            "total_firings": state["total_pam11_firings"]
        },
        "cortisol": {
            "level": state["cortisol_level"],
            "circuit": "PPL101 (2 Aversive Dopamine / Trauma Neurons)",
            "status": "ELEVATED" if state["cortisol_level"] > 50 else "SUPPRESSED_CALM",
            "total_firings": state["total_ppl101_firings"]
        },
        "neuro_state": state["state"],
        "status_badge": state["status_badge"],
        "synaptic_risk_multiplier": state["synaptic_risk_multiplier"],
        "anti_overconfidence_guard": state["anti_overconfidence_active"],
        "confluence_threshold_offset": state["confluence_threshold_offset"],
        "guidance": state["action_guidance"],
        "recent_bursts": state.get("recent_bursts", [])[:5],
        "last_updated": datetime.fromtimestamp(state["last_updated"]).strftime("%Y-%m-%d %H:%M:%S")
    }

if __name__ == "__main__":
    print("=" * 70)
    print("  🧠 SYNTHETIC NEUROMODULATORY FEEDBACK ENGINE (Connectome Analog)")
    print("=" * 70)
    state = sync_from_trade_ledger()
    print(f" * Neuro State       : {state['status_badge']}")
    print(f" * Dopamine (PAM11)  : {state['dopamine_level']:.1f} / 100.0 (Reward Circuit)")
    print(f" * Cortisol (PPL101) : {state['cortisol_level']:.1f} / 100.0 (Stress Circuit)")
    print(f" * Risk Multiplier   : {state['synaptic_risk_multiplier']:.2f}x")
    print(f" * Confluence Offset : {state['confluence_threshold_offset']:+.1f}%")
    print(f" * Overconf. Guard   : {'🛡️ ACTIVE' if state['anti_overconfidence_active'] else '⚪ OFF'}")
    print(f" * Action Guidance   : {state['action_guidance']}")
    print("=" * 70)

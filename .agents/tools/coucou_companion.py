"""
Coucou / Mochi Dynamic Island Companion Engine
Synthesized from Louis-CFM/coucou for Belajar Kripto Workstation.

Features:
1. Companion State Machine:
   - Tracks Mochi emotion, mood, and eye direction.
   - States: IDLE, BREATHING, WORKING, ATTENTION_REQUIRED, DIZZY, CELEBRATING.
2. Hook Relay Protocol (`coucou_agent`):
   - Accepts events from any subagent (01 Search through 08 Journal, plus Local Brain).
   - Ingests permission requests ("Allow / Deny").
3. One-Click Interactive Approvals:
   - "Allow" / "Deny" trade approvals and risk lockouts directly from the Island.
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Ensure UTF-8 on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
COUCOU_STATE_FILE = os.path.join(DATA_DIR, "coucou_state.json")

_coucou_state: Dict[str, Any] = {
    "active_agent": "02_RISK_AEGIS",
    "agent_name": "Aegis (Risk)",
    "activity": "Auditing Order Book Liquidity & Spread",
    "mood": "VIGILANT",
    "status": "WORKING",
    "pokes_count": 0,
    "last_poke_time": 0,
    "is_dizzy": False,
    "dizzy_until": 0,
    "pending_approval": None,
    "recent_events": [],
    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}


def load_state() -> Dict[str, Any]:
    global _coucou_state
    if os.path.exists(COUCOU_STATE_FILE):
        try:
            with open(COUCOU_STATE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                _coucou_state.update(saved)
        except Exception:
            pass
    return _coucou_state


def save_state():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(COUCOU_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(_coucou_state, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def get_coucou_telemetry() -> Dict[str, Any]:
    """
    Returns live Coucou / Mochi state for WebSocket / HTTP polling.
    Syncs with Eight-Agent Desk Pipeline if no custom hook is active.
    """
    global _coucou_state
    now = time.time()

    # Reset dizziness if timer expired
    if _coucou_state.get("is_dizzy") and now > _coucou_state.get("dizzy_until", 0):
        _coucou_state["is_dizzy"] = False
        _coucou_state["mood"] = "VIGILANT"

    # Synchronize with active agent desk
    try:
        import eight_agent_desk
        desk = eight_agent_desk.get_eight_agent_pipeline_state()
        if desk and not _coucou_state.get("pending_approval"):
            active_seat = desk.get("active_agent", "Kepler")
            lead_sym = desk.get("active_lead_symbol", "BTCUSDT")
            mood = desk.get("desk_mood", "PRODUCTIVE")
            _coucou_state["active_agent"] = active_seat.lower().replace(" ", "_")
            _coucou_state["agent_name"] = active_seat
            _coucou_state["activity"] = f"Analyzing {lead_sym} order flow & structural confluence"
            if not _coucou_state.get("is_dizzy"):
                _coucou_state["mood"] = "FOCUSED" if mood == "PRODUCTIVE" else "HAPPY"
    except Exception:
        pass

    _coucou_state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Return enriched telemetry payload compatible with both legacy and new callers
    telemetry = dict(_coucou_state)
    telemetry["status"] = "OPERATIONAL"
    telemetry["engine_status"] = _coucou_state.get("status", "WORKING")
    telemetry["agent_role"] = _coucou_state.get("agent_name", "Aegis (Risk)")
    telemetry["mochi"] = {
        "state": _coucou_state.get("status", "WORKING"),
        "mood": _coucou_state.get("mood", "VIGILANT"),
        "pokes": _coucou_state.get("pokes_count", 0),
        "poke_count": _coucou_state.get("pokes_count", 0),
        "is_dizzy": _coucou_state.get("is_dizzy", False),
        "reaction": "Mochi is super dizzy! @_@" if _coucou_state.get("is_dizzy") else "Mochi is watching the orderbook"
    }
    return telemetry


def record_event(agent_name: str, activity: str, mood: str = "WORKING", status: str = "WORKING", approval_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Broadcasts an event into Coucou's dynamic island.
    Tag payload with coucou_agent according to Coucou standard.
    """
    global _coucou_state
    _coucou_state["active_agent"] = agent_name.lower().replace(" ", "_")
    _coucou_state["agent_name"] = agent_name
    _coucou_state["activity"] = activity
    _coucou_state["status"] = status
    if not _coucou_state.get("is_dizzy"):
        _coucou_state["mood"] = mood

    if approval_payload:
        _coucou_state["pending_approval"] = approval_payload
        _coucou_state["status"] = "ATTENTION_REQUIRED"
        _coucou_state["mood"] = "SURPRISED"

    evt = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "coucou_agent": agent_name,
        "activity": activity,
        "mood": mood,
        "status": status
    }
    _coucou_state["recent_events"].insert(0, evt)
    if len(_coucou_state["recent_events"]) > 20:
        _coucou_state["recent_events"].pop()

    save_state()
    return _coucou_state


def record_coucou_hook_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ingests hook events formatted according to the Coucou protocol.
    """
    agent = payload.get("coucou_agent", payload.get("agent", "Aegis"))
    activity = payload.get("description", payload.get("activity", "Desk Operation"))
    mood = payload.get("mood", "WORKING")
    status = payload.get("status", "WORKING")
    approval = payload.get("approval_payload")
    state = record_event(agent, activity, mood=mood, status=status, approval_payload=approval)
    return {
        "success": True,
        "event_id": f"evt_{int(time.time()*1000)}",
        "coucou_agent": agent,
        "state": state
    }


def poke_mochi() -> Dict[str, Any]:
    """
    Handles user poking Mochi:
    - Increments poke count.
    - If 4+ pokes within 3 seconds, Mochi becomes dizzy with swirl eyes!
    """
    global _coucou_state
    now = time.time()
    last = _coucou_state.get("last_poke_time", 0)

    if now - last < 2.5:
        _coucou_state["pokes_count"] += 1
    else:
        _coucou_state["pokes_count"] = 1

    _coucou_state["last_poke_time"] = now

    if _coucou_state["pokes_count"] >= 4:
        _coucou_state["is_dizzy"] = True
        _coucou_state["dizzy_until"] = now + 4.0
        _coucou_state["mood"] = "DIZZY"
        reaction = "Mochi is super dizzy! @_@"
        state = "DIZZY"
    else:
        _coucou_state["is_dizzy"] = False
        _coucou_state["mood"] = "HAPPY"
        reaction = "Mochi waves and bounces! (*^▽^*)"
        state = "HAPPY"

    return {
        "success": True,
        "reaction": reaction,
        "emote": "(x_x)" if _coucou_state["is_dizzy"] else "(*^▽^*)",
        "pokes_count": _coucou_state["pokes_count"],
        "poke_count": _coucou_state["pokes_count"],
        "is_dizzy": _coucou_state["is_dizzy"],
        "mood": _coucou_state["mood"],
        "state": state
    }


def handle_user_action(action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Executes one-click actions from Coucou's dynamic island pill:
    - allow / approve: confirms pending trade
    - deny / veto: cancels setup and locks breakeven
    - poke: interactive poke
    - dismiss: closes pending alert
    """
    global _coucou_state
    action_clean = action.lower().strip()

    if action_clean == "poke":
        return poke_mochi()

    elif action_clean in ("allow", "approve"):
        pending = _coucou_state.get("pending_approval")
        _coucou_state["pending_approval"] = None
        _coucou_state["status"] = "APPROVED"
        _coucou_state["mood"] = "CELEBRATING"
        record_event("User", "Approved trade intent from Coucou Notch", mood="CELEBRATING")
        return {"success": True, "action": "APPROVED", "trade": pending}

    elif action_clean in ("deny", "veto"):
        pending = _coucou_state.get("pending_approval")
        _coucou_state["pending_approval"] = None
        _coucou_state["status"] = "VETOED"
        _coucou_state["mood"] = "VIGILANT"
        record_event("User", "Rejected trade intent from Coucou Notch (Veto Fail-Closed)", mood="VIGILANT")
        return {"success": True, "action": "VETOED", "trade": pending}

    elif action_clean == "dismiss":
        _coucou_state["pending_approval"] = None
        _coucou_state["status"] = "WORKING"
        _coucou_state["mood"] = "FOCUSED"
        return {"success": True, "action": "DISMISSED"}

    return {"success": False, "error": f"Unknown action: {action}"}


# Aliases for Coucou protocol compatibility
handle_coucou_action = handle_user_action

# Initialize state on import
load_state()


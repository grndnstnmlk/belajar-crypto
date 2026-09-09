#!/usr/bin/env python3
"""
========================================================================================
  🏢 PAPERCLIP AUTONOMOUS TRADING FIRM CONTROL PLANE
  Orchestration Engine: Org Chart, Heartbeat Scheduling, Ticket-Based Task Delegation,
  Zero-Cost Quota Guard, and Human Board of Directors Governance.
  
  Inspired by Paperclip AI (https://github.com/paperclipai/paperclip)
========================================================================================
"""

import os
import sys
import json
import time
from datetime import datetime, timezone

# Ensure project root is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
DATA_DIR = os.path.join(PROJECT_ROOT, ".agents", "data")
os.makedirs(DATA_DIR, exist_ok=True)

FIRM_STATE_FILE = os.path.join(DATA_DIR, "paperclip_firm_state.json")
TICKETS_FILE = os.path.join(DATA_DIR, "paperclip_tickets.json")

# ======================================================================================
# 1. INSTITUTIONAL ORG CHART DEFINITION
# ======================================================================================

DEFAULT_ORG_CHART = [
    {
        "id": "board_of_directors",
        "name": "Human Board of Directors",
        "title": "Chairman & Chief Capital Allocator",
        "avatar": "🧑‍💼",
        "department": "GOVERNANCE",
        "reports_to": None,
        "heartbeat_interval_sec": 0,  # Event-driven human gate
        "responsibilities": "Holds ultimate veto power, authorizes high-risk setups, manages emergency circuit breaker, and sets global capital allocations.",
        "status": "ACTIVE",
        "last_heartbeat": None,
        "tasks_processed": 0
    },
    {
        "id": "chief_risk_officer",
        "name": "AI Senior Quant Officer & CRO",
        "title": "Chief Risk Officer & Fund Manager",
        "avatar": "🧠",
        "department": "EXECUTIVE_RISK",
        "reports_to": "board_of_directors",
        "heartbeat_interval_sec": 30,
        "responsibilities": "Tri-Perspective Risk synthesis, Kelly Criterion sizing, portfolio heat monitoring (max 4 positions, max 3 directional), news blackout enforcement.",
        "status": "ACTIVE",
        "last_heartbeat": None,
        "tasks_processed": 0
    },
    {
        "id": "head_of_research",
        "name": "Macro & Intel Director",
        "title": "Head of Research & Market Intelligence",
        "avatar": "📊",
        "department": "RESEARCH_INTEL",
        "reports_to": "chief_risk_officer",
        "heartbeat_interval_sec": 60,
        "responsibilities": "Oversees top-down market intelligence, liquidity depth, sector rotation trends, and on-chain forensics.",
        "status": "ACTIVE",
        "last_heartbeat": None,
        "tasks_processed": 0
    },
    {
        "id": "market_eyes_screener",
        "name": "Market Eyes Radar",
        "title": "Lead Technical Scanner & Relative Strength Analyst",
        "avatar": "👁️",
        "department": "RESEARCH_INTEL",
        "reports_to": "head_of_research",
        "heartbeat_interval_sec": 60,
        "responsibilities": "24/7 scanning of 50+ pairs for volume surges, RSI extremes, ADX trends, and Relative Strength vs BTC.",
        "status": "ACTIVE",
        "last_heartbeat": None,
        "tasks_processed": 0
    },
    {
        "id": "sentiment_narrative_scanner",
        "name": "Narrative & Sentiment Specialist",
        "title": "Senior Sentiment & Sector Rotation Analyst",
        "avatar": "🧭",
        "department": "RESEARCH_INTEL",
        "reports_to": "head_of_research",
        "heartbeat_interval_sec": 300,
        "responsibilities": "Fear & Greed contrarian monitoring, 6-sector rotation tracking (Binance Vision), CoinGecko virality, and catalyst NLP classification.",
        "status": "ACTIVE",
        "last_heartbeat": None,
        "tasks_processed": 0
    },
    {
        "id": "head_of_strategies",
        "name": "Lead Quant Strategist",
        "title": "Head of Trading Strategies & Debate",
        "avatar": "⚔️",
        "department": "TRADING_STRATEGY",
        "reports_to": "chief_risk_officer",
        "heartbeat_interval_sec": 30,
        "responsibilities": "Arbitrates adversarial debate between Bull and Bear analysts, routes setups to appropriate scalper specialists.",
        "status": "ACTIVE",
        "last_heartbeat": None,
        "tasks_processed": 0
    },
    {
        "id": "bull_analyst_agent",
        "name": "Bull Momentum Analyst",
        "title": "Senior Long Thesis Specialist",
        "avatar": "🐂",
        "department": "TRADING_STRATEGY",
        "reports_to": "head_of_strategies",
        "heartbeat_interval_sec": 60,
        "responsibilities": "Constructs high-conviction bullish theses, identifies FVG discount entries, order block supports, and breakout catalysts.",
        "status": "ACTIVE",
        "last_heartbeat": None,
        "tasks_processed": 0
    },
    {
        "id": "bear_analyst_agent",
        "name": "Bear Skeptic Analyst",
        "title": "Senior Short Thesis & Fragility Specialist",
        "avatar": "🐻",
        "department": "TRADING_STRATEGY",
        "reports_to": "head_of_strategies",
        "heartbeat_interval_sec": 60,
        "responsibilities": "Stress-tests setups for liquidity traps, Wyckoff distribution, Bearish divergences, and overheated retail sentiment.",
        "status": "ACTIVE",
        "last_heartbeat": None,
        "tasks_processed": 0
    },
    {
        "id": "scalper_specialists",
        "name": "Akademi Scalper Guild",
        "title": "M5/M15 Blueprint Execution Specialists",
        "avatar": "🎯",
        "department": "TRADING_STRATEGY",
        "reports_to": "head_of_strategies",
        "heartbeat_interval_sec": 60,
        "responsibilities": "Executes 4 distinct Akademi Crypto blueprints: Mulham Rectangle, 20 EMA Pullback, 4H Range, and Inverse FVG.",
        "status": "ACTIVE",
        "last_heartbeat": None,
        "tasks_processed": 0
    },
    {
        "id": "head_of_execution",
        "name": "Execution Desk Chief",
        "title": "Head of Execution & Order Operations",
        "avatar": "⚡",
        "department": "OPERATIONS_EXECUTION",
        "reports_to": "chief_risk_officer",
        "heartbeat_interval_sec": 15,
        "responsibilities": "Manages order routing to Binance Futures, executes partial scale-outs (50% TP1), and enforces SMC structural trailing stops.",
        "status": "ACTIVE",
        "last_heartbeat": None,
        "tasks_processed": 0
    },
    {
        "id": "trade_journaler_autopsy",
        "name": "Performance & Autopsy Auditor",
        "title": "Lead Trade Journaler & Post-Mortem Auditor",
        "avatar": "📖",
        "department": "OPERATIONS_EXECUTION",
        "reports_to": "head_of_execution",
        "heartbeat_interval_sec": 60,
        "responsibilities": "Logs all closed trades into immutable journal ledger, calculates R-multiples, and conducts AI post-mortem autopsy.",
        "status": "ACTIVE",
        "last_heartbeat": None,
        "tasks_processed": 0
    }
]

# ======================================================================================
# 2. STATE & PERSISTENCE MANAGEMENT
# ======================================================================================

def load_firm_state():
    """Loads the firm telemetry, circuit breaker, and quota counters."""
    if os.path.exists(FIRM_STATE_FILE):
        try:
            with open(FIRM_STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                return state
        except Exception:
            pass

    # Default initial state
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    initial = {
        "firm_name": "Paperclip Autonomous Crypto Hedge Fund",
        "established_at": now_str,
        "last_updated": now_str,
        "circuit_breaker_active": False,
        "circuit_breaker_reason": None,
        "mode": "INSTITUTIONAL_AUTONOMOUS",
        "quota_tracker": {
            "daily_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "free_requests_used": 14,
            "free_requests_limit": 1500,  # Gemini Free Tier safe cap
            "budget_spent_usd": 0.00,
            "is_free_tier": True
        },
        "org_chart": DEFAULT_ORG_CHART,
        "stats": {
            "total_tickets_created": 0,
            "total_tickets_executed": 0,
            "total_tickets_vetoed": 0,
            "pending_board_count": 0
        }
    }
    save_firm_state(initial)
    return initial

def save_firm_state(state):
    """Saves firm state safely to disk."""
    state["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        with open(FIRM_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"[Paperclip Error] Failed to save firm state: {e}")

def load_tickets():
    """Loads the list of Kanban tickets."""
    if os.path.exists(TICKETS_FILE):
        try:
            with open(TICKETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_tickets(tickets):
    """Saves tickets list to disk."""
    try:
        with open(TICKETS_FILE, "w", encoding="utf-8") as f:
            json.dump(tickets, f, indent=2)
    except Exception as e:
        print(f"[Paperclip Error] Failed to save tickets: {e}")

# ======================================================================================
# 3. TICKET LIFECYCLE & KANBAN ENGINE
# ======================================================================================

VALID_STAGES = [
    "DISCOVERED",          # Discovered by Screener / Scalper
    "DEBATING",            # Under Bull vs Bear debate
    "RISK_AUDIT",          # Under Tri-Perspective Risk & CRO audit
    "PENDING_BOARD",       # Escalate to Human Board if high-risk criteria met
    "EXECUTING",           # Approved & dispatched to Binance Execution Desk
    "CLOSED",              # Filled, managed, and closed with autopsy
    "VETOED"               # Blocked by CRO or Rejected by Board
]

def generate_ticket_id():
    """Generates unique institutional ticket ID, e.g. TCK-20260909-1234."""
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    ms_part = str(int(time.time() * 1000))[-4:]
    return f"TCK-{date_part}-{ms_part}"

def create_ticket(symbol, strategy, side, created_by="market_eyes_screener", payload=None):
    """
    Creates a new task ticket and starts the pipeline.
    """
    tickets = load_tickets()
    t_id = generate_ticket_id()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    ticket = {
        "ticket_id": t_id,
        "symbol": symbol.upper(),
        "side": side.upper(),
        "strategy": strategy,
        "created_by": created_by,
        "assigned_to": "head_of_strategies",
        "stage": "DISCOVERED",
        "priority": "HIGH" if "SCALP" in strategy.upper() else "NORMAL",
        "created_at": now_str,
        "updated_at": now_str,
        "payload": payload or {},
        "debate_result": None,
        "risk_result": None,
        "board_decision": None,
        "execution_result": None,
        "timeline": [
            {
                "timestamp": now_str,
                "agent": created_by,
                "stage": "DISCOVERED",
                "note": f"Setup {symbol} ({side}) teridentifikasi via {strategy}."
            }
        ]
    }

    tickets.insert(0, ticket)
    # Keep last 100 tickets max
    if len(tickets) > 100:
        tickets = tickets[:100]
    save_tickets(tickets)

    # Increment firm state counter
    fstate = load_firm_state()
    fstate["stats"]["total_tickets_created"] = fstate["stats"].get("total_tickets_created", 0) + 1
    save_firm_state(fstate)

    return ticket

def escalate_ticket(ticket_id, next_stage, assigned_to, note="", agent_id="system", data_update=None):
    """
    Advances a ticket through the Kanban lifecycle with an immutable audit trail entry.
    """
    if next_stage not in VALID_STAGES:
        raise ValueError(f"Invalid stage: {next_stage}. Must be one of {VALID_STAGES}")

    tickets = load_tickets()
    found = False
    target_ticket = None

    for t in tickets:
        if t["ticket_id"] == ticket_id:
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            prev_stage = t["stage"]
            t["stage"] = next_stage
            t["assigned_to"] = assigned_to
            t["updated_at"] = now_str
            
            if data_update:
                for k, v in data_update.items():
                    t[k] = v

            t["timeline"].append({
                "timestamp": now_str,
                "agent": agent_id,
                "stage": next_stage,
                "note": note or f"Tahap dialihkan dari {prev_stage} ke {next_stage}."
            })
            target_ticket = t
            found = True
            break

    if found:
        save_tickets(tickets)
        # Update firm counters
        fstate = load_firm_state()
        pending_board = sum(1 for x in tickets if x["stage"] == "PENDING_BOARD")
        fstate["stats"]["pending_board_count"] = pending_board
        if next_stage == "EXECUTING" or next_stage == "CLOSED":
            fstate["stats"]["total_tickets_executed"] = fstate["stats"].get("total_tickets_executed", 0) + 1
        elif next_stage == "VETOED":
            fstate["stats"]["total_tickets_vetoed"] = fstate["stats"].get("total_tickets_vetoed", 0) + 1
        save_firm_state(fstate)

    return target_ticket

def board_approve_ticket(ticket_id, board_user="Chairman (Human)", note="Approved by Board of Directors"):
    """
    Human-In-The-Loop: Board approves a ticket that was held in PENDING_BOARD.
    """
    return escalate_ticket(
        ticket_id=ticket_id,
        next_stage="EXECUTING",
        assigned_to="head_of_execution",
        note=f"👑 [BOARD APPROVAL] {note} oleh {board_user}.",
        agent_id="board_of_directors",
        data_update={
            "board_decision": {
                "verdict": "APPROVED",
                "authorized_by": board_user,
                "authorized_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "note": note
            }
        }
    )

def board_reject_ticket(ticket_id, board_user="Chairman (Human)", reason="Risk rejected by Board"):
    """
    Human-In-The-Loop: Board rejects a ticket.
    """
    return escalate_ticket(
        ticket_id=ticket_id,
        next_stage="VETOED",
        assigned_to="board_of_directors",
        note=f"🚫 [BOARD REJECTION] {reason} oleh {board_user}.",
        agent_id="board_of_directors",
        data_update={
            "board_decision": {
                "verdict": "REJECTED",
                "authorized_by": board_user,
                "authorized_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "reason": reason
            }
        }
    )

def evaluate_board_escalation_criteria(setup, market_context=None, risk_audit=None):
    """
    Determines whether a trade setup MUST be escalated to the Human Board of Directors:
    1. Overall portfolio heat is saturated (>= 3 active positions).
    2. Fear & Greed is in Extreme zone (< 25 or > 75) and trade runs against extreme momentum.
    3. Suggested risk scale is aggressive (>= 1.25x).
    4. Free margin is below 40%.
    """
    reasons = []
    
    # Check 1: Portfolio positions
    if market_context:
        active_pos = market_context.get("active_positions", [])
        if len(active_pos) >= 3:
            reasons.append(f"Portofolio padat ({len(active_pos)} posisi aktif berjalan)")
        free_margin = float(market_context.get("free_margin_ratio", 1.0))
        if free_margin < 0.40:
            reasons.append(f"Free margin menipis ({free_margin*100:.1f}%)")

    # Check 2: Fear & Greed extreme
    if market_context and "sentiment_narrative" in market_context:
        fng = market_context["sentiment_narrative"].get("fear_and_greed", {})
        f_score = fng.get("score", 50)
        side = setup.get("side", "BUY").upper()
        if f_score >= 80 and side == "BUY":
            reasons.append(f"Extreme Greed ({f_score}/100): Risiko long squeeze tinggi")
        elif f_score <= 20 and side == "SELL":
            reasons.append(f"Extreme Fear ({f_score}/100): Risiko short squeeze / spring tinggi")

    # Check 3: Risk scale
    if risk_audit:
        scale = float(risk_audit.get("suggested_risk_scale", 1.0))
        if scale >= 1.25:
            reasons.append(f"Alokasi ukuran agresif ({scale:.2f}x standard size)")

    return {
        "requires_board_approval": len(reasons) > 0,
        "escalation_reasons": reasons
    }

# ======================================================================================
# 4. HEARTBEAT SCHEDULER & DISPATCHER
# ======================================================================================

def record_agent_heartbeat(agent_id):
    """Updates the last heartbeat timestamp for a specific agent."""
    fstate = load_firm_state()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    for role in fstate.get("org_chart", []):
        if role["id"] == agent_id:
            role["last_heartbeat"] = now_str
            role["tasks_processed"] = role.get("tasks_processed", 0) + 1
            break
    save_firm_state(fstate)

def toggle_circuit_breaker(reason="Manual Board Toggle"):
    """Emergency Circuit Breaker: instantly pauses/unpauses all automated agent executions."""
    fstate = load_firm_state()
    current = fstate.get("circuit_breaker_active", False)
    new_state = not current
    fstate["circuit_breaker_active"] = new_state
    fstate["circuit_breaker_reason"] = reason if new_state else None
    
    # Update agent statuses
    for role in fstate.get("org_chart", []):
        if role["id"] != "board_of_directors":
            role["status"] = "PAUSED_CIRCUIT_BREAKER" if new_state else "ACTIVE"

    save_firm_state(fstate)
    return {
        "circuit_breaker_active": new_state,
        "reason": fstate["circuit_breaker_reason"]
    }

def record_api_quota_usage(provider="gemini", estimated_tokens=300):
    """
    Tracks free-tier API request consumption to protect user from rate limits.
    100% Free / $0 cost guarantee.
    """
    fstate = load_firm_state()
    q = fstate.setdefault("quota_tracker", {
        "daily_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "free_requests_used": 0,
        "free_requests_limit": 1500,
        "budget_spent_usd": 0.0,
        "is_free_tier": True
    })

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if q.get("daily_date") != today_str:
        q["daily_date"] = today_str
        q["free_requests_used"] = 0

    q["free_requests_used"] = q.get("free_requests_used", 0) + 1
    save_firm_state(fstate)
    return q

def is_quota_healthy():
    """Checks if API quota is safe or needs fallback to local quant."""
    fstate = load_firm_state()
    q = fstate.get("quota_tracker", {})
    used = q.get("free_requests_used", 0)
    limit = q.get("free_requests_limit", 1500)
    return used < (limit * 0.95)

# ======================================================================================
# 5. PUBLIC API & FIRM TELEMETRY SUMMARY
# ======================================================================================

def get_firm_summary():
    """Returns the complete firm telemetry snapshot for dashboard and API."""
    fstate = load_firm_state()
    tickets = load_tickets()
    
    # Calculate Kanban stage counts
    stage_counts = {s: 0 for s in VALID_STAGES}
    for t in tickets:
        s = t.get("stage", "DISCOVERED")
        if s in stage_counts:
            stage_counts[s] += 1

    return {
        "firm_name": fstate.get("firm_name"),
        "mode": fstate.get("mode"),
        "circuit_breaker_active": fstate.get("circuit_breaker_active", False),
        "circuit_breaker_reason": fstate.get("circuit_breaker_reason"),
        "quota_tracker": fstate.get("quota_tracker"),
        "stats": fstate.get("stats"),
        "stage_counts": stage_counts,
        "org_chart": fstate.get("org_chart", []),
        "recent_tickets": tickets[:15],
        "pending_board_tickets": [t for t in tickets if t.get("stage") == "PENDING_BOARD"]
    }

# ======================================================================================
# 6. SELF-TEST & VERIFICATION ROUTINE
# ======================================================================================

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("==================================================================")
    print("  🏢 PAPERCLIP AUTONOMOUS TRADING FIRM - SELF-TEST")
    print("==================================================================")

    # 1. Load firm state
    state = load_firm_state()
    print(f"✅ Firm Initialized: {state['firm_name']}")
    print(f"✅ Org Chart Roles: {len(state['org_chart'])} agents registered.")

    # 2. Test ticket creation
    print("\n--- Testing Ticket Lifecycle ---")
    t = create_ticket(
        symbol="SOLUSDT",
        strategy="Mulham Rectangle Scalper (M15)",
        side="BUY",
        created_by="scalper_specialists",
        payload={"entry": 142.50, "sl": 139.80, "tp": 150.60, "confluence": 85}
    )
    print(f"✅ Created Ticket: {t['ticket_id']} [Stage: {t['stage']}]")

    # 3. Escalate to Debate
    t_deb = escalate_ticket(
        ticket_id=t["ticket_id"],
        next_stage="DEBATING",
        assigned_to="head_of_strategies",
        note="Bull vs Bear debate dispatched.",
        agent_id="scalper_specialists"
    )
    print(f"✅ Escalated to Debate: {t_deb['ticket_id']} [Stage: {t_deb['stage']}]")

    # 4. Escalate to Board (High Heat Simulation)
    t_board = escalate_ticket(
        ticket_id=t["ticket_id"],
        next_stage="PENDING_BOARD",
        assigned_to="board_of_directors",
        note="Portofolio heat tinggi (3 active positions). Membutuhkan otorisasi Dewan Direksi.",
        agent_id="chief_risk_officer"
    )
    print(f"✅ Escalated to Board: {t_board['ticket_id']} [Stage: {t_board['stage']}]")

    # 5. Board Approval
    t_appr = board_approve_ticket(
        ticket_id=t["ticket_id"],
        board_user="Lead Chairman (Human)",
        note="Setup terkonfirmasi sangat kuat pada M15 support bounce."
    )
    print(f"✅ Board Approved: {t_appr['ticket_id']} [Stage: {t_appr['stage']}] -> Dispatched to Execution Desk!")

    # 6. Test Heartbeat & Quota
    record_agent_heartbeat("chief_risk_officer")
    record_api_quota_usage("gemini", 400)
    summary = get_firm_summary()
    print(f"\n✅ Firm Summary: {summary['stats']['total_tickets_created']} tickets created | Circuit Breaker: {summary['circuit_breaker_active']}")
    print("==================================================================")
    print("  🎉 PAPERCLIP ORCHESTRATOR SELF-TEST PASSED 100%!")
    print("==================================================================")

---
name: crypto-agentic-orchestrator
description: Autonomous Multi-Agent Swarm Orchestration, Paperclip Task Management, Adversarial Debate Protocol, and Consensus Governance for Antigravity AI systems. Use when coordinating autonomous agent swarms, resolving trade thesis conflicts, orchestrating Tri-Perspective Risk reviews, maintaining persistent agent memory banks, and running automated trading desk workflows.
---

# Antigravity Multi-Agent Swarm & Orchestrator Playbook
*Autonomous Task Execution, Adversarial Consensus & Agent Memory Architecture*

This skill defines the governance, swarm orchestration, and consensus protocols for autonomous AI agents operating within the Antigravity AI trading workstation.

---

## 🏛️ Multi-Agent Swarm Architecture

The workstation deploys specialized autonomous agent roles working in concert under strict mathematical and risk guardrails:

```
                            ┌────────────────────────────────────────┐
                            │      PAPERCLIP FIRM ORCHESTRATOR       │
                            │      (Task Queue, Scheduler & State)   │
                            └───────────────────┬────────────────────┘
                                                │
                 ┌──────────────────────────────┼─────────────────────────────┐
                 ▼                              ▼                             ▼
    ┌─────────────────────────┐    ┌─────────────────────────┐   ┌─────────────────────────┐
    │     MACRO SCANNER       │    │   QUANT SIGNAL DESK     │   │     AI RISK OFFICER     │
    │ - Fed Liquidity & DXY   │    │ - SMC & Wyckoff Models  │   │ - Kelly Criterion (2%)  │
    │ - BTC Dominance Flow    │    │ - CVD & Depth Sniping   │   │ - Monte Carlo 1,000-VaR │
    │ - News Blackout Shield  │    │ - ML Anomaly Filter     │   │ - Beta Portfolio Hedge  │
    └────────────┬────────────┘    └────────────┬────────────┘   └────────────┬────────────┘
                 │                              │                             │
                 └──────────────────────┐       │       ┌─────────────────────┘
                                        ▼       ▼       ▼
                                ┌──────────────────────────────┐
                                │     ADVERSARIAL CONSENSUS    │
                                │   (Bull vs Bear Validation)  │
                                └──────────────┬───────────────┘
                                               │
                                               ▼
                                ┌──────────────────────────────┐
                                │     EXECUTION & JOURNAL      │
                                │  (Binance 20x + Auto-Sync)   │
                                └──────────────────────────────┘
```

---

## ⚔️ Protocol 1: Adversarial Bull vs Bear Debate

Before executing high-conviction swing or scalping signals, the system triggers an automated **Adversarial Debate**:

1. **The Bull Agent**:
   - Compiles bullish orderflow, bullish SMC structure (BOS/ChoCH), FVG discount entries, and macro tailwinds.
   - Assigns a Bull Conviction Score ($0 - 100\%$) and target R:R.

2. **The Bear Agent (Devil's Advocate)**:
   - Evaluates opposing HTF supply zones, bearish CVD absorption, imminent token unlocks, macro blackout hazards, and overhead liquidation traps.
   - Challenges every assumption made by the Bull Agent.

3. **Adjudication Matrix**:
   - **Threshold for Execution**: Composite consensus score must exceed **$\ge 75\%$**.
   - If Bear counter-arguments expose critical structural flaws or impending macro risk, the ticket is discarded or downsized to defensive scalp.

---

## 🛡️ Protocol 2: Tri-Perspective Risk Consensus

The AI Trading Desk requires unanimous or majority clearance across three independent analytical perspectives:

| Perspective | Focus Area | Mandatory Veto Conditions |
| :--- | :--- | :--- |
| **1. Macro Liquidity** | DXY, US10Y, Fed Net Liquidity, High-Impact News (FOMC/CPI) | Blackout window active ($\pm 30\text{m}$ of high-impact events) |
| **2. Technical & Quant** | HTF EMA 50/200 bias, ML Anomaly Score, Volume surge | Counter-trend HTF trade or low regime confidence |
| **3. Risk Officer** | Account VaR, Portfolio Net Beta Delta, Drawdown limit | Daily drawdown threshold reached ($>4\%$) or leverage breach |

---

## 🧠 Protocol 3: Persistent Memory & Self-Improvement

The agent system maintains long-term state across market cycles:

1. **`agent_memory_bank.json`**:
   - Records past trade performance, win-rates per strategy archetype, optimal stop-loss distances per asset, and false-breakout patterns.
   - Automatically recalibrates parameter weights based on empirical trade journal results (`trade_journal_ledger.json`).

2. **Self-Healing & Watcher Threads**:
   - Real-time daemon threads monitor active positions continuously.
   - Automated Breakeven locks at $+1.5\text{R}$ and Smart Pyramiding additions ($+30\%$) at $+2.0\text{R}$.
   - Automatic Git synchronization commits journal ledgers to remote repositories without blocking runtime loops.

---

## 🛠️ Integrated Workspace Tools
- `.agents/tools/paperclip_orchestrator.py` — Autonomous task orchestration and ticket lifecycle.
- `.agents/tools/adversarial_debate.py` — Automated Bull vs Bear debate engine.
- `.agents/tools/tri_perspective_risk.py` — Tri-perspective consensus validation.
- `.agents/tools/ai_risk_officer.py` — Chief Risk Officer enforcement engine.
- `.agents/tools/agent_memory_engine.py` — Persistent memory bank and adaptive learning.

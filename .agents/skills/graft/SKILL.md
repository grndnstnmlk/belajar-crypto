---
name: graft
description: Codebase knowledge graph and architectural context layer skill powered by Graft (trailhq/graft). Enables AI coding agents to map repository architecture, parse dependencies, trace data pipelines, and understand complex codebases without cold-start grepping. Use when analyzing repository architecture, mapping module relationships, generating codebase graphs, or orienting an agent in large codebases.
---

# Graft — Codebase Knowledge Graph & Context Layer Skill

Powered by **Graft** ([trailhq/graft](https://github.com/trailhq/graft)).

This skill teaches AI coding agents (Gemini, Antigravity, Claude Code, Cursor, Codex) how to navigate, map, and utilize an institutional codebase knowledge graph. It transforms agents from "blind searchers" (grepping from cold) into "oriented architects" that immediately understand subsystem boundaries, dependency flows, and critical guardrails.

---

## 🏛️ Core Purpose & Architecture

In large, complex codebases (70+ modules, multi-service architectures, real-time data pipelines), agents often waste 60%–80% of their tool calls and context window searching for functions and figuring out imports.

**Graft solves this by maintaining a structured, living knowledge graph in `graft/`:**

```
<project_root>/
├── graft/
│   ├── overview.md               # High-level architecture, subsystems, visual Mermaid diagram
│   ├── modules_graph.md          # Complete catalog of all modules, classes, functions, & deps
│   ├── data_pipelines.md         # Step-by-step sequence diagrams of data & execution flows
│   └── architecture_graph.json   # Machine-readable JSON graph (nodes & edges)
```

---

## ⚡ Agent Operational Rules

When working on any repository that contains or requires a Graft knowledge graph:

### 1. The "Orient First" Rule (Check `graft/` Before Grepping)
Before executing multiple recursive search or grep commands across unknown directories:
1. **Check if `graft/overview.md` exists**: Read it first to understand the high-level architecture and locate the central hub modules.
2. **Consult `graft/modules_graph.md`**: Look up the target module's exported functions, classes, and inbound/outbound dependencies.
3. **Verify `graft/data_pipelines.md`**: Understand how data flows into and out of the module to avoid breaking downstream consumers.

### 2. The "Preserve Hub Invariants" Rule
Modules with high inbound dependency counts (e.g. `trading_desk.py`, `binance_client.py`, `htf_macro_lock.py`) are **Critical Hubs**:
- Never rename exported functions or change signature parameters without updating all inbound callers listed in `graft/modules_graph.md`.
- Never bypass pre-trade risk or safety guardrails documented in `graft/data_pipelines.md`.

### 3. The "Graph Regeneration" Rule
Whenever a major architectural change is made (adding new modules, refactoring pipelines, or modifying core schemas):
- Run the bundled Graft Engine to update the `graft/` knowledge graph:
  ```bash
  python .agents/skills/graft/scripts/graft_engine.py [project_path]
  ```

---

## 🛠️ Bundled Tools & Scripts

This skill includes a native, zero-dependency Python AST Graft Engine:

- **Location**: [`scripts/graft_engine.py`](file:///.agents/skills/graft/scripts/graft_engine.py)
- **Features**:
  - 100% Python AST parsing (requires zero external C++ compilers or node-gyp build tools).
  - Fast execution (< 1 second for 100+ files).
  - Generates human-readable Markdown docs with Mermaid diagrams and machine-readable JSON.
- **Usage**:
  ```bash
  # Generate or update knowledge graph for current repository:
  python .agents/skills/graft/scripts/graft_engine.py .
  ```

---

## 📚 Reference Documentation
- GitHub Repository: [trailhq/graft](https://github.com/trailhq/graft)
- Official Documentation: [trailhq.com/graft](https://trailhq.com/graft)

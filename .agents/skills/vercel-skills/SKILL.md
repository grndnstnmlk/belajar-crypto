---
name: vercel-skills
description: Vercel Labs Skills CLI ecosystem manager (skills.sh). Enables discovering, downloading, managing, and executing skills across 75+ AI agent environments. Use when the user wants to install new skills from GitHub repositories, search community skills, list installed skills, or run skills on demand without installation.
---

# ⚡ Vercel Labs Skills CLI (skills.sh)

`skills` is the universal package manager for the open agent skills ecosystem, supporting Antigravity, Claude Code, Cursor, Codex, and 75+ AI agents.

## 🚀 Key Commands

### 1. Install Skills from Repositories
Install a full package or specific skills into the workspace (`.agents/skills/`):
```bash
# Install full package
npx skills add vercel-labs/agent-skills -y

# Install specific skill
npx skills add vercel-labs/agent-skills --skill frontend-design -y

# Install globally (available in all projects)
npx skills add vercel-labs/agent-skills -g -y
```

### 2. List & Search Skills
```bash
# List installed skills in the current project
npx skills list

# List globally installed skills
npx skills list -g

# Search skills interactively or by keyword
npx skills find <QUERY>
```

### 3. Zero-Install Execution (`skills use`)
Generate a skill prompt or run a skill on-demand without installing to disk:
```bash
npx skills use vercel-labs/agent-skills@web-design-guidelines
```

### 4. Update & Remove Skills
```bash
# Update installed skills to latest versions
npx skills update

# Remove a specific skill
npx skills remove <SKILL_NAME> -y
```

---
name: iris
description: Camera and visual verification skill for AI coding agents powered by Iris (brijr/iris). Produces fast, trustworthy screenshots of local web apps (localhost), public sites, and specific DOM selectors with dark mode and device presets (desktop, iphone, ipad). Includes native stdio MCP server support.
---

# Iris — A Camera for Coding Agents 📸

Powered by **Iris** ([brijr/iris](https://github.com/brijr/iris)).

This skill equips AI coding agents (Gemini, Antigravity, Claude Code, Cursor, Codex) with **visual perception** ("eyes"). Instead of guessing whether a frontend layout, CSS tweak, or dashboard card is rendered properly, Iris captures high-resolution, pixel-accurate screenshots in < 1 second.

---

## 🏛️ Core Capabilities

1. **Local & Remote Page Capture**:
   - `localhost:5000` (automatically resolves to HTTP)
   - Public URLs (`https://example.com`)
   - Local files (`file:///c:/path/to/page.html`)
2. **Responsive Device Presets**:
   - `desktop`: 1440×900 @2x
   - `laptop`: 1280×800
   - `iphone`: 390×844 @3x (mobile viewport)
   - `ipad`: 820×1180
3. **Appearance Modes**:
   - `--dark`: Force dark color scheme (essential for dark-mode trading dashboards).
   - `--full`: Full-page vertical scrolling capture.
4. **Element Framing**:
   - `--selector '#hero' --padding 24`: Tight framing around specific DOM elements.

---

## 🛠️ CLI Usage (Bundled Runner)

Run using the bundled runner in any terminal:

```bash
# Capture local trading dashboard in dark mode:
python .agents/skills/iris/scripts/iris_runner.py --dark localhost:5000 -o scratch/dashboard_desktop.png

# Capture mobile iPhone layout:
python .agents/skills/iris/scripts/iris_runner.py --size iphone localhost:5000 -o scratch/dashboard_mobile.png

# Capture with machine-readable JSON output:
python .agents/skills/iris/scripts/iris_runner.py --json localhost:5000
```

---

## 🔌 Model Context Protocol (MCP) Server

Iris includes a native stdio MCP server. When running as an MCP server, it exposes the `capture` tool to AI agents.

### MCP Configuration:

In your MCP client configuration (e.g. `mcp_config.json` or IDE settings):

```json
{
  "mcpServers": {
    "iris": {
      "command": "python",
      "args": ["C:/Users/USER/.gemini/config/skills/iris/scripts/iris_runner.py", "mcp"]
    }
  }
}
```

### The `capture` Tool Schema:

```json
{
  "url": "http://localhost:5000",
  "size": "desktop",
  "dark": true,
  "output": "scratch/preview.png"
}
```

---

## ⚡ Agent Operational Rules

1. **Verify UI Changes Visually**:
   Whenever making major CSS or HTML changes to `dashboard.html` or UI components, take an Iris screenshot of both `desktop` and `iphone` viewports to ensure zero text wrapping and strict adherence to `DESIGN.md`.
2. **Always Use Dark Mode for Belajar Kripto**:
   Use `--dark` flag because the workstation's design language is GSAP Animated Chalkboard (`#0e100f` near-black wall).
3. **Clean Output Paths**:
   Save temporary inspection screenshots in `scratch/` or `artifacts/` to keep project roots clean.

---
name: open-code-review
description: Alibaba OpenCodeReview skill for AI-powered, high-precision code reviews and deep codebase vulnerability scanning. Use when reviewing pull requests, git diffs, auditing directories or entire repositories for bugs, logic defects, security risks, or architectural antipatterns.
---

# 🛡️ Alibaba OpenCodeReview Skill

Alibaba OpenCodeReview (`ocr`) provides enterprise-grade, high-precision code review with line-level accuracy, deep contextual codebase exploration, and full-directory security scans (`ocr scan`).

## 🚀 Key Commands

### 1. Diff-Based Review
Review uncommitted working directory changes:
```bash
npx -y @alibaba-group/open-code-review review
```

Review against a specific branch, commit, or target base:
```bash
npx -y @alibaba-group/open-code-review review --target main
npx -y @alibaba-group/open-code-review review --target origin/main
```

### 2. Full Codebase / Directory Scan (No Diff Required)
Audit an entire folder or repository for bugs, logic issues, and security vulnerabilities:
```bash
npx -y @alibaba-group/open-code-review scan --path .
npx -y @alibaba-group/open-code-review scan --path .agents/tools
```

### 3. Agent Delegation Mode (Zero API Key Overhead)
Generate structured review specifications for the host agent to inspect directly:
```bash
npx -y @alibaba-group/open-code-review delegate
```

### 4. Interactive WebUI Session Viewer
Launch the local review session viewer:
```bash
npx -y @alibaba-group/open-code-review viewer
```

---

## 🎯 Review Workflow Guidelines
When performing code reviews:
1. **Precision Over Noise**: Focus on actual bugs, race conditions, memory leaks, unhandled exceptions, and security oversights.
2. **Context-Aware**: Inspect calling functions and related modules across the codebase before flagging a finding.
3. **Actionable Suggestions**: Provide exact code diffs and explanation of the fix.

# Agents Registry — Prox Offensive Multi-AI Agent Lab

This file tracks **named agents** used across Codex, Claude, Gemini, OpenCode, and other tools.

Each agent is defined with:
- **Name**
- **Owner** (Codex / Claude / Gemini / Shared)
- **Purpose**
- **Key Files / Context**
- **Notes**

---

## 1. Core Agents

### 1.1 `session-closer`

- **Owner:** Claude (personal + project)
- **Purpose:** End-of-day/session agent that:
  - Summarizes what happened.
  - Updates session summary files.
  - Syncs context files (`codex.md`, `claude.md`, `gemini.md`, `agents.md`).
  - Optionally commits changes via Git.
- **Key Files:**
  - `docs/project_brain.md`
  - `agents.md`
  - Any session summary docs (TBD).
- **Notes:**
  - Must never include secrets or flags in summaries.
  - May be reused across projects.

---

## 2. Future Project-Specific Agents (Placeholders)

### 2.1 `reconops-prox-orchestrator`

- **Owner:** Shared (Codex + Claude + GPT)
- **Purpose:** High-level orchestration for ReconOps Prox:
  - Ingest loot from the host loot directory (via shared folders).
  - Call parsers (linPEAS, Nmap, etc.).
  - Coordinate report generation (internal + public).
- **Key Files (planned):**
  - `docs/reconops_prox/*.md`
  - `docs/project_brain.md`
- **Notes:**
  - Will integrate with DonTrabajoGPT modules.

### 2.2 `brutal-critic`

- **Owner:** Claude
- **Purpose:** Harsh reviewer for scripts, docs, and content.
- **Key Files:**
  - `claude.md`
  - Any script or doc under review.
- **Notes:**
  - Designed to avoid agreeability; prioritize truth over comfort.

---

## 3. Conventions

- New agents should be added to this file with:
  - A short, clear name.
  - A one-line purpose at minimum.
- If an agent becomes obsolete, mark it as **DEPRECATED** instead of deleting it.

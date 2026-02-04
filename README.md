# Prox Offensive · AI Multi-Agent Red Team Lab

**Author:** Felix Gutierrez (aka Don Trabajo)  
**Organization:** Proxima Centauri Productions LLC · DBA Prox Offensive Information Security  

---

## Overview
This repository documents the development of a **multi-agent, local-first AI lab** built around a **security-hardened Clawdbot/OpenClaw mesh orchestrator** for red-team research, training, and creative workflow automation.

Each AI agent serves a defined role in the offensive workflow — from structured reasoning to secure, offline synthesis — combining precision, privacy, and creativity.

---

## Public Repo Standard
This repo is public and intentionally sanitized.

Published:
- methodology and architecture
- defensive artifacts (threat model, control plane, probe packs, incident response)
- sanitized demos and templates

Not published:
- credentials, tokens, or secrets
- target data, client details, or live operational state
- step-by-step offensive runbooks or exploitation instructions

---

## Core Components (Current)
Authoritative agent/tool registry (public-safe): **[AGENTS.md](./AGENTS.md)**

- **Clawdbot/OpenClaw Mesh Orchestrator (Proxima)** – security-hardened tool-using control plane; enforces OPSEC + lane discipline
- **ChatGPT-Codex (GPT‑5.2)** – primary “repo engineer” for structured logic, coding, and doc refactors
- **Claude CLI** – long-context writing, critique passes, and final narrative polish
- **Gemini CLI (optional)** – fact checks + mixed artifacts (UI/screenshots) when installed
- **Local LLMs (Ollama on Mac lane)** – OPSEC-sensitive / offline synthesis (e.g., DeepSeek, GPT‑OSS, Qwen)
- **Duck.ai reviewer loop** – contradiction hunting / second opinions before publishing
- **Atlas (safe research lane)** – redacted intake + safer browsing workflows

Lane discipline (high level): **Host = brain + archive · Kali = blade · Mac = heavy local-LLM lane**

---

## `/init` Blueprint
For detailed setup instructions, see  
➡️ **[AI_MultiAgent_RedTeam_Blueprint.md](./AI_MultiAgent_RedTeam_Blueprint.md)**

---

## Project Goals
- Strengthen red-team methodology through modular AI integration  
- Maintain local sovereignty over sensitive data and findings  
- Streamline documentation and creative publishing for security professionals  

---

For details on the host CLI & AI environment this project runs in,
see the Multi-Agent Lab docs.

For multi-agent prompt-injection / tool-abuse hardening (Arcanum taxonomy + OWASP LLM Top 10 adapted):
- `security/README.md`

See the Multi-Agent Lab docs:

`docs/host_cli_orchestration.md`

---

## Proof of Work
- `security/THREAT_MODEL.md`
- `security/CONTROL_PLANE.md`
- `security/PROBE_PACKS.md`
- `security/INCIDENT_RESPONSE.md`


## License
MIT License © 2025 Felix Gutierrez  
Part of the **Prox Offensive / Proxima Centauri Productions** initiative.

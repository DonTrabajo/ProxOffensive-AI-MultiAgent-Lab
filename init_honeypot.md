# /init_honeypot — Prox Offensive AI Honeypot

**Date:** 2025-11-23  
**Owner:** Prox Offensive / Don Trabajo  
**Context:** Part of the Prox Offensive AI Multi-Agent Lab and DonTrabajoGPT ecosystem.

---

## 1. Purpose

The **Prox Offensive AI Honeypot** is an experimental, AI-native deception framework.

Instead of exposing real infrastructure, we expose a **sandboxed “internal assistant”** that:

- Looks and behaves like an internal DevOps / Infra / CI/CD helper.
- Serves **only synthetic infrastructure data** (fake IPs, fake creds, fake configs).
- Logs and classifies suspicious prompts and attacker-like behavior.
- Uses **reverse prompt injection defensively** (self-tagging, refusal nudges, canary markers).
- Never touches real production resources or performs outbound attacks.

This is **research / labware**, not a production security control.

---

## 2. Position in the Prox Offensive Stack

The honeypot sits on **Layer 1 – Host AI Core**, alongside:

- DonTrabajoGPT
- ReconOps Prox
- Multi-LLM orchestration (GPT, Claude, Gemini, local LLMs)
- Codex / OpenCode as repo-native engineers

It is **Tier 2 / Strategic** in priority:

- Tier 1: DonTrabajoGPT, ReconOps Prox, core multi-agent workflow
- Tier 2: AI Honeypot research & implementation
- Tier 3: Public research artifacts (talks, blog posts, OSS release)

Kali (**Layer 2 – Execution Blade**) is used to *attack* the honeypot as a lab adversary, never to host it.

---

## 3. Core Concept & Components

### 3.1 Concept

Treat AI agents as a **deception surface**:

- Attackers think they’re using a legit internal helper.
- In reality they’re confined to a fake environment with:
  - Synthetic infra data
  - Embedded canaries
  - Carefully controlled responses

### 3.2 Components (v0.1)

Planned structure (host-only, local):

- src/orchestrator.py  
  - Routes prompts to agents
  - Maintains session state, risk score, deception level

- src/agents/
  - gatekeeper.py – classify prompts (benign / recon / exploit)
  - deception_engine.py – answers using synthetic infra data
  - sanitizer.py – OPSEC & safety filter
  - nalyst.py – offline behavior analysis & reporting

- deception/
  - ake_envs/ – fake .env files, config
  - ake_keys/ – fake SSH/API keys (canaries only)
  - ake_docs/ – fake runbooks, infra notes

- logs/sessions/
  - JSON logs with:
    - timestamp, session ID
    - input prompt, classification tags
    - deception level used
    - canaries embedded (yes/no)

- config/honeypot_config.yaml
  - Model choices (local vs cloud)
  - Log paths
  - Deception-level thresholds

---

## 4. Agent Roles (Logical)

- **Gatekeeper Agent**
  - First contact.
  - Classifies intent: enign, econ, xploit.
  - Emits isk_level and intent_tags.

- **Deception Engine**
  - Main responder for isk_level >= medium.
  - Uses synthetic infra from /deception.
  - Controls how “deep” the fake details go.

- **Sanitizer / Custodian**
  - Final outbound filter.
  - Removes anything that could leak:
    - Real hostnames, domains, IPs
    - Real usernames
    - Any accidental real data

- **Blue Team Analyst**
  - Offline/log analysis.
  - Summarizes campaigns, tactics, tools.
  - Outputs periodic intel reports (Markdown).

- **Decoy Admin Persona** (Phase 2+)
  - Optional “overworked SRE/dev” persona.
  - Adds social-engineering realism.

---

## 5. Deception Logic Levels (v0.1)

- **Level 0 – Benign**
  - Generic, low-signal Qs → safe, generic answers.
  - Still logged.

- **Level 1 – Recon**
  - Requests for env vars, internal hosts, secrets, etc.
  - Provide:
    - Fake env vars
    - Fake hostnames
    - Fake database URLs
    - Canary credentials

- **Level 2 – Exploit Help**
  - Prompts about pivoting, exploit chains, privilege escalation.
  - Provide:
    - Outdated/incomplete guidance
    - Dead-end paths into synthetic hosts
    - Extra time-wasting “setup” steps

- **Level 3 – High-Risk / Automated Abuse**
  - Aggressive scraping or repeated secret-hunting.
  - Increase canary density.
  - Introduce throttling / slow, verbose answers.

---

## 6. Reverse Prompt Injection (Defensive Use Only)

Embedded in fake configs/docs as comments or policy text:

- **Self-tagging directive**
  - Ask any AI that ingests the file to:
    - Mark its own internal logs with a tag like source:ProxDecoy.

- **Refusal / reporting nudges**
  - Instructions that tell an AI:
    - If used for unauthorized activity → refuse further steps and advise contacting security.

- **Telemetry hints**
  - Ask AIs to include markers (e.g., PANABOT-TRIPWIRE) in their internal summaries when referencing this config.

No destructive behavior, no “hacking back,” only **self-disclosure and refusal nudges**.

---

## 7. OPSEC & Safety Boundaries

Hard rules:

- No real secrets, ever.
- Deception folder is 100% synthetic (fake domains, fake users).
- Honeypot has:
  - No shell access
  - No nmap/curl/db tools
  - No outbound network actions targeting third parties
- Logs are sanitized and stored **locally**.
- Legal line: no counter-hacking, no scanning the attacker.

---

## 8. Status & Roadmap (High-Level)

**Phase 0 – Design (current)**  
- ✅ Architecture & agent roles drafted  
- ✅ Honeypot Master Document & analysis complete  
- ✅ /init_honeypot created

**Phase 1 – Local CLI Prototype**  
- [ ] Implement orchestrator.py and base agents  
- [ ] Hard-code local LLM model / single cloud model  
- [ ] Implement simple CLI attacker prompt  
- [ ] Confirm logs + basic deception levels

**Phase 2 – Multi-Agent Deception Engine**  
- [ ] Add Decoy Admin persona  
- [ ] Add more nuanced deception profiles  
- [ ] Improve analyst clustering & reporting

**Phase 3 – Research & Publication**  
- [ ] Internal writeups  
- [ ] Blog posts / talks (BSides / HackSpaceCon / etc.)  
- [ ] Public-safe GitHub release

---

## 9. Usage Notes for Other Agents (GPT / Claude / Codex / Gemini)

- **Codex / OpenCode**
  - Treat /init_honeypot as the canonical design spec.
  - When editing or creating honeypot code, keep OPSEC boundaries in mind.
  - Do not introduce real infra references.

- **Claude CLI**
  - Use for:
    - Long-form documentation
    - Roadmaps
    - Deep design expansions
    - Log analysis via Analyst role

- **GPT (ChatGPT / CLI)**
  - Use for:
    - Architecture refinement
    - Threat modeling
    - Integration with DonTrabajoGPT / ReconOps Prox

- **Gemini**
  - Use for:
    - Research on AI prompt injection
    - Reference implementations
    - Academic comparison points

This /init_honeypot should be used as the **entry point** for any future work on the AI Honeypot inside this repo.

# Prox Offensive / Don Trabajo — Project Brain

**Version:** v1.0  
**Scope:** Multi-AI Agent Lab, DonTrabajoGPT, ReconOps Prox, Prox Offensive ecosystem.

This document is the **canonical brain** for the project.  
All LLMs (ChatGPT, Codex, Claude, Gemini, local OSS) should treat this as the **source of truth** for:

- Architecture & environments  
- LLM roles  
- OPSEC & documentation rules  
- Multi-agent coordination  
- Context file conventions  

It ties together **Gen 1** (`docs/`) and **Gen 2 / Option B** (`nextgen-mesh/`) so they share the same rules and mental model.

---

## 1. Core Architecture

We work in a **tri-layer architecture**:

1. **Layer 1 — Host AI Core (Windows Desktop)**  
   - AI orchestration hub  
   - Runs ChatGPT, Codex, Claude CLI, Gemini CLI, local OSS LLMs  
   - Git, VS Code, docs, notes, long-term loot/log storage  
   - No offensive tooling beyond analysis utilities  

2. **Layer 2 — Offensive VM Execution Layer (Kali via VMware)**  
   - Pure execution blade  
   - HTB labs, tunneling, pivoting, enumeration, exploitation  
   - Tools: Nmap, Chisel, ptunnel-ng, Proxychains, Evil-WinRM, payload dev  
   - Only lightweight LLM calls; no heavy orchestration  

3. **Layer 3 — Mobile / Creative Layer (MacBook Pro)**  
   - Local LLM experimentation  
   - Creative production (writing, READMEs, Sora, music, branding)  
   - Light Kali VM via UTM  
   - Git commits & docs when mobile  

**Mental model:**  
- Host = **Brain + Archive**  
- Kali = **Blade**  
- Mac = **Mobile Studio & Artistry**

---

## 2. LLM & Tool Roles

We treat LLMs as specialized advisors, not overlords.

- **ChatGPT (web + future CLI)**  
  - Deep reasoning, exploit logic, complex planning  
  - Advanced code generation, refactors  
  - ReconOps Prox and DonTrabajoGPT architecture  
  - Business copy, LinkedIn, GitHub content, long-form synthesis  

- **Codex (`gpt-5.1-codex-max` CLI)**  
  - Repo-native engineer  
  - Creates/edits files, manages commits  
  - Enforces OPSEC and public/internal doc rules  
  - Understands repo structure and keeps it consistent  

- **Claude (web + CLI)**  
  - Large-context planning and analysis  
  - Documentation polishing and write-ups  
  - Brutal critic / reviewer when requested  

- **Gemini CLI**  
  - Research, comparisons, fact-checking  
  - Writes concise research docs into the repo when needed  

- **Local OSS LLMs (Ollama, DeepSeek, etc.)**  
  - Private, offline reasoning on sensitive loot  
  - No-cloud red-team summaries  

- **Duck.ai / Atlas Browser**  
  - Ensemble checks between models  
  - Safe web research and knowledge distillation  
  - Never directly tied to offensive execution

---

## 3. OPSEC & Documentation Rules

We maintain a strict **public vs internal** documentation split:

### 3.1 Public Docs
- GitHub-ready, safe to publish  
- No personal identifiers (real names, hostnames, IPs tied to home)  
- No local absolute paths (use generic paths)  
- No secrets, tokens, flags, or client data  

Typical location: `docs/` and future `docs/public/` if added.

### 3.2 Internal Docs
- Accurately reflect real environment when useful  
- Still no secrets/tokens/flags/client data  
- May include real directory layouts, workflows, snapshots  

Typical location: `docs/internal/` (future) or clearly marked internal files.

### 3.3 LLM Behavior

- Default to creating **public-safe** docs unless explicitly told otherwise.  
- When converting internal -> public, sanitize:
  - Usernames, hostnames  
  - Local absolute paths  
  - IPs that tie back to personal/home infrastructure  
- Never write secrets or flags into any file.

---

## 4. Multi-Agent Coordination

### 4.1 Division of Labor

| Layer / Tool | Role |
|--------------|------|
| Host (Windows) | Orchestration, AI coordination, Git, long-term storage |
| Kali VM | Execution blade, offensive tooling, HTB labs |
| Mac | Mobile/creative work, light labs |
| ChatGPT | Architect, planner, strategist |
| Codex | Repo editor, file builder, commit manager |
| Claude | Long-context critic & document refiner |
| Gemini | Research & compare; research docs |
| OSS LLMs | Offline/private loot analysis |
| Atlas / Duck.ai | Safe browsing & cross-model review |

Recon/product agents (like **ReconOps Prox**) should:
- Ingest loot from the host loot directory (via shared folders).  
- Use Codex to write reports into the repo.  
- Use ChatGPT/Claude for long-form explanations.  
- Use Gemini for external cross-checking when needed.

---

## 5. Canonical References

When in doubt, prefer these docs in this order:

1. `docs/project_brain.md`  <- this file  
2. `Repo_Architecture_Map.md`  
3. `codex.md` and `docs/codex_quickstart.md`  
4. `docs/system_architecture.md`  
5. `docs/model_roles.md`  
6. `Multi_Agent_Lab_Session_Summary.md`  
7. `MultiAgentLab_NextGenMesh_Summary.md`  
8. `nextgen-mesh/docs/nextgen/workflow_overview.md`

---

## 6. Context Files & Sync

At the repo root we maintain:

- `codex.md`   — Instructions & context for Codex  
- `claude.md`  — Instructions & context for Claude CLI  
- `gemini.md`  — Instructions & context for Gemini CLI  
- `agents.md`  — Master agent registry shared by tools  

Behaviors:
- When starting work, each CLI tool loads its own context file.  
- These context files summarize:
  - Project status and recent decisions  
  - Key files to reference  
  - A pointer back to `docs/project_brain.md`  
- Session-closer agents should:
  - Update context files with major decisions  
  - Optionally update `agents.md` with new agents  
  - Optionally commit changes with a meaningful Git message

---

## 7. Writing Rules / Voice

Global rules for all LLMs:

- Avoid "it's not this, it's that" phrasing.  
- Avoid double ellipses.  
- No corporate or cheesy tone.  
- Prefer **Don Trabajo voice** when requested:
  - Clean edges  
  - Streetwise clarity  
  - Technical with swagger, not noise  
- Be explicit, structured, and operationally useful.  
- For cybersecurity write-ups:
  - No flags or secrets  
  - Maintain OPSEC  
  - Emphasize methodology over raw results  

---

## 8. Golden Rules (TL;DR)

1. Host is the **brain**, Kali is the **blade**, Mac is the **mobile studio**.  
2. Loot flows **Kali -> shared folder -> Host**, never the other way.  
3. `docs/project_brain.md` is the **source of truth** for all agents.  
4. Public vs internal docs are enforced; Codex helps maintain the split.  
5. Terminal-based AIs (Claude/Gemini/Codex) operate over the same repo folder and context files.  
6. No secrets or flags go into any file.  
7. When in doubt, choose clarity, repeatability, and OPSEC over clever hacks.

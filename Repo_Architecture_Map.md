# Repo Architecture Map (Public/OPSEC-Safe)
**Project:** Prox Offensive AI Multi-Agent Lab
**Audience:** ChatGPT 5.1 (web) and other LLMs needing a quick mental model of this repo.

---

## 1) Quick Purpose
- Provide a single, shareable summary of how the repo is organized (Gen 1 + Gen 2).
- Point to the canonical docs for host CLI, init files, and the local-first mesh (Option B).
- Keep paths generic and OPSEC-safe.

---

## 2) Top-Level Layout
- `README.md` — brief landing page for the lab.
- `AI_MultiAgent_RedTeam_Blueprint.md` — early blueprint for multi-agent red/blue concepts.
- `codex.md` — house rules for Codex (repo-native assistant).
- `MultiAgentLab_NextGenMesh_Summary.md` — status of the local-first next-gen mesh (Option B).
- `docs/` — core documentation (host CLI, architecture, model roles, init anchors).
- `nextgen-mesh/` — next-gen local-first mesh subtree (Option B) with its own docs and subfolders.
- `social/` — LinkedIn draft posts (public comms).

---

## 3) Generations (Two-Track Model)
- **Gen 1 (Classic lab):** Cloud-augmented, local-aware multi-agent workflow. Core docs live in `docs/` (system architecture, host orchestration, model roles).
- **Gen 2 (Option B, local-first):** Local-first, CLI-first mesh with Slingshot + Kali separation and richer local LLM routing. Lives under `nextgen-mesh/ProxOffensive-LocalMesh/` plus `nextgen-mesh/docs/nextgen/`.

---

## 4) Core Docs (Gen 1) — `docs/`
- `README.md` and `index.md` — navigation/landing for docs.
- `system_architecture.md` — overall system view.
- `model_roles.md` — LLM role definitions and typical usage split.
- `host_cli_orchestration.md` — host-side orchestration guidance (OPSEC-safe public view).
- `host_cli_setup.md` — public-safe host CLI setup (workspace layout, prompt, shortcut, loot share).
- `codex_quickstart.md` — how to use Codex (repo-native agent) safely and effectively.
- `init/`
  - `init_host_cli.md` — /init anchor for host CLI behavior.
  - `slingshot_kali_init.md` — /init anchor for Slingshot + Kali split and rationale.

---

## 5) Next-Gen Mesh (Option B) — `nextgen-mesh/`
- `ProxOffensive-LocalMesh/` (working subtree)
  - `README.md` — describes the local-first cyber mesh concept.
  - `init.md` — /init anchor for Option B architecture.
  - `agents/` — placeholders for orchestrators (planned: `prox_mesh.py`).
  - `atlas/` — Atlas lane docs/patterns (redacted research lane).
  - `cli/` — CLI wrappers and profile snippets (planned `gpt`, `cld`, `gem`, `loc` helpers).
  - `duck/` — reviewer loop patterns (multi-model ensemble triggers).
  - `kali/` — Kali blade configuration (future).
  - `local-llm/` — local LLM cluster configs/scripts (future start/stop, defaults).
  - `slingshot/` — Slingshot integration templates and engagement layout (future).
- `docs/nextgen/`
  - `workflow_overview.md` — full Option B workflow view.
  - `local_llm_setup.md` — hardware lanes and local LLM roles/setup.
  - `cli_tools.md` — CLI-first philosophy across GPT/Claude/Gemini/local.
  - `atlas_lane.md` — Atlas as safe research lane with Gemini integration.
  - `duck_reviewer_loop.md` — reviewer ensemble patterns.

---

## 6) Social — `social/`
- `linkedin_host_cli_business.txt`, `linkedin_host_cli_personal.txt` — public-facing LinkedIn drafts about the host CLI/AI orchestration.

---

## 7) How to Use This Map with ChatGPT (Web)
- Share this file directly to give ChatGPT context on where to read/write.
- When asking for edits, specify exact paths (e.g., `docs/host_cli_setup.md` or `nextgen-mesh/ProxOffensive-LocalMesh/agents/prox_mesh.py`).
- For public vs internal splits: keep public content in `docs/` or `docs/public/` (if added later) and internal depth in `docs/internal/` (future pattern) or the next-gen subtree as appropriate.
- OPSEC guardrails: avoid real usernames/hosts/IPs/keys; favor generic paths like `C:\workspace` or `~/workspace`.

---

## 8) Near-Term Focus (from summary)
- Build `prox-mesh` CLI v0 (routing stub) under `nextgen-mesh/ProxOffensive-LocalMesh/agents/`.
- Flesh out Slingshot engagement structure under `nextgen-mesh/ProxOffensive-LocalMesh/slingshot/`.
- Add minimal local-LLM launcher scripts/configs under `nextgen-mesh/ProxOffensive-LocalMesh/local-llm/`.

---

## 9) Source of Truth Files to Consult First
- `codex.md`, `codex_quickstart.md` — how to collaborate with repo-native Codex and style/behavior rules.
- `docs/system_architecture.md` — Gen 1 architecture.
- `docs/host_cli_setup.md` and `docs/init/init_host_cli.md` — host workspace and /init anchor.
- `MultiAgentLab_NextGenMesh_Summary.md` — current next-gen mesh status and next steps.
- `nextgen-mesh/docs/nextgen/workflow_overview.md` — Option B workflow reference.

---

## 10) OPSEC Reminder
- Do not introduce secrets, real hostnames, or identifying IPs/domains.
- Prefer generic paths (`C:\workspace`, `~/workspace/repos`).
- Keep public/shared docs sanitized; deeper details belong in clearly marked internal or next-gen subtrees.

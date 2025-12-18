# Repo Refresher — As-Built Map

## Git State
- Working tree: clean before this refresher (only `prox_mesh.py` updated during this run).
- Recent history (15): d73078f Add local KB integration docs; ccea3b0 Add multi-agent workflow doc; 236db95 Add session summary for knowledge_loader audit; ccee804 Add honeypot init design doc; a172376 Add session summary for prox-mesh v1 + CLI integration; 3db8cd6 Upgrade prox-mesh to v1.0 with context injection/tool detection; c81edc6 Add prox-mesh v0 router CLI; acef941 Update repo architecture map (v2.0); aebe57f Add agents registry; ea12684 Add Gemini context guidance; 68dfa48 Add Claude context guidance; 30c8e96 Add canonical references/behavior guidance to codex; 22caf42 Add project brain + repo architecture docs; 802a759 Add next-gen local mesh progress summary; fa280da Update Codex quickstart with OPSEC-safe instructions.

## Layout Snapshot (git ls-files)
- Root files: README.md, codex.md, claude.md, gemini.md, agents.md, Repo_Architecture_Map.md, AI_MultiAgent_RedTeam_Blueprint.md, MultiAgentLab_NextGenMesh_Summary.md.
- Docs: `docs/` (host setup, orchestration, project_brain, model roles, kb integration, session_summaries/…).
- Next-gen mesh: `nextgen-mesh/ProxOffensive-LocalMesh/` (README.md, init.md, agents/prox_mesh.py, placeholders under atlas/, cli/, duck/, kali/, local-llm/, slingshot/).
- Next-gen docs: `nextgen-mesh/docs/nextgen/` (workflow_overview, cli_tools, local_llm_setup, atlas_lane, duck_reviewer_loop).
- Social: `social/linkedin_host_cli_business.txt`, `social/linkedin_host_cli_personal.txt`.

## Runnable Entrypoints (found via ripgrep for *.py/ps1/sh)
- `nextgen-mesh/ProxOffensive-LocalMesh/agents/prox_mesh.py` — argparse CLI router. Routes plan/research/edit/ask/generate to external CLIs (Claude/Codex/Gemini/local) with optional context injection. New `kb` route added here to call the Windows `kb_ask.py --raw` wrapper and JSONL-log results. Requires underlying CLIs to be on PATH; supports `--dry-run`.
- No other tracked *.py/*.ps1/*.sh files. Session docs mention a PowerShell launcher `prox-mesh.ps1`, but it is not committed.

## Mesh Harness Reality Check
- **prox_mesh.py (v1.0)** is the only executable harness. It builds combined prompts from repo context, checks tool availability, and shells out to the configured CLI per route. It is runnable now if the target CLIs exist (use `--dry-run` otherwise).
- **New KB hook:** `prox-mesh kb "<query>" [--log-path ...]` shells to `python "C:\Users\Felix\bin\kb_ask.py" --raw "<query>"`, streams stdout, and appends JSONL entries with timestamp/query/opsec_flags to `logs/kb_queries.jsonl` (overridable via `PROXMESH_KB_LOG` or `--log-path`).
- Other harness pieces (orchestrators/routers/dispatchers) are design-only in docs: `nextgen-mesh/docs/nextgen/*.md`, Repo_Architecture_Map.md, MultiAgentLab_NextGenMesh_Summary.md. No additional code for orchestration is present.
- The PowerShell smart launcher described in session_2025-11-21 is absent from the repo; only the Python core is here.

## Memory/State System
- **Implemented:** Narrative memory via docs (`docs/project_brain.md`, session_summaries/*) and the new KB JSONL log path created by the `kb` route.
- **Documented but missing code:** `knowledge_loader.py` (approved in session_2025-11-24_closer.md) is not in the repo; no task queue/state store files. `agents.md` defines a `session-closer` agent concept but no automation. `docs/kb_integration.md` defines the contract for `kb_query`/`kb_ask` and opsec_flags, but the actual wrappers live outside this repo.
- **Routing/manifest/queue:** Only discussed in architecture docs; no persisted manifests or state machines in code.

## What Runs Today (commands you can execute)
- `python nextgen-mesh/ProxOffensive-LocalMesh/agents/prox_mesh.py plan "..." --dry-run` (or other routes) — shows resolved shell command using configured CLIs.
- `python nextgen-mesh/ProxOffensive-LocalMesh/agents/prox_mesh.py kb "kerberoasting" --dry-run` — shows how the KB wrapper would be called; drop `--dry-run` to execute if `C:\Users\Felix\bin\kb_ask.py` is present.
- If your PATH already includes a `prox-mesh` launcher, the same subcommands apply; otherwise call via `python .../prox_mesh.py`.

## Design / Stub Only
- Placeholders under `nextgen-mesh/ProxOffensive-LocalMesh/atlas`, `duck`, `kali`, `local-llm`, `slingshot`, and `cli` (only `kb_ask_stub.md` text lives there).
- `knowledge_loader.py` and any orchestrator integrations referenced in session summaries are absent.
- No persisted memory/state beyond docs; no task queues, manifests, or routing daemons checked in.

## Gaps to Make the Harness Real (top 3)
- Ship the missing `knowledge_loader.py` + tests and wire it into prox-mesh or a follow-on orchestrator for KB-backed responses.
- Commit the smart PowerShell launcher (`prox-mesh.ps1`) and a small installer/readme so routes are discoverable without manual PATH edits.
- Add health checks/tests for prox-mesh (e.g., `--doctor` to verify tool availability, KB wrapper path, and log write perms) plus a minimal config file to avoid env-var drift.

## Bonus: Minimal v0 KB Harness
- Added `prox-mesh kb "<query>"` route that calls `python "C:\Users\Felix\bin\kb_ask.py" --raw "<query>"` and appends JSONL to `logs/kb_queries.jsonl` with timestamp, query, returncode, and any `opsec_flags` in the response. Override command via `PROXMESH_KB_CMD`; override log path via `PROXMESH_KB_LOG` or `--log-path`.

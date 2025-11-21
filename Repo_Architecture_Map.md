# Repo Architecture Map (Public / OPSEC-Safe)
**Project:** Prox Offensive AI Multi-Agent Lab  
**Audience:** ChatGPT 5.1, Codex, Claude, Gemini, and other LLMs needing an instant mental model of this repository.

This map defines the directory structure, generational split, documentation philosophy, and the authoritative source-of-truth files for all agents.

---

# 1) Purpose
- Provide a unified overview of the repo for both **Gen 1 (cloud-augmented)** and **Gen 2 (local-first mesh)**.
- Point LLMs and agents to the correct documents and entry points.
- Maintain OPSEC-safe navigation instructions.
- Establish where public vs internal documentation belongs.

---

# 2) Top-Level Layout

```
ProxOffensive-AI-MultiAgent-Lab/
│
├── README.md
├── AI_MultiAgent_RedTeam_Blueprint.md
├── MultiAgentLab_NextGenMesh_Summary.md
│
├── codex.md
├── claude.md
├── gemini.md
├── agents.md
│
├── docs/
│   ├── README.md / index.md
│   ├── project_brain.md
│   ├── system_architecture.md
│   ├── model_roles.md
│   ├── host_cli_setup.md
│   ├── host_cli_orchestration.md
│   ├── codex_quickstart.md
│   └── init/
│       ├── init_host_cli.md
│       └── slingshot_kali_init.md
│
├── nextgen-mesh/
│   ├── ProxOffensive-LocalMesh/
│   │   ├── README.md
│   │   ├── init.md
│   │   ├── agents/
│   │   ├── atlas/
│   │   ├── cli/
│   │   ├── duck/
│   │   ├── kali/
│   │   ├── local-llm/
│   │   └── slingshot/
│   │
│   └── docs/nextgen/
│       ├── workflow_overview.md
│       ├── local_llm_setup.md
│       ├── cli_tools.md
│       ├── atlas_lane.md
│       └── duck_reviewer_loop.md
│
└── social/
    ├── linkedin_host_cli_business.txt
    └── linkedin_host_cli_personal.txt
```

---

# 3) Generations (Two-Track Model)

### **Gen 1 — Classic Lab (Cloud-Augmented)**
- Lives under `docs/`
- Uses ChatGPT web, Claude web, Gemini web
- Host = brain  
- Kali = blade  
- Mac = mobile  
- Documentation-first, cloud-aware, operator-driven

### **Gen 2 — Local-First Mesh (Option B)**
- Lives under `nextgen-mesh/`
- CLI-first workflow (Claude CLI, Gemini CLI, Codex, OpenCode, local models)
- Slingshot + Kali separation
- Local LLM clusters + routing lanes
- Multi-agent mesh structure (prox_mesh orchestrator)

Both generations share the same **canonical brain**:
`docs/project_brain.md`.

---

# 4) Core Docs (Gen 1) — `docs/`

- **project_brain.md** ← *Source of Truth for everything*
- system_architecture.md
- model_roles.md
- host_cli_setup.md
- host_cli_orchestration.md
- codex_quickstart.md  
- `/init` directory for persistent initialization anchors

These are **public-safe**, with internal-depth versions planned for `/docs/internal/`.

---

# 5) Next-Gen Mesh (Gen 2 / Option B) — `nextgen-mesh/`

This subtree defines the **local-first operational mesh**, including:

- Local model routing  
- Terminal-first AI workflows  
- Slingshot engagement folder structure  
- CLI helpers (`gpt`, `cld`, `gem`, `loc`)  
- Reviewer loops (duck)  
- Atlas lane separation  
- Local-LLM cluster configuration

---

# 6) Social (`/social/`)
Public LinkedIn-style posts about:
- Host CLI optimization  
- AI stack workflows  
- Productivity & tooling  

Safe for public communication.

---

# 7) How to Use This Map with ChatGPT or Codex

### When editing files:
Specify exact paths.

### When generating new docs:
- Put **public-safe** docs into `docs/`
- Put **internal-depth** docs into `docs/internal/`
- Put **Option B** docs into `nextgen-mesh/docs/nextgen/`

### When using agents:
- Codex reads `codex.md`
- Claude reads `claude.md`
- Gemini reads `gemini.md`
- All agents read `docs/project_brain.md`

---

# 8) Near-Term Focus

- Build the **prox-mesh CLI v0**
- Flesh out **Slingshot engagement structure**
- Add local LLM launcher scripts
- Integrate **ReconOps Prox** as first agent

---

# 9) Source of Truth Files

1. `docs/project_brain.md`
2. `codex.md`, `claude.md`, `gemini.md`, `agents.md`
3. `Repo_Architecture_Map.md`
4. `docs/system_architecture.md`
5. `docs/model_roles.md`
6. `docs/init/init_host_cli.md`, `slingshot_kali_init.md`
7. `Multi_Agent_Lab_Session_Summary.md`
8. `MultiAgentLab_NextGenMesh_Summary.md`
9. `nextgen-mesh/docs/nextgen/workflow_overview.md`

---

# 10) OPSEC Reminder

- No secrets, keys, flags, or identifying data.
- Avoid home IPs, usernames, hostnames.
- Prefer generic paths.
- Public docs go in `docs/`.
- Internal depth in `docs/internal/` or next-gen subtree.

---

# End of Repo Architecture Map (v2.0)

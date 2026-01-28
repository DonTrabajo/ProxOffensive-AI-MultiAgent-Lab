# Agents Registry (Repo-Local)

**Purpose:** a single, OPSEC-safe registry that defines the agents/tools in the Prox Offensive mesh.

- This file is designed to be useful to *humans* **and** parseable by tools.
- Keep it **public-safe**: no secrets/tokens, no client identifiers, no home/public IPs.
- Prefer **invocation patterns** (commands/aliases) + **lanes** + **when to use**.

---

## 0) Global Rules (applies to every agent)

- **No secrets**: never store API keys, auth tokens, passwords, flags.
- **Public vs internal**:
  - Public-safe docs live in `docs/`.
  - If you need deeper environment detail, create `docs/internal/` (still no secrets).
- **Lane discipline** (from `docs/project_brain.md`):
  - Host = brain + archive
  - Kali = blade
  - Mac = mobile studio + heavy local LLM lane
- **Default prompt routing**:
  - OPSEC-sensitive synthesis → local models
  - Strict logic/coding/debugging → GPT/Codex
  - Long-form shaping/polish → Claude
  - Fact checks / mixed artifacts (screenshots, dashboards) → Gemini
  - Second opinions → Duck.ai reviewer loop

---

## 1) Human-Readable Agent Cards

### 1.1 Proxima (Clawdbot Agent)
- **Type:** Orchestrator harness (tool-using agent), not an LLM
- **Lane:** Host control-plane (can reach Mac/Kali via SSH/tunnels when configured)
- **Primary jobs:**
  - Run checks (connectivity, repo scans)
  - Read/write files and keep repo clean
  - Trigger other agents/tools (via CLIs, SSH, HTTP endpoints)
  - Keep OPSEC rules enforced
  - Maintain session summaries / update registry/docs
- **Current backing model (example):** `openai-codex/gpt-5.2` (varies by runtime)

### 1.2 Codex (Repo Engineer)
- **Lane:** Host (Brain)
- **Invoke:** `codex` (CLI)
- **Use when:**
  - editing files in this repo
  - refactors, code changes, structured doc updates
  - creating public/internal doc splits
  - preparing commits
- **Avoid when:**
  - you need narrative polish (use Claude)
  - you need external research grounding (use Gemini)

### 1.3 Claude (Long-Form Writer / Critic)
- **Lane:** Host (Brain)
- **Invoke:** `claude` (CLI)
- **Use when:**
  - long-context reading + synthesis
  - report drafting + document shaping
  - “brutal critic” review passes

### 1.4 Gemini (Research / Mixed-Artifact Specialist)
- **Lane:** Host (Brain) + Atlas lane
- **Invoke:** `gemini` (CLI) *(optional; not currently installed on Host)*
- **Use when:**
  - quick fact checks and comparisons
  - screenshot/UI/dashboard interpretation
  - grounding claims before publishing

### 1.5 Local LLMs (Private Synthesis)
- **Lane:** Mac heavy lane and/or Host light lane
- **Common runtime:** Ollama (HTTP API on `:11434`)
- **Use when:**
  - OPSEC-sensitive loot analysis
  - offline synthesis
  - fast iteration without cloud

### 1.6 Duck.ai (Reviewer Council)
- **Lane:** Duck reviewer loop
- **Invoke:** browser workflow (tabs) or documented loop in `nextgen-mesh/docs/nextgen/duck_reviewer_loop.md`
- **Use when:**
  - you want contradictions surfaced
  - you’re about to ship a report / make a big change

### 1.7 Atlas (Safe Research Lane)
- **Lane:** Atlas (redacted intake)
- **Use when:**
  - gathering info safely, then exporting/redacting before synthesis

### 1.8 Kali VM (Execution Blade)
- **Lane:** Kali
- **Use when:**
  - enumeration/exploitation/pivoting/tunneling
  - capturing loot/logs for later analysis
- **Rule:** loot flows **Kali → shared folder → Host**

---

## 2) Machine-Readable Registry (YAML)

> Tools may parse everything between `BEGIN_REGISTRY_YAML` and `END_REGISTRY_YAML`.

```yaml
BEGIN_REGISTRY_YAML
version: 1
last_updated: "YYYY-MM-DD"

lanes:
  host:
    purpose: "AI orchestration, repos, docs, analysis"
  kali:
    purpose: "offensive execution blade"
  mac:
    purpose: "mobile studio + heavy local LLM lane"
  atlas:
    purpose: "safe research + redacted intake"
  duck:
    purpose: "multi-model reviewer loop"

agents:
  - id: proxima
    name: "Proxima"
    kind: "orchestrator"
    lane: host
    description: "Clawdbot tool-using agent; routes work to other tools; maintains repo + OPSEC."
    backing_model:
      default: "openai-codex/gpt-5.2"   # example; may change
    capabilities:
      - file_read_write
      - command_exec
      - ssh_remote_exec
      - scheduling_heartbeat
    inputs:
      - type: "chat"
      - type: "repo_files"
    outputs:
      - type: "repo_edits"
      - type: "reports"

  - id: codex
    name: "Codex"
    kind: "cli_llm"
    lane: host
    invoke:
      command: "codex"
    context_files:
      - "codex.md"
      - "docs/project_brain.md"
    best_for:
      - "repo edits"
      - "refactors"
      - "OPSEC-safe doc splits"
      - "git commits"

  - id: claude
    name: "Claude"
    kind: "cli_llm"
    lane: host
    invoke:
      command: "claude"
    context_files:
      - "claude.md"
      - "docs/project_brain.md"
    best_for:
      - "long-form writing"
      - "planning + critique"
      - "polish + structure"

  - id: gemini
    name: "Gemini"
    kind: "cli_llm"
    lane: host
    optional: true
    invoke:
      command: "gemini"   # optional; not currently installed on Host
    context_files:
      - "gemini.md"
      - "docs/project_brain.md"
    best_for:
      - "research + comparisons"
      - "fact grounding"
      - "mixed artifacts (screenshots/UI)"

  - id: ollama_mac
    name: "Ollama (MacBook)"
    kind: "local_llm_runtime"
    lane: mac
    invoke:
      ssh_host: "<mac-tailscale-ip-or-hostname>"
      binary_path: "/Applications/Ollama.app/Contents/Resources/ollama"
      examples:
        - "/Applications/Ollama.app/Contents/Resources/ollama list"
        - "/Applications/Ollama.app/Contents/Resources/ollama run deepseek-r1:14b \"hello\""
    endpoint:
      http_base: "http://<mac-tailscale-ip-or-hostname>:11434"
    models:
      - "deepseek-r1:14b"
      - "deepseek-r1:32b"
      - "gpt-oss:20b"
      - "qwen3:30b-a3b"
      - "bge-m3"
      - "nomic-embed-text"

  - id: duck_ai
    name: "Duck.ai"
    kind: "browser_ensemble"
    lane: duck
    invoke:
      method: "browser"
    docs:
      - "nextgen-mesh/docs/nextgen/duck_reviewer_loop.md"

  - id: atlas
    name: "Atlas"
    kind: "browser_lane"
    lane: atlas
    invoke:
      method: "browser"
    docs:
      - "nextgen-mesh/docs/nextgen/atlas_lane.md"

  - id: kali
    name: "Kali VM"
    kind: "execution_environment"
    lane: kali
    notes:
      - "Use for enumeration/exploitation/pivoting"
      - "Export loot to shared folder; analyze on host"

routes:
  # Default routing policy (aligns with next-gen mesh docs)
  plan: { agent: claude }
  research: { agent: claude }
  edit: { agent: codex }
  ask: { agent: claude }
  generate: { agent: codex }
  sensitive_synthesis: { agent: ollama_mac }

  fallback_policy:
    default_agent: codex
    fallbacks:
      - when: opsec_sensitive_or_local_only
        agent: ollama_mac
        model_preference: ["qwen3:30b-a3b", "deepseek-r1:14b", "gpt-oss:20b"]
      - when: longform_polish_or_critique
        agent: claude
      - when: research_or_mixed_artifacts
        agent: gemini
        optional: true

END_REGISTRY_YAML
```

---

## 3) Notes / TODOs

- Fill `last_updated`.
- Replace placeholders like `<mac-tailscale-ip-or-hostname>` with **non-identifying** values in public copies.
- Consider adding a `docs/internal/agents.private.md` if you want real hostnames/paths (still no secrets).


## 4) Default Model + Fallback Ladder (Operational)

**Default (Proxima / Clawdbot):** `openai-codex/gpt-5.2`

**Fallback ladder (in order):**
1) **Local (MacBook / Ollama)** — use when OPSEC-sensitive, KB/books/loot, or cloud budget is tight.
   - **Preferred local default:** `qwen3:30b-a3b` (strong generalist; good reasoning + writing)
   - **Reasoning specialist (when you want chain-of-thought style reasoning):** `deepseek-r1:14b` *(can be verbose / “thinking” heavy)*
   - **Generalist alt:** `gpt-oss:20b`
2) **Claude CLI (Pro)** — long-form structure, narrative clarity, critique passes; treat as a precision tool due to daily limits.
3) **Gemini CLI (optional)** — fact-grounding + mixed artifacts (screenshots/UI) when installed.

**Failure-mode routing:**
- If Codex is rate-limited / budget tight → shift bulk synthesis to **local**, keep Codex for final repo edits.
- If Claude daily cap hit → use **Codex + local** (Codex for structure, local for bulk).
- If content is `LOCAL_ONLY` (copyrighted books / raw loot) → **local-only**; export cloud-safe briefs via KB tooling if needed.

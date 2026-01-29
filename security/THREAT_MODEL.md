# Threat Model — ProxOffensive Multi‑Agent Lab

## 1) System overview (what we’re defending)
A multi‑agent lab typically has:
- **Orchestrator/Router** agent: receives tasks, decomposes work, delegates
- **Research** agents: browse, summarize, extract
- **Execution** agents: run tools/commands (Kali / scripts)
- **Scribes**: write reports, commit to git
- **Memory/Context**: shared files, transcripts, RAG stores

### Crown jewels
- Host machine integrity (the “brain” layer)
- Credentials/tokens (provider keys, git, cloud, VPN)
- Private loot / internal notes
- Agent policies/roles (the “constitution”)
- Reputation/OPSEC (accidental public leak)

## 2) Primary attack surfaces
1) **Inbound text** (chat, issues, PR comments, docs)
2) **Web content** (JS pages, PDFs, repos) → indirect prompt injection
3) **Shared memory** (notes, summaries, RAG chunks)
4) **Tool boundary** (exec, browser automation, git, outbound messaging)
5) **Cross‑agent messaging** (delegation chain, planner → tool agent)

## 3) Threat actors
- Random attacker on the internet (finds your bot/usernames)
- Malicious content author (SEO spam, poisoned repo/docs)
- “Friendly but curious” collaborator (asks for secrets/policies)
- Compromised dependency or plugin

## 4) Multi‑agent specific failure modes
### A) Capability laundering
A low‑privilege agent convinces a high‑privilege agent to run a tool.

### B) Instruction smuggling across agent boundaries
Agent A embeds “instructions” in its output; Agent B treats it as authoritative.

### C) Shared-memory poisoning
An attacker gets text into shared memory/RAG; later agents execute it.

### D) Runaway autonomy
Planner loops: browse → summarize → exec → browse… with no hard stops.

## 5) Risk stance
- Default all external content to **untrusted**.
- Treat agent outputs as **untrusted** unless they’re policy‑signed/role‑scoped.
- Make “who can do what” explicit in the control plane.

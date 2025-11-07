# AI-Augmented Red Team Lab — `/init` Blueprint

**Author:** Felix Gutierrez (aka Don Trabajo) · Prox Offensive  
**Goal:** Run a local-first, multi-agent workflow for offensive-security research and clean write-ups.

---

## Why this exists
Automation is easy. Integration is the real work.  
I wired the lab so each model has a job and earns its keep. Private when it should be, fast when it can be.

---

## Hardware lanes
- **Windows desktop (Ryzen 7, 16 GB, GTX 1660)** — main workspace: ChatGPT Plus (web), Claude/Gemini CLIs, Kali VM for HTB.  
- **MacBook Pro (M4 Pro, 24 GB)** — runs one local 20B model (quantized) as an HTTP server.  
- **i5 box (12 GB, RX580)** — background tasks: logs, small 7B, utility jobs.

---

## Agent mesh (roles, not buzzwords)
- **ChatGPT Plus (GPT-4 Turbo)** — structure and planning in the browser.
- **Claude Pro CLI** — long-context notes and report drafts.
- **Gemini CLI** — quick cross-checks and lookups.
- **Local LLMs (gpt-oss 20B, DeepSeek)** — private synthesis on the Mac.
- **Duck.ai** — browser reviewers (gpt-oss-120B & friends) for second opinions.
- **Atlas Browser (Mac)** — safe research + redacted drafting. Never touch live targets here.

---

## `/init` quickstart

### 1) Windows host
```bash
# Gemini CLI / Claude CLI / OpenAI CLI (examples)
# install per vendor docs, then export API keys
setx OPENAI_API_KEY "sk-…"
setx CLAUDE_API_KEY "ak-…"
```

### 2) Mac local model server
```bash
# example with Ollama or llama.cpp (pick your toolchain)
# Serve a quantized 20B model
ollama pull gpt-oss:20b-q4
ollama serve gpt-oss:20b-q4

# test endpoint
curl http://localhost:11434/api/generate -d '{"prompt":"hello"}'
```

### 3) Kali VM (HTB work)
```bash
sudo apt update && sudo apt install -y chisel proxychains git python3-pip
# run your lab; logs into ~/htb_inlanefreight
```

### 4) Context files (repo root)
- `claude.md` — persistent notes  
- `gemini.md` — refs and quick checks  
- `duck.md` — browser reviewer outputs  
- `session-summary.md` — single source of truth  
- `agents.md` — roles + endpoints

---

## Duck.ai reviewer loop
1) Open three tabs: `gpt-oss-120b`, `Claude Haiku`, `Llama 3`.  
2) Paste **redacted** sections; ask for risks, edits, alternates.  
3) Save to `duck.md`.  
4) Merge with the **local 20B** for final synthesis.  
5) Commit.

---

## Atlas lane (safe defaults)
- Separate Mac profile. Memory off. Private windows.  
- No passwords/SSO. No browsing live targets.  
- All outputs → `atlas-drafts.md` → merge offline with local 20B.

---

## One-paragraph rhythm
Build, break, document, refine. The machines keep tempo; the human sets the song.  
When it’s clean, push the notes. When it’s sensitive, keep it local.

---

## /init checklist
- [x] Keys and env vars set  
- [x] Local 20B server up on Mac  
- [x] Kali ready with tools  
- [x] Reviewers open (Duck.ai)  
- [x] Atlas drafts redacted  
- [x] `session-summary.md` updated  
- [x] Commit + push

---

### License
MIT

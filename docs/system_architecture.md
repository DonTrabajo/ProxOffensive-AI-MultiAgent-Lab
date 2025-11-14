# Prox Offensive · AI-Augmented Lab System Architecture

**Author:** Felix Gutierrez (aka Don Trabajo)  
**Scope:** High-level architecture for a multi-machine, multi-LLM offensive-security lab.

---

## 1. Overview

The Prox Offensive lab is not a single box or a single model.  
It is a **3-layer system**:

1. **Host AI Core** – Stable orchestration, browsers, CLIs, and local LLMs  
2. **Offensive VM Execution Layer** – Kali attack box for HTB and real-world tradecraft  
3. **Mobile / Creative Layer** – MacBook Pro for documentation, experiments, and on-the-go work  

Each layer has a specific role.  
LLMs, tools, and workflows are assigned to each layer **by purpose**, not by convenience.

This avoids:
- overloading Kali  
- mixing workstation duties with attack-box duties  
- scattering notes and scripts across random places  
- fragile “single-machine, single-model” setups

---

## 2. Hardware Layers

### 2.1 Host AI Core (Windows Desktop)

- **CPU:** Ryzen 7 3700X (8 cores / 16 threads)  
- **RAM:** 16 GB  
- **GPU:** GTX 1660  
- **OS:** Windows 11 Pro  
- **Primary role:** AI orchestration + stable workstation

**Responsibilities:**
- Run web UIs: ChatGPT, Claude, Gemini, Duck.ai, Atlas  
- Host local LLM servers (OpenAI OSS, DeepSeek, etc.)  
- Provide stable browsers for multi-LLM tabs  
- Store repos, docs, screenshots, notes  
- Run Git, VS Code, lightweight dev workflows  
- Manage VMware / virtualization host side

**LLM responsibility mapping:**
- GPT (web + CLI): coding, exploit logic, debugging  
- Claude (web + CLI): long-form docs, planning, refactors  
- Gemini: knowledge grounding, reference checks  
- Local models: private synthesis, sensitive reasoning  
- Duck.ai: ensemble reviewers (multi-model sanity check)  
- Atlas: safe research and drafting lane

---

### 2.2 Offensive VM Execution Layer (Kali VM)

- **Hypervisor:** VMware Workstation Player on Windows  
- **Guest:** Kali Linux Rolling  
- **Resources (recommended):**
  - **4 vCPUs** (half of physical cores)
  - **8–10 GB RAM**
  - **Expanded disk (e.g., 100 GB)**
- **Primary role:** Attack box

**Responsibilities:**
- All HTB labs and offensive training  
- Nmap, Chisel, Proxychains, ptunnel-ng, Evil-WinRM, etc.  
- Exploit delivery, enumeration, lateral movement, pivoting  
- Local scripts (DonTrabajoGPT utilities, custom tools)  
- Staging loot, logs, and lab-specific data

**LLM usage:**
- Lightweight CLI usage only when needed:
  - Claude CLI for quick code review or script explanation  
  - GPT CLI or Gemini CLI for targeted, redacted prompts  
- Heavy AI work stays on the Host AI Core to:
  - avoid resource thrash  
  - keep Kali clean and reproducible  
  - protect against breakage during upgrades

**Security/OPSEC:**
- Treat Kali as semi-disposable  
- Use snapshots before big changes  
- Keep sensitive creds, tokens, and long-term notes **off** the VM  
- Never treat Kali as a password manager or knowledge base

---

### 2.3 Mobile / Creative Layer (MacBook Pro)

- **CPU:** Apple M4 Pro  
- **RAM:** 24 GB  
- **OS:** macOS Sequoia  
- **Primary role:** Portable lab + creative + secondary AI orchestrator

**Responsibilities:**
- Local LLM experiments (Ollama, llama.cpp, etc.)  
- Secondary AI console (Atlas, Duck.ai, ChatGPT web)  
- Writing: blog posts, READMEs, HTB write-ups, architecture docs  
- Running a lightweight Kali VM (UTM) for travel or away-from-desk work  
- Git commits and repo maintenance when away from the Windows host

**LLM usage:**
- Local 20B+ models for private synthesis  
- Atlas Browser as a **redacted research lane**  
- Multi-LLM browsing (similar to host) when docked or mobile

---

## 3. CPU & RAM Strategy

### Host (Windows)
- Reserved as **AI Orchestration Core**  
- Avoid overcommitting to VMs:
  - Max **4 vCPUs** to Kali  
  - Max **8–10 GB** RAM to Kali  
- Leave headroom for:
  - browsers  
  - CLIs  
  - local LLM servers  
  - background tasks  

### Kali VM
- 4 vCPUs is the **sweet spot**:
  - enough for Nmap + Burp + terminals  
  - not so many that host performance tanks
- 8–10 GB RAM:
  - enough for multiple tools  
  - low risk of swapping to disk  
- Swap handled via **swapfile** on expanded root partition

### MacBook Pro
- Has more RAM and a modern CPU  
- Suited for:
  - local LLM servers  
  - running 1–2 small VMs  
  - creative tools (DAW, design, etc.)

---

## 4. LLM Role Assignment (System-Level)

| Layer | LLM Role |
|-------|----------|
| **Host (Windows)** | Primary orchestrator; all major SaaS LLMs + some local models |
| **Kali VM** | Minimal AI; only targeted CLI use in support of offensive ops |
| **MacBook Pro** | Private synthesis, experiments, documentation, and creative work |

---

## 5. Example Workflows

### 5.1 HTB Lab Day (Full Stack)

1. **Plan (Host)**  
   - Use GPT + Claude to outline objectives for the lab.  
   - Open Duck.ai tabs for later cross-checking.

2. **Engage (Kali VM)**  
   - Run Nmap, enumeration, initial foothold.  
   - Use tunnels/proxychains for pivoting.  
   - Keep logs in `~/htb_<lab>/logs`.

3. **Consult AI (Host + Kali)**  
   - Redact sensitive details.  
   - Ask GPT/Claude/Gemini targeted questions from host terminals/browsers.  
   - Optionally run Claude CLI inside Kali for inline script clarification.

4. **Synthesize (MacBook or Host)**  
   - Use local LLM on Mac or GPT/Claude on host to write clean notes.  
   - Summarize the attack chain, fixes, and lessons learned.  

5. **Publish (Host or Mac)**  
   - Commit/write-up to GitHub (without flags or secrets).  

---

### 5.2 Tool Development / DonTrabajoGPT Module

1. **Design (Host)**  
   - Use GPT/Claude to draft architecture.  

2. **Implement (Host)**  
   - Code in VS Code on Windows or Mac.  

3. **Test (Kali)**  
   - Run modules in real HTB-style context.  

4. **Document (Mac or Host)**  
   - Use Claude/local LLM to document usage, config, and examples.  

---

## 6. Security & Stability Principles

- Don’t promote Kali to “main workstation.”  
- Don’t promote one LLM to “do everything.”  
- Use layers: host, offensive VM, mobile/creative.  
- Use a mesh: GPT, Claude, Gemini, local LLMs, Duck.ai, Atlas.  
- Check results across models when it matters.  
- Keep sensitive data local when possible.  
- Snapshot your Kali VM after major upgrades and milestones.

---

## 7. Future Extensions

- Add a dedicated **“LLM gateway”** host or container to standardize API access.  
- Integrate ReconOps Prox and DonTrabajoGPT as first-class agents in this architecture.  
- Add monitoring/logging for AI interactions (local transcripts for research).  

---

MIT License © 2025 — Prox Offensive / Felix Gutierrez (Don Trabajo)

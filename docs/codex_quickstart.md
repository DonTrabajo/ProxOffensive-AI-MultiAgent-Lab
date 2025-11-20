# Codex Quickstart (Public / OPSEC-Safe Version)
**For the Prox Offensive AI Multi-Agent Lab**  
*How to use gpt-5.1-codex-max effectively inside this repo.*

---

## 1. Purpose

Codex is the primary **repo-native AI assistant** in the Prox Offensive Multi-Agent Lab.

It is designed for:

- Editing project files  
- Maintaining documentation  
- Creating public/internal doc splits  
- Refactoring content  
- Managing branches & commits  
- Understanding the structure of this repo  
- Supporting DonTrabajoGPT + ReconOps Prox development  

Codex runs directly inside your project folder and always loads your local `codex.md` instructions automatically.

**Think of it as:**  
- ChatGPT -> Strategic Advisor  
- Codex -> Hands-on Engineer inside the repo  

---

## 2. Launching Codex

From your host machine, navigate to the repo:

```bash
cd ~/workspace/repos/ProxOffensive-AI-MultiAgent-Lab
```

Then run:

```bash
codex
```

Codex will ask to access the directory (only once).  
Select **Yes** - this gives Codex visibility into the repo structure.

You'll now see a Codex terminal UI with:

- Loaded project instructions from `codex.md`  
- Open files  
- Repo metadata  
- Context summary  

---

## 3. Core Commands

### **Open a file**

```
open docs/host_cli_setup.md
```

### **Edit with natural language**

```
Rewrite this file with improved structure. Keep it OPSEC-safe.
```

### **Create a new file**

```
Create a new file at docs/public/host_cli_architecture.md 
with a high-level overview of the host AI role.
```

### **Search the repo**

```
Search for any identifying information in /docs.
```

### **Propose a commit**

```
Propose a git commit for all modified docs.
```

Then:

```
commit
push
```

---

## 4. Public vs Internal Docs (Codex Workflow)

Codex understands the repo's **two-tier documentation model**:

### Public docs
- Stored in `docs/public/` or `docs/`
- OPSEC-safe  
- High-level workflows, sanitized examples  

### Internal docs
- Stored in `docs/internal/`  
- More detailed  
- Must avoid secrets or IRL-sensitive data  

### Generate both versions automatically

```
Read docs/host_cli_setup.md and generate:

1. A public OPSEC-safe version in docs/public/host_cli_setup.md
2. An internal version in docs/internal/host_cli_setup.md
```

Codex will draft both, show diffs, and prepare commits.

---

## 5. Using Codex With Other Tools

The project uses a **multi-LLM orchestration model**:

- **Codex** -> Repo editor, file operations, commits  
- **Claude CLI** -> Brutal critic, long-context editor  
- **Gemini CLI** -> Research, comparison, cross-checking  
- **Local LLMs (via Ollama)** -> Offline analysis  

Workflow example:

```
Gemini -> gather info
Claude -> refine/write-up
Codex -> integrate into repo + commit
ChatGPT -> strategic design and planning
```

Codex is the **"write it to disk"** AI.

---

## 6. Common Tasks Codex Excels At

### A. OPSEC cleanup  
```
Review docs/ for real identifiers. Suggest replacements.
```

### B. Normalize documentation  
```
Normalize the tone of all host CLI docs using host_cli_orchestration_public.md as a template.
```

### C. Update architecture  
```
Update init.md to reflect current repo workflows.
```

### D. Draft new modules  
```
Create docs/public/reconops_overview.md with a high-level ReconOps Prox description.
```

### E. Summaries  
```
Summarize this Codex session and update session notes.
```

---

## 7. Best Practices

- Use **small frequent commits**.  
- Keep `/docs` as the truth source.  
- Split public/internal early.  
- Ask Codex to **scan before writing**.  
- Use second-pass refinement.  

---

## 8. Starter Prompt

```
You are Codex working inside the Prox Offensive AI Multi-Agent Lab.

Follow codex.md.  
Help maintain OPSEC-safe documentation, create public/internal splits, update /init files,  
and organize the repo structure.

Begin by scanning /docs and telling me what needs improvement.
```

---

## 9. ChatGPT vs Codex

**ChatGPT** -> design, strategy, architecture, writing  
**Codex** -> repo editing, commits, structure, sanitation  
Together they form the backbone of the **Don Trabajo Super Stack**.

---

## 10. Final Notes

Codex behaves like a **long-term repo collaborator**, using `codex.md` as its guiding brain.

It:

- Knows the lab's structure  
- Edits files safely  
- Maintains OPSEC  
- Proposes commits  
- Supports multi-agent development  

Treat it as a core tool in your Host AI layer.

# Host Machine CLI & AI Orchestration Setup

This document outlines the configuration and workflow for the Prox Offensive / Don Trabajo host machine environment. The goal is a clean, stable, AI-augmented development and analysis layer that supports Kali VM offensive operations and long-term project work.

## Overview  
The Host machine (Windows 11) serves as the brain of the Prox Offensive ecosystem:

- AI reasoning (local + optional cloud tools)
- Code development (DonTrabajoGPT, ReconOps Prox)
- Git + repo management
- Writeups, notes, and documentation
- Long-term loot storage and analysis

Kali VM acts as the execution layer (enumeration, exploitation, pivoting), with the host providing orchestration and AI assistance.

---

## Directory Structure

```
C:\Users\Felix\workspace\
    repos\          # All Git repos
    loot\           # Kali → Host loot
    notes\          # Writeups & analysis
    docs\           # Reference materials
    scripts\        # Workflow helpers
```

---

## PowerShell Profile Setup  
A custom prompt was configured to show:

- user@host  
- timestamp  
- current working directory  
- git branch (when inside a repo)

Example:

```
Felix@FULCRO [11:42] ~\workspace\repos\DonTrabajoGPT (main)
>
```

This profile loads automatically when launching the “DonT'sWorkspace” shortcut.

---

## DonT’sWorkspace Shortcut  
A Windows shortcut was created that opens PowerShell directly inside:

```
C:\Users\Felix\workspace
```

This creates a stable, frictionless launch point for all host-side operations.

---

## Git Repository Organization  
All project repositories were consolidated under:

```
C:\Users\Felix\workspace\repos
```

Repos include:

- DonTrabajoGPT  
- ReconOps Prox  
- Recon Toolkit  
- Prox Offensive site  

---

## Local AI Integration (Ollama)

Ollama was installed using:

```
winget install Ollama.Ollama
ollama run llama3.1
```

This enables:

- Offline reasoning  
- Code planning  
- Loot summarization  
- Privacy-first analysis  

No API keys are required.

---

## Python (User-Scoped Installation)

A clean user-level Python installation was configured via:

```
winget install Python.Python.3.12
```

This prevents access errors and ensures `pip install --user` works reliably.

Gemini SDK + OpenAI SDK were installed in user mode:

```
python -m pip install --user google-generativeai
python -m pip install --user openai
```

---

## Shared Loot Folder (Kali ↔ Host)

A shared folder was created on the host:

```
C:\Users\Felix\workspace\loot
```

Then mounted inside Kali using:

```
vmware-hgfsclient
sudo mkdir -p /mnt/hgfs
sudo mount -t fuse.vmhgfs-fuse .host:/ /mnt/hgfs -o allow_other
ls /mnt/hgfs/loot
```

This allows loot and logs to flow seamlessly back to the host for analysis.

---

## Host ↔ Kali Workflow Summary

1. Launch DonT’sWorkspace  
2. Use local AI to plan enumeration or exploitation  
3. Execute tasks inside Kali  
4. Export loot to `/mnt/hgfs/loot`  
5. Analyze on host using AI + scripts  
6. Write documentation + commit changes to repos  

This creates a stable, repeatable red-team cycle:

**Host (Brain) → Kali (Blade) → Host (Book + AI)**

---

## Status  
The orchestration layer is now fully operational and ready for:

- ReconOps Prox development  
- DonTrabajoGPT enhancements  
- Lab writeups  
- Red-team automation  

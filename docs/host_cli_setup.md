# Host CLI Environment Setup (Public, OPSEC-Safe Version)

## 1. Purpose of This Environment

The host operating system is the **orchestration brain** for a red-team and multi‑agent AI lab. It is responsible for:

- AI reasoning (local + cloud)
- Repo and code work (multi‑agent lab, tooling, documentation)
- Long‑term loot/log storage
- Note‑taking and reporting

The attack VM (e.g., Kali) is the **execution blade**, responsible for:

- Enumeration
- Exploitation
- Pivoting and tunneling
- Lab operations

Standard workflow:

> **Host (Brain) → Kali (Blade) → Host (Book + AI)**

This document uses **generic, non‑identifying paths** so it is safe to publish publicly.

---

## 2. Host Workspace Structure (Generic)

Base directory (example):

```text
C:\workspace\
```

Recommended structure:

```text
workspace/
    repos/      # All Git repositories
    loot/       # Shared loot folder (host <-> Kali)
    notes/      # Writeups & lab notes
    docs/       # Reference docs & /init files
    scripts/    # Automation & helper scripts
```

Guidelines:

- All coding, version control, and AI‑assisted analysis happen on the **host**.
- Loot is always returned to the **host**.
- Notes and documentation live on the **host**, not in attack environments.

---

## 3. PowerShell Profile & Custom Prompt (Generic Paths)

On modern Windows, the standard PowerShell profile path looks like:

```text
C:\Users\<USER>\Documents\PowerShell\Microsoft.PowerShell_profile.ps1
```

Use a clean, informative prompt that shows:

- `user@host`
- A timestamp
- The working directory (with `$HOME` shown as `~`)

Example:

```text
user@WORKSTATION [11:42] ~\workspace\repos\proxoffensive-ai-multiagent-lab
>
```

This gives you immediate awareness of user, host, time, and context.

---

## 4. “Workspace” Shortcut (Generic)

Create a Windows shortcut (e.g., on the Desktop or Start Menu) that:

- Launches PowerShell
- Starts in your workspace directory

Shortcut **Target** example:

```text
powershell.exe -NoLogo -NoExit -Command "Set-Location 'C:\workspace'"
```

This enforces a consistent starting point and avoids exposing your real user profile path in public docs or screenshots.

---

## 5. Local AI (Ollama) on the Host

Ollama can be used for private, offline‑friendly reasoning on the host:

```bash
ollama pull llama3.1
ollama run llama3.1
```

Common use cases:

- Pre‑lab planning (enumeration strategy, threat modeling)
- Enumeration logic and decision trees
- Post‑loot analysis and hypothesis testing
- Code architecture and refactoring ideas

Because everything runs locally, no sensitive data leaves your machine unless you explicitly send it to a cloud model.

---

## 6. Shared Loot Folder: Kali ↔ Host (Generic)

Designate a **shared loot folder** on the host:

```text
C:\workspace\loot
```

In VMware (or a similar hypervisor), configure this folder as a shared directory and mount it inside Kali, for example:

```bash
# Inside Kali
sudo mkdir -p /mnt/shared
sudo mount -t fuse.vmhgfs-fuse .host:/ /mnt/shared -o allow_other
ls /mnt/shared
```

Typical usage from Kali to Host:

```bash
./linpeas.sh > /mnt/shared/linpeas_targetA.txt
nmap -A 10.10.10.10 -oN /mnt/shared/nmap_targetA.txt
cp ~/Pictures/screenshot.png /mnt/shared/
```

Principles:

- **Never** store loot permanently in Kali.
- The host is the archive; the VM is disposable.

---

## 7. Host ↔ Kali Workflow Summary

1. Launch the **Workspace** shortcut on the host.
2. Use local or cloud AI on the host for planning.
3. Execute scans/exploits/tunnels in **Kali**.
4. Export loot to `/mnt/shared/` (host‑mapped folder).
5. Analyze loot on the **host** using AI + scripts.
6. Write notes, export docs, and update Git repos from the host.

Role mapping:

- **Host = Brain + Archive**
- **Kali = Blade**
- **Repos = Book**

---

## 8. LLM Role Assignment (Public‑Safe)

You can assign roles to different LLMs in a way that’s safe to publish:

- **GPT (web/CLI)** – deep reasoning, exploit logic, complex multi‑step planning, business copy, long‑form synthesis.
- **Claude (web/CLI)** – large‑context planning, documentation, refactors, and writeups.
- **Gemini** – technical cross‑checks, quick comparisons, and validation.
- **Local LLMs (OSS models, DeepSeek, gpt‑oss‑20b, etc.)** – private synthesis and no‑cloud summaries.
- **Duck.ai (reviewer)** – ensemble checks, multi‑view debugging, sanity checks.
- **Atlas Browser** – safe research, knowledge distillation, and “containment zone” for web context.

No machine names, usernames, or secrets need to be mentioned when describing this in public.

---

## 9. Operational Philosophy (Public)

**Tools in orbit. Precision at the core.**

- The host is the stable brain.
- The Kali VM is the isolation layer and blade.
- A laptop or secondary machine can be the mobility + creative layer.
- LLMs are advisors, not authorities.
- Important reasoning is cross‑checked across models.
- Attack environments remain isolated from creative/personal environments.
- Stability, reproducibility, and clarity trump short‑term hacks.

This version of the document is safe to link on GitHub, LinkedIn, and portfolio sites.

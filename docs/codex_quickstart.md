# codex_quickstart.md - Prox Offensive AI Multi-Agent Lab

## Purpose
Concise onboarding for working in this repo with OPSEC-safe defaults. Pairs with `codex.md` (behavioral rules) and `docs/host_cli_setup.md` (host setup).

## Audience
- Contributors using the host as the orchestration brain and Kali (or similar) as the execution blade.
- Anyone needing a public-safe, high-level setup and workflow checklist.

## TL;DR Workflow
1) Host = Brain + Archive; Kali = Blade; Repos = Book. Keep loot on host. 
2) Work out of the workspace root (example: `C:\workspace`).
3) Plan on host with local/cloud LLMs. Execute scans/exploits in Kali. Bring loot back to the host shared folder. 
4) Commit code/docs from the host. Keep OPSEC clean (no real usernames/paths/keys).

## Host Setup (Public-Safe)
- **Workspace directory**: create `C:\workspace` (or similar) with `repos/`, `loot/`, `notes/`, `docs/`, `scripts/`.
- **PowerShell profile**: use `Microsoft.PowerShell_profile.ps1` under your Documents/PowerShell path; prompt should show `user@host`, timestamp, cwd (see `docs/host_cli_setup.md`).
- **Workspace shortcut**: target `powershell.exe -NoLogo -NoExit -Command "Set-Location 'C:\workspace'"`.
- **Local AI (optional)**: `ollama pull llama3.1 && ollama run llama3.1`.
- **Python (user install)**: `winget install Python.Python.3.12` then use `python -m pip install --user <pkg>`.

## Repo Checkout
```pwsh
cd C:\workspace\repos
git clone https://github.com/DonTrabajo/ProxOffensive-AI-MultiAgent-Lab.git
cd ProxOffensive-AI-MultiAgent-Lab
```

## Shared Loot Folder (Host <-> Kali)
- Host path example: `C:\workspace\loot`
- Mount in Kali (VMware example):
```bash
sudo mkdir -p /mnt/shared
sudo mount -t fuse.vmhgfs-fuse .host:/ /mnt/shared -o allow_other
ls /mnt/shared
```
- Usage examples from Kali:
```bash
./linpeas.sh > /mnt/shared/linpeas_targetA.txt
nmap -A 10.10.10.10 -oN /mnt/shared/nmap_targetA.txt
cp ~/Pictures/screenshot.png /mnt/shared/
```
- Principles: never park loot in Kali; host is the archive.

## Daily Flow
- **Plan** on host (LLMs, notes). 
- **Run** in Kali (scans, exploits, tunnels). 
- **Return** loot to `/mnt/shared/` on host. 
- **Analyze** on host (scripts, LLM synthesis, docs). 
- **Commit** from host (docs, code, notes where appropriate).

## OPSEC Reminders
- Use generic paths/hosts in public docs: `C:\workspace`, `WORKSTATION`, `KALI-VM`.
- Do not commit secrets, tokens, passwords, or real IPs/domains.
- Split public vs internal content when needed (`docs/public/` vs `docs/internal/`).
- If unsure, sanitize and ask before publishing.

## Helpful References
- `codex.md` (behavior + writing rules)
- `docs/host_cli_setup.md` (public-safe host setup)
- `docs/init*.md` files (architecture and workflow snapshots)

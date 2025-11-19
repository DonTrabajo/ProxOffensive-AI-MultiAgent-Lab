# /init – Host CLI Environment Setup (Prox Offensive / Don Trabajo)

## 1. Purpose of This Environment
The Windows host is the **orchestration brain**, responsible for:
- AI reasoning (local LLMs)
- Repo + code work (DonTrabajoGPT, ReconOps Prox, Multi-Agent Lab)
- Documentation, notes, and writeups
- Long-term loot/log storage

Kali VM is the **execution blade**, responsible for:
- Enumeration
- Exploitation
- Pivoting and tunneling
- Lab operations

Workflow pattern:
**Host (Brain) → Kali (Blade) → Host (Book + AI)**

---

## 2. Host Workspace Structure
Base directory:

```
C:\Users\Felix\workspace\
```

Structure:

```
workspace/
    repos/      # All Git repos
    loot/       # Shared loot folder (host <-> Kali)
    notes/      # Writeups & lab notes
    docs/       # Reference docs & /init files
    scripts/    # Automation & helper scripts
```

- All coding happens on the **host**.
- Loot is always returned to the **host**.
- Notes and AI analysis happen **only on the host**.

---

## 3. PowerShell Profile & Custom Prompt
Profile located at:

```
C:\Users\Felix\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1
```

Custom prompt displays:
- `user@host`
- timestamp `[HH:mm]`
- working directory (with `$HOME` as `~`)

Example:

```
Felix@FULCRO [11:42] ~\workspace\repos\proxoffensive-ai-multiagent-lab
>
```

---

## 4. DonT’sWorkspace Shortcut
A Windows shortcut that:
- Launches PowerShell
- Starts in `C:\Users\Felix\workspace`

Shortcut target:

```
powershell.exe -NoLogo -NoExit -Command "Set-Location 'C:\Users\Felix\workspace'"
```

This enforces a consistent starting point for all host-side work.

---

## 5. Local AI (Ollama)
Ollama is used for private, offline-friendly reasoning:

```
ollama pull llama3.1
ollama run llama3.1
```

Use cases:
- Pre-lab planning
- Enumeration logic
- Post-loot analysis
- Code architecture brainstorming

No cloud keys required.

---

## 6. Shared Loot Folder: Kali ↔ Host
Host loot folder:

```
C:\Users\Felix\workspace\loot
```

Mounted inside Kali via VMware:

```bash
vmware-hgfsclient
sudo mkdir -p /mnt/hgfs
sudo mount -t fuse.vmhgfs-fuse .host:/ /mnt/hgfs -o allow_other
ls /mnt/hgfs/loot
```

Kali → Host examples:

```bash
./linpeas.sh > /mnt/hgfs/loot/linpeas.txt
nmap -A 10.10.10.10 -oN /mnt/hgfs/loot/nmap_target.txt
cp ~/Pictures/screenshot.png /mnt/hgfs/loot/
```

Never store loot permanently in Kali.

---

## 7. Host ↔ Kali Workflow Summary

1. Launch **DonT’sWorkspace**
2. Use local AI for planning
3. Execute tasks in **Kali**
4. Export loot → `/mnt/hgfs/loot`
5. Analyze on **host** using AI + scripts
6. Write notes, export docs, update repos

Roles:
- **Host = Brain + Archive**
- **Kali = Blade**
- **Repos = Book**

---

This `/init` captures the full host CLI setup workflow for this thread.  
Drop this into `docs/` in your Multi-Agent Lab repository for future reference.

# Lab Pack Quickstart (Windows -> Mac)

`prox-mesh lab-pack` sends local lab state to the Mac `kb_query.py --lab-pack` entrypoint over SSH. The Mac side already sanitizes output; Windows only renders metadata and the cloud-safe pack.

## Dry run (no log written)

```powershell
prox-mesh lab-pack "Linux privesc via SUID" --state-file .\state.md --host proxkb --dry-run
```

## Live run with a state file on disk

```powershell
prox-mesh lab-pack "Linux privesc via SUID" --state-file .\state.md --host proxkb --sources cpts --limit 10
```

## Live run piping stdin

```powershell
Get-Content -Raw .\state.md | prox-mesh lab-pack "Linux privesc via SUID" --state-file - --host proxkb --sources cpts --limit 10
```

## PowerShell piping note

Piping into `prox-mesh` relies on the updated `prox-mesh.ps1` launcher that forwards pipeline input to Python. If your launcher is older or missing, call Python directly:

```powershell
Get-Content -Raw .\state.md | python .\nextgen-mesh\ProxOffensive-LocalMesh\agents\prox_mesh.py lab-pack "Linux privesc via SUID" --state-file - --host proxkb --sources cpts --limit 10
```

Defaults:
- Logs land under `logs/lab_pack_*.json` (gitignored).
- The Windows wrapper reads a local state file (when provided) and streams it to the Mac over SSH; when `--state-file -` is used, stdin is reserved for the state payload and prox-mesh will not consume it.
- CLOUD-SAFE banners come from the Mac cloud pack; hints are metadata-only (path/line/type/abstractive hint).

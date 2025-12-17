# `prox-mesh plan-kb` quickstart

`plan-kb` generates an OPSEC-safe plan from KB *metadata only* (paths/lines/titles/tags). It never prints or logs raw snippets, even if the KB tool returns them.

## Acceptance commands

### Dry run (no subprocess calls, no logs)

From anywhere on Windows (not necessarily inside the repo):

```powershell
prox-mesh plan-kb "HTB Linux target, need initial recon + privesc path" --host proxkb --dry-run
```

Expected behavior:
- Prints the intended KB command (preview only).
- Prints the intended plan JSON output path (preview only).
- Does **not** execute the KB tool.
- Does **not** write any logs (no `logs\kb_queries.jsonl`, no `logs\plan_kb_*.json`).

### Real run (writes KB metadata + plan JSON)

```powershell
prox-mesh plan-kb "Need SUID privesc ideas for Linux box" --host proxkb --no-llm --no-snippets
```

Expected behavior:
- Prints a human-friendly plan to stdout.
- Plan references KB results by metadata only (e.g., `path:line-start-line-end`), with no snippets.
- Appends a metadata-only entry to `logs\kb_queries.jsonl` (existing behavior).
- Writes a plan JSON file to `logs\plan_kb_*.json` (gitignored).

### LOCAL_ONLY behavior (cloud_safe=false)

If the KB JSON includes `cloud_safe=false` (or `opsec_flags.cloud_safe=false`):
- Stdout includes a `LOCAL_ONLY` banner.
- Stdout includes `local_only_reason` if provided by KB.
- Plan JSON includes:
  - `plan.classification = "LOCAL_ONLY"`
  - `plan.local_only_reason` (when present)

## Output controls

- `--json`: print plan JSON only (no human-friendly output).
- `--log-path <path>`: override where the plan JSON is written (relative to repo root or absolute).
- `--kb-query "<query>"`: override deterministic v0 query extraction.


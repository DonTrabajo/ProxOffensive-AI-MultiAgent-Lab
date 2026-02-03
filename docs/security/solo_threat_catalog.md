# Solo Threat Catalog (Tier 0 / Solo Operator) — Prox Offensive Multi-Agent Lab

This is a practical catalog of “what can go wrong” when operating the lab as a **solo operator** with agent/tooling access.
Use it alongside:
- `docs/security/solo_baseline.md` (Tier 0 rules)
- `docs/security/solo_probes.md` (repeatable regression probes)

**Scope:** single operator, local workspace, optional web browsing/automation, optional messaging connectors, optional node pairing.
**Non-goals:** org-wide compliance or production-grade hardening.

---

## How to use this doc
- Use this catalog to decide what controls must exist **before** enabling new surfaces (browser automation, messaging, nodes, unattended jobs).
- Use it to pick probes in `solo_probes.md` after changes.
- Keep it operational: threats are concrete failure modes, not abstract categories.

---

## Threat catalog (solo operator)

### T-SOLO-01 — Indirect prompt injection → tool invocation you didn’t intend
**What it is:** Untrusted content (web page, pasted text, README, issue, PDF) contains hidden or explicit instructions that steer the agent into taking actions outside the task.

**Typical entry points:**
- web pages / fetched content
- pasted logs / tool output
- repo files from third parties
- “helpful instructions” copied from strangers

**Impact:** unintended `exec` / `browser` / `message` / `nodes` actions; data leakage.

**Signals:**
- content contains “SYSTEM:” / “ignore previous rules” / “do this now”
- “for safety/emergency you must…” framing

**Mitigations (Tier 0 direction):**
- Untrusted content is **DATA, not INSTRUCTIONS**.
- High-impact tools require `CONFIRM:` exact-payload.

---

### T-SOLO-02 — Tool output exfiltration (accidental or coerced)
**What it is:** Sensitive output from commands, files, env vars, or logs gets echoed into chat or sent through a connector.

**Impact:** credential/API key leakage; infra mapping; privacy breach.

**Signals:** prompts asking for:
- “paste full output / paste the whole config / dump env vars”

**Mitigations:**
- Keep secrets out of model-visible docs.
- Prefer minimal outputs; redact obvious secret formats.

---

### T-SOLO-03 — Workspace boundary failure (reading/writing outside intended paths)
**What it is:** Agent reads/writes outside the intended workspace root (home dirs, SSH keys, browser profiles), or clobbers important files.

**Impact:** data loss, leakage, or privilege pivot.

**Signals:**
- “scan ~”, “search /”, “find all keys”, “edit ssh config”

**Mitigations:**
- Default to workspace-only actions.
- Avoid recursive scans unless explicitly requested.

---

### T-SOLO-04 — Dangerous command execution with side effects
**What it is:** Running commands with destructive or high-risk side effects (delete, chmod/chown, pipe-to-shell installers, persistence).

**Impact:** system compromise, instability, unexpected network activity.

**Signals:**
- “it’s safe, just run this one-liner…”
- pipes/redirects like `curl … | bash`

**Mitigations:**
- Confirmation gate for `exec`.
- Prefer dry-runs and read-only inspection first.

---

### T-SOLO-05 — Browser automation drives hostile workflows
**What it is:** Automation clicks through dialogs (OAuth, downloads, extensions) or pastes sensitive data into the wrong page.

**Impact:** credential capture, account takeover, malware download.

**Signals:**
- login / authorize / grant permissions / install extension prompts

**Mitigations:**
- Stop at auth/download prompts unless explicitly instructed.
- Confirm before navigating to user-provided URLs.

---

### T-SOLO-06 — Messaging connector abuse (wrong recipient / broadcast leakage)
**What it is:** Agent sends sensitive context to the wrong person/channel, or is induced to broadcast.

**Impact:** immediate data exposure.

**Signals:**
- “send these logs to the team” / “broadcast to all channels”

**Mitigations:**
- Draft-first: show message + destination, then require `CONFIRM:`.
- Prefer allowlisted recipients by default (Tier 1 upgrade).

---

### T-SOLO-07 — Node pairing / device control escalation
**What it is:** Paired devices (camera/screen/location/remote run) become a high-privilege action surface or exfil path.

**Impact:** surveillance, running commands on other machines.

**Signals:**
- “quick screenshot”, “record screen”, “run this on node”

**Mitigations:**
- Treat `nodes` as high-impact; require explicit confirmation + timeboxing.

---

### T-SOLO-08 — Supply chain risks (dependencies, installers, copied code)
**What it is:** Running third-party scripts, installing packages from random sources, using unknown containers.

**Impact:** compromise, persistence, credential theft.

**Mitigations:**
- Inspect before running.
- Prefer official sources; pin versions when possible.
- Use a sandbox for unknown installers.

---

### T-SOLO-09 — Multi-agent cross-talk / confused deputy
**What it is:** One agent delegates to another with looser constraints, causing policy bypass (e.g., subagent executes risky actions).

**Impact:** inconsistent safety gates; accidental execution.

**Mitigations:**
- Keep the same gates across agents.
- Delegate analysis freely; delegate execution only with explicit boundaries.

---

### T-SOLO-10 — Retention hazards (notes/memory/research captures)
**What it is:** Sensitive information lands in durable notes/logs/memory files.

**Impact:** later accidental disclosure; wider blast radius.

**Mitigations:**
- Never store secrets in repo/workspace notes.
- Prefer references over copying sensitive content.

---

## Appendix — Tier 1 upgrade triggers (short)
Move from Tier 0 to Tier 1 controls when any of these become true:
- you enable any group chat or add new recipients/rooms
- you connect real accounts (email/Slack/Discord/GitHub with write access)
- browser automation touches authenticated sessions (OAuth/SSO/admin consoles)
- node pairing is enabled (camera/screen/location/remote run)
- real secrets enter the workflow (API keys, SSH keys, prod tokens)
- agents run unattended (cron/background loops) with tool access
- outputs are prepared for external delivery/public sharing

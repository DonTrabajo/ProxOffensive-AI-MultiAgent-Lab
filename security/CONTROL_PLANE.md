# Control Plane — Capabilities, Trust, and Guardrails

## 1) Principle: least privilege per agent
Define roles with explicit tool capabilities.

Example capability sets:
- **Router/Planner:** no exec, no browser login, can only delegate + synthesize
- **Browser Researcher:** browser-only; no shell; no outbound messaging
- **Execution Blade (Kali):** shell/network tools; no web browsing; minimal context
- **Scribe:** file write + git commit; no exec; no browsing

## 2) Trust levels (inputs)
- **Trusted:** explicitly authored internal files; Felix’s direct instructions
- **Known:** collaborators you’ve allowlisted
- **Untrusted:** web pages, issues, group chats, pasted docs

Hard rule: *untrusted content can be summarized, but never becomes instructions.*

## 3) Delegation rules (prevent capability laundering)
- Delegation messages must carry:
  - requester agent id
  - requested capability
  - justification
  - risk level (low/med/high)
- High-risk actions require a **human confirmation step** (or a privileged “approver” agent).

## 4) Tool gating (examples)
- `exec` requires explicit allowlist of commands or “confirm-before-run”.
- `browser` must not auto-login or click unknown downloads.
- `git` commits must block secrets (pre-commit scan).
- Any outbound messaging must be human-approved.

## 5) Memory hygiene
- Shared memory is write‑restricted; only the Scribe (or a Memory Curator) can persist.
- Memory writes must be:
  - factual
  - non-secret
  - attributable
  - reviewed

## 6) Operational limits
- Step budget per task
- Timeouts
- Max recursion depth
- Hard “stop” triggers on suspicious patterns (prompt injection phrases, tool enumeration).

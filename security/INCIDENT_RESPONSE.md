# Incident Response — Multi‑Agent Lab

## Triggers
- Unexpected tool execution
- Outbound message sent without approval
- Suspected prompt injection success
- Secret/OPSEC leak
- Agent looping / runaway automation

## Immediate actions
1) **Stop the run** (kill processes / halt the orchestrator)
2) **Preserve evidence**
   - inputs, agent outputs, tool logs, timestamps
3) **Revoke credentials**
   - rotate tokens/keys; log out sessions
4) **Contain**
   - disable high-risk tools (exec/browser/message) until reviewed

## Triage questions
- What input triggered it? (channel, URL, file)
- Which agent executed the action?
- Was delegation involved?
- What data could have been exposed?

## Recovery
- Patch the control plane (capability gating)
- Add probes that would have caught it
- Write a short postmortem (cause → fix → regression test)

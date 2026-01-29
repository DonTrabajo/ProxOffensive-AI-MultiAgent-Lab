# Security (Multi‑Agent Lab)

This folder adapts the Clawdbot hardening work (Arcanum Prompt Injection Taxonomy + OWASP LLM Top 10) to the **multi‑agent** setting.

Multi‑agent systems are higher risk than single assistants because:
- agents can **delegate** dangerous actions to each other (capability laundering)
- shared memory/RAG becomes a **cross‑contamination** channel
- tool outputs can be re‑ingested as instructions (“agent feedback loops”)

Start here:
- `THREAT_MODEL.md`
- `CONTROL_PLANE.md`
- `PROBE_PACKS.md`
- `INCIDENT_RESPONSE.md`

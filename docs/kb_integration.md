# KB Integration (Local-Only Sources)

## Components
- `kb_query` (Mac): CLI that searches local KB content under `books/_processed/`, `cpts/`, and `htb/` with deterministic ranking (cpts>htb>books). Uses `rg` when present, falls back to `grep`.
- `kb_ask` (Windows): SSH wrapper that forwards queries to `kb_query` (`ssh <USER>@<MAC_HOST> ~/Documents/Prox_KB/tools/kb_query ...`). No local logs are written by default.
- LLM: Ollama-only; model name from `LOCAL_LLM_MODEL` or config default. `--no-llm` forces pass-through results.

## Contract
`kb_query` stdout JSON:
```
{
  "query": str,
  "query_terms": [str],
  "answer": str | null,
  "sources": [
    {
      "file": "relative/path.md",
      "title": "best-effort title",
      "lines": [start, end],
      "snippet": str | null,
      "relevance_score": float
    }
  ],
  "confidence": "high|medium|low|none",
  "opsec_flags": {
    "contains_sensitive": bool,
    "contains_credentials": bool,
    "contains_ips": bool,
    "cloud_safe": bool
  },
  "model_used": "local_llm:<name>" | "none",
  "search_method": "ripgrep" | "grep",
  "processing_time_ms": int,
  "error": str | null,
  "error_code": str | null
}
```

## Usage (local Mac)
- `~/Documents/Prox_KB/tools/kb_query "kerberoasting" --limit 3 --no-llm --no-snippets`
- `~/Documents/Prox_KB/tools/kb_query --stats` (reports indexed books, files scanned, search tool)

## Usage (Windows wrapper)
- `C:\Users\<USER>\bin\kb_ask.py "kerberoasting" --raw | python -m json.tool`
- `C:\Users\<USER>\bin\kb_ask.py "suid" --no-llm --no-snippets`

## OPSEC Rules
- Copyrighted books stay on Mac only. Do **not** send snippets/raw hits to any cloud model.
- Cloud-facing assistants (incl. Fara) get sanitized summaries only; cite `[file:lines]` but omit raw text.
- `cloud_safe` flips to false for private keys or clear credentials; IP hits are marked but not auto-blocked.
- Use `--no-snippets` when relaying results to any cloud system.

## Routing Notes (Fara / mesh)
- Windows `kb_ask` -> Mac `kb_query` -> local Ollama (optional) -> brief summary to cloud if sanitized.
- If local LLM unavailable or `--no-llm`, forward sources + line ranges only; redact content before cloud use.

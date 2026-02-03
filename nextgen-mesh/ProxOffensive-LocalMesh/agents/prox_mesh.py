#!/usr/bin/env python3
from __future__ import annotations
"""
prox-mesh v1.0 - Prox Offensive Local Mesh Router

A CLI wrapper that routes high-level actions (plan, research, edit, ask, generate)
to underlying AI tools (Codex, Claude, Gemini, local LLMs, etc.) with:

- Route → tool mapping (env-overridable)
- Automatic detection of tool presence
- Context injection from repo root (codex.md / claude.md / gemini.md)
- Optional inclusion of docs/project_brain.md
- Dry-run mode

Usage examples:

  prox-mesh plan "Design a Slingshot + Kali engagement folder tree for an SMB client."

  prox-mesh research "Current OSCP-style pivoting techniques over SOCKS5."

  prox-mesh edit "Tighten up docs/host_cli_setup.md in Don Trabajo voice."

  prox-mesh ask "Summarize docs/project_brain.md for a new agent."

  prox-mesh generate "Draft an internal recon checklist for ReconOps Prox."

  prox-mesh kb "kerberoasting" --no-llm --no-snippets --sources all --limit 5
  # runs kb_ask.py --raw and logs JSONL
"""

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent
import re

# ---------------------------------------------------------------------------
# Paths & Repo Root Detection
# ---------------------------------------------------------------------------

THIS_FILE = Path(__file__).resolve()
# prox_mesh.py is at: repo_root/nextgen-mesh/ProxOffensive-LocalMesh/agents/prox_mesh.py
# repo_root = parent of nextgen-mesh
try:
    REPO_ROOT = THIS_FILE.parents[3]
except IndexError:
    REPO_ROOT = THIS_FILE.parents[-1]

# Context files at repo root
CONTEXT_FILES = {
    "claude": REPO_ROOT / "claude.md",
    "codex": REPO_ROOT / "codex.md",
    "gemini": REPO_ROOT / "gemini.md",
}

PROJECT_BRAIN = REPO_ROOT / "docs" / "project_brain.md"

# ---------------------------------------------------------------------------
# Route → Tool Configuration
# ---------------------------------------------------------------------------

# Default tools per route; env vars override the base command.
DEFAULT_CMDS = {
    "plan": os.getenv("PROXMESH_PLAN_CMD", "claude"),
    "research": os.getenv("PROXMESH_RESEARCH_CMD", "claude"),  # switch to 'gemini' when ready
    "edit": os.getenv("PROXMESH_EDIT_CMD", "codex"),
    "ask": os.getenv("PROXMESH_ASK_CMD", "claude"),
    "generate": os.getenv("PROXMESH_GENERATE_CMD", "codex"),
}

# Windows-side KB command (default: Python wrapper in ~/bin)
# Must be a list of argv tokens (no embedded quotes)
KB_WRAPPER_PATH = REPO_ROOT / "nextgen-mesh" / "ProxOffensive-LocalMesh" / "tools" / "kb_ask.py"
DEFAULT_KB_CMD: list[str] = ["python", str(KB_WRAPPER_PATH), "--raw"]
DEFAULT_KB_LOG = Path(
    os.getenv("PROXMESH_KB_LOG", REPO_ROOT / "logs" / "kb_queries.jsonl")
)

DEFAULT_PLAN_KB_LOG_DIR = REPO_ROOT / "logs"


def parse_kb_cmd(env_value: str | None) -> list[str]:
    """
    Parse PROXMESH_KB_CMD into a list of argv tokens.

    Supports:
      a) JSON array: ["python", "C:\\Users\\<USER>\\bin\\kb_ask.py", "--raw"]
      b) String command: python "C:\\Users\\<USER>\\bin\\kb_ask.py" --raw

    For string format, strips surrounding quotes from each token.
    Returns DEFAULT_KB_CMD if env_value is None or empty.
    """
    if not env_value:
        return DEFAULT_KB_CMD.copy()

    # Try JSON array first
    env_value = env_value.strip()
    if env_value.startswith("["):
        try:
            parsed = json.loads(env_value)
            if isinstance(parsed, list) and all(isinstance(t, str) for t in parsed):
                return parsed
        except json.JSONDecodeError:
            pass

    # Fall back to shlex parsing (posix=False for Windows)
    tokens = shlex.split(env_value, posix=False)
    # Strip surrounding quotes from each token
    clean_tokens = []
    for tok in tokens:
        if len(tok) >= 2 and tok.startswith('"') and tok.endswith('"'):
            tok = tok[1:-1]
        clean_tokens.append(tok)
    return clean_tokens


def get_kb_cmd() -> list[str]:
    """Get the KB command as a list of argv tokens."""
    return parse_kb_cmd(os.getenv("PROXMESH_KB_CMD"))


# Which context file to use per route (by tool name key above)
ROUTE_CONTEXT_TOOL = {
    "plan": "claude",
    "research": "claude",   # later: "gemini"
    "edit": "codex",
    "ask": "claude",
    "generate": "codex",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_file_if_exists(path: Path) -> str:
    try:
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
    except OSError:
        pass
    return ""


def read_prompt(args: argparse.Namespace, *, allow_stdin: bool = True) -> str:
    """
    Determine the prompt text from:
    - --file
    - positional args
    - stdin (if not a TTY)
    """
    # 1) Prompt from file
    if args.file:
        try:
            content = Path(args.file).read_text(encoding="utf-8").strip()
            if content:
                return content
        except OSError as e:
            print(f"[prox-mesh] Error reading file {args.file}: {e}", file=sys.stderr)
            sys.exit(1)

    # 2) Prompt from positional arguments
    if args.prompt:
        content = " ".join(args.prompt).strip()
        if content:
            return content

    # 3) Prompt from stdin (if piped)
    if allow_stdin and not sys.stdin.isatty():
        content = sys.stdin.read().strip()
        if content:
            return content

    print(
        "[prox-mesh] No prompt provided. Use positional text, --file, or pipe content via stdin.",
        file=sys.stderr,
    )
    sys.exit(1)


_PATH_REDACTIONS = [
    r"[A-Za-z]:\\\\[^\\s\"']+",
    r"[A-Za-z]:/[^\\s\"']+",
    r"/Users/[^\\s\"']+",
    r"/home/[^\\s\"']+",
]


def _redact_paths(text: str | None) -> str | None:
    if not text:
        return text
    redacted = text
    for pat in _PATH_REDACTIONS:
        redacted = re.sub(pat, "[REDACTED-PATH]", redacted)
    return redacted


def build_combined_prompt(route: str, base_tool: str, user_prompt: str,
                          include_context: bool, include_brain: bool,
                          extra_context_file: str | None) -> str:
    """
    Build the combined prompt with:
    - tool-specific context (claude.md, codex.md, gemini.md)
    - optional project brain
    - optional extra context file
    - user prompt
    """
    parts = []

    parts.append(
        "You are operating inside the Prox Offensive AI Multi-Agent Lab "
        "and the ProxOffensive-AI-MultiAgent-Lab Git repository."
    )

    parts.append(f"This request is routed via prox-mesh v1.0 on route '{route}' using tool '{base_tool}'.")

    if include_context:
        ctx_tool = ROUTE_CONTEXT_TOOL.get(route)
        if ctx_tool:
            ctx_path = CONTEXT_FILES.get(ctx_tool)
            ctx_text = read_file_if_exists(ctx_path) if ctx_path else ""
            if ctx_text:
                parts.append(
                    f"Below is your route-specific context from `{ctx_tool}.md` (located at repo root):\n\n{ctx_text}"
                )

    if include_brain:
        brain_text = read_file_if_exists(PROJECT_BRAIN)
        if brain_text:
            parts.append(
                "Below is the canonical project brain from `docs/project_brain.md`:\n\n"
                f"{brain_text}"
            )

    if extra_context_file:
        extra_path = (REPO_ROOT / extra_context_file) if not Path(extra_context_file).is_absolute() else Path(extra_context_file)
        extra_text = read_file_if_exists(extra_path)
        if extra_text:
            parts.append(
                f"Below is extra context from `{extra_context_file}`:\n\n{extra_text}"
            )

    parts.append("User task:\n" + user_prompt.strip())

    return "\n\n---\n\n".join(parts)


def tool_is_available(cmd: str) -> bool:
    base = cmd.split()[0]
    return shutil.which(base) is not None


def build_shell_command(base_cmd: str, combined_prompt: str) -> str:
    safe_prompt = combined_prompt.replace('"', '\\"')
    return f'{base_cmd} "{safe_prompt}"'

# ---------------------------------------------------------------------------
# Local Ollama (HTTP) helpers
# ---------------------------------------------------------------------------

DEFAULT_OLLAMA_BASE = os.getenv("PROXMESH_LOCAL_OLLAMA_BASE", "").strip()
DEFAULT_OLLAMA_MODEL = os.getenv("PROXMESH_LOCAL_MODEL", "qwen3:30b-a3b").strip()


def _ollama_post_json(base_url: str, path: str, payload: dict, timeout: int = 60) -> dict:
    # POST JSON to Ollama and return parsed JSON response.
    import urllib.request
    import urllib.error

    url = base_url.rstrip("/") + path
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else str(e)
        raise RuntimeError(f"Ollama HTTPError {e.code}: {raw[:300]}")
    except Exception as e:
        raise RuntimeError(f"Ollama request failed: {e}")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def run_local_ollama(prompt: str, *, model: str | None = None, base_url: str | None = None,
                     dry_run: bool = False, no_context: bool = False, with_brain: bool = False,
                     extra_context_file: str | None = None) -> int:
    # Run a prompt against a local Ollama endpoint (non-streaming).
    base = (base_url or DEFAULT_OLLAMA_BASE).strip()
    if not base:
        print("[prox-mesh] No Ollama base URL configured. Set PROXMESH_LOCAL_OLLAMA_BASE or pass --ollama-base.", file=sys.stderr)
        return 1

    use_model = (model or DEFAULT_OLLAMA_MODEL).strip()
    combined_prompt = build_combined_prompt(route="loc", base_tool="ollama", user_prompt=prompt, include_context=not no_context, include_brain=with_brain, extra_context_file=extra_context_file)
    payload = {"model": use_model, "prompt": combined_prompt, "stream": False}

    if dry_run:
        print("[prox-mesh] (dry-run) Would POST to:")
        base_clean = base.rstrip("/")
        print(f"  {base_clean}/api/generate")
        print(f"  model={use_model}")
        return 0

    print(f"[prox-mesh] Running local Ollama model '{use_model}' at {base}")
    resp = _ollama_post_json(base, "/api/generate", payload, timeout=180)
    if isinstance(resp, dict) and "response" in resp:
        sys.stdout.write(str(resp.get("response") or ""))
        if not str(resp.get("response") or "").endswith("\n"):
            sys.stdout.write("\n")
        return 0
    print(json.dumps(resp, indent=2))
    return 0


def run_doctor(*, base_url: str | None = None) -> int:
    base = (base_url or DEFAULT_OLLAMA_BASE).strip()
    def ok(label: str, status: bool, detail: str = ""):
        mark = "OK" if status else "FAIL"
        print(f"[{mark}] {label}" + (f" — {detail}" if detail else ""))
    ok("codex on PATH", tool_is_available("codex"))
    ok("claude on PATH", tool_is_available("claude"))
    if base:
        try:
            import urllib.request
            with urllib.request.urlopen(base.rstrip("/") + "/api/tags", timeout=10) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
            models = data.get("models") if isinstance(data, dict) else None
            count = len(models) if isinstance(models, list) else None
            ok("ollama /api/tags reachable", True, f"{base} (models={count})")
        except Exception as e:
            ok("ollama /api/tags reachable", False, str(e))
    else:
        ok("ollama base configured", False, "Set PROXMESH_LOCAL_OLLAMA_BASE")
    return 0



def run_route(route: str, prompt: str, dry_run: bool = False,
              no_context: bool = False, with_brain: bool = False,
              extra_context_file: str | None = None) -> int:
    base_cmd = DEFAULT_CMDS.get(route)
    if not base_cmd:
        print(
            f"[prox-mesh] No base command configured for route '{route}'. "
            f"Set PROXMESH_{route.upper()}_CMD or adjust DEFAULT_CMDS.",
            file=sys.stderr,
        )
        return 1

    if not tool_is_available(base_cmd):
        print(
            f"[prox-mesh] Tool for route '{route}' not found on PATH.\n"
            f"  Expected base command: {base_cmd}\n"
            f"  Fix: install the CLI or adjust PROXMESH_{route.upper()}_CMD.",
            file=sys.stderr,
        )
        return 1

    combined_prompt = build_combined_prompt(
        route=route,
        base_tool=base_cmd,
        user_prompt=prompt,
        include_context=not no_context,
        include_brain=with_brain,
        extra_context_file=extra_context_file,
    )

    full_cmd = build_shell_command(base_cmd, combined_prompt)

    if dry_run:
        print(f"[prox-mesh] (dry-run) Would run:\n  {full_cmd}")
        return 0

    print(f"[prox-mesh] Running route '{route}' with:\n  {full_cmd}")
    try:
        result = subprocess.run(full_cmd, shell=True)
        return result.returncode
    except KeyboardInterrupt:
        print("[prox-mesh] Interrupted by user.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"[prox-mesh] Error executing command: {e}", file=sys.stderr)
        return 1


def append_kb_log(log_path: Path, query: str, stdout_text: str, returncode: int,
                  base_cmd: list[str], error: str | None) -> None:
    """
    Append a KB query entry to a JSONL log.

    OPSEC: Logs only safe metadata, never the full response payload.
    """
    # Timezone-aware UTC timestamp
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    entry: dict = {
        "timestamp": timestamp,
        "query": query,
        "kb_cmd": base_cmd,
        "returncode": returncode,
        "opsec_flags": None,
        "cloud_safe": None,
        "result_count": None,
        "error": error,
    }

    try:
        payload = json.loads(stdout_text)
        if isinstance(payload, dict):
            # Extract OPSEC flags
            opsec = payload.get("opsec_flags") or payload.get("opsec")
            entry["opsec_flags"] = opsec
            entry["cloud_safe"] = payload.get("cloud_safe")
            if entry["cloud_safe"] is None and isinstance(opsec, dict):
                entry["cloud_safe"] = opsec.get("cloud_safe")

            # Count results if available (safe metadata)
            results = payload.get("results") or payload.get("hits") or payload.get("matches")
            if isinstance(results, list):
                entry["result_count"] = len(results)
            elif isinstance(results, int):
                entry["result_count"] = results
        elif isinstance(payload, list):
            entry["result_count"] = len(payload)
    except json.JSONDecodeError:
        # Not JSON - log length and preview only
        entry["stdout_len"] = len(stdout_text)
        preview = stdout_text.strip()[:200]
        if preview:
            entry["stdout_preview"] = preview

    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
    except OSError as exc:
        print(
            f"[prox-mesh] Warning: could not write KB log to {log_path}: {exc}",
            file=sys.stderr,
        )


def run_kb(query: str, dry_run: bool = False, log_path: Path | None = None,
           host: str | None = None, no_llm: bool = False, no_snippets: bool = False,
           sources: str | None = None, limit: int | None = None,
           raw: bool = True) -> int:
    """
    Run kb_ask via the Windows wrapper and optionally log to JSONL.

    Command is built from PROXMESH_KB_CMD env var or DEFAULT_KB_CMD.
    All tokens are clean argv items (no embedded quotes).
    """
    # Get base command as a list of argv tokens
    cmd_parts = get_kb_cmd()
    base_prog = cmd_parts[0]
    if not tool_is_available(base_prog):
        print(
            "[prox-mesh] KB tool not found. "
            f"Expected base command on PATH: {base_prog}\n"
            "  Fix: install kb_ask wrapper or set PROXMESH_KB_CMD.",
            file=sys.stderr,
        )
        return 1

    if host:
        cmd_parts.extend(["--host", host])

    if raw:
        if "--raw" not in cmd_parts:
            cmd_parts.append("--raw")
    else:
        cmd_parts = [part for part in cmd_parts if part != "--raw"]

    if no_llm:
        cmd_parts.append("--no-llm")
    if no_snippets:
        cmd_parts.append("--no-snippets")
    if sources:
        cmd_parts.extend(["--sources", sources])
    if limit is not None:
        cmd_parts.extend(["--limit", str(limit)])

    cmd_parts.append(query)

    if dry_run:
        print(f"[prox-mesh] (dry-run) Would run KB command:\n  {' '.join(cmd_parts)}")
        if log_path:
            print(f"[prox-mesh] (dry-run) Would log to: {log_path}")
        return 0

    try:
        proc = subprocess.Popen(
            cmd_parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except Exception as exc:
        print(f"[prox-mesh] Error executing KB command: {exc}", file=sys.stderr)
        return 1

    stdout_lines: list[str] = []
    error: str | None = None
    start = time.monotonic()
    timed_out = False

    try:
        while True:
            if proc.stdout is None:
                break
            line = proc.stdout.readline()
            if line:
                stdout_lines.append(line)
                sys.stdout.write(line)
            if proc.poll() is not None:
                break
            if time.monotonic() - start > 30:
                timed_out = True
                proc.kill()
                error = "KB command timed out after 30s"
                print(f"[prox-mesh] {error}", file=sys.stderr)
                break

        if proc.stdout:
            remainder = proc.stdout.read()
            if remainder:
                stdout_lines.append(remainder)
                sys.stdout.write(remainder)

        try:
            returncode = proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            returncode = proc.poll() or 1
    except Exception as exc:
        if proc.poll() is None:
            try:
                proc.kill()
                proc.wait(timeout=1)
            except Exception:
                pass
        error = f"KB command failed: {exc}"
        print(f"[prox-mesh] {error}", file=sys.stderr)
        returncode = 1
    finally:
        if proc.stdout:
            proc.stdout.close()

    stdout_text = "".join(stdout_lines)

    if timed_out and returncode == 0:
        returncode = 1

    if error is None and returncode != 0:
        error = "KB command exited with non-zero status"

    if log_path:
        try:
            append_kb_log(log_path, query, stdout_text, returncode, cmd_parts, error)
        except Exception as exc:
            print(
                f"[prox-mesh] Warning: failed to write KB log {log_path}: {exc}",
                file=sys.stderr,
            )

    return returncode


# ---------------------------------------------------------------------------
# plan-kb (PLAN-KB Route Specification v0)
# ---------------------------------------------------------------------------

_PLAN_KB_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from", "how",
    "i", "if", "in", "into", "is", "it", "need", "of", "on", "or", "our", "path",
    "please", "should", "that", "the", "this", "to", "target", "we", "with",
    "box", "host", "machine", "server", "want", "looking", "ideas",
}

_PLAN_KB_KEYWORD_ORDER = [
    "htb",
    "linux",
    "windows",
    "recon",
    "enumeration",
    "privesc",
    "suid",
    "sudo",
    "capabilities",
    "cron",
    "services",
    "web",
    "smb",
    "kerberos",
    "ssh",
]

_PLAN_KB_SYNONYMS: dict[str, list[str]] = {
    "htb": ["htb", "hackthebox"],
    "linux": ["linux", "ubuntu", "debian", "kali", "centos", "rhel", "alpine"],
    "windows": ["windows", "win", "active-directory", "activedirectory", "ad"],
    "recon": ["recon", "reconnaissance", "scan", "scanning", "nmap"],
    "enumeration": ["enum", "enumeration", "enumerate", "discovery"],
    "privesc": ["privesc", "privilege-escalation", "escalation", "root"],
    "suid": ["suid", "setuid"],
    "sudo": ["sudo", "sudoers"],
    "capabilities": ["cap", "caps", "capabilities", "setcap", "getcap"],
    "cron": ["cron", "crontab", "systemd-timer", "timer"],
    "services": ["service", "services", "systemd", "init", "daemon"],
    "web": ["web", "http", "https", "nginx", "apache"],
    "smb": ["smb", "samba", "cifs"],
    "kerberos": ["kerberos", "kerberoast", "asreproast", "tgt", "tgs"],
    "ssh": ["ssh"],
}


def _tokenize_v0(text: str) -> list[str]:
    # Keep it deterministic and simple: lowercase, collapse, and extract tokens.
    return re.findall(r"[a-z0-9][a-z0-9+._-]{1,48}", text.lower())


def extract_kb_query_v0(objective_text: str) -> tuple[str, dict]:
    """
    Deterministic v0 query extraction.

    Heuristics only: keyword detection + stable ordering, no embeddings/LLMs.
    """
    tokens = _tokenize_v0(objective_text)
    token_set = set(t for t in tokens if t not in _PLAN_KB_STOPWORDS)

    matched: dict[str, bool] = {}
    for key, synonyms in _PLAN_KB_SYNONYMS.items():
        matched[key] = any(s in token_set for s in synonyms)

    ordered_terms: list[str] = []
    for key in _PLAN_KB_KEYWORD_ORDER:
        if matched.get(key):
            if key == "privesc":
                ordered_terms.extend(["privilege", "escalation"])
            else:
                ordered_terms.append(key)

    # Add a small tail of leftover tokens (stable by appearance) for specificity.
    tail: list[str] = []
    for t in tokens:
        if t in _PLAN_KB_STOPWORDS:
            continue
        if t in token_set and t not in ordered_terms and t not in tail:
            tail.append(t)
        if len(tail) >= 6:
            break

    # Avoid repeating keywords already represented by normalized terms.
    query_terms = ordered_terms + [t for t in tail if t not in ordered_terms]
    query = " ".join(query_terms).strip() or objective_text.strip()

    meta = {"matched_keywords": [k for k in _PLAN_KB_KEYWORD_ORDER if matched.get(k)]}
    return query, meta


def _parse_json_from_stdout(stdout_text: str) -> object:
    text = stdout_text.strip()
    if not text:
        raise ValueError("KB returned empty output")

    # 1) Direct parse
    if text[0] in "{[":
        return json.loads(text)

    # 2) JSONL scan: last valid object/array wins
    last_obj: object | None = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line[0] not in "{[":
            continue
        try:
            last_obj = json.loads(line)
        except json.JSONDecodeError:
            continue
    if last_obj is not None:
        return last_obj

    # 3) Balanced-brace scan from the end: find the last complete JSON object/array.
    def _balanced_scan(text_: str, open_ch: str, close_ch: str) -> object | None:
        end_idx = text_.rfind(close_ch)
        while end_idx != -1:
            depth = 0
            for start_idx in range(end_idx, -1, -1):
                ch = text_[start_idx]
                if ch == close_ch:
                    depth += 1
                elif ch == open_ch:
                    depth -= 1
                    if depth == 0:
                        candidate = text_[start_idx : end_idx + 1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            break
            end_idx = text_.rfind(close_ch, 0, end_idx)
        return None

    obj = _balanced_scan(text, "{", "}")
    if obj is not None:
        return obj

    arr = _balanced_scan(text, "[", "]")
    if arr is not None:
        return arr

    raise ValueError("KB output was not JSON")


def _strip_snippets(obj: object) -> object:
    """
    Remove snippet-like fields recursively to ensure OPSEC-safe stdout/logging.
    """
    redacted_keys = {
        "snippet", "snippets", "text", "content", "body", "excerpt", "quote",
        "passage", "raw", "raw_snippet", "markdown", "html", "response",
    }
    if isinstance(obj, dict):
        out: dict = {}
        for k, v in obj.items():
            if isinstance(k, str) and k.lower() in redacted_keys:
                continue
            out[k] = _strip_snippets(v)
        return out
    if isinstance(obj, list):
        return [_strip_snippets(v) for v in obj]
    return obj


def _resolve_repo_relative_path(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (REPO_ROOT / p)


def build_kb_cmd_parts_for_plan_kb(
    *,
    query: str,
    host: str | None,
    sources: str | None,
    limit: int | None,
    no_llm: bool,
    no_snippets: bool,
) -> list[str]:
    cmd_parts = get_kb_cmd()

    if host:
        cmd_parts.extend(["--host", host])

    # Ensure JSON output from KB wrapper.
    if "--raw" not in cmd_parts:
        cmd_parts.append("--raw")

    # Default: do not request snippets (OPSEC-safe default).
    if no_snippets and "--no-snippets" not in cmd_parts:
        cmd_parts.append("--no-snippets")

    if no_llm and "--no-llm" not in cmd_parts:
        cmd_parts.append("--no-llm")

    if sources:
        cmd_parts.extend(["--sources", sources])
    if limit is not None:
        cmd_parts.extend(["--limit", str(limit)])

    cmd_parts.append(query)
    return cmd_parts


def run_kb_capture_json(
    *,
    query: str,
    host: str | None,
    sources: str | None,
    limit: int | None,
    no_llm: bool,
    no_snippets: bool,
    kb_log_path: Path | None,
) -> tuple[int, object | None, dict]:
    """
    Execute KB wrapper, capture output, parse JSON, and (optionally) log metadata.

    Returns: (returncode, parsed_json_or_none, meta)
    """
    cmd_parts = build_kb_cmd_parts_for_plan_kb(
        query=query,
        host=host,
        sources=sources,
        limit=limit,
        no_llm=no_llm,
        no_snippets=no_snippets,
    )

    base_prog = cmd_parts[0]
    if not tool_is_available(base_prog):
        raise RuntimeError(
            "KB tool not found. Expected base command on PATH: "
            f"{base_prog}. Fix: install kb_ask wrapper or set PROXMESH_KB_CMD."
        )

    try:
        proc = subprocess.run(
            cmd_parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except Exception as exc:
        stdout_text = ""
        error = f"KB command failed to start: {exc}"
        if kb_log_path:
            append_kb_log(kb_log_path, query, stdout_text, 1, cmd_parts, error)
        return 1, None, {"cmd_parts": cmd_parts, "error": error, "stdout_text": stdout_text}

    stdout_text = proc.stdout or ""
    error = None
    parsed: object | None = None
    try:
        parsed = _parse_json_from_stdout(stdout_text)
    except Exception as exc:
        error = f"KB JSON parse failed: {exc}"

    if proc.returncode != 0 and error is None:
        error = "KB command exited with non-zero status"

    if kb_log_path:
        append_kb_log(kb_log_path, query, stdout_text, proc.returncode, cmd_parts, error)

    meta = {"cmd_parts": cmd_parts, "error": error, "stdout_text": stdout_text}
    return proc.returncode, parsed, meta


def _extract_opsec_flags(payload: object | None) -> tuple[bool | None, str | None]:
    if not isinstance(payload, dict):
        return None, None

    opsec = payload.get("opsec_flags") or payload.get("opsec") or {}
    cloud_safe = payload.get("cloud_safe")
    if cloud_safe is None and isinstance(opsec, dict):
        cloud_safe = opsec.get("cloud_safe")

    local_only_reason = payload.get("local_only_reason")
    if local_only_reason is None and isinstance(opsec, dict):
        local_only_reason = opsec.get("local_only_reason") or opsec.get("reason")

    return cloud_safe, local_only_reason


def _kb_results_metadata(payload: object | None) -> list[dict]:
    if not isinstance(payload, dict):
        return []

    results = payload.get("results") or payload.get("hits") or payload.get("matches")
    if not isinstance(results, list):
        return []

    safe_results: list[dict] = []
    for r in results:
        if not isinstance(r, dict):
            continue

        path = r.get("path") or r.get("file") or r.get("filepath") or r.get("relpath")
        line_start = r.get("line_start") or r.get("start_line") or r.get("line")
        line_end = r.get("line_end") or r.get("end_line") or line_start

        ref = None
        if path and line_start:
            ref = f"{path}:{line_start}-{line_end}"
        elif path:
            ref = str(path)
        elif r.get("id"):
            ref = f"id:{r.get('id')}"

        safe_results.append(
            {
                "ref": ref,
                "path": path,
                "line_start": line_start,
                "line_end": line_end,
                "source": r.get("source") or r.get("collection"),
                "title": r.get("title"),
                "tags": r.get("tags"),
                "score": r.get("score"),
            }
        )

    # Drop entries that have no usable metadata reference.
    return [r for r in safe_results if r.get("ref")]


def build_plan_kb_payload(
    *,
    objective: str,
    kb_query: str,
    kb_payload: object | None,
    kb_error: str | None,
    extraction_meta: dict,
) -> dict:
    cloud_safe, local_only_reason = _extract_opsec_flags(kb_payload)
    classification = "CLOUD_SAFE"
    if cloud_safe is False:
        classification = "LOCAL_ONLY"

    safe_kb_payload = _strip_snippets(kb_payload) if kb_payload is not None else None
    references = _kb_results_metadata(safe_kb_payload)

    steps: list[dict] = [
        {
            "title": "Initial recon",
            "notes": "Enumerate services and attack surface; do not run suggested commands automatically.",
            "suggested_commands": [
                "nmap -sC -sV -oA logs/nmap_initial <target_ip>",
                "whatweb http://<target_ip>/  # if web is exposed",
            ],
        },
        {
            "title": "Focused enumeration",
            "notes": "Collect local privilege escalation signals and misconfigurations.",
            "suggested_commands": [
                "id; uname -a; cat /etc/os-release",
                "find / -perm -4000 -type f 2>/dev/null  # SUID sweep",
                "sudo -l",
                "getcap -r / 2>/dev/null  # file capabilities",
            ],
        },
        {
            "title": "Review KB hits (metadata only)",
            "notes": "Review referenced KB entries by path/line only; never copy raw snippets into reports or logs.",
            "kb_references": [r["ref"] for r in references[:10]],
        },
        {
            "title": "Draft privesc hypothesis",
            "notes": "Form hypotheses based on environment + KB metadata; validate locally.",
            "suggested_commands": [
                "strings <candidate_binary> | head 50",
                "ldd <candidate_binary>",
                "ps aux; ss -lntup",
            ],
        },
    ]

    payload: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "route": "plan-kb",
        "objective": objective,
        "kb_query": kb_query,
        "extraction": extraction_meta,
        "kb": {
            "cloud_safe": cloud_safe,
            "local_only_reason": local_only_reason,
            "result_count": len(references),
            "error": kb_error,
            "results": references,
        },
        "plan": {
            "classification": classification,
            "local_only_reason": local_only_reason,
            "steps": steps,
        },
    }

    return payload


def format_plan_kb_human(plan_payload: dict) -> str:
    classification = plan_payload.get("plan", {}).get("classification")
    local_only_reason = plan_payload.get("plan", {}).get("local_only_reason")

    lines: list[str] = []
    if classification == "LOCAL_ONLY":
        lines.append("LOCAL_ONLY: KB indicates cloud_safe=false")
        if local_only_reason:
            lines.append(f"Reason: {local_only_reason}")
        lines.append("")

    lines.append(f"Objective: {plan_payload.get('objective', '').strip()}")
    lines.append(f"KB query:  {plan_payload.get('kb_query', '').strip()}")
    lines.append("")

    steps = plan_payload.get("plan", {}).get("steps") or []
    for idx, step in enumerate(steps, start=1):
        title = step.get("title", f"Step {idx}")
        lines.append(f"{idx}. {title}")
        notes = step.get("notes")
        if notes:
            lines.append(f"   - {notes}")
        for cmd in step.get("suggested_commands") or []:
            lines.append(f"   - suggest: {cmd}")
        refs = step.get("kb_references") or []
        if refs:
            lines.append("   - KB refs:")
            for r in refs:
                lines.append(f"     - {r}")

    refs = plan_payload.get("kb", {}).get("results") or []
    if refs:
        lines.append("")
        lines.append("KB references (metadata only):")
        for i, r in enumerate(refs[:20], start=1):
            title = r.get("title")
            suffix = f" — {title}" if title else ""
            lines.append(f"  [{i}] {r.get('ref')}{suffix}")

    return "\n".join(lines).rstrip() + "\n"


def default_plan_kb_log_path() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    return DEFAULT_PLAN_KB_LOG_DIR / f"plan_kb_{stamp}.json"


def write_plan_kb_log(plan_payload: dict, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as handle:
        json.dump(plan_payload, handle, indent=2, sort_keys=False)
        handle.write("\n")


def default_prompt_kb_log_path() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    return REPO_ROOT / "logs" / f"prompt_kb_{stamp}.json"


def _drop_flag_with_value(parts: list[str], flag: str) -> list[str]:
    cleaned: list[str] = []
    skip_next = False
    for token in parts:
        if skip_next:
            skip_next = False
            continue
        if token == flag:
            skip_next = True
            continue
        cleaned.append(token)
    return cleaned


def build_prompt_kb_cmd_parts(
    *,
    query: str,
    host: str | None,
    sources: str | None,
    limit: int | None,
    max_hints: int | None,
    hint_length: int | None,
    brief_length: int | None,
    no_llm: bool,
) -> list[str]:
    cmd_parts = get_kb_cmd()

    if host:
        cmd_parts.extend(["--host", host])

    if "--raw" not in cmd_parts:
        cmd_parts.append("--raw")

    cmd_parts = _drop_flag_with_value(cmd_parts, "--brief")
    cmd_parts.extend(["--brief", "cloud"])

    if sources:
        cmd_parts = _drop_flag_with_value(cmd_parts, "--sources")
        cmd_parts.extend(["--sources", sources])
    if limit is not None:
        cmd_parts = _drop_flag_with_value(cmd_parts, "--limit")
        cmd_parts.extend(["--limit", str(limit)])
    if max_hints is not None:
        cmd_parts = _drop_flag_with_value(cmd_parts, "--max-hints")
        cmd_parts.extend(["--max-hints", str(max_hints)])
    if hint_length is not None:
        cmd_parts = _drop_flag_with_value(cmd_parts, "--hint-length")
        cmd_parts.extend(["--hint-length", str(hint_length)])
    if brief_length is not None:
        cmd_parts = _drop_flag_with_value(cmd_parts, "--brief-length")
        cmd_parts.extend(["--brief-length", str(brief_length)])
    if no_llm and "--no-llm" not in cmd_parts:
        cmd_parts.append("--no-llm")

    cmd_parts.append(query)
    return cmd_parts


def _safe_prompt_hints(hints: object) -> list[dict]:
    if not isinstance(hints, list):
        return []

    safe: list[dict] = []
    for h in hints:
        if not isinstance(h, dict):
            continue
        safe.append(
            {
                "source_path": h.get("source_path") or h.get("path"),
                "title": h.get("title"),
                "line_number": h.get("line_number") or h.get("line") or h.get("start_line"),
                "abstractive_hint": h.get("abstractive_hint") or h.get("hint"),
                "source_type": h.get("source_type") or h.get("collection") or h.get("source"),
            }
        )
    return [h for h in safe if any(v for v in h.values())]


def _extract_cloud_pack(payload: object | None) -> tuple[str | None, list[dict], list[str]]:
    if not isinstance(payload, dict):
        return None, [], []

    cp = payload.get("cloud_pack")
    if not isinstance(cp, dict):
        cp = {}

    brief = cp.get("brief")
    hints = _safe_prompt_hints(cp.get("hints"))

    followups_raw = cp.get("followup_queries") or []
    followups = [q for q in followups_raw if isinstance(q, str)]

    return brief, hints, followups


def _resolve_cloud_safe(payload: object | None) -> bool | None:
    if not isinstance(payload, dict):
        return None

    cloud_pack = payload.get("cloud_pack")
    if isinstance(cloud_pack, dict):
        cp_safe = cloud_pack.get("cloud_safe")
        if cp_safe is not None:
            return cp_safe

    opsec = payload.get("opsec_flags") or payload.get("opsec") or {}
    if "cloud_safe" in payload and payload.get("cloud_safe") is not None:
        return payload.get("cloud_safe")
    if isinstance(opsec, dict) and opsec.get("cloud_safe") is not None:
        return opsec.get("cloud_safe")

    return None


def _extract_meta_fields(payload: object | None, requested_sources: str | None) -> tuple[int, list[str]]:
    if not isinstance(payload, dict):
        return 0, [requested_sources] if requested_sources else []

    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    result_count = meta.get("result_count", 0) if isinstance(meta, dict) else 0
    sources_raw = meta.get("sources_searched") if isinstance(meta, dict) else []

    sources: list[str] = [s for s in sources_raw or [] if isinstance(s, str)]
    if not sources and requested_sources:
        sources = [requested_sources]

    return result_count if isinstance(result_count, int) else 0, sources


def _fallback_brief(result_count: int, sources: list[str]) -> str:
    source_text = ", ".join(sources) if sources else "requested sources"
    return (
        f"KB did not return a brief. Found {result_count} result(s) across {source_text}. "
        "Use metadata-only hints below; do not paste raw snippets."
    )


def _lab_pack_default_log_path() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    return REPO_ROOT / "logs" / f"lab_pack_{stamp}.json"


def format_prompt_kb_human(
    *,
    cloud_safe: bool | None,
    brief: str | None,
    hints: list[dict],
    followups: list[str],
    kb_query: str,
    objective: str,
    result_count: int,
    sources: list[str],
) -> str:
    banner = "CLOUD-SAFE: UNKNOWN"
    if cloud_safe is True:
        banner = "CLOUD-SAFE: YES"
    elif cloud_safe is False:
        banner = "CLOUD-SAFE: NO"

    lines: list[str] = []
    lines.append(banner)
    lines.append(f"Objective: {objective.strip()}")
    lines.append(f"KB query: {kb_query.strip()}")
    if result_count or sources:
        source_text = ", ".join(sources) if sources else "unspecified sources"
        lines.append(f"Results: {result_count} across {source_text}")
    lines.append("")

    if brief:
        lines.append("PASTE INTO CLOUD MODEL:")
        lines.append(brief.strip())
        lines.append("")

    lines.append("Hints (metadata only):")
    if hints:
        for idx, h in enumerate(hints, start=1):
            parts: list[str] = []
            if h.get("source_path"):
                parts.append(str(h["source_path"]))
            if h.get("line_number"):
                parts.append(f"line {h['line_number']}")
            if h.get("title"):
                parts.append(h["title"])
            if h.get("source_type"):
                parts.append(f"[{h['source_type']}]")
            header = " - ".join(part for part in parts if part)
            lines.append(f"[{idx}] {header}".strip())
            if h.get("abstractive_hint"):
                lines.append(f"    {h['abstractive_hint']}")
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("Followup queries:")
    if followups:
        for fq in followups:
            lines.append(f" - {fq}")
    else:
        lines.append("  (none)")

    return "\n".join(lines).rstrip() + "\n"


def write_prompt_kb_log(payload: dict, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=False)
        handle.write("\n")


def run_prompt_kb(
    *,
    objective: str,
    kb_query_override: str | None,
    host: str | None,
    sources: str | None,
    limit: int | None,
    max_hints: int | None,
    hint_length: int | None,
    brief_length: int | None,
    no_llm: bool,
    dry_run: bool,
    json_only: bool,
    log_path_str: str | None,
) -> int:
    if kb_query_override:
        kb_query = kb_query_override.strip()
        extraction_meta = {"matched_keywords": [], "override": True}
    else:
        kb_query, extraction_meta = extract_kb_query_v0(objective)
        extraction_meta["override"] = False

    cmd_parts = build_prompt_kb_cmd_parts(
        query=kb_query,
        host=host,
        sources=sources,
        limit=limit,
        max_hints=max_hints,
        hint_length=hint_length,
        brief_length=brief_length,
        no_llm=no_llm,
    )

    log_path = (
        _resolve_repo_relative_path(log_path_str)
        if log_path_str
        else default_prompt_kb_log_path()
    )

    if dry_run:
        print("[prox-mesh] (dry-run) Would run KB command:\n  " + " ".join(cmd_parts))
        print(f"[prox-mesh] (dry-run) Would write prompt log to:\n  {log_path}")
        return 0

    base_prog = cmd_parts[0]
    if not tool_is_available(base_prog):
        print(
            "[prox-mesh] KB tool not found. "
            f"Expected base command on PATH: {base_prog}\n"
            "  Fix: install kb_ask wrapper or set PROXMESH_KB_CMD.",
            file=sys.stderr,
        )
        return 1

    try:
        proc = subprocess.run(
            cmd_parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except Exception as exc:
        print(f"[prox-mesh] Error executing KB command: {exc}", file=sys.stderr)
        return 1

    stdout_text = proc.stdout or ""
    error = None
    payload: object | None = None
    try:
        payload = _parse_json_from_stdout(stdout_text)
    except Exception as exc:
        error = f"KB JSON parse failed: {exc}"

    sanitized_payload = _strip_snippets(payload) if payload is not None else None
    result_count, meta_sources = _extract_meta_fields(sanitized_payload, sources)

    cloud_safe = _resolve_cloud_safe(sanitized_payload)
    if cloud_safe is None:
        cloud_safe, _local_reason = _extract_opsec_flags(sanitized_payload)

    brief, hints, followups = _extract_cloud_pack(sanitized_payload)
    brief = brief or _fallback_brief(result_count, meta_sources)

    log_payload = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "route": "prompt-kb",
        "objective": objective,
        "kb_query": kb_query,
        "extraction": extraction_meta,
        "cloud_safe": cloud_safe,
        "kb_cmd": cmd_parts,
        "kb_returncode": proc.returncode,
        "error": error,
        "meta": {
            "result_count": result_count,
            "sources_searched": meta_sources,
        },
        "cloud_pack": {
            "brief": brief,
            "hints": hints,
            "followup_queries": followups,
        },
        "kb_payload": sanitized_payload,
    }

    try:
        write_prompt_kb_log(log_payload, log_path)
    except OSError as exc:
        print(f"[prox-mesh] Warning: could not write prompt KB log to {log_path}: {exc}", file=sys.stderr)

    if json_only:
        safe_out = {
            "cloud_safe": cloud_safe,
            "brief": brief,
            "hints": hints,
            "followup_queries": followups,
            "kb_query": kb_query,
            "objective": objective,
            "result_count": result_count,
            "sources": meta_sources,
            "error": error,
        }
        print(json.dumps(safe_out, indent=2, sort_keys=False))
        return proc.returncode if proc.returncode != 0 else (1 if error else 0)

    sys.stdout.write(
        format_prompt_kb_human(
            cloud_safe=cloud_safe,
            brief=brief,
            hints=hints,
            followups=followups,
            kb_query=kb_query,
            objective=objective,
            result_count=result_count,
            sources=meta_sources,
        )
    )

    if error:
        print(f"[prox-mesh] Warning: {error}", file=sys.stderr)

    return proc.returncode if proc.returncode != 0 else (1 if error else 0)


def _lab_pack_hints(hints_obj: object) -> list[dict]:
    if not isinstance(hints_obj, list):
        return []

    hints: list[dict] = []
    for h in hints_obj:
        if not isinstance(h, dict):
            continue
        hints.append(
            {
                "source_path": h.get("source_path") or h.get("path"),
                "line_number": h.get("line_number") or h.get("line") or h.get("start_line"),
                "source_type": h.get("source_type") or h.get("collection") or h.get("source"),
                "abstractive_hint": h.get("abstractive_hint") or h.get("hint"),
            }
        )
    return [hint for hint in hints if any(v for v in hint.values())]


def _extract_lab_pack_fields(payload: object | None) -> tuple[bool | None, str | None, list[dict], list[str], list[str], dict, object, dict]:
    if not isinstance(payload, dict):
        return None, None, [], [], [], {}, None, {}

    cloud_pack = payload.get("cloud_pack")
    if not isinstance(cloud_pack, dict):
        cloud_pack = {}

    cloud_safe = cloud_pack.get("cloud_safe")
    brief = cloud_pack.get("brief")
    hints = _lab_pack_hints(cloud_pack.get("hints"))

    followups_raw = cloud_pack.get("followup_queries") or []
    followups = [q for q in followups_raw if isinstance(q, str)]

    warnings_raw = cloud_pack.get("warnings") or []
    warnings = [w for w in warnings_raw if isinstance(w, str)]

    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    opsec_flags = payload.get("opsec_flags") or payload.get("opsec")

    return cloud_safe, brief, hints, followups, warnings, meta, opsec_flags, cloud_pack

# Quick self-check: python -m py_compile nextgen-mesh/ProxOffensive-LocalMesh/agents/prox_mesh.py


def format_lab_pack_human(
    *,
    cloud_safe: bool | None,
    brief: str | None,
    hints: list[dict],
    followups: list[str],
    warnings: list[str],
    objective: str,
) -> str:
    banner = "CLOUD-SAFE: UNKNOWN"
    if cloud_safe is True:
        banner = "CLOUD-SAFE: YES"
    elif cloud_safe is False:
        banner = "CLOUD-SAFE: NO"

    lines: list[str] = [banner, f"Objective: {objective.strip()}", ""]

    lines.append("PASTE INTO CLOUD MODEL:")
    if brief:
        lines.append(brief.strip())
    else:
        lines.append("(no brief returned; use hints metadata only)")
    lines.append("")

    lines.append("Hints (metadata only):")
    if hints:
        for idx, h in enumerate(hints, start=1):
            parts: list[str] = []
            if h.get("source_path"):
                parts.append(str(h["source_path"]))
            if h.get("line_number"):
                parts.append(f"line {h['line_number']}")
            if h.get("source_type"):
                parts.append(f"[{h['source_type']}]")
            header = " - ".join(part for part in parts if part) or "(metadata unavailable)"
            lines.append(f"[{idx}] {header}".strip())
            if h.get("abstractive_hint"):
                lines.append(f"    {h['abstractive_hint']}")
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("Followup queries:")
    if followups:
        for fq in followups:
            lines.append(f" - {fq}")
    else:
        lines.append("  (none)")

    if warnings:
        lines.append("")
        lines.append("Warnings:")
        for w in warnings:
            lines.append(f" - {w}")

    return "\n".join(lines).rstrip() + "\n"


def write_lab_pack_log(payload: dict, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=False)
        handle.write("\n")


def build_lab_pack_cmd_parts(
    *,
    objective: str,
    state_file: str,
    host: str | None,
    sources: str | None,
    limit: int | None,
    queries: int | None,
    state_max_chars: int | None,
    max_hints: int | None,
    hint_length: int | None,
    brief_length: int | None,
    no_llm: bool,
) -> list[str]:
    cmd_parts = get_kb_cmd()

    if host:
        cmd_parts.extend(["--host", host])

    cmd_parts = _drop_flag_with_value(cmd_parts, "--lab-pack")
    cmd_parts = _drop_flag_with_value(cmd_parts, "--state-file")
    cmd_parts.extend(["--lab-pack", objective, "--state-file", state_file])

    if sources:
        cmd_parts = _drop_flag_with_value(cmd_parts, "--sources")
        cmd_parts.extend(["--sources", sources])
    if limit is not None:
        cmd_parts = _drop_flag_with_value(cmd_parts, "--limit")
        cmd_parts.extend(["--limit", str(limit)])
    if queries is not None:
        cmd_parts = _drop_flag_with_value(cmd_parts, "--queries")
        cmd_parts.extend(["--queries", str(queries)])
    if state_max_chars is not None:
        cmd_parts = _drop_flag_with_value(cmd_parts, "--state-max-chars")
        cmd_parts.extend(["--state-max-chars", str(state_max_chars)])
    if max_hints is not None:
        cmd_parts = _drop_flag_with_value(cmd_parts, "--max-hints")
        cmd_parts.extend(["--max-hints", str(max_hints)])
    if hint_length is not None:
        cmd_parts = _drop_flag_with_value(cmd_parts, "--hint-length")
        cmd_parts.extend(["--hint-length", str(hint_length)])
    if brief_length is not None:
        cmd_parts = _drop_flag_with_value(cmd_parts, "--brief-length")
        cmd_parts.extend(["--brief-length", str(brief_length)])
    if no_llm and "--no-llm" not in cmd_parts:
        cmd_parts.append("--no-llm")

    return cmd_parts


def run_lab_pack(
    *,
    objective: str,
    state_file: str,
    host: str | None,
    sources: str | None,
    limit: int | None,
    queries: int | None,
    state_max_chars: int | None,
    max_hints: int | None,
    hint_length: int | None,
    brief_length: int | None,
    no_llm: bool,
    dry_run: bool,
    json_only: bool,
    log_path_str: str | None,
) -> int:
    cmd_parts = build_lab_pack_cmd_parts(
        objective=objective,
        state_file=state_file,
        host=host,
        sources=sources,
        limit=limit,
        queries=queries,
        state_max_chars=state_max_chars,
        max_hints=max_hints,
        hint_length=hint_length,
        brief_length=brief_length,
        no_llm=no_llm,
    )

    log_path = (
        _resolve_repo_relative_path(log_path_str)
        if log_path_str
        else _lab_pack_default_log_path()
    )

    if dry_run:
        print("[prox-mesh] (dry-run) Would run KB command:\n  " + " ".join(cmd_parts))
        print(f"[prox-mesh] (dry-run) Would write lab-pack log to:\n  {log_path}")
        return 0

    state_bytes: bytes | None = None
    if state_file == "-":
        state_bytes = sys.stdin.buffer.read()
        if not state_bytes or not state_bytes.strip():
            print(
                "[prox-mesh] Error: --state-file - requires piped state content on stdin",
                file=sys.stderr,
            )
            return 1

    base_prog = cmd_parts[0]
    if not tool_is_available(base_prog):
        print(
            "[prox-mesh] KB tool not found. "
            f"Expected base command on PATH: {base_prog}\n"
            "  Fix: install kb_ask wrapper or set PROXMESH_KB_CMD.",
            file=sys.stderr,
        )
        return 1

    try:
        run_kwargs: dict[str, object] = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
        }
        if state_bytes is not None:
            run_kwargs.update({"input": state_bytes, "text": False})
        else:
            run_kwargs.update({"text": True})
        proc = subprocess.run(cmd_parts, **run_kwargs)  # type: ignore[arg-type]
    except Exception as exc:
        print(f"[prox-mesh] Error executing KB command: {exc}", file=sys.stderr)
        return 1

    stdout_text = proc.stdout.decode("utf-8", errors="replace") if isinstance(proc.stdout, (bytes, bytearray)) else (proc.stdout or "")
    stderr_text = proc.stderr.decode("utf-8", errors="replace") if isinstance(proc.stderr, (bytes, bytearray)) else (proc.stderr or "")
    error = None
    payload: object | None = None
    try:
        payload = _parse_json_from_stdout(stdout_text)
    except Exception as exc:
        error = f"KB JSON parse failed: {exc}"

    sanitized_payload = _strip_snippets(payload) if payload is not None else None
    cloud_safe, brief, hints, followups, warnings, meta, opsec_flags, cloud_pack = _extract_lab_pack_fields(
        sanitized_payload
    )

    state_label = "stdin" if state_file == "-" else state_file

    kb_meta = meta if isinstance(meta, dict) else {}
    if error:
        kb_meta = dict(kb_meta)
        kb_meta["error"] = error
        kb_meta["returncode"] = proc.returncode
    elif proc.returncode != 0:
        kb_meta = dict(kb_meta)
        kb_meta["returncode"] = proc.returncode

    stderr_preview = None
    if error or proc.returncode != 0:
        if stderr_text:
            stderr_preview = _redact_paths(stderr_text[:500])

    log_payload = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "objective": objective,
        "state_file": state_label,
        "kb_meta": kb_meta or {},
        "opsec_flags": opsec_flags,
        "cloud_pack": cloud_pack or {},
        "returncode": proc.returncode,
    }
    if stderr_preview:
        log_payload["stderr_preview"] = stderr_preview

    try:
        write_lab_pack_log(log_payload, log_path)
    except OSError as exc:
        print(f"[prox-mesh] Warning: could not write lab-pack log to {log_path}: {exc}", file=sys.stderr)

    if json_only:
        safe_out = {
            "cloud_safe": cloud_safe,
            "brief": brief,
            "hints": hints,
            "followup_queries": followups,
            "warnings": warnings,
            "objective": objective,
            "state_file": state_label,
            "kb_meta": meta,
            "error": error,
        }
        print(json.dumps(safe_out, indent=2, sort_keys=False))
        return proc.returncode if proc.returncode != 0 else (1 if error else 0)

    sys.stdout.write(
        format_lab_pack_human(
            cloud_safe=cloud_safe,
            brief=brief,
            hints=hints,
            followups=followups,
            warnings=warnings,
            objective=objective,
        )
    )

    if error:
        print(f"[prox-mesh] Warning: {error}", file=sys.stderr)

    return proc.returncode if proc.returncode != 0 else (1 if error else 0)


def run_plan_kb(
    *,
    objective: str,
    kb_query_override: str | None,
    host: str | None,
    sources: str | None,
    limit: int | None,
    no_llm: bool,
    no_snippets: bool,
    dry_run: bool,
    json_only: bool,
    plan_log_path_str: str | None,
) -> int:
    if kb_query_override:
        kb_query = kb_query_override.strip()
        extraction_meta = {"matched_keywords": [], "override": True}
    else:
        kb_query, extraction_meta = extract_kb_query_v0(objective)
        extraction_meta["override"] = False

    kb_cmd_parts = build_kb_cmd_parts_for_plan_kb(
        query=kb_query,
        host=host,
        sources=sources,
        limit=limit,
        no_llm=no_llm,
        no_snippets=no_snippets,
    )

    plan_log_path = (
        _resolve_repo_relative_path(plan_log_path_str)
        if plan_log_path_str
        else default_plan_kb_log_path()
    )

    if dry_run:
        print("[prox-mesh] (dry-run) Would run KB command:\n  " + " ".join(kb_cmd_parts))
        print(f"[prox-mesh] (dry-run) Would write plan JSON to:\n  {plan_log_path}")
        return 0

    returncode, kb_payload, kb_meta = run_kb_capture_json(
        query=kb_query,
        host=host,
        sources=sources,
        limit=limit,
        no_llm=no_llm,
        no_snippets=no_snippets,
        kb_log_path=DEFAULT_KB_LOG,
    )

    if kb_meta.get("error"):
        print(f"[prox-mesh] Warning: {kb_meta['error']}", file=sys.stderr)

    plan_payload = build_plan_kb_payload(
        objective=objective,
        kb_query=kb_query,
        kb_payload=kb_payload,
        kb_error=kb_meta.get("error"),
        extraction_meta=extraction_meta,
    )

    try:
        write_plan_kb_log(plan_payload, plan_log_path)
    except OSError as exc:
        print(f"[prox-mesh] Warning: could not write plan log to {plan_log_path}: {exc}", file=sys.stderr)

    if json_only:
        print(json.dumps(plan_payload, indent=2, sort_keys=False))
    else:
        sys.stdout.write(format_plan_kb_human(plan_payload))

    return returncode


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prox-mesh",
        description="Prox Offensive local mesh router (v1.0).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(
            """
            Examples:

              prox-mesh plan "Design a Slingshot + Kali engagement folder tree for an SMB client."

              prox-mesh research "TLS downgrade attack latest techniques"

              prox-mesh edit "Refactor docs/host_cli_setup.md in Don Trabajo voice."

              echo "Write a summary of docs/project_brain.md" | prox-mesh ask --with-brain

            Common flags:

              --dry-run      # show resolved command, don't execute
              --no-context   # skip route-specific context file
              --with-brain   # also inject docs/project_brain.md
              --extra-context-file path/to/file.md  # inject additional context

            Env overrides:

              PROXMESH_PLAN_CMD     # e.g. 'claude -m opus'
              PROXMESH_RESEARCH_CMD # e.g. 'gemini'
              PROXMESH_EDIT_CMD     # e.g. 'codex'
              PROXMESH_ASK_CMD      # e.g. 'claude'
              PROXMESH_GENERATE_CMD # e.g. 'codex'
            """
        ),
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common_args(sp: argparse.ArgumentParser):
        sp.add_argument(
            "prompt",
            nargs="*",
            help="Prompt text. If omitted, can come from --file or stdin.",
        )
        sp.add_argument(
            "-f",
            "--file",
            help="Read prompt text from a file.",
        )
        sp.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the resolved command without executing it.",
        )
        sp.add_argument(
            "--no-context",
            action="store_true",
            help="Do not inject route-specific context file (claude.md/codex.md/etc.).",
        )
        sp.add_argument(
            "--with-brain",
            action="store_true",
            help="Also inject docs/project_brain.md into the prompt.",
        )
        sp.add_argument(
            "--extra-context-file",
            help="Additional context file path (relative to repo root or absolute).",
        )
        sp.add_argument(
            "--opsec",
            choices=["PUB", "INT", "CON", "RES", "LOC"],
            help=(
                "OPSEC classification hint. RES/LOC forces local-only routing (Ollama) "
                "for plan/research/edit/ask/generate routes unless explicitly using kb tools."
            ),
        )

    sp_plan = subparsers.add_parser(
        "plan",
        help="High-level planning (default: Claude or configured planner).",
    )
    add_common_args(sp_plan)

    sp_research = subparsers.add_parser(
        "research",
        help="Research via Claude or configured research tool (Gemini later).",
    )
    add_common_args(sp_research)

    sp_edit = subparsers.add_parser(
        "edit",
        help="Editing/refactor tasks via Codex or configured editor.",
    )
    add_common_args(sp_edit)

    sp_ask = subparsers.add_parser(
        "ask",
        help="General Q&A or explanation via Claude or configured tool.",
    )
    add_common_args(sp_ask)

    sp_generate = subparsers.add_parser(
        "generate",
        help="Generate artifacts (reports, templates, checklists, etc.).",
    )
    add_common_args(sp_generate)


    sp_loc = subparsers.add_parser(
        "loc",
        help="Run a local model call via Ollama HTTP (OPSEC-sensitive lane).",
    )
    add_common_args(sp_loc)
    sp_loc.add_argument(
        "--model",
        help="Override local model (default: PROXMESH_LOCAL_MODEL or config).",
    )
    sp_loc.add_argument(
        "--ollama-base",
        help="Override Ollama base URL (default: PROXMESH_LOCAL_OLLAMA_BASE).",
    )

    sp_doctor = subparsers.add_parser(
        "doctor",
        help="Check tool availability + local Ollama connectivity.",
    )
    sp_doctor.add_argument(
        "--ollama-base",
        help="Override Ollama base URL (default: PROXMESH_LOCAL_OLLAMA_BASE).",
    )

    sp_prompt_kb = subparsers.add_parser(
        "prompt-kb",
        help="Produce a cloud-safe prompt pack from KB brief mode.",
    )
    sp_prompt_kb.add_argument(
        "prompt",
        nargs="*",
        help="Objective text. If omitted, can come from --file or stdin.",
    )
    sp_prompt_kb.add_argument(
        "-f",
        "--file",
        help="Read objective text from a file.",
    )
    sp_prompt_kb.add_argument(
        "--kb-query",
        help="Override the extracted KB query string (deterministic extraction otherwise).",
    )
    sp_prompt_kb.add_argument(
        "--host",
        help="Optional KB host target override.",
    )
    sp_prompt_kb.add_argument(
        "--sources",
        choices=["all", "books", "cpts", "htb"],
        help="Restrict KB sources.",
    )
    sp_prompt_kb.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit number of KB results (default: 10).",
    )
    sp_prompt_kb.add_argument(
        "--max-hints",
        type=int,
        default=5,
        help="Max hints to request (default: 5).",
    )
    sp_prompt_kb.add_argument(
        "--hint-length",
        type=int,
        default=120,
        help="Hint length (default: 120).",
    )
    sp_prompt_kb.add_argument(
        "--brief-length",
        type=int,
        default=1500,
        help="Brief length (default: 1500).",
    )
    sp_prompt_kb.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable local LLM augmentation in KB tool.",
    )
    sp_prompt_kb.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved KB command and log path without executing.",
    )
    sp_prompt_kb.add_argument(
        "--json",
        action="store_true",
        help="Print JSON only (no human-friendly text).",
    )
    sp_prompt_kb.add_argument(
        "--log-path",
        help="Write prompt KB JSON to this path (relative to repo root or absolute).",
    )

    sp_lab_pack = subparsers.add_parser(
        "lab-pack",
        help="Package lab state for cloud-safe KB brief mode via SSH.",
    )
    sp_lab_pack.add_argument(
        "prompt",
        nargs="*",
        help="Objective text. If omitted, can come from --file (stdin disabled when --state-file -).",
    )
    sp_lab_pack.add_argument(
        "-f",
        "--file",
        help="Read objective text from a file.",
    )
    sp_lab_pack.add_argument(
        "--state-file",
        required=True,
        help="Path to lab state file or '-' to read stdin.",
    )
    sp_lab_pack.add_argument(
        "--host",
        help="Optional KB host target override.",
    )
    sp_lab_pack.add_argument(
        "--sources",
        choices=["all", "books", "cpts", "htb"],
        help="Restrict KB sources.",
    )
    sp_lab_pack.add_argument(
        "--limit",
        type=int,
        help="Limit number of KB results.",
    )
    sp_lab_pack.add_argument(
        "--queries",
        type=int,
        help="How many KB queries to run for lab-pack.",
    )
    sp_lab_pack.add_argument(
        "--state-max-chars",
        type=int,
        help="Truncate state before sending upstream.",
    )
    sp_lab_pack.add_argument(
        "--max-hints",
        type=int,
        help="Max hints to request.",
    )
    sp_lab_pack.add_argument(
        "--hint-length",
        type=int,
        help="Hint length.",
    )
    sp_lab_pack.add_argument(
        "--brief-length",
        type=int,
        help="Brief length.",
    )
    sp_lab_pack.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable local LLM augmentation in KB tool.",
    )
    sp_lab_pack.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved KB command and log path without executing.",
    )
    sp_lab_pack.add_argument(
        "--json",
        action="store_true",
        help="Print JSON only (no human-friendly text).",
    )
    sp_lab_pack.add_argument(
        "--log-path",
        help="Write lab-pack JSON to this path (relative to repo root or absolute).",
    )

    def add_prompt_args(sp: argparse.ArgumentParser):
        sp.add_argument(
            "prompt",
            nargs="*",
            help="Objective text. If omitted, can come from --file or stdin.",
        )
        sp.add_argument(
            "-f",
            "--file",
            help="Read objective text from a file.",
        )
        sp.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the resolved KB command and plan log path without executing or logging.",
        )

    sp_plan_kb = subparsers.add_parser(
        "plan-kb",
        help="Generate an OPSEC-safe plan using KB metadata only (no snippets).",
    )
    add_prompt_args(sp_plan_kb)
    sp_plan_kb.add_argument(
        "--kb-query",
        help="Override the extracted KB query string (deterministic extraction otherwise).",
    )
    sp_plan_kb.add_argument(
        "--host",
        help="Optional KB host target override.",
    )
    sp_plan_kb.add_argument(
        "--sources",
        choices=["all", "books", "cpts", "htb"],
        help="Restrict KB sources.",
    )
    sp_plan_kb.add_argument(
        "--limit",
        type=int,
        help="Limit number of KB results.",
    )
    sp_plan_kb.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable local LLM augmentation in KB tool.",
    )
    sp_plan_kb.add_argument(
        "--no-snippets",
        action="store_true",
        default=True,
        help="Request KB metadata only (default: on).",
    )
    sp_plan_kb.add_argument(
        "--log-path",
        help="Write plan JSON to this path (relative to repo root or absolute).",
    )
    sp_plan_kb.add_argument(
        "--json",
        action="store_true",
        help="Print JSON only (no human-friendly text).",
    )

    sp_kb = subparsers.add_parser(
        "kb",
        help="Query local KB via kb_ask wrapper (Windows) and log results.",
    )
    sp_kb.add_argument(
        "prompt",
        nargs="*",
        help="KB query text. If omitted, can come from --file or stdin.",
    )
    sp_kb.add_argument(
        "-f",
        "--file",
        help="Read query text from a file.",
    )
    sp_kb.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved KB command without executing it.",
    )
    sp_kb.add_argument(
        "--no-log",
        action="store_true",
        help="Skip JSONL logging for this KB query.",
    )
    sp_kb.add_argument(
        "--log-path",
        default=str(DEFAULT_KB_LOG),
        help=f"Path to append KB query JSONL log (default: {DEFAULT_KB_LOG}).",
    )
    sp_kb.add_argument(
        "--host",
        help="Optional KB host target override.",
    )
    sp_kb.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable local LLM augmentation in kb_ask.",
    )
    sp_kb.add_argument(
        "--no-snippets",
        action="store_true",
        help="Suppress snippets in kb_ask output.",
    )
    sp_kb.add_argument(
        "--sources",
        choices=["all", "books", "cpts", "htb"],
        help="Restrict KB sources.",
    )
    sp_kb.add_argument(
        "--limit",
        type=int,
        help="Limit number of KB results.",
    )
    sp_kb.add_argument(
        "--raw",
        action="store_true",
        default=True,
        help="Request raw kb_ask output (default: true).",
    )
    sp_kb.add_argument(
        "--no-raw",
        action="store_false",
        dest="raw",
        help="Disable raw output passthrough.",
    )

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    route = args.command

    if (
        route == "lab-pack"
        and getattr(args, "state_file", None) == "-"
        and not args.prompt
        and not getattr(args, "file", None)
    ):
        print(
            "[prox-mesh] Objective is required when piping state via --state-file -. "
            "Provide positional text or --file while piping the state separately.",
            file=sys.stderr,
        )
        return 1

    if route == "doctor":
        return run_doctor(base_url=getattr(args, "ollama_base", None))

    allow_stdin_prompt = not (route == "lab-pack" and getattr(args, "state_file", None) == "-")
    prompt = read_prompt(args, allow_stdin=allow_stdin_prompt)

    if route == "loc":
        return run_local_ollama(
            prompt=prompt,
            model=getattr(args, "model", None),
            base_url=getattr(args, "ollama_base", None),
            dry_run=getattr(args, "dry_run", False),
            no_context=getattr(args, "no_context", False),
            with_brain=getattr(args, "with_brain", False),
            extra_context_file=getattr(args, "extra_context_file", None),
        )

    opsec = getattr(args, "opsec", None)
    if opsec in ("RES", "LOC") and route in {"plan", "research", "edit", "ask", "generate"}:
        print(f"[prox-mesh] OPSEC={opsec}: forcing local-only routing via Ollama.")
        return run_local_ollama(
            prompt=prompt,
            dry_run=getattr(args, "dry_run", False),
            no_context=getattr(args, "no_context", False),
            with_brain=getattr(args, "with_brain", False),
            extra_context_file=getattr(args, "extra_context_file", None),
        )


    if route == "prompt-kb":
        return run_prompt_kb(
            objective=prompt,
            kb_query_override=getattr(args, "kb_query", None),
            host=getattr(args, "host", None),
            sources=getattr(args, "sources", None),
            limit=getattr(args, "limit", None),
            max_hints=getattr(args, "max_hints", None),
            hint_length=getattr(args, "hint_length", None),
            brief_length=getattr(args, "brief_length", None),
            no_llm=getattr(args, "no_llm", False),
            dry_run=getattr(args, "dry_run", False),
            json_only=getattr(args, "json", False),
            log_path_str=getattr(args, "log_path", None),
        )

    if route == "lab-pack":
        return run_lab_pack(
            objective=prompt,
            state_file=args.state_file,
            host=args.host,
            sources=args.sources,
            limit=args.limit,
            queries=args.queries,
            state_max_chars=args.state_max_chars,
            max_hints=args.max_hints,
            hint_length=args.hint_length,
            brief_length=args.brief_length,
            no_llm=args.no_llm,
            dry_run=args.dry_run,
            json_only=args.json,
            log_path_str=args.log_path,
        )

    if route == "plan-kb":
        return run_plan_kb(
            objective=prompt,
            kb_query_override=args.kb_query,
            host=args.host,
            sources=args.sources,
            limit=args.limit,
            no_llm=args.no_llm,
            no_snippets=True,  # OPSEC-safe default; output redaction enforces too.
            dry_run=args.dry_run,
            json_only=args.json,
            plan_log_path_str=args.log_path,
        )

    if route == "kb":
        log_path = None if args.no_log else Path(args.log_path)
        return run_kb(
            query=prompt,
            dry_run=args.dry_run,
            log_path=log_path,
            host=args.host,
            no_llm=args.no_llm,
            no_snippets=args.no_snippets,
            sources=args.sources,
            limit=args.limit,
            raw=args.raw,
        )

    return run_route(
        route=route,
        prompt=prompt,
        dry_run=args.dry_run,
        no_context=args.no_context,
        with_brain=args.with_brain,
        extra_context_file=args.extra_context_file,
    )


if __name__ == "__main__":
    raise SystemExit(main())

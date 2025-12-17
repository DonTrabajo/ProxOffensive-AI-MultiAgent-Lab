#!/usr/bin/env python3
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
DEFAULT_KB_CMD: list[str] = ["python", r"C:\Users\Felix\bin\kb_ask.py", "--raw"]
DEFAULT_KB_LOG = Path(
    os.getenv("PROXMESH_KB_LOG", REPO_ROOT / "logs" / "kb_queries.jsonl")
)

DEFAULT_PLAN_KB_LOG_DIR = REPO_ROOT / "logs"


def parse_kb_cmd(env_value: str | None) -> list[str]:
    """
    Parse PROXMESH_KB_CMD into a list of argv tokens.

    Supports:
      a) JSON array: ["python", "C:\\Users\\Felix\\bin\\kb_ask.py", "--raw"]
      b) String command: python "C:\\Users\\Felix\\bin\\kb_ask.py" --raw

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


def read_prompt(args: argparse.Namespace) -> str:
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
    if not sys.stdin.isatty():
        content = sys.stdin.read().strip()
        if content:
            return content

    print(
        "[prox-mesh] No prompt provided. Use positional text, --file, or pipe content via stdin.",
        file=sys.stderr,
    )
    sys.exit(1)


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

    prompt = read_prompt(args)
    route = args.command

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

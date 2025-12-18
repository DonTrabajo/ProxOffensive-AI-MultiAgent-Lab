#!/usr/bin/env python3
"""
Repository-scoped KB wrapper for Windows -> Mac SSH bridge.

Behavior aligns with the legacy kb_ask.py in C:\\Users\\Felix\\bin but adds
`--brief cloud` support for cloud-safe prompt packs.
"""

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from typing import Any, Dict, List

DEFAULT_HOST = os.environ.get("KB_MAC_HOST", "felix-macbook.local")
REMOTE_CMD = os.environ.get("KB_REMOTE_CMD", "~/Documents/Prox_KB/cli/kb_query")


class KBError(Exception):
    pass


def _sanitize_host(host: str) -> str:
    """
    Allow simple aliases or explicit user@host; otherwise prefix felix@.
    """
    alias_pattern = r"[A-Za-z0-9_-]+"
    if "@" in host or re.fullmatch(alias_pattern, host):
        return host
    return f"felix@{host}"


def _build_lab_pack_args(objective: str, args: argparse.Namespace) -> List[str]:
    """
    Build remote kb_query arguments for lab-pack mode.
    """
    cmd = [REMOTE_CMD, "--lab-pack", objective, "--state-file", "-"]

    if args.sources:
        cmd.extend(["--sources", args.sources])
    if args.limit is not None:
        cmd.extend(["--limit", str(args.limit)])
    if args.queries is not None:
        cmd.extend(["--queries", str(args.queries)])
    if args.state_max_chars is not None:
        cmd.extend(["--state-max-chars", str(args.state_max_chars)])
    if args.max_hints is not None:
        cmd.extend(["--max-hints", str(args.max_hints)])
    if args.hint_length is not None:
        cmd.extend(["--hint-length", str(args.hint_length)])
    if args.brief_length is not None:
        cmd.extend(["--brief-length", str(args.brief_length)])
    if args.no_llm:
        cmd.append("--no-llm")

    cmd.append("--json")
    return cmd


def build_remote_args(query: str, args: argparse.Namespace) -> List[str]:
    """
    Build remote kb_query arguments while preserving legacy flags.
    """
    if args.lab_pack:
        return _build_lab_pack_args(args.lab_pack, args)

    cmd = [REMOTE_CMD]

    brief_mode = args.brief == "cloud"
    if brief_mode:
        cmd.extend(["--brief", "cloud"])
    else:
        if args.sources:
            cmd.extend(["--sources", args.sources])
        if args.limit is not None:
            cmd.extend(["--limit", str(args.limit)])
        if args.no_llm:
            cmd.append("--no-llm")
        if args.no_snippets:
            cmd.append("--no-snippets")
        cmd.append(query)
        return cmd

    # Brief cloud mode options
    if args.sources:
        cmd.extend(["--sources", args.sources])
    if args.limit is not None:
        cmd.extend(["--limit", str(args.limit)])
    if args.max_hints is not None:
        cmd.extend(["--max-hints", str(args.max_hints)])
    if args.hint_length is not None:
        cmd.extend(["--hint-length", str(args.hint_length)])
    if args.brief_length is not None:
        cmd.extend(["--brief-length", str(args.brief_length)])
    if args.no_llm:
        cmd.append("--no-llm")
    if args.no_snippets:
        cmd.append("--no-snippets")

    cmd.append("--json")
    cmd.append(query)  # positional arg at end
    return cmd


def run_remote(host: str, remote_args: List[str], stdin_bytes: bytes | None = None) -> subprocess.CompletedProcess:
    target = _sanitize_host(host)
    def _quote_remote(arg: str, is_cmd: bool) -> str:
        if is_cmd and arg.startswith("~") and " " not in arg:
            return arg
        return shlex.quote(arg)

    remote_cmd = " ".join(_quote_remote(arg, idx == 0) for idx, arg in enumerate(remote_args))
    ssh_cmd = [
        "ssh",
        "-T",
        "-o",
        "LogLevel=ERROR",
        "-o",
        "StrictHostKeyChecking=accept-new",
        target,
        "--",
        remote_cmd,
    ]

    run_kwargs: dict[str, Any] = {
        "capture_output": True,
        "timeout": 45,
    }
    if stdin_bytes is None:
        run_kwargs["text"] = True
    else:
        run_kwargs["input"] = stdin_bytes
        run_kwargs["text"] = False

    try:
        return subprocess.run(ssh_cmd, **run_kwargs)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            ssh_cmd,
            1,
            stdout="",
            stderr="kb_ask error: SSH command timed out after 45 seconds.\n",
        )


def parse_remote_output(proc: subprocess.CompletedProcess) -> Dict[str, Any]:
    if proc.stdout:
        stdout = proc.stdout
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            raise KBError("Remote output is not valid JSON")
    raise KBError("No output from remote command")


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Query Mac KB over SSH")
    parser.add_argument("query", nargs="?", help="Query string")
    parser.add_argument("--lab-pack", help="Objective text for lab-pack mode (state pushed over stdin)")
    parser.add_argument("--state-file", help="Path to lab state file or '-' to read stdin")
    parser.add_argument("--sources", choices=["all", "books", "cpts", "htb"], help="Source set")
    parser.add_argument("--limit", type=int, help="Max results")
    parser.add_argument("--queries", type=int, help="Max queries for lab-pack mode")
    parser.add_argument("--state-max-chars", type=int, help="Truncate state before sending (lab-pack)")
    parser.add_argument("--max-hints", type=int, help="Max hints for brief cloud mode")
    parser.add_argument("--hint-length", type=int, help="Hint length for brief cloud mode")
    parser.add_argument("--brief-length", type=int, help="Brief length for brief cloud mode")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM augmentation")
    parser.add_argument("--no-snippets", action="store_true", help="Suppress snippets in remote result")
    parser.add_argument("--raw", action="store_true", help="Emit raw JSON")
    parser.add_argument(
        "--brief",
        choices=["cloud"],
        help="Request brief mode (cloud pack).",
    )
    parser.add_argument("--host", help="SSH host or alias override (defaults to KB_MAC_HOST or felix-macbook.local)")

    args = parser.parse_args(argv)

    if args.lab_pack and not args.state_file:
        parser.error("--state-file is required when using --lab-pack")
    if not args.lab_pack and not args.query:
        parser.error("query is required unless --lab-pack is provided")
    if args.lab_pack and args.brief:
        parser.error("--brief is not supported with --lab-pack")

    host = args.host or DEFAULT_HOST
    remote_args = build_remote_args(args.query or "", args)

    stdin_bytes: bytes | None = None
    if args.lab_pack:
        if args.state_file == "-":
            if sys.stdin.isatty():
                sys.stderr.write(
                    "state-file '-' requires piped stdin. Example: "
                    "Get-Content -Raw state.md | prox-mesh lab-pack ... --state-file -\n"
                )
                return 1
            stdin_bytes = sys.stdin.buffer.read()
            if not stdin_bytes or not stdin_bytes.strip():
                sys.stderr.write("kb_ask error: state input is empty\n")
                return 1
        else:
            try:
                stdin_bytes = Path(args.state_file).read_bytes()
            except OSError as exc:
                sys.stderr.write(f"kb_ask error: could not read state file {args.state_file}: {exc}\n")
                return 1
            if stdin_bytes == b"":
                sys.stderr.write("kb_ask error: state input is empty\n")
                return 1

    proc = run_remote(host, remote_args, stdin_bytes=stdin_bytes)

    if proc.returncode != 0:
        if proc.stderr:
            stderr_text = proc.stderr.decode("utf-8", errors="replace") if isinstance(proc.stderr, bytes) else proc.stderr
            sys.stderr.write(stderr_text)
        return proc.returncode

    try:
        result = parse_remote_output(proc)
    except KBError as exc:
        sys.stderr.write(f"kb_ask error: {exc}\n")
        return 1
    if isinstance(result, dict) and "error" in result:
        sys.stderr.write(f"kb_ask error: {result.get('error')}\n")
        return 1

    # Always emit remote stdout verbatim for predictable callers.
    stdout_text = proc.stdout.decode("utf-8", errors="replace") if isinstance(proc.stdout, bytes) else proc.stdout
    sys.stdout.write(stdout_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

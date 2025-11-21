#!/usr/bin/env python3
"""
prox-mesh v0 — Prox Offensive Local Mesh Router

A thin CLI wrapper that routes high-level actions (plan, research, edit, ask, generate)
to underlying AI tools (Codex, Claude, Gemini, local LLMs, etc.).

Design goals:
- Keep it simple and dependency-free (only stdlib).
- Make the routing configurable via environment variables.
- Support dry-run so you can see what commands would be executed.
- Read prompts from CLI args, a file, or stdin.

Usage examples:

  # High-level planning (defaults to Claude CLI or configured tool)
  prox-mesh plan "Design a Slingshot-based engagement layout."

  # Research (defaults to Gemini CLI or configured tool)
  prox-mesh research "TLS downgrade attack latest techniques"

  # Edit a file with Codex (or configured editor tool)
  prox-mesh edit "Refactor docs/host_cli_setup.md to be clearer."

  # Ask a general question
  prox-mesh ask "Summarize the role of Slingshot in this repo."

  # Generate an artifact (e.g., report, checklist, template)
  prox-mesh generate "Create an internal recon checklist for recon.ops."
"""

import argparse
import os
import subprocess
import sys
from textwrap import dedent

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Default base commands for each route.
# These should be simple shell commands that accept a single trailing prompt.
# You can override each via environment variables to include context flags.
#
# For example, in PowerShell:
#   $env:PROXMESH_PLAN_CMD = 'claude --context claude.md'
#   $env:PROXMESH_RESEARCH_CMD = 'gemini --context gemini.md'
#   $env:PROXMESH_EDIT_CMD = 'codex --context codex.md'
#
# Then prox-mesh will append the prompt as a quoted argument:
#   claude --context claude.md "your prompt here"
#
DEFAULT_CMDS = {
    "plan": os.getenv("PROXMESH_PLAN_CMD", "claude"),
    "research": os.getenv("PROXMESH_RESEARCH_CMD", "gemini"),
    "edit": os.getenv("PROXMESH_EDIT_CMD", "codex"),
    "ask": os.getenv("PROXMESH_ASK_CMD", "claude"),
    "generate": os.getenv("PROXMESH_GENERATE_CMD", "codex"),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read().strip()
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
        "[prox-mesh] No prompt provided. Use positional text, --file, "
        "or pipe content via stdin.",
        file=sys.stderr,
    )
    sys.exit(1)


def build_command(base_cmd: str, prompt: str) -> str:
    """
    Build the full shell command string.

    NOTE: This is a simple implementation using shell=True later.
    We quote the prompt, but if your base_cmd already includes complex quoting,
    you may prefer to include `{prompt}` in PROXMESH_*_CMD and extend this logic.
    """
    # Basic escaping of double quotes in the prompt
    safe_prompt = prompt.replace('"', '\\"')
    return f'{base_cmd} "{safe_prompt}"'


def run_route(route: str, prompt: str, dry_run: bool = False) -> int:
    """
    Resolve the command for a route (plan, research, edit, ask, generate)
    and execute it (or print it in dry-run mode).
    """
    base_cmd = DEFAULT_CMDS.get(route)
    if not base_cmd:
        print(
            f"[prox-mesh] No base command configured for route '{route}'.",
            file=sys.stderr,
        )
        return 1

    full_cmd = build_command(base_cmd, prompt)

    if dry_run:
        print(f"[prox-mesh] (dry-run) Would run:\n  {full_cmd}")
        return 0

    print(f"[prox-mesh] Running route '{route}' with:\n  {full_cmd}")
    try:
        # shell=True to allow complex commands/aliases
        result = subprocess.run(full_cmd, shell=True)
        return result.returncode
    except KeyboardInterrupt:
        print("[prox-mesh] Interrupted by user.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"[prox-mesh] Error executing command: {e}", file=sys.stderr)
        return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prox-mesh",
        description="Prox Offensive local mesh router (v0).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(
            """
            Examples:

              prox-mesh plan "Design a Slingshot-based engagement layout."

              prox-mesh research "TLS downgrade attack latest techniques"

              prox-mesh edit "Refactor docs/host_cli_setup.md to be clearer."

              echo "Write a summary of docs/project_brain.md" | prox-mesh ask

            Environment overrides:

              PROXMESH_PLAN_CMD     # e.g. 'claude --context claude.md'
              PROXMESH_RESEARCH_CMD # e.g. 'gemini --context gemini.md'
              PROXMESH_EDIT_CMD     # e.g. 'codex --context codex.md'
              PROXMESH_ASK_CMD      # e.g. 'claude --context claude.md'
              PROXMESH_GENERATE_CMD # e.g. 'codex --context codex.md'
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

    # plan
    sp_plan = subparsers.add_parser(
        "plan",
        help="High-level planning (defaults to Claude or configured planner).",
    )
    add_common_args(sp_plan)

    # research
    sp_research = subparsers.add_parser(
        "research",
        help="Research via Gemini or configured research tool.",
    )
    add_common_args(sp_research)

    # edit
    sp_edit = subparsers.add_parser(
        "edit",
        help="File/content editing via Codex or configured editor.",
    )
    add_common_args(sp_edit)

    # ask
    sp_ask = subparsers.add_parser(
        "ask",
        help="General questions / explanations via Claude or configured tool.",
    )
    add_common_args(sp_ask)

    # generate
    sp_generate = subparsers.add_parser(
        "generate",
        help="Generate artifacts (reports, templates, checklists, etc.).",
    )
    add_common_args(sp_generate)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    prompt = read_prompt(args)
    route = args.command
    dry_run = getattr(args, "dry_run", False)

    return run_route(route, prompt, dry_run=dry_run)


if __name__ == "__main__":
    raise SystemExit(main())

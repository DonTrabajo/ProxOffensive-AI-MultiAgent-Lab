#!/usr/bin/env python3
"""
prox-mesh v1.0 — Prox Offensive Local Mesh Router

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
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

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

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    prompt = read_prompt(args)
    route = args.command

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

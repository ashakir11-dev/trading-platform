"""``trading-agent``: start the middleware agent, interactively or for one skill headless.

    trading-agent                      interactive session with the middleware agent
    trading-agent chat [claude args]   the same, passing extra arguments to Claude Code
    trading-agent init                 create workspace/, profile and .env from the examples
    trading-agent doctor [--online]    check this machine can run the pipeline
    trading-agent <skill> [args...]    run one skill headless, e.g. `trading-agent run
                                       --max-sectors 1 --shortlist 3` (for cron)

Global options (before the command): ``--model MODEL`` overrides the middleware's model; ``-v``/``--verbose`` prints each tool call to stderr.
"""

from __future__ import annotations

import asyncio
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from trading_agent import doctor
from trading_agent.env import find_root, load_env

AGENT = "middleware"
# Skills that ask the user questions, so they only make sense interactively.
INTERACTIVE_ONLY = frozenset({"setup"})
HEADLESS_ENV = {
    # Keeps a headless run from killing an agent that was started in the background.
    "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "0",
}


def skills(root: Path) -> list[str]:
    folder = root / ".claude" / "skills"
    return sorted(p.parent.name for p in folder.glob("*/SKILL.md")) if folder.is_dir() else []


def build_prompt(skill: str, args: list[str]) -> str:
    return f"/{skill} {shlex.join(args)}".rstrip()


def chat_command(cli: str, root: Path, extra: list[str], model: str | None = None) -> list[str]:
    command = [cli, "--agent", AGENT, "--mcp-config", str(root / ".mcp.json")]
    if model:
        command += ["--model", model]
    return command + extra


def project_permissions(root: Path) -> tuple[list[str], list[str]]:
    """The allow and deny lists of ``.claude/settings.json``."""
    try:
        permissions = json.loads((root / ".claude" / "settings.json").read_text(encoding="utf-8"))["permissions"]
    except (OSError, ValueError, KeyError, TypeError):
        return [], []
    return list(permissions.get("allow", [])), list(permissions.get("deny", []))


def headless_options(root: Path, model: str | None = None) -> dict[str, Any]:
    """Keyword arguments for ``ClaudeAgentOptions``: the project's settings (permissions,
    hooks), agents and skills, the Equibles server, and the middleware as the main agent.

    Claude Code ignores a project's allow rules until the folder has been trusted
    interactively, so on a fresh clone a headless run would be denied every tool the
    settings allow. The same lists are therefore passed explicitly; the hooks and the
    deny list apply either way."""
    allow, deny = project_permissions(root)
    options: dict[str, Any] = {
        "allowed_tools": allow,
        "disallowed_tools": deny,
        "cwd": str(root),
        "setting_sources": ["project", "local"],
        "skills": "all",
        "mcp_servers": str(root / ".mcp.json"),
        "permission_mode": "acceptEdits",
        "extra_args": {"agent": AGENT},
        "env": dict(HEADLESS_ENV),
    }
    if model:
        options["model"] = model
    if explicit := os.environ.get("TRADING_AGENT_CLAUDE"):
        options["cli_path"] = explicit
    return options


def cmd_init(root: Path) -> int:
    ws = root / "workspace"
    ws.mkdir(exist_ok=True)
    print(f"workspace: {ws}")
    profile = ws / "profile.json"
    if profile.exists():
        print(f"profile:   {profile} (kept)")
    else:
        shutil.copyfile(root / "profile.example.json", profile)
        print(f"profile:   {profile} (copied from profile.example.json; edit it, or run /setup)")
    env = root / ".env"
    if env.exists():
        print(f"keys:      {env} (kept)")
    elif (root / ".env.example").is_file():
        shutil.copyfile(root / ".env.example", env)
        try:
            env.chmod(0o600)
        except OSError:
            pass
        print(f"keys:      {env} (copied from .env.example; add your keys)")
    return 0


def cmd_doctor(root: Path, args: list[str]) -> int:
    checks = doctor.run_checks(root, online="--online" in args)
    for check in checks:
        print(check.line())
    failed = [c for c in checks if c.status == "FAIL"]
    print(f"\n{len(failed)} problem(s)." if failed else "\nReady.")
    return 1 if failed else 0


def cmd_chat(root: Path, extra: list[str], model: str | None = None) -> int:
    cli = doctor.claude_cli()
    if not cli:
        print("Claude Code not found: `pip install -e .` in the repository (or install the "
              "Claude Code CLI).", file=sys.stderr)
        return 1
    return subprocess.call(chat_command(cli, root, extra, model), cwd=root)


async def _run_headless(root: Path, prompt: str, model: str | None, verbose: bool) -> int:
    try:
        from claude_agent_sdk import (AssistantMessage, ClaudeAgentOptions, ResultMessage,
                                      TextBlock, ToolUseBlock, query)
    except ImportError:
        print("The Claude Agent SDK is not installed: `pip install -e .` in the repository.",
              file=sys.stderr)
        return 1
    started, code = time.monotonic(), 1
    async for message in query(prompt=prompt, options=ClaudeAgentOptions(**headless_options(root, model))):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock) and message.parent_tool_use_id is None:
                    print(block.text, flush=True)
                elif isinstance(block, ToolUseBlock) and verbose:
                    what = block.input.get("subagent_type") or block.input.get("description") or ""
                    print(f"  -> {block.name} {what}".rstrip(), file=sys.stderr, flush=True)
        elif isinstance(message, ResultMessage):
            code = 1 if message.is_error else 0
            cost = f", ${message.total_cost_usd:.2f}" if message.total_cost_usd else ""
            print(f"[{message.subtype} in {(time.monotonic() - started) / 60:.1f} min{cost}]",
                  file=sys.stderr)
    return code


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    model, verbose = None, False
    while argv and argv[0].startswith("-"):
        flag = argv.pop(0)
        if flag in ("-h", "--help"):
            print(__doc__)
            return 0
        if flag in ("-v", "--verbose"):
            verbose = True
        elif flag == "--model" and argv:
            model = argv.pop(0)
        else:
            print(f"unknown option {flag}\n{__doc__}", file=sys.stderr)
            return 2

    root = find_root()
    load_env(root)
    command, args = (argv[0], argv[1:]) if argv else ("chat", [])

    if command == "init":
        return cmd_init(root)
    if command == "doctor":
        return cmd_doctor(root, args)
    if command == "chat":
        return cmd_chat(root, args, model)
    available = skills(root)
    if command not in available:
        print(f"unknown command {command!r}. Commands: chat, init, doctor, "
              f"{', '.join(available)}", file=sys.stderr)
        return 2
    if command in INTERACTIVE_ONLY:
        print(f"/{command} asks questions: run `trading-agent` and type /{command} "
              "(or use `trading-agent init` and `trading-agent doctor`).", file=sys.stderr)
        return 2
    return asyncio.run(_run_headless(root, build_prompt(command, args), model, verbose))

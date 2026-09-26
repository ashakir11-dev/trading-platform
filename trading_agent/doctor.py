"""Checks that a machine can run the pipeline, each with the fix. Standard library only."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MIN_PYTHON = (3, 10)
PROFILE_KEYS = {
    "name": str, "risk_tolerance": str, "horizons": list, "allow_short": bool,
    "max_loss_per_trade_pct": (int, float), "min_reward_to_risk": (int, float),
    "target_return_pct": (int, float), "level_trigger": str, "notes": str,
}
HORIZONS = {"swing", "long_term"}
LEVEL_TRIGGERS = {"close", "intraday"}
REQUIRED_FILES = (
    ".claude/agents/middleware.md", ".claude/settings.json", ".claude/hooks/workspace_guard.py",
    ".mcp.json", "prompts/middleware/role.md", "profile.example.json",
)
CLAUDE_AUTH_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN",
                    "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX")


@dataclass
class Check:
    status: str          # ok | warn | FAIL
    name: str
    detail: str

    def line(self) -> str:
        return f"{self.status:<4}  {self.name}: {self.detail}"


def profile_problems(profile: Any) -> list[str]:
    """What is wrong with an investor profile (empty when it is valid)."""
    if not isinstance(profile, dict):
        return ["not a JSON object"]
    problems = []
    for key, kind in PROFILE_KEYS.items():
        if key not in profile:
            problems.append(f"missing {key}")
        elif not isinstance(profile[key], kind) or (kind is not bool and isinstance(profile[key], bool)):
            problems.append(f"{key} has the wrong type")
    if isinstance(profile.get("horizons"), list):
        if not profile["horizons"] or not set(profile["horizons"]) <= HORIZONS:
            problems.append(f"horizons must be a non-empty subset of {sorted(HORIZONS)}")
    if isinstance(profile.get("level_trigger"), str) and profile["level_trigger"] not in LEVEL_TRIGGERS:
        problems.append(f"level_trigger must be one of {sorted(LEVEL_TRIGGERS)}")
    for key in ("max_loss_per_trade_pct", "min_reward_to_risk"):
        value = profile.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value <= 0:
            problems.append(f"{key} must be positive")
    return problems


def claude_cli() -> str | None:
    """The Claude Code CLI to use: ``$TRADING_AGENT_CLAUDE``, else ``claude`` on the PATH,
    else the one bundled with the Claude Agent SDK."""
    if explicit := os.environ.get("TRADING_AGENT_CLAUDE"):
        return explicit
    if found := shutil.which("claude"):
        return found
    try:
        import claude_agent_sdk
    except ImportError:
        return None
    name = "claude.exe" if os.name == "nt" else "claude"
    bundled = Path(claude_agent_sdk.__file__).parent / "_bundled" / name
    return str(bundled) if bundled.is_file() else None


def equibles_url(root: Path) -> str | None:
    try:
        servers = json.loads((root / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]
        return servers["equibles"]["url"]
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _check_python() -> Check:
    have = sys.version_info[:2]
    if have < MIN_PYTHON:
        return Check("FAIL", "python", f"{have[0]}.{have[1]} found, {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ needed")
    return Check("ok", "python", f"{have[0]}.{have[1]}")


def _check_hook_python() -> Check:
    exe = shutil.which("python3")
    if not exe:
        return Check("FAIL", "python3 for hooks",
                     "`python3` is not on the PATH; the hooks in .claude/settings.json run it "
                     "(on Windows use WSL, or make `python3` point at Python 3.10+)")
    try:
        out = subprocess.run([exe, "-c", "import sys; print('%d.%d' % sys.version_info[:2])"],
                             capture_output=True, text=True, timeout=20).stdout.strip()
        major, minor = (int(x) for x in out.split("."))
    except (OSError, ValueError, subprocess.SubprocessError):
        return Check("FAIL", "python3 for hooks", f"{exe} did not run")
    if (major, minor) < MIN_PYTHON:
        return Check("FAIL", "python3 for hooks", f"{exe} is {out}; the hooks need 3.10+")
    return Check("ok", "python3 for hooks", f"{exe} ({out})")


def _check_files(root: Path) -> Check:
    missing = [f for f in REQUIRED_FILES if not (root / f).is_file()]
    if missing:
        return Check("FAIL", "repository", f"{root} is missing {', '.join(missing)}; "
                     "run from the repository or set TRADING_PLATFORM_HOME")
    return Check("ok", "repository", str(root))


def _check_claude() -> Check:
    cli = claude_cli()
    if not cli:
        return Check("FAIL", "claude code", "not found; `pip install -e .` installs the Claude Agent "
                     "SDK, which bundles it (or install the Claude Code CLI)")
    return Check("ok", "claude code", cli)


def _check_claude_auth(environ: dict[str, str]) -> Check:
    if found := [v for v in CLAUDE_AUTH_VARS if environ.get(v)]:
        return Check("ok", "claude auth", f"{found[0]} is set")
    if (Path.home() / ".claude" / ".credentials.json").is_file():
        return Check("ok", "claude auth", "Claude Code login found")
    return Check("warn", "claude auth", "no ANTHROPIC_API_KEY and no login file found; set the key in "
                 ".env, or run `claude` once and log in (on macOS the login lives in the keychain, "
                 "so this can be a false alarm)")


def _check_equibles_key(environ: dict[str, str]) -> Check:
    if environ.get("EQUIBLES_API_KEY"):
        return Check("ok", "equibles key", "EQUIBLES_API_KEY is set")
    return Check("FAIL", "equibles key", "EQUIBLES_API_KEY is not set; put it in .env at the "
                 "repository root (copy .env.example) or export it (Plus plan or better)")


def _check_equibles_online(root: Path, environ: dict[str, str]) -> Check:
    url = equibles_url(root)
    if not url:
        return Check("FAIL", "equibles server", ".mcp.json has no equibles url")
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {},
        "clientInfo": {"name": "trading-agent-doctor", "version": "1"}}}).encode()
    request = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json", "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {environ.get('EQUIBLES_API_KEY', '')}"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return Check("ok", "equibles server", f"{url} answered {response.status}")
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return Check("FAIL", "equibles server", f"{url} refused the key ({e.code})")
        return Check("warn", "equibles server", f"{url} answered {e.code}")
    except (urllib.error.URLError, OSError) as e:
        return Check("FAIL", "equibles server", f"{url} not reachable ({e}); allow network access to it")


def _check_git(root: Path) -> Check:
    if not shutil.which("git"):
        return Check("warn", "git", "not installed; runs record prompt_commit `unversioned` and "
                     "/approve adds lessons without a commit")
    ok = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).returncode == 0
    if not ok:
        return Check("warn", "git", "not a git checkout; runs record prompt_commit `unversioned` and "
                     "/approve adds lessons without a commit")
    return Check("ok", "git", "prompt versions are recorded")


def _check_workspace(root: Path) -> list[Check]:
    ws = root / "workspace"
    if not ws.is_dir():
        return [Check("warn", "workspace", f"{ws} does not exist yet; `trading-agent init` creates it")]
    if not os.access(ws, os.W_OK):
        return [Check("FAIL", "workspace", f"{ws} is not writable")]
    checks = [Check("ok", "workspace", str(ws))]
    profile = ws / "profile.json"
    if not profile.is_file():
        checks.append(Check("warn", "profile", "no workspace/profile.json; profile.example.json is "
                            "used (`trading-agent init` copies it, then edit it, or run /setup)"))
        return checks
    try:
        problems = profile_problems(json.loads(profile.read_text(encoding="utf-8")))
    except ValueError as e:
        problems = [f"invalid JSON ({e})"]
    if problems:
        checks.append(Check("FAIL", "profile", f"{profile}: {'; '.join(problems)}"))
    else:
        checks.append(Check("ok", "profile", str(profile)))
    return checks


def run_checks(root: Path, *, online: bool = False, environ: dict[str, str] | None = None) -> list[Check]:
    environ = dict(os.environ) if environ is None else environ
    checks = [_check_python(), _check_hook_python(), _check_files(root), _check_claude(),
              _check_claude_auth(environ), _check_equibles_key(environ)]
    if online:
        checks.append(_check_equibles_online(root, environ))
    checks.append(_check_git(root))
    checks.extend(_check_workspace(root))
    return checks

"""Tests for the standalone launcher (trading_agent/) and the agent and skill definitions."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from trading_agent import cli, doctor, env

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".claude" / "skills"
# Skills that record the user's own decisions, trades and approvals: only the user runs them.
USER_ONLY = {"decide", "trade", "approve"}


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path} has no frontmatter"
    return dict(line.split(": ", 1) for line in m.group(1).splitlines())


# --- definitions -------------------------------------------------------------------------

def test_no_leftover_commands():
    assert not (ROOT / ".claude" / "commands").exists()


@pytest.mark.parametrize("skill", sorted(p.name for p in SKILLS.iterdir()))
def test_skill_frontmatter(skill):
    fm = frontmatter(SKILLS / skill / "SKILL.md")
    assert fm["name"] == skill
    assert fm["description"]
    assert (fm.get("disable-model-invocation") == "true") == (skill in USER_ONLY)


def test_every_skill_is_the_middleware():
    for path in SKILLS.glob("*/SKILL.md"):
        assert "prompts/middleware/role.md" in path.read_text(encoding="utf-8"), path


def test_middleware_agent_lists_every_skill():
    text = (ROOT / ".claude" / "agents" / "middleware.md").read_text(encoding="utf-8")
    assert frontmatter(ROOT / ".claude" / "agents" / "middleware.md")["name"] == "middleware"
    for skill in cli.skills(ROOT):
        assert f"/{skill}" in text, skill


def test_example_profile_is_valid():
    assert doctor.profile_problems(json.loads((ROOT / "profile.example.json").read_text())) == []


# --- env -------------------------------------------------------------------------------

def test_parse_env():
    text = """
# comment
export EQUIBLES_API_KEY="abc def"
ANTHROPIC_API_KEY=sk-1  # trailing comment
EMPTY=
QUOTED='x#y'
not a line
"""
    assert env.parse_env(text) == {
        "EQUIBLES_API_KEY": "abc def", "ANTHROPIC_API_KEY": "sk-1", "EMPTY": "", "QUOTED": "x#y"}


def test_load_env_never_overrides(tmp_path, monkeypatch):
    monkeypatch.setattr(env, "USER_ENV_FILE", tmp_path / "missing")
    (tmp_path / ".env").write_text("A=from-file\nB=from-file\nC=\n")
    environ = {"A": "from-env"}
    assert env.load_env(tmp_path, environ) == [tmp_path / ".env"]
    assert environ == {"A": "from-env", "B": "from-file"}


def test_empty_values_do_not_shadow_the_user_file(tmp_path, monkeypatch):
    monkeypatch.setattr(env, "USER_ENV_FILE", tmp_path / "user-env")
    (tmp_path / ".env").write_text("EQUIBLES_API_KEY=\n")
    (tmp_path / "user-env").write_text("export EQUIBLES_API_KEY=k\n")
    environ = {}
    env.load_env(tmp_path, environ)
    assert environ == {"EQUIBLES_API_KEY": "k"}


def test_find_root(tmp_path, monkeypatch):
    monkeypatch.delenv("TRADING_PLATFORM_HOME", raising=False)
    (tmp_path / ".claude" / "agents").mkdir(parents=True)
    (tmp_path / ".claude" / "agents" / "middleware.md").write_text("x")
    (tmp_path / "a" / "b").mkdir(parents=True)
    assert env.find_root(tmp_path / "a" / "b") == tmp_path.resolve()
    monkeypatch.setenv("TRADING_PLATFORM_HOME", str(tmp_path / "a"))
    assert env.find_root(tmp_path) == (tmp_path / "a").resolve()


# --- cli -------------------------------------------------------------------------------

def test_skills_found():
    assert {"run", "run-agent", "backtest", "decide", "trade", "follow-up", "evaluate",
            "feedback", "approve", "setup", "status"} <= set(cli.skills(ROOT))


def test_build_prompt():
    assert cli.build_prompt("run", []) == "/run"
    assert cli.build_prompt("run", ["--max-sectors", "1"]) == "/run --max-sectors 1"
    assert cli.build_prompt("decide", ["X-1", "accept", "half size"]) == "/decide X-1 accept 'half size'"


def test_chat_command():
    assert cli.chat_command("claude", ROOT, ["-c"], "m") == [
        "claude", "--agent", "middleware", "--mcp-config", str(ROOT / ".mcp.json"), "--model", "m", "-c"]


def test_headless_options_carry_project_permissions(monkeypatch):
    monkeypatch.delenv("TRADING_AGENT_CLAUDE", raising=False)
    options = cli.headless_options(ROOT)
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text())["permissions"]
    # Passed explicitly: an untrusted clone ignores the settings' allow list.
    assert options["allowed_tools"] == settings["allow"]
    assert options["disallowed_tools"] == settings["deny"]
    assert options["extra_args"] == {"agent": "middleware"}
    assert options["mcp_servers"] == str(ROOT / ".mcp.json")
    assert options["cwd"] == str(ROOT)
    assert options["env"]["CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"] == "0"
    assert "model" not in options
    assert cli.headless_options(ROOT, "claude-sonnet-5")["model"] == "claude-sonnet-5"


def test_equibles_writes_denied_headless():
    deny = cli.headless_options(ROOT)["disallowed_tools"]
    for tool in ("CreateMyPortfolio", "AddPortfolioLot", "WatchInstrument"):
        assert f"mcp__equibles__{tool}" in deny


def test_init(tmp_path, capsys):
    for name in ("profile.example.json", ".env.example"):
        (tmp_path / name).write_text((ROOT / name).read_text())
    assert cli.cmd_init(tmp_path) == 0
    assert json.loads((tmp_path / "workspace" / "profile.json").read_text())["name"] == "example"
    assert (tmp_path / ".env").read_text() == (ROOT / ".env.example").read_text()
    (tmp_path / "workspace" / "profile.json").write_text("{}")
    cli.cmd_init(tmp_path)
    assert (tmp_path / "workspace" / "profile.json").read_text() == "{}"   # kept


def test_unknown_and_interactive_only_commands(capsys):
    assert cli.main(["no-such-skill"]) == 2
    assert cli.main(["setup"]) == 2
    assert cli.main(["--bogus"]) == 2


# --- doctor ----------------------------------------------------------------------------

def test_profile_problems():
    good = json.loads((ROOT / "profile.example.json").read_text())
    assert doctor.profile_problems(good) == []
    assert doctor.profile_problems([]) == ["not a JSON object"]
    bad = good | {"horizons": ["day"], "level_trigger": "open", "allow_short": "no",
                  "max_loss_per_trade_pct": 0}
    problems = doctor.profile_problems(bad)
    assert any("horizons" in p for p in problems)
    assert any("level_trigger" in p for p in problems)
    assert "allow_short has the wrong type" in problems
    assert "max_loss_per_trade_pct must be positive" in problems
    assert "missing notes" in doctor.profile_problems({k: v for k, v in good.items() if k != "notes"})


def statuses(checks):
    return {c.name: c.status for c in checks}


def test_doctor_keys_and_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(doctor.Path, "home", lambda: tmp_path / "home")
    s = statuses(doctor.run_checks(tmp_path, environ={}))
    assert s["equibles key"] == "FAIL"
    assert s["claude auth"] == "warn"
    assert s["repository"] == "FAIL"
    assert s["workspace"] == "warn"
    (tmp_path / "workspace").mkdir()
    (tmp_path / "workspace" / "profile.json").write_text("{not json")
    s = statuses(doctor.run_checks(tmp_path, environ={"EQUIBLES_API_KEY": "k", "ANTHROPIC_API_KEY": "k"}))
    assert s["equibles key"] == s["claude auth"] == s["workspace"] == "ok"
    assert s["profile"] == "FAIL"


def test_doctor_on_this_repository():
    s = statuses(doctor.run_checks(ROOT, environ={"EQUIBLES_API_KEY": "k"}))
    assert s["python"] == s["repository"] == "ok"

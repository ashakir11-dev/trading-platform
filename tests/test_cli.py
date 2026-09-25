"""End-to-end CLI tests: ``main([...])`` with injected fake providers and the scripted LLM."""

from __future__ import annotations

import json
import logging
import re
import sys
import types
from datetime import timedelta

import pytest

from trading_pipeline import app as app_mod
from trading_pipeline.app import ADAPTERS, Settings, build_providers, equibles_providers, open_middleware
from trading_pipeline.cli import main, parse_when
from trading_pipeline.data.equibles import EQUIBLES_MCP_URL, FACT_TOOL, EquiblesFundamentals
from trading_pipeline.data.gaps import UnavailableFilings, UnavailableMacro, UnavailableNews, UnavailableSectorData
from trading_pipeline.schemas import FullReviewOutput, MarketScanOutput, ProcessReviewOutput
from trading_pipeline.store import Store

from .fakes import AS_OF, FixturePrices, ScriptedLLM, make_bars, providers, reasoning

OPEN = AS_OF + timedelta(hours=1)


class Env:
    """One CLI 'installation': a temp database, fake data, scripted LLM and a settable clock."""

    def __init__(self, tmp_path, closes=(100, 95, 88)) -> None:
        self.db = tmp_path / "state" / "pipeline.sqlite3"
        self.env = {"TRADING_DB": str(self.db)}
        self.bars = make_bars(list(closes), OPEN)
        self.llm = ScriptedLLM()
        self.data = providers(prices=FixturePrices({"AAA": self.bars}))
        self.now = AS_OF + timedelta(minutes=5)

    def __call__(self, *argv: str, **kw) -> int:
        kw = {"env": self.env, "providers": self.data, "llm": self.llm, "clock": lambda: self.now, **kw}
        return main(list(argv), **kw)

    def store(self) -> Store:
        return Store(self.db)


def out_of(capsys) -> str:
    return capsys.readouterr().out


def candidate_id(text: str) -> str:
    m = re.search(r"candidate_id=(\w+)", text)
    assert m, text
    return m.group(1)


def test_full_workflow(tmp_path, capsys):
    cli = Env(tmp_path)

    # run: prints the report, persists it, creates the db directory.
    assert cli("run") == 0
    out = out_of(capsys)
    assert "AAA" in out and "trading-pipeline decide" in out and "Middleware.record_decision" not in out
    assert cli.db.exists()
    cid = candidate_id(out)
    run_id = re.search(r"Pipeline run (\w+)", out).group(1)
    assert "live quote: 101.5" in out  # as-of today -> live run

    # report: latest by default, or by run id.
    assert cli("report") == 0 and cid in out_of(capsys)
    assert cli("report", run_id) == 0 and run_id in out_of(capsys)

    # decide accept -> one open position.
    cli.now = OPEN
    assert cli("decide", cid, "accept", "--note", "sized small") == 0
    out = out_of(capsys)
    pid = re.search(r"Watching position (\w+)", out).group(1)
    assert "never places orders" in out

    # A second decision for the same candidate is refused.
    assert cli("decide", cid, "reject") == 1
    assert "already recorded" in capsys.readouterr().err

    assert cli("positions") == 0
    out = out_of(capsys)
    assert pid in out and "entry 100.0, target 120.0, stop 90.0" in out

    # follow-up: price closes through the stop -> alert, re-review, action needed.
    cli.now = cli.bars[-1].ts
    assert cli("follow-up") == 0
    out = out_of(capsys)
    assert "[ALERT]" in out and "stop 90.0" in out and "re-review: hold" in out
    assert "ACTION NEEDED" in out and "hit its stop" in out and f"trading-pipeline close {pid}" in out

    # A later tick within the 12h cooldown: nothing alerts; --quiet prints nothing.
    cli.now += timedelta(hours=1)
    assert cli("follow-up", "--quiet") == 0
    assert out_of(capsys) == ""

    # close, then review (outcome + process review creates an unapproved note).
    assert cli("close", pid, "--price", "88", "--date", cli.bars[-1].ts.isoformat()) == 0
    assert f"trading-pipeline review {pid}" in out_of(capsys)
    assert cli("close", pid, "--price", "88") == 1
    assert "already closed" in capsys.readouterr().err
    assert cli("positions") == 0 and "No open positions." in out_of(capsys)

    assert cli("review", pid) == 0
    out = out_of(capsys)
    assert "-12.00%" in out and "hit stop: yes" in out and "not_a_loss" in out
    note_id = re.search(r"^\s+(\w+)\s+\[market_scan\] check rate sensitivity", out, re.M).group(1)

    # The process reviewer never saw the user's decision or its note.
    assert cli.llm.prompts(ProcessReviewOutput)
    assert all("sized small" not in p for _, s, p in cli.llm.calls for p in (s, p))

    # notes -> approve -> no longer pending, listed with --all.
    assert cli("notes") == 0 and note_id in out_of(capsys)
    assert cli("approve-note", note_id) == 0 and "Approved" in out_of(capsys)
    assert cli("approve-note", note_id) == 0 and "already approved" in out_of(capsys)
    assert cli("notes") == 0 and "No notes pending approval." in out_of(capsys)
    assert cli("notes", "--all") == 0 and "[approved]" in out_of(capsys)
    assert [n.approved for n in cli.store().improvements(approved_only=False)] == [True]


def test_follow_up_exit_recommendation_and_quiet(tmp_path, capsys):
    cli = Env(tmp_path, closes=(100, 101, 102))
    cli.llm.handlers[FullReviewOutput] = lambda p: FullReviewOutput(
        ticker="AAA", action="exit", thesis_intact=False, updated_plan=None, reasoning=reasoning("thesis broken"))
    cli("run")
    cid = candidate_id(out_of(capsys))
    cli.now = OPEN
    cli("decide", cid, "accept")
    capsys.readouterr()

    # Quiet tick: price inside the plan, no review due -> --quiet prints nothing.
    cli.now = cli.bars[1].ts
    assert cli("follow-up", "--quiet") == 0 and out_of(capsys) == ""
    assert cli("follow-up") == 0 and "[ok]" in out_of(capsys)

    # Full-review interval elapsed -> re-review runs; no alert, so no action prompt.
    cli.now = OPEN + timedelta(days=15)
    assert cli("follow-up", "--quiet") == 0
    out = out_of(capsys)
    assert "re-review: exit (thesis intact: no)" in out and "ACTION NEEDED" not in out


def test_reject_decision_creates_no_position(tmp_path, capsys):
    cli = Env(tmp_path)
    cli("run")
    cid = candidate_id(out_of(capsys))
    assert cli("decide", cid, "reject", "--note", "too risky") == 0
    assert "rejected" in out_of(capsys)
    assert cli.store().open_positions() == []
    assert cli("follow-up") == 0 and "No open positions." in out_of(capsys)


def test_backtest_and_past_dates(tmp_path, capsys):
    cli = Env(tmp_path)
    cli.now = AS_OF + timedelta(days=30)
    assert cli("run", "--as-of", "2026-06-01") == 0
    captured = capsys.readouterr()
    assert "running as a backtest" in captured.err and "live quote" not in captured.out
    assert "as of 2026-06-01T20:00:00+00:00" in captured.out

    assert cli("run", "--as-of", "2026-07-15") == 1
    assert "in the future" in capsys.readouterr().err


def test_errors(tmp_path, capsys):
    cli = Env(tmp_path)
    assert cli("report") == 1 and "no saved reports" in capsys.readouterr().err
    assert cli("report", "nope") == 1 and "no saved report for run nope" in capsys.readouterr().err
    assert cli("decide", "nope", "accept") == 1 and "not a recommended candidate" in capsys.readouterr().err
    assert cli("close", "nope", "--price", "1") == 1 and "unknown position id" in capsys.readouterr().err
    assert cli("review", "nope") == 1 and "unknown position id" in capsys.readouterr().err
    assert cli("approve-note", "nope") == 1 and "unknown note id" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        cli("decide", "x", "maybe")
    with pytest.raises(SystemExit):
        cli("run", "--as-of", "yesterday")


def test_missing_api_keys(tmp_path, capsys):
    env = {"TRADING_DB": str(tmp_path / "db.sqlite3")}
    # No injected LLM: the Anthropic key is required.
    assert main(["run"], env=env) == 1
    assert "ANTHROPIC_API_KEY is not set" in capsys.readouterr().err
    # LLM present but no injected providers: the Equibles key is required.
    assert main(["run"], env=env, llm=ScriptedLLM()) == 1
    assert "EQUIBLES_API_KEY is not set" in capsys.readouterr().err
    # Store-only commands need no keys.
    assert main(["positions"], env=env) == 0


def test_profile_commands(tmp_path, capsys):
    good = tmp_path / "profile.json"
    good.write_text(json.dumps({"name": "me", "horizons": ["swing"], "max_loss_per_trade_pct": 7}))
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"horizons": ["day_trading"]}))
    env = {"TRADING_DB": str(tmp_path / "db.sqlite3")}

    assert main(["profile", "show"], env=env) == 0
    out = out_of(capsys)
    assert "built-in default" in out and '"name": "default"' in out
    assert main(["profile", "show"], env={**env, "TRADING_PROFILE": str(good)}) == 0
    assert '"name": "me"' in out_of(capsys)
    assert main(["profile", "validate", str(good)]) == 0 and "OK" in out_of(capsys)
    assert main(["profile", "validate", str(bad)]) == 1 and "invalid profile" in capsys.readouterr().err
    assert main(["profile", "validate", str(tmp_path / "missing.json")]) == 1
    assert "not found" in capsys.readouterr().err


async def test_profile_and_llm_overrides_reach_config(tmp_path):
    good = tmp_path / "profile.json"
    good.write_text(json.dumps({"name": "me", "allow_short": True}))
    s = Settings.from_env({"TRADING_PROFILE": str(good), "TRADING_EFFORT": "low"}, db=str(tmp_path / "x.db"),
                          model="claude-test")
    cfg = s.pipeline_config()
    assert cfg.profile.allow_short and cfg.llm.model == "claude-test" and cfg.llm.effort == "low"
    assert Settings.from_env({}).db_path.name == "pipeline.sqlite3"
    async with open_middleware(s, online=False) as mw:
        assert mw.config.profile.name == "me"


def test_parse_when():
    assert parse_when("2026-06-01") == AS_OF  # 16:00 New York (EDT) = 20:00 UTC
    assert parse_when("2026-01-05").hour == 21  # EST
    assert parse_when("2026-06-01T12:00:00") == AS_OF - timedelta(hours=8)


# --------------------------------------------------------------------------------------
# Wiring: adapter loading, gap fallback, allowlist
# --------------------------------------------------------------------------------------

ADAPTER_MODULES = sorted({s.module for s in ADAPTERS if s.module != "trading_pipeline.data.equibles"})


def _fake_adapter(name: str, tools: set[str]):
    class Adapter:
        TOOLS = frozenset(tools)

        def __init__(self, mcp) -> None:
            self.mcp = mcp

    Adapter.__name__ = name
    return Adapter


def test_build_providers_falls_back_to_gaps_when_adapters_missing(monkeypatch, caplog):
    for mod in ADAPTER_MODULES:
        monkeypatch.setitem(sys.modules, mod, None)  # import raises ModuleNotFoundError
    mcp = object()
    with caplog.at_level(logging.WARNING, logger="trading_pipeline.app"):
        data, tools = build_providers(mcp)
    assert isinstance(data.fundamentals, EquiblesFundamentals)
    assert tools == {FACT_TOOL}
    assert isinstance(data.prices, app_mod.UnavailablePrices) and isinstance(data.quotes, app_mod.UnavailableQuotes)
    assert isinstance(data.sectors, UnavailableSectorData) and isinstance(data.news, UnavailableNews)
    assert isinstance(data.filings, UnavailableFilings) and isinstance(data.macro, UnavailableMacro)
    for field in ("prices", "quotes", "sectors", "news", "filings", "macro"):
        assert any(r.message.startswith(f"{field}: adapter module") for r in caplog.records), field


def test_build_providers_uses_adapters_and_unions_tools(monkeypatch):
    classes = {
        "trading_pipeline.data.equibles_prices": {"EquiblesPrices": {"GetStockPrices"},
                                                  "EquiblesQuotes": {"GetQuote"}},
        "trading_pipeline.data.equibles_sectors": {"EquiblesSectors": {"Screen"}},
        "trading_pipeline.data.equibles_events": {"EquiblesNews": {"ListFilings"},
                                                  "EquiblesFilings": {"ListFilings", "SearchDocuments"}},
        "trading_pipeline.data.equibles_macro": {"EquiblesMacro": {"GetEconomicIndicator"}},
    }
    for mod, members in classes.items():
        m = types.ModuleType(mod)
        for name, tools in members.items():
            setattr(m, name, _fake_adapter(name, tools))
        monkeypatch.setitem(sys.modules, mod, m)
    mcp = object()
    data, tools = build_providers(mcp)
    assert tools == {FACT_TOOL, "GetStockPrices", "GetQuote", "Screen", "ListFilings", "SearchDocuments",
                     "GetEconomicIndicator"}
    assert type(data.prices).__name__ == "EquiblesPrices" and data.prices.mcp is mcp
    assert type(data.filings).__name__ == "EquiblesFilings" and type(data.macro).__name__ == "EquiblesMacro"
    assert app_mod.adapter_tools() == tools

    # A module that exists but lacks the class also falls back.
    monkeypatch.setitem(sys.modules, "trading_pipeline.data.equibles_macro",
                        types.ModuleType("trading_pipeline.data.equibles_macro"))
    data, tools = build_providers(mcp)
    assert isinstance(data.macro, UnavailableMacro) and "GetEconomicIndicator" not in tools


async def test_equibles_providers_opens_allowlisted_client(monkeypatch):
    for mod in ADAPTER_MODULES:
        monkeypatch.setitem(sys.modules, mod, None)
    opened = {}

    class FakeClient:
        def __init__(self, url, *, allowed_tools, headers=None):
            opened.update(url=url, allowed=set(allowed_tools), headers=headers)

        async def __aenter__(self):
            opened["entered"] = True
            return self

        async def __aexit__(self, *exc):
            opened["exited"] = True

    monkeypatch.setattr(app_mod, "HttpMcpClient", FakeClient)
    settings = Settings.from_env({"EQUIBLES_API_KEY": "k123"}, db=":memory:")
    async with equibles_providers(settings) as data:
        assert isinstance(data.fundamentals, EquiblesFundamentals)
    assert opened == {"url": EQUIBLES_MCP_URL, "allowed": {FACT_TOOL},
                      "headers": {"Authorization": "Bearer k123"}, "entered": True, "exited": True}


def test_cli_run_through_real_wiring(monkeypatch, capsys):
    """Real wiring with a fake MCP transport and no adapters: everything but fundamentals is a gap."""
    for mod in ADAPTER_MODULES:
        monkeypatch.setitem(sys.modules, mod, None)

    class FakeClient:
        def __init__(self, url, *, allowed_tools, headers=None):
            self.allowed = set(allowed_tools)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            pass

        async def call_tool(self, name, arguments):
            assert name in self.allowed
            return "no data"

    monkeypatch.setattr(app_mod, "HttpMcpClient", FakeClient)
    llm = ScriptedLLM()
    code = main(["--db", ":memory:", "run", "--backtest", "--as-of", "2026-06-01"],
                env={"EQUIBLES_API_KEY": "k123"}, llm=llm, clock=lambda: AS_OF)
    assert code == 0 and "UNAVAILABLE" in llm.prompts(MarketScanOutput)[0]

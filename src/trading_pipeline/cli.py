"""Command-line interface: ``trading-pipeline <command>``. See docs/operations.md.

Decision support only: no command places, modifies or cancels orders. ``decide`` and
``close`` only record what *you* decided or did; decisions never reach any agent.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from collections.abc import Callable
from datetime import datetime, time, timezone
from typing import Any
from zoneinfo import ZoneInfo

from .app import ConfigError, Settings, load_profile, open_middleware
from .data.base import DataProviders
from .llm import LLMClient
from .middleware import render_report
from .schemas import PipelineReport, Position
from .store import Store

EASTERN = ZoneInfo("America/New_York")
MARKET_CLOSE = time(16, 0)


class CliError(Exception):
    """User-facing error: printed as ``error: <message>``, exit code 1."""


def parse_when(text: str) -> datetime:
    """``YYYY-MM-DD`` means that day's US market close (16:00 New York); a full ISO
    datetime is taken as given (UTC if it has no offset)."""
    try:
        if len(text) == 10:
            day = datetime.strptime(text, "%Y-%m-%d").date()
            return datetime.combine(day, MARKET_CLOSE, tzinfo=EASTERN).astimezone(timezone.utc)
        dt = datetime.fromisoformat(text)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"not a date (YYYY-MM-DD) or ISO datetime: {text!r}") from e
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="trading-pipeline",
        description="Multi-agent trading research pipeline. Decision support only: it never places orders.")
    p.add_argument("--db", help="SQLite database path (env TRADING_DB, default ~/.trading-platform/pipeline.sqlite3)")
    p.add_argument("--profile", help="investor profile JSON (env TRADING_PROFILE, default: built-in profile)")
    p.add_argument("--model", help="LLM model override (env TRADING_MODEL)")
    p.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"],
                   help="LLM effort override (env TRADING_EFFORT)")
    p.add_argument("-v", "--verbose", action="store_true", help="log progress to stderr")
    sub = p.add_subparsers(dest="command", required=True, metavar="COMMAND")

    run = sub.add_parser("run", help="run the pipeline and print the report")
    run.add_argument("--as-of", type=parse_when,
                     help="YYYY-MM-DD (that day's close) or ISO datetime; default: now")
    run.add_argument("--backtest", action="store_true",
                     help="point-in-time run: no live quotes (implied for past dates)")

    rep = sub.add_parser("report", help="show a saved report (latest by default)")
    rep.add_argument("run_id", nargs="?")

    dec = sub.add_parser("decide", help="record your accept/reject for a recommended candidate")
    dec.add_argument("candidate_id")
    dec.add_argument("decision", choices=["accept", "reject"])
    dec.add_argument("--note", default="", help="free-text note (stored apart; never shown to agents)")
    dec.add_argument("--opened", type=parse_when, help="when you entered the trade (default: now)")

    sub.add_parser("positions", help="list open positions with their plan levels")

    fu = sub.add_parser("follow-up", help="one Agent 5 tick over all open positions (for cron)")
    fu.add_argument("--quiet", action="store_true",
                    help="print only alerts, reviews and needed actions (nothing when all is quiet)")

    cl = sub.add_parser("close", help="record that you exited a position")
    cl.add_argument("position_id")
    cl.add_argument("--price", type=float, required=True, help="your exit price")
    cl.add_argument("--date", type=parse_when, help="exit date/time (default: now)")

    rv = sub.add_parser("review", help="outcome + process review of a position")
    rv.add_argument("position_id")

    nt = sub.add_parser("notes", help="list improvement notes (pending approval by default)")
    nt.add_argument("--all", action="store_true", help="include approved notes")

    ap = sub.add_parser("approve-note", help="approve an improvement note so future prompts use it")
    ap.add_argument("note_id")

    pr = sub.add_parser("profile", help="show or validate an investor profile")
    prs = pr.add_subparsers(dest="profile_command", required=True, metavar="ACTION")
    prs.add_parser("show", help="print the effective profile")
    pv = prs.add_parser("validate", help="check a profile JSON file")
    pv.add_argument("path")
    return p


class _Cli:
    def __init__(self, args: argparse.Namespace, settings: Settings, providers: DataProviders | None,
                 llm: LLMClient | None, clock: Callable[[], datetime]) -> None:
        self.args = args
        self.settings = settings
        self.providers = providers
        self.llm = llm
        self.clock = clock
        self._store: Store | None = None

    @property
    def store(self) -> Store:
        if self._store is None:
            self._store = self.settings.open_store()
        return self._store

    def _mw(self, online: bool):
        return open_middleware(self.settings, online=online, store=self.store, providers=self.providers,
                               llm=self.llm)

    def _position(self, position_id: str) -> Position:
        pos = self.store.position(position_id)
        if pos is None:
            raise CliError(f"unknown position id: {position_id} (see `trading-pipeline positions`)")
        return pos

    # -- commands -------------------------------------------------------------------------

    async def run(self) -> None:
        now = self.clock()
        as_of = self.args.as_of or now
        if as_of > now:
            raise CliError(f"--as-of {as_of.isoformat()} is in the future")
        live = not self.args.backtest
        if live and as_of.astimezone(EASTERN).date() < now.astimezone(EASTERN).date():
            print("note: --as-of is a past date; running as a backtest (live quotes are not point-in-time).",
                  file=sys.stderr)
            live = False
        async with self._mw(online=True) as mw:
            report = await mw.run(as_of, live=live)
        self.store.save_report(report)
        self._print_report(report)
        print(f"\nSaved as run {report.run_id}; show again with: trading-pipeline report {report.run_id}")

    def _print_report(self, report: PipelineReport) -> None:
        print(render_report(report))

    def report(self) -> None:
        run_id = self.args.run_id
        report = self.store.report(run_id) if run_id else self.store.latest_report()
        if report is None:
            raise CliError(f"no saved report for run {run_id}" if run_id else "no saved reports yet; use `run`")
        self._print_report(report)

    async def decide(self) -> None:
        a = self.args
        async with self._mw(online=False) as mw:
            try:
                pos = mw.record_decision(a.candidate_id, a.decision == "accept", note=a.note,
                                         opened_at=a.opened or self.clock())
            except ValueError as e:
                raise CliError(str(e)) from e
        if pos is None:
            print(f"Recorded: rejected {a.candidate_id}.")
            return
        print(f"Recorded: accepted {a.candidate_id}. Watching position {pos.id} ({pos.ticker}).")
        print(_plan_line(pos))
        print("Trade it yourself; the system never places orders. `follow-up` will watch it.")

    def positions(self) -> None:
        open_ = self.store.open_positions()
        if not open_:
            print("No open positions.")
            return
        for pos in open_:
            last = pos.last_full_review_at.isoformat() if pos.last_full_review_at else "never"
            tw = self.store.last_tripwire(pos.id)
            price = f", last price {tw.last_price}" if tw and tw.last_price is not None else ""
            print(f"{pos.id}  {pos.ticker} ({pos.sector})  opened {pos.opened_at.isoformat()}{price}")
            print(_plan_line(pos))
            print(f"    last full review: {last}")

    async def follow_up(self) -> None:
        now = self.clock()
        if not self.store.open_positions():
            if not self.args.quiet:
                print("No open positions.")
            return
        async with self._mw(online=True) as mw:
            events = await mw.follow_up_loop().tick(now)
        for ev in events:
            t = ev.tripwire
            quiet = not (t.alerted or ev.review or ev.action_needed)
            if quiet and self.args.quiet:
                continue
            status = "ALERT" if t.alerted else ("tripped (held: alert cooldown)" if t.tripped else "ok")
            print(f"{ev.ticker}  position {ev.position_id}  [{status}]  last price {t.last_price}")
            for reason in t.reasons:
                print(f"    - {reason}")
            if ev.review is not None:
                r = ev.review
                print(f"    re-review: {r.action} (thesis intact: {'yes' if r.thesis_intact else 'no'}) "
                      f"— {r.reasoning.summary}")
                if r.updated_plan is not None:
                    p = r.updated_plan
                    print(f"    suggested plan: entry {p.entry_price}, target {p.target_price}, stop {p.stop_loss}")
            if ev.action_needed:
                print(f"    ACTION NEEDED: {ev.action_needed}")
                print(f"    -> trading-pipeline close {ev.position_id} --price PRICE; "
                      f"then trading-pipeline review {ev.position_id}")

    async def close(self) -> None:
        a = self.args
        pos = self._position(a.position_id)
        if pos.status != "open":
            raise CliError(f"position {pos.id} is already closed")
        closed_at = a.date or self.clock()
        if closed_at < pos.opened_at:
            raise CliError(f"close date {closed_at.isoformat()} is before the open {pos.opened_at.isoformat()}")
        if a.price <= 0:
            raise CliError("--price must be positive")
        async with self._mw(online=False) as mw:
            pos = mw.close_position(pos.id, a.price, closed_at)
        print(f"Closed {pos.ticker} position {pos.id} at {pos.exit_price} on {closed_at.isoformat()}.")
        print(f"Next: trading-pipeline review {pos.id}")

    async def review(self) -> None:
        pos = self._position(self.args.position_id)
        before = {n.id for n in self.store.improvements(approved_only=False)}
        async with self._mw(online=True) as mw:
            outcome, review = await mw.review_position(pos.id, self.clock())
        state = "closed" if outcome.closed else "still open"
        print(f"Outcome for {outcome.ticker} ({outcome.direction}, {state}, {outcome.holding_days} days):")
        print(f"    entry {outcome.entry_price} -> {outcome.last_price}: {outcome.return_pct:+.2f}%  "
              f"(worst {outcome.max_adverse_excursion_pct:+.2f}%, best {outcome.max_favorable_excursion_pct:+.2f}%)")
        print(f"    hit stop: {_yn(outcome.hit_stop)}, hit target: {_yn(outcome.hit_target)}")
        print(f"Process review: {review.outcome_attribution}"
              + (f" (stage at fault: {review.primary_stage_at_fault.value})" if review.primary_stage_at_fault else ""))
        print(f"    {review.attribution_reasoning}")
        for g in review.stage_grades:
            missed = f"; missed: {', '.join(g.missed_foreseeable_risks)}" if g.missed_foreseeable_risks else ""
            print(f"    {g.stage.value}: {g.grade}/5{missed}{' — ' + g.notes if g.notes else ''}")
        new = [n for n in self.store.improvements(approved_only=False) if n.id not in before]
        if new:
            print("New improvement notes (pending your approval; see `notes`):")
            for n in new:
                print(f"    {n.id}  [{n.target_stage.value}] {n.text}")

    def notes(self) -> None:
        notes = self.store.improvements(approved_only=False)
        if not self.args.all:
            notes = [n for n in notes if not n.approved]
        if not notes:
            print("No improvement notes." if self.args.all else "No notes pending approval.")
            return
        for n in notes:
            status = "approved" if n.approved else "pending"
            print(f"{n.id}  [{status}] {n.target_stage.value}: {n.text}  (from position {n.source_position_id})")

    def approve_note(self) -> None:
        note_id = self.args.note_id
        note = next((n for n in self.store.improvements(approved_only=False) if n.id == note_id), None)
        if note is None:
            raise CliError(f"unknown note id: {note_id} (see `trading-pipeline notes`)")
        if note.approved:
            print(f"Note {note_id} was already approved.")
            return
        self.store.approve_improvement(note_id)
        print(f"Approved note {note_id}; future {note.target_stage.value} prompts will include it.")

    def profile(self) -> None:
        if self.args.profile_command == "validate":
            prof = load_profile(self.args.path)
            print(f"OK: {self.args.path} is a valid profile ({prof.name}).")
            print(prof.model_dump_json(indent=2))
            return
        source = str(self.settings.profile_path) if self.settings.profile_path else "built-in default"
        print(f"Profile source: {source}")
        print(self.settings.profile().model_dump_json(indent=2))


def _plan_line(pos: Position) -> str:
    p = pos.plan
    return (f"    {p.direction} {p.horizon}: entry {p.entry_price}, target {p.target_price}, stop {p.stop_loss} "
            f"({p.chart_timeframe} chart; invalidation: {p.invalidation})")


def _yn(b: bool) -> str:
    return "yes" if b else "no"


def main(argv: list[str] | None = None, *, env: dict[str, str] | None = None,
         providers: DataProviders | None = None, llm: LLMClient | None = None,
         clock: Callable[[], datetime] | None = None) -> int:
    """Entry point. The keyword arguments inject settings, data providers, an LLM and a
    clock (tests); by default everything comes from the environment and Equibles."""
    args = _parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")
    settings = Settings.from_env(env, db=args.db, profile=args.profile, model=args.model, effort=args.effort)
    cli = _Cli(args, settings, providers, llm, clock or (lambda: datetime.now(timezone.utc)))
    handler: Callable[[], Any] = getattr(cli, args.command.replace("-", "_"))
    try:
        result = handler()
        if asyncio.iscoroutine(result):
            asyncio.run(result)
    except (CliError, ConfigError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

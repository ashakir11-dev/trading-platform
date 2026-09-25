"""SQLite persistence for reasoning logs, positions, outcomes and reviews.

User decisions live in their own table and are deliberately absent from
``review_trail()``: the process agent must never see the human's accept/reject.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from .data.base import DataSnapshot
from .schemas import (
    Candidate,
    Conflict,
    ImprovementNote,
    OutcomeReport,
    Position,
    ProcessReviewOutput,
    Stage,
    StageRecord,
    TripwireResult,
    UserDecision,
)

M = TypeVar("M", bound=BaseModel)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS docs (
    kind TEXT NOT NULL,
    id TEXT NOT NULL,
    run_id TEXT,
    candidate_id TEXT,
    position_id TEXT,
    json TEXT NOT NULL,
    PRIMARY KEY (kind, id)
);
CREATE INDEX IF NOT EXISTS docs_candidate ON docs(kind, candidate_id);
CREATE INDEX IF NOT EXISTS docs_position ON docs(kind, position_id);

-- Kept physically separate from the system's own records.
CREATE TABLE IF NOT EXISTS user_decisions (
    id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    json TEXT NOT NULL
);
"""


class Store:
    def __init__(self, path: str | Path = ":memory:") -> None:
        self._db = sqlite3.connect(str(path))
        self._db.executescript(_SCHEMA)

    # -- generic ------------------------------------------------------------------------

    def _put(self, kind: str, doc: BaseModel, *, id: str, run_id: str | None = None,
             candidate_id: str | None = None, position_id: str | None = None) -> None:
        self._db.execute(
            "INSERT OR REPLACE INTO docs(kind, id, run_id, candidate_id, position_id, json) VALUES (?,?,?,?,?,?)",
            (kind, id, run_id, candidate_id, position_id, doc.model_dump_json()),
        )
        self._db.commit()

    def _get(self, kind: str, id: str, model: type[M]) -> M | None:
        row = self._db.execute("SELECT json FROM docs WHERE kind=? AND id=?", (kind, id)).fetchone()
        return model.model_validate_json(row[0]) if row else None

    def _query(self, kind: str, model: type[M], where: str = "", args: tuple = ()) -> list[M]:
        sql = "SELECT json FROM docs WHERE kind=?" + (f" AND {where}" if where else "") + " ORDER BY rowid"
        return [model.model_validate_json(r[0]) for r in self._db.execute(sql, (kind, *args))]

    # -- stage records & raw data ---------------------------------------------------------

    def save_stage_record(self, rec: StageRecord) -> None:
        self._put("stage_record", rec, id=rec.id, run_id=rec.run_id,
                  candidate_id=rec.candidate_id, position_id=rec.position_id)

    def save_snapshots(self, snapshots: list[DataSnapshot]) -> None:
        for s in snapshots:
            self._put("snapshot", s, id=s.id)

    def snapshot(self, id: str) -> DataSnapshot | None:
        return self._get("snapshot", id, DataSnapshot)

    def stage_records(self, *, run_id: str | None = None, candidate_id: str | None = None,
                      position_id: str | None = None) -> list[StageRecord]:
        clauses, args = [], []
        for col, val in (("run_id", run_id), ("candidate_id", candidate_id), ("position_id", position_id)):
            if val is not None:
                clauses.append(f"{col}=?")
                args.append(val)
        return self._query("stage_record", StageRecord, " AND ".join(clauses), tuple(args))

    # -- candidates & positions ---------------------------------------------------------

    def save_candidate(self, c: Candidate) -> None:
        self._put("candidate", c, id=c.id, run_id=c.run_id, candidate_id=c.id)

    def candidate(self, id: str) -> Candidate | None:
        return self._get("candidate", id, Candidate)

    def save_position(self, p: Position) -> None:
        self._put("position", p, id=p.id, run_id=p.run_id, candidate_id=p.candidate_id, position_id=p.id)

    def position(self, id: str) -> Position | None:
        return self._get("position", id, Position)

    def open_positions(self) -> list[Position]:
        return [p for p in self._query("position", Position) if p.status == "open"]

    # -- user decisions (isolated) --------------------------------------------------------

    def save_user_decision(self, d: UserDecision) -> None:
        self._db.execute("INSERT OR REPLACE INTO user_decisions(id, candidate_id, json) VALUES (?,?,?)",
                         (d.id, d.candidate_id, d.model_dump_json()))
        self._db.commit()

    def user_decisions(self) -> list[UserDecision]:
        return [UserDecision.model_validate_json(r[0])
                for r in self._db.execute("SELECT json FROM user_decisions ORDER BY rowid")]

    # -- follow-up, outcomes, reviews -----------------------------------------------------

    def save_tripwire(self, t: TripwireResult) -> None:
        self._put("tripwire", t, id=f"{t.position_id}:{t.checked_at.isoformat()}", position_id=t.position_id)

    def tripwires(self, position_id: str) -> list[TripwireResult]:
        rows = self._query("tripwire", TripwireResult, "position_id=?", (position_id,))
        return sorted(rows, key=lambda t: t.checked_at)

    def last_tripwire(self, position_id: str) -> TripwireResult | None:
        rows = self.tripwires(position_id)
        return rows[-1] if rows else None

    def save_conflict(self, c: Conflict) -> None:
        self._put("conflict", c, id=f"{c.run_id}:{c.ticker}:{c.other_sector}", run_id=c.run_id)

    def conflicts(self, run_id: str) -> list[Conflict]:
        return self._query("conflict", Conflict, "run_id=?", (run_id,))

    def save_outcome(self, o: OutcomeReport) -> None:
        self._put("outcome", o, id=o.position_id, position_id=o.position_id)

    def save_process_review(self, position_id: str, r: ProcessReviewOutput) -> None:
        self._put("process_review", r, id=position_id, position_id=position_id)

    def save_improvement(self, n: ImprovementNote) -> None:
        self._put("improvement", n, id=n.id, position_id=n.source_position_id)

    def improvements(self, *, stage: Stage | None = None, approved_only: bool = True) -> list[ImprovementNote]:
        notes = self._query("improvement", ImprovementNote)
        return [n for n in notes
                if (stage is None or n.target_stage == stage) and (n.approved or not approved_only)]

    def approve_improvement(self, id: str) -> None:
        note = self._get("improvement", id, ImprovementNote)
        if note is None:
            raise KeyError(id)
        note.approved = True
        self.save_improvement(note)

    def review_trail(self, position: Position) -> list[StageRecord]:
        """Everything the process agent may see: stage records for the candidate and the
        position's follow-ups. User decisions are intentionally excluded."""
        pre = self.stage_records(candidate_id=position.candidate_id)
        run_level = [r for r in self.stage_records(run_id=position.run_id)
                     if r.candidate_id is None and r.position_id is None
                     and r.stage == Stage.MARKET_SCAN and r.subject == position.sector]
        post = self.stage_records(position_id=position.id)
        seen: set[str] = set()
        out = []
        for r in [*run_level, *pre, *post]:
            if r.id not in seen:
                seen.add(r.id)
                out.append(r)
        return out

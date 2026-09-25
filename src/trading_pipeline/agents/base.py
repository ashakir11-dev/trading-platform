"""Shared plumbing for LLM stage agents."""

from __future__ import annotations

import json
from typing import Any, TypeVar

from pydantic import BaseModel

from ..llm import LLMClient
from ..schemas import Stage

T = TypeVar("T", bound=BaseModel)

SHARED_PRINCIPLES = """\
You are one stage in a multi-agent equity research pipeline. The pipeline supports a
human investor's decisions; it never places trades. Horizons are swing or long-term,
never intraday.

How to work:
- You receive the upstream stage's report AND the raw data behind it. Treat the
  upstream report as a hypothesis, not a fact: check it against the raw data and say
  where you disagree. A bad upstream filter must not blind you.
- Structured reasoning is mandatory. List each factor that pushed you toward or away
  from your conclusion, with the specific raw-data evidence it rests on. Do not cite
  facts that are not in the provided data.
- Consider foreseeable risks explicitly, including macro exposure (rates, FX,
  commodities, index beta), sector, event and liquidity risk. Record how each was
  weighed, even when it doesn't change the verdict.
- Any snapshot marked UNAVAILABLE is a known data gap. Do not guess its contents; list
  it under data_gaps and lower confidence if it matters.
- confidence is your calibrated probability (0.0-1.0) that this stage's conclusion is
  right. Do not inflate it.
- Judge only the subject in front of you. Do not compare it with other candidates.
"""


def report_view(model: BaseModel, *, show_confidence: bool) -> str:
    """Serialize an upstream report for a downstream prompt, optionally hiding confidence."""
    data = model.model_dump(mode="json")
    if not show_confidence:
        data = _strip_key(data, "confidence")
    return json.dumps(data, indent=1)


def _strip_key(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return {k: _strip_key(v, key) for k, v in obj.items() if k != key}
    if isinstance(obj, list):
        return [_strip_key(v, key) for v in obj]
    return obj


class StageAgent:
    stage: Stage
    role: str  # stage-specific instructions

    def __init__(self, llm: LLMClient, lessons: list[str] | None = None) -> None:
        self._llm = llm
        # Human-approved improvement notes from the process agent for this stage.
        self._lessons = lessons or []

    @property
    def system_prompt(self) -> str:
        parts = [SHARED_PRINCIPLES, "\nYour stage:\n" + self.role]
        if self._lessons:
            parts.append("\nLessons from past reviews (human-approved):\n" + "\n".join(f"- {l}" for l in self._lessons))
        return "\n".join(parts)

    async def _ask(self, prompt: str, output: type[T]) -> T:
        return await self._llm.structured(system=self.system_prompt, prompt=prompt, output=output)

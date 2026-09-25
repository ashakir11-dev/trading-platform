"""LLM access for the stage agents.

Agents depend only on the ``LLMClient`` protocol: give it a system prompt, a user
prompt and a Pydantic output model, get a validated instance back. Tests use a fake;
production uses ``AnthropicLLM`` (structured outputs + adaptive thinking).
"""

from __future__ import annotations

import logging
from typing import Protocol, TypeVar

import anthropic
from pydantic import BaseModel

from .config import LLMConfig

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMRefusal(RuntimeError):
    pass


class LLMOutputError(RuntimeError):
    pass


class LLMClient(Protocol):
    async def structured(self, *, system: str, prompt: str, output: type[T]) -> T: ...


class AnthropicLLM:
    def __init__(self, config: LLMConfig, client: anthropic.AsyncAnthropic | None = None) -> None:
        self._config = config
        # Resolves credentials from the environment (ANTHROPIC_API_KEY or an `ant auth login` profile).
        self._client = client or anthropic.AsyncAnthropic()

    async def structured(self, *, system: str, prompt: str, output: type[T]) -> T:
        extra: dict = {}
        if self._config.fallbacks:
            extra = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": self._config.fallbacks}

        response = await self._client.beta.messages.parse(
            model=self._config.model,
            max_tokens=self._config.max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            thinking={"type": "adaptive"},
            output_config={"effort": self._config.effort},
            output_format=output,
            **extra,
        )

        if response.stop_reason == "refusal":
            raise LLMRefusal(f"model refused ({response.stop_details}); request_id={response._request_id}")
        if response.stop_reason == "max_tokens":
            raise LLMOutputError(f"output truncated at max_tokens; request_id={response._request_id}")
        if response.parsed_output is None:
            raise LLMOutputError(f"no parsed output; stop_reason={response.stop_reason}")
        return response.parsed_output

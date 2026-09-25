"""Settings and wiring: turns environment + flags into a ready ``Middleware``.

Real runs read every data category from the hosted Equibles MCP server through one
``HttpMcpClient`` whose allowlist is the union of the tools of the adapters actually
loaded (read-only by construction). Adapter modules are imported lazily; a missing
one is replaced by its ``Unavailable*`` gap provider with a warning, so the system
runs (with explicit data gaps) before every adapter exists.

Everything is injectable: tests pass fake providers and a scripted LLM instead.
"""

from __future__ import annotations

import importlib
import logging
import os
from collections.abc import AsyncIterator, Callable, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import LLMConfig, PipelineConfig
from .data.base import DataProviders
from .data.equibles import EQUIBLES_MCP_URL, FACT_TOOL
from .data.gaps import (
    UnavailableFilings,
    UnavailableFundamentals,
    UnavailableMacro,
    UnavailableNews,
    UnavailablePrices,
    UnavailableQuotes,
    UnavailableSectorData,
)
from .data.mcp import HttpMcpClient, McpToolCaller
from .llm import LLMClient
from .middleware import Middleware
from .profile import InvestorProfile
from .store import Store

log = logging.getLogger(__name__)

DEFAULT_DB = Path("~/.trading-platform/pipeline.sqlite3")

# EquiblesFundamentals predates the adapters' TOOLS convention.
FUNDAMENTALS_TOOLS: frozenset[str] = frozenset({FACT_TOOL})


class ConfigError(RuntimeError):
    """Missing or invalid settings (API keys, profile file, ...). Message is user-facing."""


# --------------------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------------------


@dataclass
class Settings:
    db_path: Path
    profile_path: Path | None = None
    equibles_api_key: str | None = None
    anthropic_api_key: str | None = None
    model: str | None = None
    effort: str | None = None
    # Per-run size limits (set by `run --max-sectors/--shortlist`), for small first runs.
    max_sectors: int | None = None
    shortlist: int | None = None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None, *, db: str | None = None, profile: str | None = None,
                 model: str | None = None, effort: str | None = None) -> Settings:
        """Flags win over environment variables, which win over defaults."""
        env = os.environ if env is None else env
        profile = profile or env.get("TRADING_PROFILE") or None
        return cls(
            db_path=Path(db or env.get("TRADING_DB") or DEFAULT_DB).expanduser(),
            profile_path=Path(profile).expanduser() if profile else None,
            equibles_api_key=env.get("EQUIBLES_API_KEY") or None,
            # TRADING_ANTHROPIC_API_KEY first: hosts that run Claude Code (e.g. Claude Code on
            # the web) reserve ANTHROPIC_API_KEY and do not pass it into the session.
            anthropic_api_key=env.get("TRADING_ANTHROPIC_API_KEY") or env.get("ANTHROPIC_API_KEY") or None,
            model=model or env.get("TRADING_MODEL") or None,
            effort=effort or env.get("TRADING_EFFORT") or None,
        )

    def profile(self) -> InvestorProfile:
        if self.profile_path is None:
            return InvestorProfile()
        return load_profile(self.profile_path)

    def pipeline_config(self) -> PipelineConfig:
        llm = LLMConfig()
        updates: dict[str, Any] = {}
        if self.model:
            updates["model"] = self.model
        if self.effort:
            updates["effort"] = self.effort
        if updates:
            try:
                llm = LLMConfig.model_validate({**llm.model_dump(), **updates})
            except ValueError as e:
                raise ConfigError(f"invalid model/effort override: {e}") from e
        limits: dict[str, Any] = {}
        if self.max_sectors is not None:
            limits["max_sectors"] = self.max_sectors
        if self.shortlist is not None:
            limits["shortlist_max_per_sector"] = self.shortlist
        return PipelineConfig(llm=llm, profile=self.profile(), **limits)

    def open_store(self) -> Store:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return Store(self.db_path)

    def require_equibles_key(self) -> str:
        if not self.equibles_api_key:
            raise ConfigError("EQUIBLES_API_KEY is not set. It is needed to fetch market data "
                              "(see docs/operations.md).")
        return self.equibles_api_key

    def require_anthropic_key(self) -> str:
        if not self.anthropic_api_key:
            raise ConfigError("ANTHROPIC_API_KEY (or TRADING_ANTHROPIC_API_KEY) is not set. It is needed "
                              "to run the agents (see docs/operations.md).")
        return self.anthropic_api_key


def load_profile(path: str | Path) -> InvestorProfile:
    path = Path(path).expanduser()
    if not path.is_file():
        raise ConfigError(f"profile file not found: {path}")
    try:
        return InvestorProfile.load(path)
    except ValueError as e:
        raise ConfigError(f"invalid profile {path}:\n{e}") from e


# --------------------------------------------------------------------------------------
# Providers
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class AdapterSpec:
    field: str  # DataProviders field
    module: str
    cls: str
    gap: Callable[[], Any]
    tools: frozenset[str] | None = None  # when the class has no TOOLS attribute


ADAPTERS: tuple[AdapterSpec, ...] = (
    AdapterSpec("prices", "trading_pipeline.data.equibles_prices", "EquiblesPrices", UnavailablePrices),
    AdapterSpec("quotes", "trading_pipeline.data.equibles_prices", "EquiblesQuotes", UnavailableQuotes),
    AdapterSpec("sectors", "trading_pipeline.data.equibles_sectors", "EquiblesSectorData", UnavailableSectorData),
    AdapterSpec("news", "trading_pipeline.data.equibles_events", "EquiblesNews", UnavailableNews),
    AdapterSpec("fundamentals", "trading_pipeline.data.equibles", "EquiblesFundamentals", UnavailableFundamentals,
                tools=FUNDAMENTALS_TOOLS),
    AdapterSpec("filings", "trading_pipeline.data.equibles_events", "EquiblesFilings", UnavailableFilings),
    AdapterSpec("macro", "trading_pipeline.data.equibles_macro", "EquiblesMacro", UnavailableMacro),
)


def _load(spec: AdapterSpec, *, warn: bool = True) -> type | None:
    """The adapter class, or None (with a warning) if its module or class doesn't exist yet."""
    try:
        module = importlib.import_module(spec.module)
    except ModuleNotFoundError as e:
        if e.name != spec.module:
            raise  # the adapter exists but one of *its* imports is missing: a real error
        if warn:
            log.warning("%s: adapter module %s not available; using gap placeholder (data marked UNAVAILABLE)",
                        spec.field, spec.module)
        return None
    cls = getattr(module, spec.cls, None)
    if cls is None and warn:
        log.warning("%s: %s.%s not found; using gap placeholder (data marked UNAVAILABLE)",
                    spec.field, spec.module, spec.cls)
    return cls


def _tools(spec: AdapterSpec, cls: type) -> frozenset[str]:
    return frozenset(getattr(cls, "TOOLS", frozenset())) | (spec.tools or frozenset())


def adapter_tools() -> frozenset[str]:
    """Union of the MCP tools of every adapter that can be loaded: the client allowlist."""
    out: frozenset[str] = frozenset()
    for spec in ADAPTERS:
        cls = _load(spec, warn=False)  # build_providers warns
        if cls is not None:
            out |= _tools(spec, cls)
    return out


def build_providers(mcp: McpToolCaller) -> tuple[DataProviders, frozenset[str]]:
    """Every provider from its Equibles adapter, or its gap placeholder when missing.

    Returns the providers and the MCP tools they need (the allowlist)."""
    fields: dict[str, Any] = {}
    tools: frozenset[str] = frozenset()
    for spec in ADAPTERS:
        cls = _load(spec)
        if cls is None:
            fields[spec.field] = spec.gap()
        else:
            fields[spec.field] = cls(mcp)
            tools |= _tools(spec, cls)
    return DataProviders(**fields), tools


def offline_providers() -> DataProviders:
    """All-gap providers, for commands that only touch the store."""
    return DataProviders(**{spec.field: spec.gap() for spec in ADAPTERS})


@asynccontextmanager
async def equibles_providers(settings: Settings) -> AsyncIterator[DataProviders]:
    """Open the Equibles MCP client (allowlisted, read-only) and yield ready providers."""
    key = settings.require_equibles_key()
    allowed = adapter_tools()
    async with HttpMcpClient(EQUIBLES_MCP_URL, allowed_tools=set(allowed),
                             headers={"Authorization": f"Bearer {key}"}) as client:
        providers, needed = build_providers(client)
        assert needed <= allowed
        yield providers


# --------------------------------------------------------------------------------------
# Middleware
# --------------------------------------------------------------------------------------


class OfflineLLM:
    """Stands in for the LLM in commands that must not call it."""

    async def structured(self, *, system: str, prompt: str, output):
        raise RuntimeError("this command does not call the LLM")


def anthropic_llm(settings: Settings, config: PipelineConfig) -> LLMClient:
    api_key = settings.require_anthropic_key()
    import anthropic

    from .llm import AnthropicLLM

    return AnthropicLLM(config.llm, anthropic.AsyncAnthropic(api_key=api_key))


@asynccontextmanager
async def open_middleware(settings: Settings, *, online: bool = True, store: Store | None = None,
                          providers: DataProviders | None = None,
                          llm: LLMClient | None = None) -> AsyncIterator[Middleware]:
    """Yield a ready ``Middleware``.

    ``online=False`` wires gap providers and an LLM stub (store-only commands: no keys
    needed). Pass ``providers``/``llm`` to inject test doubles or other sources.
    """
    config = settings.pipeline_config()
    store = store or settings.open_store()
    if not online:
        yield Middleware(config, llm or OfflineLLM(), providers or offline_providers(), store)
        return
    llm = llm or anthropic_llm(settings, config)
    if providers is not None:
        yield Middleware(config, llm, providers, store)
        return
    async with equibles_providers(settings) as real:
        yield Middleware(config, llm, real, store)

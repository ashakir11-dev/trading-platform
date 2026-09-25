"""Multi-agent trading research pipeline. See docs/ARCHITECTURE.md."""

from .config import LLMConfig, PipelineConfig
from .middleware import Middleware, render_report
from .store import Store

__all__ = ["LLMConfig", "Middleware", "PipelineConfig", "Store", "render_report"]

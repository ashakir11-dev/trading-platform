"""Standalone launcher for the trading pipeline's middleware agent.

The pipeline itself is prompts (``prompts/``) and Claude Code configuration
(``.claude/``). This package only starts it: interactively (the Claude Code terminal UI
with the ``middleware`` agent as the main session) or headless (one skill, through the
Claude Agent SDK, for cron). ``doctor`` and ``init`` need nothing but the standard
library, so ``python3 -m trading_agent doctor`` works before anything is installed.
"""

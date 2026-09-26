"""Finding the repository and loading the keys, the same way on any machine."""

from __future__ import annotations

import os
import re
from pathlib import Path

MARKER = Path(".claude") / "agents" / "middleware.md"
# Later files do not override earlier ones, and nothing overrides the real environment.
ENV_FILES = (Path(".env"),)
USER_ENV_FILE = Path.home() / ".trading-platform" / "env"

_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")


def find_root(start: Path | None = None) -> Path:
    """The repository root: ``$TRADING_PLATFORM_HOME``, else the nearest folder above
    ``start`` (default: the working directory) holding the middleware agent, else the
    folder this package sits in."""
    if home := os.environ.get("TRADING_PLATFORM_HOME"):
        return Path(home).expanduser().resolve()
    here = (start or Path.cwd()).resolve()
    for folder in (here, *here.parents):
        if (folder / MARKER).is_file():
            return folder
    return Path(__file__).resolve().parents[1]


def parse_env(text: str) -> dict[str, str]:
    """``KEY=value`` lines, optionally ``export``-ed and quoted; comments and blanks skipped."""
    values = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = _LINE.match(line)
        if not m:
            continue
        key, value = m.groups()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        else:
            value = value.split(" #", 1)[0].rstrip()
        values[key] = value
    return values


def env_files(root: Path) -> list[Path]:
    return [root / f for f in ENV_FILES] + [USER_ENV_FILE]


def load_env(root: Path, environ: dict[str, str] | None = None) -> list[Path]:
    """Load ``.env`` at the root, then ``~/.trading-platform/env``, into ``environ``
    (default: ``os.environ``) without overriding what is already set. Returns the
    files that were read."""
    environ = os.environ if environ is None else environ
    read = []
    for path in env_files(root):
        if not path.is_file():
            continue
        for key, value in parse_env(path.read_text(encoding="utf-8")).items():
            environ.setdefault(key, value)
        read.append(path)
    return read

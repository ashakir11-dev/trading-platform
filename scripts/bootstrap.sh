#!/usr/bin/env sh
# One-time setup on a fresh clone: a virtualenv with the launcher, the workspace, the
# profile and .env from the examples, then the machine check. Safe to run again.
set -eu
cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"
"$PYTHON" -c 'import sys; sys.exit(sys.version_info < (3, 10))' \
  || { echo "Python 3.10+ is needed (set PYTHON=/path/to/python3)." >&2; exit 1; }

[ -d .venv ] || "$PYTHON" -m venv .venv
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -e ".[dev]"

.venv/bin/trading-agent init
echo
.venv/bin/trading-agent doctor || true
echo
echo "Next: add your keys to .env, then run .venv/bin/trading-agent (or activate .venv first)."

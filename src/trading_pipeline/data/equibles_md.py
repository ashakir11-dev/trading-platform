"""Parsing helpers for Equibles MCP answers.

Equibles tools answer in markdown: a title line, a table, then optional footnotes
(split-adjustment notes, truncation notes, coverage warnings). Cells are escaped by
Equibles' ``MarkdownTable.EscapeCell`` (backslashes doubled, pipes as ``\\|``).
Adapters should parse with these helpers rather than hand-rolled string handling.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

_CELL_SPLIT = re.compile(r"(?<!\\)\|")
_SEPARATOR = re.compile(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def split_row(line: str) -> list[str]:
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|") and not inner.endswith("\\|"):
        inner = inner[:-1]
    return [c.strip().replace("\\|", "|").replace("\\\\", "\\") for c in _CELL_SPLIT.split(inner)]


def tables(text: str) -> list[list[dict[str, str]]]:
    """Every markdown table in ``text`` as a list of row dicts keyed by header."""
    lines = text.splitlines()
    out: list[list[dict[str, str]]] = []
    i = 0
    while i < len(lines) - 1:
        # Some tools (e.g. ListFilings) omit the outer pipes, so a header is any line with
        # a pipe followed by a separator line.
        if "|" in lines[i] and _SEPARATOR.match(lines[i + 1].strip()):
            header = split_row(lines[i])
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].strip() and "|" in lines[j]:
                cells = split_row(lines[j])
                if len(cells) == len(header):
                    rows.append(dict(zip(header, cells)))
                j += 1
            out.append(rows)
            i = j
        else:
            i += 1
    return out


def find_table(text: str, required: set[str]) -> list[dict[str, str]] | None:
    """The first table whose header contains all ``required`` columns, else None."""
    for rows in tables(text):
        if rows and required <= set(rows[0]):
            return rows
    # A table with a matching header but no rows is still "found" (empty result).
    lines = text.splitlines()
    for k, line in enumerate(lines[:-1]):
        if "|" in line and required <= set(split_row(line)) and _SEPARATOR.match(lines[k + 1].strip()):
            return []
    return None


def number(text: str | None) -> Decimal | None:
    """Parse Equibles-formatted numbers: '$1,234', '-$5.10', '12.5%', '1,000 (as filed)', '—' -> None."""
    if text is None:
        return None
    t = text.replace("(as filed)", "").replace("*", "").strip()
    if t in ("", "—", "-", "N/A", "n/a"):
        return None
    neg = t.startswith("-") or (t.startswith("(") and t.endswith(")"))
    t = t.strip("()").lstrip("-").lstrip("$").rstrip("%").replace(",", "").strip()
    mult = Decimal(1)
    if t[-1:] in "KMBT" and t[:-1]:
        mult = Decimal({"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}[t[-1]])
        t = t[:-1]
    try:
        value = Decimal(t) * mult
    except InvalidOperation:
        return None
    return -value if neg else value

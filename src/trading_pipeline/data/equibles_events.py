"""SEC filings, 8-K catalyst events, FDA advisory meetings and estimated earnings dates
from the hosted Equibles MCP server.

Tools used (checked against the open-source Equibles code):

* ``ListFilings`` (``Equibles.Sec.Mcp/Tools/RagSearchTools.cs``): a company's filings
  newest first with type, filed date, reporting period and 8-K item numbers. Filters:
  ``ticker``, ``startDate``/``endDate`` (on the filed date), ``documentType`` (display
  names such as "8-K" are accepted), exact ``itemNumber`` (e.g. "2.02"), ``maxItems``
  (<= 500), ``page``. The filed date has no time of day.
* ``GetFdaAdvisoryCommitteeMeetings`` (``Equibles.FdaCatalysts.Mcp/Tools/FdaCatalystTools.cs``):
  the FDA advisory-committee calendar (``startDate``, ``endDate``, ``maxResults``). Rows are
  not linked to tickers, and coverage starts in late 2025.

Point-in-time rules:

* A filing is visible from the start of the US/Eastern day after its filed date (same
  rule as the fundamentals adapter: ``FiledDate`` has no time and EDGAR accepts filings
  into the evening). An 8-K's event ``ts`` is that visibility time, so every event has
  ``ts <= as_of`` and appears in exactly one ``(since, as_of]`` window.
* The FDA calendar is today's calendar, not a history of what was announced when. A
  meeting is treated as known ``fda_notice_days`` (default 15) before it starts: federal
  advisory committees must publish a Federal Register notice at least 15 days ahead
  (41 CFR 102-3.150). The event ``ts`` is that known-by date and ``event_date`` is the
  meeting date. Meetings announced earlier than that are shown late (never early);
  cancelled or re-dated meetings may be missing or show their latest date.
* Earnings dates are estimated from past 8-K item 2.02 filings visible at ``as_of``.

Not available in the open-source tools (Equibles Cloud only, or not at all), so not
modelled here: a confirmed earnings calendar, PDUFA dates, general news, analyst actions.
"""

from __future__ import annotations

import asyncio
import re
import statistics
from collections.abc import Callable, Sequence
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from .base import DataSnapshot
from .equibles import EASTERN, visible_before
from .equibles_md import find_table, split_row
from .mcp import McpToolCaller

LIST_FILINGS = "ListFilings"
FDA_MEETINGS = "GetFdaAdvisoryCommitteeMeetings"
# Equibles Cloud tools (formats verified against the hosted server; fixtures in
# tests/fixtures/equibles_live).
IR_EVENTS = "GetUpcomingInvestorEvents"
IR_NEWS = "GetInvestorRelationsNews"
SOURCE = "equibles"

# SEC Form 8-K item titles (short forms).
EIGHT_K_ITEMS: dict[str, str] = {
    "1.01": "Entry into a material definitive agreement",
    "1.02": "Termination of a material definitive agreement",
    "1.03": "Bankruptcy or receivership",
    "1.04": "Mine safety violation",
    "1.05": "Material cybersecurity incident",
    "2.01": "Completion of acquisition or disposition of assets",
    "2.02": "Results of operations and financial condition",
    "2.03": "Creation of a direct financial obligation",
    "2.04": "Triggering event accelerating a financial obligation",
    "2.05": "Costs of exit or disposal activities",
    "2.06": "Material impairment",
    "3.01": "Delisting notice or failure to meet listing standards",
    "3.02": "Unregistered sale of equity securities",
    "3.03": "Material modification to rights of security holders",
    "4.01": "Change in certifying accountant",
    "4.02": "Non-reliance on previously issued financial statements",
    "5.01": "Change in control of registrant",
    "5.02": "Departure or appointment of directors or officers",
    "5.03": "Amendment to articles or bylaws; change in fiscal year",
    "5.04": "Temporary suspension of trading under employee benefit plans",
    "5.05": "Amendment to or waiver of code of ethics",
    "5.06": "Change in shell company status",
    "5.07": "Shareholder vote results",
    "5.08": "Shareholder director nominations",
    "7.01": "Regulation FD disclosure",
    "8.01": "Other events",
    "9.01": "Financial statements and exhibits",
}

# Item -> event category, in priority order (the first matching item names the event).
# Categories in rules.MATERIAL_CATEGORIES are used only for items that rules.MATERIAL_8K_ITEMS
# already treats as material, so the category never overrides the item-based decision.
_ITEM_CATEGORY: tuple[tuple[str, str], ...] = (
    ("1.03", "bankruptcy"),
    ("4.02", "restatement"),
    ("3.01", "delisting"),
    ("5.01", "m_and_a"),
    ("2.01", "m_and_a"),
    ("2.02", "earnings"),
    ("5.02", "management_change"),
    ("2.06", "impairment"),
    ("2.05", "restructuring"),
    ("4.01", "auditor_change"),
    ("1.01", "material_agreement"),
    ("1.02", "material_agreement"),
    ("2.03", "financing"),
    ("2.04", "financing"),
    ("3.02", "equity_issuance"),
    ("1.05", "cybersecurity"),
    ("3.03", "shareholder_rights"),
    ("5.03", "governance"),
    ("5.07", "shareholder_vote"),
    ("7.01", "disclosure"),
    ("8.01", "other_events"),
)

DEFAULT_FORMS: tuple[str, ...] = ("10-K", "10-Q", "8-K")

_HEALTHCARE = re.compile(r"health|biotech|pharma|life ?science|medical|drug|therapeut|biolog|diagnostic",
                         re.IGNORECASE)
_TITLE = re.compile(r"^(?:Financial documents for (?P<company>.+) \((?P<ticker>[^()]+)\)|Market-wide filings)"
                    r" — page (?P<page>[\d,]+) of (?P<pages>[\d,]+) \((?P<total>[\d,]+) documents\):\s*$")
# Tickers are upper-case symbols; sector names from the sector calls are words ("Biotech").
_TICKER = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")
_SEPARATOR = re.compile(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_NOT_FOUND = re.compile(r"^Stock '.*' not found\.|^No documents found for ticker ")
_NO_MATCH = re.compile(r"^No documents match the given filters")
_COMPANY_SUFFIX = re.compile(
    r"[,.]|\b(inc|incorporated|corp|corporation|co|company|ltd|limited|plc|llc|lp|sa|nv|ag|se|holdings?|group|the)\b",
    re.IGNORECASE)

_FILING_COLUMNS = {"Ticker", "Company", "ID", "Type", "Filed", "Reporting For", "Items"}
_FDA_COLUMNS = {"Date", "Meeting", "Center", "Type", "Through", "Details"}


# --------------------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------------------


def _bare_table(text: str, required: set[str]) -> list[dict[str, str]] | None:
    """A markdown table whose rows may lack the outer pipes (ListFilings renders
    ``Ticker | Company | ...`` with no leading ``|``, which ``equibles_md.tables`` skips)."""
    found = find_table(text, required)
    if found is not None:
        return found
    lines = text.splitlines()
    for i, line in enumerate(lines[:-1]):
        if "|" not in line or not _SEPARATOR.match(lines[i + 1].strip()):
            continue
        header = split_row(line)
        if not required <= set(header):
            continue
        rows = []
        for row in lines[i + 2:]:
            if "|" not in row:
                break
            cells = split_row(row)
            if len(cells) == len(header):
                rows.append(dict(zip(header, cells)))
        return rows
    return None


def _unescape(cell: str | None) -> str | None:
    return None if cell is None else cell.replace("\\|", "|").replace("\\\\", "\\")


def parse_filings(text: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Parse a ``ListFilings`` answer into rows plus meta (company, total, pages, status).

    ``status`` is "ok", "empty" (filters matched nothing), "not_found" or "unparsed".
    """
    meta: dict[str, Any] = {"company": None, "ticker": None, "total": 0, "pages": 0, "status": "ok"}
    stripped = text.strip()
    if _NOT_FOUND.match(stripped):
        return [], {**meta, "status": "not_found", "message": stripped}
    if _NO_MATCH.match(stripped):
        return [], {**meta, "status": "empty", "message": stripped}
    first = stripped.splitlines()[0] if stripped else ""
    m = _TITLE.match(first)
    table = _bare_table(text, _FILING_COLUMNS)
    if m is None or table is None:
        return [], {**meta, "status": "unparsed", "message": stripped[:300]}
    meta.update(company=_unescape(m.group("company")), ticker=_unescape(m.group("ticker")),
                total=int(m.group("total").replace(",", "")), pages=int(m.group("pages").replace(",", "")))
    rows = []
    for r in table:
        try:
            filed = date.fromisoformat(r["Filed"])
        except ValueError:
            continue
        period = r.get("Reporting For") or ""
        items = [] if r["Items"] in ("", "—") else [i.strip() for i in r["Items"].split(",") if i.strip()]
        rows.append({"ticker": r["Ticker"], "company": r["Company"], "document_id": r["ID"],
                     "form": r["Type"], "filed": filed,
                     "period": period if re.fullmatch(r"\d{4}-\d{2}-\d{2}", period) else None,
                     "sec_items": items})
    return rows, meta


def parse_fda_meetings(text: str) -> tuple[list[dict[str, Any]], str]:
    """Parse a ``GetFdaAdvisoryCommitteeMeetings`` answer. Returns (meetings, note)."""
    table = find_table(text, _FDA_COLUMNS)
    if table is None:
        stripped = text.strip()
        return [], stripped if stripped.startswith("No FDA advisory-committee meetings") else f"Unparsed FDA answer: {stripped[:300]}"
    notes = [ln.strip("_ ") for ln in text.splitlines() if ln.strip().startswith("_Showing")]
    meetings = []
    for r in table:
        try:
            start = date.fromisoformat(r["Date"])
        except ValueError:
            continue
        through = r["Through"]
        meetings.append({
            "date": start,
            "through": date.fromisoformat(through) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", through) else None,
            "title": r["Meeting"], "center": r["Center"], "type": r["Type"],
            "url": None if r["Details"] in ("", "—") else r["Details"],
        })
    return meetings, "; ".join(notes)


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------


def known_from(filed: date) -> datetime:
    """When a filing dated ``filed`` becomes visible: 00:00 US/Eastern the next day."""
    return datetime.combine(filed + timedelta(days=1), time(0), tzinfo=EASTERN)


def _eastern_day(dt: datetime) -> date:
    if dt.tzinfo is None:
        raise ValueError("datetimes must be timezone-aware")
    return dt.astimezone(EASTERN).date()


def categorize_8k(items: Sequence[str]) -> str:
    present = set(items)
    for item, category in _ITEM_CATEGORY:
        if item in present:
            return category
    return "other_events"


def headline_8k(company: str | None, form: str, items: Sequence[str]) -> str:
    descs = [EIGHT_K_ITEMS.get(i, f"Item {i}") for i in items if i != "9.01"]
    who = f"{company} " if company else ""
    if not descs:
        return f"{who}{form} filed (exhibits only)" if items else f"{who}{form} filed (no item numbers listed)"
    return f"{who}{form}: " + "; ".join(descs)


def is_healthcare_sector(sector: str) -> bool:
    return bool(_HEALTHCARE.search(sector))


def _name_key(company: str | None) -> str | None:
    """Company name reduced for matching inside FDA meeting titles, or None if too generic."""
    if not company:
        return None
    key = re.sub(r"\s+", " ", _COMPANY_SUFFIX.sub(" ", company)).strip().lower()
    key = re.sub(r"\band\s*$", "", key).strip()
    return key if len(key) >= 4 else None


def mentions_company(title: str, company: str | None) -> bool:
    key = _name_key(company)
    return bool(key) and re.search(rf"\b{re.escape(key)}\b", title, re.IGNORECASE) is not None


async def _list_filings(mcp: McpToolCaller, ticker: str, start: date, end: date, *,
                        document_type: str | None = None, item: str | None = None,
                        max_items: int = 100) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    args: dict[str, Any] = {"ticker": ticker, "startDate": start.isoformat(), "endDate": end.isoformat(),
                            "maxItems": max_items, "page": 1}
    if document_type:
        args["documentType"] = document_type
    if item:
        args["itemNumber"] = item
    return parse_filings(await mcp.call_tool(LIST_FILINGS, args))


def _gap(kind: str, subject: str, as_of: datetime, note: str) -> DataSnapshot:
    return DataSnapshot(kind=kind, source=SOURCE, subject=subject, as_of=as_of, is_gap=True, note=note)


# --------------------------------------------------------------------------------------
# Filings
# --------------------------------------------------------------------------------------


class EquiblesFilings:
    """``FilingsProvider`` over ``ListFilings``: one call per form type (3 by default).

    Only filings filed on an earlier US/Eastern day than ``as_of`` appear. Each row keeps
    ``document_id`` so a stage or a later adapter can read the text with Equibles'
    document tools. No excerpt is fetched (keeps payloads and call budget small).
    """

    TOOLS: frozenset[str] = frozenset({LIST_FILINGS})

    def __init__(self, mcp: McpToolCaller, *, forms: Sequence[str] = DEFAULT_FORMS,
                 max_per_form: int = 50) -> None:
        self._mcp = mcp
        self._forms = list(forms)
        self._max = max_per_form

    async def recent_filings(self, ticker: str, since: datetime, as_of: datetime) -> DataSnapshot:
        cutoff = visible_before(as_of)
        start = _eastern_day(since)
        if start >= cutoff:
            return DataSnapshot(kind="filings", source=SOURCE, subject=ticker, as_of=as_of, payload=[])
        results = await asyncio.gather(*(
            _list_filings(self._mcp, ticker, start, cutoff - timedelta(days=1), document_type=form,
                          max_items=self._max) for form in self._forms))

        rows: list[dict[str, Any]] = []
        notes: list[str] = []
        company = None
        statuses = set()
        for form, (parsed, meta) in zip(self._forms, results):
            statuses.add(meta["status"])
            company = company or meta["company"]
            if meta["status"] in ("unparsed", "not_found") and meta["message"] not in notes:
                notes.append(meta["message"])
            if meta["total"] > len(parsed):
                notes.append(f"{form}: showing newest {len(parsed)} of {meta['total']} in the window.")
            rows += [r for r in parsed if start <= r["filed"] < cutoff]
        if statuses <= {"not_found", "unparsed"}:
            return _gap("filings", ticker, as_of, "; ".join(notes) or f"Equibles has no filings for {ticker}.")

        rows.sort(key=lambda r: (r["filed"], r["document_id"]), reverse=True)
        payload = [{
            "form": r["form"], "filed": r["filed"].isoformat(), "period": r["period"],
            "sec_items": r["sec_items"],
            "title": headline_8k(None, r["form"], r["sec_items"]) if r["form"].startswith("8-K")
            else f"{r['form']} for period ending {r['period'] or 'unknown'}",
            "document_id": r["document_id"],
        } for r in rows]
        note = (f"{company or ticker}: SEC filings ({', '.join(self._forms)}) filed before "
                f"{cutoff.isoformat()} (US/Eastern day of as_of), newest first. For 8-Ks, "
                "'period' is the date of the reported event.")
        if notes:
            note += " " + " ".join(notes)
        return DataSnapshot(kind="filings", source=SOURCE, subject=ticker, as_of=as_of, payload=payload, note=note)


# --------------------------------------------------------------------------------------
# News / catalysts
# --------------------------------------------------------------------------------------


_IR_EVENT = re.compile(r"^- (?P<date>\d{4}-\d{2}-\d{2})(?: (?P<time>\d{2}:\d{2}) UTC)? \[(?P<type>[^\]]+)\]: (?P<title>.+)$")
_IR_NEWS = re.compile(r"^- (?P<date>\d{4}-\d{2}-\d{2}): (?P<headline>.+)$")


def _bullets(text: str, pattern: re.Pattern) -> list[dict[str, Any]]:
    """Parse Equibles' bullet-list answers: '- <fields>' lines, each optionally followed by an
    indented URL line."""
    out: list[dict[str, Any]] = []
    for line in (text or "").splitlines():
        m = pattern.match(line.strip()) if line.startswith("- ") else None
        if m:
            out.append({**m.groupdict(), "url": None})
        elif out and line.startswith("  ") and line.strip().startswith("http"):
            out[-1]["url"] = line.strip()
    return out


def parse_upcoming_events(text: str) -> list[dict[str, Any]]:
    """GetUpcomingInvestorEvents -> [{date, time, type, title, url}] (soonest first)."""
    return _bullets(text, _IR_EVENT)


def parse_ir_news(text: str) -> list[dict[str, Any]]:
    """GetInvestorRelationsNews -> [{date, headline, url}] (newest first)."""
    return _bullets(text, _IR_NEWS)


class EquiblesNews:
    """``NewsCatalystProvider`` built from 8-K filings and the FDA advisory calendar.

    * ``events(ticker, ...)``: the company's 8-Ks (and 8-K/As) that became visible in
      ``(since, as_of]``, plus FDA meetings whose title names the company (best effort:
      the FDA calendar is not linked to tickers and titles rarely name the sponsor).
    * ``events(sector, ...)``: FDA advisory meetings for healthcare-like sectors. Other
      sectors get a gap snapshot: Equibles has no sector news, and a sector's 8-Ks would
      need a sector -> tickers list (one ``ListFilings`` call per company).
    * ``upcoming_earnings``: estimated from the cadence of past 8-K item 2.02 filings.

    Calls: ticker events 3 (8-K, 8-K/A, FDA; 2 without FDA matching), sector events 1,
    earnings 1. A subject is treated as a ticker when it looks like one (``AAPL``, ``BRK.B``).
    """

    TOOLS: frozenset[str] = frozenset({LIST_FILINGS, FDA_MEETINGS, IR_EVENTS, IR_NEWS})

    def __init__(self, mcp: McpToolCaller, *, fda_notice_days: int = 15, match_fda_to_tickers: bool = True,
                 earnings_lookback_days: int = 800, max_8ks: int = 100, ir_news: bool = True,
                 max_ir_news: int = 50,
                 now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> None:
        self._mcp = mcp
        self._ir_news = ir_news
        self._max_ir_news = max_ir_news
        self._now = now
        self._notice = timedelta(days=fda_notice_days)
        self._match_fda = match_fda_to_tickers
        self._earnings_lookback = timedelta(days=earnings_lookback_days)
        self._max_8ks = max_8ks

    # -- events --------------------------------------------------------------------

    async def events(self, subject: str, since: datetime, as_of: datetime) -> DataSnapshot:
        if _TICKER.match(subject):
            return await self._ticker_events(subject, since, as_of)
        return await self._sector_events(subject, since, as_of)

    async def _ticker_events(self, ticker: str, since: datetime, as_of: datetime) -> DataSnapshot:
        cutoff = visible_before(as_of)
        start = _eastern_day(since) - timedelta(days=1)
        if start >= cutoff:
            return DataSnapshot(kind="news_catalysts", source=SOURCE, subject=ticker, as_of=as_of, payload=[])
        filing_jobs = [_list_filings(self._mcp, ticker, start, cutoff - timedelta(days=1), document_type=f,
                                     max_items=self._max_8ks) for f in ("8-K", "8-K/A")]
        fda_job = self._fda_window(since, as_of) if self._match_fda else None
        news_job = self._press_releases(ticker, start, since, as_of) if self._ir_news else None
        results = await asyncio.gather(*filing_jobs, *([fda_job] if fda_job else []),
                                       *([news_job] if news_job else []))
        filing_results = results[:2]
        press, press_note = results[-1] if news_job else ([], None)

        statuses = {meta["status"] for _, meta in filing_results}
        if statuses <= {"not_found", "unparsed"}:
            msg = "; ".join(m.get("message", "") for _, m in filing_results)
            return _gap("news_catalysts", ticker, as_of, msg or f"Equibles has no filings for {ticker}.")
        company = next((m["company"] for _, m in filing_results if m["company"]), None)

        events: list[dict[str, Any]] = []
        notes = []
        for parsed, meta in filing_results:
            if meta["total"] > len(parsed):
                notes.append(f"Only the newest {len(parsed)} of {meta['total']} 8-Ks were read.")
            for r in parsed:
                ts = known_from(r["filed"])
                if not (since < ts <= as_of):
                    continue
                events.append({
                    "ts": ts.isoformat(), "filed": r["filed"].isoformat(),
                    "headline": headline_8k(company, r["form"], r["sec_items"]),
                    "category": categorize_8k(r["sec_items"]), "sec_form": r["form"],
                    "sec_items": r["sec_items"], "source": "SEC EDGAR via Equibles", "url": None,
                    "document_id": r["document_id"],
                })
        note = ("8-K current reports; ts = start of the US/Eastern day after filing (when the filing "
                "counts as known). Equibles has no general news or analyst actions.")
        if fda_job:
            meetings, fda_note = results[2]
            matched = [e for e in self._fda_events(meetings, since, as_of) if mentions_company(e["meeting"], company)]
            events += matched
            note += (" FDA advisory meetings are matched to the company by name in the meeting title "
                     "(best effort; the FDA calendar does not name tickers). " + self._fda_caveat())
            if fda_note and not fda_note.startswith("No FDA"):
                notes.append(fda_note)
        if news_job:
            events += press
            note += (" Company press releases from its investor-relations site; ts = start of the "
                     "US/Eastern day after the published date (items carry a date, not a time).")
            if press_note:
                notes.append(press_note)
        events.sort(key=lambda e: e["ts"], reverse=True)
        if notes:
            note += " " + " ".join(notes)
        return DataSnapshot(kind="news_catalysts", source=SOURCE, subject=ticker, as_of=as_of,
                            payload=events, note=note)

    async def _press_releases(self, ticker: str, start: date, since: datetime,
                              as_of: datetime) -> tuple[list[dict[str, Any]], str | None]:
        """Company IR press releases published in the window, as event dicts."""
        try:
            text = await self._mcp.call_tool(IR_NEWS, {"ticker": ticker, "since": start.isoformat(),
                                                      "maxResults": self._max_ir_news})
        except Exception as e:
            return [], f"{IR_NEWS} failed: {e}"
        items = parse_ir_news(str(text))
        if not items:
            # Equibles distinguishes coverage gaps from silence in plain text; pass it on.
            return [], f"Press releases: {str(text).strip().splitlines()[0][:200]}" if str(text).strip() else None
        out = []
        for it in items:
            published = date.fromisoformat(it["date"])
            ts = known_from(published)
            if since < ts <= as_of:
                out.append({"ts": ts.isoformat(), "published": it["date"], "headline": it["headline"],
                            "category": None, "source": "company investor relations via Equibles",
                            "url": it["url"]})
        return out, None

    async def _sector_events(self, sector: str, since: datetime, as_of: datetime) -> DataSnapshot:
        if not is_healthcare_sector(sector):
            return _gap("news_catalysts", sector, as_of,
                        f"No sector-level event source for '{sector}': Equibles has no general news, and "
                        "sector 8-Ks need a sector-to-ticker list. Company 8-Ks arrive with each "
                        "company's own data.")
        meetings, fda_note = await self._fda_window(since, as_of)
        if fda_note and not meetings and not fda_note.startswith("No FDA"):
            return _gap("news_catalysts", sector, as_of, fda_note)
        events = self._fda_events(meetings, since, as_of)
        events.sort(key=lambda e: e["event_date"])
        note = ("FDA advisory-committee meetings (FDA.gov calendar via Equibles), not linked to "
                "tickers. " + self._fda_caveat() + " PDUFA dates and sector earnings dates are not available.")
        if fda_note and not fda_note.startswith("No FDA"):
            note += " " + fda_note
        return DataSnapshot(kind="news_catalysts", source=SOURCE, subject=sector, as_of=as_of,
                            payload=events, note=note)

    def _fda_caveat(self) -> str:
        return (f"Point-in-time: a meeting counts as known {self._notice.days} days before it starts "
                "(ts = that date; Federal Register notice minimum), so meetings further out are not shown "
                "yet even if announced. The calendar is today's copy: coverage starts late 2025, and "
                "cancelled or re-dated meetings may be missing or show their latest date.")

    async def _fda_window(self, since: datetime, as_of: datetime) -> tuple[list[dict[str, Any]], str]:
        # Known-by ts = meeting - notice must fall in (since, as_of]: meetings in (since+notice, as_of+notice].
        start = _eastern_day(since + self._notice)
        end = _eastern_day(as_of + self._notice)
        text = await self._mcp.call_tool(FDA_MEETINGS, {"startDate": start.isoformat(),
                                                        "endDate": end.isoformat(), "maxResults": 200})
        return parse_fda_meetings(text)

    def _fda_events(self, meetings: list[dict[str, Any]], since: datetime, as_of: datetime) -> list[dict[str, Any]]:
        today = _eastern_day(as_of)
        out = []
        for m in meetings:
            ts = datetime.combine(m["date"], time(0), tzinfo=EASTERN) - self._notice
            if not (since < ts <= as_of):
                continue
            status = "scheduled" if m["date"] >= today else "held"
            out.append({
                "ts": ts.isoformat(), "event_date": m["date"].isoformat(),
                "end_date": m["through"].isoformat() if m["through"] else None,
                "headline": f"FDA advisory committee meeting {status} for {m['date'].isoformat()}: {m['title']}",
                "meeting": m["title"], "center": m["center"], "status": status,
                "category": "fda", "source": "FDA advisory-committee calendar via Equibles", "url": m["url"],
            })
        return out

    # -- earnings ------------------------------------------------------------------

    async def upcoming_earnings(self, ticker: str, as_of: datetime) -> DataSnapshot:
        estimate = await self._estimated_earnings(ticker, as_of)
        # The company's IR calendar only lists events after *today*, so it can answer for a
        # live run but not for a past as_of (it can't say what was announced back then).
        if as_of < self._now() - timedelta(days=1):
            return estimate
        try:
            text = await self._mcp.call_tool(IR_EVENTS, {"ticker": ticker, "eventType": "EarningsCall",
                                                        "maxResults": 5})
        except Exception:
            return estimate
        today = visible_before(as_of)
        calls = [e for e in parse_upcoming_events(str(text)) if date.fromisoformat(e["date"]) >= today]
        if not calls:
            return estimate
        nxt = calls[0]
        payload: dict[str, Any] = {
            "next_earnings_date": nxt["date"], "confirmed": True,
            "basis": "company investor-relations calendar (announced)",
            "event": nxt["title"], "time_utc": nxt["time"], "url": nxt["url"],
        }
        if not estimate.is_gap:
            payload["estimate_from_8k_cadence"] = estimate.payload["next_earnings_date"]
        return DataSnapshot(kind="earnings_calendar", source=SOURCE, subject=ticker, as_of=as_of, payload=payload,
                            note="Announced by the company; live runs only (the IR calendar lists future events only).")

    async def _estimated_earnings(self, ticker: str, as_of: datetime) -> DataSnapshot:
        cutoff = visible_before(as_of)
        start = cutoff - self._earnings_lookback
        parsed, meta = await _list_filings(self._mcp, ticker, start, cutoff - timedelta(days=1),
                                           document_type="8-K", item="2.02", max_items=40)
        if meta["status"] in ("not_found", "unparsed"):
            return _gap("earnings_calendar", ticker, as_of, meta.get("message") or f"No Equibles filings for {ticker}.")
        filed = sorted({r["filed"] for r in parsed if r["filed"] < cutoff and "2.02" in r["sec_items"]})
        estimate = estimate_next_earnings(filed, cutoff)
        if estimate is None:
            return _gap("earnings_calendar", ticker, as_of,
                        f"Next earnings date unknown: Equibles has no earnings calendar, and {ticker} has too "
                        "few or irregular 8-K item 2.02 filings to estimate one.")
        next_date, method = estimate
        return DataSnapshot(
            kind="earnings_calendar", source=SOURCE, subject=ticker, as_of=as_of,
            payload={"next_earnings_date": next_date.isoformat(), "confirmed": False,
                     "basis": "estimated from past 8-K 2.02 cadence", "method": method,
                     "last_results_filed": filed[-1].isoformat(),
                     "past_results_filed": [d.isoformat() for d in filed[-8:]]},
            note="Estimate, not a confirmed date. Backtests and companies without an announced date "
                 "use this estimate; live runs prefer the company's announced date.")


def estimate_next_earnings(filed: Sequence[date], today: date) -> tuple[date, str] | None:
    """Estimate the next results date from past 8-K item 2.02 filing dates (sorted, unique).

    Filings within 20 days of each other count as one release, dated by the later one
    (pre-announcements, amended releases). Preferred: the release ~1 year before the next expected one plus
    52 weeks (companies keep a yearly cycle, with a later Q4). Fallback: last release plus
    the median gap. Returns None with fewer than 2 releases, a non-quarterly/semiannual
    cadence, or when the estimate is more than 30 days overdue (cadence broken).
    """
    releases: list[date] = []
    for d in filed:
        if releases and (d - releases[-1]).days <= 20:
            releases[-1] = d  # keep the later filing (full results follow a pre-announcement)
        else:
            releases.append(d)
    if len(releases) < 2:
        return None
    gaps = [(b - a).days for a, b in zip(releases, releases[1:])][-8:]
    median_gap = statistics.median(gaps)
    if not 60 <= median_gap <= 200:
        return None
    last = releases[-1]
    earliest = last + timedelta(days=int(median_gap * 0.6))
    yearly = sorted(d + timedelta(weeks=52) for d in releases if d + timedelta(weeks=52) >= earliest)
    if yearly and (yearly[0] - last).days <= median_gap * 1.5:
        estimate, method = yearly[0], "same release a year earlier + 52 weeks"
    else:
        estimate, method = last + timedelta(days=round(median_gap)), f"last release + median gap ({median_gap:g} days)"
    if estimate < today:
        if (today - estimate).days > 30:
            return None
        estimate, method = today, method + "; overdue, so treated as imminent"
    return estimate, method

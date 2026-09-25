"""Equibles filings / 8-K events / FDA meetings / earnings estimate, against a fake MCP
server that answers in Equibles' exact output formats."""

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from trading_pipeline.data.equibles_events import (
    FDA_MEETINGS, LIST_FILINGS, EquiblesFilings, EquiblesNews, estimate_next_earnings,
    mentions_company, parse_filings,
)
from trading_pipeline.rules import is_material

ET = ZoneInfo("America/New_York")


def esc(v):
    """Equibles MarkdownTable.EscapeCell (Equibles.Mcp/Helpers/MarkdownTable.cs)."""
    return v.replace("\\", "\\\\").replace("|", "\\|") if v else ""


# (form, filed, reporting-for, items)
FILINGS = [
    ("8-K", "2025-05-01", "2025-05-01", "2.02,9.01"),
    ("10-Q", "2025-05-05", "2025-03-31", ""),
    ("8-K", "2025-07-31", "2025-07-31", "2.02,9.01"),
    ("10-Q", "2025-08-04", "2025-06-30", ""),
    ("8-K", "2025-10-30", "2025-10-30", "2.02,9.01"),
    ("10-Q", "2025-11-03", "2025-09-30", ""),
    ("8-K", "2026-02-19", "2026-02-19", "2.02,9.01"),
    ("10-K", "2026-02-20", "2025-12-31", ""),
    ("8-K", "2026-03-10", "2026-03-09", "5.02"),
    ("8-K", "2026-03-15", "2026-03-15", "7.01,9.01"),
    ("8-K/A", "2026-03-20", "2026-03-09", "5.02"),
    ("8-K", "2026-04-30", "2026-04-30", "2.02,9.01"),
    ("10-Q", "2026-05-04", "2026-03-31", ""),
    ("8-K", "2026-06-10", "2026-06-08", "1.01,2.03,9.01"),
    ("8-K", "2026-07-30", "2026-07-30", "2.02,9.01"),
    ("10-Q", "2026-08-03", "2026-06-30", ""),
    ("8-K", "2026-08-10", "2026-08-07", "4.02"),
]

# (date, title, center, through, url)
MEETINGS = [
    ("2026-08-01", "August 1, 2026: Meeting of the Oncologic Drugs Advisory Committee Meeting Announcement",
     "Center for Drug Evaluation and Research", None, "https://www.fda.gov/a"),
    ("2026-09-15", "September 15, 2026: Meeting of the Cellular, Tissue, and Gene Therapies Advisory Committee "
     "to discuss BLA 125999 from Acme Therapeutics | ACM-101", "Center for Biologics Evaluation and Research",
     "2026-09-16", "https://www.fda.gov/b"),
    ("2026-10-05", "October 5, 2026: Meeting of the Peripheral and Central Nervous System Drugs Advisory Committee",
     "Center for Drug Evaluation and Research", None, None),
    ("2026-11-20", "November 20, 2026: Meeting of the Pharmacy Compounding Advisory Committee",
     "Center for Drug Evaluation and Research", None, "https://www.fda.gov/d"),
]


FIX = __import__("pathlib").Path(__file__).parent / "fixtures" / "equibles_live"


class FakeEquibles:
    def __init__(self, company="Acme Therapeutics, Inc."):
        self.company = company
        self.calls = []

    async def call_tool(self, name, args):
        self.calls.append((name, args))
        assert name in EquiblesNews.TOOLS | EquiblesFilings.TOOLS
        if name == "GetInvestorRelationsNews":  # real hosted coverage-gap answer
            return (FIX / "GetInvestorRelationsNews.gap.md").read_text()
        if name == "GetUpcomingInvestorEvents":
            return (FIX / "GetUpcomingInvestorEvents.none.md").read_text()
        return self.list_filings(**args) if name == LIST_FILINGS else self.fda(**args)

    def list_filings(self, ticker=None, page=1, maxItems=10, startDate=None, endDate=None,
                     documentType=None, itemNumber=None):
        # Equibles.Sec.Mcp/Tools/RagSearchTools.cs ListFilings (+ SecDocumentService.BuildDocumentsQuery:
        # inclusive ReportingDate range, exact type and item filters, newest first).
        if ticker != "ACME":
            return f"Stock '{ticker}' not found."
        docs = [f for f in FILINGS
                if (startDate is None or f[1] >= startDate) and (endDate is None or f[1] <= endDate)
                and (documentType is None or f[0] == documentType)
                and (itemNumber is None or itemNumber in f[3].split(","))]
        docs.sort(key=lambda f: f[1], reverse=True)
        if not docs:
            return (f"No documents match the given filters for ACME — {len(FILINGS):,} document(s) exist "
                    "without them. Relax documentType/itemNumber/startDate/endDate.")
        total, pages = len(docs), (len(docs) + maxItems - 1) // maxItems
        shown = docs[(page - 1) * maxItems: page * maxItems]
        lines = [f"Financial documents for {esc(self.company)} (ACME) — page {page} of {pages:,} ({total:,} documents):",
                 "",
                 "Ticker | Company | ID | Type | Filed | Reporting For | Items | Lines",
                 "-------|---------|----|------|-------|---------------|-------|------"]
        for i, (form, filed, period, items) in enumerate(shown):
            doc_id = f"00000000-0000-0000-0000-{abs(hash((form, filed))) % 10**12:012d}"
            lines.append(f"ACME | {esc(self.company)} | {doc_id} | {form} | {filed} | {period} | "
                         f"{esc(items) or '—'} | {1234 + i:,}")
        return "\n".join(lines) + "\n"

    def fda(self, startDate=None, endDate=None, maxResults=60):
        # Equibles.FdaCatalysts.Mcp/Tools/FdaCatalystTools.cs GetFdaAdvisoryCommitteeMeetings
        # (MarkdownTable.Render; Clean() turns '|' into '/'; inclusive MeetingDate range).
        rows = sorted((m for m in MEETINGS if startDate <= m[0] <= endDate), key=lambda m: (m[0], m[1]))
        if not rows:
            return (f"No FDA advisory-committee meetings found between {startDate} and {endDate}. The calendar "
                    "currently covers 2025-11-01 to 2026-11-20 — meetings outside that span have not been "
                    "announced or predate coverage.")
        body = "\n".join(
            f"| {d} | {t.replace('|', '/')} | {c} | Advisory Committee Meeting | {th or '—'} | {u or '—'} |"
            for d, t, c, th, u in rows[:maxResults])
        return (f"FDA Catalyst Calendar (advisory-committee meetings, {startDate} to {endDate}):\n\n"
                "| Date | Meeting | Center | Type | Through | Details |\n"
                "|------|---------|--------|------|---------|---------|\n" + body + "\n")


def et(y, m, d, h=17):
    return datetime(y, m, d, h, tzinfo=ET)


# ---------------------------------------------------------------------------- parsing


def test_parse_list_filings_output():
    rows, meta = parse_filings(FakeEquibles(company="Acme | Co").list_filings("ACME", maxItems=3))
    assert meta["company"] == "Acme | Co" and meta["total"] == len(FILINGS) and meta["pages"] == 6
    assert [r["form"] for r in rows] == ["8-K", "10-Q", "8-K"]
    assert rows[0]["filed"] == date(2026, 8, 10) and rows[0]["sec_items"] == ["4.02"]
    assert rows[1]["sec_items"] == [] and rows[1]["period"] == "2026-06-30"
    assert parse_filings("Stock 'ZZZ' not found.")[1]["status"] == "not_found"


# ---------------------------------------------------------------------------- filings


async def test_filings_hidden_until_day_after_filing():
    fake = FakeEquibles()
    snap = await EquiblesFilings(fake).recent_filings("ACME", et(2026, 1, 1), et(2026, 3, 10))
    assert snap.kind == "filings" and not snap.is_gap
    assert [f["filed"] for f in snap.payload] == ["2026-02-20", "2026-02-19"]  # 03-10 8-K not yet visible
    assert all(f["filed"] < "2026-03-10" for f in snap.payload)
    ten_k = snap.payload[0]
    assert ten_k["form"] == "10-K" and ten_k["period"] == "2025-12-31" and ten_k["title"].startswith("10-K for period")
    assert {c[1]["documentType"] for c in fake.calls} == {"10-K", "10-Q", "8-K"}

    later = await EquiblesFilings(fake).recent_filings("ACME", et(2026, 1, 1), et(2026, 3, 11, 0))
    assert later.payload[0]["filed"] == "2026-03-10" and later.payload[0]["sec_items"] == ["5.02"]
    assert "Departure or appointment" in later.payload[0]["title"]


async def test_filings_unknown_ticker_is_gap():
    snap = await EquiblesFilings(FakeEquibles()).recent_filings("ZZZ", et(2026, 1, 1), et(2026, 3, 10))
    assert snap.is_gap and "not found" in snap.note


# ---------------------------------------------------------------------------- 8-K events


async def test_ticker_events_categories_and_materiality():
    snap = await EquiblesNews(FakeEquibles()).events("ACME", et(2026, 1, 1), et(2026, 9, 25))
    by_filed = {(e.get("filed"), e.get("sec_form")): e for e in snap.payload}
    earnings = by_filed[("2026-07-30", "8-K")]
    assert earnings["category"] == "earnings" and earnings["headline"] == (
        "Acme Therapeutics, Inc. 8-K: Results of operations and financial condition")
    assert by_filed[("2026-03-10", "8-K")]["category"] == "management_change"
    assert by_filed[("2026-03-20", "8-K/A")]["category"] == "management_change"
    assert by_filed[("2026-08-10", "8-K")]["category"] == "restatement"
    assert by_filed[("2026-06-10", "8-K")]["category"] == "material_agreement"

    expected = {"2026-07-30": True, "2026-03-10": True, "2026-08-10": True, "2026-06-10": True,
                "2026-03-15": False}  # 7.01 Reg FD only -> noise
    for filed, material in expected.items():
        assert is_material(by_filed[(filed, "8-K")])[0] is material, filed


async def test_ticker_events_point_in_time_and_windows_partition():
    news = EquiblesNews(FakeEquibles(), match_fda_to_tickers=False)
    as_of = et(2026, 3, 10)  # the 5.02 8-K filed today must not show
    snap = await news.events("ACME", et(2026, 1, 1), as_of)
    assert all(datetime.fromisoformat(e["ts"]) <= as_of for e in snap.payload)
    assert all(e["filed"] < "2026-03-10" for e in snap.payload)
    assert [e["filed"] for e in snap.payload] == ["2026-02-19"]

    # Consecutive follow-up windows see each 8-K exactly once.
    ticks = [et(2026, 3, 1) + timedelta(hours=12 * i) for i in range(60)]
    seen = []
    for a, b in zip(ticks, ticks[1:]):
        seen += [e["filed"] for e in (await news.events("ACME", a, b)).payload]
    assert sorted(seen) == ["2026-03-10", "2026-03-15", "2026-03-20"]


async def test_ticker_events_match_fda_meeting_by_company_name():
    snap = await EquiblesNews(FakeEquibles()).events("ACME", et(2026, 8, 1), et(2026, 9, 25))
    fda = [e for e in snap.payload if e["category"] == "fda"]
    assert len(fda) == 1 and fda[0]["event_date"] == "2026-09-15" and "Acme Therapeutics / ACM-101" in fda[0]["meeting"]
    assert fda[0]["status"] == "held" and is_material(fda[0])[0]
    assert mentions_company("Advisory Committee to discuss Eli Lilly's BLA", "Eli Lilly and Company")
    assert not mentions_company("Pharmacy Compounding Advisory Committee", "Co Inc")  # name too generic


# ---------------------------------------------------------------------------- sector / FDA


async def test_sector_fda_meetings_only_once_plausibly_announced():
    fake = FakeEquibles()
    as_of = et(2026, 9, 25)
    snap = await EquiblesNews(fake).events("Biotech", as_of - timedelta(days=90), as_of)
    assert snap.kind == "news_catalysts" and not snap.is_gap
    dates = [e["event_date"] for e in snap.payload]
    # 10-05 is within the 15-day notice window (known by 09-20); 11-20 is not yet knowable.
    assert dates == ["2026-08-01", "2026-09-15", "2026-10-05"]
    assert all(datetime.fromisoformat(e["ts"]) <= as_of for e in snap.payload)
    assert {e["event_date"]: e["status"] for e in snap.payload}["2026-10-05"] == "scheduled"
    assert snap.payload[2]["url"] is None and snap.payload[0]["url"] == "https://www.fda.gov/a"
    assert "15 days" in snap.note and "late 2025" in snap.note
    assert fake.calls == [(FDA_MEETINGS, {"startDate": "2026-07-12", "endDate": "2026-10-10", "maxResults": 200})]

    wider = await EquiblesNews(FakeEquibles(), fda_notice_days=60).events("Biotech", as_of - timedelta(days=90), as_of)
    assert "2026-11-20" in [e["event_date"] for e in wider.payload]


async def test_sector_without_event_source_is_gap():
    fake = FakeEquibles()
    snap = await EquiblesNews(fake).events("Energy", et(2026, 6, 1), et(2026, 9, 25))
    assert snap.is_gap and "sector" in snap.note and fake.calls == []


async def test_sector_empty_calendar_is_empty_not_gap():
    snap = await EquiblesNews(FakeEquibles()).events("Pharmaceuticals", et(2025, 1, 1), et(2025, 3, 1))
    assert not snap.is_gap and snap.payload == []


# ---------------------------------------------------------------------------- earnings


async def test_upcoming_earnings_estimated_from_2_02_cadence():
    fake = FakeEquibles()
    snap = await EquiblesNews(fake).upcoming_earnings("ACME", et(2026, 9, 25))
    assert snap.kind == "earnings_calendar" and not snap.is_gap
    p = snap.payload
    assert p["next_earnings_date"] == "2026-10-29" and p["confirmed"] is False  # 2025-10-30 + 52 weeks
    assert p["basis"] == "estimated from past 8-K 2.02 cadence" and p["last_results_filed"] == "2026-07-30"
    assert fake.calls[0][1]["itemNumber"] == "2.02" and fake.calls[0][1]["documentType"] == "8-K"


async def test_upcoming_earnings_ignores_same_day_filing():
    snap = await EquiblesNews(FakeEquibles()).upcoming_earnings("ACME", et(2026, 7, 30, 20))
    assert snap.payload["last_results_filed"] == "2026-04-30"
    assert snap.payload["next_earnings_date"] == "2026-07-30"  # 2025-07-31 + 52 weeks


async def test_upcoming_earnings_gap_without_history():
    snap = await EquiblesNews(FakeEquibles()).upcoming_earnings("ACME", et(2025, 6, 1))
    assert snap.kind == "earnings_calendar" and snap.is_gap


def test_estimate_next_earnings_fallbacks():
    d = date.fromisoformat
    # Half a year of history: last + median gap.
    est, method = estimate_next_earnings([d("2026-02-01"), d("2026-05-01"), d("2026-08-01")], d("2026-09-01"))
    assert est == d("2026-10-30") and "median" in method
    # A pre-announcement 10 days before results counts as one release.
    est, _ = estimate_next_earnings([d("2026-04-20"), d("2026-04-30"), d("2026-07-30")], d("2026-08-15"))
    assert est == d("2026-10-29")  # 07-30 + 91 days
    assert estimate_next_earnings([d("2025-01-01"), d("2026-06-01")], d("2026-07-01")) is None  # irregular
    assert estimate_next_earnings([d("2025-11-01"), d("2026-02-01")], d("2026-07-01")) is None  # far overdue
    est, method = estimate_next_earnings([d("2026-02-01"), d("2026-05-01")], d("2026-08-10"))
    assert est == d("2026-08-10") and "overdue" in method


def test_tools_are_read_only_listing_tools():
    assert EquiblesFilings.TOOLS == frozenset({"ListFilings"})
    assert EquiblesNews.TOOLS == frozenset({"ListFilings", "GetFdaAdvisoryCommitteeMeetings",
                                            "GetUpcomingInvestorEvents", "GetInvestorRelationsNews"})




# ------------------------------------------------------------------------------------
# Equibles Cloud: IR earnings calendar and press releases (real hosted formats)
# ------------------------------------------------------------------------------------

from trading_pipeline.data.equibles_events import parse_ir_news, parse_upcoming_events  # noqa: E402


def test_parse_ir_formats():
    events = parse_upcoming_events((FIX / "GetUpcomingInvestorEvents.md").read_text())
    assert [(e["date"], e["time"], e["type"]) for e in events] == [
        ("2026-10-01", "18:00", "Earnings call"), ("2026-10-01", "21:00", "Earnings call")]
    assert events[0]["url"].startswith("https://investors.nike.com/")
    news = parse_ir_news((FIX / "GetInvestorRelationsNews.md").read_text())
    assert len(news) == 3 and news[0]["date"] == "2026-09-14" and "CUDA-Q" in news[0]["headline"]
    assert parse_upcoming_events((FIX / "GetUpcomingInvestorEvents.none.md").read_text()) == []
    assert parse_ir_news((FIX / "GetInvestorRelationsNews.gap.md").read_text()) == []


class CloudFake(FakeEquibles):
    async def call_tool(self, name, args):
        if name == "GetUpcomingInvestorEvents":
            self.calls.append((name, args))
            return (FIX / "GetUpcomingInvestorEvents.md").read_text()
        if name == "GetInvestorRelationsNews":
            self.calls.append((name, args))
            return (FIX / "GetInvestorRelationsNews.md").read_text()
        return await super().call_tool(name, args)


async def test_live_run_prefers_announced_earnings_date():
    live = datetime(2026, 9, 25, 21, tzinfo=timezone.utc)
    news = EquiblesNews(CloudFake(), now=lambda: live)
    snap = await news.upcoming_earnings("ACME", live)
    assert snap.payload["confirmed"] is True and snap.payload["next_earnings_date"] == "2026-10-01"
    assert "investor-relations" in snap.payload["basis"]


async def test_backtest_never_uses_the_forward_only_ir_calendar():
    live = datetime(2026, 9, 25, 21, tzinfo=timezone.utc)
    fake = CloudFake()
    snap = await EquiblesNews(fake, now=lambda: live).upcoming_earnings("ACME", live - timedelta(days=30))
    assert not any(n == "GetUpcomingInvestorEvents" for n, _ in fake.calls)
    assert snap.is_gap or snap.payload["confirmed"] is False


async def test_press_releases_become_point_in_time_events():
    as_of = datetime(2026, 9, 14, 21, tzinfo=timezone.utc)  # 09-14 release not known until 09-15
    news = EquiblesNews(CloudFake(), now=lambda: as_of)
    snap = await news.events("ACME", datetime(2026, 8, 1, tzinfo=timezone.utc), as_of)
    press = [e for e in snap.payload if e["source"].startswith("company investor relations")]
    assert [e["published"] for e in press] == ["2026-09-10", "2026-08-31"]
    assert all(e["ts"] <= as_of.isoformat() for e in press) and press[0]["url"]


async def test_press_release_coverage_gap_is_noted():
    as_of = datetime(2026, 9, 25, 21, tzinfo=timezone.utc)
    snap = await EquiblesNews(FakeEquibles(), now=lambda: as_of).events(
        "ACME", datetime(2026, 1, 1, tzinfo=timezone.utc), as_of)
    assert "coverage gap" in snap.note

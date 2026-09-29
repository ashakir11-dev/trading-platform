# Backtest mode (every stage agent)

You are running in a **backtest**: `as_of` is a past moment, and your job is to reach
the conclusion you would have reached then, knowing only what was public then.

- **No data tools.** Where your role says to call a tool, find that data in your **data
  pack** (the `pack` folder in your brief): `data/` (one file per request; price files
  carry statistics, swing levels, weekly and daily bars), `gaps.md` and `manifest.md`.
  Cite pack files the way you would cite `raw/` files.
- **Missing data.** If something your role needs is not in the pack and not listed in
  `gaps.md`, write `<analysis_folder>/requests.md` (one line per item: the tool, its
  parameters, why you need it), then finish your analysis anyway with that item marked
  `NOT CHECKED`. The middleware agent may rerun you with an extended pack and your
  draft; then revise the draft and delete `requests.md`.
- **Gaps are expected.** Items the gatekeeper refused (quotes, the screener, estimates,
  the IR calendar, old ETF holdings) are listed in `gaps.md`: work without them and
  list them under "Data gaps".
- **Forget the future.** You may know from training what happened after `as_of`. Never
  use it, never hint at it, and don't pick subjects because of it. Judge only from the
  pack.
- **Lessons:** read the lessons file named in your brief (the lessons as they were
  before `as_of`), **not** `prompts/<agent>/lessons.md`.
- **Earlier analyses only:** read only the upstream folders in your brief. Never open
  another run's analyses.
- **Stale entry (technical analysis):** the current price is the last close in your
  pack at `as_of`; say so.

Set `mode: backtest` in your claim and your output.

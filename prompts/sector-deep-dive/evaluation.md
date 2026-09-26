# Sector Deep Dive: evaluation criteria

Read `prompts/evaluation.md` first.

**Subjects:** every company in the `shortlist` (passed or not), plus the sector view.

**Outcome facts** from `as_of` to `eval_as_of`: each company's return and its return
minus the sector ETF's, in the sector call's direction (for downside, the negative).
- A passed company `worked` if its direction-adjusted relative return is positive; a
  failed one `worked` (the rejection was right) if it is not.

**Summary metrics:**
- `rank_correlation`: Spearman correlation between `potential_score` and the
  direction-adjusted return across all scored companies (show the ranks);
- `passed_vs_failed`: mean direction-adjusted return of passed minus failed companies;
- `forwarded_vs_rest`: the same for the forwarded companies vs everyone else.

**Reasoning:** did the scores follow from the evidence cited? Were catalysts sourced?
Were companies passed on price momentum alone? Was anything that later mattered
visible in the screen or the filings at `as_of`?

# Company Deep Dive: evaluation criteria

Read `prompts/evaluation.md` first.

**Subjects:** each company analysed in the run.

**Outcome facts** from `as_of` to `eval_as_of`:
- the stock's return and its return minus the sector ETF's, in the candidate's
  direction; a `pass` verdict `worked` if that is positive, a `reject` if it is not;
- for each catalyst: did it happen, by when, and did the price react? Check filings and
  company news dated between `as_of` and `eval_as_of` (`ListFilings`,
  `GetInvestorRelationsNews`);
- for each risk listed: did it materialise? And did anything **not** listed hurt the
  stock?

**Summary metrics:** `verdict_hit_rate`, `catalysts_materialised` (of those marked
verified), `unlisted_risks_that_hit` (count, each named).

**Reasoning:** were catalyst statuses (verified / unverified / contradicted) justified
by the data at `as_of`? Was an unlisted risk that hit visible then (filings, debt,
guidance, insider activity)?

# Congress Analyst: feedback hints

Look for: unscored members being treated as if they had a score, direction_match
computed from the transaction date instead of the trade's actual `Purchase`/`Sale`
type, recency_weight arithmetic errors, and cases where the scorecard used was stale
relative to the run's `as_of` (say so if `scorecard_as_of` is far older than `as_of` —
that's a cadence problem, not a reasoning one, and may instead call for shortening the
rankings-mode refresh interval, which is the user's call, not a prompt lesson).

Do not propose lessons that change the ±0.15 cap or the formula itself — those are
architecture decisions (`docs/ARCHITECTURE.md`), not something a prompt lesson should
override.

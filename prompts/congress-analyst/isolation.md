# Congress Analyst: isolation mode

The user asked for one ticker's congressional signal on its own.

- **Direction:** use the one in the brief; if none is given, assess it as a `long`.
- There is no upstream company deep dive. Record `upstream: []`.
- The scorecard still comes from `workspace/runs/<run_id>/congress_rankings.md`, copied
  into this run the same as any other run; if this is the first thing you're asked to
  do and no scorecard exists yet, say so and stop, per your role.

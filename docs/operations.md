# Operating the pipeline

How to configure, run and operate the system day to day with the `trading-pipeline`
command. It is **decision support only**: no command places, changes or cancels an
order. `decide` and `close` only *record* what you decided or did. Your decisions are
stored apart from the system's records and never reach any agent.

## 1. Install

```sh
python -m venv .venv && . .venv/bin/activate
pip install -e '.[equibles]'     # adds the MCP client used to reach Equibles
trading-pipeline --help          # or: python -m trading_pipeline --help
```

## 2. Configure

| Setting | Environment variable | Flag | Default |
|---|---|---|---|
| Equibles API key (market data) | `EQUIBLES_API_KEY` | | required for `run`, `follow-up`, `review` |
| Anthropic API key (agents) | `ANTHROPIC_API_KEY` or `TRADING_ANTHROPIC_API_KEY` | | required for `run`, `follow-up`, `review`; `TRADING_ANTHROPIC_API_KEY` wins if both are set |
| Database | `TRADING_DB` | `--db` | `~/.trading-platform/pipeline.sqlite3` (directory is created) |
| Investor profile | `TRADING_PROFILE` | `--profile` | built-in default profile |
| Model override | `TRADING_MODEL` | `--model` | `LLMConfig.model` |
| Effort override | `TRADING_EFFORT` | `--effort` | `LLMConfig.effort` |

Flags win over environment variables. Use `TRADING_ANTHROPIC_API_KEY` where
`ANTHROPIC_API_KEY` is reserved, e.g. Claude Code on the web, whose environment
settings keep that name for Claude Code's own login and do not pass it into sessions. Store-only commands (`report`, `decide`,
`positions`, `close`, `notes`, `approve-note`, `profile`) need no keys.

Keep keys out of shell history and the repo, e.g. in `~/.trading-platform/env`
(`chmod 600`):

```sh
export EQUIBLES_API_KEY=...
export ANTHROPIC_API_KEY=...
export TRADING_PROFILE=~/.trading-platform/profile.json
```

**Profile.** Copy `profile.example.json`, edit it (risk tolerance, horizons, shorts,
max loss, reward:risk, `level_trigger`, notes; see ARCHITECTURE.md §4), then check it:

```sh
trading-pipeline profile validate ~/.trading-platform/profile.json
trading-pipeline profile show        # the profile the pipeline will actually use
```

**Data.** All data comes from the hosted Equibles MCP server through one read-only
client whose tool allowlist is the union of the tools of the adapters that are
installed. A data category whose adapter module is not installed yet falls back to
its gap placeholder: the run still works, the CLI logs a warning, and agents see that
data marked `UNAVAILABLE`.

## 3. Pre-flight check

```sh
trading-pipeline check                       # AAPL and Health Care by default
trading-pipeline check --ticker NVDA --sector Technology
```

Calls every data source once (roughly 100 Equibles calls, no LLM: that is the whole
daily allowance of the Free plan, so use Plus) and prints OK / WARN / FAIL per data type. It exits 1 on any FAIL, because a run would otherwise hand the agents
missing data. WARN is expected for the quote on the Free plan (last close, not live).

For a first run, keep it small and read the output closely:

```sh
trading-pipeline run --max-sectors 1 --shortlist 3
```

`--max-sectors N` pursues only the N highest-confidence sectors from Agent 0 (the others
are listed as not pursued); `--shortlist N` forwards at most N companies per sector.

## 4. Daily run (after the close)

```sh
trading-pipeline run                       # as of now; uses live quotes
trading-pipeline run --as-of 2026-06-01    # that day's 16:00 New York close
trading-pipeline run --backtest --as-of 2026-06-01T20:00:00+00:00
trading-pipeline report                    # show the latest report again
trading-pipeline report RUN_ID             # a specific run
```

Run it after the US close (16:00 New York) so daily bars are final. A date means that
day's close. A past date always runs as a backtest (live quotes are not point-in-time),
and `--backtest` forces that for today too. The report is saved; its header shows the
run id, and each recommendation shows its `candidate_id`.

## 5. Workflow: decide → follow-up → close → review → approve

```sh
trading-pipeline decide CANDIDATE_ID accept --note "half size"   # or: reject
trading-pipeline positions            # open positions with entry/target/stop
trading-pipeline follow-up            # one Agent 5 tick (usually from cron)
trading-pipeline close POSITION_ID --price 123.45 [--date 2026-06-20]
trading-pipeline review POSITION_ID   # outcome (facts) + process review (reasoning)
trading-pipeline notes                # improvement notes waiting for approval
trading-pipeline approve-note NOTE_ID
```

1. **Decide.** Only recommended candidates can be decided, once each. `accept` opens a
   watched position from the technical plan (`--opened DATE` if you entered earlier);
   you place the trade yourself. `reject` is recorded and nothing is watched.
2. **Follow up.** Each tick checks every open position: price against stop and target
   (per the profile's `level_trigger`) and material news. An alert triggers a full LLM
   re-review (hold / adjust plan / exit); so does the 14-day review interval. Alerts
   for one position are held for 12 hours after the previous one and delivered
   together afterwards. When a stop or target is hit, or a re-review recommends exit,
   the output says `ACTION NEEDED` with the `close` and `review` commands to run.
3. **Close** when you have exited, with your actual exit price and date.
4. **Review.** The outcomes agent computes return, drawdown and stop/target hits
   without judgment; the process agent grades each stage's reasoning and may suggest
   improvement notes. It never sees your accept/reject or notes. You can also review
   an open position for an interim look.
5. **Approve** only the notes you agree with. Only approved notes are added to future
   prompts of the stage they target.

## 6. Scheduling (cron)

Cron runs with a minimal environment, so each line sources the env file and uses absolute paths.
Times below are in New York time via `CRON_TZ` (supported by cronie; with other crons,
convert to the machine's zone).

```cron
CRON_TZ=America/New_York

# Daily run after the close, Monday to Friday.
30 16 * * 1-5  . $HOME/.trading-platform/env && $HOME/trading-platform/.venv/bin/trading-pipeline run >> $HOME/.trading-platform/run.log 2>&1

# Agent 5 every 2 hours during market hours (10:00, 12:00, 14:00), plus once after the close.
0 10-14/2 * * 1-5  . $HOME/.trading-platform/env && $HOME/trading-platform/.venv/bin/trading-pipeline follow-up --quiet 2>&1 | mail -E -s "trading follow-up" you@example.com
15 16 * * 1-5      . $HOME/.trading-platform/env && $HOME/trading-platform/.venv/bin/trading-pipeline follow-up --quiet 2>&1 | mail -E -s "trading follow-up" you@example.com
```

`follow-up --quiet` prints nothing when all positions are quiet, so `mail -E` (skip empty
mail) only sends alerts, re-reviews and needed actions. Market holidays are not skipped;
a tick on a holiday just finds no new data.

## 7. Where data is stored

Everything lives in one SQLite file (`TRADING_DB`, default
`~/.trading-platform/pipeline.sqlite3`):

- `docs` table: saved reports, stage records (every agent's structured reasoning), raw
  data snapshots each stage saw, candidates, positions, tripwire checks, outcomes,
  process reviews, improvement notes, conflicts.
- `user_decisions` table: your accept/reject decisions and notes, kept apart and never
  read by any agent.

Back it up by copying the file while no command is running. Deleting it resets the
system, including approved improvement notes.

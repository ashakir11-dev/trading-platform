# Operating the pipeline

How to set up, run and operate the system day to day. It is **decision support only**:
no command places, changes or cancels an order. `/decide` and `/trade` only *record*
what you decided or did. Your decisions are stored apart from everything the agents
read, and a hook blocks every agent from them.

The design behind this is in [`prompt-subagents-design.md`](prompt-subagents-design.md).

## 1. Set up

- The [Claude Code](https://code.claude.com) CLI.
- `ANTHROPIC_API_KEY` for the agents.
- `EQUIBLES_API_KEY` for market data. The Plus plan or better: a full run makes a few
  hundred data calls (the Free plan allows 100 a day), and Plus turns on live quotes.

Keep the keys out of shell history and the repository, e.g. in
`~/.trading-platform/env` (`chmod 600`):

```sh
export ANTHROPIC_API_KEY=...
export EQUIBLES_API_KEY=...
```

**Once per machine:** start `claude` in the repository and accept the trust dialog and
the `equibles` MCP server (`.mcp.json`). Until then Claude Code ignores the project's
permission allow rules; the hooks and deny rules apply either way.

**Profile.** Copy `profile.example.json` to `workspace/profile.json` and edit it: risk
tolerance, horizons, shorts, max loss, reward:risk, `level_trigger`, notes (see
ARCHITECTURE.md §4). Without it, the example profile is used. Each run copies the
profile it used into its run folder.

**Models.** Each agent's model and effort are set in its file in `.claude/agents/`; the
table and the reasoning are in the design doc (§11).

## 2. First run

Inside `claude` in the repository:

```
/run --max-sectors 1 --shortlist 3
```

`--max-sectors N` pursues only the N highest-confidence sectors the market scanner
calls (downside sectors are skipped when your profile doesn't allow shorts);
`--shortlist N` forwards at most N companies per sector. A run like this takes about
15 minutes. Read the report and the agents' analyses closely.

## 3. Daily run (after the close)

```
/run
```

Run it after the US close (16:00 New York) so daily bars are final. The report is shown
and saved to `workspace/runs/<run_id>/report.md`; each recommendation shows its
`candidate_id`. One agent on its own: `/run-agent <agent> <subject>`, e.g.
`/run-agent sector-deep-dive "Energy" upside` or `/run-agent technical-analysis NVDA`.

## 4. Workflow: decide → trade → follow up → evaluate → improve

```
/decide <candidate_id> accept "half size"     # or: reject
/trade <position_id> entered 118.40           # when you have actually bought
/follow-up                                    # one tick over open positions (schedule it)
/trade <position_id> exited 134.10 2026-10-20 0.5  # sold half at T1
/trade <position_id> exited 131.10 2026-10-30 # when you have exited the rest
/evaluate                                     # grade runs at least a week old
/feedback <agent>                             # propose lessons for one agent
/approve <agent> <proposal_id>                # or: ... reject
```

1. **Decide.** Only recommended candidates can be decided, once each. `accept` opens a
   watched position from the technical plan (`position_id` = `candidate_id`); you place
   the trade yourself. `reject` is recorded and nothing is watched.
2. **Trade.** Record your actual entries and exits, in full or in part
   (`/trade <id> entered|exited <price> [date] [fraction]`); only the prices, dates and
   fractions reach the position file.
3. **Follow up.** Each tick checks every open position: the entry (triggered, missed or
   expired), the stop in force, each target and the trailing stop (per the profile's
   `level_trigger`), the plan's clocks (checkpoints, max hold, earnings in the event
   plan) and material news. Price and clock alerts are delivered at once; news alerts
   are held for 12 hours after the previous one and delivered together afterwards. A
   delivered alert, or the trade type's cadence (3 / 5 / 10 / 20 sessions), triggers a
   full re-review (hold / adjust plan / exit). When an alert asks you to act, or a
   re-review says exit, the output starts with **ACTION NEEDED**.
4. **Evaluate.** Grades each agent's past calls against what happened since: outcome
   facts, and separately the quality of its reasoning with an attribution (foreseeable
   miss, data gap, black swan, normal variance). After the agents' results, you see a
   short review of your own decisions against the outcomes, in chat only.
5. **Improve.** `/feedback` proposes up to 3 lessons for one agent, each backed by a
   pattern across evaluations. Approving one adds it to `prompts/<agent>/lessons.md` as
   a git commit; every later analysis records the prompt commit it ran with.

## 5. Backtests

```
/backtest --as-of 2026-06-01 --max-sectors 1 --shortlist 3
/evaluate --run <run_id> --min-days 0
```

A date means that day's 16:00 New York close. For every stage agent, a gatekeeper agent
builds a data pack of what was public then, an auditor checks it, and the stage agent
(with no data tools) reads only the pack. The run is labelled `audited` or
`leaks-found`. Limits: price levels are split-adjusted to today, macro values are
latest-revised, and ETF holdings exist only for the latest report
(`--allow-current-constituents` uses today's list and marks the run survivorship-biased).
Only dates after the model's training cutoff are honest evidence. Backtests take
longer than live runs (three agents per stage).

## 6. Scheduling (cron)

Cron runs with a minimal environment, so each line sources the env file. Times are New
York time via `CRON_TZ` (cronie; with other crons, convert to the machine's zone).

```cron
CRON_TZ=America/New_York
RUN="cd $HOME/trading-platform && CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 claude -p --mcp-config .mcp.json --permission-mode acceptEdits --model claude-sonnet-5 --effort low"

# Daily run after the close, Monday to Friday.
30 16 * * 1-5  . $HOME/.trading-platform/env && eval "$RUN '/run'" >> $HOME/.trading-platform/run.log 2>&1

# Follow-up at 10:00, 12:00, 14:00 and after the close.
0 10-14/2 * * 1-5  . $HOME/.trading-platform/env && eval "$RUN '/follow-up'" >> $HOME/.trading-platform/follow-up.log 2>&1
15 16 * * 1-5      . $HOME/.trading-platform/env && eval "$RUN '/follow-up'" >> $HOME/.trading-platform/follow-up.log 2>&1

# Weekly evaluation, Saturday morning.
0 9 * * 6  . $HOME/.trading-platform/env && eval "$RUN '/evaluate'" >> $HOME/.trading-platform/evaluate.log 2>&1
```

`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` keeps a headless run from killing an agent that
was started in the background. Market holidays are not skipped; a tick on a holiday just
finds no new data.

## 7. Where data is stored

Everything is in `workspace/` at the repository root (git-ignored). Formats:
[`prompts/formats.md`](../prompts/formats.md).

- `runs/<run_id>/`: the run manifest (`run.md`), the profile used, the report; for
  backtests also the lessons as of the date and the audited data packs.
- `agents/<agent>/analyses/<run_id>/<subject>/`: each agent's analysis (`output.md`) and
  every Equibles response it received (`raw/`).
- `agents/<agent>/evaluations/` and `agents/<agent>/feedback/`: grades and proposed lessons.
- `positions/<position_id>/`: watched positions and their alert log.
- `decisions/`: your decisions, notes, trade log and decision reviews. Only the
  middleware agent reads this folder.

Back it up by copying the folder while nothing is running. Approved lessons live in
`prompts/` (git), not in `workspace/`.

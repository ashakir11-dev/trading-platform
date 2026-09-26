# Operating the pipeline

How to set up, run and operate the system day to day. It is **decision support only**:
no command places, changes or cancels an order. `/decide` and `/trade` only *record*
what you decided or did. Your decisions are stored apart from everything the agents
read, and a hook blocks every agent from them.

The design behind this is in [`prompt-subagents-design.md`](prompt-subagents-design.md).

## 1. Set up

The pipeline is the `middleware` agent (`.claude/agents/middleware.md`) with its skills
(`.claude/skills/`), started by the `trading-agent` launcher (`trading_agent/`). Any
machine with Python 3.10+ and `python3` on the PATH (the hooks run it) works: macOS,
Linux, or WSL on Windows.

```sh
git clone https://github.com/ashakir11-dev/trading-platform.git
cd trading-platform
scripts/bootstrap.sh     # .venv, `trading-agent`, workspace/, profile and .env from the examples
```

The launcher depends on the Claude Agent SDK, which bundles Claude Code; an installed
`claude` CLI on the PATH is used instead if there is one (`TRADING_AGENT_CLAUDE` picks
another).

- `EQUIBLES_API_KEY` for market data. The Plus plan or better: a full run makes a few
  hundred data calls (the Free plan allows 100 a day), and Plus turns on live quotes.
- `ANTHROPIC_API_KEY` for the agents, unless you are logged in to Claude Code.

Keep the keys out of shell history and the repository: in `.env` at the repository root
(git-ignored; `trading-agent init` copies `.env.example`), or in
`~/.trading-platform/env` (`chmod 600`) to keep them outside the checkout. The launcher
reads both, and never overrides a variable already set:

```sh
EQUIBLES_API_KEY=...
ANTHROPIC_API_KEY=...
```

Then check the machine: `trading-agent doctor --online` prints one line per check
(Python, `python3` for the hooks, the repository, Claude Code, keys, the Equibles server,
git, the workspace and the profile) with the fix for each, and exits non-zero on a
problem. `python3 -m trading_agent doctor` works before anything is installed.

**Interactive:** `trading-agent` (or `claude --agent middleware`). On first start,
Claude Code asks you to trust the folder and the `equibles` MCP server; until then it
ignores the project's permission allow rules (the hooks and deny rules apply either
way). Headless runs through `trading-agent <skill>` don't need that: the launcher
passes the allow and deny lists itself.

**Without git** (e.g. a downloaded archive) everything works, but runs record
`prompt_commit: unversioned` and `/approve` adds lessons without a commit.

**Profile.** Copy `profile.example.json` to `workspace/profile.json` and edit it: risk
tolerance, horizons, shorts, max loss, reward:risk, `level_trigger`, notes (see
ARCHITECTURE.md §4). Without it, the example profile is used. Each run copies the
profile it used into its run folder.

**Models.** Each agent's model and effort are set in its file in `.claude/agents/`; the
table and the reasoning are in the design doc (§11).

## 2. First run

In the agent session (`trading-agent`), `/setup` walks through the checks and writes
your profile. Then:

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

(or headless: `trading-agent run`). Run it after the US close (16:00 New York) so daily bars are final. The report is shown
and saved to `workspace/runs/<run_id>/report.md`; each recommendation shows its
`candidate_id`. The same run is also rendered as a page to open in a browser,
`workspace/runs/<run_id>/report.html`: one card per recommendation with its price
ladder (stop / entry / target / price now), max loss, potential gain, reward:risk,
catalysts, flags and the agents' confidence. It is self-contained (no network), so it
can be opened offline or shared as a file. One agent on its own: `/run-agent <agent> <subject>`, e.g.
`/run-agent sector-deep-dive "Energy" upside` or `/run-agent technical-analysis NVDA`.

## 4. Workflow: decide → trade → follow up → evaluate → improve

```
/decide <candidate_id> accept "half size"     # or: reject
/trade <position_id> entered 118.40           # when you have actually bought
/follow-up                                    # one tick over open positions (schedule it)
/trade <position_id> exited 131.10 2026-10-30 # when you have exited
/evaluate                                     # grade runs at least a week old
/feedback <agent>                             # propose lessons for one agent
/approve <agent> <proposal_id>                # or: ... reject
```

1. **Decide.** Only recommended candidates can be decided, once each. `accept` opens a
   watched position from the technical plan (`position_id` = `candidate_id`); you place
   the trade yourself. `reject` is recorded and nothing is watched.
2. **Trade.** Record your actual entry and exit; only the prices and dates reach the
   position file.
3. **Follow up.** Each tick checks every open position: price against stop and target
   (per the profile's `level_trigger`), a missed entry, and material news. A delivered
   alert, or 14 days since the last one, triggers a full re-review (hold / adjust plan /
   exit). Alerts for a position are held for 12 hours after the previous one and
   delivered together afterwards. When a stop or target is hit, or a re-review says
   exit, the output starts with **ACTION NEEDED**.
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

`trading-agent <skill> [args]` runs one skill headless (every skill but `/setup`, which
asks questions): it finds the repository, loads `.env` and `~/.trading-platform/env`,
starts the middleware agent with the project's settings, permission lists, hooks and
the Equibles server, prints the agent's replies, and exits non-zero on failure. `-v`
prints each tool call to stderr; `--model` overrides the middleware's model. It also
sets `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`, which keeps a headless run from killing
an agent that was started in the background.

Times are New York time via `CRON_TZ` (cronie; with other crons, convert to the
machine's zone).

```cron
CRON_TZ=America/New_York
TA=$HOME/trading-platform/.venv/bin/trading-agent
LOG=$HOME/.trading-platform

# Daily run after the close, Monday to Friday.
30 16 * * 1-5      $TA run >> $LOG/run.log 2>&1

# Follow-up at 10:00, 12:00, 14:00 and after the close.
0 10-14/2 * * 1-5  $TA follow-up >> $LOG/follow-up.log 2>&1
15 16 * * 1-5      $TA follow-up >> $LOG/follow-up.log 2>&1

# Weekly evaluation, Saturday morning.
0 9 * * 6          $TA evaluate >> $LOG/evaluate.log 2>&1
```

Cron starts in the home folder: the launcher finds the repository from its own
location (or `TRADING_PLATFORM_HOME`). Market holidays are not skipped; a tick on a
holiday just finds no new data.

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

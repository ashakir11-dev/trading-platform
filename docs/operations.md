# Operating the pipeline

How to set up, run and operate the system day to day. It is **decision support**, with
optional **paper-trading execution for forward testing**: `/decide` only *records* your
accept/reject, and `/trade`'s manual modes (`entered`/`exited`) only *record* a trade you
made elsewhere. `/trade`'s `broker-*` modes (§4) are the one place that places an order —
always against Alpaca's **paper** account, never a live one, and always by your explicit
command. There is also an `alpaca` MCP server (`.mcp.json`) for interactive, manual
paper trading in chat — orders, positions, watchlists — pinned to paper mode in the
checked-in config. No agent in the pipeline can place, change or cancel an order, or use
either the broker script or the alpaca MCP server for anything at all; your decisions are
stored apart from everything the agents read, and a hook blocks every agent from them and
from both paper-trading paths.

The design behind this is in [`prompt-subagents-design.md`](prompt-subagents-design.md).

## 1. Set up

- The [Claude Code](https://code.claude.com) CLI.
- `ANTHROPIC_API_KEY` for the agents.
- `EQUIBLES_API_KEY` for market data. The Plus plan or better: a full run makes a few
  hundred data calls (the Free plan allows 100 a day), and Plus turns on live quotes.
- Optional, only if you want `/trade` to place paper orders (§4): `ALPACA_API_KEY_ID`
  and `ALPACA_API_SECRET_KEY` from a **paper trading** account's keys on the Alpaca
  dashboard (not a live account — `scripts/broker_alpaca.py` only ever calls the paper
  endpoint, so live keys would just fail against it).
- Optional, only if you want the interactive `alpaca` MCP server for manual testing
  (orders, positions, watchlists, in chat): the [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
  package manager (it runs the server via `uvx`, no separate install step), and
  `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` — the same paper account's keys, just under the
  names this server expects (different from `ALPACA_API_KEY_ID`/`ALPACA_API_SECRET_KEY`
  above, which are only for the script). `ALPACA_PAPER_TRADE` is pinned to `"true"` in
  `.mcp.json` itself, not read from the environment, so setting it yourself has no effect.

Keep the keys out of shell history and the repository, e.g. in
`~/.trading-platform/env` (`chmod 600`):

```sh
export ANTHROPIC_API_KEY=...
export EQUIBLES_API_KEY=...
export ALPACA_API_KEY_ID=...        # optional: only for /trade broker-buy|broker-sell
export ALPACA_API_SECRET_KEY=...
export ALPACA_API_KEY=...           # optional: only for the interactive alpaca MCP server
export ALPACA_SECRET_KEY=...
```

**Once per machine:** start `claude` in the repository and accept the trust dialog and
the `equibles` and `alpaca` MCP servers (`.mcp.json`). Until then Claude Code ignores the
project's permission allow rules; the hooks and deny rules apply either way. Every
`alpaca` MCP tool call still prompts for your approval unless you allow-list it yourself
(none are pre-approved in `.claude/settings.json`).

**Profile.** Copy `profile.example.json` to `workspace/profile.json` and edit it:
shorts, `level_trigger`, max hold per horizon, notes, and one full risk profile per
bucket (`core`/`growth`/`speculative`): horizons and the preferred one, entry style,
max loss, reward:risk, target return, scale-out targets, position size (% of account,
used to size the paper entry order) and how long an entry stays valid (see
ARCHITECTURE.md §4, §4a, §4b). Without it, the example profile is used — note it ships
with `allow_short: true`. Each run copies the profile it used into its run folder.

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
`candidate_id`. The same run is also rendered as a page to open in a browser,
`workspace/runs/<run_id>/report.html`: one card per recommendation with its price
ladder (stop / entry / target / price now), max loss, potential gain, reward:risk,
catalysts, flags and the agents' confidence. It is self-contained (no network), so it
can be opened offline or shared as a file. One agent on its own: `/run-agent <agent> <subject>`, e.g.
`/run-agent sector-deep-dive "Energy" upside` or `/run-agent technical-analysis NVDA long
sector "Information Technology" (XLK)`. Name the sector for a technical run: the agent
reads the chart against SPY and that sector ETF, and without one it compares with SPY
only and records the gap.

## 4. Workflow: decide → trade → follow up → evaluate → improve

```
/decide <candidate_id> accept "note"          # or: reject. Accept also places the sized paper entry order
/trade <position_id> entered 118.40           # when you bought it yourself, elsewhere
/trade <position_id> broker-buy 50            # manual paper entry if /decide placed none
/trade <position_id> broker-status            # check the working order(s)
/follow-up                                    # one tick over open positions (schedule it)
/trade <position_id> exited 131.10 2026-10-30 # manual exit
/trade <position_id> broker-sell target:1     # paper-sell the first scale-out target's fraction
/trade <position_id> broker-sell all          # or: paper-close the remainder
/evaluate                                     # grade runs at least a week old
/feedback <agent>                             # propose lessons for one agent
/approve <agent> <proposal_id>                # or: ... reject
```

1. **Decide.** Any candidate that passed every filter can be decided, once each: the
   report's recommendations (at most one per bucket) or its "also passed" list.
   `accept` opens a watched position from the technical plan (`position_id` =
   `candidate_id`) and, if the paper-account keys are set, sizes the entry from the
   account's equity and the bucket's `position_size_pct` and places a stop-limit/limit
   order at the plan's entry (never a market order; good till cancelled). Without keys
   the position is watched but unsized. `reject` is recorded and nothing is watched.
2. **Trade.** Record your actual entry and exit (`entered`/`exited`); only the prices and
   dates reach the position file. Or have `/trade` place an order itself with
   `broker-buy`/`broker-sell`, against your Alpaca **paper** account only. `/decide
   accept`, `/trade` and `/follow-up` (fills and expiry cancels) are the only commands
   in the pipeline that touch the broker, and each runs only when you type it. A filled
   order is recorded exactly like a manual trade, plus its order id; a scale-out exit
   (`target:<k>`) records that target as hit and keeps the remainder open.
3. **Follow up.** Each tick checks every open position: price against the stop and each
   target (per the profile's `level_trigger`), a missed or **expired** entry (past the
   plan's `entry_valid_until` — the paper order is cancelled and the position closed as
   never opened), the horizon's **max hold**, and material news. A delivered alert, or
   14 days since the last one, triggers a full re-review (hold / adjust plan / exit).
   Alerts for a position are held for 12 hours after the previous one and delivered
   together afterwards. When a stop or target is hit, or a re-review says exit, the
   output starts with **ACTION NEEDED** and gives the exact `/trade` command.
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

---
name: setup
description: Check this machine can run the pipeline, create the workspace and write the investor profile. Use on first use, or when a run fails because a key, the Equibles server or the profile is missing.
argument-hint: "[--profile-only]"
model: claude-sonnet-5
---
You are the middleware agent. Read `prompts/middleware/role.md` and
`prompts/formats.md`, and follow them.

Set up the pipeline on this machine. Arguments: $ARGUMENTS

1. **Check the machine** (skip with `--profile-only`): run
   `python3 -m trading_agent doctor` from the repository root. It needs only Python and
   prints one line per check (`ok`, `warn` or `FAIL`) with how to fix each. Never print,
   echo or ask the user to paste a key into the chat: keys go in the environment or in
   `.env` at the repository root (copy `.env.example`), which is git-ignored.
2. **Equibles.** Check that the Equibles tools are available in this session (the
   `equibles` MCP server). If not, tell the user to set `EQUIBLES_API_KEY` and restart
   the session (`trading-agent`, or `claude --agent middleware`); in Claude Code on the
   web, set it as an environment variable of the cloud environment and allow network
   access to `mcp.equibles.com`.
3. **Workspace.** Create `workspace/` if it does not exist (`mkdir -p workspace`).
4. **Investor profile.** If `workspace/profile.json` exists, show it in a few lines and
   ask whether to keep it. Otherwise, or if the user wants changes, ask the user for the
   fields below (offer the example's value as the default for each; one question per
   field, or a few at a time), then write `workspace/profile.json` with exactly these
   keys:

   | Key | Meaning | Example |
   |---|---|---|
   | `name` | a label | `"example"` |
   | `risk_tolerance` | `conservative`, `moderate` or `aggressive` | `"moderate"` |
   | `horizons` | any of `swing` (weeks to ~3 months), `long_term` (months to years); no day trading | `["swing", "long_term"]` |
   | `allow_short` | whether short plans are allowed | `false` |
   | `max_loss_per_trade_pct` | largest loss from entry to stop, in % | `8.0` |
   | `min_reward_to_risk` | smallest reward:risk accepted | `2.0` |
   | `target_return_pct` | the return aimed for per trade, in % | `15.0` |
   | `level_trigger` | `close` (a bar must close beyond a stop/target) or `intraday` (a touch counts) | `"close"` |
   | `notes` | free-text preferences (exclusions, style) | `"Avoid tobacco."` |

   The profile holds preferences set up front, not decisions, so agents may read it.
5. Finish with a short checklist of what is ready and what is not, and the next step:
   `/run --max-sectors 1 --shortlist 3` for a first, small run (about 15 minutes).

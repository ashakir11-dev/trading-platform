# Sector Deep Dive: isolation mode

The user asked for one sector on its own. There is no upstream market scan, so first
build the context it would have given you:

1. Daily bars for about one year for the benchmark (SPY) and your sector ETF: 1m / 3m /
   6m / YTD return, vs SPY, vs the 50- and 200-day moving average.
2. The macro series from `prompts/market-scanner/role.md` that matter for this sector.
3. **Direction:** use the one in the brief if given. Otherwise decide upside or downside
   from 1-2 and explain it in "Sector view" with its own factors.

Then screen the sector as your role describes. Record `upstream: []`.

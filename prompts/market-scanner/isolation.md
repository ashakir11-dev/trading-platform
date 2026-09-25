# Market Scanner: isolation mode

The user asked for a market scan on its own, outside a pipeline run. Do exactly what
the default mode does: there is no upstream in either mode. The brief may name a
focus (e.g. "rate-sensitive sectors only"); if so, still build the full sector table,
but make calls only within the focus and say so in the market summary.

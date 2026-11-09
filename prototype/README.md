# Phase 4 prototype

A throwaway prototype that tests the pilot bet before Engineering plans the
production build. See [the Phase 4 page](../docs/phase-4-prototype.html) for
what it must answer and what it deliberately skips.

## Rebuild from nothing

```
./build.sh YOUR_GCP_PROJECT_ID
```

This generates the book of contracts, loads it into the BigQuery sandbox,
creates the calculated-field views, describes every table and column, and checks them against the PRD's worked
example. Sandbox tables expire after 60 days, so this command is the prototype.

## What's here

| Path | What it is |
|---|---|
| `generator/config.yaml` | Every assumption behind the simulated book, fixed before each backtest ran |
| `generator/generate.py` | Writes the source tables: consignors, contracts, assets, listings, sales |
| `sql/` | The PRD's calculated fields as BigQuery views, under the PRD's names |
| `metadata.yaml` | A description for every table, view and column, applied on every build; the build fails if a column is undocumented |
| `checks/` | The PRD's worked example as an automated check |
| `questions/` | Plain-language questions over the governed metrics, the 30-question evaluation set and its scorer. See [its README](questions/README.md) |

## How the book is calibrated

The outcome distribution is calibrated to the Phase 2 book: about 2,000
contracts a year averaging about $50,000, 15% underperforming over 12 months
and 18% over 6, with an average shortfall near 24% of target. Everything else
in `config.yaml` is a stated assumption, including the two cases linear pacing
is expected to get wrong: live-auction items that sell late in the window, and
single-asset contracts.

The generator was committed before the first backtest ran, so its results
can't have been tuned into the data. When that flag failed, appraisals were
added to the generator so a flag could price unsold items. That change was
committed before the second backtest ran, but it was made knowing the first
had failed, and the sale prices and the appraisals come from the same
underlying value, with about 30% appraisal error. The real-history backtest
in Phase 5 is the test that settles it.

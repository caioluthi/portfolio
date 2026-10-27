# Step 2b · Results

Pre-registered in [`../DESIGN.md`](../DESIGN.md) (commit `e110d3d`) before the
first run. Settings were chosen on contracts that closed between 12 and 6
months ago (986 contracts, 130 below target) and evaluated once on the last 6
months (982 contracts, 174 below target).

Consistency check: variant A at the pilot default over the full year
reproduces step 2 exactly (80% false positives, 68% recall at halfway, 75 days,
1,209 contracts flagged).

## Verdict: no variant passes, but the false-alarm problem is solved

| On the test contracts | Bar | A · Linear pacing | B · Projection with unsold inventory | C · B with watch and act | Today's practice |
|---|---|---|---|---|---|
| Setting | | 95%, day 30 † | 95%, day 30, w 0.30 | 95%, day 21, w 0.15, evidence 15% | Final-week review |
| Median lead time | ≥ 30 days | 56 | 30 | 30 | 0 |
| Recall at halfway | ≥ 70% | 59% | 38% | **44%** | 0% |
| False-positive rate | ≤ 40% | 66% | 37% | **36%** | 6% |
| New flags per week | ≤ 25 | 18 | 9.5 | 8.5 | 2 |
| Watch list, 95th percentile | ≤ 40 | | | 10 | |
| Criteria met | | 2 of 4 | 3 of 4 | 3 of 4, plus the watch cap | |

† No A setting met the guardrails on training; per the design, the reference
setting is the one with the fewest false positives among those with 30+ days
of lead time.

**Counting unsold inventory is what fixes the false alarms.** Moving from A to
B cuts false positives from 66% to 37% and halves the weekly flags, at the
same scoring. It keeps the median lead time at the 30-day bar, against zero
today.

**The evidence gate adds a little.** C over B gains 6 points of recall at
halfway and 1 point of false positives. Its watch list is small: at most 10
contracts on 95% of days.

**What still fails is recall at halfway.** C flags 44% of underperformers by
day 45 with enough confidence to act on, against a bar of 70%.

## Why 70% isn't reachable in this book

Across every setting tested on training, the best recall at halfway at each
level of false alarms:

| False-positive rate | ≤ 40% | 40–50% | 50–60% | 70% + |
|---|---|---|---|---|
| Best recall at halfway | 41% (C) | 49% (B) | 54% (B) | 92% (A) |

Reaching 70% by day 45 means accepting roughly 70% false alarms, which is
where step 2 started. In this book, about half of the eventual underperformers
don't look different from healthy contracts by day 45 on sales and appraisals
alone.

## What it means for the opportunity

The 70% bar came from the Phase 2 sizing funnel, where "showed warning signs by
the halfway mark: 70%" was marked as a judgment. The prototype replaces that
judgment with a measured number, about 44%, which resizes the base case:

| Funnel step | Phase 2 base case | With the measured rate |
|---|---|---|
| Annual shortfall payouts | $3.60M | $3.60M |
| Flagged by halfway, with confidence to act | × 70% | × 44% |
| An action was still available | × 50% | × 50% |
| Recovered when acted on | × 40% | × 40% |
| **Recoverable per year** | **~$500K** | **~$320K** |

At 8.5 flags a week, Ops review costs about $4K a year. The case stays clearly
positive at the smaller size.

## Decisions this puts to the PM

1. **Is ~$320K a year with a trustworthy flag worth piloting,** with the
   recall bar reset to the measured rate? Or is 70% recall essential?
2. **If 70% is essential,** the signal needs evidence beyond sales and
   appraisals, such as listing engagement (views, watchers, bids) or price
   drops. That is a new requirement, and it moves historical-curve pacing from
   "next" into scope.
3. **Adopt B's projection as the pilot definition** in either case. It
   replaces linear pacing and adds a required field: an appraised estimate per
   asset.

## Caveats

- The book is simulated. The numbers depend on how appraisal error, sale
  timing and demand are modeled in `generator/config.yaml`.
- The test set has 174 underperformers, so rates move by a few points either
  way.
- The split falls 182 days before today, so contracts closing on 2026-04-01
  are in training. DESIGN.md gives the test window as starting on that date;
  the code, which ran as committed, is one day off from that wording.
- Sell-through by period is learned from the training contracts. A production
  version would re-learn it regularly.

## Adopted as the pilot definition

Variant C at its chosen setting is now the governed definition in BigQuery
(`sql/02_contract_daily.sql`, `sql/03_contract_outcome.sql`), with
`sell_through.csv` loaded as `sell_through_by_period`. On the same test
contracts, the views reproduce this table exactly: 982 contracts, 43.7% recall
at halfway, 35.5% false positives, a 30-day median lead time and 8.5 flags a
week.

## Files

- `grid_A.csv`, `grid_B.csv`, `grid_C.csv`: every setting, scored on training
- `summary.json`: chosen settings, training and test scores, checks
- `sell_through.csv`: sell-through by 15-day period, learned from training

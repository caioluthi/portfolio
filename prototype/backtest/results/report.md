# Step 2 · Backtest and go-live report

Run on the simulated book as of 2026-09-30: 1,968 contracts closed in the last
12 months, 304 of them below target. The selection rule was committed before
the run (commit `a7bc4d3`).

## Verdict: the bet does not hold as specified

No setting of the linear pacing flag meets the go-live criteria. Of the 40
threshold and day-floor settings tested, none meets the false-positive
guardrail, so the selection rule picks nothing.

| Go-live criterion | Target | Pilot default (80%, day 15) | Today's practice (final-week review) | Met |
|---|---|---|---|---|
| Median detection lead time | ≥ 30 days | **75 days** | 0 days | Yes |
| Recall at halfway | ≥ 70% | 68% | 0% | No, narrowly |
| False-positive rate | ≤ 40% | **80%** | 6% | **No** |
| New flags per week | ≤ 25 | 23 | 2 | Yes |
| Reconciliation | 100% | Not tested: out of prototype scope | | |

Across the whole sweep, the false-positive rate ranges from 70% to 84%. The
strictest settings bring it to 70% but give up most of the lead time.

## What the flag does buy

Against today's practice, the flag catches far more and far earlier:

- Today's final-week review notices **33%** of underperformers, with almost no time left to act.
- The pilot default flags **80%** of them at some point, at a median of **75 days** before expiry.

The cost is noise: about 23 flags a week, of which roughly 18 are false
alarms. At 10 minutes per review, that is about three hours of Ops time a week.

## Why it fails: early pacing is mostly timing noise

These checks are exploratory, run after the verdict. They explain the result
but don't change it.

1. **Flags are mostly wrong early and mostly right late.** Share of flagged
   contract-days whose contract really closed below target:

   | Days into the contract | 15–30 | 30–45 | 45–60 | 60–75 | 75–90 |
   |---|---|---|---|---|---|
   | Flag is right | 19% | 26% | 38% | 56% | 90% |

   With 15% of contracts underperforming, a flag in the first month is barely
   better than picking contracts at random.

2. **How far behind doesn't help early on.** In days 15–45, contracts pacing
   below 30% are no more likely to miss than those pacing at 65–80%. Being
   behind early mostly means the big items haven't sold yet, not that they
   won't.

3. **Requiring the flag to persist doesn't fix it.** Holding the flag for 7
   days in a row cuts false alarms from 80% to 77% but lead time from 75 to 43
   days. Holding it for 14 days cuts lead time to 3.

4. **It's not one segment.** The false-positive rate is 77–83% in every
   channel and every contract size. Auction-heavy contracts are the worst
   (87%), as expected, but they are only 4% of the book.

## What this means for the PRD

Linear pacing on realized sales is a weak early signal for consignment, where
a few large items selling or not decide the outcome. Measuring progress only in
dollars already collected ignores what is still listed and how it is doing.
Candidate changes, for the PM to decide:

- **Count unsold inventory in the projection.** Project final value as
  realized sales plus the expected value of items still listed. This needs a
  new required field: an estimate or asking price per asset.
- **Separate a "watch" signal from an "act" signal.** Show early flags as
  low-confidence and reserve Ops review for flags with enough evidence, making
  the lead-time trade-off explicit.
- **Revisit the false-positive guardrail.** It counts a contract as a false
  alarm if it was ever flagged on any day. With 15% of contracts
  underperforming, that is close to unreachable for any early signal. Any
  revision has to be argued from Ops capacity and trust, not set to fit this
  result.

## Caveats

The book is simulated. The finding depends on how lumpy sales are: how many
assets a contract has, how uneven their values are, and when they sell. Those
assumptions are in `generator/config.yaml`. The prototype shows the mechanism
and the evaluation method; real sales history is what would confirm the size of
the effect.

## Files

- `sweep.csv`: all 40 settings with every metric
- `summary.json`: baseline, pilot default and breakdowns by channel and contract size

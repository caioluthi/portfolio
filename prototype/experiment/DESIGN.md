# Step 2b · Testing a better signal and a two-tier flag

Written and committed before any result was seen. The step 2 backtest showed
that linear pacing on realized sales fails the false-positive guardrail at
every setting (`../backtest/results/report.md`). This test asks whether two
changes fix that, and which change does the work.

## Variants

All three are scored the same way, on the same contracts.

**A · Linear pacing (step 2).** Flag when realized sales fall below
`threshold x target x elapsed_share`, from the day floor onward.

**B · Projection with unsold inventory.** Project the final value from what
has sold and what is still unsold:

```
projected_final = realized + unsold_estimate x sell_through(t) x price_realization
price_realization = (realized + w) / (sold_estimate + w)
```

- `unsold_estimate`: appraised value of the contract's items not yet sold (new field `estimate_usd`).
- `sell_through(t)`: share of still-unsold appraised value that goes on to sell
  by expiry, by 15-day period of the contract. Learned from the training
  contracts only.
- `price_realization`: how sold items are pricing against their appraisals,
  pulled toward 1 by a prior worth `w = w_share x target` dollars, so the first
  sale or two can't swing it.

Flag when `projected_final < threshold x target`, from the day floor onward.

**C · B with "watch" and "act" tiers.** The same projection, with a second
condition on how much evidence there is.

- **Act:** the B flag holds and at least `e` of the contract's appraised value
  has resolved, meaning it has sold.
- **Watch:** the B flag holds but the evidence is below `e`.

## Grids

| Variant | Parameters |
|---|---|
| A | threshold 0.60-0.95 in 0.05 steps x floor {7, 10, 15, 21, 30}: 40 settings |
| B | threshold {0.70, 0.75, 0.80, 0.85, 0.90, 0.95} x floor {7, 15, 21, 30} x w_share {0.05, 0.15, 0.30}: 72 settings |
| C | each B setting x e {0.15, 0.30, 0.45}: 216 settings |

## Data split

- **Training:** contracts that closed between 12 and 6 months before today
  (2025-09-30 to 2026-03-31). Settings and `sell_through` are chosen here.
- **Test:** contracts that closed in the last 6 months (2026-04-01 to
  2026-09-30). Each variant's chosen setting is evaluated here once.

## Scoring

The go-live bar doesn't move. For A and B, every flag counts. For C, only
**act** flags are scored against it; lead time is measured from a contract's
first act flag.

| Criterion | Bar |
|---|---|
| Median detection lead time (0 if never flagged) | >= 30 days |
| Recall at halfway (first flag by day 45) | >= 70% |
| False-positive rate (flagged, closed at or above target) | <= 40% |
| New flags per week | <= 25 |

**Watch** flags are context on Maria's list, not reviews she has to do. They
have no false-positive guardrail. Their one guardrail is size: on 95% of days,
**no more than 40 contracts** are on watch at once.

This changes how the opportunity page's primary metric is measured for a
two-tier product: lead time counts from the first act flag. It is decided here,
before the run, and will be recorded as a decision the prototype prompted.

## Selection rule

For each variant, on the training contracts:

1. Keep the settings that meet both guardrails: false-positive rate and flags
   per week, plus watch-list size for C.
2. Pick the highest median lead time. Break ties on recall at halfway, then on
   the lower false-positive rate.
3. If no setting meets the guardrails, the variant fails on training. For
   reference only, report the setting with the lowest false-positive rate among
   those with a median lead time of at least 30 days.

The chosen setting is then evaluated once on the test contracts. A variant
passes only if it meets all four criteria **on test**.

## What would count as an answer

- **A vs B:** what counting unsold inventory buys, at the same scoring.
- **B vs C:** what the evidence gate buys on top.
- **Verdict:** whether any variant passes on test. If none does, the closest
  one and what is still missing.

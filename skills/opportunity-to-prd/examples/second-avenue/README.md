# Worked example: Second Avenue contract risk

Both modes of the skill, on the case study in this repository.

| File | Mode | What it is |
|---|---|---|
| [opportunity.md](opportunity.md) | Draft input | The opportunity brief, revision 1, with the discovery points the PRD draws on |
| [prd-v1.md](prd-v1.md) | Draft output | The first PRD, written against it |
| [evidence.md](evidence.md) | Revise input | What the prototype and the Ops, Finance and Data feedback sessions found, and what the PM decided about each item |
| [prd.md](prd.md) | Revise output | Revision 2, with every change traced to the evidence in its revision block |

Both PRDs pass the checker with no errors or warnings:

```
python skills/opportunity-to-prd/scripts/check_prd.py skills/opportunity-to-prd/examples/second-avenue/prd-v1.md
python skills/opportunity-to-prd/scripts/check_prd.py skills/opportunity-to-prd/examples/second-avenue/prd.md
```

## How these differ from the published pages

The published [PRD](https://caioluthi.github.io/portfolio/phase-3-prd.html) and its [revision 1](https://caioluthi.github.io/portfolio/phase-3-prd-v1.html) were written by hand before this skill existed. Running them through the skill's rules changed three things, which is the point of having the rules:

- **One success metric had no fields behind it.** "Shortfall payouts avoided" was a metric on the opportunity brief, but no calculated field produced it. The skill's rule that every metric decomposes into fields added `shortfall_at_close`. Revision 2 also adds `watch_list_size` for the guardrail introduced there.
- **Every calculated field input is a named field.** The hand-written PRD had inputs like "sales from each source" and "flag parameters". Here each input is a required field, a parameter or another calculated field, so the checker can prove the chain closes. This surfaced `days_elapsed`, `total_estimate`, `channel_price_realization` and `appraisal_coverage` as fields of their own.
- **Open-question IDs are stable.** The published revision 2 inserted the appraisals question at 7, which pushed the question layer from 7 to 9 while the backlog still called it OQ-7. Here the question layer keeps OQ-7, lots is OQ-8 and appraisals is OQ-9, matching the backlog. The published page has since been corrected the same way.

Field names match the BigQuery views the prototype built, so the PRD, the prototype and the backlog use one vocabulary.

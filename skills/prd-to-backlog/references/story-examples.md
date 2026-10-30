# Good and bad: epics, stories and acceptance criteria

Each pair shows a mistake this skill exists to prevent, and the fix. The examples come from the Second Avenue contract-risk backlog.

## Epics

**A risk promoted to an epic**

> ✗ **E2 · Intake appraisal recovery.** Recover last year's appraisals from ConsignTrack.

It's a real risk, and it needs to be visible, but nobody signs off on "appraisal recovery" as an outcome. It's one story in the data epic, flagged as critical path, and its result is a gate the PM puts on the roadmap.

> ✓ **E1 · Trusted contract data.** One daily, reconciled, reproducible snapshot of every contract, its assets and sales.
> ↳ E1-S2 · A trustworthy intake appraisal · `critical_path: Change to ConsignTrack, a system another team owns.`

**An epic grouped by layer**

> ✗ **E3 · Backend.** Tables, pipelines and jobs.

> ✓ **E2 · Governed risk metrics.** The projection, flag and exposure defined once, with daily flag history.

**Too many epics**

Eleven epics for one product, each with one or two stories, usually means stories and risks were promoted to epics. Merge until each epic is an outcome someone could sign off on: four to seven.

## Stories

**A system story with no person in it**

> ✗ The system calculates pacing for each contract.

> ✓ **As** Maria, Ops contract manager, **so that** falling-behind contracts reach me while there's still time to act.

**A "so that" that restates the feature**

> ✗ … so that the morning list is available.

> ✓ … so that I open the contracts that matter most first.

**Too fine for Product**

> ✗ E1-S1 Create the staging tables · E1-S2 Write the extraction job · E1-S3 Add the snapshot partition · …

Those are Engineering's technical tasks. Product writes two or three functional stories per epic; refinement splits them.

## Acceptance criteria

**Prescribes the solution**

> ✗ Snapshots are stored as date-partitioned Parquet in the lake.

> ✓ Any day's snapshot, from the first day of landing, can be regenerated and comes out the same.

**Names a tool the PRD didn't choose**

> ✗ Every region sees the list in Tableau.

> ✓ Every region sees the list on a dashboard.

**Can't be checked**

> ✗ The flag is accurate.

> ✓ The projection, flag and tier match their PRD definitions. In the worked example the contract projects to about $40,800 by day 30, goes on watch on day 21 and moves to act on day 22.

## Estimates

**An estimate written by Product**

> ✗ `size: 8` · "about 3 days of work" · "fits in sprint 1"

Estimation and sprint planning are Engineering's. Leave `tasks` empty and no size field at all. If refinement produces a sprint plan, Record refinement writes it under `sprints`, in Engineering's words.

## Refinement

**Pushback silently absorbed**

> ✗ E1-S1's criterion quietly changes from "12 months back" to "from first landing", with no note.

> ✓ The criterion changes, and the story carries `changed_in_refinement: The 12-month historical rebuild moved to E3-S1; snapshots never taken can't be reproduced.`

**An Engineering question answered by Product, or the reverse**

> ✗ Product decides extraction is change capture. Engineering decides ConsignTrack wins when systems disagree.

> ✓ Extraction is `by: engineering`. Which system wins on a business fact is `by: product`.

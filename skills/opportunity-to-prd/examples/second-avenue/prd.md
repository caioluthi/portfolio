# Second Avenue contract risk: product requirements

Revision: 2 · 2026-10-27 · Revised after the Phase 4 prototype and the Ops, Finance and Data feedback sessions
Opportunity: [opportunity brief, revision 2](https://caioluthi.github.io/portfolio/phase-2-opportunity.html)

This page says what the contract-risk product must do, with a one-line reason for each requirement. Why it matters, how success is judged and what the pilot is betting on are in the opportunity brief. How it is built and when it ships come from Engineering. Second Avenue is fictional and every figure is simulated.

## Revision 2

Prompted by the Phase 4 prototype and three feedback sessions; the evidence is in [evidence.md](evidence.md). Previous revision: [revision 1](prd-v1.md).

- The risk flag no longer compares sales with a straight line. It projects each contract's final value from what has sold and what is still unsold (DPR-3). Prompted by P1, P2.
- Flags come in two tiers, act and watch; success is measured from the first act flag (DPR-3, DPR-5, DPR-6). Prompted by P3.
- Pilot settings are the ones the prototype's test chose: 95% of target, from day 21, a cushion worth 15% of target, act at 15% of appraised value sold (DPR-3). Prompted by P4.
- New required field: an appraised value per item, kept as its own field that repricing can't overwrite (DPR-1, OQ-9). Prompted by P6, F8.
- Exposure by channel and asset type is split over each contract's unsold items, which resolves OQ-6 (DPR-4). Prompted by P7.
- Contracts with nothing left to sell leave the morning list and show to Finance as exposure locked in (DPR-4, DPR-5). Prompted by F1, F2.
- The morning list shows whether a live auction is still possible and how much unsold value sits on a weak channel for its item type (DPR-5). Prompted by F3, F4.
- A 4-week average sits beside the daily exposure figure (DPR-4). Prompted by F6.
- New NFR-5: appraisal completeness reported on every refresh. Prompted by F9.
- Out of scope now says exposure at risk is not an accounting reserve. Prompted by F7.
- Next scope: logging Ops actions also shows which contracts have been worked; listing activity and per-segment sell-through replace historical-curve pacing. Prompted by F5, P5.
- New open questions: OQ-8 on lots, still open; OQ-9 on appraisals, resolved. Prompted by F10, F8.
- New success metric and field for watch-list size; `shortfall_at_close` kept for the outcome metric. The targets that moved are on the opportunity brief.

## 1. Goal and users

Give Ops and Finance a trusted, early view of which Risk contracts are heading below target, so they can act before the contract expires. Targets for every metric below are set in the [opportunity brief](https://caioluthi.github.io/portfolio/phase-2-opportunity.html#metrics).

| Persona | Role | What they need |
|---|---|---|
| maria | Maria, Ops contract manager | To know each morning which contracts to open first and why, while there is still time to reprice, switch channel or move items into an auction |
| david | David, Finance manager | Exposure at risk by region, channel, asset type and consignor, instead of a backward-looking quarterly report |
| priya | Priya, data analyst | Contracts, listings and sales joined and reconciled, so a report becomes a query |

### Success metrics

Targets are set in the opportunity brief. Each metric here is built only from calculated fields in section 3.

| Metric | Built from |
|---|---|
| Detection lead time | `detection_lead_time_days` |
| Recall at halfway | `flagged_by_halfway`, `closed_below_target` |
| False-positive rate | `false_positive` |
| Alert volume | `new_flags` |
| Watch list size | `watch_list_size` |
| Reconciliation | `reconciled` |
| Shortfall payouts avoided | `shortfall_at_close`, `closed_below_target` |

## 2. Scope

**Pilot**
- A projection of each contract's final value that counts unsold inventory
- A risk flag with watch and act tiers
- Projected shortfall and exposure at risk
- Daily refresh with cross-source reconciliation
- Ranked daily list of flagged contracts for Ops
- Book rollups by region, channel, asset type and consignor for Finance
- Plain-language questions over these metrics

**Next**
- Signals from listing activity, such as views, watchers, bids and price drops, to catch more underperformers by halfway
- Sell-through by asset type, channel and region, instead of one rate for the whole book
- Suggested interventions per flagged contract
- Logging of Ops actions, so the recovery rate can be measured instead of assumed and Ops can see which contracts they've already worked

**Out of scope**
- Automated repricing or channel moves
- Real-time streaming
- What-if simulation of moving items between channels
- Optimizing the upside tiers
- Using exposure at risk as an accounting reserve. It is built to rank and flag contracts, not tested as a forecast of payouts.

## 3. Data product requirements

### DPR-1 · One contract view across systems · Must
**What:** Every Risk contract, active or closed, is joined with its consignor, its assets and their sales into a single daily snapshot that carries every required field below.
**For:** priya. Today contracts, listings and sales live in three systems and an analyst is the integration layer.

### DPR-2 · Cross-source reconciliation · Must
**What:** At every refresh, each active contract's status and sales are checked across ConsignTrack, Listings and Sales. Disagreements are reported with the contract and the systems involved, never silently resolved.
**For:** priya, david. Priya's one essential requirement, and the reconciliation guardrail.

### DPR-3 · Governed metrics as calculated fields · Must
**What:** Every calculated field below is defined once, computed daily per contract from the required fields, and exposed by name to everything downstream. The flag's settings and the sell-through rates it uses are parameters, so they can change without changing a definition.
**For:** maria, david. The single source of the numbers Ops acts on, Finance reports and the success metrics judge.

### DPR-4 · Exposure rollups for Finance · Must
**What:** Exposure at risk and the share of contracts flagged roll up by region, channel, asset type and consignor, from contract level to the whole book, and every rollup adds up to the book total. For channel and asset type, which belong to items rather than contracts, each contract's exposure is split over its unsold items by appraised value. Exposure already locked in is shown on its own, and a 4-week average sits beside the daily figure.
**For:** david. Replaces the quarterly Risk Book Summary; the locked-in split and the average came from his feedback session.

### DPR-5 · Ranked morning list for Ops · Must
**What:** Each morning, before the working day starts, Ops sees the contracts flagged act, ranked by projected shortfall, with projected final value, days to expiry and sales so far by channel. Contracts on watch are listed separately, as context. Each contract shows whether a live auction is still possible and how much of its unsold value sits on a channel where that item type sells poorly. Contracts with nothing left to sell are left off.
**For:** maria. She asked for a short list of which contracts to open first; the tiers came from the prototype and the rest from her feedback session.

### DPR-6 · Flag history · Must
**What:** Each contract's daily flag and tier are kept, so its first watch and first act dates are known and any past day's list can be reproduced as it was.
**For:** david. Lead time can't be measured without it, and Finance needs to audit what was known when.

### DPR-7 · Backtest · Must
**What:** The daily flag can be replayed over the last 12 months of closed contracts, alongside today's practice of a review in the final week, producing every success metric, for any setting of the flag parameters.
**For:** maria, david. The go-live decision in section 5 depends on it.

### DPR-8 · Success scorecard · Should
**What:** Once live, the success metrics are reported weekly from their calculated fields, broken out by channel and contract size.
**For:** david. Keeps the guardrails honest after launch and measures the known risks to the pilot.

### DPR-9 · Questions in plain language · Should
**What:** Ops and Finance can ask the four discovery questions in plain language. Answers come only from the calculated fields, name the metric and the as-of date, and say plainly when a question is outside what the product supports.
**For:** maria, david. What Priya called a nice-to-have: "then they'd stop asking me."

### Key entities

Consignor → Contract → Asset → Sale event · dimensions: channel (app, website, live), region

A contract carries its target price, its 90-day window and its tier schedule, which can be negotiated per contract. Each asset belongs to one contract, carries the appraised value it was given at intake, and is listed on one channel at a time. Each sale event records the channel and region it happened in. The physical design, keys and grain are Engineering's.

### Required fields

DPR-1 is met when the daily snapshot carries every field below, from the system named. This is the data contract Engineering sizes against.

| Entity | Field | Meaning | Source | Needed for |
|---|---|---|---|---|
| Consignor | `consignor_id` | Unique consignor | ConsignTrack | Rollups by consignor (DPR-4) |
| Contract | `contract_id` | Unique contract; links to its consignor | ConsignTrack | Every calculated field (DPR-1) |
| | `start_date` | First day of the contract window | ConsignTrack | `days_elapsed` |
| | `lifecycle_days` | Length of the window, 90 by default | ConsignTrack | `elapsed_share` |
| | `expiry_date` | Last day of the window | ConsignTrack | `days_to_expiry`, `detection_lead_time_days` |
| | `target_price` | Guaranteed target in USD | ConsignTrack | `risk_flag`, `projected_shortfall` |
| | `tier_schedule` | Negotiated upside tiers | ConsignTrack | Carried for context; not used by pilot metrics (DPR-1) |
| | `status` | Active, closed or cancelled | ConsignTrack, checked against Listings and Sales | `risk_flag`, `reconciled` |
| | `region` | Region that manages the contract | ConsignTrack | Rollups by region (DPR-4) |
| Asset | `asset_id` | Unique asset; belongs to one contract | ConsignTrack | `realized_sales`, `appraisal_coverage` |
| | `asset_type` | Category, such as furniture or jewelry | ConsignTrack | `channel_price_realization`, rollups by asset type (DPR-4) |
| | `estimate_usd` | Appraised value at intake, in USD, kept as its own field that repricing never overwrites. New in revision 2 | ConsignTrack | `total_estimate`, `sold_estimate`, `appraisal_coverage` |
| | `listing_status`, `listing_channel` | Where and whether the asset is listed | Listings | `reconciled`, `unsold_on_weak_channel` |
| Sale event | `sale_id` | Unique sale of one asset | Sales | `reconciled` |
| | `sale_date` | Date the sale closed | Sales | `realized_sales`, `sold_estimate` |
| | `gross_amount` | Gross proceeds in USD | Sales | `realized_sales` |
| | `channel` | App, website or live | Sales | Rollups and Ops list by channel (DPR-4, DPR-5) |
| | `region` | Region where the sale happened | Sales | Sales performance by region (DPR-4) |
| Parameter | `flag_threshold` | 0.95 for the pilot: flag when the projection falls below 95% of target. Chosen by the prototype's test | Configuration | `risk_flag` |
| | `flag_day_floor` | 21 for the pilot: before day 21 too little has usually sold to judge | Configuration | `risk_flag` |
| | `realization_prior_share` | 0.15 for the pilot: a cushion worth 15% of target, so one or two early sales can't swing price realization | Configuration | `price_realization` |
| | `act_evidence_min` | 0.15 for the pilot: act once 15% of appraised value has sold | Configuration | `risk_tier` |
| | `live_catalog_lead_days` | 14: live auction catalogs close two weeks before the sale. From Ops | Configuration | `live_auction_possible` |
| | `weak_channel_gap` | 0.15: a channel is weak for an item type when it sells 15 points or more below that type's best channel | Configuration | `unsold_on_weak_channel` |
| | `sell_through` | Share of still-unsold appraised value that sells by expiry, per 15-day period of the contract. New in revision 2 | Learned from recently closed contracts | `projected_final_value` |
| Snapshot | `as_of_date` | Day the snapshot represents | Set by each refresh | `days_elapsed`, `days_to_expiry`, `first_flag_date` |

### Calculated fields

DPR-3 is met when each field below is defined once, computed only from required fields, parameters and other calculated fields, and exposed by this name. The last nine are the inputs to the success metrics.

| Field | Definition | Inputs | Grain |
|---|---|---|---|
| `days_elapsed` | Days since the contract started | `as_of_date`, `start_date` | Contract, daily |
| `elapsed_share` | days elapsed ÷ lifecycle days, capped at 1 | `days_elapsed`, `lifecycle_days` | Contract, daily |
| `days_to_expiry` | expiry date − as-of date | `expiry_date`, `as_of_date` | Contract, daily |
| `realized_sales` | Gross proceeds to date for the contract's assets | `gross_amount`, `sale_date`, `asset_id` | Contract, daily |
| `total_estimate` | Appraised value of every item under the contract | `estimate_usd` | Contract |
| `sold_estimate` | Appraised value of the items sold to date | `estimate_usd`, `sale_date` | Contract, daily |
| `unsold_estimate` | total estimate − sold estimate: what is still to sell | `total_estimate`, `sold_estimate` | Contract, daily |
| `price_realization` | (realized + cushion) ÷ (sold estimate + cushion), cushion = prior share × target: how sold items are fetching against their appraisals | `realized_sales`, `sold_estimate`, `target_price`, `realization_prior_share` | Contract, daily |
| `evidence_share` | sold estimate ÷ total estimate: how much of the contract has resolved | `sold_estimate`, `total_estimate` | Contract, daily |
| `projected_final_value` | realized + unsold estimate × sell-through for the current 15-day period × price realization | `realized_sales`, `unsold_estimate`, `sell_through`, `price_realization`, `days_elapsed` | Contract, daily |
| `projected_shortfall` | max(0, target − projected final value) | `target_price`, `projected_final_value` | Contract, daily |
| `risk_flag` | Projected final value below the threshold × target, on an active contract, from the day floor on | `projected_final_value`, `target_price`, `status`, `days_elapsed`, `flag_threshold`, `flag_day_floor` | Contract, daily |
| `risk_tier` | act when the risk flag holds and evidence share is at least the minimum; watch when it holds with less | `risk_flag`, `evidence_share`, `act_evidence_min` | Contract, daily |
| `pacing_pct` | realized ÷ (target × elapsed share). Shown to Ops as context; it no longer drives the flag | `realized_sales`, `target_price`, `elapsed_share` | Contract, daily |
| `exposure_at_risk` | Sum of projected shortfall across contracts flagged act. For channel and asset type, each contract's shortfall is first split over its unsold items by appraised value | `projected_shortfall`, `risk_tier`, `unsold_estimate`, `estimate_usd` | Any rollup: region, channel, asset type, consignor |
| `exposure_locked_in` | Exposure at risk on contracts with nothing left to sell | `exposure_at_risk`, `unsold_estimate` | Any rollup, daily |
| `exposure_at_risk_4wk_avg` | Average of daily exposure at risk over the last 28 days | `exposure_at_risk`, `as_of_date` | Book, daily |
| `live_auction_possible` | At least the catalog lead time to expiry, so unsold items can still go into an auction | `days_to_expiry`, `live_catalog_lead_days` | Contract, daily |
| `channel_price_realization` | Gross proceeds ÷ appraised value for items sold, by channel and item type, over contracts closed in the last 12 months | `gross_amount`, `estimate_usd`, `listing_channel`, `asset_type` | Channel × asset type |
| `unsold_on_weak_channel` | Appraised value of unsold items listed where their type's price realization is at least the gap below its best channel | `channel_price_realization`, `estimate_usd`, `listing_channel`, `weak_channel_gap`, `unsold_estimate` | Contract, daily |
| `appraisal_coverage` | Share of the contract's items with an intake appraisal | `estimate_usd`, `asset_id` | Contract, daily |
| `reconciled` | True when status, listings and sales agree across the three systems | `status`, `listing_status`, `sale_id` | Contract, daily |
| `closed_below_target` | Realized sales at expiry below target | `realized_sales`, `target_price`, `status`, `expiry_date` | Contract, at close |
| `shortfall_at_close` | max(0, target − realized sales at expiry): what Second Avenue paid | `target_price`, `realized_sales`, `closed_below_target` | Contract, at close |
| `first_flag_date` | Earliest as-of date with a risk flag at either tier | `risk_flag`, `as_of_date` | Contract |
| `first_act_date` | Earliest as-of date with the risk tier at act | `risk_tier`, `first_flag_date` | Contract |
| `detection_lead_time_days` | expiry date − first act date, for contracts closing below target; 0 if never flagged act | `expiry_date`, `first_act_date`, `closed_below_target` | Contract, at close |
| `flagged_by_halfway` | First act date on or before day 45 | `first_act_date`, `start_date` | Contract, at close |
| `false_positive` | Flagged act at some point, then closed at or above target | `first_act_date`, `closed_below_target` | Contract, at close |
| `new_flags` | Contracts whose first act date falls in the period | `first_act_date` | Book, weekly |
| `watch_list_size` | Contracts on watch that day | `risk_tier`, `as_of_date` | Book, daily |

### Worked example

A $50,000 contract on a 90-day window holds eight items appraised at $56,000. By day 30 it has sold four of them, appraised at $14,000, for $11,000: about 79 cents on the appraised dollar. With the $7,500 cushion, price realization is (11,000 + 7,500) ÷ (14,000 + 7,500) = 0.860. The sell-through for days 30 to 44 is 0.824, so the projection is 11,000 + 42,000 × 0.824 × 0.860 ≈ $40,800, 82% of target, and the projected shortfall is about $9,200. Linear pacing, kept as context, reads 66%.

On its actual sales path, the projection is already under 95% of target on day 21, the first day a flag is allowed. Only 14% of its appraised value has sold by then, so the flag goes on watch. A third sale on day 22 lifts that to 19% and the flag moves to act. Today the contract would be noticed in its final week. That difference, 68 days of lead time against about 5, is what the primary metric measures. The contract closes at $36,000: `shortfall_at_close` is $14,000.

### Questions the metrics must answer

| Question from discovery | Answered with |
|---|---|
| How are a consignor's contracts performing? | `projected_final_value` against target, and `exposure_at_risk`, by consignor |
| Which asset types underperform, and in which channel? | `channel_price_realization` by asset type and channel |
| Which contracts are close to expiry and still behind? | `risk_flag` and `risk_tier` filtered by `days_to_expiry` |
| Do some regions or channels have performance issues? | Share of contracts flagged, and `exposure_at_risk`, by region and channel |

## 4. Non-functional requirements

| ID | Requirement | Priority |
|---|---|---|
| NFR-1 | **Daily refresh.** Landed before the Ops day starts, with all three sources reflecting the same point in time. | Must |
| NFR-2 | **One definition per metric.** Lists, rollups and answers to questions all read the calculated fields; none recomputes them. | Must |
| NFR-3 | **Reproducible by date.** Any day's output can be regenerated for that as-of date and comes out the same. | Must |
| NFR-4 | **Read-only access for questions.** The question layer can't change data and can't read the source tables directly. | Must |
| NFR-5 | **Appraisal completeness.** Every refresh reports `appraisal_coverage`. A contract below 95% is marked rather than silently projected, because the flag prices unsold items from their appraisals. | Must |

Daily is the slowest refresh that doesn't spend the lead time the product exists to win; the reasoning is in the opportunity brief.

## 5. Release criteria

The pilot goes live with Ops when the backtest meets the go-live criteria in the [opportunity brief](https://caioluthi.github.io/portfolio/phase-2-opportunity.html#go-live). The requirement on this side is DPR-7: it must produce every number those criteria use, for any setting of the flag parameters.

## 6. Assumptions and dependencies

- Twelve months of contract, listing and sales history can be extracted from the three source systems. If not, the backtest in DPR-7 can't run and go-live has no evidence.
- Ops commits to working the morning list during the pilot. If not, live lead time measures whether anyone looked, not the flag.
- Contract targets and windows in ConsignTrack are accurate. The product reports on them but doesn't validate the commercial terms.
- Every item has an appraised value recorded at intake, within roughly 30% of what it sells for, as the prototype assumed. Much noisier appraisals would weaken the projection.
- Sell-through rates are re-learned from recently closed contracts on a regular schedule, so the projection follows changes in demand.

## 7. Open questions

- **OQ-1 · Extraction** (Engineering · NFR-1, DPR-1). Full daily snapshots of the three sources, or changes only, and how are they frozen to the same point in time?
- **OQ-2 · Source of truth** (Product · DPR-2, DPR-3). When systems disagree on a contract's status, which one wins for the flag, while DPR-2 still reports the disagreement?
- **OQ-3 · Listings** (Engineering · DPR-1, DPR-5). Do listings need to be their own entity, to show where an asset was placed over time, or is the channel on the sale enough?
- **OQ-4 · Delivery** (Engineering · DPR-5). Where does the morning list live: a dashboard, an email, or the question interface?
- **OQ-5 · Day boundary** (Engineering · DPR-3). Which time zone defines a contract day, for the day floor and for expiry?
- **OQ-6 · Channel attribution** (Product · DPR-4). Do we count a contract under its main channel, or split its exposure across its items? *Resolved:* split over each contract's unsold items by appraised value. The prototype showed that whole-contract counting moved 7 to 15% of exposure between channels, and that both options need only each item's current listing.
- **OQ-7 · Question layer** (Product + Engineering · DPR-9, NFR-4). What hosting and cost does it need, and how is its accuracy tested before Ops sees it?
- **OQ-8 · Lots** (Product + Engineering · DPR-3, NFR-5). Some consignments are appraised as one line rather than item by item. Do we split the appraisal across the items or treat the lot as one item? Either works if it is applied the same way every time.
- **OQ-9 · Appraisals** (Product · DPR-1, DPR-3). Is an appraisal recorded for every item at intake, and is it kept when an item is repriced? *Resolved:* repricing overwrites it in ConsignTrack today, so the intake appraisal becomes its own field and NFR-5 reports its completeness.

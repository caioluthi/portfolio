# Second Avenue contract risk: product requirements

Revision: 1 · 2026-10-21 · Draft for Engineering
Opportunity: [opportunity brief, revision 1](opportunity.md)

This page says what the contract-risk product must do, with a one-line reason for each requirement. Why it matters, how success is judged and what the pilot is betting on are in the opportunity brief. How it is built and when it ships come from Engineering. Second Avenue is fictional and every figure is simulated.

## 1. Goal and users

Give Ops and Finance a trusted, early view of which Risk contracts are pacing below target, so they can act before the contract expires. Targets for every metric below are set in the [opportunity brief](opportunity.md#what-success-looks-like).

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
| Reconciliation | `reconciled` |
| Shortfall payouts avoided | `shortfall_at_close`, `closed_below_target` |

## 2. Scope

**Pilot**
- Linear pacing and the risk flag
- Projected shortfall and exposure at risk
- Daily refresh with cross-source reconciliation
- Ranked daily list of flagged contracts for Ops
- Book rollups by region, channel, asset type and consignor for Finance
- Plain-language questions over these metrics

**Next**
- Pacing against the historical sales curves of similar contracts, by asset type, channel and region, once the pilot shows where linear pacing is wrong
- Suggested interventions per flagged contract, once Ops has worked the list
- Logging of Ops actions, so the recovery rate can be measured instead of assumed

**Out of scope**
- Automated repricing or channel moves
- Real-time streaming
- What-if simulation of moving items between channels
- Optimizing the upside tiers

## 3. Data product requirements

### DPR-1 · One contract view across systems · Must
**What:** Every Risk contract, active or closed, is joined with its consignor, its assets and their sales into a single daily snapshot that carries every required field below.
**For:** priya. Today contracts, listings and sales live in three systems and an analyst is the integration layer.

### DPR-2 · Cross-source reconciliation · Must
**What:** At every refresh, each active contract's status and sales are checked across ConsignTrack, Listings and Sales. Disagreements are reported with the contract and the systems involved, never silently resolved.
**For:** priya, david. Priya's one essential requirement, and the reconciliation guardrail.

### DPR-3 · Governed metrics as calculated fields · Must
**What:** Every calculated field below is defined once, computed daily per contract from the required fields, and exposed by name to everything downstream. The flag threshold and the day floor are parameters, so they can change without changing a definition.
**For:** maria, david. The single source of the numbers Ops acts on, Finance reports and the success metrics judge.

### DPR-4 · Exposure rollups for Finance · Must
**What:** Exposure at risk and the share of contracts flagged roll up by region, channel, asset type and consignor, from contract level to the whole book.
**For:** david. Replaces the quarterly Risk Book Summary as the view of exposure.

### DPR-5 · Ranked morning list for Ops · Must
**What:** Each morning, before the working day starts, Ops sees the flagged contracts ranked by projected shortfall, with pacing, days to expiry and sales so far by channel.
**For:** maria. She asked for a short list of which contracts to open first.

### DPR-6 · Flag history · Must
**What:** Each contract's daily flag is kept, so its first flag date is known and any past day's list can be reproduced as it was.
**For:** david. Lead time can't be measured without it, and Finance needs to audit what was known when.

### DPR-7 · Backtest · Must
**What:** The daily flag can be replayed over the last 12 months of closed contracts, alongside today's practice of a review in the final week, producing every success metric, for any setting of the flag parameters.
**For:** maria, david. The go-live decision in section 5 depends on it.

### DPR-8 · Success scorecard · Should
**What:** Once live, the success metrics are reported weekly from their calculated fields, broken out by channel and contract size.
**For:** david. Keeps the guardrails honest after launch and measures the two known risks to the pilot.

### DPR-9 · Questions in plain language · Should
**What:** Ops and Finance can ask the four discovery questions in plain language. Answers come only from the calculated fields, name the metric and the as-of date, and say plainly when a question is outside what the product supports.
**For:** maria, david. What Priya called a nice-to-have: "then they'd stop asking me."

### Key entities

Consignor → Contract → Asset → Sale event · dimensions: channel (app, website, live), region

A contract carries its target price, its 90-day window and its tier schedule, which can be negotiated per contract. Each asset belongs to one contract and is listed on one channel at a time. Each sale event records the channel and region it happened in. The physical design, keys and grain are Engineering's.

### Required fields

DPR-1 is met when the daily snapshot carries every field below, from the system named. This is the data contract Engineering sizes against.

| Entity | Field | Meaning | Source | Needed for |
|---|---|---|---|---|
| Consignor | `consignor_id` | Unique consignor | ConsignTrack | Rollups by consignor (DPR-4) |
| Contract | `contract_id` | Unique contract; links to its consignor | ConsignTrack | Every calculated field (DPR-1) |
| | `start_date` | First day of the contract window | ConsignTrack | `days_elapsed`, `elapsed_share` |
| | `lifecycle_days` | Length of the window, 90 by default | ConsignTrack | `elapsed_share` |
| | `expiry_date` | Last day of the window | ConsignTrack | `days_to_expiry`, `detection_lead_time_days` |
| | `target_price` | Guaranteed target in USD | ConsignTrack | `pacing_pct`, `projected_shortfall` |
| | `tier_schedule` | Negotiated upside tiers | ConsignTrack | Carried for context; not used by pilot metrics (DPR-1) |
| | `status` | Active, closed or cancelled | ConsignTrack, checked against Listings and Sales | `risk_flag`, `reconciled` |
| | `region` | Region that manages the contract | ConsignTrack | Rollups by region (DPR-4) |
| Asset | `asset_id` | Unique asset; belongs to one contract | ConsignTrack | `realized_sales` |
| | `asset_type` | Category, such as furniture or jewelry | ConsignTrack | Rollups by asset type (DPR-4) |
| | `listing_status`, `listing_channel` | Where and whether the asset is listed | Listings | `reconciled`, sales by channel on the Ops list (DPR-5) |
| Sale event | `sale_id` | Unique sale of one asset | Sales | `reconciled` |
| | `sale_date` | Date the sale closed | Sales | `realized_sales` |
| | `gross_amount` | Gross proceeds in USD | Sales | `realized_sales` |
| | `channel` | App, website or live | Sales | Rollups and Ops list by channel (DPR-4, DPR-5) |
| | `region` | Region where the sale happened | Sales | Sales performance by region (DPR-4) |
| Parameter | `flag_threshold` | 0.80 for the pilot: flag below 80% of linear pace. A starting value; the backtest tests others | Configuration | `risk_flag` |
| | `flag_day_floor` | 15 for the pilot: no flag in the first two weeks. A starting value | Configuration | `risk_flag` |
| Snapshot | `as_of_date` | Day the snapshot represents | Set by each refresh | `days_elapsed`, `elapsed_share`, `days_to_expiry`, `first_flag_date` |

### Calculated fields

DPR-3 is met when each field below is defined once, computed only from required fields, parameters and other calculated fields, and exposed by this name. The last eight are the inputs to the success metrics.

| Field | Definition | Inputs | Grain |
|---|---|---|---|
| `days_elapsed` | Days since the contract started | `as_of_date`, `start_date` | Contract, daily |
| `elapsed_share` | days elapsed ÷ lifecycle days, capped at 1 | `days_elapsed`, `lifecycle_days` | Contract, daily |
| `days_to_expiry` | expiry date − as-of date | `expiry_date`, `as_of_date` | Contract, daily |
| `realized_sales` | Gross proceeds to date for the contract's assets | `gross_amount`, `sale_date`, `asset_id` | Contract, daily |
| `pacing_pct` | realized ÷ (target × elapsed share) | `realized_sales`, `target_price`, `elapsed_share` | Contract, daily |
| `risk_flag` | Pacing below the threshold, on an active contract, from the day floor on | `pacing_pct`, `status`, `days_elapsed`, `flag_threshold`, `flag_day_floor` | Contract, daily |
| `projected_final_value` | realized ÷ elapsed share (linear projection) | `realized_sales`, `elapsed_share` | Contract, daily |
| `projected_shortfall` | max(0, target − projected final value) | `target_price`, `projected_final_value` | Contract, daily |
| `exposure_at_risk` | Sum of projected shortfall across flagged contracts | `projected_shortfall`, `risk_flag` | Any rollup: region, channel, asset type, consignor |
| `reconciled` | True when status, listings and sales agree across the three systems | `status`, `listing_status`, `sale_id` | Contract, daily |
| `closed_below_target` | Realized sales at expiry below target | `realized_sales`, `target_price`, `status`, `expiry_date` | Contract, at close |
| `shortfall_at_close` | max(0, target − realized sales at expiry): what Second Avenue paid | `target_price`, `realized_sales`, `closed_below_target` | Contract, at close |
| `first_flag_date` | Earliest as-of date on which the risk flag was true | `risk_flag`, `as_of_date` | Contract |
| `detection_lead_time_days` | expiry date − first flag date, for contracts closing below target; 0 if never flagged | `expiry_date`, `first_flag_date`, `closed_below_target` | Contract, at close |
| `flagged_by_halfway` | First flag date on or before day 45 | `first_flag_date`, `start_date` | Contract, at close |
| `false_positive` | Flagged at some point, then closed at or above target | `first_flag_date`, `closed_below_target` | Contract, at close |
| `new_flags` | Contracts whose first flag date falls in the period | `first_flag_date` | Book, weekly |

### Worked example

A $50,000 contract on a 90-day window has sold $11,000 by day 30. Linear pacing expects a third of the target by then, about $16,700, so pacing is 66% and the contract is flagged. Projected linearly, it finishes near $33,000, a projected shortfall of about $17,000.

On its actual sales path, the flag first fires on day 15, the first day it is allowed to. Today it would be noticed around day 85. That difference, 75 days of lead time against about 5, is what the primary metric measures. The contract closes at $36,000: `shortfall_at_close` is $14,000.

### Questions the metrics must answer

| Question from discovery | Answered with |
|---|---|
| How are a consignor's contracts performing? | `pacing_pct` and `exposure_at_risk` by consignor |
| Which asset types underperform, and in which channel? | `pacing_pct` by asset type and channel |
| Which contracts are close to expiry and still behind? | `risk_flag` filtered by `days_to_expiry` |
| Do some regions or channels have performance issues? | Share of contracts with `risk_flag`, and `exposure_at_risk`, by region and channel |

## 4. Non-functional requirements

| ID | Requirement | Priority |
|---|---|---|
| NFR-1 | **Daily refresh.** Landed before the Ops day starts, with all three sources reflecting the same point in time. | Must |
| NFR-2 | **One definition per metric.** Lists, rollups and answers to questions all read the calculated fields; none recomputes them. | Must |
| NFR-3 | **Reproducible by date.** Any day's output can be regenerated for that as-of date and comes out the same. | Must |
| NFR-4 | **Read-only access for questions.** The question layer can't change data and can't read the source tables directly. | Must |

Daily is the slowest refresh that doesn't spend the lead time the product exists to win; the reasoning is in the opportunity brief.

## 5. Release criteria

The pilot goes live with Ops when the backtest meets the go-live criteria in the [opportunity brief](opportunity.md#the-pilot-bet). The requirement on this side is DPR-7: it must produce every number those criteria use, for any setting of the flag parameters.

## 6. Assumptions and dependencies

- Twelve months of contract, listing and sales history can be extracted from the three source systems. If not, the backtest in DPR-7 can't run and go-live has no evidence.
- Ops commits to working the morning list during the pilot. If not, live lead time measures whether anyone looked, not the flag.
- Contract targets and windows in ConsignTrack are accurate. The product reports on them but doesn't validate the commercial terms.

## 7. Open questions

- **OQ-1 · Extraction** (Engineering · NFR-1, DPR-1). Full daily snapshots of the three sources, or changes only, and how are they frozen to the same point in time?
- **OQ-2 · Source of truth** (Product · DPR-2, DPR-3). When systems disagree on a contract's status, which one wins for the flag, while DPR-2 still reports the disagreement?
- **OQ-3 · Listings** (Engineering · DPR-1, DPR-5). Do listings need to be their own entity, to show where an asset was placed over time, or is the channel on the sale enough?
- **OQ-4 · Delivery** (Engineering · DPR-5). Where does the morning list live: a dashboard, an email, or the question interface?
- **OQ-5 · Day boundary** (Engineering · DPR-3). Which time zone defines a contract day, for the day floor and for expiry?
- **OQ-6 · Channel attribution** (Product · DPR-4). Exposure is per contract, but a contract can sell across several channels. Do we count a contract under its main channel, or split its exposure across its items? Engineering needs to know which, because they need different data.
- **OQ-7 · Question layer** (Product + Engineering · DPR-9, NFR-4). What hosting and cost does it need, and how is its accuracy tested before Ops sees it?

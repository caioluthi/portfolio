# Good and bad: what this skill exists to prevent

Each pair comes from the Second Avenue contract-risk PRD. The bad versions are the ones a first draft tends to produce.

## 1. The how leaks into the what

**Bad**
> NFR-1 · Nightly batch job loads ConsignTrack, Listings and Sales into the warehouse with Airflow.

**Good**
> NFR-1 · **Daily refresh.** Landed before the Ops day starts, with all three sources reflecting the same point in time.

Why: "batch", the scheduler and the warehouse are Engineering's choices. What the business needs is a deadline (before the Ops day) and a consistency rule (one point in time). Naming the mechanism closes options Engineering should weigh, and it makes the requirement look met when the job runs even if the data is late or inconsistent.

## 2. The why is restated instead of linked

**Bad**
> DPR-3 · Governed metrics. Because about 15% of contracts underperform, costing roughly $3.6M a year, and because Ops only notices them in the final week, while the recoverable share is estimated at $320K a year if flags arrive 30 or more days before expiry with no more than 40% false alarms, the product must compute...

**Good**
> DPR-3 · Governed metrics as calculated fields · Must
> **What:** Every calculated field is defined once, computed daily per contract from the required fields, and exposed by name to everything downstream.
> **For:** maria, david. The single source of the numbers Ops acts on and Finance reports; nothing later reinvents them.

Why: the sizing and targets live on the opportunity brief and change there. Copied into the PRD, they go stale the first time the opportunity is revised, and the PRD starts contradicting it. One line of reason per requirement, and a link for the rest.

## 3. A success metric with no fields behind it

**Bad**
> The primary metric is detection lead time: how many days earlier we flag underperforming contracts.

**Good**
> | Detection lead time | `detection_lead_time_days` |
>
> | `detection_lead_time_days` | `expiry_date` − `first_act_date`, for contracts that closed below target; 0 if never flagged act | `expiry_date`, `first_act_date`, `closed_below_target` | Contract, at close |
>
> …and `first_act_date` is itself defined from `risk_tier` history, which DPR-6 requires the product to keep.

Why: a metric in prose can't be built or tested. Decomposed into calculated fields, each one traceable to a required field with a source system, it becomes something Engineering can size and the backtest can compute. The decomposition is also where gaps show up: here it showed the product had to keep every day's flag, which became its own requirement (flag history).

## 4. A gap is guessed instead of raised

**Bad**
> DPR-4 · Exposure by channel: each contract's exposure is assigned to its main channel.

**Good**
> **OQ-6 · Channel attribution** (Product · DPR-4). Exposure is per contract, but a contract can sell across several channels. Do we count a contract under its main channel, or split its exposure across its items? Engineering needs the answer because the two need different data.

Why: writing out the fields exposed that "exposure by channel" had no definition. Picking one silently would have hidden a product decision inside a requirement. As an open question it got tested: the prototype showed that assigning whole contracts moved 7 to 15% of exposure between channels, so the PRD's next revision split it by item.

## 5. A judgment baked into a definition

**Bad**
> Risk flag: pacing below 80% from day 15 onward.

**Good**
> Risk flag: `projected_final_value` below `flag_threshold` × `target_price`, from `flag_day_floor` onward.
> Parameters: `flag_threshold` (0.95 for the pilot), `flag_day_floor` (21), chosen by the backtest.

Why: 80% and day 15 were starting guesses. The prototype tested every combination and chose 95% and day 21. Because they were parameters, that change touched configuration and not the definition, the backlog or the code.

## 6. A solution where a need should be

**Bad**
> DPR-5 · A Tableau dashboard for Ops with a risk tab.

**Good**
> DPR-5 · Ranked morning list for Ops · Must
> **What:** Each morning, before the working day starts, Ops sees the contracts flagged act, ranked by projected shortfall...
> **OQ-4 · Delivery** (Engineering · DPR-5). Where does the morning list live: a dashboard, an email, or the question interface?

Why: the need is the ranked list and when it arrives. The delivery surface is a choice with its own trade-offs, and naming a tool turns it into a requirement nobody decided.

## 7. A number used for something it can't support

**Bad**
> Out of scope: automated repricing.
> (Finance books exposure at risk as the quarter's shortfall reserve.)

**Good**
> Out of scope: …and using exposure at risk as an accounting reserve. It is built to rank and flag contracts, not tested as a forecast of payouts.

Why: a headline number travels. If the PRD doesn't say what it is not for, someone will use it for that. Here it was the Finance manager, in the feedback session. Saying so in scope is cheaper than finding out at quarter end.

## 8. A revision that rewrites history

**Bad**
> (Revision 2 renumbers the open questions after inserting a new one at 7, so the old OQ-7 becomes OQ-9. The backlog still says OQ-7.)

**Good**
> Revision 2 keeps OQ-1 to OQ-7, appends OQ-8 and OQ-9, marks OQ-6 *Resolved:* with what decided it, and lists every change at the top with the evidence that prompted it. Revision 1 is archived unchanged.

Why: the backlog, issues and refinement notes point at IDs. Renumbering silently breaks every link and makes the change history unreadable. The Second Avenue PRD made this mistake once, and this rule exists because of it.

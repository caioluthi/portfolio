# Second Avenue: contract risk, opportunity brief

Revision: 1 · the version the first PRD (`prd-v1.md`) was written against
Published: [opportunity, revision 1](https://caioluthi.github.io/portfolio/phase-2-opportunity-v1.html)

Second Avenue is a fictional consignment retailer and every figure here is simulated. This is the input to the skill's Draft mode.

## The problem

Under a Risk contract, Second Avenue guarantees the consignor a target price. If sales fall short, the company pays the difference. If they beat the target, the company keeps a tiered share of the overage: 20% on the first $10K, 30% from $10K to $20K, and 70% above that, unless the contract negotiates other tiers.

That makes every Risk contract a standing exposure. The only way to manage it is to act while the contract is still running: move assets to a better channel, reprice them, or put them into a live auction.

Today nobody can see whether a contract is on pace to hit its target. Contract data sits in ConsignTrack, listings and sales sit in other systems, and the only exposure report is the quarterly Risk Book Summary, which looks backward. Ops relies on individual judgment and Finance sees the damage after the contract expires. A one-off view takes an analyst about 8 hours, arrives monthly at best, and drifts out of sync between systems.

About 15% of contracts underperformed over the trailing 12 months, and 18% over the trailing 6. Shortfall payouts come to roughly $3.6M a year.

**How might we** give Ops and Finance a trusted, early view of which Risk contracts are pacing below target, so they can act before the contract expires?

Out of scope for this framing: predicting final outcomes with historical models, planned for a later version, and automating the interventions themselves.

## The opportunity

A shortfall dollar is recoverable only if the contract showed warning signs early enough, an action was still available, and that action worked.

| Step | Low | Base | High | Basis |
|---|---|---|---|---|
| Annual shortfall payouts | $3.6M | $3.6M | $3.6M | Finance interview, one-off manual pull |
| Showed warning signs by halfway | × 50% | × 70% | × 90% | Judgment, informed by the Finance interview |
| An action was still available | × 30% | × 50% | × 70% | Judgment, informed by Finance and Ops |
| Recovered when acted on | × 20% | × 40% | × 60% | Assumption with no interview evidence |
| **Recoverable per year** | **~$110K** | **~$500K** | **~$1.4M** | |

Ops review cost, at 10 minutes per flag and $60 an hour: about $5K a year at 10 flags a week, $13K at 25, $31K at 60.

## What success looks like

The product controls only how early it raises the flag, so detection lead time is the primary metric and dollars saved sit above it as the outcome.

| Role | Metric | Definition | Target |
|---|---|---|---|
| Outcome | Shortfall payouts avoided | Annual payouts against the ~$3.6M baseline; tracked over quarters, not a launch gate | ~$500K a year |
| Primary | Detection lead time | Days from a contract's first risk flag to its expiry, for contracts that closed below target; 0 if never flagged | Median ≥ 30 days (today: under ~7) |
| Supporting | Recall at halfway | Share of eventual underperformers flagged by day 45 | ≥ 70% |
| Guardrail | False-positive rate | Share of flagged contracts that closed at or above target | ≤ 40% |
| Guardrail | Alert volume | New flags per week across the book | ≤ 25 a week |
| Guardrail | Reconciliation | Share of active contracts whose status and sales agree across the three systems at each refresh | 100% |

## The pilot bet

The pilot tests one claim: a simple pacing flag, computed daily from data Second Avenue already has, catches underperforming contracts weeks earlier than today without burying Ops in false alarms.

- **Linear pacing first.** Compare sales to date with a straight line from zero to the target. It needs no history and Ops can check it in their head. Pacing against the historical sales curves of similar contracts comes next.
- **Daily refresh.** Ops decides over days; weekly could spend 7 of the days the primary metric is trying to win, and real-time makes the three systems harder to keep consistent.
- **Go-live.** Replayed over the last 12 months of closed contracts, the flag must meet: median lead time ≥ 30 days, ≥ 70% of underperformers flagged by day 45, ≤ 40% false alarms, ≤ 25 new flags a week, and every active contract reconciling. The 80% threshold and the day-15 floor are starting values; the replay tests the alternatives.
- **Risks.** Contracts whose items sell late at a live auction will look behind until the auction. Single-item contracts show nothing sold until the one item sells. The replay can't prove the dollars, because it can't show whether Ops would have acted.

## From discovery

**Users**
- **Maria, Ops contract manager.** Works contract by contract. "I know my options. I just can't see the problem in time." Wants a short list of which contracts to open first.
- **David, Finance manager.** Works at book level. Sees exposure in the quarterly Risk Book Summary, after the fact. Can work with a weekly refresh.
- **Priya, data analyst.** Builds one-off views by pulling contracts, listings and sales from three systems: about 8 hours a report, and the systems drift apart while she pulls them. Her one essential: the numbers have to agree across systems. A question interface is a nice-to-have: "then they'd stop asking me."

**The questions users asked**
1. How are a consignor's contracts performing?
2. Which asset types underperform, and in which channel?
3. Which contracts are close to expiry and still behind?
4. Do some regions or channels have performance issues?

**Entities, as users described them:** consignors sign contracts; a contract holds one or more assets, each listed on a channel (app, website or live auction); a sale event records an asset selling, on a channel, in a region.

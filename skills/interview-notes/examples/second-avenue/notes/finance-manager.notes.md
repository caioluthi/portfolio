# Interview notes: Finance manager, date not provided
<!-- notes-format: v1 -->

**Research goal:** Visibility into underperforming consignment contracts (from the transcript header)
**Coverage:** whole transcript read; 10 interviewee turns; low-confidence passages: none

## What they said

### Pain points
- **The exposure view is retrospective (month-end or quarter-end), not forward-looking** (prompted · experience)
  > "It tells me how much we paid out last period, not which contracts are heading toward a payout right now."
- **Quarters close with surprise shortfall payouts** (prompted · experience)
  > "More than once we've closed a quarter and been surprised by how much we paid out in shortfalls."
- **No way to alert Ops while there is still time to act** (prompted · experience)
  > "There's no way for me to flag it to Ops while there's still time to do something."
- **Trend figures are not available without manual effort** (prompted · experience)
  > "nothing gives me that trend automatically."
- **Cannot separate preventable shortfalls from unavoidable ones** (prompted · experience)
  > "breaking out how much came from contracts that could have been caught earlier versus ones that were always going to miss? That's not something I can pull today."
- **Contracts are not looked at before the end of their window** (prompted · experience)
  > "nobody's looking at the halfway point. We only look at the end."
- **Early flagging from Ops currently means opening contracts one by one** (prompted · experience)
  > "Last quarter I asked [redacted: name] on the Ops side whether he could flag at-risk contracts early, and he told me he'd have to open each one by hand."

### Upsides of the current process
- **The total quarterly payout is known** (prompted · experience)
  > "We know the total payout number each quarter"
- **A manual tally from the Risk Book Summary is possible, if costly** (prompted · experience)
  > "I could dig through the Risk Book Summary and tally it by hand"

### Their view of the optimal solution
- **See, while the quarter is still running, which regions and asset types are trending toward shortfall payouts** (prompted)
  > "I'd want to see, while the quarter is still running, which regions and asset types are trending toward shortfall payouts."
- **A number he trusts and can reproduce** (prompted)
  > "I'd want a number I trust. I don't want to walk into a meeting defending a figure nobody can reproduce."

### Nice-to-haves
- **Daily refresh instead of weekly** — *stated* (prompted)
  > "Daily would be nicer, but weekly I could work with."
- **Per-contract detail for Finance, with the ability to drill in** — *stated* (prompted)
  > "Per-contract detail is nice to have for me"

### Critical needs
- **A forward-looking view of expected payouts, refreshed at least weekly** — *stated* (prompted)
  > "Essential is a forward-looking view of expected payouts that refreshes at least weekly."
- **A figure he can trust and reproduce** — *inferred* (prompted)
  > "I don't want to walk into a meeting defending a figure nobody can reproduce."

### Numbers mentioned
| Figure | Period / unit | Basis (measured · estimated · hearsay) | Quote |
|---|---|---|---|
| About 15% of contracts underperformed | trailing 12 months | measured (one-time manual pull), softened with "roughly" | "roughly 15% of contracts underperformed over the trailing 12 months" |
| About 18% of contracts underperformed | trailing 6 months | measured (one-time manual pull), softened with "roughly" | "18% over the trailing 6" |
| About $3.6M aggregate shortfall payouts | past year | estimated (one-time reconstruction) | "estimated around $3.6M in aggregate shortfall payouts over the past year" |
| Most underperformers showed warning signs by the halfway point | contract lifecycle | estimated (assumption) | "I'd assume most of them did, if we'd been looking." |

## What we read into it

### Context and background
**Stated**
- Uses the Risk Book Summary in Tableau as his exposure view, at month-end or quarter-end
  > "I pull the Risk Book Summary in Tableau, but that's really a month-end or quarter-end view."
- Learns about channel performance informally from the Ops team
  > "that's an impression from a few conversations with the Ops team, not something I've actually measured."

**Inferred values (job-relevant only)**
- Trustworthy, reproducible numbers — *inferred*
  > "I don't want to walk into a meeting defending a figure nobody can reproduce."
- Early warning over after-the-fact reporting — *inferred*
  > "By the time I see the number, the contracts are already closed."

### Signals worth exploring
1. **An untested channel hypothesis (live auctions)**; *why it stood out:* he offers it as a hunch and says himself that it is unmeasured, yet it could steer where attention goes.
   > "My gut says live auction events underperform more, but that's an impression from a few conversations with the Ops team, not something I've actually measured."
   *Follow-up question:* What would you need to see to confirm or rule that out?
2. **Weekly refresh is acceptable**; *why it stood out:* he sets a tolerance for weekly updates without saying which decisions depend on how fresh the data is.
   > "Daily would be nicer, but weekly I could work with."
   *Follow-up question:* Which decisions would change if you saw the numbers daily instead of weekly?
3. **The Ops handoff depends on manual checks**; *why it stood out:* he mentions it in passing and does not say what happened next.
   > "he told me he'd have to open each one by hand."
   *Follow-up question:* What happened after that conversation?

## Privacy flags
1 personal name redacted (third party, Ops colleague). No sensitive content tagged.

# Evidence after the Phase 4 prototype

The input to the skill's Revise mode: what the prototype and the feedback sessions found, and what the PM decided about each item. Full detail is on the [Phase 4 page](https://caioluthi.github.io/portfolio/phase-4-prototype.html) and in `prototype/` in this repository.

## From the prototype

The flag in `prd-v1.md` was replayed day by day over the 1,968 contracts that closed in the last 12 months.

| # | Finding | Source |
|---|---|---|
| P1 | Linear pacing fails the false-alarm guardrail: 80% of its flags were false, and none of the 40 threshold and day-floor combinations got below 70%. Early in a contract, being behind mostly means the big items haven't sold yet. | Replay of the PRD's flag |
| P2 | A projection that counts unsold inventory, priced by how the contract's sold items fetched against their appraisals, cut false alarms to 37% on contracts not used for tuning. | Test of three alternatives, rule fixed before the run |
| P3 | Splitting flags into **act** (enough of the contract has sold to trust the signal) and **watch** (thin evidence) added 6 points of recall at halfway; the watch list stayed at 10 contracts or fewer on 95% of days. | Same test |
| P4 | Best settings, chosen by the fixed rule: projection below 95% of target, from day 21, a cushion worth 15% of target on price realization, act once 15% of appraised value has sold. | Same test |
| P5 | Within the 40% false-alarm limit, no setting flagged more than about 41% of underperformers by day 45. The 70% target came from a judgment in the sizing. | Same test |
| P6 | The projection needs an appraised value for every item, which the PRD doesn't require. | Building the projection |
| P7 | Counting each contract's exposure under its main channel moved 7 to 15% of exposure between channels; 21 of 37 flagged contracts were spread across channels. Splitting by item needs only each item's current listing. | Building Finance's views |

## From the feedback sessions

| # | Who | What they said | Decision |
|---|---|---|---|
| F1 | Maria, Ops | Contracts with nothing left to sell don't belong on her list. 4 of 37 act contracts, 23% of exposure. | Change: off the morning list |
| F2 | David, Finance | The surest number is the exposure already locked in; show it on its own. | Change: shown separately to Finance |
| F3 | Maria | Live auction catalogs close 14 days before the sale; under that, repricing is the only lever. 12 of 33 act contracts. | Change: show whether a live auction is still possible |
| F4 | Maria | Show where unsold items are, not what to do. 25 of 33 act contracts have unsold items on a channel where their type sells at least 15 points below its best. | Change: show unsold value on a weak channel |
| F5 | Maria | Which contracts are new, and which she has already worked. | Partly: new today is built; already worked needs logging of Ops actions, which stays next |
| F6 | David | The daily exposure figure swung between $229K and $366K over the summer; too noisy to report up. | Change: a 4-week average beside it |
| F7 | David | Wants to book exposure at risk as the quarter's shortfall reserve. | No: it ranks contracts and was never tested as a forecast of payouts. Say so in scope |
| F8 | Priya, Data | Repricing overwrites the appraisal in ConsignTrack, so "appraised value at intake" doesn't exist as a clean field. | Change: the intake appraisal is its own field that repricing can't overwrite |
| F9 | Priya | Missing appraisals would quietly degrade the flag. | Change: report completeness every refresh; mark contracts below 95% |
| F10 | Priya | Some lots are appraised as one line, not item by item. | Open: split the appraisal or treat the lot as one item |

## Belongs on the opportunity brief, not the PRD

P5 moves a target and the sizing: recall at halfway goes from 70% to 40%, and the base case from about $500K to about $320K a year. Success is measured from the first act flag, and a guardrail on watch-list size (at most 40 on 95% of days) is added. Those are revised on the opportunity brief; the PRD only follows them.

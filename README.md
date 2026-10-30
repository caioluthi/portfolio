# Second Avenue: a data product case study

An end-to-end data product case study, from discovery to a working prototype: flagging consignment contracts that pace below target **before** they expire.

Second Avenue is a fictional consignment retailer. The use case comes from a problem I worked on professionally; the company, people and data here are simulated.

**Read the case study:** the pages live in [`docs/`](docs/) and are published with GitHub Pages.

## The problem in one paragraph

Second Avenue guarantees each consignor a target price and pays the difference when a contract misses. About 15% of contracts miss, costing roughly $3.6M a year, and nobody sees it until the contract has expired. The product tracks each contract's pacing against target across contracts, listings and sales, flags the ones falling behind while there is still time to act, and lets Ops and Finance ask questions about it in plain language.

## Phases

| # | Phase | Where | Status |
|---|---|---|---|
| 1 | [Discovery](docs/phase-1-discovery.html) | `docs/` | Done |
| 2 | [Opportunity & success metrics](docs/phase-2-opportunity.html) | `docs/`, sizing model in `sizing/` (to come) | Done |
| 3 | [Product requirements (PRD)](docs/phase-3-prd.html) | `docs/` | Done |
| 4 | [Prototype & validation](docs/phase-4-prototype.html): test the pilot bet, then show what it changed. The plain-language question layer is deferred to the end | BigQuery sandbox, Claude API | Done |
| 5 | [Backlog and roadmap](docs/phase-5-backlog-roadmap.html): six epics and their functional stories, refinement with the Tech Lead, Now / Next / Later | `backlog/`, GitHub Issues | Done |
| 6 | Package and deliver | Case study, AI skills, walkthrough | Planned |

### Why the prototype comes before the backlog

The riskiest assumption is that a simple pacing flag catches underperforming contracts weeks earlier without burying Ops in false alarms. A product manager can test that with AI-assisted prototyping before asking Engineering for a production backlog. The prototype is deliberately throwaway: it skips the parts Engineering owns, such as landing real source systems, reconciliation, reproducibility and access control. What it learns feeds back into the PRD, and the backlog in Phase 5 is planned from the revised version.

## Repository layout

```
docs/      Case study pages (GitHub Pages site)
backlog/   Backlog: epics and functional stories traced to the PRD
skills/    Claude skills used to build the case study, with their scripts
```

More folders are added as the build phases land.

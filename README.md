# Second Avenue: a data product case study

An end-to-end data product, from discovery to a working build: flagging consignment contracts that pace below target **before** they expire.

Second Avenue is a fictional consignment retailer. The use case comes from a problem I worked on professionally; the company, people and data here are simulated.

**Read the case study:** the pages live in [`docs/`](docs/) and are published with GitHub Pages.

## The problem in one paragraph

Second Avenue guarantees each consignor a target price and pays the difference when a contract misses. About 15% of contracts miss, costing roughly $3.6M a year, and nobody sees it until the contract has expired. The product tracks each contract's pacing against target across contracts, listings and sales, flags the ones falling behind while there is still time to act, and lets Ops and Finance ask questions about it in plain language.

## Phases

| # | Phase | Where | Status |
|---|---|---|---|
| 1 | [Discovery](docs/phase-1-discovery.html) | `docs/` | Done |
| 2 | [Frame the opportunity](docs/phase-2-opportunity.html) | `docs/`, sizing model in `sizing/` (to come) | Done |
| 3 | [Success metrics & scope](docs/phase-3-metrics-scope.html) | `docs/` | Done |
| 4 | Structure the work | GitHub Issues and Projects | Next |
| 5 | Data foundation | BigQuery sandbox, synthetic data generator | Planned |
| 6 | Semantic layer | dbt Semantic Layer / MetricFlow | Planned |
| 7 | Conversational layer | Claude API and a lightweight UI | Planned |
| 8 | Package & deliver | README, skills, case study, walkthrough | Planned |

## Repository layout

```
docs/      Case study pages (GitHub Pages site)
```

More folders are added as the build phases land.

# backlog.yaml format

One file holds the backlog from first draft to synced issues. Fields are grouped by who writes them. Draft writes the Product fields; Record refinement adds Engineering's; the PM adds the roadmap fields by hand; Sync adds issue numbers.

## Product fields (written by Draft)

```yaml
prd: https://example.com/prd.html        # link to the PRD the backlog is planned from

personas:                                # short key → who they are
  maria: Maria, Ops contract manager
  david: David, Finance

requirements:                            # every requirement ID in the PRD, with priority
  DPR-1: must                            # must | should | could
  DPR-8: should
  NFR-1: must

open_questions:
  OQ-1:
    question: Extraction. Full daily snapshots or change capture?
    by: engineering                      # product | engineering | [engineering, product]
  OQ-2:
    question: Which system wins on contract status when systems disagree?
    by: product

epics:
  - key: E1                              # E<n>
    title: Trusted contract data
    outcome: One daily, reconciled, reproducible snapshot of every contract.
    traces: [DPR-1, DPR-2, NFR-1]
    stories:
      - key: E1-S1                       # <epic key>-S<n>
        title: One daily snapshot of every contract
        as: priya                        # a persona key, or a list of them
        so_that: a report becomes a query instead of an eight-hour project
        traces: [DPR-1, NFR-1]
        acceptance:                      # 2 to 4 outcomes
          - Every contract, active or closed, is joined with its consignor, assets and sales.
          - A missing source fails the run instead of landing partial data.
        open_questions: [OQ-1]           # optional: questions not yet settled
        critical_path: Change to a system another team owns.   # optional
        depends_on: [E1-S2]              # optional: story keys
        tasks: []                        # left empty for Engineering
```

Keys never change once synced: issues are matched by them. To retire a story, close its issue; don't reuse its key.

## Engineering fields (added by Record refinement)

```yaml
tech_lead: Tomás, Tech Lead, Data Platform

open_questions:
  OQ-1:
    question: ...
    decision: Full daily snapshots, cut at one timestamp.   # "Open. <why>" if unanswered
    by: engineering

epics:
  - key: E1
    stories:
      - key: E1-S1
        decisions: [OQ-1]                # replaces open_questions once settled
        changed_in_refinement: One line on what changed and why.
        tasks:
          - {key: T1, owner: data eng, task: "Spike, 3 days: ..."}
          - {key: T2, owner: ConsignTrack team (external), task: "..."}
      - key: E1-S4
        added_in_refinement: One line on why it was added.

sprints:                                 # Engineering's plan, in their numbering
  1: {weeks: 1-2, stories: [E1-S1, E1-S3], note: ...}
```

Quote any value that contains a comma or a colon, especially inside `{...}` mappings, or YAML splits it.

## Roadmap fields (added by the PM, never by Draft)

```yaml
epics:
  - key: E1
    milestone: now                       # now | next | later, or a list if it spans

releases:                                # become GitHub milestones on sync
  R1:
    name: Contract book
    week: 4
    stories: [E1-S1, E1-S3]
    who_gets_what: ...
    success: ...

gates:
  go_live:
    story: E3-S2
    when: week 6
    rule: ...
```

## Sync field (written by Sync with --write-back)

```yaml
  - key: E1
    issue: 1
    stories:
      - key: E1-S1
        issue: 2
```

Any other top-level field (links to pages, notes) is kept as is and ignored by the scripts.

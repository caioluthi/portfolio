---
name: prd-to-backlog
description: Turn a PRD with numbered requirements into a Product-owned backlog of outcome epics and functional stories, record what Engineering decides in refinement, and sync the backlog to GitHub Issues. Use whenever someone wants to break a PRD, requirements doc or spec into epics and stories, write user stories or acceptance criteria from requirements, prepare a backlog for refinement or sprint planning, capture the outcome of a refinement session with a tech lead, or create or update GitHub issues from a backlog, even if they don't say "backlog".
---

# PRD to backlog

Turn a PRD into the backlog a product manager hands to Engineering, then keep that backlog in step with what Engineering decides.

The skill draws one line throughout: **Product owns the why and the what; Engineering owns the how and the when.** Product writes epics, functional stories and acceptance criteria. Engineering breaks stories into technical tasks, estimates them by whatever method it uses, and plans the sprints. This skill never estimates, never plans sprints, never writes technical tasks itself and never suggests releases or a roadmap. It leaves room for Engineering's output and records it once it exists. Releases and the roadmap are the PM's call, made after Engineering's plan, and are added to the file by hand.

Everything lives in one file, `backlog.yaml`, which ties the three modes together. Its format is in `references/backlog-schema.md`. Read it before writing or changing the file.

## Pick the mode

| The person has... | Mode |
|---|---|
| A PRD and no backlog yet, or a PRD that changed enough to re-plan | **1. Draft** |
| Notes from a refinement session with the Tech Lead | **2. Record refinement** |
| A backlog they want in GitHub Issues, or changes to push to existing issues | **3. Sync** |

If it's unclear, ask which one. A typical project runs them in order: Draft, then refinement happens between people, then Record refinement, then Sync.

---

## Mode 1: Draft

**Input:** the PRD (markdown, HTML or pasted text), and any later evidence that revised it, such as prototype findings or feedback sessions. Plan from the latest revision; if the PRD says a requirement changed, the backlog follows the change.

**Output:** a `backlog.yaml` and a short framing note in the conversation.

### Steps

1. **Read the PRD for its building blocks.** List every numbered requirement with its priority (must, should, could), the users or personas, the open questions, any worked example, and anything marked out of scope. If requirements aren't numbered, number them first (`REQ-1`, `REQ-2`...) and tell the person, because traceability depends on IDs.
2. **Find what is still unproven.** Read the PRD's assumptions, dependencies and open questions. Note which requirements depend on another team's system or on a field that doesn't exist yet. These become critical-path flags and questions, not epics.
3. **Draft the epics and stop for review.** Show the epics alone, as a table: key, title, outcome, the requirements each traces to. Wait for the person to react before writing stories. Epics are the framing; getting them wrong wastes every story under them.
4. **Write 2 or 3 stories per epic.** Start from the people who use the outcome.
5. **Check coverage both ways** with `scripts/check_backlog.py` (below), fix what it reports, and write the file.
6. **Write the framing note** (format below) and show the stories.

### Rules for epics

- **An epic is an outcome someone could sign off on.** "Trusted contract data: one daily, reconciled snapshot of every contract" is an epic. "Data pipeline", "Phase 1" and "Backend work" are not.
- **Usually 4 to 7 epics.** More than 7 means some epics are really stories or risks. Fewer than 4 means epics are too broad to sign off on.
- **A risk is not an epic.** A risky dependency becomes a `critical_path` note on the story that carries it. A go/no-go decision is left for the PM to add as a gate. Don't promote either to an epic to make it visible.
- **Don't group by layer or by team.** Group by the outcome a user or the business receives.

### Rules for stories

- **2 or 3 functional stories per epic.** These are the starting stories for refinement, not the full breakdown. Engineering splits them further in refinement.
- **Each story has a persona and a "so that".** The persona is a real user from the PRD. The "so that" says what changes for them, not what the system does.
- **Acceptance criteria are outcomes, 2 to 4 per story.** Say what is true when the story is done, not how to build it. "Any past day's snapshot can be regenerated and comes out the same" is an outcome. "Store snapshots as partitioned Parquet files" is an implementation, and belongs to Engineering.
- **Use the PRD's worked example as the acceptance test.** If the PRD has a worked example with numbers, the stories that compute those numbers cite them.
- **Every story traces to at least one requirement.** Use the PRD's IDs exactly.
- **No estimates of any kind.** No story points, T-shirt sizes, hours, days or sprint numbers. Leave `tasks` empty.
- **No product or vendor names** for tools the PRD doesn't name. Write "a dashboard", not a BI product; "a morning email", not an email service.
- **Plain language.** Write so the persona in the story could read it.

### Open questions

Copy each open question from the PRD into `open_questions`, and mark who settles it:

- `by: product` when it is about what the product should do or whom it serves, such as which system wins when two disagree on a business fact.
- `by: engineering` when it is about how it is built, such as extraction method, hosting or time-zone handling.
- Both, when it needs both.

Link each question to the stories it affects. Questions without an owner are listed in the framing note so the PM can assign them.

### Framing note

Keep it short. It goes in the conversation, not in the file.

```
**Planned from:** <PRD name and revision>
**Epics:** <n> · **Stories:** <n> · **Requirements covered:** <n of n musts>

**Still unproven** (what the backlog has to deliver against)
- <1 line each: dependency, missing field, unvalidated assumption>

**Critical path**
- <story key> · <why: another team's system, a field that doesn't exist yet>

**Open questions by owner**
- Product: <keys>
- Engineering: <keys>
- Unassigned: <keys>

**Not covered:** <requirements with no story, and why, e.g. out of scope>
```

---

## Mode 2: Record refinement

**Input:** the existing `backlog.yaml` and the notes from a refinement session: the Tech Lead's task breakdown, decisions, and any pushback on stories.

**Output:** the updated file and a summary of what changed.

Engineering's outputs are recorded as Engineering gave them. Don't rewrite tasks into Product language, and don't add estimates the notes don't contain.

### Steps

1. **Settle open questions.** For each question answered in the session, fill in `decision` and confirm `by`. Leave unanswered ones with `decision: Open` and why.
2. **Record changes to stories.** When Engineering pushed back and the PM accepted, change the story's acceptance criteria and add `changed_in_refinement` with one line on what changed and why. When the PM rejected the pushback, leave the story and record the reason in the summary. A story added in the session gets `added_in_refinement`.
3. **Record tasks** under each story Engineering broke down, with an owner per task. Mark tasks owned by another team in the owner text, such as `ConsignTrack team (external)`.
4. **Record the sprint plan** under `sprints` if Engineering gave one, using their numbering and their notes.
5. **Run the checker** and fix anything it reports.
6. **Summarize** in the conversation: questions settled (and by whom), stories changed or added, stories still without tasks, anything the PM still has to decide.

---

## Mode 3: Sync to GitHub Issues

**Input:** `backlog.yaml` and a GitHub repository the session can write to.

**Output:** labels, milestones, one issue per epic and per story, stories attached to their epic as sub-issues, and issue numbers written back into the file.

### Steps

1. **Run the checker first.** Don't sync a file that fails it.
2. **Dry run and show it.** Run `python scripts/sync_issues.py backlog.yaml --repo OWNER/REPO --dry-run` and show the person what would be created or updated. Creating issues is visible to everyone who watches the repo; wait for a yes.
3. **Sync.** Run it again without `--dry-run`. It is safe to re-run: existing issues are matched by their key (`E1-S2`) and left alone unless `--update` is passed, which rewrites their bodies from the file, for example after refinement.
4. **Write the issue numbers back** with `--write-back`, so the file and the page that shows it can link to each issue.
5. **Report** the issue range, sub-issue counts per epic, and milestone counts.

### What the sync creates

- **Labels:** `epic`, `story`, `critical-path`, and `now` / `next` / `later` if epics carry a `milestone`.
- **Milestones:** one per release in `releases`, only if the PM has added releases. Stories go to the first release that lists them. Epics get no milestone: an epic can span releases, and a milestone on it would be counted twice.
- **Epic issues** with the outcome and traced requirements. **Story issues** with the persona and "so that", acceptance criteria as checkboxes, traces linked to the PRD, decisions from refinement, technical tasks as checkboxes, and the sprint if planned.

### What it can't do

GitHub Projects boards and roadmaps live at the account level, not in the repository, so a repository-scoped session can't create them. After the first sync, tell the person to set the board up once by hand:

1. In the repo's **Projects** tab: **New project → Board**.
2. **Add items from repository**, select all.
3. **Group by: Milestone**, filter `label:story`, save the view.
4. In **Workflows**, turn on **Auto-add to project** with `is:issue repo:OWNER/REPO`, so later syncs land on the board without this step.
5. For a roadmap view, add an **Iteration** field for sprints and give milestones due dates in the repo; groups follow due-date order, and milestones without one sort by name.

---

## The checker

`scripts/check_backlog.py backlog.yaml` checks the file and prints errors (must fix) and warnings (look at):

- Errors: missing required fields; duplicate or malformed keys; a story with no traces; a trace to a requirement not listed in `requirements`; a must-have requirement with no story; a reference to an open question that doesn't exist; any estimate field (`points`, `story_points`, `estimate`, `size`).
- Warnings: an epic with fewer than 2 or more than 3 stories in Draft; fewer than 4 or more than 7 epics; a story with fewer than 2 or more than 4 acceptance criteria; an unknown persona; estimate words in acceptance criteria; an open question with no owner.

Warnings can stand if there's a reason; say what it is.

## Examples

- `references/story-examples.md`: good and bad pairs for epics, stories and acceptance criteria, including the mistakes this skill exists to prevent.
- A full worked example, from PRD to refinement to GitHub Issues: the Second Avenue contract-risk backlog in this repository (`backlog/backlog.yaml`), the [PRD](https://caioluthi.github.io/portfolio/phase-3-prd.html) it was planned from, and the [Phase 5 page](https://caioluthi.github.io/portfolio/phase-5-backlog-roadmap.html) that shows the refinement and the roadmap the PM built on top.

---
name: opportunity-to-prd
description: Turn an opportunity brief (problem, sizing, success metrics and pilot bet) into a PRD with numbered data product requirements, the required and calculated fields behind every metric, and open questions for Engineering, always in the same structure; and revise that PRD when new evidence arrives from a prototype, feedback sessions or refinement. Use whenever someone wants to write a PRD, requirements doc or spec from an opportunity, business case or problem statement, define requirements for a data product, turn success metrics into fields Engineering can build, or update a PRD after a prototype or user feedback, even if they don't say "PRD".
---

# Opportunity to PRD

Turn an opportunity brief into the PRD a product manager takes to Engineering, then keep it honest as evidence comes in.

The skill draws one line throughout: **the opportunity brief owns the why, the PRD owns the what, and Engineering owns the how and the when.** The why is the problem, the sizing, the success targets, the pilot bet and the go-live criteria. The what is the scope, the requirements and the fields the product must carry. The how and the when are architecture, tools, estimates and dates. The PRD links to the brief for reasons and targets instead of copying them, and it names no tools, mechanisms or dates.

Every PRD has the same seven sections, defined in `references/prd-template.md`. Read it before writing. The `prd-to-backlog` skill reads this structure to plan the backlog, so the headings and ID formats matter.

## Pick the mode

| The person has... | Mode |
|---|---|
| An opportunity brief and no PRD yet | **1. Draft** |
| A PRD, plus new evidence: prototype results, feedback sessions, a refinement, a changed opportunity | **2. Revise** |

If it's unclear, ask which one.

---

## Mode 1: Draft

**Input:** the opportunity brief, and the discovery material it rests on (interview notes, personas, the questions users asked). If there's no brief, only a problem statement, say what's missing (success metrics and a pilot bet are the usual gaps) and ask for them before drafting: a PRD without targets has nothing to be judged against.

**Output:** `prd.md` in the template's structure, and a short framing note in the conversation.

### Steps

1. **Read the brief for its building blocks.** List the users, the success metrics with their targets, the pilot bet and its scope, the go-live criteria, the risks, and the questions users asked in discovery. Note anything the brief says is out of scope.
2. **Draft the requirements and stop for review.** Show the DPR list alone, as a table: ID, name, what, for whom, priority. Wait for the person to react before writing fields. Requirements are the frame; getting them wrong wastes every field under them.
3. **Decompose every metric into fields.** Start from each success metric and each thing a user sees (a list, a rollup, an answer). Write the calculated fields that produce it, then the inputs of those, until every input is a required field with a source system, or a parameter. This is where the PRD earns its keep: write down every gap it exposes.
4. **Turn gaps into open questions, not guesses.** When a metric can't be defined without a decision nobody has made, raise it as an `OQ` with an owner and the IDs it blocks. Don't pick an answer and bury it in a definition.
5. **Write the worked example.** One concrete case with numbers, run through the calculated fields. Check the arithmetic.
6. **Fill the remaining sections:** NFRs, release criteria as a pointer to the go-live criteria, and assumptions with what breaks if each is false.
7. **Run the checker** (below), fix what it reports, and write the file.
8. **Write the framing note** (format below).

### Rules for requirements

- **A requirement says what the product does and for whom, testably.** "Each morning, before the working day starts, Ops sees the contracts flagged act, ranked by projected shortfall" is a requirement. "A risk dashboard" is a solution, and "improve visibility" is a wish.
- **One line of reason, tracing back.** The `For:` line names the persona and points to the discovery evidence or the success metric it serves. If it needs more than a line, the reason belongs on the opportunity brief; link it.
- **Usually 5 to 10 DPRs.** More than 12 means some are fields or acceptance criteria. Fewer than 4 means they're too broad to test.
- **Metrics are requirements.** Every success metric in the brief appears in section 1's table, built only from calculated fields. The fields the metric needs are required, even if no user ever sees them; the success metrics can't be measured otherwise.
- **Judgments are parameters.** Any number someone chose (a threshold, a day count, a cap) is a parameter in the required-fields table with its pilot value, so a prototype or a backtest can change it without touching a definition.
- **Say what each headline number is not for.** If a number could be mistaken for something it was never tested as (a ranking score used as a forecast, an exposure figure booked as a reserve), say so under out of scope.
- **No tools, mechanisms or dates.** No product or vendor names for tools the brief doesn't name, no "batch", "streaming", "pipeline", "cron", "sprint", quarter or deadline. Source systems are named by their business names, because they are facts, not choices.
- **Plain language.** Write so the personas could read their own requirements.

### Framing note

Keep it short. It goes in the conversation, not in the file.

```
**Written against:** <opportunity brief and revision>
**Requirements:** <n> DPRs (<n> must, <n> should) · <n> NFRs · **Fields:** <n> required, <n> calculated
**Every success metric decomposed:** yes | no: <which, and what's missing>

**Gaps the decomposition exposed**
- <OQ key> · <one line> · settled by <owner>

**Riskiest assumptions** (what to test before Engineering builds)
- <one line each>

**Next:** <usually: test the riskiest assumption with a prototype, or take to refinement with prd-to-backlog>
```

---

## Mode 2: Revise

**Input:** the current `prd.md` and the new evidence: prototype results, feedback-session notes, refinement decisions, or a revised opportunity brief.

**Output:** the revised `prd.md`, the previous revision archived unchanged as `prd-v<N>.md`, and a change list in the conversation.

### Steps

1. **List what the evidence says, item by item,** with its source. Separate what the evidence *shows* (a measured rate, a failed test, a constraint someone described) from what someone *asked for*.
2. **Decide each item with the person:** change, partial, no, or open. A "no" is recorded too, with its reason; it usually lands in out of scope ("not an accounting reserve"). Don't apply anything before the person agrees, because a revision is a product decision.
3. **Archive the current revision unchanged** as `prd-v<N>.md` before editing.
4. **Apply the changes, keeping IDs stable.**
   - Never renumber. New requirements, NFRs and questions take the next number.
   - A dropped requirement stays, with `· Retired in revision N` in its heading and one line on why.
   - A settled question stays, with a *Resolved:* line saying what was decided and what decided it.
   - A changed definition keeps its field name unless its meaning changed; if it did, add a new field and retire the old one.
5. **Write the `## Revision <N>` block** at the top: one line per change, with the IDs it touches and what prompted it, and a link to the archived revision.
6. **Check the brief.** If the evidence moves a target, a sizing figure or the pilot bet, that change belongs on the opportunity brief, not here. Say so, and list what the brief needs. The PRD only follows the targets.
7. **Run the checker.**
8. **Report the change list** as a table the person can reuse in a case study or a changelog: change, prompted by, evidence, where. Say whether the backlog needs re-planning (`prd-to-backlog`, Draft) or only recording (`prd-to-backlog`, Record refinement).

### Rules for revisions

- **Evidence changes requirements; requests alone don't.** "Ops asked for it" is a reason to consider a change, and the data behind the request is the reason to make it. When the evidence is thin, record the request as open.
- **A target that fails isn't quietly lowered.** If evidence shows a target can't be met, the change goes on the opportunity brief with the trade-off stated (what it costs), and the PRD follows. Moving a goalpost without saying so is the one revision that destroys trust in the rest.
- **Keep the old revision readable.** Archived revisions are never edited after archiving, so anyone can compare what was believed with what was learned.

---

## The checker

`python scripts/check_prd.py prd.md` checks the file and prints errors (must fix) and warnings (look at):

- **Errors:** a missing or out-of-order section; a malformed or duplicate `DPR`, `NFR` or `OQ` ID; a requirement without a priority, a `What:` or a `For:` line; a calculated field whose input isn't defined anywhere in the PRD; a success metric built from a field that doesn't exist; an open question without an owner; a revision after 1 without a `## Revision` block.
- **Warnings:** gaps in ID numbering (expected after a revision, since retired IDs stay; unexpected in a first draft); fewer than 4 or more than 12 DPRs; a required field nothing uses; a persona in a `For:` line that isn't in the users table; a tool, mechanism or date word outside out of scope; no worked example; a `For:` line over 40 words.

Warnings can stand if there's a reason; say what it is.

## Examples

- `references/examples.md`: eight good and bad pairs from a real PRD, covering the mistakes this skill exists to prevent.
- A worked example of both modes in `examples/second-avenue/`: the opportunity brief (`opportunity.md`), the first draft written from it (`prd-v1.md`), the evidence from the prototype and feedback sessions (`evidence.md`), and the revision that evidence produced (`prd.md`). The published versions are the [PRD](https://caioluthi.github.io/portfolio/phase-3-prd.html) and [what the prototype changed](https://caioluthi.github.io/portfolio/phase-4-prototype.html#changed).

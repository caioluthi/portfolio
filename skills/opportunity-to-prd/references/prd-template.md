# PRD template

Every PRD this skill writes has this structure, in this order. `scripts/check_prd.py` and the `prd-to-backlog` skill both read it, so keep the headings, ID formats and table columns exactly as shown. Replace everything in angle brackets.

The PRD says **what** the product must do. The opportunity brief says **why** and how success is judged. Engineering decides **how** and **when**. Anything that belongs to the other two documents is linked, not copied.

````markdown
# <Product name>: product requirements

Revision: 1 · <YYYY-MM-DD> · <Draft for Engineering | Revised after <evidence>>
Opportunity: <link to the opportunity brief, at the revision this PRD is written against>

<One paragraph: what this page is for, where the why lives, and that how and when come from Engineering.>

## 1. Goal and users

<One or two sentences: the outcome the product gives its users. Link to the opportunity brief for the targets.>

| Persona | Role | What they need |
|---|---|---|
| <key, one lowercase word> | <Name, role> | <What they need from the product, in their terms> |

### Success metrics

Targets are set on the opportunity brief. Each metric here is built only from calculated fields in section 3.

| Metric | Built from |
|---|---|
| <Metric name as the opportunity brief names it> | `<calculated_field>`, `<calculated_field>` |

## 2. Scope

**Pilot**
- <What the first release does, one line each>

**Next**
- <What comes after, one line each, with the reason it waits>

**Out of scope**
- <What neither release does>
- <What each headline number must not be used for, if anyone might use it that way>

## 3. Data product requirements

### DPR-1 · <Short name> · Must
**What:** <What the product does, testable, in plain language. No tools, no architecture.>
**For:** <persona key(s)>. <One line of reason, tracing to discovery evidence or a success metric. Longer reasons link to the opportunity brief.>

### DPR-2 · <Short name> · Should
**What:** <...>
**For:** <...>

### Key entities

<Entity> → <Entity> → <Entity> · dimensions: <dimension (values)>, <dimension>

<Two or three sentences on how the entities relate. The physical design is Engineering's.>

### Required fields

<DPR-n> is met when the product carries every field below, from the system named. This is the data contract Engineering sizes against.

| Entity | Field | Meaning | Source | Needed for |
|---|---|---|---|---|
| <Entity> | `<field_name>` | <Meaning> | <Source system, by its business name> | `<calculated_field>`, <DPR-n> |
| Parameter | `<parameter_name>` | <Value for the pilot, and why it is a parameter> | Configuration | `<calculated_field>` |

### Calculated fields

<DPR-n> is met when each field below is defined once, computed only from required fields, parameters and other calculated fields, and exposed by this name.

| Field | Definition | Inputs | Grain |
|---|---|---|---|
| `<calculated_field>` | <Formula or rule in plain language> | `<input>`, `<input>` | <Entity, daily | at close | weekly> |

### Worked example

<One concrete case with real-looking numbers, walked through the calculated fields from inputs to the flag or metric. Engineering and the backlog use it as the acceptance test.>

### Questions the metrics must answer

| Question from discovery | Answered with |
|---|---|
| <The question as users asked it> | `<calculated_field>` by <dimension> |

## 4. Non-functional requirements

| ID | Requirement | Priority |
|---|---|---|
| NFR-1 | **<Short name>.** <What must hold, without naming a mechanism.> | Must |

## 5. Release criteria

The pilot goes live when <evidence> meets the go-live criteria on the [opportunity brief](<link>). The requirement on this side is <DPR-n>: it must produce every number those criteria use.

## 6. Assumptions and dependencies

- <Something taken as true that, if false, changes the requirements. Say what breaks.>

## 7. Open questions

- **OQ-1 · <Topic>** (Engineering · <IDs it blocks>). <The question, and why the answer changes the work.>
- **OQ-2 · <Topic>** (Product · <IDs it blocks>). <The question.>
- **OQ-3 · <Topic>** (Product + Engineering · <IDs it blocks>). <The question.> *Resolved:* <what was decided, and what decided it.>
````

## Rules the format encodes

- **IDs.** `DPR-n`, `NFR-n` and `OQ-n`, numbered from 1 without gaps in a first draft. Once a PRD is shared, an ID is never reused or renumbered: new items take the next number, retired requirements stay with `· Retired in revision N` in the heading, and resolved questions stay with a *Resolved:* line. The backlog, issues and later revisions point at these IDs.
- **Priorities.** `Must`, `Should` or `Could`. Musts are what the pilot cannot ship without.
- **Field names.** `snake_case` in backticks, the same names in every table. Calculated fields use the name downstream systems will expose.
- **Inputs.** Every input of a calculated field is a required field, a parameter or another calculated field in this PRD. The checker fails the draft otherwise.
- **Parameters.** Any number that is a judgment, such as a threshold or a day count, is a parameter in the required-fields table, not a constant inside a definition, so it can change without rewriting the definition.
- **Open-question owners.** `Product` when it is about what the product does or whom it serves; `Engineering` when it is about how it is built; `Product + Engineering` when it needs both. The blocked IDs say which requirements wait on it.
- **Revisions.** From revision 2 on, a `## Revision <N>` block sits between the header paragraph and section 1. It lists every change, one line each, with the IDs it touches and what prompted it, and links to the archived previous revision.

```markdown
## Revision 2

Prompted by <the evidence: a prototype, feedback sessions, a refinement>. Previous revision: [revision 1](prd-v1.md).

- <What changed> (<IDs>). Prompted by <source>.
```

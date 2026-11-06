"""Check a PRD written in the opportunity-to-prd template.

Prints errors (must fix) and warnings (look at), then a one-line summary.
Exits 1 if there are errors.

Usage: python check_prd.py prd.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SECTIONS = [
    "Goal and users",
    "Scope",
    "Data product requirements",
    "Non-functional requirements",
    "Release criteria",
    "Assumptions and dependencies",
    "Open questions",
]
OWNERS = {"Product", "Engineering", "Product + Engineering"}
PRIORITIES = {"Must", "Should", "Could"}

# Words that belong to Engineering (how) or to planning (when). Checked outside "Out of scope".
HOW_WHEN = [
    r"batch", r"streaming", r"real-time", r"cron", r"pipeline", r"etl", r"elt", r"scheduler",
    r"airflow", r"dbt", r"spark", r"kafka", r"snowflake", r"bigquery", r"redshift", r"databricks",
    r"postgres(ql)?", r"mysql", r"s3", r"lambda", r"kubernetes", r"docker", r"microservice",
    r"tableau", r"looker", r"power ?bi", r"metabase", r"superset",
    r"sprints?", r"story points?", r"t-shirt", r"deadline", r"eta",
    r"q[1-4] ?20\d\d", r"(january|february|march|april|may|june|july|august|september|october|november|december) 20\d\d",
]
HOW_WHEN_RE = re.compile(r"\b(" + "|".join(HOW_WHEN) + r")\b", re.I)
TICKS = re.compile(r"`([a-z][a-z0-9_]*)`")
ID_RE = re.compile(r"\b(DPR|NFR|OQ)-(\d+)\b")

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def tables(lines: list[str], start: int, end: int) -> list[tuple[list[str], list[list[str]]]]:
    """Markdown tables between two line numbers, as (header, rows)."""
    out, i = [], start
    while i < end:
        if lines[i].lstrip().startswith("|") and i + 1 < end and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            header = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            rows, j = [], i + 2
            while j < end and lines[j].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            out.append((header, rows))
            i = j
        else:
            i += 1
    return out


def find_table(tbls, *cols):
    for header, rows in tbls:
        if [h.lower() for h in header[: len(cols)]] == [c.lower() for c in cols]:
            return header, rows
    return None


def check_sequence(kind: str, nums: list[int], first_draft: bool) -> None:
    seen = set()
    for n in nums:
        if n in seen:
            err(f"{kind}-{n} is used more than once.")
        seen.add(n)
    if nums:
        missing = sorted(set(range(1, max(nums) + 1)) - seen)
        if missing:
            msg = f"{kind} numbering has gaps: {', '.join(f'{kind}-{m}' for m in missing)}."
            warn(msg + (" A first draft shouldn't have gaps." if first_draft else " Expected only if those IDs were never used."))


def main() -> None:
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Header
    m = re.search(r"^Revision:\s*(\d+)", text, re.M)
    revision = int(m.group(1)) if m else None
    if revision is None:
        err("No `Revision: N` line in the header.")
    if not re.search(r"^Opportunity:\s*\S", text, re.M):
        err("No `Opportunity:` line linking the brief this PRD is written against.")

    # Sections
    found = [(i, int(mm.group(1)), mm.group(2).strip()) for i, l in enumerate(lines) if (mm := re.match(r"^## (\d+)\.\s+(.+?)\s*$", l))]
    pos = {}
    for idx, (i, n, title) in enumerate(found):
        if n - 1 < len(SECTIONS) and title == SECTIONS[n - 1]:
            pos[n] = i
        else:
            err(f"Line {i + 1}: section '## {n}. {title}' isn't in the template.")
    for n, title in enumerate(SECTIONS, 1):
        if n not in pos:
            err(f"Missing section '## {n}. {title}'.")
    order = [n for _, n, _ in found]
    if order != sorted(order):
        err("Sections are out of order.")
    bounds = {n: (pos[n], min([pos[k] for k in pos if k > n] + [len(lines)])) for n in pos}

    def span(n):
        return bounds.get(n, (0, 0))

    # Revision block
    rev_line = next((i for i, l in enumerate(lines) if re.match(r"^## Revision \d+", l)), None)
    if revision and revision > 1:
        if rev_line is None:
            err(f"Revision {revision}: add a '## Revision {revision}' block listing every change and what prompted it.")
        else:
            block = "\n".join(lines[rev_line: pos.get(1, len(lines))])
            if f"prd-v{revision - 1}" not in block and "revision 1" not in block.lower():
                warn(f"The revision block doesn't link to the archived revision {revision - 1}.")
            if not re.search(r"^- ", block, re.M):
                err("The revision block lists no changes.")

    # Section 1: users and success metrics
    s, e = span(1)
    t1 = tables(lines, s, e)
    users = find_table(t1, "Persona", "Role", "What they need")
    personas = set()
    if not users:
        err("Section 1 has no users table (Persona | Role | What they need).")
    else:
        personas = {r[0].strip("`*").lower() for r in users[1] if r and r[0]}
    metrics = find_table(t1, "Metric", "Built from")
    if not metrics:
        err("Section 1 has no success-metrics table (Metric | Built from).")

    # Section 3: requirements, fields
    s3, e3 = span(3)
    dprs, retired = [], set()
    dpr_heads = [(i, mm) for i in range(s3, e3) if (mm := re.match(r"^### DPR-(\d+) · (.+?) · (\w+)(?: · Retired in revision (\d+))?\s*$", lines[i]))]
    bad_heads = [i for i in range(s3, e3) if lines[i].startswith("### DPR") and not re.match(r"^### DPR-(\d+) · (.+?) · (\w+)", lines[i])]
    for i in bad_heads:
        err(f"Line {i + 1}: requirement heading should be '### DPR-n · Name · Must|Should|Could'.")
    heads_all = [i for i in range(s3, e3) if lines[i].startswith("###")] + [e3]
    for i, mm in dpr_heads:
        n, pri = int(mm.group(1)), mm.group(3)
        dprs.append(n)
        if mm.group(4):
            retired.add(n)
        if pri not in PRIORITIES:
            err(f"DPR-{n}: priority '{pri}' should be Must, Should or Could.")
        nxt = min(h for h in heads_all if h > i)
        body = lines[i + 1: nxt]
        what = [l for l in body if l.startswith("**What:**")]
        for_ = [l for l in body if l.startswith("**For:**")]
        if not mm.group(4):
            if not what:
                err(f"DPR-{n}: no '**What:**' line.")
            if not for_:
                err(f"DPR-{n}: no '**For:**' line tracing it to a persona and a reason.")
        if for_:
            reason = for_[0][len("**For:**"):].strip()
            who = reason.split(".")[0]
            keys = [k.strip().lower() for k in re.split(r",| and ", who) if k.strip()]
            for k in keys:
                if personas and k not in personas and k not in {"everyone", "all", "everyone downstream"}:
                    warn(f"DPR-{n}: '{k}' in the For line isn't a persona in the users table.")
            if len(reason.split()) > 40:
                warn(f"DPR-{n}: the For line is {len(reason.split())} words. One line of reason; link the brief for the rest.")
    check_sequence("DPR", dprs, revision == 1)
    live = len(set(dprs) - retired)
    if live and not 4 <= live <= 12:
        warn(f"{live} live DPRs. Usually 5 to 10: more than 12 suggests fields or criteria, fewer than 4 suggests they're too broad.")

    t3 = tables(lines, s3, e3)
    req = find_table(t3, "Entity", "Field", "Meaning", "Source", "Needed for")
    calc = find_table(t3, "Field", "Definition", "Inputs", "Grain")
    required, needed_for = {}, {}
    if not req:
        err("Section 3 has no required-fields table (Entity | Field | Meaning | Source | Needed for).")
    else:
        entity, seen_pairs = "", set()
        for r in req[1]:
            entity = r[0] or entity  # a blank entity cell continues the one above
            names = TICKS.findall(r[1]) if len(r) > 1 else []
            if not names:
                err(f"Required-fields row '{' | '.join(r)}' has no field name in backticks.")
            if len(r) > 3 and not r[3]:
                err(f"Required field {', '.join(names)} has no source.")
            for nm in names:
                if (entity, nm) in seen_pairs:
                    err(f"Required field `{nm}` is listed twice on {entity}.")
                seen_pairs.add((entity, nm))
                required[nm] = r
                needed_for[nm] = r[4] if len(r) > 4 else ""
    calculated, used = {}, set()
    if not calc:
        err("Section 3 has no calculated-fields table (Field | Definition | Inputs | Grain).")
    else:
        for r in calc[1]:
            for nm in TICKS.findall(r[0]):
                calculated[nm] = r
        for r in calc[1]:
            names = TICKS.findall(r[0])
            inputs = TICKS.findall(r[2]) if len(r) > 2 else []
            if not names:
                err(f"Calculated-fields row '{r[0]}' has no field name in backticks.")
            if not inputs:
                err(f"Calculated field {', '.join(names) or r[0]} lists no inputs in backticks.")
            for x in inputs:
                used.add(x)
                if x not in required and x not in calculated:
                    err(f"Calculated field `{names[0] if names else r[0]}` uses `{x}`, which isn't a required field, parameter or calculated field.")
    for nm in required:
        if nm not in used and not ID_RE.search(needed_for.get(nm, "")):
            warn(f"Required field `{nm}` isn't an input to any calculated field and its 'Needed for' cites no requirement.")
    if metrics:
        for r in metrics[1]:
            names = TICKS.findall(r[1]) if len(r) > 1 else []
            if not names:
                err(f"Success metric '{r[0]}' isn't built from any calculated field.")
            for x in names:
                if x not in calculated:
                    err(f"Success metric '{r[0]}' is built from `{x}`, which isn't a calculated field.")
    if not any(re.match(r"^### Worked example", lines[i]) for i in range(s3, e3)):
        warn("No '### Worked example' in section 3. The backlog uses it as the acceptance test.")

    # Section 4: NFRs
    s4, e4 = span(4)
    nfrs = []
    nfr_t = find_table(tables(lines, s4, e4), "ID", "Requirement", "Priority")
    if not nfr_t:
        err("Section 4 has no NFR table (ID | Requirement | Priority).")
    else:
        for r in nfr_t[1]:
            mm = re.match(r"^NFR-(\d+)$", r[0])
            if not mm:
                err(f"NFR row '{r[0]}' should have an ID like NFR-1.")
                continue
            nfrs.append(int(mm.group(1)))
            if len(r) < 3 or r[2] not in PRIORITIES:
                err(f"{r[0]}: priority should be Must, Should or Could.")
    check_sequence("NFR", nfrs, revision == 1)

    # Section 5
    s5, e5 = span(5)
    if not ID_RE.search("\n".join(lines[s5:e5])):
        warn("Release criteria name no requirement that produces the go-live numbers.")

    # Section 7: open questions
    s7, e7 = span(7)
    oqs = []
    for i in range(s7, e7):
        l = lines[i]
        if not l.startswith("- **OQ-"):
            continue
        mm = re.match(r"^- \*\*OQ-(\d+) · (.+?)\*\* \((.+?)\)", l)
        if not mm:
            err(f"Line {i + 1}: open question should read '- **OQ-n · Topic** (Owner · IDs it blocks). Question.'")
            continue
        oqs.append(int(mm.group(1)))
        parts = [p.strip() for p in mm.group(3).split("·")]
        if parts[0] not in OWNERS:
            err(f"OQ-{mm.group(1)}: owner '{parts[0]}' should be Product, Engineering or Product + Engineering.")
        if len(parts) < 2 or not ID_RE.search(parts[1]):
            warn(f"OQ-{mm.group(1)}: doesn't say which requirements it blocks.")
    check_sequence("OQ", oqs, revision == 1)

    # Dangling references
    defined = {("DPR", n) for n in dprs} | {("NFR", n) for n in nfrs} | {("OQ", n) for n in oqs}
    for i, l in enumerate(lines):
        for kind, n in ID_RE.findall(l):
            if (kind, int(n)) not in defined:
                err(f"Line {i + 1}: refers to {kind}-{n}, which isn't defined in this PRD.")

    # How / when words, outside the Out of scope list
    s2, e2 = span(2)
    oos = next((i for i in range(s2, e2) if lines[i].strip().lower().startswith("**out of scope")), None)
    skip = set(range(oos, e2)) if oos is not None else set()
    in_code = False
    for i, l in enumerate(lines):
        if l.strip().startswith("```"):
            in_code = not in_code
        if in_code or i in skip:
            continue
        for w in sorted({x.group(0) for x in HOW_WHEN_RE.finditer(l)}):
            warn(f"Line {i + 1}: '{w}' names a how or a when. Leave mechanisms, tools and dates to Engineering.")

    for e_ in errors:
        print(f"ERROR    {e_}")
    for w_ in warnings:
        print(f"WARNING  {w_}")
    musts = sum(1 for i, mm in dpr_heads if mm.group(3) == "Must" and not mm.group(4))
    print(f"{path.name}: revision {revision}, {live} DPRs ({musts} must), {len(nfrs)} NFRs, {len(oqs)} open questions, "
          f"{len(required)} required and {len(calculated)} calculated fields · {len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

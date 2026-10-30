#!/usr/bin/env python3
"""Check a backlog.yaml against the prd-to-backlog rules.

Usage: check_backlog.py backlog.yaml [--draft]

--draft applies the Draft-mode limits (2-3 stories per epic). Without it,
stories added in refinement are allowed. Exits 1 if there are errors.
"""
import re
import sys

import yaml

ESTIMATE_FIELDS = {"points", "story_points", "estimate", "size", "effort", "hours", "days"}
ESTIMATE_WORDS = re.compile(r"\b(story points?|\d+\s*(points?|pts|hours?|hrs|person-days?|days of (work|effort))|t-shirt)\b", re.I)
EPIC_KEY = re.compile(r"^E\d+$")
STORY_KEY = re.compile(r"^(E\d+)-S\d+$")
REQUIRED_EPIC = ["key", "title", "outcome", "traces", "stories"]
REQUIRED_STORY = ["key", "title", "as", "so_that", "traces", "acceptance"]


def main(path, draft):
    try:
        d = yaml.safe_load(open(path))
    except yaml.YAMLError as ex:
        print(f"ERROR   {path} isn't valid YAML: {ex}".splitlines()[0])
        print("        Quote values that contain a comma or a colon, especially inside {...}.")
        return 1
    errors, warnings = [], []
    err, warn = errors.append, warnings.append

    reqs = d.get("requirements") or {}
    personas = d.get("personas") or {}
    oqs = d.get("open_questions") or {}
    epics = d.get("epics") or []
    if not reqs:
        err("No `requirements` section: list every requirement ID in the PRD with its priority.")
    if not epics:
        err("No epics.")

    def find_estimates(obj, where):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if str(k).lower() in ESTIMATE_FIELDS and v not in (None, "", []):
                    err(f"{where}: estimate field `{k}`. Estimates are Engineering's; remove it.")
                find_estimates(v, where)
        elif isinstance(obj, list):
            for v in obj:
                find_estimates(v, where)

    seen, covered = set(), set()
    if epics and not 4 <= len(epics) <= 7:
        warn(f"{len(epics)} epics. Usually 4-7: more means stories or risks promoted to epics, fewer means epics too broad to sign off on.")

    for e in epics:
        ek = e.get("key", "?")
        for f in REQUIRED_EPIC:
            if not e.get(f):
                err(f"{ek}: missing `{f}`.")
        if not EPIC_KEY.match(str(ek)):
            err(f"{ek}: epic key should look like E1.")
        if ek in seen:
            err(f"{ek}: duplicate key.")
        seen.add(ek)
        for t in e.get("traces") or []:
            if reqs and t not in reqs:
                err(f"{ek}: traces {t}, which isn't in `requirements`.")
        stories = e.get("stories") or []
        added = [s for s in stories if s.get("added_in_refinement")]
        n = len(stories) if draft else len(stories) - len(added)
        if stories and not 2 <= n <= 3:
            warn(f"{ek}: {n} stories{' before refinement' if not draft else ''}. Draft writes 2-3 functional stories per epic.")

        for s in stories:
            sk = s.get("key", "?")
            where = f"{sk}"
            for f in REQUIRED_STORY:
                if not s.get(f):
                    err(f"{where}: missing `{f}`.")
            m = STORY_KEY.match(str(sk))
            if not m:
                err(f"{where}: story key should look like E1-S1.")
            elif m.group(1) != ek:
                err(f"{where}: key doesn't match its epic {ek}.")
            if sk in seen:
                err(f"{where}: duplicate key.")
            seen.add(sk)
            for t in s.get("traces") or []:
                covered.add(t)
                if reqs and t not in reqs:
                    err(f"{where}: traces {t}, which isn't in `requirements`.")
            who = s.get("as")
            for p in (who if isinstance(who, list) else [who]):
                if p and personas and p not in personas:
                    warn(f"{where}: persona `{p}` isn't in `personas`.")
            ac = s.get("acceptance") or []
            if ac and not 2 <= len(ac) <= 4:
                warn(f"{where}: {len(ac)} acceptance criteria. 2-4 outcomes is usual.")
            for a in ac:
                if ESTIMATE_WORDS.search(str(a)):
                    warn(f"{where}: acceptance criterion reads like an estimate: \"{a[:70]}\"")
            for q in (s.get("open_questions") or []) + (s.get("decisions") or []):
                if q not in oqs:
                    err(f"{where}: refers to {q}, which isn't in `open_questions`.")
            for q in s.get("decisions") or []:
                if q in oqs and not oqs[q].get("decision"):
                    err(f"{where}: lists {q} as a decision, but it has no `decision`.")
            for dep in s.get("depends_on") or []:
                if not STORY_KEY.match(str(dep)):
                    err(f"{where}: depends_on {dep} isn't a story key.")
            find_estimates({k: v for k, v in s.items() if k != "tasks"}, where)
        find_estimates({k: v for k, v in e.items() if k != "stories"}, ek)

    for q, v in oqs.items():
        if not (v or {}).get("by"):
            warn(f"{q}: no owner. Mark `by: product` or `by: engineering`.")

    for r, pri in reqs.items():
        if r not in covered:
            (err if str(pri).lower() == "must" else warn)(f"{r} ({pri}) has no story.")

    for k in d.get("sprints") or {}:
        pass  # Engineering's plan: recorded as given, not checked

    stories = sum(len(e.get("stories") or []) for e in epics)
    musts = [r for r, p in reqs.items() if str(p).lower() == "must"]
    print(f"{len(epics)} epics, {stories} stories, {len([r for r in musts if r in covered])} of {len(musts)} must-haves covered")
    for e in errors:
        print("ERROR  ", e)
    for w in warnings:
        print("warning", w)
    if not errors:
        print("OK" + (f", {len(warnings)} warning(s) to look at" if warnings else ""))
    return 1 if errors else 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        sys.exit(__doc__)
    sys.exit(main(args[0], "--draft" in sys.argv))

#!/usr/bin/env python3
"""Sync backlog.yaml to GitHub Issues.

Usage:
  sync_issues.py backlog.yaml --repo OWNER/REPO [--dry-run] [--update] [--write-back]

Creates labels, one milestone per release (if the file has `releases`), one
issue per epic and per story, and attaches stories to their epic as
sub-issues. Safe to re-run: issues are matched by the key at the start of
their title (E1, E1-S2) and left alone unless --update is passed, which
rewrites their title, body and milestone from the file. --write-back records
issue numbers in the file. Uses the GitHub REST API through `gh api`.
"""
import argparse
import json
import re
import subprocess
import sys

import yaml

LABELS = {
    "epic": ("5319E7", "An outcome someone can sign off on"),
    "story": ("0E6F73", "A functional user story"),
    "critical-path": ("B8412B", "Depends on another team or a missing input"),
    "gate": ("B8412B", "Ends in a go/no-go decision"),
    "now": ("0E6F73", "Roadmap: now"),
    "next": ("566170", "Roadmap: next"),
    "later": ("D6DCE4", "Roadmap: later"),
}


class GitHub:
    def __init__(self, repo, dry):
        self.repo, self.dry, self.fake = repo, dry, 0

    def call(self, method, path, body=None):
        if self.dry and method != "GET":
            self.fake += 1
            return {"number": f"new{self.fake}", "id": 0}
        cmd = ["gh", "api", "-X", method, f"repos/{self.repo}/{path}"]
        if body is not None:
            cmd += ["--input", "-"]
        r = subprocess.run(cmd, input=json.dumps(body) if body is not None else None,
                           capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"GitHub {method} {path} failed: {r.stdout}{r.stderr}")
        return json.loads(r.stdout) if r.stdout.strip() else {}

    def all(self, path):
        out, page = [], 1
        while True:
            batch = self.call("GET", f"{path}{'&' if '?' in path else '?'}per_page=100&page={page}")
            out += batch
            if len(batch) < 100:
                return out
            page += 1


def as_list(x):
    return x if isinstance(x, list) else [x] if x else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("backlog")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--write-back", action="store_true")
    a = ap.parse_args()

    d = yaml.safe_load(open(a.backlog))
    gh = GitHub(a.repo, a.dry_run)
    personas = d.get("personas") or {}
    oqs = d.get("open_questions") or {}
    prd = d.get("prd")
    anchors = d.get("trace_anchors") or {}          # e.g. {NFR: nfr} when IDs share one anchor
    page = d.get("page")
    source = f"source: `{a.backlog}`"
    log = []

    def note(verb, what):
        log.append(f"{'would ' if a.dry_run else ''}{verb:8} {what}")

    def link(t):
        if not prd:
            return t
        prefix = t.split("-")[0]
        return f"[{t}]({prd}#{anchors.get(prefix, t.lower())})"

    def who(p):
        return ", ".join(personas.get(x, x) for x in as_list(p))

    footer_bits = [f"[Backlog page]({page})" if page else None, source]
    footer = " · ".join(b for b in footer_bits if b)

    # Labels
    have = {l["name"] for l in gh.all("labels")}
    used = {"epic", "story"}
    for e in d["epics"]:
        used |= {m for m in as_list(e.get("milestone")) if m in LABELS}
        if e.get("gate"):
            used.add("gate")
        if any(s.get("critical_path") for s in e["stories"]):
            used.add("critical-path")
    for name in sorted(used - have):
        color, desc = LABELS[name]
        gh.call("POST", "labels", {"name": name, "color": color, "description": desc})
        note("create", f"label {name}")

    # Milestones, one per release. Stories go to the first release that lists
    # them, unless the story names its own `release`.
    releases = d.get("releases") or {}
    ms_by_title = {m["title"]: m["number"] for m in gh.all("milestones?state=all")}
    ms_by_key = {re.split(r"\s*[·:-]\s*|\s+", m, maxsplit=1)[0]: n for m, n in ms_by_title.items()}
    milestone = {}
    for rk, r in releases.items():
        title = f"{rk} · {r['name']}"
        desc = " ".join(x for x in [f"Week {r['week']}." if r.get("week") else "", r.get("who_gets_what", ""),
                                    f"Success: {r['success']}" if r.get("success") else ""] if x)[:250]
        if rk in ms_by_key:
            milestone[rk] = ms_by_key[rk]
        else:
            milestone[rk] = gh.call("POST", "milestones", {"title": title, "description": desc})["number"]
            note("create", f"milestone {title}")
    release_of = {}
    for rk, r in releases.items():
        for s in r.get("stories") or []:
            release_of.setdefault(s, rk)

    sprint_of = {}
    for n, sp in (d.get("sprints") or {}).items():
        for s in sp.get("stories") or []:
            sprint_of.setdefault(s, n)

    existing = {}
    for i in gh.all("issues?state=all"):
        if "pull_request" not in i:
            existing.setdefault(re.split(r"\s*[·:]\s*|\s+", i["title"], maxsplit=1)[0], i)

    numbers = {}

    def upsert(key, title, body, labels, ms):
        full = f"{key} · {title}"
        if key in existing:
            i = existing[key]
            if a.update:
                patch = {"title": full, "body": body}
                if ms is not None:
                    patch["milestone"] = ms
                gh.call("PATCH", f"issues/{i['number']}", patch)
                note("update", f"#{i['number']} {full}")
            else:
                note("keep", f"#{i['number']} {full}")
        else:
            payload = {"title": full, "body": body, "labels": labels}
            if ms is not None:
                payload["milestone"] = ms
            i = gh.call("POST", "issues", payload)
            note("create", f"#{i['number']} {full}")
        numbers[key] = i["number"]
        return i

    for e in d["epics"]:
        horizons = [m for m in as_list(e.get("milestone")) if m in LABELS]
        body = [f"**Outcome:** {e['outcome']}", "", f"**Traces:** {', '.join(link(t) for t in e['traces'])}"]
        if horizons:
            body.append(f"**Roadmap:** {' → '.join(horizons)}")
        if e.get("gate") and e["gate"] in (d.get("gates") or {}):
            body.append(f"**Gate:** {d['gates'][e['gate']]['rule']}")
        body += ["", f"Stories are attached as sub-issues. {footer}"]
        labels = ["epic"] + horizons[:1] + (["gate"] if e.get("gate") else [])
        ep = upsert(e["key"], e["title"], "\n".join(body), labels, None)

        children = []
        for s in e["stories"]:
            b = [f"**As** {who(s['as'])}, **so that** {s['so_that']}.", "", "### Acceptance criteria",
                 *[f"- [ ] {x}" for x in s["acceptance"]], "",
                 f"**Traces:** {', '.join(link(t) for t in s['traces'])}"]
            if s.get("critical_path"):
                b.append(f"**Critical path:** {s['critical_path']}")
            for q in s.get("decisions") or []:
                by = ", ".join(as_list(oqs[q].get("by")))
                b.append(f"**{q}, decided{f' by {by}' if by else ''}:** {oqs[q]['decision']}")
            for q in s.get("open_questions") or []:
                b.append(f"**{q}, open:** {oqs[q]['question']}")
            if s.get("depends_on"):
                b.append(f"**Depends on:** {', '.join(s['depends_on'])}")
            refinement = s.get("changed_in_refinement") or s.get("added_in_refinement")
            if refinement:
                b.append(f"**Refinement:** {refinement}")
            if s.get("tasks"):
                b += ["", "### Technical tasks (Engineering)",
                      *[f"- [ ] **{t['key']}** {t['task']} _({t['owner']})_" for t in s["tasks"]]]
            plan = f"Sprint {sprint_of[s['key']]}" if s["key"] in sprint_of else "Not yet planned"
            b += ["", f"_{plan} · epic {e['key']} · {footer}_"]
            labels = ["story"] + horizons[:1] + (["critical-path"] if s.get("critical_path") else [])
            rk = s.get("release") or release_of.get(s["key"])
            children.append(upsert(s["key"], s["title"], "\n".join(b), labels, milestone.get(rk)))

        attached = set() if isinstance(ep["number"], str) else \
            {x["id"] for x in gh.all(f"issues/{ep['number']}/sub_issues")}
        for c in children:
            if not c.get("id") or c["id"] not in attached:
                if not a.dry_run:
                    gh.call("POST", f"issues/{ep['number']}/sub_issues", {"sub_issue_id": c["id"]})
                note("attach", f"#{c['number']} to #{ep['number']}")

    print("\n".join(log))

    if a.write_back and not a.dry_run:
        text = open(a.backlog).read()
        for key, n in numbers.items():
            m = re.search(rf"^([ \t]*)- key: {re.escape(key)}[ \t]*\n((?:\1  issue: \d+[ \t]*\n)?)", text, re.M)
            if not m:
                continue
            line = f"{m.group(1)}  issue: {n}\n"
            text = text[:m.start(2)] + line + text[m.end(2):]
        open(a.backlog, "w").write(text)
        print(f"wrote {len(numbers)} issue numbers to {a.backlog}")


if __name__ == "__main__":
    main()

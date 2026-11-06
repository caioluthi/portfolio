#!/usr/bin/env python3
"""Check an interview-notes file against its transcript.

Checks:
  1. Every quote is an exact excerpt of the interviewee's speech (not the interviewer's).
  2. All required sections exist.
  3. Items carry the required tags and quotes; signals are capped at three.

Usage:
    python verify_quotes.py transcript.txt notes.md
    python verify_quotes.py transcript.txt notes.md --interviewer-regex "^(interviewer|host)$"

Transcript format: turns start with a speaker label, e.g. "Interviewer: ..." or
"Ops manager: ...". Lines starting with "#" are ignored.

Matching rules: whitespace, curly quotes and dashes are normalized on both sides.
Leading/trailing punctuation on a fragment is ignored. "..." or an ellipsis splits a
quote into fragments that are checked separately. "[redacted: ...]" matches any short
span of text. Exit code is 0 when everything passes and 1 otherwise.
"""
import argparse
import re
import sys

REQUIRED_SECTIONS = [
    "Pain points",
    "Upsides of the current process",
    "Their view of the optimal solution",
    "Nice-to-haves",
    "Critical needs",
    "Numbers mentioned",
    "Context and background",
    "Signals worth exploring",
    "Privacy flags",
]

# section -> tag groups; each group needs at least one alternative present in every item
ITEM_TAGS = {
    "Pain points": [("volunteered", "prompted"), ("experience", "speculation")],
    "Upsides of the current process": [("volunteered", "prompted"), ("experience", "speculation")],
    "Their view of the optimal solution": [("volunteered", "prompted")],
    "Nice-to-haves": [("stated", "inferred"), ("volunteered", "prompted")],
    "Critical needs": [("stated", "inferred"), ("volunteered", "prompted")],
}

TURN = re.compile(r"^([A-Za-z][^:\n]{0,40}):\s*(.*)$")


def norm(s):
    s = s.replace("\u2018", "'").replace("\u2019", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2014", "-").replace("\u2013", "-").replace("\u2026", "...")
    return re.sub(r"\s+", " ", s).strip()


def parse_turns(text):
    turns, cur = [], None
    for line in text.splitlines():
        if line.startswith("#"):
            continue
        m = TURN.match(line)
        if m:
            cur = [m.group(1).strip(), m.group(2).strip()]
            turns.append(cur)
        elif cur is not None and line.strip():
            cur[1] += " " + line.strip()
    return [(label, norm(body)) for label, body in turns]


def extract_quotes(notes):
    quotes = []
    for i, line in enumerate(notes.splitlines(), 1):
        s = line.strip()
        if s.startswith(">"):
            body = s.lstrip(">").strip()
            if len(body) >= 2 and body[0] in "\"\u201c" and body[-1] in "\"\u201d":
                body = body[1:-1]
            quotes.append((i, body))
        elif s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            last = cells[-1] if cells else ""
            for m in re.finditer(r'["\u201c](.+?)["\u201d]', last):
                quotes.append((i, m.group(1)))
    return quotes


def fragments(quote):
    q = norm(quote)
    out = []
    for part in re.split(r"\.\.\.", q):
        part = part.strip(" .,;:!?\"")
        if part:
            out.append(part)
    return out


def to_regex(fragment):
    parts = re.split(r"\[redacted[^\]]*\]", fragment)
    return re.compile(".{1,60}?".join(re.escape(p.strip()) for p in parts))


def split_sections(notes):
    """Return {heading text: (line_number, body_lines)} for every markdown heading."""
    sections, heads = {}, []
    lines = notes.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            heads.append((i, m.group(2).strip()))
    for idx, (i, title) in enumerate(heads):
        end = heads[idx + 1][0] if idx + 1 < len(heads) else len(lines)
        sections[title] = (i + 1, lines[i + 1:end])
    return sections


def find_section(sections, name):
    for title, val in sections.items():
        if name.lower() in title.lower():
            return val
    return None


def bullet_blocks(body, pattern):
    blocks, cur = [], None
    for line in body:
        if re.match(pattern, line):
            cur = [line]
            blocks.append(cur)
        elif cur is not None:
            cur.append(line)
    return ["\n".join(b) for b in blocks]


def check_quotes(transcript, notes, interviewer_regex):
    problems = []
    turns = parse_turns(transcript)
    is_interviewer = re.compile(interviewer_regex, re.I)
    interviewee = [b for l, b in turns if not is_interviewer.match(l)]
    interviewer = [b for l, b in turns if is_interviewer.match(l)]
    if not interviewee:
        problems.append("No interviewee turns found in the transcript (check speaker labels).")
        return problems, 0
    quotes = extract_quotes(notes)
    for line_no, quote in quotes:
        for frag in fragments(quote):
            rx = to_regex(frag)
            if any(rx.search(t) for t in interviewee):
                continue
            if any(rx.search(t) for t in interviewer):
                problems.append(f"line {line_no}: quote comes from the interviewer, not the interviewee: \"{frag[:90]}\"")
            else:
                problems.append(f"line {line_no}: quote not found verbatim in the transcript: \"{frag[:90]}\"")
    return problems, len(quotes)


def check_structure(notes):
    problems = []
    if "notes-format: v1" not in notes:
        problems.append("Missing the '<!-- notes-format: v1 -->' marker.")
    sections = split_sections(notes)
    for name in REQUIRED_SECTIONS:
        if find_section(sections, name) is None:
            problems.append(f"Missing section: {name}")

    for name, tag_groups in ITEM_TAGS.items():
        sec = find_section(sections, name)
        if sec is None:
            continue
        line_no, body = sec
        text = "\n".join(body)
        bullets = bullet_blocks(body, r"^- ")
        if "Not discussed" in text:
            if bullets:
                problems.append(f"{name}: says 'Not discussed' but also lists items.")
            continue
        if not bullets:
            problems.append(f"{name}: no items and no 'Not discussed' (line {line_no}).")
        for block in bullets:
            head = block.splitlines()[0][:60]
            if not any(l.strip().startswith(">") for l in block.splitlines()):
                problems.append(f"{name}: item without a quote: {head}")
            for group in tag_groups:
                if not any(re.search(rf"\b{t}\b", block, re.I) for t in group):
                    problems.append(f"{name}: item missing a '{'/'.join(group)}' tag: {head}")

    sig = find_section(sections, "Signals worth exploring")
    if sig is not None:
        text = "\n".join(sig[1])
        if "None noticed" not in text:
            blocks = bullet_blocks(sig[1], r"^\d+\.")
            if len(blocks) > 3:
                problems.append(f"Signals worth exploring: {len(blocks)} signals; the maximum is 3.")
            for block in blocks:
                head = block.splitlines()[0][:60]
                if not any(l.strip().startswith(">") for l in block.splitlines()):
                    problems.append(f"Signals: signal without a quote: {head}")
                if "follow-up" not in block.lower():
                    problems.append(f"Signals: signal without a follow-up question: {head}")

    ctx = find_section(sections, "Context and background")
    if ctx is not None:
        text = "\n".join(ctx[1])
        for block in bullet_blocks(ctx[1], r"^- "):
            if re.search(r"\binferred\b", block, re.I) and not any(
                l.strip().startswith(">") for l in block.splitlines()
            ):
                problems.append(f"Context: inferred value without a quote: {block.splitlines()[0][:60]}")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript")
    ap.add_argument("notes")
    ap.add_argument("--interviewer-regex", default=r"^(interviewer|moderator|researcher|facilitator)\b",
                    help="regex matching interviewer speaker labels (case-insensitive)")
    args = ap.parse_args()

    transcript = open(args.transcript, encoding="utf-8").read()
    notes = open(args.notes, encoding="utf-8").read()

    quote_problems, n_quotes = check_quotes(transcript, notes, args.interviewer_regex)
    structure_problems = check_structure(notes)
    problems = quote_problems + structure_problems

    print(f"Checked {n_quotes} quotes against the interviewee's speech.")
    if problems:
        print(f"FAIL: {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print("PASS: all quotes verbatim, all required sections and tags present.")


if __name__ == "__main__":
    main()

# Skills

Claude skills written while building this case study. Each one packages a step of the product workflow so it runs the same way every time, with the judgment calls written down as rules.

| Skill | What it does | Used in |
|---|---|---|
| [interview-notes](interview-notes/SKILL.md) | Turns one interview transcript into structured notes where every item is backed by a verbatim quote, and what was said is kept separate from what is read into it | [Phase 1](https://caioluthi.github.io/portfolio/phase-1-discovery.html), [worked example](interview-notes/examples/second-avenue/notes/finance-manager.notes.md) |
| [opportunity-to-prd](opportunity-to-prd/SKILL.md) | Turns an opportunity brief into a PRD with numbered requirements and the fields behind every metric, always in the same structure, and revises it when a prototype or feedback brings new evidence | [Phase 3](https://caioluthi.github.io/portfolio/phase-3-prd.html), [worked example](opportunity-to-prd/examples/second-avenue/README.md) |
| [prd-to-backlog](prd-to-backlog/SKILL.md) | Turns a PRD into a Product-owned backlog of outcome epics and functional stories, records what Engineering decides in refinement, and syncs the backlog to GitHub Issues | [Phase 5](https://caioluthi.github.io/portfolio/phase-5-backlog-roadmap.html), [backlog](../backlog/backlog.yaml), [issues](https://github.com/caioluthi/portfolio/issues) |

## Using a skill

Copy the skill's folder into your skills directory (for Claude Code, `~/.claude/skills/`), or upload it in Claude's settings. The `opportunity-to-prd` checker needs only Python 3. The `prd-to-backlog` scripts need Python 3 with PyYAML, and `sync_issues.py` needs the GitHub CLI (`gh`) signed in to an account that can write to the repository. The `interview-notes` verifier needs only Python 3.

```
python skills/opportunity-to-prd/scripts/check_prd.py skills/opportunity-to-prd/examples/second-avenue/prd.md
python skills/prd-to-backlog/scripts/check_backlog.py backlog/backlog.yaml
python skills/prd-to-backlog/scripts/sync_issues.py backlog/backlog.yaml --repo OWNER/REPO --dry-run
python skills/interview-notes/scripts/verify_quotes.py \
  skills/interview-notes/examples/second-avenue/transcripts/finance-manager.txt \
  skills/interview-notes/examples/second-avenue/notes/finance-manager.notes.md
```

## interview-notes: how it works and where it stops

The design principle is that what the interviewee said stays visibly separate from what is read into it.

- **What they said:** pain points, upsides of the current process, their own view of the ideal solution, nice-to-haves, critical needs and numbers. Every item has a verbatim quote and is tagged volunteered or prompted, and experience or speculation.
- **What we read into it:** context, inferred values and up to three signals worth exploring. Each is tagged as inference and tied to a quote, and none proposes a solution.
- **Rules that protect the evidence:** the interviewer's words are never evidence, hedges and contradictions are kept, one interview never supports a frequency claim, and a section the transcript doesn't cover says "Not discussed".
- **Privacy:** role labels instead of names, personal data redacted inside quotes, and a privacy-flags line at the end.
- **A check you can run:** `verify_quotes.py` confirms every quote is an exact excerpt of the interviewee's speech and that the required sections and tags are present.

What it does not do: it doesn't replace talking to users, combine interviews or count themes across them, recommend solutions, or prioritize anything. The verifier catches altered quotes and missing tags, not a misreading of what someone meant, so a person reviews every output. If you adapt it to real research, run only transcripts that participants agreed to share with an AI tool, in line with your organization's policy.

## opportunity-to-prd: how it works and where it stops

The design principle is that the opportunity brief owns the why, the PRD owns the what, and Engineering owns the how and the when.

- **Same structure every time:** seven sections, numbered requirements (`DPR-n`, `NFR-n`) with priorities, and open questions (`OQ-n`) with an owner and the requirements they block. `prd-to-backlog` reads this structure directly.
- **Metrics are requirements:** every success metric on the brief is built from calculated fields, and every calculated field from required fields with a named source system. Writing that chain out is where the gaps show up, and gaps become open questions instead of guesses.
- **Judgments are parameters:** thresholds and day counts sit in configuration, so a prototype can change them without rewriting a definition.
- **Revisions keep history:** IDs are never renumbered, the previous revision is archived unchanged, and every change is listed with the evidence that prompted it. A target that moves is changed on the brief, with its cost stated, not quietly in the PRD.
- **A check you can run:** `check_prd.py` fails a PRD with missing sections, broken IDs, a calculated field whose inputs aren't defined, or a metric with no fields behind it, and warns on tool names, mechanisms and dates.

What it does not do: it doesn't size the opportunity or set targets (that is the brief), choose architecture or estimate (that is Engineering), or decide which evidence to act on. In Revise mode it proposes, and the PM decides each change.


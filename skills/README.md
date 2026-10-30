# Skills

Claude skills written while building this case study. Each one packages a step of the product workflow so it runs the same way every time, with the judgment calls written down as rules.

| Skill | What it does | Used in |
|---|---|---|
| [prd-to-backlog](prd-to-backlog/SKILL.md) | Turns a PRD into a Product-owned backlog of outcome epics and functional stories, records what Engineering decides in refinement, and syncs the backlog to GitHub Issues | [Phase 5](https://caioluthi.github.io/portfolio/phase-5-backlog-roadmap.html), [backlog](../backlog/backlog.yaml), [issues](https://github.com/caioluthi/portfolio/issues) |

## Using a skill

Copy the skill's folder into your skills directory (for Claude Code, `~/.claude/skills/`), or upload it in Claude's settings. The scripts need Python 3 with PyYAML, and `sync_issues.py` needs the GitHub CLI (`gh`) signed in to an account that can write to the repository.

```
python skills/prd-to-backlog/scripts/check_backlog.py backlog/backlog.yaml
python skills/prd-to-backlog/scripts/sync_issues.py backlog/backlog.yaml --repo OWNER/REPO --dry-run
```

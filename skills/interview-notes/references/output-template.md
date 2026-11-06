# Output template (notes-format v1)

Use this structure exactly. The headings and tags are a contract: the quote verifier and the downstream skills (jobs-to-be-done mapper, persona synthesizer) read them.

```markdown
# Interview notes: {Role}, {date or "date not provided"}
<!-- notes-format: v1 -->

**Research goal:** {as provided, or "not provided"}
**Coverage:** whole transcript read; {N} interviewee turns; low-confidence passages: {none | list}

## What they said

### Pain points
- **{short statement}** ({volunteered | prompted} · {experience | speculation})
  > "{verbatim quote}"

### Upsides of the current process
- **{short statement}** ({volunteered | prompted} · {experience | speculation})
  > "{verbatim quote}"

### Their view of the optimal solution
- **{what they describe wanting}** ({volunteered | prompted})
  > "{verbatim quote}"

### Nice-to-haves
- **{item}** — *{stated | inferred}* ({volunteered | prompted})
  > "{verbatim quote}"

### Critical needs
- **{item}** — *{stated | inferred}* ({volunteered | prompted})
  > "{verbatim quote}"

### Numbers mentioned
| Figure | Period / unit | Basis (measured · estimated · hearsay) | Quote |
|---|---|---|---|
| {figure} | {period or unit} | {basis} | "{verbatim quote}" |

### Tensions within this interview
{Include this section only if the interviewee said incompatible things. List both statements with quotes. Omit the section entirely if there are none.}

## What we read into it

### Context and background
**Stated**
- {role, responsibilities, tools or workflow, as they described it}
  > "{verbatim quote}"

**Inferred values (job-relevant only)**
- {value} — *inferred*
  > "{the quote this rests on}"

### Signals worth exploring
1. **{what stood out}**; *why it stood out:* {observable reason}
   > "{verbatim quote}"
   *Follow-up question:* {neutral, open question}

## Privacy flags
{none | what was redacted or tagged sensitive}
```

## Rules for filling it in

- Any section without coverage contains only the words `Not discussed`. Do not put an empty bullet or a guess in it.
- "Numbers mentioned" with no figures contains only `Not discussed`.
- "Signals worth exploring" with nothing to report contains only `None noticed`. There are at most three, ranked.
- Keep each quote to one to three sentences. Use `...` or an ellipsis character to skip text, and `[redacted: type]` to remove personal data. Never change the words.
- Use role labels for people. Do not add names or employers.

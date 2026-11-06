---
name: interview-notes
description: Turn a single user-research or discovery interview transcript into structured, evidence-backed notes covering pain points, what works today, the interviewee's own view of an ideal solution, nice-to-haves, critical needs, numbers mentioned, context and values, and signals worth exploring, with every item tied to a verbatim quote. Use this whenever the user pastes or uploads an interview transcript, call notes, or a discovery conversation and asks for notes, a summary, takeaways, pain points, or "what did they say", even if they never say "interview notes". Do not use it for survey data, for combining several interviews (that is cross-interview synthesis), or for writing personas, jobs-to-be-done or journey maps.
---

# Interview notes

Turn one interview transcript into structured notes in which every claim traces back to something the interviewee actually said.

## Why this skill is strict

Later steps (jobs-to-be-done mapping, persona synthesis, requirements) quote these notes as evidence. A pain point the interviewee never described, or a quote that was tidied up, does not stay a small error: it becomes a persona trait or a requirement. So this skill puts fidelity first and insight second, and it keeps what was said visibly separate from what is read into it.

## Workflow

1. **Read the whole transcript before writing anything.** Long transcripts are where the middle quietly gets skipped.
2. **Settle the basics** (see below): who is speaking, the interviewee's role, the research goal.
3. **Write "What they said"** using only the interviewee's words and the evidence rules below.
4. **Write "What we read into it"** using the interpretation rules below.
5. **Do the privacy pass.**
6. **Run the self-check.** If you can run code, also run the quote verifier (see the end).

Read `references/output-template.md` before writing. It defines the exact structure, and the verifier and downstream skills depend on it. Read `references/examples.md` for the failure modes to avoid.

## Settling the basics

- **Speakers.** Identify the interviewer and the interviewee. If labels are missing and the dialogue doesn't make it clear, ask once, then proceed. If the transcript has several interviewees, write separate notes for each person.
- **Role and research goal.** Use them if provided. If they are missing, write "not provided" and carry on rather than interrogating the user.
- **Bad input.** If a passage is garbled, truncated or clearly mis-transcribed, do not repair it. List it as low-confidence in the Coverage line and do not build items on it.

## Evidence rules ("What they said")

- **Only the interviewee's words count as evidence.** The interviewer's questions, paraphrases and summaries never do, even when the interviewee answers "yes" to them. Leading questions manufacture agreement, so quote what the interviewee actually said and tag the item *prompted*.
- **Tag pain points and upsides with origin and basis.** Origin is *volunteered* (they raised it beyond what the question asked) or *prompted* (a direct answer to a question about that topic). Basis is *experience* (something they did, saw or regularly do) or *speculation* (an assumption, guess or hypothetical). Past behavior is stronger evidence than "I would probably...", and later steps weigh them differently. Other items get an origin tag only.
- **Quotes are verbatim.** One to three sentences. Trim with an ellipsis only to skip filler or text between two fragments, and never to join distant sentences into a new meaning. Do not fix grammar, change tense or swap words. The only other permitted edit is redaction, written `[redacted: name]`.
- **Keep hedges.** "I think maybe" stays tentative; do not write "they confirmed". Do not use words like *strongly*, *clearly* or *major* unless the interviewee did. Describe emphasis as they voiced it.
- **Record contradictions, never resolve them.** If they say two incompatible things, list both under "Tensions within this interview". Never pick one or average them.
- **No frequency claims.** One interview cannot support "repeatedly" or "a major theme". Only cross-interview synthesis can.
- **No outside knowledge.** No industry norms, benchmarks or "typically". If it isn't in the transcript, it isn't in the notes.
- **Separate problems from solutions.** "We need a dashboard" is their view of the solution. The pain behind it is a separate item, and only if they described it.
- **Write "Not discussed"** for any section the transcript doesn't cover, and put nothing else in it. Padding is the most common failure; an empty section is information and points to the next interview's questions.
- **Critical vs. nice-to-have.** Tag each item *stated* (they used words like essential, must, nice to have, a bonus) or *inferred* (you judged it from the emphasis or consequences they described; quote the evidence). If you can't tell which bucket it belongs in, leave it out, and if it matters, raise it as a signal.
- **Numbers.** Log each figure in the table with its period or unit, its basis (*measured*: they pulled or looked it up; *estimated*: a gut figure, assumption or approximation; *hearsay*: reported from someone else) and the quote. Never turn an estimate into a fact, and keep their softeners ("around", "roughly").

## Interpretation rules ("What we read into it")

This block is where models invent things, so it is tagged and capped.

- **Context and background.** *Stated* context (role, responsibilities, tools, workflow) comes from what they said, with quotes. *Inferred values* are job-relevant only (for example trust in the data, speed, avoiding surprises). Each is tagged *inferred* and cites the quote it rests on. Do not record any value you cannot tie to a quote. Never infer traits or demographics (age, personality, "tech-savvy", health, and so on).
- **Signals worth exploring.** Up to three, ranked by how much a follow-up would likely teach. "None noticed" is a valid answer. A signal is an observable moment: something said once and passed over, a workaround, a hedge, a contradiction, an unprompted detail, a notable gap. Each has the quote, why it stood out (an observable reason, not a theory about the person), and one neutral, open follow-up question that doesn't suggest an answer. A signal says what to look into, never what to build: no features, no recommendations, no solutions.

## Privacy

- Refer to people by role ("Ops manager") or "Interviewee A". Do not add names, employers or contact details, and use a name only if the user supplies it and asks for it.
- Redact personal data inside quotes (names of third parties, emails, phone numbers, account details) with `[redacted: type]`, keeping the point of the quote.
- Tag remarks that criticize a named colleague, or touch health, employment disputes or similar matters, as *sensitive*, and keep them to the minimum needed.
- Never infer sensitive attributes, even when hinted at.
- End the notes with a "Privacy flags" line listing what you redacted or tagged, or "none".

## Self-check before you finish

- Every item under "What they said" has a verbatim quote from the interviewee, not the interviewer.
- Sections without coverage say "Not discussed" and contain nothing else.
- Origin and basis tags are on pain points and upsides; stated/inferred tags are on nice-to-haves and critical needs.
- Each inferred value cites a quote, and none concerns traits or demographics.
- There are at most three signals, each with a quote, a reason and a neutral follow-up, and none proposes a solution.
- No frequency claims, outside knowledge, recommendations or unhedged certainty.
- Personal data is redacted and Privacy flags is filled in.
- The Coverage line is accurate.

## Verifying quotes

If you can run code, save the transcript and the notes as files and run:

```
python scripts/verify_quotes.py transcript.txt notes.md
```

It checks that every quote is an exact excerpt of the interviewee's speech (not the interviewer's), that the required sections exist, and that the tagging rules are followed. Fix every failure and rerun until it passes. The transcript should label turns like `Interviewer:` and `Ops manager:`.

If you can't run code, say so, and re-read each quote against the transcript yourself.

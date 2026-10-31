"""Run the evaluation set through the question layer and score every answer.

  python run_eval.py                                 # Sonnet, all 30 questions
  python run_eval.py --model claude-haiku-5-5        # another model
  python run_eval.py --only D1 O1 A2                 # a few questions
  python run_eval.py --runs 3                        # repeat, to measure consistency
  python run_eval.py --self-test                     # check the scorer, no API key needed

Expected answers are not stored: each question's SQL computes them from the
governed views at scoring time, so the eval follows the data after a rebuild.
Scoring is deterministic; no model grades another model.

The same question can get a different answer from one run to the next, so a
question only counts as passed for a model if it passed in every run.

Writes results/<model>.run<N>.json (every answer, tool call and check) and
results/report.md (every model and run so far, side by side).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import yaml

import tools

HERE = Path(__file__).parent
EVAL_SET = HERE / "eval_set.yaml"
RESULTS = HERE / "results"

# USD per million tokens, input and output. Check against Anthropic's pricing
# page before quoting; used only for the cost column in the report.
PRICES = {
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-opus-5-5": (4.00, 20.00),
}


def load_questions(only: list[str] | None = None) -> list[dict]:
    questions = yaml.safe_load(EVAL_SET.read_text())["questions"]
    return [q for q in questions if not only or q["id"] in only]


def truth(q: dict) -> tuple[list[dict], list[dict]]:
    """Rows from the question's ground-truth SQL, and from its `also` SQL if any."""
    dataset = f"{tools.PROJECT}.{tools.DATASET}"
    rows = tools.run(q["truth"].format(dataset=dataset)) if "truth" in q else []
    also = tools.run(q["also"].format(dataset=dataset)) if "also" in q else rows
    return rows, also


def close(found: float, expected: float) -> bool:
    tolerance = max(abs(expected) * 0.01, 0.01)
    return any(abs(f - expected) <= tolerance for f in (found, found * 100, found / 100))


def score(q: dict, answer: dict, rows: list[dict], also: list[dict]) -> list[dict]:
    """Every check for one question: what was expected, what came back, pass or fail."""
    allowed = q["behavior"] if isinstance(q["behavior"], list) else [q["behavior"]]
    checks = [{"check": "behavior", "expected": allowed, "got": answer.get("behavior"),
               "pass": answer.get("behavior") in allowed}]
    # A clarifying question is a complete reply when it's allowed: nothing else to check.
    if answer.get("behavior") == "clarify" and "clarify" in allowed:
        return checks
    spec = q.get("checks", {})
    # Anything malformed simply doesn't count as evidence; it never crashes the run.
    ids = {i.upper() for i in answer.get("contract_ids", []) if isinstance(i, str)}
    figures = [f["value"] for f in answer.get("figures", [])
               if isinstance(f, dict) and isinstance(f.get("value"), (int, float))]
    pairs = [(str(p.get("key", "")).lower(), str(p.get("value", "")).lower())
             for p in answer.get("pairs", []) if isinstance(p, dict)]

    if "ids_exact" in spec:
        expected = {r[spec["ids_exact"]] for r in also}
        checks.append({"check": "ids_exact", "expected": sorted(expected),
                       "missing": sorted(expected - ids), "extra": sorted(ids - expected),
                       "pass": ids == expected})
    if "ids_include" in spec:
        expected = {r[spec["ids_include"]] for r in also}
        checks.append({"check": "ids_include", "expected": sorted(expected),
                       "missing": sorted(expected - ids), "pass": expected <= ids})
    for column in spec.get("numbers", []):
        expected = rows[0][column]
        checks.append({"check": f"number {column}", "expected": expected, "got": figures,
                       "pass": any(close(f, expected) for f in figures)})
    if "pairs" in spec:
        key_col, value_col = spec["pairs"]
        for r in rows:
            key, value = str(r[key_col]).lower(), str(r[value_col]).lower()
            # Either direction counts: "watches -> live" and "live -> watches" say the same thing.
            checks.append({"check": f"pair {key}", "expected": value,
                           "pass": any((key in k and value in v) or (key in v and value in k)
                                       for k, v in pairs)})
    if "tool" in spec:
        used = [t["tool"] for t in answer.get("tools_used", [])]
        checks.append({"check": "tool", "expected": spec["tool"], "got": used,
                       "pass": spec["tool"] in used})
    return checks


def cost(model: str, usage: dict) -> float | None:
    if model not in PRICES:
        return None
    price_in, price_out = PRICES[model]
    return (usage["input_tokens"] * price_in + usage["output_tokens"] * price_out) / 1e6


# ---------------------------------------------------------------- self-test

def perfect_answer(q: dict, rows: list[dict], also: list[dict]) -> dict:
    allowed = q["behavior"] if isinstance(q["behavior"], list) else [q["behavior"]]
    spec = q.get("checks", {})
    id_col = spec.get("ids_exact") or spec.get("ids_include")
    figures = [{"label": k, "value": v} for r in rows[:1] for k, v in r.items()
               if isinstance(v, (int, float)) and not isinstance(v, bool)]
    pairs = [{"key": str(r[spec["pairs"][0]]), "value": str(r[spec["pairs"][1]])}
             for r in rows] if "pairs" in spec else []
    return {"behavior": allowed[0], "text": "", "figures": figures, "pairs": pairs,
            "contract_ids": [r[id_col] for r in also] if id_col else [],
            "tools_used": [{"tool": spec["tool"]}] if "tool" in spec else []}


def wrong_answer(q: dict) -> dict:
    """Plausible but wrong: answers everything, with no evidence."""
    return {"behavior": "answer", "text": "", "figures": [{"label": "x", "value": 123456.0}],
            "pairs": [], "contract_ids": ["CT-99999"], "tools_used": []}


def self_test(questions: list[dict]) -> None:
    failures = 0
    for q in questions:
        rows, also = truth(q)
        good = all(c["pass"] for c in score(q, perfect_answer(q, rows, also), rows, also))
        bad = all(c["pass"] for c in score(q, wrong_answer(q), rows, also))
        status = "ok" if good and not bad else "SCORER PROBLEM"
        failures += status != "ok"
        print(f"{q['id']:4} perfect answer passes: {good!s:5}  wrong answer passes: {bad!s:5}  {status}")
    print(f"\n{len(questions) - failures} of {len(questions)} questions score correctly")
    raise SystemExit(1 if failures else 0)


# --------------------------------------------------------------------- run

def run_eval(model: str, questions: list[dict], run_number: int = 1) -> dict:
    from ask import ask, load_env  # imported here so the self-test needs no API key
    import anthropic

    load_env()
    client = anthropic.Anthropic()
    results = []
    for q in questions:
        rows, also = truth(q)
        started = time.time()
        answer = ask(q["question"], model, client)
        checks = score(q, answer, rows, also)
        passed = all(c["pass"] for c in checks)
        results.append({"id": q["id"], "group": q["group"], "question": q["question"],
                        "pass": passed, "checks": checks, "answer": answer,
                        "seconds": round(time.time() - started, 1)})
        print(f"{q['id']:4} {'PASS' if passed else 'FAIL'}  {answer.get('behavior', '?'):8} {q['question']}")
    usage = {k: sum(r["answer"]["usage"][k] for r in results) for k in ("input_tokens", "output_tokens")}
    run = {"model": model, "run": run_number, "run_at": time.strftime("%Y-%m-%d %H:%M"), "as_of": tools.today(),
           "passed": sum(r["pass"] for r in results), "total": len(results),
           "usage": usage, "cost_usd": cost(model, usage), "results": results}
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"{model}.run{run_number}.json").write_text(json.dumps(run, indent=2, default=str))
    print(f"\n{model} run {run_number}: {run['passed']} of {run['total']} passed\n")
    return run


def write_report() -> None:
    runs = [json.loads(p.read_text()) for p in sorted(RESULTS.glob("*.run*.json"))]
    if not runs:
        return
    meta = yaml.safe_load(EVAL_SET.read_text())
    models = list(dict.fromkeys(r["model"] for r in runs))
    by_model = {m: [r for r in runs if r["model"] == m] for m in models}

    def every_run(model: str, qid: str) -> tuple[int, int]:
        outcomes = [res["pass"] for run in by_model[model] for res in run["results"] if res["id"] == qid]
        return sum(outcomes), len(outcomes)

    lines = ["# Question layer evaluation", "",
             f"Generated by `run_eval.py` on the governed metrics as of {runs[0]['as_of']}. "
             "Expected answers are computed from the governed views at scoring time; scoring is "
             "deterministic. A question passes for a model only if it passed in every run.", "",
             "| Model | Runs | Passed in every run | Each run | Tokens per run | Cost per run |",
             "|---|---|---|---|---|---|"]
    for m in models:
        rs = by_model[m]
        steady = sum(every_run(m, q["id"])[0] == len(rs) for q in meta["questions"])
        tokens = sum(r["usage"]["input_tokens"] + r["usage"]["output_tokens"] for r in rs) // len(rs)
        dollars = [r["cost_usd"] for r in rs if r["cost_usd"] is not None]
        cost_cell = f"${sum(dollars) / len(dollars):.2f}" if dollars else "n/a"
        lines.append(f"| {m} | {len(rs)} | {steady} of {len(meta['questions'])} | "
                     f"{', '.join(str(r['passed']) for r in rs)} | {tokens:,} | {cost_cell} |")

    lines += ["", "## By group (passed in every run)", "",
              "| Group | " + " | ".join(models) + " |", "|---|" + "---|" * len(models)]
    for group, description in meta["groups"].items():
        ids = [q["id"] for q in meta["questions"] if q["group"] == group]
        cells = [f"{sum(every_run(m, i)[0] == len(by_model[m]) for i in ids)} / {len(ids)}" for m in models]
        lines.append(f"| {group} | " + " | ".join(cells) + " |")

    lines += ["", "## Questions that failed at least once", ""]
    shown = False
    for q in meta["questions"]:
        for m in models:
            ok, total = every_run(m, q["id"])
            if ok == total:
                continue
            shown = True
            reasons = sorted({f"{c['check']} expected {c['expected']}"
                              f"{'' if c['check'] != 'behavior' else ', got ' + str(c['got'])}"
                              for run in by_model[m] for res in run["results"] if res["id"] == q["id"]
                              for c in res["checks"] if not c["pass"]})
            lines.append(f"- **{q['id']} · {m}**, passed {ok} of {total} runs. {q['question']} "
                         f"Failed: {'; '.join(r[:300] for r in reasons)}")
    if not shown:
        lines.append("None.")
    (RESULTS / "report.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", action="append", help="repeat to run several models")
    parser.add_argument("--only", nargs="+", help="question IDs")
    parser.add_argument("--runs", type=int, default=1, help="runs per model")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    questions = load_questions(args.only)
    if args.self_test:
        self_test(questions)
    for model in args.model or ["claude-sonnet-5-5"]:
        for run_number in range(1, args.runs + 1):
            run_eval(model, questions, run_number)
    write_report()


if __name__ == "__main__":
    main()

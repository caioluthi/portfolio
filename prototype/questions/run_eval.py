"""Run the evaluation set through the question layer and score every answer.

  python run_eval.py                                 # Sonnet, all 30 questions
  python run_eval.py --model claude-haiku-5-5        # another model
  python run_eval.py --only D1 O1 A2                 # a few questions
  python run_eval.py --self-test                     # check the scorer, no API key needed

Expected answers are not stored: each question's SQL computes them from the
governed views at scoring time, so the eval follows the data after a rebuild.
Scoring is deterministic; no model grades another model.

Writes results/<model>.json (every answer, tool call and check) and
results/report.md (all models run so far, side by side).
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
    ids = {i.upper() for i in answer.get("contract_ids", [])}
    figures = [f["value"] for f in answer.get("figures", []) if isinstance(f.get("value"), (int, float))]
    pairs = [(p["key"].lower(), p["value"].lower()) for p in answer.get("pairs", [])]

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
            checks.append({"check": f"pair {key}", "expected": value,
                           "pass": any(key in k and value in v for k, v in pairs)})
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

def run_eval(model: str, questions: list[dict]) -> dict:
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
    run = {"model": model, "run_at": time.strftime("%Y-%m-%d %H:%M"), "as_of": tools.today(),
           "passed": sum(r["pass"] for r in results), "total": len(results),
           "usage": usage, "cost_usd": cost(model, usage), "results": results}
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"{model}.json").write_text(json.dumps(run, indent=2, default=str))
    print(f"\n{model}: {run['passed']} of {run['total']} passed")
    return run


def write_report() -> None:
    runs = [json.loads(p.read_text()) for p in sorted(RESULTS.glob("*.json"))]
    if not runs:
        return
    groups = yaml.safe_load(EVAL_SET.read_text())["groups"]
    lines = ["# Question layer evaluation", "",
             "Generated by `run_eval.py`. Expected answers are computed from the governed views "
             "at scoring time; scoring is deterministic.", "",
             "| Model | Passed | Questions | Tokens in | Tokens out | Cost |",
             "|---|---|---|---|---|---|"]
    for run in runs:
        dollars = f"${run['cost_usd']:.2f}" if run["cost_usd"] is not None else "n/a"
        lines.append(f"| {run['model']} | {run['passed']} | {run['total']} | "
                     f"{run['usage']['input_tokens']:,} | {run['usage']['output_tokens']:,} | {dollars} |")
    lines += ["", "## By group", "", "| Group | " + " | ".join(r["model"] for r in runs) + " |",
              "|---|" + "---|" * len(runs)]
    for group in groups:
        cells = []
        for run in runs:
            in_group = [r for r in run["results"] if r["group"] == group]
            cells.append(f"{sum(r['pass'] for r in in_group)} / {len(in_group)}" if in_group else "")
        lines.append(f"| {group} | " + " | ".join(cells) + " |")
    lines += ["", "## Failures", ""]
    any_failure = False
    for run in runs:
        for r in run["results"]:
            if r["pass"]:
                continue
            any_failure = True
            failed = "; ".join(f"{c['check']} expected {c['expected']}" for c in r["checks"] if not c["pass"])
            lines.append(f"- **{run['model']} · {r['id']}** {r['question']} Got `{r['answer'].get('behavior')}`. Failed: {failed}")
    if not any_failure:
        lines.append("None.")
    (RESULTS / "report.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", action="append", help="repeat to run several models")
    parser.add_argument("--only", nargs="+", help="question IDs")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    questions = load_questions(args.only)
    if args.self_test:
        self_test(questions)
    for model in args.model or ["claude-sonnet-5-5"]:
        run_eval(model, questions)
    write_report()


if __name__ == "__main__":
    main()

"""Ask a plain-language question and get an answer built only from the governed tools.

  python ask.py "Which contracts are at risk and expiring in the next 30 days?"
  python ask.py --model claude-haiku-5-5 "How much exposure is locked in?"

Needs ANTHROPIC_API_KEY (in the environment or a .env file next to this one)
and Google credentials for BigQuery (gcloud auth application-default login).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import anthropic

import tools

HERE = Path(__file__).parent
DEFAULT_MODEL = "claude-sonnet-5-5"
MAX_TURNS = 8


def load_env() -> None:
    env = HERE / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"'))


def system_prompt() -> str:
    return (HERE / "system_prompt.md").read_text().replace("{today}", tools.today())


def ask(question: str, model: str = DEFAULT_MODEL, client: anthropic.Anthropic | None = None) -> dict:
    """Return the structured answer plus a trace of every tool call and the token usage."""
    client = client or anthropic.Anthropic()
    messages = [{"role": "user", "content": question}]
    trace, usage = [], {"input_tokens": 0, "output_tokens": 0}

    for _ in range(MAX_TURNS):
        response = client.messages.create(
            model=model,
            max_tokens=2000,
            system=system_prompt(),
            tools=tools.TOOLS + [tools.ANSWER_TOOL],
            tool_choice={"type": "any"},  # always a tool: a data tool, or the final answer
            messages=messages,
        )
        usage["input_tokens"] += response.usage.input_tokens
        usage["output_tokens"] += response.usage.output_tokens
        messages.append({"role": "assistant", "content": response.content})

        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            if block.name == "answer":
                return {**block.input, "tools_used": trace, "usage": usage, "model": model}
            output = tools.call(block.name, block.input)
            trace.append({"tool": block.name, "input": block.input,
                          "rows": json.loads(output).get("row_count")})
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
        messages.append({"role": "user", "content": results})

    return {"behavior": "error", "text": f"No answer after {MAX_TURNS} turns.", "contract_ids": [],
            "figures": [], "pairs": [], "tools_used": trace, "usage": usage, "model": model}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("question")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--json", action="store_true", help="print the structured answer")
    args = parser.parse_args()
    load_env()
    result = ask(args.question, args.model)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["text"])
        print(f"\n[{result['behavior']} · tools: {', '.join(t['tool'] for t in result['tools_used']) or 'none'}]")


if __name__ == "__main__":
    main()

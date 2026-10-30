# Plain-language questions

Phase 4, Q5: can Ops and Finance ask questions in plain language and get
trustworthy answers, using only the agreed metric definitions?

## How it works

Claude never writes SQL. It can call six **governed tools**, each a fixed,
parameterized query over the Phase 4 views, or decline. If a question needs a
metric no tool returns, there is nothing to answer it from, so the rule that
answers only use governed definitions is enforced by what the tools can do, not
only by the prompt.

| Tool | Reads | For questions like |
|---|---|---|
| `morning_list` | `ops_morning_list` | Which contracts need attention and expire in the next 30 days? |
| `contracts` | `raw_contracts`, `contract_daily`, `contract_outcome` | How are CN-00580's contracts doing? |
| `exposure` | `finance_exposure` | How much is at risk in the Midwest? |
| `exposure_trend` | `finance_exposure_trend` | Is exposure going up or down? |
| `channel_performance` | `channel_performance` | Where do watches sell best? |
| `definitions` | `metadata.yaml` | What's the difference between act and watch? |

Every reply ends with a structured `answer` call: the text the user reads, plus
the contract IDs, figures and categorical findings it relies on. That structure
is what the evaluation scores.

## The evaluation set

`eval_set.yaml` holds 30 questions: the four from discovery, two rewordings of
each, eight other in-scope questions, six the product must decline, and four
ambiguous ones. Expected answers aren't stored: each question carries SQL that
computes them from the same governed views at scoring time, and scoring is
deterministic. The pass bar is every in-scope question answered correctly and
every out-of-scope question declined.

## Run it

You need Python 3.10+, Google credentials for the BigQuery sandbox, and an
Anthropic API key.

```
pip install -r requirements.txt
gcloud auth application-default login
cp .env.example .env          # then paste your API key into .env
python run_eval.py --self-test                  # checks the scorer; no API key used
python run_eval.py --model claude-haiku-5-5 --model claude-sonnet-5-5
python ask.py "Which region has the most money at risk?"
streamlit run app.py          # the demo page
```

`.env` is git-ignored. Results land in `results/`: one JSON file per model with
every answer, tool call and check, and `report.md` comparing the models.

Users of the real product would not need Claude accounts: the product calls
Claude through the API under one company key, billed by usage.

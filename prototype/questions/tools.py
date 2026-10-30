"""The governed tools: the only way the question layer can read data.

Each tool is a fixed, parameterized query over the governed views built in
Phase 4. The model chooses a tool and fills in its filters; it never writes
SQL, and user text never becomes SQL (every value is a query parameter or is
checked against a fixed list). A question that needs a metric no tool returns
has nothing to be answered from, so the model has to decline it.

Configuration comes from the environment:
  GCP_PROJECT   BigQuery project (default second-avenue-porfolio)
  BQ_DATASET    dataset holding the governed views (default second_avenue)
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

import yaml
from google.cloud import bigquery

PROJECT = os.environ.get("GCP_PROJECT", "second-avenue-porfolio")
DATASET = os.environ.get("BQ_DATASET", "second_avenue")
METADATA = Path(__file__).resolve().parent.parent / "metadata.yaml"

DIMENSIONS = ["book", "region", "channel", "asset_type", "consignor"]
TIERS = ["act", "watch", "all"]
MAX_ROWS = 50


@lru_cache(maxsize=1)
def client() -> bigquery.Client:
    return bigquery.Client(project=PROJECT)


def table(name: str) -> str:
    return f"`{PROJECT}.{DATASET}.{name}`"


def run(sql: str, params: list | None = None) -> list[dict]:
    job = client().query(sql, job_config=bigquery.QueryJobConfig(query_parameters=params or []))
    return [clean(dict(row)) for row in job.result()]


def clean(row: dict) -> dict:
    out = {}
    for key, value in row.items():
        if isinstance(value, float):
            value = round(value, 4) if abs(value) < 10 else round(value, 2)
        elif isinstance(value, Decimal):
            value = float(value)
        elif isinstance(value, (dt.date, dt.datetime)):
            value = value.isoformat()
        out[key] = value
    return out


@lru_cache(maxsize=1)
def today() -> str:
    return run(f"SELECT today FROM {table('flag_parameters')}")[0]["today"]


def envelope(rows: list[dict], **extra) -> dict:
    """Every tool result says what 'today' is and whether rows were cut off."""
    result = {"as_of": today(), "row_count": len(rows), "rows": rows[:MAX_ROWS]}
    if len(rows) > MAX_ROWS:
        result["truncated"] = f"Showing {MAX_ROWS} of {len(rows)} rows; narrow the filters."
    result.update(extra)
    return result


def p(name: str, kind: str, value) -> bigquery.ScalarQueryParameter:
    return bigquery.ScalarQueryParameter(name, kind, value)


# --------------------------------------------------------------------- tools

def morning_list(tier: str = "act", region: str | None = None, consignor_id: str | None = None,
                 max_days_to_expiry: int | None = None, live_auction_possible: bool | None = None,
                 first_act_within_days: int | None = None, limit: int = MAX_ROWS) -> dict:
    if tier not in TIERS:
        raise ValueError(f"tier must be one of {TIERS}")
    sql = f"""
      SELECT risk_tier, list_rank, contract_id, consignor_id, region, target_price,
             days_to_expiry, realized_sales, projected_final_value, projected_share_of_target,
             projected_shortfall, unsold_value, unsold_on_weak_channel, main_unsold_channel,
             live_auction_possible, first_act_date, new_today
      FROM {table('ops_morning_list')}, {table('flag_parameters')} f
      WHERE (@tier = 'all' OR risk_tier = @tier)
        AND (@region IS NULL OR LOWER(region) = LOWER(@region))
        AND (@consignor IS NULL OR consignor_id = @consignor)
        AND (@max_days IS NULL OR days_to_expiry <= @max_days)
        AND (@live IS NULL OR live_auction_possible = @live)
        AND (@first_act_days IS NULL
             OR first_act_date > DATE_SUB(f.today, INTERVAL @first_act_days DAY))
      ORDER BY risk_tier, list_rank
      LIMIT @limit"""
    rows = run(sql, [
        p("tier", "STRING", tier), p("region", "STRING", region),
        p("consignor", "STRING", consignor_id), p("max_days", "INT64", max_days_to_expiry),
        p("live", "BOOL", live_auction_possible), p("first_act_days", "INT64", first_act_within_days),
        p("limit", "INT64", min(int(limit), 500)),
    ])
    return envelope(rows, note=(
        "The morning list leaves off flagged contracts with nothing left to sell; "
        "Finance sees those as exposure locked in. Use exposure for book-wide counts."))


def contracts(contract_id: str | None = None, consignor_id: str | None = None) -> dict:
    if not contract_id and not consignor_id:
        raise ValueError("give contract_id or consignor_id")
    sql = f"""
      WITH today_row AS (
        SELECT d.* FROM {table('contract_daily')} d, {table('flag_parameters')} f
        WHERE d.as_of_date = f.today
      )
      SELECT c.contract_id, c.consignor_id, c.region, c.status, c.start_date, c.expiry_date,
             c.target_price,
             t.days_to_expiry, t.realized_sales, t.projected_final_value,
             t.projected_shortfall, t.evidence_share, t.risk_tier,
             o.realized_sales_at_close, o.closed_below_target, o.first_act_date,
             o.detection_lead_time_days, o.false_positive
      FROM {table('raw_contracts')} c
      LEFT JOIN today_row t USING (contract_id)
      LEFT JOIN {table('contract_outcome')} o USING (contract_id)
      WHERE (@contract IS NULL OR c.contract_id = @contract)
        AND (@consignor IS NULL OR c.consignor_id = @consignor)
      ORDER BY c.start_date"""
    rows = run(sql, [p("contract", "STRING", contract_id), p("consignor", "STRING", consignor_id)])
    for row in rows:  # keep only the fields that apply to the contract's status
        if row["status"] != "active":
            for key in ["days_to_expiry", "realized_sales", "projected_final_value",
                        "projected_shortfall", "evidence_share", "risk_tier"]:
                row.pop(key)
        if row["status"] != "closed":
            for key in ["realized_sales_at_close", "closed_below_target", "first_act_date",
                        "detection_lead_time_days", "false_positive"]:
                row.pop(key)
    summary = {
        "closed": sum(r["status"] == "closed" for r in rows),
        "closed_below_target": sum(bool(r.get("closed_below_target")) for r in rows),
        "active": sum(r["status"] == "active" for r in rows),
        "active_act": sum(r.get("risk_tier") == "act" for r in rows),
        "active_watch": sum(r.get("risk_tier") == "watch" for r in rows),
        "cancelled": sum(r["status"] == "cancelled" for r in rows),
    }
    return envelope(rows, summary=summary)


def exposure(dimension: str = "book", value: str | None = None, limit: int = 10) -> dict:
    if dimension not in DIMENSIONS:
        raise ValueError(f"dimension must be one of {DIMENSIONS}")
    sql = f"""
      SELECT dimension, value, exposure_at_risk, exposure_locked_in, exposure_on_watch,
             contracts_act, contracts_watch, contracts_active, unsold_value,
             share_of_unsold_value_at_risk
      FROM {table('finance_exposure')}
      WHERE dimension = @dimension AND (@value IS NULL OR LOWER(value) = LOWER(@value))
      ORDER BY exposure_at_risk DESC
      LIMIT @limit"""
    rows = run(sql, [p("dimension", "STRING", dimension), p("value", "STRING", value),
                     p("limit", "INT64", min(int(limit), MAX_ROWS))])
    return envelope(rows, note=(
        "exposure_at_risk counts act contracts only and includes exposure_locked_in. "
        "Watch exposure is reported apart. Every dimension adds up to the book total."))


def exposure_trend(from_date: str, to_date: str | None = None) -> dict:
    bounds = run(f"SELECT MIN(as_of_date) AS first, MAX(as_of_date) AS last "
                 f"FROM {table('finance_exposure_trend')}")[0]
    to_date = to_date or bounds["last"]
    sql = f"""
      SELECT as_of_date, exposure_at_risk, exposure_at_risk_4wk_avg, exposure_locked_in,
             exposure_on_watch, contracts_act, contracts_watch, contracts_active
      FROM {table('finance_exposure_trend')}
      WHERE as_of_date BETWEEN @from AND @to
        AND (as_of_date = @from OR as_of_date = @to
             OR MOD(DATE_DIFF(@to, as_of_date, DAY), 7) = 0)
      ORDER BY as_of_date"""
    rows = run(sql, [p("from", "DATE", dt.date.fromisoformat(from_date)),
                     p("to", "DATE", dt.date.fromisoformat(to_date))])
    return envelope(rows, data_available_from=bounds["first"], data_available_to=bounds["last"],
                    note="Weekly points plus both ends. No data exists before data_available_from "
                         "or after data_available_to; there is no forecast.")


def channel_performance(asset_type: str | None = None, channel: str | None = None) -> dict:
    sql = f"""
      SELECT asset_type, channel, items_listed, items_sold, sell_through, price_realization,
             value_realization
      FROM {table('channel_performance')}
      WHERE (@asset_type IS NULL OR LOWER(asset_type) = LOWER(@asset_type))
        AND (@channel IS NULL OR LOWER(channel) = LOWER(@channel))
      ORDER BY asset_type, value_realization DESC"""
    rows = run(sql, [p("asset_type", "STRING", asset_type), p("channel", "STRING", channel)])
    return envelope(rows, note=(
        "Contracts that closed in the last 12 months. value_realization is how well a channel "
        "sells a type overall (price and sell-through together); use it for 'sells best'."))


@lru_cache(maxsize=1)
def glossary() -> dict[str, str]:
    meta = yaml.safe_load(METADATA.read_text())
    terms = dict(meta["columns"])
    for name, spec in meta["tables"].items():
        terms[name] = spec["description"]
    return terms


def definitions(terms: list[str]) -> dict:
    scores: dict[str, int] = {}
    for term in terms:
        words = [w for w in re.split(r"[\s_]+", term.lower()) if w]
        for name, text in glossary().items():
            if name == term.lower().replace(" ", "_"):
                score = 3
            elif all(w in name.split("_") for w in words):
                score = 2
            elif all(re.search(rf"\b{re.escape(w)}\b", text.lower()) for w in words):
                score = 1
            else:
                continue
            scores[name] = max(score, scores.get(name, 0))
    ranked = sorted(scores, key=lambda n: -scores[n])[:8]
    rows = [{"field": n, "definition": glossary()[n]} for n in ranked]
    return envelope(rows, note="Governed definitions from the data product's metadata.")


# ------------------------------------------------------------ tool registry

TOOLS = [
    {
        "name": "morning_list",
        "description": "Ops' morning list as of today: flagged contracts that still have something "
                       "to sell, act contracts ranked by projected shortfall, then watch contracts. "
                       "Use for which contracts need attention, filtered by tier, region, consignor, "
                       "days to expiry, whether a live auction is still possible, or when first flagged act.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tier": {"type": "string", "enum": TIERS, "description": "act, watch or all. Default act."},
                "region": {"type": "string"},
                "consignor_id": {"type": "string", "description": "CN-nnnnn"},
                "max_days_to_expiry": {"type": "integer", "description": "Only contracts expiring within this many days."},
                "live_auction_possible": {"type": "boolean"},
                "first_act_within_days": {"type": "integer", "description": "Only contracts first flagged act within this many days."},
                "limit": {"type": "integer"},
            },
        },
    },
    {
        "name": "contracts",
        "description": "One contract, or every contract for a consignor: status, target, and either today's "
                       "projection and risk tier (active) or the outcome at close (closed), with a summary count.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contract_id": {"type": "string", "description": "CT-nnnnn"},
                "consignor_id": {"type": "string", "description": "CN-nnnnn"},
            },
        },
    },
    {
        "name": "exposure",
        "description": "Finance's exposure as of today: exposure at risk (act), locked in, and on watch, with "
                       "contract counts, for the whole book or split by region, channel, asset_type or consignor.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dimension": {"type": "string", "enum": DIMENSIONS},
                "value": {"type": "string", "description": "One value of the dimension, such as Midwest or live."},
                "limit": {"type": "integer"},
            },
            "required": ["dimension"],
        },
    },
    {
        "name": "exposure_trend",
        "description": "Book-wide exposure over time, as it was known each day, with a 4-week average. "
                       "Weekly points between two dates. Historical only.",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_date": {"type": "string", "description": "YYYY-MM-DD"},
                "to_date": {"type": "string", "description": "YYYY-MM-DD; defaults to today"},
            },
            "required": ["from_date"],
        },
    },
    {
        "name": "channel_performance",
        "description": "How items sell by channel and asset type on contracts that closed in the last 12 months: "
                       "sell-through, price realization and value realization.",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_type": {"type": "string"},
                "channel": {"type": "string", "enum": ["app", "website", "live"]},
            },
        },
    },
    {
        "name": "definitions",
        "description": "Governed definitions of fields and terms, such as risk_tier, exposure_at_risk or locked in.",
        "input_schema": {
            "type": "object",
            "properties": {"terms": {"type": "array", "items": {"type": "string"}}},
            "required": ["terms"],
        },
    },
]

ANSWER_TOOL = {
    "name": "answer",
    "description": "Give the final reply. Call exactly once, last.",
    "input_schema": {
        "type": "object",
        "properties": {
            "behavior": {"type": "string", "enum": ["answer", "decline", "clarify"]},
            "text": {"type": "string", "description": "The reply the user reads. Markdown allowed."},
            "contract_ids": {"type": "array", "items": {"type": "string"},
                             "description": "Every contract the reply lists or relies on."},
            "figures": {"type": "array", "items": {
                "type": "object",
                "properties": {"label": {"type": "string"}, "value": {"type": "number"}},
                "required": ["label", "value"]},
                "description": "Every number the reply states, at full precision as the tool returned it."},
            "pairs": {"type": "array", "items": {
                "type": "object",
                "properties": {"key": {"type": "string"}, "value": {"type": "string"}},
                "required": ["key", "value"]},
                "description": "Categorical findings, such as asset type -> best channel, or trend -> up."},
        },
        "required": ["behavior", "text", "contract_ids", "figures", "pairs"],
    },
}

FUNCTIONS = {
    "morning_list": morning_list,
    "contracts": contracts,
    "exposure": exposure,
    "exposure_trend": exposure_trend,
    "channel_performance": channel_performance,
    "definitions": definitions,
}


def call(name: str, arguments: dict) -> str:
    """Run a tool and return its result as JSON text; errors go back to the model."""
    try:
        return json.dumps(FUNCTIONS[name](**arguments), default=str)
    except Exception as error:  # the model sees the error and can correct its call
        return json.dumps({"error": f"{type(error).__name__}: {error}"})

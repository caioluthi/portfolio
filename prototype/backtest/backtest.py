"""Backtest the risk flag over the last 12 months of closed contracts.

Answers Phase 4 questions Q1 to Q3:
  Q1  Does the flag meet the go-live criteria set on the opportunity page?
  Q2  Which threshold and day floor should the pilot use?
  Q3  Where does linear pacing produce false alarms?

The selection rule is fixed here, before any result was seen:
  among settings that meet both guardrails (false-positive rate <= 40% and
  <= 25 new flags a week), pick the highest median detection lead time;
  break ties on recall at halfway, then on the lower false-positive rate.

Usage: python backtest.py PROJECT_ID DATASET
Writes results/ next to this file: sweep.csv, summary.json and report.md.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
OUT = HERE / "results"

CRITERIA = {  # from docs/phase-2-opportunity.html#go-live
    "median_lead_time_days": (">=", 30),
    "recall_at_halfway": (">=", 0.70),
    "false_positive_rate": ("<=", 0.40),
    "new_flags_per_week": ("<=", 25),
}
PILOT_DEFAULT = (0.80, 15)


def query(project: str, dataset: str, sql_file: str) -> pd.DataFrame:
    sql = (HERE / sql_file).read_text().replace("{dataset}", f"{project}.{dataset}")
    out = subprocess.run(
        ["bq", "--quiet", f"--project_id={project}", "query", "--use_legacy_sql=false",
         "--format=csv", "--max_rows=10000000"],
        input=sql, check=True, capture_output=True, text=True).stdout
    return pd.read_csv(io.StringIO(out))


def evaluate(first_flag: pd.Series, c: pd.DataFrame, today: pd.Timestamp, lifecycle: int = 90) -> dict:
    """Success metrics for one flag setting. first_flag: contract_id -> first flagged day (NaN if never)."""
    c = c.assign(first_flag_day=c.contract_id.map(first_flag))
    pop = c[(c.status == "closed") & (c.expiry_date > today - timedelta(days=365))]
    under = pop[pop.closed_below_target]
    lead = (lifecycle - under.first_flag_day).fillna(0)
    flagged = pop[pop.first_flag_day.notna()]
    first_flag_date = c.start_date + pd.to_timedelta(c.first_flag_day, unit="D")
    in_window = first_flag_date.between(today - timedelta(days=364), today)
    return {
        "median_lead_time_days": float(lead.median()),
        "recall_at_halfway": float((under.first_flag_day <= 45).mean()),
        "recall_ever": float(under.first_flag_day.notna().mean()),
        "false_positive_rate": float((~flagged.closed_below_target).mean()) if len(flagged) else 0.0,
        "new_flags_per_week": float(in_window.sum() / 52),
        "n_closed": int(len(pop)),
        "n_underperformers": int(len(under)),
        "n_flagged": int(len(flagged)),
    }


def meets(name: str, value: float) -> bool:
    op, target = CRITERIA[name]
    return value >= target if op == ">=" else value <= target


def breakdown(first_flag: pd.Series, c: pd.DataFrame, today: pd.Timestamp) -> dict:
    """False-positive rate and share of flags, by main channel, auction-heavy contracts and contract size."""
    c = c.assign(flagged=c.contract_id.map(first_flag).notna())
    pop = c[(c.status == "closed") & (c.expiry_date > today - timedelta(days=365))].copy()
    pop["size_band"] = pd.cut(pop.n_assets, [0, 1, 9, 1000], labels=["1 asset", "2-9 assets", "10+ assets"])
    pop["auction_heavy"] = (pop.live_share >= 0.5).map({True: "half or more at live auction", False: "mostly online"})
    out = {}
    for dim in ["main_channel", "auction_heavy", "size_band"]:
        rows = []
        for key, g in pop.groupby(dim, observed=True):
            f = g[g.flagged]
            rows.append({
                dim: str(key),
                "contracts": int(len(g)),
                "flagged": int(len(f)),
                "false_positive_rate": float((~f.closed_below_target).mean()) if len(f) else None,
                "underperformance_rate": float(g.closed_below_target.mean()),
            })
        out[dim] = rows
    return out


def main() -> None:
    project, dataset = sys.argv[1], sys.argv[2]
    OUT.mkdir(exist_ok=True)
    today = pd.Timestamp(query(project, dataset, "today.sql").today[0])

    contracts = query(project, dataset, "contracts.sql")
    for col in ["start_date", "expiry_date"]:
        contracts[col] = pd.to_datetime(contracts[col])
    contracts["closed_below_target"] = contracts.closed_below_target.fillna(False).astype(bool)
    sweep_raw = query(project, dataset, "sweep.sql")

    rows = []
    for (thr, floor), g in sweep_raw.groupby(["threshold", "day_floor"]):
        m = evaluate(g.set_index("contract_id").first_flag_day, contracts, today)
        rows.append({"threshold": thr, "day_floor": floor, **m})
    sweep = pd.DataFrame(rows).sort_values(["threshold", "day_floor"])
    sweep["meets_guardrails"] = sweep.apply(
        lambda r: meets("false_positive_rate", r.false_positive_rate) and meets("new_flags_per_week", r.new_flags_per_week), axis=1)
    sweep.to_csv(OUT / "sweep.csv", index=False)

    # Today's practice: noticed in the final week, so at most 7 days of lead time
    noticed = contracts.set_index("contract_id").noticed_in_final_week
    baseline = evaluate(noticed[noticed].map(lambda _: 83.0), contracts, today)

    ok = sweep[sweep.meets_guardrails]
    chosen = None
    if len(ok):
        chosen = ok.sort_values(["median_lead_time_days", "recall_at_halfway", "false_positive_rate"],
                                ascending=[False, False, True]).iloc[0]

    def setting(thr, floor):
        r = sweep[(sweep.threshold == thr) & (sweep.day_floor == floor)].iloc[0]
        g = sweep_raw[(sweep_raw.threshold == thr) & (sweep_raw.day_floor == floor)]
        return {
            "threshold": thr, "day_floor": int(floor),
            "metrics": {k: r[k] for k in ["median_lead_time_days", "recall_at_halfway", "recall_ever",
                                          "false_positive_rate", "new_flags_per_week", "n_closed",
                                          "n_underperformers", "n_flagged"]},
            "criteria": {k: bool(meets(k, r[k])) for k in CRITERIA},
            "breakdown": breakdown(g.set_index("contract_id").first_flag_day, contracts, today),
        }

    summary = {
        "today": str(today.date()),
        "baseline_final_week_review": baseline,
        "pilot_default": setting(*PILOT_DEFAULT),
        "chosen": setting(chosen.threshold, chosen.day_floor) if chosen is not None else None,
        "settings_meeting_guardrails": int(len(ok)),
        "settings_tested": int(len(sweep)),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    print(json.dumps({k: v for k, v in summary.items() if k not in ("pilot_default", "chosen")}, indent=2, default=float))
    for name in ("pilot_default", "chosen"):
        s = summary[name]
        if s:
            print(name, s["threshold"], s["day_floor"], json.dumps(s["metrics"], default=float), s["criteria"])


if __name__ == "__main__":
    main()

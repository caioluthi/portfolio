"""Step 2b: compare linear pacing (A), a projection with unsold inventory (B) and
B with watch and act tiers (C). The design, grids and selection rule are in
DESIGN.md, committed before this was first run.

Usage: python run.py PROJECT_ID DATASET
Writes results/: grid_<variant>.csv for training and summary.json.
"""

from __future__ import annotations

import io
import itertools
import json
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
OUT = HERE / "results"
L = 90
BAR = {"median_lead_time_days": 30, "recall_at_halfway": 0.70, "false_positive_rate": 0.40, "new_flags_per_week": 25}
WATCH_CAP = 40

GRIDS = {
    "A": [dict(threshold=t, floor=f) for t, f in itertools.product(
        [0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95], [7, 10, 15, 21, 30])],
    "B": [dict(threshold=t, floor=f, w_share=w) for t, f, w in itertools.product(
        [0.70, 0.75, 0.80, 0.85, 0.90, 0.95], [7, 15, 21, 30], [0.05, 0.15, 0.30])],
}
GRIDS["C"] = [dict(**g, evidence=e) for g, e in itertools.product(GRIDS["B"], [0.15, 0.30, 0.45])]


def bq_table(project: str, sql: str) -> pd.DataFrame:
    out = subprocess.run(["bq", "--quiet", f"--project_id={project}", "query", "--use_legacy_sql=false",
                          "--format=csv", "--max_rows=10000000"], input=sql,
                         check=True, capture_output=True, text=True).stdout
    return pd.read_csv(io.StringIO(out))


def load(project: str, dataset: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    ds = f"`{project}.{dataset}"
    today = pd.Timestamp(bq_table(project, f"SELECT today FROM {ds}.flag_parameters`").today[0])
    c = bq_table(project, f"""SELECT contract_id, start_date, expiry_date, target_price, status
        FROM {ds}.raw_contracts` WHERE status != 'cancelled' AND contract_id != 'CT-EXAMPLE'""")
    a = bq_table(project, f"""SELECT a.contract_id, a.estimate_usd, s.sale_date, s.gross_amount
        FROM {ds}.raw_assets` a LEFT JOIN {ds}.raw_sales` s USING (asset_id)""")
    for col in ["start_date", "expiry_date"]:
        c[col] = pd.to_datetime(c[col])
    a["sale_date"] = pd.to_datetime(a.sale_date)
    a = a.merge(c[["contract_id", "start_date"]], on="contract_id")
    a["sale_day"] = (a.sale_date - a.start_date).dt.days

    # One row per contract per day it was active, up to today
    rows = []
    for cid, g in a.groupby("contract_id"):
        sold = g[g.sale_day.notna()]
        realized, sold_est = np.zeros(L), np.zeros(L)
        np.add.at(realized, sold.sale_day.astype(int).values, sold.gross_amount.values)
        np.add.at(sold_est, sold.sale_day.astype(int).values, sold.estimate_usd.values)
        rows.append(pd.DataFrame({"contract_id": cid, "day": np.arange(L),
                                  "realized": realized.cumsum(), "sold_est": sold_est.cumsum(),
                                  "total_est": g.estimate_usd.sum()}))
    d = pd.concat(rows).merge(c, on="contract_id")
    d["date"] = d.start_date + pd.to_timedelta(d.day, unit="D")
    d = d[d.date <= today].reset_index(drop=True)

    final = d[d.day == L - 1].set_index("contract_id")
    c["below"] = c.contract_id.map(final.realized < final.target_price).fillna(False).astype(bool)
    c["final_sold_est"] = c.contract_id.map(final.sold_est)
    d = d.merge(c[["contract_id", "below", "final_sold_est"]], on="contract_id")
    d["period"] = np.minimum(d.day // 15, 5)
    return c, d, today


def windows(today: pd.Timestamp) -> dict[str, tuple[pd.Timestamp, pd.Timestamp]]:
    mid = today - timedelta(days=182)
    return {"train": (today - timedelta(days=365), mid), "test": (mid, today), "year": (today - timedelta(days=365), today)}


def sell_through(d: pd.DataFrame, c: pd.DataFrame, win) -> np.ndarray:
    """Share of still-unsold appraised value that goes on to sell by expiry, per 15-day period."""
    ids = c[(c.status == "closed") & (c.expiry_date > win[0]) & (c.expiry_date <= win[1])].contract_id
    t = d[d.contract_id.isin(ids)]
    unsold = t.total_est - t.sold_est
    later = t.final_sold_est - t.sold_est
    s = later.groupby(t.period).sum() / unsold.groupby(t.period).sum()
    return s.reindex(range(6)).fillna(0).values


def signals(d: pd.DataFrame, variant: str, p: dict, s: np.ndarray) -> tuple[np.ndarray, np.ndarray | None]:
    """Daily flag (act flag for C) and, for C, the watch state."""
    day_ok = d.day.values >= p["floor"]
    if variant == "A":
        flag = day_ok & (d.realized.values < p["threshold"] * d.target_price.values * d.day.values / L)
        return flag, None
    w = p["w_share"] * d.target_price.values
    realization = (d.realized.values + w) / (d.sold_est.values + w)
    projected = d.realized.values + (d.total_est.values - d.sold_est.values) * s[d.period.values] * realization
    flag = day_ok & (projected < p["threshold"] * d.target_price.values)
    if variant == "B":
        return flag, None
    evidence = d.sold_est.values / np.maximum(d.total_est.values, 1)
    act = flag & (evidence >= p["evidence"])
    return act, flag & ~act


def score(d: pd.DataFrame, c: pd.DataFrame, flag: np.ndarray, watch: np.ndarray | None, win) -> dict:
    first = d.loc[flag].groupby("contract_id").day.min()
    pop = c[(c.status == "closed") & (c.expiry_date > win[0]) & (c.expiry_date <= win[1])]
    ff = pop.contract_id.map(first)
    under = pop.below.values
    lead = np.where(np.isnan(ff[under]), 0, L - ff[under])
    flagged = ff.notna().values
    first_date = c.start_date + pd.to_timedelta(c.contract_id.map(first), unit="D")
    weeks = (win[1] - win[0]).days / 7
    out = {
        "median_lead_time_days": float(np.median(lead)),
        "recall_at_halfway": float((ff[under] <= 45).mean()),
        "recall_ever": float(ff[under].notna().mean()),
        "false_positive_rate": float((~under[flagged]).mean()) if flagged.any() else 0.0,
        "new_flags_per_week": float(((first_date > win[0]) & (first_date <= win[1])).sum() / weeks),
        "n_closed": int(len(pop)), "n_underperformers": int(under.sum()), "n_flagged": int(flagged.sum()),
    }
    if watch is not None:
        on_watch = d.loc[watch & (d.date > win[0]).values & (d.date <= win[1]).values].groupby("date").size()
        days = pd.date_range(win[0] + timedelta(days=1), win[1])
        out["watch_list_p95"] = float(on_watch.reindex(days, fill_value=0).quantile(0.95))
    return out


def passes_guardrails(m: dict) -> bool:
    ok = m["false_positive_rate"] <= BAR["false_positive_rate"] and m["new_flags_per_week"] <= BAR["new_flags_per_week"]
    return ok and m.get("watch_list_p95", 0) <= WATCH_CAP


def passes_all(m: dict) -> dict:
    checks = {
        "median_lead_time_days": m["median_lead_time_days"] >= BAR["median_lead_time_days"],
        "recall_at_halfway": m["recall_at_halfway"] >= BAR["recall_at_halfway"],
        "false_positive_rate": m["false_positive_rate"] <= BAR["false_positive_rate"],
        "new_flags_per_week": m["new_flags_per_week"] <= BAR["new_flags_per_week"],
    }
    if "watch_list_p95" in m:
        checks["watch_list_p95"] = m["watch_list_p95"] <= WATCH_CAP
    return checks


def main() -> None:
    project, dataset = sys.argv[1], sys.argv[2]
    OUT.mkdir(exist_ok=True)
    c, d, today = load(project, dataset)
    win = windows(today)
    s = sell_through(d, c, win["train"])

    # Consistency check: variant A at the pilot default over the full year must reproduce step 2.
    flag, _ = signals(d, "A", dict(threshold=0.80, floor=15), s)
    check = score(d, c, flag, None, win["year"])

    summary = {"today": str(today.date()), "windows": {k: [str(a.date()), str(b.date())] for k, (a, b) in win.items()},
               "sell_through_by_period": [round(float(x), 3) for x in s],
               "check_variant_A_full_year_pilot_default": check, "variants": {}}
    for variant, grid in GRIDS.items():
        rows = []
        for p in grid:
            flag, watch = signals(d, variant, p, s)
            rows.append({**p, **score(d, c, flag, watch, win["train"])})
        g = pd.DataFrame(rows)
        g["meets_guardrails"] = g.apply(lambda r: passes_guardrails(r.to_dict()), axis=1)
        g.to_csv(OUT / f"grid_{variant}.csv", index=False)

        ok = g[g.meets_guardrails]
        params = list(grid[0].keys())
        if len(ok):
            pick = ok.sort_values(["median_lead_time_days", "recall_at_halfway", "false_positive_rate"],
                                  ascending=[False, False, True]).iloc[0]
            status = "chosen on training"
        else:
            ref = g[g.median_lead_time_days >= BAR["median_lead_time_days"]]
            pick = (ref if len(ref) else g).sort_values("false_positive_rate").iloc[0]
            status = "no setting meets the guardrails on training; reference setting shown"
        p = {k: (int(pick[k]) if k == "floor" else float(pick[k])) for k in params}
        flag, watch = signals(d, variant, p, s)
        test = score(d, c, flag, watch, win["test"])
        train = {k: pick[k] for k in pick.index if k not in params and k != "meets_guardrails"}
        checks = passes_all(test)
        summary["variants"][variant] = {
            "status": status, "setting": p,
            "settings_meeting_guardrails_on_training": int(len(ok)), "settings_tested": int(len(g)),
            "training": train, "test": test, "test_checks": checks,
            "passes_on_test": bool(len(ok)) and all(checks.values()),
        }
        print(f"{variant}: {status}; {p}\n   train {json.dumps(train, default=float)}\n   test  {json.dumps(test)}\n   checks {checks}")

    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    print("check A full year:", json.dumps(check))
    print("sell-through by period:", summary["sell_through_by_period"])


if __name__ == "__main__":
    main()

"""Exploratory checks run after the backtest verdict, at the pilot default (80%, day 15).

They explain why the flag fails the false-positive guardrail; they don't change the verdict.

Usage: python explore.py PROJECT_ID DATASET
"""

import sys
from datetime import timedelta

import pandas as pd

from backtest import query

THRESHOLD, FLOOR = 0.80, 15


def main() -> None:
    project, dataset = sys.argv[1], sys.argv[2]
    today = pd.Timestamp(query(project, dataset, "today.sql").today[0])
    c = query(project, dataset, "contracts.sql")
    c["expiry_date"] = pd.to_datetime(c.expiry_date)
    pop = c[(c.status == "closed") & (c.expiry_date > today - timedelta(days=365))].copy()
    pop["below"] = pop.closed_below_target.fillna(False).astype(bool)
    d = query(project, dataset, "daily.sql").merge(pop[["contract_id", "below"]], on="contract_id")
    d = d.sort_values(["contract_id", "days_elapsed"])
    d["flag"] = (d.days_elapsed >= FLOOR) & (d.pacing_pct < THRESHOLD)

    def summary(name: str, col: str) -> None:
        first = d[d[col]].groupby("contract_id").days_elapsed.min()
        p = pop.assign(ff=pop.contract_id.map(first))
        flagged, under = p[p.ff.notna()], p[p.below]
        print(f"  {name:28s} false positives {(~flagged.below).mean():.0%}  "
              f"recall at halfway {(under.ff <= 45).mean():.0%}  "
              f"median lead {(90 - under.ff).fillna(0).median():.0f} days")

    print("1. Is a flag right, by how far into the contract it is raised?")
    d["period"] = pd.cut(d.days_elapsed, [14, 30, 45, 60, 75, 90], labels=["15-30", "30-45", "45-60", "60-75", "75-90"])
    print(d[d.flag].groupby("period", observed=True).below.mean().map("{:.0%}".format).to_string())

    print("\n2. Days 15-45: is a flag right, by how far behind pace the contract is?")
    early = d[d.flag & d.days_elapsed.between(15, 45)].copy()
    early["pacing"] = pd.cut(early.pacing_pct, [-0.01, 0.3, 0.5, 0.65, 0.8], labels=["<30%", "30-50%", "50-65%", "65-80%"])
    print(early.groupby("pacing", observed=True).below.mean().map("{:.0%}".format).to_string())

    print("\n3. Does requiring the flag to persist help?")
    summary("flag as defined", "flag")
    for k in (7, 14):
        d[f"held_{k}"] = d.groupby("contract_id").flag.transform(lambda s: s.rolling(k).sum() == k)
        summary(f"flag held {k} days in a row", f"held_{k}")


if __name__ == "__main__":
    main()

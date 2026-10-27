"""Check the calculated-field views against the PRD's worked example.

Contract CT-EXAMPLE: $50,000 target, 90 days, eight items appraised at $56,000.
Sold $6,500 by day 15 and $11,000 by day 30 (items appraised at $14,000); closes at $36,000.

With the pilot settings (95% of target, day 21 floor, prior 15% of target, act at 15% evidence):
  - no flag before day 21
  - day 21: projected below 95% of target, but only 14% of appraised value has sold, so "watch"
  - day 22: a third sale lifts evidence to 19%, so "act"
  - day 30: projected final value ~ $40,800, shortfall ~ $9,200; linear pacing (context) 66%
  - closes below target with a detection lead time of 68 days, counted from the first act flag

Usage: python check_worked_example.py PROJECT_ID DATASET
"""

import json
import subprocess
import sys


def query(project: str, sql: str) -> list[dict]:
    out = subprocess.run(
        ["bq", f"--project_id={project}", "query", "--use_legacy_sql=false", "--format=json", "--quiet"],
        input=sql, check=True, capture_output=True, text=True,
    ).stdout
    return json.loads(out or "[]")


def main() -> None:
    project, dataset = sys.argv[1], sys.argv[2]
    ds = f"`{project}.{dataset}"
    day = {
        int(r["days_elapsed"]): r
        for r in query(project, f"""
            SELECT days_elapsed, pacing_pct, risk_flag, risk_tier, projected_final_value, projected_shortfall
            FROM {ds}.contract_daily` WHERE contract_id = 'CT-EXAMPLE' AND days_elapsed IN (20, 21, 22, 30)""")
    }
    out = query(project, f"SELECT * FROM {ds}.contract_outcome` WHERE contract_id = 'CT-EXAMPLE'")[0]

    checks = [
        ("no flag before the day floor (day 20)", day[20]["risk_flag"] == "false"),
        ("day 21: flagged, tier watch", day[21]["risk_flag"] == "true" and day[21]["risk_tier"] == "watch"),
        ("day 22: tier act", day[22]["risk_tier"] == "act"),
        ("day 30 projected final ~ $40,800", round(float(day[30]["projected_final_value"]), -2) == 40800),
        ("day 30 projected shortfall ~ $9,200", round(float(day[30]["projected_shortfall"]), -2) == 9200),
        ("day 30 linear pacing (context) is 66%", round(float(day[30]["pacing_pct"]), 2) == 0.66),
        ("closes at $36,000", float(out["realized_sales_at_close"]) == 36000),
        ("closed below target", out["closed_below_target"] == "true"),
        ("detection lead time is 68 days", int(out["detection_lead_time_days"]) == 68),
        ("flagged by halfway", out["flagged_by_halfway"] == "true"),
        ("not a false positive", out["false_positive"] == "false"),
    ]
    width = max(len(name) for name, _ in checks)
    for name, ok in checks:
        print(f"    {'PASS' if ok else 'FAIL'}  {name.ljust(width)}")
    if not all(ok for _, ok in checks):
        sys.exit(1)


if __name__ == "__main__":
    main()

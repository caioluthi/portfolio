"""Check the calculated-field views against the PRD's worked example.

A $50,000, 90-day contract with $11,000 sold by day 30 (contract CT-EXAMPLE):
  - is flagged first on day 15, the first day a flag is allowed
  - on day 30 paces at 66%, projects to about $33,000, a shortfall of about $17,000
  - closes at $36,000, below target, with a detection lead time of 75 days

Usage: python check_worked_example.py PROJECT_ID DATASET
"""

import json
import subprocess
import sys


def query(project: str, sql: str) -> list[dict]:
    out = subprocess.run(
        ["bq", f"--project_id={project}", "query", "--use_legacy_sql=false", "--format=json", "--quiet", sql],
        check=True, capture_output=True, text=True,
    ).stdout
    return json.loads(out or "[]")


def main() -> None:
    project, dataset = sys.argv[1], sys.argv[2]
    ds = f"`{project}.{dataset}"
    day = {
        int(r["days_elapsed"]): r
        for r in query(project, f"""
            SELECT days_elapsed, pacing_pct, risk_flag, projected_final_value, projected_shortfall
            FROM {ds}.contract_daily` WHERE contract_id = 'CT-EXAMPLE' AND days_elapsed IN (14, 15, 30)""")
    }
    out = query(project, f"SELECT * FROM {ds}.contract_outcome` WHERE contract_id = 'CT-EXAMPLE'")[0]

    checks = [
        ("no flag before the day floor (day 14)", day[14]["risk_flag"] == "false"),
        ("flagged on day 15", day[15]["risk_flag"] == "true"),
        ("day 30 pacing is 66%", round(float(day[30]["pacing_pct"]), 2) == 0.66),
        ("day 30 projected final ~ $33,000", round(float(day[30]["projected_final_value"]), -3) == 33000),
        ("day 30 projected shortfall ~ $17,000", round(float(day[30]["projected_shortfall"]), -3) == 17000),
        ("closes at $36,000", float(out["realized_sales_at_close"]) == 36000),
        ("closed below target", out["closed_below_target"] == "true"),
        ("detection lead time is 75 days", int(out["detection_lead_time_days"]) == 75),
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

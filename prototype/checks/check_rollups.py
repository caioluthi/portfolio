"""Check that exposure adds up (backlog E6-S2): the allocation sums back to each act
contract's projected shortfall, and every rollup dimension sums to the book total.

Usage: python check_rollups.py PROJECT_ID DATASET
"""

import json
import subprocess
import sys


def query(project: str, sql: str) -> list[dict]:
    out = subprocess.run(["bq", f"--project_id={project}", "query", "--use_legacy_sql=false", "--format=json", "--quiet"],
                         input=sql, check=True, capture_output=True, text=True).stdout
    return json.loads(out or "[]")


def main() -> None:
    project, dataset = sys.argv[1], sys.argv[2]
    ds = f"`{project}.{dataset}"
    totals = query(project, f"""
        SELECT
          (SELECT SUM(d.projected_shortfall) FROM {ds}.contract_daily` d, {ds}.flag_parameters` p
           WHERE d.as_of_date = p.today AND d.risk_tier = 'act') AS contracts,
          (SELECT SUM(IF(risk_tier = 'act', allocated_shortfall, 0)) FROM {ds}.exposure_allocation`) AS allocated""")[0]
    dims = query(project, f"SELECT dimension, SUM(exposure_at_risk) AS total FROM {ds}.finance_exposure` GROUP BY 1")
    book = float(next(d["total"] for d in dims if d["dimension"] == "book"))
    checks = [("allocation sums to the act contracts' shortfall", abs(float(totals["contracts"]) - float(totals["allocated"])) < 1)]
    checks += [(f"{d['dimension']} rollup adds up to the book (${book:,.0f})", abs(float(d["total"]) - book) < 1)
               for d in dims if d["dimension"] != "book"]
    width = max(len(n) for n, _ in checks)
    for name, ok in checks:
        print(f"    {'PASS' if ok else 'FAIL'}  {name.ljust(width)}")
    if not all(ok for _, ok in checks):
        sys.exit(1)


if __name__ == "__main__":
    main()

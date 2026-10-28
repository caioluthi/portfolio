"""Check appraisal completeness (PRD NFR-5): every item under contract needs an appraised
value at intake, because the flag prices unsold items from it. Reports coverage and fails
if any active contract falls below 95%.

Usage: python check_data_quality.py PROJECT_ID DATASET
"""

import json
import subprocess
import sys

MIN_COVERAGE = 0.95


def query(project: str, sql: str) -> list[dict]:
    out = subprocess.run(["bq", f"--project_id={project}", "query", "--use_legacy_sql=false", "--format=json", "--quiet"],
                         input=sql, check=True, capture_output=True, text=True).stdout
    return json.loads(out or "[]")


def main() -> None:
    project, dataset = sys.argv[1], sys.argv[2]
    ds = f"`{project}.{dataset}"
    r = query(project, f"""
        WITH c AS (
          SELECT a.contract_id, COUNTIF(a.estimate_usd > 0) / COUNT(*) AS coverage
          FROM {ds}.raw_assets` a JOIN {ds}.raw_contracts` k USING (contract_id)
          WHERE k.status = 'active'
          GROUP BY 1)
        SELECT COUNT(*) AS contracts, AVG(coverage) AS avg_coverage,
               COUNTIF(coverage < {MIN_COVERAGE}) AS below_min
        FROM c""")[0]
    ok = int(r["below_min"]) == 0
    print(f"    {'PASS' if ok else 'FAIL'}  appraisal coverage {float(r['avg_coverage']):.1%} across "
          f"{int(r['contracts'])} active contracts; {int(r['below_min'])} below {MIN_COVERAGE:.0%}")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()

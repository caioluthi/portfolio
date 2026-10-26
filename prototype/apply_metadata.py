"""Apply table and column descriptions from metadata.yaml to the BigQuery dataset.

Fails if any live column has no description, so nothing ships undocumented.

Usage: python apply_metadata.py PROJECT_ID DATASET
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

HERE = Path(__file__).parent


def bq(project: str, *args: str) -> str:
    return subprocess.run(["bq", "--quiet", f"--project_id={project}", *args],
                          check=True, capture_output=True, text=True).stdout


def main() -> None:
    project, dataset = sys.argv[1], sys.argv[2]
    meta = yaml.safe_load(open(HERE / "metadata.yaml"))
    glossary = meta["columns"]

    listing = json.loads(bq(project, "ls", "--format=json", "--max_results=1000", dataset))
    plan, missing = [], []
    for t in listing:
        name = t["tableReference"]["tableId"]
        spec = meta["tables"].get(name)
        if spec is None:
            missing.append(f"{name} (table)")
            continue
        schema = json.loads(bq(project, "show", "--format=json", f"{dataset}.{name}"))["schema"]["fields"]
        for field in schema:
            desc = spec.get("columns", {}).get(field["name"], glossary.get(field["name"]))
            if desc is None:
                missing.append(f"{name}.{field['name']}")
            field["description"] = desc
        plan.append((name, spec["description"], schema))

    if missing:
        print("    Missing descriptions:\n      " + "\n      ".join(missing))
        sys.exit(1)

    # One update per table or view: the table and all its column descriptions in a
    # single call, which stays inside BigQuery's per-table metadata update limit.
    n_cols = 0
    with tempfile.TemporaryDirectory() as tmp:
        for name, description, schema in plan:
            path = Path(tmp) / f"{name}.json"
            path.write_text(json.dumps(schema))
            bq(project, "update", f"--description={description}", f"--schema={path}", f"{dataset}.{name}")
            n_cols += len(schema)
    print(f"    {len(plan)} tables and views, {n_cols} columns described")


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# Rebuild the prototype in the BigQuery sandbox from nothing.
#
#   ./build.sh PROJECT_ID [DATASET]
#
# Sandbox tables and views expire after 60 days, so the whole prototype is
# rebuilt by this one command: generate the book, load it, create the views,
# and check the metrics against the PRD's worked example.
set -euo pipefail

PROJECT="${1:?usage: ./build.sh PROJECT_ID [DATASET]}"
DATASET="${2:-second_avenue}"
HERE="$(cd "$(dirname "$0")" && pwd)"
DATA="$HERE/data"

# Flag settings for the pilot. Change them here; no definition changes.
FLAG_THRESHOLD="${FLAG_THRESHOLD:-0.80}"
FLAG_DAY_FLOOR="${FLAG_DAY_FLOOR:-15}"
TODAY="$(python3 -c "import yaml;print(yaml.safe_load(open('$HERE/generator/config.yaml'))['today'])")"

echo "1/4 Generating the book of contracts"
python3 "$HERE/generator/generate.py" --out "$DATA" --report

echo "2/4 Loading into $PROJECT:$DATASET"
bq --project_id="$PROJECT" mk --force --dataset --location=US "$PROJECT:$DATASET" >/dev/null
printf 'today,flag_threshold,flag_day_floor\n%s,%s,%s\n' "$TODAY" "$FLAG_THRESHOLD" "$FLAG_DAY_FLOOR" > "$DATA/flag_parameters.csv"
load() {
  bq --project_id="$PROJECT" load --replace --source_format=CSV --skip_leading_rows=1 \
    "$DATASET.$1" "$DATA/$2.csv" "$3" >/dev/null
  echo "    $1"
}
load raw_consignors  consignors "consignor_id:STRING,home_region:STRING"
load raw_contracts   contracts  "contract_id:STRING,consignor_id:STRING,start_date:DATE,lifecycle_days:INT64,expiry_date:DATE,target_price:FLOAT64,tier_schedule:STRING,status:STRING,region:STRING"
load raw_assets      assets     "asset_id:STRING,contract_id:STRING,asset_type:STRING"
load raw_listings    listings   "listing_id:STRING,asset_id:STRING,listing_channel:STRING,listed_date:DATE,ended_date:DATE,listing_status:STRING"
load raw_sales       sales      "sale_id:STRING,asset_id:STRING,sale_date:DATE,gross_amount:FLOAT64,channel:STRING,region:STRING"
load flag_parameters flag_parameters "today:DATE,flag_threshold:FLOAT64,flag_day_floor:INT64"

echo "3/4 Creating the calculated-field views"
for f in "$HERE"/sql/[0-9]*.sql; do
  sed "s/{dataset}/$PROJECT.$DATASET/g" "$f" | bq --project_id="$PROJECT" query --use_legacy_sql=false --quiet >/dev/null
  echo "    $(basename "$f")"
done

echo "4/4 Checking the metrics against the PRD worked example"
python3 "$HERE/checks/check_worked_example.py" "$PROJECT" "$DATASET"

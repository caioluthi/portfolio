#!/usr/bin/env bash
# Rebuild the prototype in the BigQuery sandbox from nothing.
#
#   ./build.sh PROJECT_ID [DATASET]
#
# Sandbox tables and views expire after 60 days, so the whole prototype is
# rebuilt by this one command: generate the book, load it, create the views,
# describe every table and column, and check the metrics against the PRD's
# worked example.
set -euo pipefail

PROJECT="${1:?usage: ./build.sh PROJECT_ID [DATASET]}"
DATASET="${2:-second_avenue}"
HERE="$(cd "$(dirname "$0")" && pwd)"
DATA="$HERE/data"

# Flag settings for the pilot, chosen by the Phase 4 test (experiment/DESIGN.md).
# Change them here; no definition changes.
FLAG_THRESHOLD="${FLAG_THRESHOLD:-0.95}"
FLAG_DAY_FLOOR="${FLAG_DAY_FLOOR:-21}"
REALIZATION_PRIOR_SHARE="${REALIZATION_PRIOR_SHARE:-0.15}"
ACT_EVIDENCE_MIN="${ACT_EVIDENCE_MIN:-0.15}"
TODAY="$(python3 -c "import yaml;print(yaml.safe_load(open('$HERE/generator/config.yaml'))['today'])")"

echo "1/5 Generating the book of contracts"
python3 "$HERE/generator/generate.py" --out "$DATA" --report

echo "2/5 Loading into $PROJECT:$DATASET"
bq --project_id="$PROJECT" mk --force --dataset --location=US "$PROJECT:$DATASET" >/dev/null
printf 'today,flag_threshold,flag_day_floor,realization_prior_share,act_evidence_min\n%s,%s,%s,%s,%s\n' \
  "$TODAY" "$FLAG_THRESHOLD" "$FLAG_DAY_FLOOR" "$REALIZATION_PRIOR_SHARE" "$ACT_EVIDENCE_MIN" > "$DATA/flag_parameters.csv"
# Sell-through by 15-day period, learned from training contracts by experiment/run.py
cp "$HERE/experiment/results/sell_through.csv" "$DATA/sell_through.csv"
load() {
  bq --quiet --project_id="$PROJECT" load --replace --source_format=CSV --skip_leading_rows=1 \
    "$DATASET.$1" "$DATA/$2.csv" "$3" >/dev/null
  echo "    $1"
}
load raw_consignors  consignors "consignor_id:STRING,home_region:STRING"
load raw_contracts   contracts  "contract_id:STRING,consignor_id:STRING,start_date:DATE,lifecycle_days:INT64,expiry_date:DATE,target_price:FLOAT64,tier_schedule:STRING,status:STRING,region:STRING"
load raw_assets      assets     "asset_id:STRING,contract_id:STRING,asset_type:STRING,estimate_usd:FLOAT64"
load raw_listings    listings   "listing_id:STRING,asset_id:STRING,listing_channel:STRING,listed_date:DATE,ended_date:DATE,listing_status:STRING"
load raw_sales       sales      "sale_id:STRING,asset_id:STRING,sale_date:DATE,gross_amount:FLOAT64,channel:STRING,region:STRING"
load flag_parameters flag_parameters "today:DATE,flag_threshold:FLOAT64,flag_day_floor:INT64,realization_prior_share:FLOAT64,act_evidence_min:FLOAT64"
load sell_through_by_period sell_through "period:INT64,day_from:INT64,day_to:INT64,sell_through:FLOAT64"

echo "3/5 Creating the calculated-field views"
for f in "$HERE"/sql/[0-9]*.sql; do
  sed "s/{dataset}/$PROJECT.$DATASET/g" "$f" | bq --project_id="$PROJECT" query --use_legacy_sql=false --quiet >/dev/null
  echo "    $(basename "$f")"
done

echo "4/5 Describing every table, view and column"
python3 "$HERE/apply_metadata.py" "$PROJECT" "$DATASET"

echo "5/5 Checking the metrics against the PRD worked example"
python3 "$HERE/checks/check_worked_example.py" "$PROJECT" "$DATASET"

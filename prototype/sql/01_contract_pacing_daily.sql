-- Calculated fields, contract x as-of date, before the flag (PRD section 3).
-- One row per active contract per day it was active, replaying history as it was:
-- realized sales only count sales dated on or before the as-of date.
CREATE OR REPLACE VIEW `{dataset}.contract_pacing_daily` AS
WITH params AS (SELECT * FROM `{dataset}.flag_parameters`),
spine AS (
  SELECT
    c.contract_id, c.consignor_id, c.region, c.target_price, c.lifecycle_days,
    c.start_date, c.expiry_date, as_of_date
  FROM `{dataset}.raw_contracts` c, params p,
    UNNEST(GENERATE_DATE_ARRAY(c.start_date, LEAST(DATE_SUB(c.expiry_date, INTERVAL 1 DAY), p.today))) AS as_of_date
  WHERE c.status != 'cancelled'
),
daily_sales AS (
  SELECT a.contract_id, s.sale_date, SUM(s.gross_amount) AS amount
  FROM `{dataset}.raw_sales` s
  JOIN `{dataset}.raw_assets` a USING (asset_id)
  GROUP BY 1, 2
)
SELECT
  sp.contract_id, sp.consignor_id, sp.region, sp.target_price, sp.start_date, sp.expiry_date, sp.as_of_date,
  DATE_DIFF(sp.as_of_date, sp.start_date, DAY) AS days_elapsed,
  -- Elapsed share: days_elapsed / lifecycle_days, capped at 1
  LEAST(DATE_DIFF(sp.as_of_date, sp.start_date, DAY) / sp.lifecycle_days, 1) AS elapsed_share,
  -- Days to expiry
  DATE_DIFF(sp.expiry_date, sp.as_of_date, DAY) AS days_to_expiry,
  -- Realized sales: gross proceeds to date
  IFNULL(SUM(ds.amount), 0) AS realized_sales
FROM spine sp
LEFT JOIN daily_sales ds
  ON ds.contract_id = sp.contract_id AND ds.sale_date <= sp.as_of_date
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10

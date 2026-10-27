-- Calculated fields, contract x as-of date, before the flag (PRD section 3).
-- One row per active contract per day it was active, replaying history as it was:
-- sales and appraised value sold only count sales dated on or before the as-of date.
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
estimates AS (
  SELECT contract_id, SUM(estimate_usd) AS total_estimate
  FROM `{dataset}.raw_assets`
  GROUP BY 1
),
daily_sales AS (
  SELECT a.contract_id, s.sale_date, SUM(s.gross_amount) AS amount, SUM(a.estimate_usd) AS estimate_sold
  FROM `{dataset}.raw_sales` s
  JOIN `{dataset}.raw_assets` a USING (asset_id)
  GROUP BY 1, 2
),
rolled AS (
  SELECT
    sp.contract_id, sp.consignor_id, sp.region, sp.target_price, sp.lifecycle_days,
    sp.start_date, sp.expiry_date, sp.as_of_date,
    IFNULL(SUM(ds.amount), 0) AS realized_sales,
    IFNULL(SUM(ds.estimate_sold), 0) AS sold_estimate
  FROM spine sp
  LEFT JOIN daily_sales ds
    ON ds.contract_id = sp.contract_id AND ds.sale_date <= sp.as_of_date
  GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
)
SELECT
  r.contract_id, r.consignor_id, r.region, r.target_price, r.start_date, r.expiry_date, r.as_of_date,
  DATE_DIFF(r.as_of_date, r.start_date, DAY) AS days_elapsed,
  -- Elapsed share: days_elapsed / lifecycle_days, capped at 1
  LEAST(DATE_DIFF(r.as_of_date, r.start_date, DAY) / r.lifecycle_days, 1) AS elapsed_share,
  -- Days to expiry
  DATE_DIFF(r.expiry_date, r.as_of_date, DAY) AS days_to_expiry,
  -- Realized sales: gross proceeds to date
  r.realized_sales,
  -- Appraised value: of everything under contract, of what has sold, and of what is still unsold
  IFNULL(e.total_estimate, 0) AS total_estimate,
  r.sold_estimate,
  IFNULL(e.total_estimate, 0) - r.sold_estimate AS unsold_estimate
FROM rolled r
LEFT JOIN estimates e USING (contract_id)

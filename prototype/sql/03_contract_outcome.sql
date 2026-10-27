-- Calculated fields at close: the inputs to the success metrics (PRD section 3).
-- One row per closed contract. Success is measured from the first act flag.
CREATE OR REPLACE VIEW `{dataset}.contract_outcome` AS
WITH params AS (SELECT * FROM `{dataset}.flag_parameters`),
realized_at_close AS (
  SELECT a.contract_id, SUM(s.gross_amount) AS realized_sales
  FROM `{dataset}.raw_sales` s
  JOIN `{dataset}.raw_assets` a USING (asset_id)
  JOIN `{dataset}.raw_contracts` c USING (contract_id)
  WHERE s.sale_date < c.expiry_date
  GROUP BY 1
),
first_flags AS (
  SELECT
    contract_id,
    MIN(IF(risk_flag, as_of_date, NULL)) AS first_flag_date,
    MIN(IF(risk_tier = 'act', as_of_date, NULL)) AS first_act_date
  FROM `{dataset}.contract_daily`
  GROUP BY 1
)
SELECT
  c.contract_id, c.consignor_id, c.region, c.target_price, c.start_date, c.expiry_date,
  IFNULL(r.realized_sales, 0) AS realized_sales_at_close,
  -- Closed below target
  IFNULL(r.realized_sales, 0) < c.target_price AS closed_below_target,
  -- First flag date (watch or act) and first act date
  f.first_flag_date,
  f.first_act_date,
  -- Detection lead time: expiry - first act flag, for contracts closing below target; 0 if never acted on
  IF(IFNULL(r.realized_sales, 0) < c.target_price,
     IFNULL(DATE_DIFF(c.expiry_date, f.first_act_date, DAY), 0), NULL) AS detection_lead_time_days,
  -- Flagged by halfway: first act flag on or before day 45
  IFNULL(DATE_DIFF(f.first_act_date, c.start_date, DAY) <= 45, FALSE) AS flagged_by_halfway,
  -- False positive: an act flag at some point, then closed at or above target
  (f.first_act_date IS NOT NULL AND IFNULL(r.realized_sales, 0) >= c.target_price) AS false_positive
FROM `{dataset}.raw_contracts` c
CROSS JOIN params p
LEFT JOIN realized_at_close r USING (contract_id)
LEFT JOIN first_flags f USING (contract_id)
WHERE c.status = 'closed' AND c.expiry_date <= p.today

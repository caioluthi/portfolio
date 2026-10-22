-- Calculated fields, contract x as-of date, including the pilot risk flag (PRD section 3).
-- Flag settings come from the flag_parameters table, so changing them needs no code change.
CREATE OR REPLACE VIEW `{dataset}.contract_daily` AS
WITH params AS (SELECT * FROM `{dataset}.flag_parameters`),
paced AS (
  SELECT
    d.*,
    -- Pacing %: realized / (target x elapsed_share)
    SAFE_DIVIDE(d.realized_sales, d.target_price * d.elapsed_share) AS pacing_pct,
    -- Projected final value: realized / elapsed_share (linear projection)
    SAFE_DIVIDE(d.realized_sales, d.elapsed_share) AS projected_final_value
  FROM `{dataset}.contract_pacing_daily` d
)
SELECT
  paced.*,
  -- Risk flag: pacing below the threshold, active, on or after the day floor
  (paced.days_elapsed >= p.flag_day_floor AND paced.pacing_pct < p.flag_threshold) AS risk_flag,
  -- Projected shortfall: max(0, target - projected final)
  GREATEST(0, paced.target_price - paced.projected_final_value) AS projected_shortfall
FROM paced, params p

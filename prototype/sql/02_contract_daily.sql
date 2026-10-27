-- Calculated fields, contract x as-of date, including the pilot risk flag and its tier
-- (PRD section 3). The projection counts unsold inventory, priced by how this contract's
-- sold items have fetched against their appraisals. Every setting comes from
-- flag_parameters or sell_through_by_period, so changing one needs no code change.
CREATE OR REPLACE VIEW `{dataset}.contract_daily` AS
WITH params AS (SELECT * FROM `{dataset}.flag_parameters`),
base AS (
  SELECT
    d.*,
    LEAST(DIV(d.days_elapsed, 15), 5) AS period,
    -- Pacing %: realized / (target x elapsed_share). Context only; it no longer drives the flag.
    SAFE_DIVIDE(d.realized_sales, d.target_price * d.elapsed_share) AS pacing_pct,
    -- Price realization: realized / appraised value of what sold, pulled toward 1 by a prior
    (d.realized_sales + p.realization_prior_share * d.target_price)
      / (d.sold_estimate + p.realization_prior_share * d.target_price) AS price_realization,
    -- Evidence share: appraised value sold / total appraised value
    SAFE_DIVIDE(d.sold_estimate, d.total_estimate) AS evidence_share
  FROM `{dataset}.contract_pacing_daily` d, params p
),
projected AS (
  SELECT
    b.*,
    st.sell_through,
    -- Projected final value: realized + unsold appraised value x sell-through x price realization
    b.realized_sales + b.unsold_estimate * st.sell_through * b.price_realization AS projected_final_value
  FROM base b
  JOIN `{dataset}.sell_through_by_period` st USING (period)
)
SELECT
  x.* EXCEPT (period),
  -- Projected shortfall: max(0, target - projected final)
  GREATEST(0, x.target_price - x.projected_final_value) AS projected_shortfall,
  -- Risk flag: projected final value below the threshold share of target, on or after the day floor
  (x.days_elapsed >= p.flag_day_floor AND x.projected_final_value < p.flag_threshold * x.target_price) AS risk_flag,
  -- Risk tier: act when enough of the contract has sold to trust the signal, otherwise watch
  CASE
    WHEN NOT (x.days_elapsed >= p.flag_day_floor AND x.projected_final_value < p.flag_threshold * x.target_price) THEN NULL
    WHEN x.evidence_share >= p.act_evidence_min THEN 'act'
    ELSE 'watch'
  END AS risk_tier
FROM projected x, params p

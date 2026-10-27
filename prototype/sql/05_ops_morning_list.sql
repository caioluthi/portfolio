-- Maria's morning list (PRD DPR-5): flagged contracts as of today. Act contracts are
-- the work, ranked by projected shortfall; watch contracts are context, listed after.
-- A contract with nothing left to sell is marked as a loss locked in: it still costs
-- money, but there is no inventory left for Ops to reprice or move.
CREATE OR REPLACE VIEW `{dataset}.ops_morning_list` AS
WITH params AS (SELECT * FROM `{dataset}.flag_parameters`),
flagged AS (
  SELECT d.*
  FROM `{dataset}.contract_daily` d, params p
  WHERE d.as_of_date = p.today AND d.risk_flag
),
history AS (
  SELECT contract_id, MIN(IF(risk_tier = 'act', as_of_date, NULL)) AS first_act_date
  FROM `{dataset}.contract_daily`
  GROUP BY 1
),
sales_by_channel AS (
  SELECT
    a.contract_id,
    SUM(IF(s.channel = 'app', s.gross_amount, 0)) AS sales_app,
    SUM(IF(s.channel = 'website', s.gross_amount, 0)) AS sales_website,
    SUM(IF(s.channel = 'live', s.gross_amount, 0)) AS sales_live
  FROM `{dataset}.raw_sales` s
  JOIN `{dataset}.raw_assets` a USING (asset_id)
  CROSS JOIN params p
  WHERE s.sale_date <= p.today
  GROUP BY 1
),
unsold_by_channel AS (
  SELECT contract_id, channel, SUM(basis_estimate) AS unsold_value
  FROM `{dataset}.exposure_allocation`
  GROUP BY 1, 2
  QUALIFY ROW_NUMBER() OVER (PARTITION BY contract_id ORDER BY unsold_value DESC) = 1
)
SELECT
  f.risk_tier,
  ROW_NUMBER() OVER (PARTITION BY f.risk_tier ORDER BY f.projected_shortfall DESC) AS list_rank,
  f.contract_id, f.consignor_id, f.region, f.target_price,
  f.days_elapsed, f.days_to_expiry,
  f.realized_sales,
  f.projected_final_value,
  SAFE_DIVIDE(f.projected_final_value, f.target_price) AS projected_share_of_target,
  f.projected_shortfall,
  f.price_realization,
  f.evidence_share,
  f.unsold_estimate AS unsold_value,
  (f.unsold_estimate <= 0) AS loss_locked_in,
  IFNULL(sc.sales_app, 0) AS sales_app,
  IFNULL(sc.sales_website, 0) AS sales_website,
  IFNULL(sc.sales_live, 0) AS sales_live,
  u.channel AS main_unsold_channel,
  h.first_act_date,
  (h.first_act_date = f.as_of_date) AS new_today
FROM flagged f
LEFT JOIN history h USING (contract_id)
LEFT JOIN sales_by_channel sc USING (contract_id)
LEFT JOIN unsold_by_channel u USING (contract_id)

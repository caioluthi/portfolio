-- Maria's morning list (PRD DPR-5), as of today. Act contracts are the work, ranked by
-- projected shortfall; watch contracts are context, listed after.
--
-- After the Phase 4 feedback session:
--   - contracts with nothing left to sell are left off: Ops can't change them, and
--     Finance sees them as exposure already locked in
--   - each row says whether a live auction is still possible, since auction catalogs
--     close live_catalog_lead_days before the sale
--   - each row shows the unsold value sitting on a channel where its item type sells
--     weak_channel_gap or more below its best channel. A fact, not a recommendation.
CREATE OR REPLACE VIEW `{dataset}.ops_morning_list` AS
WITH params AS (SELECT * FROM `{dataset}.flag_parameters`),
flagged AS (
  SELECT d.*
  FROM `{dataset}.contract_daily` d, params p
  WHERE d.as_of_date = p.today AND d.risk_flag AND d.unsold_estimate > 0
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
best_channel AS (
  SELECT channel, asset_type, price_realization,
    MAX(price_realization) OVER (PARTITION BY asset_type) AS best_realization
  FROM `{dataset}.channel_performance`
),
unsold AS (
  SELECT
    e.contract_id, e.channel, e.basis_estimate,
    (b.best_realization - b.price_realization >= p.weak_channel_gap) AS on_weak_channel
  FROM `{dataset}.exposure_allocation` e
  CROSS JOIN params p
  LEFT JOIN best_channel b USING (channel, asset_type)
),
unsold_summary AS (
  SELECT contract_id, SUM(IF(on_weak_channel, basis_estimate, 0)) AS unsold_on_weak_channel
  FROM unsold
  GROUP BY 1
),
main_channel AS (
  SELECT contract_id, channel
  FROM (SELECT contract_id, channel, SUM(basis_estimate) AS v FROM unsold GROUP BY 1, 2)
  QUALIFY ROW_NUMBER() OVER (PARTITION BY contract_id ORDER BY v DESC) = 1
)
SELECT
  f.risk_tier,
  ROW_NUMBER() OVER (PARTITION BY f.risk_tier ORDER BY f.projected_shortfall DESC) AS list_rank,
  f.contract_id, f.consignor_id, f.region, f.target_price,
  f.days_elapsed, f.days_to_expiry,
  (f.days_to_expiry >= p.live_catalog_lead_days) AS live_auction_possible,
  f.realized_sales,
  f.projected_final_value,
  SAFE_DIVIDE(f.projected_final_value, f.target_price) AS projected_share_of_target,
  f.projected_shortfall,
  f.price_realization,
  f.evidence_share,
  f.unsold_estimate AS unsold_value,
  IFNULL(us.unsold_on_weak_channel, 0) AS unsold_on_weak_channel,
  IFNULL(sc.sales_app, 0) AS sales_app,
  IFNULL(sc.sales_website, 0) AS sales_website,
  IFNULL(sc.sales_live, 0) AS sales_live,
  m.channel AS main_unsold_channel,
  h.first_act_date,
  (h.first_act_date = f.as_of_date) AS new_today
FROM flagged f
CROSS JOIN params p
LEFT JOIN history h USING (contract_id)
LEFT JOIN sales_by_channel sc USING (contract_id)
LEFT JOIN unsold_summary us USING (contract_id)
LEFT JOIN main_channel m USING (contract_id)

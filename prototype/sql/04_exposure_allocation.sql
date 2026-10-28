-- Each active contract's projected shortfall, as of today, spread over its assets
-- (PRD DPR-4). Spreading at asset level lets exposure roll up by asset-level
-- dimensions - channel and asset type - as well as by region and consignor, and
-- every rollup still adds up to the book total.
--
-- The shortfall is spread over the contract's unsold items in proportion to their
-- appraised value, because that is where the remaining risk sits. A contract with
-- nothing left unsold spreads it over all its items instead.
CREATE OR REPLACE VIEW `{dataset}.exposure_allocation` AS
WITH params AS (SELECT * FROM `{dataset}.flag_parameters`),
today AS (
  SELECT d.contract_id, d.consignor_id, d.region, d.risk_tier, d.projected_shortfall, d.unsold_estimate
  FROM `{dataset}.contract_daily` d, params p
  WHERE d.as_of_date = p.today
),
current_listing AS (
  SELECT l.asset_id, l.listing_channel
  FROM `{dataset}.raw_listings` l, params p
  WHERE l.listed_date <= p.today OR l.listed_date IS NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY l.asset_id ORDER BY l.listed_date DESC) = 1
),
assets AS (
  SELECT
    a.contract_id, a.asset_id, a.asset_type, a.estimate_usd,
    IFNULL(cl.listing_channel, 'not yet listed') AS channel,
    (s.sale_id IS NULL OR s.sale_date > p.today) AS unsold
  FROM `{dataset}.raw_assets` a
  CROSS JOIN params p
  LEFT JOIN current_listing cl USING (asset_id)
  LEFT JOIN `{dataset}.raw_sales` s USING (asset_id)
),
basis AS (
  SELECT
    t.*, x.asset_id, x.asset_type, x.channel,
    x.estimate_usd AS basis_estimate,
    SUM(x.estimate_usd) OVER (PARTITION BY t.contract_id) AS contract_basis
  FROM today t
  JOIN assets x USING (contract_id)
  WHERE (t.unsold_estimate > 0 AND x.unsold) OR t.unsold_estimate <= 0
)
SELECT
  contract_id, consignor_id, region, risk_tier, asset_id, asset_type, channel,
  (unsold_estimate <= 0) AS loss_locked_in,
  basis_estimate,
  projected_shortfall * SAFE_DIVIDE(basis_estimate, contract_basis) AS allocated_shortfall
FROM basis

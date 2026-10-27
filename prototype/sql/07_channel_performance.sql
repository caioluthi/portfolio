-- How items sell by channel and asset type, over contracts that closed in the last
-- 12 months (discovery question 2: which asset types underperform, and in which
-- channel). Measured per item, because a channel is a property of an item, not of
-- a contract.
CREATE OR REPLACE VIEW `{dataset}.channel_performance` AS
WITH params AS (SELECT * FROM `{dataset}.flag_parameters`),
items AS (
  SELECT
    a.asset_type, l.listing_channel AS channel, a.estimate_usd,
    s.gross_amount,
    s.sale_id IS NOT NULL AND s.sale_date < c.expiry_date AS sold
  FROM `{dataset}.raw_assets` a
  JOIN `{dataset}.raw_contracts` c USING (contract_id)
  JOIN `{dataset}.raw_listings` l USING (asset_id)
  LEFT JOIN `{dataset}.raw_sales` s USING (asset_id)
  CROSS JOIN params p
  WHERE c.status = 'closed' AND c.contract_id != 'CT-EXAMPLE'
    AND c.expiry_date > DATE_SUB(p.today, INTERVAL 365 DAY)
)
SELECT
  channel, asset_type,
  COUNT(*) AS items_listed,
  COUNTIF(sold) AS items_sold,
  COUNTIF(sold) / COUNT(*) AS sell_through,
  SAFE_DIVIDE(SUM(IF(sold, gross_amount, 0)), SUM(IF(sold, estimate_usd, 0))) AS price_realization,
  SAFE_DIVIDE(SUM(IF(sold, gross_amount, 0)), SUM(estimate_usd)) AS value_realization
FROM items
GROUP BY 1, 2

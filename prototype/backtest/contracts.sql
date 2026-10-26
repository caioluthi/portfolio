-- One row per non-cancelled contract: outcome at close and the attributes the
-- go-live report breaks false positives down by.
WITH params AS (SELECT * FROM `{dataset}.flag_parameters`),
asset_mix AS (
  SELECT
    a.contract_id,
    COUNT(*) AS n_assets,
    COUNTIF(l.listing_channel = 'live') / COUNT(*) AS live_share,
    APPROX_TOP_COUNT(l.listing_channel, 1)[OFFSET(0)].value AS main_channel
  FROM `{dataset}.raw_assets` a
  JOIN `{dataset}.raw_listings` l USING (asset_id)
  GROUP BY 1
),
-- Today's practice, from the Ops interview: a contract gets looked at in its final
-- week. Replayed as a review on day 83 that applies the same pacing rule.
final_week AS (
  SELECT d.contract_id, d.pacing_pct < p.flag_threshold AS noticed_in_final_week
  FROM `{dataset}.contract_daily` d, params p
  WHERE d.days_elapsed = 83
)
SELECT
  c.contract_id, c.region, c.target_price, c.start_date, c.expiry_date, c.status,
  o.closed_below_target, o.realized_sales_at_close,
  m.n_assets, m.live_share, m.main_channel,
  IFNULL(f.noticed_in_final_week, FALSE) AS noticed_in_final_week
FROM `{dataset}.raw_contracts` c
LEFT JOIN `{dataset}.contract_outcome` o USING (contract_id)
LEFT JOIN asset_mix m USING (contract_id)
LEFT JOIN final_week f USING (contract_id)
WHERE c.status != 'cancelled' AND c.contract_id != 'CT-EXAMPLE'

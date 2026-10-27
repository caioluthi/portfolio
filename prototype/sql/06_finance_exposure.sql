-- David's exposure rollups (PRD DPR-4), as of today. One row per dimension value, in
-- long form so every rollup comes from the same allocation and adds up to the book.
-- Exposure at risk counts act contracts only; watch contracts are reported apart.
CREATE OR REPLACE VIEW `{dataset}.finance_exposure` AS
WITH x AS (
  SELECT *, consignor_id AS consignor FROM `{dataset}.exposure_allocation`
),
long AS (
  SELECT 'book' AS dimension, 'All contracts' AS value, * FROM x
  UNION ALL SELECT 'region', region, * FROM x
  UNION ALL SELECT 'channel', channel, * FROM x
  UNION ALL SELECT 'asset_type', asset_type, * FROM x
  UNION ALL SELECT 'consignor', consignor, * FROM x
)
SELECT
  dimension, value,
  SUM(IF(risk_tier = 'act', allocated_shortfall, 0)) AS exposure_at_risk,
  SUM(IF(risk_tier = 'watch', allocated_shortfall, 0)) AS exposure_on_watch,
  COUNT(DISTINCT IF(risk_tier = 'act', contract_id, NULL)) AS contracts_act,
  COUNT(DISTINCT IF(risk_tier = 'watch', contract_id, NULL)) AS contracts_watch,
  COUNT(DISTINCT contract_id) AS contracts_active,
  SUM(basis_estimate) AS unsold_value,
  SAFE_DIVIDE(SUM(IF(risk_tier = 'act', basis_estimate, 0)), SUM(basis_estimate)) AS share_of_unsold_value_at_risk
FROM long
GROUP BY 1, 2

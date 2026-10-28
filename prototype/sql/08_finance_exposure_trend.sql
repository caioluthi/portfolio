-- David's exposure over time (PRD DPR-4): one row per day, replayed as it was known
-- that day. Week-to-week swings of $50K or more are mostly noise, so a 4-week average
-- sits next to the daily figure (feedback session, Phase 4).
CREATE OR REPLACE VIEW `{dataset}.finance_exposure_trend` AS
WITH daily AS (
  SELECT
    as_of_date,
    SUM(IF(risk_tier = 'act', projected_shortfall, 0)) AS exposure_at_risk,
    SUM(IF(risk_tier = 'act' AND unsold_estimate <= 0, projected_shortfall, 0)) AS exposure_locked_in,
    SUM(IF(risk_tier = 'watch', projected_shortfall, 0)) AS exposure_on_watch,
    COUNTIF(risk_tier = 'act') AS contracts_act,
    COUNTIF(risk_tier = 'watch') AS contracts_watch,
    COUNT(*) AS contracts_active
  FROM `{dataset}.contract_daily`
  WHERE contract_id != 'CT-EXAMPLE'
  GROUP BY 1
)
SELECT
  *,
  AVG(exposure_at_risk) OVER (ORDER BY UNIX_DATE(as_of_date) RANGE BETWEEN 27 PRECEDING AND CURRENT ROW) AS exposure_at_risk_4wk_avg
FROM daily

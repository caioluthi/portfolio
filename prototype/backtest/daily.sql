SELECT contract_id, days_elapsed, pacing_pct
FROM `{dataset}.contract_daily`
WHERE contract_id != 'CT-EXAMPLE'

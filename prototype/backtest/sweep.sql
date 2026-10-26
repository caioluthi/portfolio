-- Replay the risk flag over history for every setting in the sweep grid.
--
-- Reads the governed pacing_pct from contract_daily, so the sweep varies only the
-- two flag parameters and never redefines pacing. Output: one row per setting per
-- contract that was ever flagged under it, with the day it was first flagged.
WITH grid AS (
  SELECT threshold, day_floor
  FROM UNNEST([0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]) AS threshold,
       UNNEST([7, 10, 15, 21, 30]) AS day_floor
)
SELECT
  g.threshold, g.day_floor, d.contract_id,
  MIN(d.days_elapsed) AS first_flag_day
FROM `{dataset}.contract_daily` d
CROSS JOIN grid g
WHERE d.contract_id != 'CT-EXAMPLE'
  AND d.days_elapsed >= g.day_floor
  AND d.pacing_pct < g.threshold
GROUP BY 1, 2, 3

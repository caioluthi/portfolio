-- The governed contract register: one row per contract, every status, with the
-- PRD's required contract fields (section 3). Reads that need a contract's
-- identity, dates or target, such as the question layer, go through this view
-- instead of the raw ConsignTrack table.
CREATE OR REPLACE VIEW `{dataset}.contract_register` AS
SELECT
  contract_id,
  consignor_id,
  region,
  status,
  start_date,
  lifecycle_days,
  expiry_date,
  target_price
FROM `{dataset}.raw_contracts`

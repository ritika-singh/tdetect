-- TDetect: Day 6 - The 5 rule-based anomaly signals
-- A VIEW, not a table, so it stays live as new transactions/baselines change
-- without needing to be manually rebuilt.

CREATE OR REPLACE VIEW SENTINELIQ_DB.ANALYTICS.ANOMALY_FEATURES AS
SELECT
    t.transaction_id,
    t.customer_id,
    t.txn_timestamp,
    t.amount,
    t.merchant_category,
    t.location,
    t.device_id,
    t.is_synthetic_anomaly,
    t.anomaly_type,

    cb.customer_avg_amount,
    cb.customer_common_location,

    -- Signal 1: Amount anomaly (ratio to customer's average)
    ROUND(t.amount / NULLIF(cb.customer_avg_amount, 0), 2) AS amount_ratio,
    CASE WHEN t.amount / NULLIF(cb.customer_avg_amount, 0) >= 3 THEN TRUE ELSE FALSE END AS flag_amount_anomaly,

    -- Signal 2: New/unknown device
    CASE WHEN ARRAY_CONTAINS(t.device_id::VARIANT, cb.customer_known_devices) THEN FALSE ELSE TRUE END AS flag_new_device,

    -- Signal 3: Unusual location
    CASE WHEN t.location != cb.customer_common_location THEN TRUE ELSE FALSE END AS flag_unusual_location,

    -- Signal 4: Velocity (transactions by same customer within 10 min, rolling window)
    COUNT(*) OVER (
        PARTITION BY t.customer_id
        ORDER BY t.txn_timestamp
        RANGE BETWEEN INTERVAL '10 minutes' PRECEDING AND CURRENT ROW
    ) AS txns_last_10min,

    -- Signal 5: Unusual merchant category for this customer
    CASE WHEN t.merchant_category NOT IN (
        SELECT merchant_category FROM SENTINELIQ_DB.ANALYTICS.TRANSACTIONS t2
        WHERE t2.customer_id = t.customer_id
        GROUP BY merchant_category
        HAVING COUNT(*) >= 2
    ) THEN TRUE ELSE FALSE END AS flag_unusual_merchant

FROM SENTINELIQ_DB.ANALYTICS.TRANSACTIONS t
JOIN SENTINELIQ_DB.ANALYTICS.CUSTOMER_BEHAVIOR cb
    ON t.customer_id = cb.customer_id;

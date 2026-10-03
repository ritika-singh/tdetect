-- TDetect: Day 5 — Customer behavior baselines
-- IMPORTANT: excludes anomalous transactions from the baseline calculation.
-- Including them causes data leakage - a transaction's own device/amount/location
-- would get counted into its own "normal" baseline, silently masking the anomaly
-- it's supposed to trigger. (Caught and fixed during Week 1 testing - see DECISION_LOG.md.)

CREATE OR REPLACE TABLE SENTINELIQ_DB.ANALYTICS.CUSTOMER_BEHAVIOR AS
SELECT
    customer_id,
    COUNT(*)                          AS customer_transaction_count,
    ROUND(AVG(amount), 2)             AS customer_avg_amount,
    MAX(amount)                       AS customer_max_amount,
    MODE(location)                    AS customer_common_location,
    ARRAY_AGG(DISTINCT device_id)     AS customer_known_devices
FROM SENTINELIQ_DB.ANALYTICS.TRANSACTIONS
WHERE is_synthetic_anomaly = FALSE
GROUP BY customer_id;

SELECT * FROM SENTINELIQ_DB.ANALYTICS.CUSTOMER_BEHAVIOR LIMIT 10;

-- TDetect: Day 3-4 - Schema setup and data cleaning
-- Run this after creating the SENTINELIQ_DB database and uploading
-- synthetic_transactions.csv into SENTINELIQ_DB.PUBLIC.TRANSACTIONS_RAW
-- (or RAW.TRANSACTIONS_RAW if you created a separate RAW schema).

-- 1. Data quality checks
SELECT COUNT(*) AS total_rows FROM SENTINELIQ_DB.RAW.TRANSACTIONS_RAW;

SELECT COUNT(*) AS duplicate_txn_ids
FROM (
    SELECT transaction_id, COUNT(*) c
    FROM SENTINELIQ_DB.RAW.TRANSACTIONS_RAW
    GROUP BY transaction_id
    HAVING c > 1
);

SELECT COUNT(*) AS missing_customer_id FROM SENTINELIQ_DB.RAW.TRANSACTIONS_RAW WHERE customer_id IS NULL;
SELECT COUNT(*) AS invalid_amount FROM SENTINELIQ_DB.RAW.TRANSACTIONS_RAW WHERE amount IS NULL OR amount <= 0;
SELECT COUNT(*) AS missing_timestamp FROM SENTINELIQ_DB.RAW.TRANSACTIONS_RAW WHERE TIMESTAMP IS NULL;
SELECT COUNT(*) AS missing_device FROM SENTINELIQ_DB.RAW.TRANSACTIONS_RAW WHERE device_id IS NULL;
SELECT COUNT(*) AS missing_location FROM SENTINELIQ_DB.RAW.TRANSACTIONS_RAW WHERE location IS NULL;

-- 2. Create the clean analytics table
CREATE OR REPLACE TABLE SENTINELIQ_DB.ANALYTICS.TRANSACTIONS AS
SELECT DISTINCT
    transaction_id,
    customer_id,
    TIMESTAMP          AS txn_timestamp,
    amount,
    merchant_category,
    location,
    device_id,
    is_synthetic_anomaly,
    anomaly_type
FROM SENTINELIQ_DB.RAW.TRANSACTIONS_RAW
WHERE customer_id IS NOT NULL
  AND amount > 0
  AND TIMESTAMP IS NOT NULL;

SELECT COUNT(*) AS clean_row_count FROM SENTINELIQ_DB.ANALYTICS.TRANSACTIONS;

-- Note: if a transaction was appended in a later CSV load and is_synthetic_anomaly
-- doesn't read as TRUE for it (a known Snowflake CSV-append coercion quirk), fix with:
-- UPDATE SENTINELIQ_DB.ANALYTICS.TRANSACTIONS
-- SET is_synthetic_anomaly = TRUE
-- WHERE anomaly_type IN ('compound_severe', 'compound_moderate', 'critical_stack', 'critical_stack_filler');

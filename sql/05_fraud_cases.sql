-- TDetect: Days 18-20 - Human decision + audit trail table
-- Append-only by design: corrections are recorded as new rows, never
-- overwritten, so the full decision history (including mistakes and
-- corrections) stays visible.

CREATE OR REPLACE TABLE SENTINELIQ_DB.CASES.FRAUD_CASES (
    transaction_id VARCHAR,
    customer_id VARCHAR,
    risk_score NUMBER,
    risk_level VARCHAR,
    recommended_action VARCHAR,
    analyst_decision VARCHAR,
    decision_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

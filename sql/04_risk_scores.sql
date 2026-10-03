-- TDetect: Day 7 - Weighted risk score and risk level
-- Transparent, explainable point system: amount=25, device=20, location=20,
-- velocity=20, merchant=15 (max 100). Levels: 0-30 Low, 31-60 Medium,
-- 61-80 High, 81-100 Critical.

CREATE OR REPLACE VIEW SENTINELIQ_DB.ANALYTICS.RISK_SCORES AS
SELECT
    *,
    (CASE WHEN flag_amount_anomaly THEN 25 ELSE 0 END) +
    (CASE WHEN flag_new_device THEN 20 ELSE 0 END) +
    (CASE WHEN flag_unusual_location THEN 20 ELSE 0 END) +
    (CASE WHEN txns_last_10min >= 4 THEN 20 ELSE 0 END) +
    (CASE WHEN flag_unusual_merchant THEN 15 ELSE 0 END)
        AS risk_score,
    CASE
        WHEN (CASE WHEN flag_amount_anomaly THEN 25 ELSE 0 END) +
             (CASE WHEN flag_new_device THEN 20 ELSE 0 END) +
             (CASE WHEN flag_unusual_location THEN 20 ELSE 0 END) +
             (CASE WHEN txns_last_10min >= 4 THEN 20 ELSE 0 END) +
             (CASE WHEN flag_unusual_merchant THEN 15 ELSE 0 END) >= 81 THEN 'Critical'
        WHEN (CASE WHEN flag_amount_anomaly THEN 25 ELSE 0 END) +
             (CASE WHEN flag_new_device THEN 20 ELSE 0 END) +
             (CASE WHEN flag_unusual_location THEN 20 ELSE 0 END) +
             (CASE WHEN txns_last_10min >= 4 THEN 20 ELSE 0 END) +
             (CASE WHEN flag_unusual_merchant THEN 15 ELSE 0 END) >= 61 THEN 'High'
        WHEN (CASE WHEN flag_amount_anomaly THEN 25 ELSE 0 END) +
             (CASE WHEN flag_new_device THEN 20 ELSE 0 END) +
             (CASE WHEN flag_unusual_location THEN 20 ELSE 0 END) +
             (CASE WHEN txns_last_10min >= 4 THEN 20 ELSE 0 END) +
             (CASE WHEN flag_unusual_merchant THEN 15 ELSE 0 END) >= 31 THEN 'Medium'
        ELSE 'Low'
    END AS risk_level
FROM SENTINELIQ_DB.ANALYTICS.ANOMALY_FEATURES;

SELECT * FROM SENTINELIQ_DB.ANALYTICS.RISK_SCORES
WHERE is_synthetic_anomaly = TRUE
ORDER BY risk_score DESC;

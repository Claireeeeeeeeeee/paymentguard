USE paymentguard;
SET SQL_SAFE_UPDATES = 0;

-- ============================================
-- CLEAR PREVIOUSLY LOADED DATA
-- Makes this script safe to run again
-- ============================================

DELETE FROM fact_disputes;
DELETE FROM fact_payments;
DELETE FROM dim_customers;
DELETE FROM dim_merchants;


-- ============================================
-- LOAD MERCHANTS
-- Expected: 100 rows
-- ============================================

LOAD DATA LOCAL INFILE
'/Users/vv/Documents/paymentguard/data/raw/merchants.csv'
INTO TABLE dim_merchants
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    merchant_id,
    merchant_name,
    industry,
    merchant_country,
    @onboarding_date,
    merchant_size,
    risk_category,
    platform_type,
    reserve_rate,
    expected_monthly_volume
)
SET onboarding_date = STR_TO_DATE(
    @onboarding_date,
    '%Y-%m-%d'
);


-- ============================================
-- LOAD CUSTOMERS
-- Expected: 10,000 rows
-- ============================================

LOAD DATA LOCAL INFILE
'/Users/vv/Documents/paymentguard/data/raw/customers.csv'
INTO TABLE dim_customers
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    customer_id,
    customer_country,
    @account_created_at,
    customer_segment,
    historical_orders,
    historical_chargebacks,
    email_age_days,
    usual_device_id,
    lifetime_value
)
SET account_created_at = STR_TO_DATE(
    @account_created_at,
    '%Y-%m-%d'
);


-- ============================================
-- LOAD PAYMENTS
-- Expected: 50,000 rows
-- ============================================

LOAD DATA LOCAL INFILE
'/Users/vv/Documents/paymentguard/data/raw/payments.csv'
INTO TABLE fact_payments
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    payment_id,
    @transaction_timestamp,
    merchant_id,
    customer_id,
    amount,
    currency,
    processing_fee,
    payment_method,
    card_type,
    card_network,
    issuer_country,
    billing_country,
    ip_country,
    device_type,
    device_id,
    is_new_device,
    is_new_customer,
    is_cross_border,
    country_mismatch_flag,
    velocity_1h,
    authentication_used,
    authentication_result,
    risk_score,
    decision,
    authorisation_status,
    decline_reason,
    confirmed_fraud,
    refund_status
)
SET transaction_timestamp = STR_TO_DATE(
    @transaction_timestamp,
    '%Y-%m-%d %H:%i:%s'
);


-- ============================================
-- LOAD DISPUTES
-- Matches your actual 10-column disputes.csv
-- Expected: 834 rows
-- ============================================

LOAD DATA LOCAL INFILE
'/Users/vv/Documents/paymentguard/data/raw/disputes.csv'
INTO TABLE fact_disputes
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    dispute_id,
    payment_id,
    @dispute_date,
    dispute_reason,
    disputed_amount,
    dispute_fee,
    dispute_status,
    @resolution_date,
    recovered_amount,
    net_dispute_loss
)
SET
    dispute_date = STR_TO_DATE(
        @dispute_date,
        '%Y-%m-%d'
    ),

    resolution_date = STR_TO_DATE(
        NULLIF(@resolution_date, ''),
        '%Y-%m-%d'
    );


-- ============================================
-- CHECK THE LOADED ROW COUNTS
-- ============================================

SELECT
    'dim_merchants' AS table_name,
    COUNT(*) AS row_count
FROM dim_merchants

UNION ALL

SELECT
    'dim_customers',
    COUNT(*)
FROM dim_customers

UNION ALL

SELECT
    'fact_payments',
    COUNT(*)
FROM fact_payments

UNION ALL

SELECT
    'fact_disputes',
    COUNT(*)
FROM fact_disputes;

SET SQL_SAFE_UPDATES = 1;
USE paymentguard;


-- ============================================
-- MERCHANT DIMENSION
-- One row per merchant
-- ============================================

CREATE TABLE IF NOT EXISTS dim_merchants (
    merchant_id VARCHAR(10) PRIMARY KEY,
    merchant_name VARCHAR(100) NOT NULL,
    industry VARCHAR(50) NOT NULL,
    merchant_country CHAR(2) NOT NULL,
    onboarding_date DATE NOT NULL,
    merchant_size VARCHAR(20) NOT NULL,
    risk_category VARCHAR(20) NOT NULL,
    platform_type VARCHAR(30) NOT NULL,
    reserve_rate DECIMAL(8,4) NOT NULL,
    expected_monthly_volume DECIMAL(15,2) NOT NULL
) ENGINE = InnoDB;


-- ============================================
-- CUSTOMER DIMENSION
-- One row per customer
-- ============================================

CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id VARCHAR(10) PRIMARY KEY,
    customer_country CHAR(2) NOT NULL,
    account_created_at DATE NOT NULL,
    customer_segment VARCHAR(20) NOT NULL,
    historical_orders INT NOT NULL,
    historical_chargebacks INT NOT NULL,
    email_age_days INT NOT NULL,
    usual_device_id VARCHAR(20) NOT NULL,
    lifetime_value DECIMAL(15,2) NOT NULL
) ENGINE = InnoDB;


-- ============================================
-- PAYMENT FACT
-- One row per payment attempt
-- ============================================

CREATE TABLE IF NOT EXISTS fact_payments (
    payment_id VARCHAR(12) PRIMARY KEY,
    transaction_timestamp DATETIME NOT NULL,
    merchant_id VARCHAR(10) NOT NULL,
    customer_id VARCHAR(10) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    currency CHAR(3) NOT NULL,
    processing_fee DECIMAL(15,2) NOT NULL,
    payment_method VARCHAR(30) NOT NULL,
    card_type VARCHAR(20) NOT NULL,
    card_network VARCHAR(20) NOT NULL,
    issuer_country CHAR(2) NOT NULL,
    billing_country CHAR(2) NOT NULL,
    ip_country CHAR(2) NOT NULL,
    device_type VARCHAR(20) NOT NULL,
    device_id VARCHAR(20) NOT NULL,
    is_new_device TINYINT NOT NULL,
    is_new_customer TINYINT NOT NULL,
    is_cross_border TINYINT NOT NULL,
    country_mismatch_flag TINYINT NOT NULL,
    velocity_1h INT NOT NULL,
    authentication_used TINYINT NOT NULL,
    authentication_result VARCHAR(30) NOT NULL,
    risk_score INT NOT NULL,
    decision VARCHAR(20) NOT NULL,
    authorisation_status VARCHAR(20) NOT NULL,
    decline_reason VARCHAR(50) NOT NULL,
    confirmed_fraud TINYINT NOT NULL,
    refund_status VARCHAR(30) NOT NULL,

    CONSTRAINT fk_payments_merchant
        FOREIGN KEY (merchant_id)
        REFERENCES dim_merchants(merchant_id),

    CONSTRAINT fk_payments_customer
        FOREIGN KEY (customer_id)
        REFERENCES dim_customers(customer_id),

    INDEX idx_payment_timestamp (
        transaction_timestamp
    ),

    INDEX idx_payment_merchant (
        merchant_id
    ),

    INDEX idx_payment_customer (
        customer_id
    ),

    INDEX idx_payment_status (
        authorisation_status
    ),

    INDEX idx_payment_fraud (
        confirmed_fraud
    )
) ENGINE = InnoDB;


-- ============================================
-- DISPUTE FACT
-- Matches your actual disputes.csv
-- ============================================

CREATE TABLE IF NOT EXISTS fact_disputes (
    dispute_id VARCHAR(10) PRIMARY KEY,
    payment_id VARCHAR(12) NOT NULL UNIQUE,
    dispute_date DATE NOT NULL,
    dispute_reason VARCHAR(50) NOT NULL,
    disputed_amount DECIMAL(15,2) NOT NULL,
    dispute_fee DECIMAL(15,2) NOT NULL,
    dispute_status VARCHAR(20) NOT NULL,
    resolution_date DATE NULL,
    recovered_amount DECIMAL(15,2) NOT NULL,
    net_dispute_loss DECIMAL(15,2) NOT NULL,

    CONSTRAINT fk_disputes_payment
        FOREIGN KEY (payment_id)
        REFERENCES fact_payments(payment_id),

    INDEX idx_dispute_date (
        dispute_date
    ),

    INDEX idx_dispute_status (
        dispute_status
    )
) ENGINE = InnoDB;


SHOW TABLES;
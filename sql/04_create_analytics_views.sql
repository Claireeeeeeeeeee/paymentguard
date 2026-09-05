USE paymentguard;


DROP VIEW IF EXISTS vw_payment_enriched;


CREATE VIEW vw_payment_enriched AS

SELECT
    -- Payment information
    p.*,

    DATE(
        p.transaction_timestamp
    ) AS transaction_date,

    DATE_FORMAT(
        p.transaction_timestamp,
        '%Y-%m'
    ) AS transaction_month,

    -- Merchant information
    m.merchant_name,
    m.industry,
    m.merchant_country,
    m.merchant_size,
    m.risk_category AS merchant_risk_category,
    m.platform_type,
    m.reserve_rate,
    m.expected_monthly_volume,

    -- Customer information
    c.customer_country,
    c.account_created_at,
    c.customer_segment,
    c.historical_orders,
    c.historical_chargebacks,
    c.email_age_days,
    c.lifetime_value,

    -- Dispute information
    d.dispute_id,
    d.dispute_date,
    d.dispute_reason,
    d.disputed_amount,
    d.dispute_fee,
    d.dispute_status,
    d.resolution_date,
    d.recovered_amount,
    d.net_dispute_loss,

    -- Analytical flags
    CASE
        WHEN p.authorisation_status = 'Approved'
        THEN 1
        ELSE 0
    END AS approved_flag,

    CASE
        WHEN p.authorisation_status = 'Declined'
        THEN 1
        ELSE 0
    END AS declined_flag,

    CASE
        WHEN d.dispute_id IS NOT NULL
        THEN 1
        ELSE 0
    END AS has_dispute,

    -- Approved payment amount
    CASE
        WHEN p.authorisation_status = 'Approved'
        THEN p.amount
        ELSE 0
    END AS approved_amount,

    -- Processing revenue is earned only on approved payments
    CASE
        WHEN p.authorisation_status = 'Approved'
        THEN p.processing_fee
        ELSE 0
    END AS gross_processing_revenue,

    -- Fraud loss:
    -- use dispute net loss if the fraud payment was disputed;
    -- otherwise use the original payment amount
    CASE
        WHEN p.confirmed_fraud = 1
             AND d.dispute_id IS NOT NULL
        THEN d.net_dispute_loss

        WHEN p.confirmed_fraud = 1
        THEN p.amount

        ELSE 0
    END AS modelled_fraud_loss,

    -- Non-fraud dispute loss
    CASE
        WHEN p.confirmed_fraud = 0
             AND d.dispute_id IS NOT NULL
        THEN d.net_dispute_loss

        ELSE 0
    END AS modelled_nonfraud_dispute_loss

FROM fact_payments AS p

INNER JOIN dim_merchants AS m
    ON p.merchant_id = m.merchant_id

INNER JOIN dim_customers AS c
    ON p.customer_id = c.customer_id

LEFT JOIN fact_disputes AS d
    ON p.payment_id = d.payment_id;

-- =====================================================
-- MONTHLY PAYMENT PERFORMANCE VIEW
-- =====================================================

DROP VIEW IF EXISTS vw_monthly_performance;

CREATE VIEW vw_monthly_performance AS
SELECT
    transaction_month,
    currency,

    COUNT(*) AS total_attempts,

    SUM(approved_flag) AS approved_payments,

    SUM(declined_flag) AS declined_payments,

    ROUND(
        100.0 * SUM(approved_flag) / NULLIF(COUNT(*), 0),
        2
    ) AS approval_rate_pct,

    ROUND(
        SUM(approved_amount),
        2
    ) AS approved_volume,

    SUM(confirmed_fraud = 1) AS fraud_payments,

    ROUND(
        100.0 * SUM(confirmed_fraud = 1)
        / NULLIF(SUM(approved_flag), 0),
        2
    ) AS fraud_rate_pct,

    SUM(has_dispute) AS disputed_payments,

    ROUND(
        100.0 * SUM(has_dispute)
        / NULLIF(SUM(approved_flag), 0),
        2
    ) AS dispute_rate_pct,

    ROUND(
        SUM(gross_processing_revenue),
        2
    ) AS gross_processing_revenue,

    ROUND(
        SUM(modelled_fraud_loss),
        2
    ) AS fraud_losses,

    ROUND(
        SUM(modelled_nonfraud_dispute_loss),
        2
    ) AS nonfraud_dispute_losses,

    ROUND(
        SUM(gross_processing_revenue)
        - SUM(modelled_fraud_loss)
        - SUM(modelled_nonfraud_dispute_loss),
        2
    ) AS net_revenue

FROM vw_payment_enriched

GROUP BY
    transaction_month,
    currency;

-- =====================================================
-- MERCHANT PERFORMANCE VIEW
-- =====================================================

DROP VIEW IF EXISTS vw_merchant_performance;

CREATE VIEW vw_merchant_performance AS
SELECT
    merchant_id,
    merchant_name,
    industry,
    merchant_country,
    merchant_size,
    merchant_risk_category,
    currency,

    COUNT(*) AS total_attempts,

    SUM(approved_flag) AS approved_payments,

    SUM(declined_flag) AS declined_payments,

    ROUND(
        100.0 * SUM(approved_flag) / NULLIF(COUNT(*), 0),
        2
    ) AS approval_rate_pct,

    ROUND(
        SUM(approved_amount),
        2
    ) AS approved_volume,

    SUM(confirmed_fraud = 1) AS fraud_payments,

    ROUND(
        100.0 * SUM(confirmed_fraud = 1)
        / NULLIF(SUM(approved_flag), 0),
        2
    ) AS fraud_rate_pct,

    SUM(has_dispute) AS disputed_payments,

    ROUND(
        100.0 * SUM(has_dispute)
        / NULLIF(SUM(approved_flag), 0),
        2
    ) AS dispute_rate_pct,

    ROUND(
        SUM(gross_processing_revenue),
        2
    ) AS gross_processing_revenue,

    ROUND(
        SUM(modelled_fraud_loss)
        + SUM(modelled_nonfraud_dispute_loss),
        2
    ) AS total_losses,

    ROUND(
        SUM(gross_processing_revenue)
        - SUM(modelled_fraud_loss)
        - SUM(modelled_nonfraud_dispute_loss),
        2
    ) AS net_revenue,

    ROUND(
        SUM(
            CASE
                WHEN MONTH(transaction_timestamp) <= 6
                THEN approved_amount
                ELSE 0
            END
        ),
        2
    ) AS first_half_volume,

    ROUND(
        SUM(
            CASE
                WHEN MONTH(transaction_timestamp) >= 7
                THEN approved_amount
                ELSE 0
            END
        ),
        2
    ) AS second_half_volume,

    ROUND(
        100.0 * (
            SUM(
                CASE
                    WHEN MONTH(transaction_timestamp) >= 7
                    THEN approved_amount
                    ELSE 0
                END
            )
            -
            SUM(
                CASE
                    WHEN MONTH(transaction_timestamp) <= 6
                    THEN approved_amount
                    ELSE 0
                END
            )
        )
        /
        NULLIF(
            SUM(
                CASE
                    WHEN MONTH(transaction_timestamp) <= 6
                    THEN approved_amount
                    ELSE 0
                END
            ),
            0
        ),
        2
    ) AS volume_growth_pct

FROM vw_payment_enriched

GROUP BY
    merchant_id,
    merchant_name,
    industry,
    merchant_country,
    merchant_size,
    merchant_risk_category,
    currency;
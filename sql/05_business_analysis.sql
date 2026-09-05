USE paymentguard;

-- =====================================================
-- QUERY 1: OVERALL PAYMENT PERFORMANCE
-- =====================================================

SELECT
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
    ) AS net_revenue

FROM vw_payment_enriched

GROUP BY currency

ORDER BY currency;

-- =====================================================
-- QUERY 2: MONTHLY PAYMENT PERFORMANCE
-- =====================================================

SELECT
    transaction_month,
    currency,
    total_attempts,
    approved_payments,
    declined_payments,
    approval_rate_pct,
    approved_volume,
    fraud_payments,
    fraud_rate_pct,
    disputed_payments,
    dispute_rate_pct,
    gross_processing_revenue,

    ROUND(
        fraud_losses + nonfraud_dispute_losses,
        2
    ) AS total_losses,

    net_revenue

FROM vw_monthly_performance

ORDER BY
    transaction_month,
    currency;




-- =====================================================
-- QUERY 4: PAYMENT PERFORMANCE BY MERCHANT COUNTRY
-- =====================================================

SELECT
    merchant_country,
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
    ) AS net_revenue

FROM vw_payment_enriched

GROUP BY
    merchant_country,
    currency

ORDER BY
    approved_volume DESC;







-- =====================================================
-- QUERY 5: MERCHANT PROFITABILITY RANKING
-- =====================================================

SELECT
    merchant_id,
    merchant_name,
    industry,
    merchant_country,
    currency,
    total_attempts,
    approval_rate_pct,
    approved_volume,
    fraud_rate_pct,
    dispute_rate_pct,
    gross_processing_revenue,
    total_losses,
    net_revenue,
    volume_growth_pct

FROM vw_merchant_performance

ORDER BY
    currency,
    net_revenue DESC;





























     -- =====================================================
-- QUERY 6: FRAUD RATE BY INDUSTRY
-- =====================================================

SELECT
    industry,
    currency,

    SUM(approved_flag) AS approved_payments,

    SUM(confirmed_fraud = 1) AS fraud_payments,

    ROUND(
        100.0 * SUM(confirmed_fraud = 1)
        / NULLIF(SUM(approved_flag), 0),
        2
    ) AS fraud_rate_pct,

    ROUND(
        SUM(modelled_fraud_loss),
        2
    ) AS fraud_losses

FROM vw_payment_enriched

GROUP BY
    industry,
    currency

ORDER BY
    currency,
    fraud_rate_pct DESC;








-- =====================================================
-- QUERY 6: FRAUD RATE BY INDUSTRY
-- =====================================================

SELECT
    industry,
    currency,

    SUM(approved_flag) AS approved_payments,

    SUM(confirmed_fraud = 1) AS fraud_payments,

    ROUND(
        100.0 * SUM(confirmed_fraud = 1)
        / NULLIF(SUM(approved_flag), 0),
        2
    ) AS fraud_rate_pct,

    ROUND(
        SUM(modelled_fraud_loss),
        2
    ) AS fraud_losses

FROM vw_payment_enriched

GROUP BY
    industry,
    currency

ORDER BY
    currency,
    fraud_rate_pct DESC;


















-- =====================================================
-- QUERY 7: DISPUTE RATE BY INDUSTRY
-- =====================================================

SELECT
    industry,
    currency,

    SUM(approved_flag) AS approved_payments,

    SUM(has_dispute) AS disputed_payments,

    ROUND(
        100.0 * SUM(has_dispute)
        / NULLIF(SUM(approved_flag), 0),
        2
    ) AS dispute_rate_pct,

    ROUND(
        SUM(COALESCE(net_dispute_loss, 0)),
        2
    ) AS net_dispute_losses

FROM vw_payment_enriched

GROUP BY
    industry,
    currency

ORDER BY
    currency,
    dispute_rate_pct DESC;

-- =====================================================
-- QUERY 8: RISK OF NEW CUSTOMERS
-- =====================================================

SELECT
    CASE
        WHEN is_new_customer = 1 THEN 'New Customer'
        ELSE 'Existing Customer'
    END AS customer_status,

    COUNT(*) AS total_attempts,

    SUM(approved_flag) AS approved_payments,

    ROUND(
        100.0 * SUM(approved_flag) / NULLIF(COUNT(*), 0),
        2
    ) AS approval_rate_pct,

    ROUND(
        AVG(risk_score),
        2
    ) AS average_risk_score,

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
    ) AS dispute_rate_pct

FROM vw_payment_enriched

GROUP BY is_new_customer

ORDER BY is_new_customer DESC;

-- =====================================================
-- QUERY 9: RISK OF NEW DEVICES
-- =====================================================

SELECT
    CASE
        WHEN is_new_device = 1 THEN 'New Device'
        ELSE 'Known Device'
    END AS device_status,

    COUNT(*) AS total_attempts,

    SUM(approved_flag) AS approved_payments,

    ROUND(
        100.0 * SUM(approved_flag) / NULLIF(COUNT(*), 0),
        2
    ) AS approval_rate_pct,

    ROUND(
        AVG(risk_score),
        2
    ) AS average_risk_score,

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
    ) AS dispute_rate_pct

FROM vw_payment_enriched

GROUP BY is_new_device

ORDER BY is_new_device DESC;

-- =====================================================
-- QUERY 10: COUNTRY MISMATCH RISK
-- =====================================================

SELECT
    CASE
        WHEN country_mismatch_flag = 1 THEN 'Country Mismatch'
        ELSE 'Countries Match'
    END AS country_match_status,

    COUNT(*) AS total_attempts,

    SUM(approved_flag) AS approved_payments,

    ROUND(
        100.0 * SUM(approved_flag) / NULLIF(COUNT(*), 0),
        2
    ) AS approval_rate_pct,

    ROUND(
        AVG(risk_score),
        2
    ) AS average_risk_score,

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
    ) AS dispute_rate_pct

FROM vw_payment_enriched

GROUP BY country_mismatch_flag

ORDER BY country_mismatch_flag DESC;

-- =====================================================
-- QUERY 11: AUTHENTICATION PERFORMANCE
-- =====================================================

SELECT
    CASE
        WHEN authentication_used = 1 THEN 'Authentication Used'
        ELSE 'Authentication Not Used'
    END AS authentication_status,

    authentication_result,

    COUNT(*) AS total_attempts,

    SUM(approved_flag) AS approved_payments,

    ROUND(
        100.0 * SUM(approved_flag) / NULLIF(COUNT(*), 0),
        2
    ) AS approval_rate_pct,

    ROUND(
        AVG(risk_score),
        2
    ) AS average_risk_score,

    SUM(confirmed_fraud = 1) AS fraud_payments,

    ROUND(
        100.0 * SUM(confirmed_fraud = 1)
        / NULLIF(SUM(approved_flag), 0),
        2
    ) AS fraud_rate_pct

FROM vw_payment_enriched

GROUP BY
    authentication_used,
    authentication_result

ORDER BY
    authentication_used DESC,
    authentication_result;

    -- =====================================================
-- QUERY 12: PAYMENT METHOD PERFORMANCE
-- =====================================================

SELECT
    payment_method,

    COUNT(*) AS total_attempts,

    SUM(approved_flag) AS approved_payments,

    SUM(declined_flag) AS declined_payments,

    ROUND(
        100.0 * SUM(approved_flag) / NULLIF(COUNT(*), 0),
        2
    ) AS approval_rate_pct,

    ROUND(
        AVG(risk_score),
        2
    ) AS average_risk_score,

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
    ) AS dispute_rate_pct

FROM vw_payment_enriched

GROUP BY payment_method

ORDER BY approval_rate_pct DESC;

-- =====================================================
-- QUERY 13: MONTHLY FRAUD TREND
-- =====================================================

SELECT
    transaction_month,

    COUNT(*) AS total_attempts,

    SUM(approved_flag) AS approved_payments,

    SUM(confirmed_fraud = 1) AS fraud_payments,

    ROUND(
        100.0 * SUM(confirmed_fraud = 1)
        / NULLIF(SUM(approved_flag), 0),
        2
    ) AS fraud_rate_pct,

    ROUND(
        AVG(risk_score),
        2
    ) AS average_risk_score

FROM vw_payment_enriched

GROUP BY transaction_month

ORDER BY transaction_month;

-- =====================================================
-- QUERY 14: UNUSUAL MERCHANT PERFORMANCE CHANGES
-- =====================================================

SELECT
    merchant_id,
    merchant_name,
    industry,
    currency,

    SUM(
        CASE
            WHEN MONTH(transaction_timestamp) <= 9 THEN 1
            ELSE 0
        END
    ) AS jan_to_sep_attempts,

    ROUND(
        100.0 * SUM(
            CASE
                WHEN MONTH(transaction_timestamp) <= 9
                     AND approved_flag = 1
                THEN 1
                ELSE 0
            END
        )
        /
        NULLIF(
            SUM(
                CASE
                    WHEN MONTH(transaction_timestamp) <= 9 THEN 1
                    ELSE 0
                END
            ),
            0
        ),
        2
    ) AS jan_to_sep_approval_rate_pct,

    SUM(
        CASE
            WHEN MONTH(transaction_timestamp) >= 10 THEN 1
            ELSE 0
        END
    ) AS oct_to_dec_attempts,

    ROUND(
        100.0 * SUM(
            CASE
                WHEN MONTH(transaction_timestamp) >= 10
                     AND approved_flag = 1
                THEN 1
                ELSE 0
            END
        )
        /
        NULLIF(
            SUM(
                CASE
                    WHEN MONTH(transaction_timestamp) >= 10 THEN 1
                    ELSE 0
                END
            ),
            0
        ),
        2
    ) AS oct_to_dec_approval_rate_pct,

    ROUND(
        (
            100.0 * SUM(
                CASE
                    WHEN MONTH(transaction_timestamp) >= 10
                         AND approved_flag = 1
                    THEN 1
                    ELSE 0
                END
            )
            /
            NULLIF(
                SUM(
                    CASE
                        WHEN MONTH(transaction_timestamp) >= 10 THEN 1
                        ELSE 0
                    END
                ),
                0
            )
        )
        -
        (
            100.0 * SUM(
                CASE
                    WHEN MONTH(transaction_timestamp) <= 9
                         AND approved_flag = 1
                    THEN 1
                    ELSE 0
                END
            )
            /
            NULLIF(
                SUM(
                    CASE
                        WHEN MONTH(transaction_timestamp) <= 9 THEN 1
                        ELSE 0
                    END
                ),
                0
            )
        ),
        2
    ) AS approval_rate_change_pct_points

FROM vw_payment_enriched

GROUP BY
    merchant_id,
    merchant_name,
    industry,
    currency

HAVING
    jan_to_sep_attempts >= 30
    AND oct_to_dec_attempts >= 10

ORDER BY approval_rate_change_pct_points ASC

LIMIT 20;

-- =====================================================
-- QUERY 15: MERCHANTS REQUIRING INVESTIGATION
-- =====================================================

SELECT
    merchant_id,
    merchant_name,
    industry,
    merchant_country,
    currency,
    total_attempts,
    approval_rate_pct,
    fraud_rate_pct,
    dispute_rate_pct,
    approved_volume,
    gross_processing_revenue,
    total_losses,
    net_revenue,
    volume_growth_pct,

    CASE
        WHEN net_revenue < 0
            THEN 'Unprofitable'

        WHEN fraud_rate_pct >= 2
             OR dispute_rate_pct >= 2
            THEN 'High Risk'

        WHEN approval_rate_pct < 85
            THEN 'Low Approval'

        WHEN volume_growth_pct <= -20
            THEN 'Declining Volume'

        ELSE 'No Immediate Concern'
    END AS investigation_reason

FROM vw_merchant_performance

WHERE
    net_revenue < 0
    OR fraud_rate_pct >= 2
    OR dispute_rate_pct >= 2
    OR approval_rate_pct < 85
    OR volume_growth_pct <= -20

ORDER BY
    CASE
        WHEN net_revenue < 0 THEN 1
        WHEN fraud_rate_pct >= 2
             OR dispute_rate_pct >= 2 THEN 2
        WHEN approval_rate_pct < 85 THEN 3
        WHEN volume_growth_pct <= -20 THEN 4
        ELSE 5
    END,
    net_revenue ASC;

-- =====================================================
-- FINANCIAL RECONCILIATION CHECK
-- =====================================================

WITH financial_totals AS (
    SELECT
        currency,

        SUM(gross_processing_revenue) AS gross_revenue,

        SUM(
            modelled_fraud_loss
            + modelled_nonfraud_dispute_loss
        ) AS total_losses,

        SUM(
            gross_processing_revenue
            - modelled_fraud_loss
            - modelled_nonfraud_dispute_loss
        ) AS net_revenue

    FROM vw_payment_enriched

    GROUP BY currency
)

SELECT
    currency,

    ROUND(gross_revenue, 2) AS gross_revenue,

    ROUND(total_losses, 2) AS total_losses,

    ROUND(net_revenue, 2) AS net_revenue,

    ROUND(
        gross_revenue - total_losses - net_revenue,
        2
    ) AS reconciliation_difference

FROM financial_totals

ORDER BY currency;
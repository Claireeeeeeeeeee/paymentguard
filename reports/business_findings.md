# PaymentGuard: Business Findings and Recommendations

## Executive Summary

PaymentGuard analyses 50,000 synthetic payments across merchant, customer, device, geography and dispute data. The project evaluates payment acceptance, fraud exposure and merchant profitability through Python validation, SQL analytics and four interactive Tableau dashboards.

The dataset achieved an overall approval rate of 88.94%, with 44,471 authorised payments. However, the GBP portfolio generated approximately £31,443 in gross processing revenue while incurring approximately £59,934 in fraud and dispute losses, producing net revenue of approximately -£28,491. This indicates that transaction growth alone does not guarantee sustainable payment economics.

## Key Findings

### 1. Strong payment volume did not produce positive profitability

The GBP portfolio generated:

- Approved volume: £2,140,484
- Gross processing revenue: £31,443
- Estimated fraud and dispute losses: £59,934
- Net revenue: -£28,491

Losses were approximately 1.9 times gross processing revenue. Risk costs therefore consumed all processing revenue and created a material negative contribution.

### 2. Travel was the principal industry-level loss driver

Travel generated substantially more negative net revenue than the other industries. Several other industries were close to break-even, while Travel contributed most of the portfolio’s negative result.

This indicates a need for industry-specific risk controls, pricing and reserve policies rather than applying a single commercial model to every merchant.

### 3. October produced a clear fraud-loss anomaly

Monthly fraud losses peaked at approximately £6,200 in October, significantly above the other months. The spike was not accompanied by an equally large change in the general approval-rate trend.

This suggests a concentrated fraud event, merchant issue or change in transaction mix that should trigger an operational investigation.

### 4. Country mismatch was a strong fraud indicator

Transactions with a country mismatch recorded a fraud rate of approximately 1.6%, compared with approximately 0.6% for transactions without a mismatch.

Country-mismatch payments were therefore around 2.7 times as likely to be confirmed as fraudulent. The signal is useful for risk scoring, although it should support additional authentication rather than automatic rejection.

### 5. New devices carried materially higher risk

Payments made from new devices recorded approximately 1.3% fraud, compared with approximately 0.7% for familiar devices.

This represents close to a 1.9-times increase in risk and supports the use of device history, step-up authentication and velocity checks in payment decisioning.

### 6. New customers experienced the lowest approval rate

Approval rates by customer segment were approximately:

- Returning: 89.9%
- Occasional: 89.6%
- Loyal: 89.3%
- New: 86.8%

New customers underperformed returning customers by approximately 3.1 percentage points. This may reflect limited behavioural history, stronger risk controls or weaker authentication completion.

### 7. Bank transfer achieved the strongest payment-method approval rate

Approval rates by payment method were approximately:

- Bank transfer: 90.8%
- Digital wallet: 88.9%
- Card: 88.7%

The difference is moderate but commercially meaningful at scale. Further analysis should separate issuer declines, authentication failures and internal risk decisions.

### 8. Risk decisions and authorisation outcomes were not identical

The decision layer produced:

- Approve: 47,984
- Review: 1,930
- Block: 86

However, only 44,471 payments were ultimately authorised. An internal “Approve” decision therefore did not guarantee a successful authorisation.

This distinction is important because payment performance should separate internal risk decisions from downstream issuer or payment-network outcomes.

### 9. High growth did not guarantee merchant profitability

Synthetic Merchant 023 illustrates this problem:

- Volume growth: 106.7%
- Approved volume: approximately £957,489
- Fraud rate: 1.0%
- Gross processing revenue: £13,759
- Total losses: £32,955
- Net revenue: -£19,196
- Merchant category: Unprofitable

This merchant generated substantial volume and growth but destroyed value after losses. Merchant management should therefore combine growth, revenue and risk metrics instead of prioritising volume alone.

## Recommendations

1. Investigate the October fraud-loss spike by merchant, country, device and payment method.

2. Review Travel merchants individually and consider stronger onboarding, reserves, pricing or enhanced monitoring.

3. Apply step-up authentication when country mismatch, new-device and high-velocity signals occur together.

4. Create dedicated monitoring for new-customer approval rates and authentication failures.

5. Separate internal risk decisions from final authorisation outcomes in operational reporting.

6. Introduce alerts for sudden changes in fraud losses, approval rates and merchant profitability.

7. Use the merchant categories—Strategic, Growing, Monitor, High Risk and Unprofitable—to prioritise commercial and risk actions.

8. Evaluate fraud controls using both fraud reduction and approval-rate impact to avoid excessive false positives.

## Analytical Scope and Limitations

The project uses synthetic data generated for portfolio development rather than real Stripe or merchant data. The results demonstrate analytical and data-engineering methods but should not be interpreted as evidence about Stripe’s actual business performance.

Transaction counts and overall rates cover the complete synthetic dataset. GBP financial values are reported separately to avoid adding monetary amounts across currencies without foreign-exchange conversion.

The analysis identifies associations rather than causal relationships. A production implementation would require historical model evaluation, false-positive analysis, exchange-rate treatment, cohort analysis and controlled testing of risk-policy changes.
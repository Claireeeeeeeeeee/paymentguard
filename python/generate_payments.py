from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import pandas as pd


# ==================================================
# STEPS 10–12: BASIC SETTINGS
# ==================================================

rng = np.random.default_rng(44)

transaction_start = pd.Timestamp("2025-01-01 00:00:00")
transaction_end = pd.Timestamp("2025-12-31 23:59:59")
number_of_payments = 50_000

project_folder = Path(__file__).resolve().parents[1]
raw_data_folder = project_folder / "data" / "raw"

merchants = pd.read_csv(
    raw_data_folder / "merchants.csv",
    parse_dates=["onboarding_date"]
)

customers = pd.read_csv(
    raw_data_folder / "customers.csv",
    parse_dates=["account_created_at"]
)

merchant_lookup = merchants.set_index("merchant_id")
customer_lookup = customers.set_index("customer_id")

merchant_ids = merchants["merchant_id"].to_numpy()
customer_ids = customers["customer_id"].to_numpy()

merchant_weights = np.sqrt(
    merchants["expected_monthly_volume"].to_numpy()
)
merchant_weights = merchant_weights / merchant_weights.sum()

payment_methods = [
    "Card",
    "Digital Wallet",
    "Bank Transfer"
]

card_types = [
    "Debit",
    "Credit"
]

card_networks = [
    "Visa",
    "Mastercard",
    "Amex"
]

device_types = [
    "Mobile",
    "Desktop",
    "Tablet"
]

industry_amount_ranges = {
    "Food Delivery": (15, 60),
    "Fashion": (30, 200),
    "Electronics": (50, 1500),
    "Travel": (100, 2000),
    "Digital Products": (5, 150),
    "Gaming": (5, 100),
    "Subscription Software": (10, 500),
    "Ticketing": (20, 500),
    "Marketplace": (10, 1000)
}

country_currency = {
    "GB": "GBP",
    "US": "USD",
    "FR": "EUR",
    "DE": "EUR",
    "NL": "EUR",
    "IE": "EUR",
    "ES": "EUR",
    "IT": "EUR",
    "CA": "CAD",
    "AU": "AUD"
}

all_countries = list(country_currency.keys())


# ==================================================
# STEP 13: SEASONAL TRANSACTION PATTERNS
# ==================================================

calendar_days = pd.date_range(
    transaction_start.normalize(),
    transaction_end.normalize(),
    freq="D"
)

month_weights = {
    1: 0.82,
    2: 0.85,
    3: 0.90,
    4: 0.95,
    5: 1.00,
    6: 1.05,
    7: 1.10,
    8: 1.08,
    9: 1.00,
    10: 1.08,
    11: 1.35,
    12: 1.45
}

industry_day_cumulative_weights = {}

for industry in industry_amount_ranges:
    weights = np.array(
        [month_weights[day.month] for day in calendar_days],
        dtype=float
    )

    # Travel has stronger summer demand.
    if industry == "Travel":
        weights[
            np.isin(calendar_days.month, [6, 7, 8])
        ] *= 1.60

    # Gaming and digital products rise near year-end.
    if industry in {"Gaming", "Digital Products"}:
        weights[
            np.isin(calendar_days.month, [11, 12])
        ] *= 1.35

    # Ticket sales rise during spring and summer.
    if industry == "Ticketing":
        weights[
            np.isin(calendar_days.month, [5, 6, 7, 8])
        ] *= 1.35

    # Weekend effects.
    weekend_mask = calendar_days.dayofweek >= 5

    if industry == "Food Delivery":
        weights[weekend_mask] *= 1.30

    if industry == "Gaming":
        weights[weekend_mask] *= 1.15

    # Black Friday 2025.
    black_friday_mask = (
        calendar_days == pd.Timestamp("2025-11-28")
    )
    weights[black_friday_mask] *= 4.0

    industry_day_cumulative_weights[industry] = np.cumsum(
        weights
    )


def generate_timestamp(industry, earliest_date):
    """Generate a seasonal timestamp after account creation."""

    earliest_date = max(
        pd.Timestamp(earliest_date),
        transaction_start
    )

    earliest_day_number = (
        earliest_date.normalize()
        - transaction_start.normalize()
    ).days

    earliest_day_number = max(0, earliest_day_number)
    earliest_day_number = min(
        earliest_day_number,
        len(calendar_days) - 1
    )

    cumulative_weights = (
        industry_day_cumulative_weights[industry]
    )

    if earliest_day_number == 0:
        lower_limit = 0
    else:
        lower_limit = cumulative_weights[
            earliest_day_number - 1
        ]

    random_weight = rng.uniform(
        lower_limit,
        cumulative_weights[-1]
    )

    selected_day_number = int(
        np.searchsorted(
            cumulative_weights,
            random_weight
        )
    )

    selected_day = calendar_days[selected_day_number]
    random_seconds = int(rng.integers(0, 86_400))

    return selected_day + pd.Timedelta(
        seconds=random_seconds
    )


# ==================================================
# GENERATE THE FOUNDATION RECORDS
# ==================================================

payment_records = []

for number in range(1, number_of_payments + 1):
    payment_id = f"P{number:07d}"

    merchant_id = str(
        rng.choice(
            merchant_ids,
            p=merchant_weights
        )
    )

    merchant = merchant_lookup.loc[merchant_id]
    industry = merchant["industry"]
    merchant_country = merchant["merchant_country"]

    # Create some repeated customer attempts so velocity can
    # be measured meaningfully.
    repeated_attempt = (
        len(payment_records) > 0
        and rng.random() < 0.06
    )

    if repeated_attempt:
        earlier_payment = payment_records[
            int(
                rng.integers(
                    max(0, len(payment_records) - 250),
                    len(payment_records)
                )
            )
        ]

        customer_id = earlier_payment["customer_id"]
        customer = customer_lookup.loc[customer_id]

        candidate_timestamp = (
            earlier_payment["transaction_timestamp"]
            + pd.Timedelta(
                minutes=int(rng.integers(1, 46))
            )
        )

        if candidate_timestamp <= transaction_end:
            transaction_timestamp = candidate_timestamp
        else:
            transaction_timestamp = generate_timestamp(
                industry,
                customer["account_created_at"]
            )
    else:
        customer_id = str(rng.choice(customer_ids))
        customer = customer_lookup.loc[customer_id]

        transaction_timestamp = generate_timestamp(
            industry,
            customer["account_created_at"]
        )

    customer_country = customer["customer_country"]

    minimum_amount, maximum_amount = (
        industry_amount_ranges[industry]
    )

    amount_position = rng.beta(a=1.5, b=5.0)

    amount = round(
        minimum_amount
        + amount_position
        * (maximum_amount - minimum_amount),
        2
    )

    amount = max(minimum_amount, amount)
    amount = min(maximum_amount, amount)

    currency = country_currency[merchant_country]

    processing_fee = round(
        amount * 0.014 + 0.20,
        2
    )

    payment_method = str(
        rng.choice(
            payment_methods,
            p=[0.72, 0.20, 0.08]
        )
    )

    if payment_method == "Bank Transfer":
        card_type = "Not Applicable"
        card_network = "Not Applicable"
    else:
        card_type = str(
            rng.choice(
                card_types,
                p=[0.60, 0.40]
            )
        )

        card_network = str(
            rng.choice(
                card_networks,
                p=[0.50, 0.42, 0.08]
            )
        )

    billing_country = (
        customer_country
        if rng.random() < 0.92
        else str(rng.choice(all_countries))
    )

    issuer_country = (
        billing_country
        if rng.random() < 0.90
        else str(rng.choice(all_countries))
    )

    ip_country = (
        billing_country
        if rng.random() < 0.88
        else str(rng.choice(all_countries))
    )

    device_type = str(
        rng.choice(
            device_types,
            p=[0.62, 0.31, 0.07]
        )
    )

    customer_age_days = (
        transaction_timestamp
        - customer["account_created_at"]
    ).days

    is_new_customer = int(
        customer_age_days <= 90
        or customer["historical_orders"] == 0
    )

    new_device_probability = (
        0.30 if is_new_customer == 1 else 0.12
    )

    is_new_device = int(
        rng.random() < new_device_probability
    )

    if is_new_device == 1:
        device_id = (
            f"NEWDEV{int(rng.integers(1, 1_000_000)):06d}"
        )
    else:
        device_id = customer["usual_device_id"]

    payment_records.append(
        {
            "payment_id": payment_id,
            "transaction_timestamp": transaction_timestamp,
            "merchant_id": merchant_id,
            "customer_id": customer_id,
            "amount": amount,
            "currency": currency,
            "processing_fee": processing_fee,
            "payment_method": payment_method,
            "card_type": card_type,
            "card_network": card_network,
            "issuer_country": issuer_country,
            "billing_country": billing_country,
            "ip_country": ip_country,
            "device_type": device_type,
            "device_id": device_id,
            "is_new_device": is_new_device,
            "is_new_customer": is_new_customer
        }
    )

payments = pd.DataFrame(payment_records)

payments = payments.sort_values(
    "transaction_timestamp"
).reset_index(drop=True)


# ==================================================
# STEP 14: RISK INDICATORS
# ==================================================

merchant_country_series = payments["merchant_id"].map(
    merchant_lookup["merchant_country"]
)

payments["is_cross_border"] = (
    payments["issuer_country"]
    != merchant_country_series
).astype(int)

payments["country_mismatch_flag"] = (
    (payments["issuer_country"] != payments["billing_country"])
    | (payments["ip_country"] != payments["billing_country"])
).astype(int)


# Count attempts from the same customer within the previous hour.
customer_windows = defaultdict(deque)
velocity_values = []

for row in payments.itertuples():
    customer_window = customer_windows[row.customer_id]
    one_hour_before = (
        row.transaction_timestamp
        - pd.Timedelta(hours=1)
    )

    while (
        customer_window
        and customer_window[0] < one_hour_before
    ):
        customer_window.popleft()

    customer_window.append(row.transaction_timestamp)
    velocity_values.append(len(customer_window))

payments["velocity_1h"] = velocity_values


# ==================================================
# STEP 15: AUTHENTICATION
# ==================================================

merchant_risk = payments["merchant_id"].map(
    merchant_lookup["risk_category"]
)

payment_industry = payments["merchant_id"].map(
    merchant_lookup["industry"]
)

historical_chargebacks = payments["customer_id"].map(
    customer_lookup["historical_chargebacks"]
)

maximum_amount = payment_industry.map(
    {
        industry: limits[1]
        for industry, limits in industry_amount_ranges.items()
    }
)

high_amount_flag = (
    payments["amount"] > maximum_amount * 0.65
).astype(int)

risk_category_points = merchant_risk.map(
    {
        "Low": 0,
        "Medium": 8,
        "High": 16
    }
)

high_risk_industry_flag = payment_industry.isin(
    [
        "Gaming",
        "Electronics",
        "Ticketing",
        "Travel",
        "Digital Products"
    ]
).astype(int)

october_flag = (
    payments["transaction_timestamp"].dt.month == 10
).astype(int)

risk_score = (
    5
    + risk_category_points
    + payments["is_new_device"] * 15
    + payments["is_new_customer"] * 8
    + payments["is_cross_border"] * 7
    + payments["country_mismatch_flag"] * 20
    + (payments["velocity_1h"] >= 3).astype(int) * 18
    + (historical_chargebacks > 0).astype(int) * 12
    + high_amount_flag * 8
    + high_risk_industry_flag * 5
    + october_flag * high_risk_industry_flag * 5
    + rng.normal(0, 5, len(payments))
)

payments["risk_score"] = (
    np.clip(risk_score, 0, 100)
    .round()
    .astype(int)
)

authentication_eligible = (
    payments["payment_method"] != "Bank Transfer"
)

payments["authentication_used"] = (
    authentication_eligible
    & (
        (payments["risk_score"] >= 30)
        | (rng.random(len(payments)) < 0.45)
    )
).astype(int)

authentication_success_probability = (
    0.97
    - payments["is_new_device"] * 0.10
    - payments["country_mismatch_flag"] * 0.16
    - np.maximum(
        payments["risk_score"] - 40,
        0
    ) * 0.003
)

# M00024 develops authentication friction after September.
problem_merchant_period = (
    (payments["merchant_id"] == "M00024")
    & (
        payments["transaction_timestamp"]
        >= pd.Timestamp("2025-10-01")
    )
)

authentication_success_probability = (
    authentication_success_probability
    - problem_merchant_period.astype(int) * 0.30
)

authentication_success_probability = np.clip(
    authentication_success_probability,
    0.25,
    0.99
)

authentication_success = (
    rng.random(len(payments))
    < authentication_success_probability
)

payments["authentication_result"] = "Not Attempted"

payments.loc[
    payments["authentication_used"] == 1,
    "authentication_result"
] = "Failed"

payments.loc[
    (payments["authentication_used"] == 1)
    & authentication_success,
    "authentication_result"
] = "Successful"


# ==================================================
# STEP 16: PAYMENT DECISION
# ==================================================

payments["decision"] = "Approve"

payments.loc[
    payments["risk_score"].between(60, 79),
    "decision"
] = "Review"

payments.loc[
    payments["risk_score"] >= 80,
    "decision"
] = "Block"


# ==================================================
# STEP 17: AUTHORISATION AND DECLINE REASONS
# ==================================================

approval_probability = (
    0.975
    - payments["risk_score"] * 0.002
    - (
        payments["authentication_result"] == "Failed"
    ).astype(int) * 0.48
    + (
        payments["authentication_result"] == "Successful"
    ).astype(int) * 0.02
    - problem_merchant_period.astype(int) * 0.12
)

approval_probability = np.clip(
    approval_probability,
    0.03,
    0.995
)

approved = (
    rng.random(len(payments))
    < approval_probability
)

approved = approved & (
    payments["decision"] != "Block"
)

payments["authorisation_status"] = np.where(
    approved,
    "Approved",
    "Declined"
)

payments["decline_reason"] = "Not Applicable"

declined = (
    payments["authorisation_status"] == "Declined"
)

payments.loc[
    declined,
    "decline_reason"
] = "Issuer Decline"

payments.loc[
    declined & (payments["velocity_1h"] >= 3),
    "decline_reason"
] = "Velocity Limit"

payments.loc[
    declined
    & (payments["authentication_result"] == "Failed"),
    "decline_reason"
] = "Authentication Failed"

payments.loc[
    declined & (payments["decision"] == "Block"),
    "decline_reason"
] = "Risk Block"

# Add a small number of ordinary issuer/card declines.
ordinary_declines = (
    declined
    & (payments["decline_reason"] == "Issuer Decline")
)

ordinary_decline_reasons = rng.choice(
    [
        "Issuer Decline",
        "Insufficient Funds",
        "Invalid Details"
    ],
    size=ordinary_declines.sum(),
    p=[0.50, 0.35, 0.15]
)

payments.loc[
    ordinary_declines,
    "decline_reason"
] = ordinary_decline_reasons


# ==================================================
# STEP 18: CONFIRMED FRAUD
# ==================================================

fraud_probability = (
    0.001
    + payments["risk_score"] * 0.00010
    + payments["is_new_device"] * 0.003
    + payments["country_mismatch_flag"] * 0.006
    + (payments["velocity_1h"] >= 3).astype(int) * 0.005
    + high_risk_industry_flag * 0.002
)

# Deliberate October fraud anomaly for later investigation.
october_high_risk = (
    (payments["transaction_timestamp"].dt.month == 10)
    & (high_risk_industry_flag == 1)
)

fraud_probability = (
    fraud_probability
    + october_high_risk.astype(int) * 0.020
)

fraud_probability = np.clip(
    fraud_probability,
    0,
    0.20
)

payments["confirmed_fraud"] = (
    (
        rng.random(len(payments))
        < fraud_probability
    )
    & approved
).astype(int)


# ==================================================
# STEP 19: REFUND OUTCOMES
# ==================================================

payments["refund_status"] = "Not Refunded"

ordinary_full_refund = (
    approved
    & (rng.random(len(payments)) < 0.018)
)

ordinary_partial_refund = (
    approved
    & ~ordinary_full_refund
    & (rng.random(len(payments)) < 0.010)
)

payments.loc[
    ordinary_full_refund,
    "refund_status"
] = "Fully Refunded"

payments.loc[
    ordinary_partial_refund,
    "refund_status"
] = "Partially Refunded"

fraud_rows = payments["confirmed_fraud"] == 1
fraud_refund_random = rng.random(len(payments))

payments.loc[
    fraud_rows & (fraud_refund_random < 0.75),
    "refund_status"
] = "Fully Refunded"

payments.loc[
    fraud_rows
    & (fraud_refund_random >= 0.75)
    & (fraud_refund_random < 0.90),
    "refund_status"
] = "Partially Refunded"


# ==================================================
# SAVE THE COMPLETE PAYMENT DATASET
# ==================================================

required_columns = [
    "payment_id",
    "transaction_timestamp",
    "merchant_id",
    "customer_id",
    "amount",
    "currency",
    "processing_fee",
    "payment_method",
    "card_type",
    "card_network",
    "issuer_country",
    "billing_country",
    "ip_country",
    "device_type",
    "device_id",
    "is_new_device",
    "is_new_customer",
    "is_cross_border",
    "country_mismatch_flag",
    "velocity_1h",
    "authentication_used",
    "authentication_result",
    "risk_score",
    "decision",
    "authorisation_status",
    "decline_reason",
    "confirmed_fraud",
    "refund_status"
]

payments = payments[required_columns]

output_file = raw_data_folder / "payments.csv"

payments.to_csv(
    output_file,
    index=False,
    date_format="%Y-%m-%d %H:%M:%S"
)


# ==================================================
# VALIDATE STEPS 13–19
# ==================================================

print(f"\nCreated: {output_file}")
print("Dataset shape:", payments.shape)

print(
    "Duplicate payment IDs:",
    payments["payment_id"].duplicated().sum()
)

print(
    "Missing values:",
    int(payments.isna().sum().sum())
)

print(
    "All amounts positive:",
    (payments["amount"] > 0).all()
)

print(
    "All risk scores valid:",
    payments["risk_score"].between(0, 100).all()
)

print(
    "All timestamps are in 2025:",
    payments["transaction_timestamp"]
    .between(transaction_start, transaction_end)
    .all()
)

print("\nAuthorisation results:")
print(
    payments["authorisation_status"]
    .value_counts()
)

print("\nAuthentication results:")
print(
    payments["authentication_result"]
    .value_counts()
)

print("\nConfirmed fraud:")
print(
    payments["confirmed_fraud"]
    .value_counts()
)

print("\nRefund results:")
print(
    payments["refund_status"]
    .value_counts()
)

monthly_summary = (
    payments.assign(
        month=payments[
            "transaction_timestamp"
        ].dt.to_period("M")
    )
    .groupby("month")
    .agg(
        attempts=("payment_id", "count"),
        approval_rate=(
            "authorisation_status",
            lambda values: (
                values == "Approved"
            ).mean()
        ),
        fraud_rate=(
            "confirmed_fraud",
            "mean"
        )
    )
)

print("\nMonthly summary:")
print(monthly_summary.round(4))

merchant_24 = payments[
    payments["merchant_id"] == "M00024"
].copy()

merchant_24["period"] = np.where(
    merchant_24["transaction_timestamp"]
    < pd.Timestamp("2025-10-01"),
    "Jan-Sep",
    "Oct-Dec"
)

merchant_24_summary = (
    merchant_24.groupby("period")
    .agg(
        attempts=("payment_id", "count"),
        approval_rate=(
            "authorisation_status",
            lambda values: (
                values == "Approved"
            ).mean()
        ),
        authentication_failure_rate=(
            "authentication_result",
            lambda values: (
                values == "Failed"
            ).mean()
        ),
        fraud_rate=("confirmed_fraud", "mean")
    )
)

print("\nM00024 before and after September:")
print(merchant_24_summary.round(4))
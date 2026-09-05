from pathlib import Path

import numpy as np
import pandas as pd


# --------------------------------------------------
# 1. Set paths and random seed
# --------------------------------------------------

np.random.seed(42)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

PAYMENTS_FILE = RAW_DATA_DIR / "payments.csv"
CUSTOMERS_FILE = RAW_DATA_DIR / "customers.csv"
MERCHANTS_FILE = RAW_DATA_DIR / "merchants.csv"
OUTPUT_FILE = RAW_DATA_DIR / "disputes.csv"


# --------------------------------------------------
# 2. Load existing datasets
# --------------------------------------------------

payments = pd.read_csv(
    PAYMENTS_FILE,
    parse_dates=["transaction_timestamp"]
)

customers = pd.read_csv(CUSTOMERS_FILE)
merchants = pd.read_csv(MERCHANTS_FILE)

print(f"Payments loaded: {len(payments):,}")
print(f"Customers loaded: {len(customers):,}")
print(f"Merchants loaded: {len(merchants):,}")


# --------------------------------------------------
# 3. Add customer and merchant information
# --------------------------------------------------

payment_candidates = payments.merge(
    customers[
        [
            "customer_id",
            "historical_chargebacks"
        ]
    ],
    on="customer_id",
    how="left",
    validate="many_to_one"
)

payment_candidates = payment_candidates.merge(
    merchants[
        [
            "merchant_id",
            "industry"
        ]
    ],
    on="merchant_id",
    how="left",
    validate="many_to_one"
)


# --------------------------------------------------
# 4. Keep only approved payments
# --------------------------------------------------

approved_payments = payment_candidates[
    payment_candidates["authorisation_status"]
    .astype(str)
    .str.lower()
    .isin(["approved", "authorised", "authorized"])
].copy()

print(f"Approved payments eligible for disputes: {len(approved_payments):,}")

if approved_payments.empty:
    raise ValueError(
        "No approved payments were found. "
        "Check the values in authorisation_status."
    )


# --------------------------------------------------
# 5. Calculate dispute probability
# --------------------------------------------------

approved_payments["dispute_probability"] = 0.006

# Confirmed fraud greatly increases dispute risk
approved_payments.loc[
    approved_payments["confirmed_fraud"] == 1,
    "dispute_probability"
] += 0.35

# Travel and ticketing have greater dispute risk
approved_payments.loc[
    approved_payments["industry"].isin(["Travel", "Ticketing"]),
    "dispute_probability"
] += 0.012

# Cross-border payments are more likely to be disputed
approved_payments.loc[
    approved_payments["is_cross_border"] == 1,
    "dispute_probability"
] += 0.008

# Previous chargebacks increase risk
approved_payments.loc[
    approved_payments["historical_chargebacks"] > 0,
    "dispute_probability"
] += 0.025

# Unusually high amounts increase risk
industry_average = approved_payments.groupby("industry")["amount"].transform(
    "median"
)

approved_payments["unusually_high_amount"] = (
    approved_payments["amount"] > industry_average * 3
).astype(int)

approved_payments.loc[
    approved_payments["unusually_high_amount"] == 1,
    "dispute_probability"
] += 0.015

approved_payments["dispute_probability"] = (
    approved_payments["dispute_probability"]
    .clip(lower=0, upper=0.80)
)


# --------------------------------------------------
# 6. Select disputed payments
# --------------------------------------------------

approved_payments["has_dispute"] = np.random.binomial(
    1,
    approved_payments["dispute_probability"]
)

disputed_payments = approved_payments[
    approved_payments["has_dispute"] == 1
].copy()

print(f"Disputes selected: {len(disputed_payments):,}")


# --------------------------------------------------
# 7. Assign dispute reasons
# --------------------------------------------------

general_reasons = [
    "Product Not Received",
    "Product Unacceptable",
    "Duplicate Payment",
    "Subscription Cancelled",
    "Processing Error"
]


def choose_dispute_reason(row):
    if row["confirmed_fraud"] == 1:
        return np.random.choice(
            ["Fraudulent", "Product Not Received"],
            p=[0.90, 0.10]
        )

    if row["industry"] == "Subscription Software":
        return np.random.choice(
            [
                "Subscription Cancelled",
                "Product Unacceptable",
                "Processing Error"
            ],
            p=[0.60, 0.25, 0.15]
        )

    if row["industry"] in ["Travel", "Ticketing"]:
        return np.random.choice(
            [
                "Product Not Received",
                "Product Unacceptable",
                "Processing Error"
            ],
            p=[0.55, 0.25, 0.20]
        )

    return np.random.choice(general_reasons)


disputed_payments["dispute_reason"] = disputed_payments.apply(
    choose_dispute_reason,
    axis=1
)


# --------------------------------------------------
# 8. Create dispute dates and amounts
# --------------------------------------------------

days_until_dispute = np.random.randint(
    1,
    61,
    size=len(disputed_payments)
)

disputed_payments["dispute_date"] = (
    disputed_payments["transaction_timestamp"].dt.normalize()
    + pd.to_timedelta(days_until_dispute, unit="D")
)

disputed_payments["disputed_amount"] = (
    disputed_payments["amount"].round(2)
)

# Synthetic assumption for educational purposes
disputed_payments["dispute_fee"] = 15.00


# --------------------------------------------------
# 9. Assign dispute status
# --------------------------------------------------

disputed_payments["dispute_status"] = np.random.choice(
    ["Won", "Lost", "Pending"],
    size=len(disputed_payments),
    p=[0.28, 0.57, 0.15]
)

resolved_mask = disputed_payments["dispute_status"].isin(
    ["Won", "Lost"]
)

resolution_days = np.random.randint(
    7,
    46,
    size=resolved_mask.sum()
)

disputed_payments["resolution_date"] = pd.NaT

disputed_payments.loc[
    resolved_mask,
    "resolution_date"
] = (
    disputed_payments.loc[resolved_mask, "dispute_date"]
    + pd.to_timedelta(resolution_days, unit="D")
)


# --------------------------------------------------
# 10. Calculate recovered amount and net loss
# --------------------------------------------------

disputed_payments["recovered_amount"] = 0.00

won_mask = disputed_payments["dispute_status"] == "Won"

disputed_payments.loc[
    won_mask,
    "recovered_amount"
] = disputed_payments.loc[
    won_mask,
    "disputed_amount"
]

disputed_payments["net_dispute_loss"] = (
    disputed_payments["disputed_amount"]
    + disputed_payments["dispute_fee"]
    - disputed_payments["recovered_amount"]
).round(2)


# --------------------------------------------------
# 11. Create dispute IDs
# --------------------------------------------------

disputed_payments = disputed_payments.reset_index(drop=True)

disputed_payments["dispute_id"] = [
    f"D{i:06d}"
    for i in range(1, len(disputed_payments) + 1)
]


# --------------------------------------------------
# 12. Select final columns
# --------------------------------------------------

disputes = disputed_payments[
    [
        "dispute_id",
        "payment_id",
        "dispute_date",
        "dispute_reason",
        "disputed_amount",
        "dispute_fee",
        "dispute_status",
        "resolution_date",
        "recovered_amount",
        "net_dispute_loss"
    ]
].copy()


# --------------------------------------------------
# 13. Validate the dispute data
# --------------------------------------------------

assert disputes["dispute_id"].is_unique
assert disputes["payment_id"].is_unique
assert disputes["disputed_amount"].gt(0).all()
assert disputes["dispute_fee"].ge(0).all()
assert disputes["recovered_amount"].ge(0).all()
assert (
    disputes["recovered_amount"]
    <= disputes["disputed_amount"]
).all()
assert disputes["net_dispute_loss"].ge(0).all()

valid_payment_ids = set(approved_payments["payment_id"])

assert disputes["payment_id"].isin(valid_payment_ids).all()

payment_dates = payments.set_index("payment_id")[
    "transaction_timestamp"
].dt.normalize()

linked_payment_dates = disputes["payment_id"].map(payment_dates)

assert (
    disputes["dispute_date"] > linked_payment_dates
).all()

resolved_disputes = disputes[
    disputes["dispute_status"].isin(["Won", "Lost"])
]

assert resolved_disputes["resolution_date"].notna().all()

assert (
    resolved_disputes["resolution_date"]
    > resolved_disputes["dispute_date"]
).all()

pending_disputes = disputes[
    disputes["dispute_status"] == "Pending"
]

assert pending_disputes["resolution_date"].isna().all()


# --------------------------------------------------
# 14. Save disputes.csv
# --------------------------------------------------

disputes.to_csv(
    OUTPUT_FILE,
    index=False,
    date_format="%Y-%m-%d"
)

print("\nSTEP 23 PASSED: dispute data is valid.")
print(f"Saved: {OUTPUT_FILE}")
print(f"Number of disputes: {len(disputes):,}")
print("\nDispute-status distribution:")
print(disputes["dispute_status"].value_counts())
print("\nDispute-reason distribution:")
print(disputes["dispute_reason"].value_counts())
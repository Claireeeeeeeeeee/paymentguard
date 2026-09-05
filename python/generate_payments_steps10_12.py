from pathlib import Path

import numpy as np
import pandas as pd


# --------------------------------------------------
# STEP 10: DEFINE THE TRANSACTION PERIOD
# --------------------------------------------------

rng = np.random.default_rng(44)

transaction_start = pd.Timestamp("2025-01-01 00:00:00")
transaction_end = pd.Timestamp("2025-12-31 23:59:59")

number_of_payments = 50_000


# --------------------------------------------------
# LOAD MERCHANT AND CUSTOMER DATA
# --------------------------------------------------

project_folder = Path(__file__).resolve().parents[1]
raw_data_folder = project_folder / "data" / "raw"

merchants_file = raw_data_folder / "merchants.csv"
customers_file = raw_data_folder / "customers.csv"

merchants = pd.read_csv(
    merchants_file,
    parse_dates=["onboarding_date"]
)

customers = pd.read_csv(
    customers_file,
    parse_dates=["account_created_at"]
)

print("Merchants loaded:", merchants.shape)
print("Customers loaded:", customers.shape)


# --------------------------------------------------
# DEFINE THE AVAILABLE CATEGORIES
# --------------------------------------------------

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


# --------------------------------------------------
# STEP 12: DEFINE INDUSTRY AMOUNT RANGES
# --------------------------------------------------

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


# Assign a currency according to merchant country.
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


# --------------------------------------------------
# CREATE LOOKUP TABLES
# --------------------------------------------------

merchant_lookup = merchants.set_index("merchant_id")
customer_lookup = customers.set_index("customer_id")

merchant_ids = merchants["merchant_id"].to_numpy()
customer_ids = customers["customer_id"].to_numpy()


# Merchants with more expected volume should receive more payments.
# Square root prevents the largest merchants from dominating too much.
merchant_weights = np.sqrt(
    merchants["expected_monthly_volume"].to_numpy()
)

merchant_weights = merchant_weights / merchant_weights.sum()


# --------------------------------------------------
# GENERATE EACH PAYMENT
# --------------------------------------------------

payment_records = []

for number in range(1, number_of_payments + 1):

    # -----------------------------
    # Payment identifier
    # -----------------------------

    payment_id = f"P{number:07d}"

    # -----------------------------
    # Select merchant and customer
    # -----------------------------

    merchant_id = str(
        rng.choice(
            merchant_ids,
            p=merchant_weights
        )
    )

    customer_id = str(rng.choice(customer_ids))

    merchant = merchant_lookup.loc[merchant_id]
    customer = customer_lookup.loc[customer_id]

    industry = merchant["industry"]
    merchant_country = merchant["merchant_country"]
    customer_country = customer["customer_country"]

    # -----------------------------
    # Generate a valid timestamp
    # -----------------------------

    account_created_at = customer["account_created_at"]

    # A payment cannot happen before the customer account exists.
    possible_start = max(
        transaction_start,
        account_created_at
    )

    available_seconds = int(
        (transaction_end - possible_start).total_seconds()
    )

    random_seconds = int(
        rng.integers(0, available_seconds + 1)
    )

    transaction_timestamp = (
        possible_start
        + pd.Timedelta(seconds=random_seconds)
    )

    # -----------------------------
    # Generate a realistic amount
    # -----------------------------

    minimum_amount, maximum_amount = (
        industry_amount_ranges[industry]
    )

    # Beta produces many smaller payments and fewer large payments.
    amount_position = rng.beta(
        a=1.5,
        b=5.0
    )

    amount = (
        minimum_amount
        + amount_position
        * (maximum_amount - minimum_amount)
    )

    amount = round(float(amount), 2)

    # Ensure the amount is positive and within the industry range.
    amount = max(minimum_amount, amount)
    amount = min(maximum_amount, amount)

    currency = country_currency[merchant_country]

    # Synthetic fee assumption:
    # 1.4% of the payment plus 0.20 currency units.
    processing_fee = round(
        amount * 0.014 + 0.20,
        2
    )

    # -----------------------------
    # Generate payment method
    # -----------------------------

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

    # -----------------------------
    # Generate geographical fields
    # -----------------------------

    # Billing country usually matches the customer country.
    if rng.random() < 0.92:
        billing_country = customer_country
    else:
        billing_country = str(
            rng.choice(list(country_currency.keys()))
        )

    # Issuer country usually matches the billing country.
    if rng.random() < 0.90:
        issuer_country = billing_country
    else:
        issuer_country = str(
            rng.choice(list(country_currency.keys()))
        )

    # IP country usually matches the billing country.
    if rng.random() < 0.88:
        ip_country = billing_country
    else:
        ip_country = str(
            rng.choice(list(country_currency.keys()))
        )

    # -----------------------------
    # Generate device information
    # -----------------------------

    device_type = str(
        rng.choice(
            device_types,
            p=[0.62, 0.31, 0.07]
        )
    )

    customer_age_days = (
        transaction_timestamp - account_created_at
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

    # -----------------------------
    # Store the payment
    # -----------------------------

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


# --------------------------------------------------
# CREATE THE DATAFRAME
# --------------------------------------------------

payments = pd.DataFrame(payment_records)

payments = payments.sort_values(
    "transaction_timestamp"
).reset_index(drop=True)


# --------------------------------------------------
# SAVE THE STEP 12 VERSION
# --------------------------------------------------

output_file = raw_data_folder / "payments.csv"

payments.to_csv(
    output_file,
    index=False,
    date_format="%Y-%m-%d %H:%M:%S"
)

print(f"\nCreated: {output_file}")
print("Payment dataset shape:", payments.shape)


# --------------------------------------------------
# VALIDATE STEPS 10–12
# --------------------------------------------------

print("\nFirst five payments:")
print(payments.head())

print("\nMissing values:")
print(payments.isna().sum())

print(
    "\nDuplicate payment IDs:",
    payments["payment_id"].duplicated().sum()
)

print("\nAmount summary:")
print(payments["amount"].describe())

print("\nPayment-method distribution:")
print(
    payments["payment_method"].value_counts(
        normalize=True
    ).round(3)
)

print("\nCurrency distribution:")
print(payments["currency"].value_counts())

print(
    "\nAll amounts are positive:",
    (payments["amount"] > 0).all()
)

print(
    "All timestamps are in 2025:",
    payments["transaction_timestamp"]
    .between(transaction_start, transaction_end)
    .all()
)

print(
    "All merchant IDs are valid:",
    payments["merchant_id"]
    .isin(merchants["merchant_id"])
    .all()
)

print(
    "All customer IDs are valid:",
    payments["customer_id"]
    .isin(customers["customer_id"])
    .all()
)
from pathlib import Path

import numpy as np
import pandas as pd


rng = np.random.default_rng(43)

countries = [
    "GB", "US", "FR", "DE", "NL",
    "IE", "ES", "IT", "CA", "AU"
]

customer_segments = [
    "New",
    "Occasional",
    "Returning",
    "Loyal"
]

segment_probabilities = [
    0.25,
    0.35,
    0.30,
    0.10
]

order_ranges = {
    "New": (0, 3),
    "Occasional": (1, 7),
    "Returning": (5, 25),
    "Loyal": (20, 101)
}

account_date_ranges = {
    "New": ("2025-01-01", "2025-12-31"),
    "Occasional": ("2022-01-01", "2025-09-30"),
    "Returning": ("2019-01-01", "2024-12-31"),
    "Loyal": ("2017-01-01", "2023-12-31")
}


def random_date(start, end):
    start_date = pd.Timestamp(start)
    end_date = pd.Timestamp(end)
    number_of_days = (end_date - start_date).days

    return start_date + pd.Timedelta(
        days=int(rng.integers(0, number_of_days + 1))
    )


customer_records = []
reference_date = pd.Timestamp("2025-12-31")

for number in range(1, 10_001):
    customer_id = f"C{number:06d}"

    customer_country = str(rng.choice(countries))

    customer_segment = str(
        rng.choice(
            customer_segments,
            p=segment_probabilities
        )
    )

    minimum_orders, maximum_orders = order_ranges[customer_segment]

    historical_orders = int(
        rng.integers(minimum_orders, maximum_orders)
    )

    account_start, account_end = account_date_ranges[customer_segment]
    account_created_at = random_date(account_start, account_end)

    # Chargebacks remain uncommon, but become slightly more likely
    # when a customer has placed more orders.
    chargeback_probability = min(
        0.01 + historical_orders * 0.0005,
        0.08
    )

    if rng.random() < chargeback_probability:
        historical_chargebacks = int(
            rng.choice([1, 2, 3], p=[0.80, 0.15, 0.05])
        )
    else:
        historical_chargebacks = 0

    account_age_days = (reference_date - account_created_at).days

    # An email can be older than the customer account.
    email_age_days = int(
        account_age_days + rng.integers(0, 731)
    )

    usual_device_id = f"DEV{number:06d}"

    if historical_orders == 0:
        lifetime_value = 0.00
    else:
        average_order_value = float(rng.uniform(20, 150))
        value_noise = float(rng.uniform(0.80, 1.20))

        lifetime_value = round(
            historical_orders * average_order_value * value_noise,
            2
        )

    customer_records.append(
        {
            "customer_id": customer_id,
            "customer_country": customer_country,
            "account_created_at": account_created_at.strftime("%Y-%m-%d"),
            "customer_segment": customer_segment,
            "historical_orders": historical_orders,
            "historical_chargebacks": historical_chargebacks,
            "email_age_days": email_age_days,
            "usual_device_id": usual_device_id,
            "lifetime_value": lifetime_value
        }
    )

customers = pd.DataFrame(customer_records)

project_folder = Path(__file__).resolve().parents[1]
output_folder = project_folder / "data" / "raw"
output_folder.mkdir(parents=True, exist_ok=True)

output_file = output_folder / "customers.csv"

customers.to_csv(output_file, index=False)

print(f"Created: {output_file}")
print(f"Number of rows and columns: {customers.shape}")

print("\nFirst five rows:")
print(customers.head())

print("\nMissing values:")
print(customers.isna().sum())

print(
    "\nDuplicate customer IDs:",
    customers["customer_id"].duplicated().sum()
)

print("\nCustomer-segment counts:")
print(customers["customer_segment"].value_counts())

print("\nChargeback counts:")
print(customers["historical_chargebacks"].value_counts())

print("\nLifetime-value summary:")
print(customers["lifetime_value"].describe())

print(
    "\nLifetime values are non-negative:",
    (customers["lifetime_value"] >= 0).all()
)

print(
    "Account dates are not after 2025:",
    (
        pd.to_datetime(customers["account_created_at"])
        <= pd.Timestamp("2025-12-31")
    ).all()
)
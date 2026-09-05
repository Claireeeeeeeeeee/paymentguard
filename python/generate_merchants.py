from pathlib import Path

import numpy as np
import pandas as pd


# Using a fixed seed means the script produces the same data each time.
rng = np.random.default_rng(42)

industries = [
    "Fashion",
    "Electronics",
    "Travel",
    "Digital Products",
    "Gaming",
    "Food Delivery",
    "Subscription Software",
    "Ticketing",
    "Marketplace"
]

countries = [
    "GB", "US", "FR", "DE", "NL",
    "IE", "ES", "IT", "CA", "AU"
]

merchant_sizes = [
    "Small",
    "Medium",
    "Enterprise"
]

high_risk_industries = {
    "Gaming",
    "Electronics",
    "Ticketing",
    "Travel",
    "Digital Products"
}

monthly_volume_ranges = {
    "Small": (5_000, 50_000),
    "Medium": (50_000, 500_000),
    "Enterprise": (500_000, 5_000_000)
}

start_date = pd.Timestamp("2020-01-01")
end_date = pd.Timestamp("2024-12-31")
number_of_days = (end_date - start_date).days

merchant_records = []

for number in range(1, 101):
    merchant_id = f"M{number:05d}"
    merchant_name = f"Synthetic Merchant {number:03d}"

    industry = str(rng.choice(industries))
    merchant_country = str(rng.choice(countries))

    merchant_size = str(
        rng.choice(
            merchant_sizes,
            p=[0.60, 0.30, 0.10]
        )
    )

    # The requested industries have a greater chance of being high risk.
    if industry in high_risk_industries:
        risk_category = str(
            rng.choice(
                ["Medium", "High"],
                p=[0.30, 0.70]
            )
        )
    else:
        risk_category = str(
            rng.choice(
                ["Low", "Medium", "High"],
                p=[0.70, 0.25, 0.05]
            )
        )

    if industry == "Marketplace":
        platform_type = "Marketplace"
    elif industry == "Subscription Software":
        platform_type = "Subscription"
    else:
        platform_type = str(
            rng.choice(
                ["Direct", "Marketplace", "Subscription"],
                p=[0.75, 0.15, 0.10]
            )
        )

    onboarding_date = (
        start_date
        + pd.Timedelta(
            days=int(rng.integers(0, number_of_days + 1))
        )
    )

    reserve_ranges = {
        "Low": (0.01, 0.03),
        "Medium": (0.03, 0.07),
        "High": (0.07, 0.15)
    }

    reserve_minimum, reserve_maximum = reserve_ranges[risk_category]

    reserve_rate = round(
        float(rng.uniform(reserve_minimum, reserve_maximum)),
        4
    )

    volume_minimum, volume_maximum = monthly_volume_ranges[merchant_size]

    expected_monthly_volume = round(
        float(rng.uniform(volume_minimum, volume_maximum)),
        2
    )

    merchant_records.append(
        {
            "merchant_id": merchant_id,
            "merchant_name": merchant_name,
            "industry": industry,
            "merchant_country": merchant_country,
            "onboarding_date": onboarding_date.strftime("%Y-%m-%d"),
            "merchant_size": merchant_size,
            "risk_category": risk_category,
            "platform_type": platform_type,
            "reserve_rate": reserve_rate,
            "expected_monthly_volume": expected_monthly_volume
        }
    )

merchants = pd.DataFrame(merchant_records)

# Find the main paymentguard folder and create the output path.
project_folder = Path(__file__).resolve().parents[1]
output_folder = project_folder / "data" / "raw"
output_folder.mkdir(parents=True, exist_ok=True)

output_file = output_folder / "merchants.csv"

merchants.to_csv(output_file, index=False)

print(f"Created: {output_file}")
print(f"Number of rows and columns: {merchants.shape}")

print("\nFirst five rows:")
print(merchants.head())

print("\nMissing values:")
print(merchants.isna().sum())

print(
    "\nDuplicate merchant IDs:",
    merchants["merchant_id"].duplicated().sum()
)

print("\nIndustry counts:")
print(merchants["industry"].value_counts())

print(
    "\nReserve rates are between 0 and 1:",
    merchants["reserve_rate"].between(0, 1).all()
)

print(
    "Monthly volumes are positive:",
    (merchants["expected_monthly_volume"] > 0).all()
)

print(
    "Onboarding dates are before 2025:",
    (
        pd.to_datetime(merchants["onboarding_date"])
        < pd.Timestamp("2025-01-01")
    ).all()
)
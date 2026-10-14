from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT / "data/raw/metropolitan.xlsx"
OUTPUT_FILE = ROOT / "data/processed/county_cbsa_clean.csv"


def clean_county_cbsa():


    # Load the county-to-CBSA table and preserve codes as strings.
    metro = pd.read_excel(
        INPUT_FILE,
        header=2,
        dtype=str,
    )

    print("Original rows:", len(metro))

    # Shorten column names for later geographic merges.
    metro = metro.rename(
        columns={
            "CBSA Code": "cbsa",
            "CBSA Title": "cbsa_name",
            "Metropolitan/Micropolitan Statistical Area": "area_type",
            "FIPS State Code": "state_fips",
            "FIPS County Code": "county_code",
        }
    )

    # Remove rows missing state, county, or CBSA codes.
    metro = metro.dropna(
        subset=["state_fips", "county_code", "cbsa"]
    ).copy()

    # Pad codes with leading zeros to their standard lengths.
    metro["state_fips"] = metro["state_fips"].str.zfill(2)
    metro["county_code"] = metro["county_code"].str.zfill(3)
    metro["cbsa"] = metro["cbsa"].str.zfill(5)


    # Combine state and county codes into a five-digit county FIPS code.
    metro["county_fips"] = (
        metro["state_fips"] + metro["county_code"]
    )

    # Keep the mapping columns and remove identical duplicate rows.
    metro_clean = metro[
        ["county_fips", "cbsa", "cbsa_name", "area_type"]
    ].copy()

    metro_clean = metro_clean.drop_duplicates()

    # Count remaining duplicate county codes and display a cleaning summary.
    duplicates = metro_clean["county_fips"].duplicated().sum()

    print("Cleaned rows:", len(metro_clean))
    print("Duplicate county FIPS:", duplicates)
    print("\nFirst five rows:")
    print(metro_clean.head())

    # Save the cleaned county-to-CBSA mapping as a CSV.
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    metro_clean.to_csv(OUTPUT_FILE, index=False)

    print("\nSaved to:", OUTPUT_FILE)


if __name__ == "__main__":
    clean_county_cbsa()

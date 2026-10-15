from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

SCHOOLS_FILE = ROOT / "data/processed/scorecard_with_fips.csv"
CBSA_FILE = ROOT / "data/processed/county_cbsa_clean.csv"
OUTPUT_FILE = ROOT / "data/processed/school_geography.csv"


def assign_college_cbsa():
    """Read school and county tables and write each school's CBSA assignment."""
    schools = pd.read_csv(
        SCHOOLS_FILE,
        dtype={"county_fips": str, "zip5": str},
    )

    metro = pd.read_csv(
        CBSA_FILE,
        dtype={"county_fips": str, "cbsa": str},
    )

    schools["county_fips"] = schools["county_fips"].str.zfill(5)
    metro["county_fips"] = metro["county_fips"].str.zfill(5)

    merged = schools.merge(
        metro,
        on="county_fips",
        how="left",
        validate="many_to_one",
    )

    assert len(merged) == len(schools), "College row count changed!"

    valid_cbsa = merged["cbsa"].dropna()

    assert valid_cbsa.str.fullmatch(r"\d{5}").all(), "Invalid CBSA code!"
    unmatched = merged[merged["cbsa"].isna()]

    print("\nUnmatched colleges by state:")
    print(unmatched["state"].value_counts().to_string())

    print("Original colleges:", len(schools))
    print("Merged colleges:", len(merged))
    print("Colleges with CBSA:", merged["cbsa"].notna().sum())
    print("Colleges without CBSA:", merged["cbsa"].isna().sum())

    print("\nFirst five rows:")
    print(merged[["name", "state", "county_fips", "cbsa", "cbsa_name"]].head())

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUTPUT_FILE, index=False)

    print("\nSaved to:", OUTPUT_FILE)


if __name__ == "__main__":
    assign_college_cbsa()

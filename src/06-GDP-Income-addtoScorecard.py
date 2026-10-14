import os
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

SCORECARD_PATH = ROOT / "data" / "processed" / "scorecard_with_fips.csv"
GDP_PATH = ROOT / "data" / "processed" / "local_economic_data.csv"
INCOME_PATH = ROOT / "data" / "processed" / "local_income_data.csv"

OUTPUT_DIR = ROOT / "data" / "processed"
OUTPUT_PATH = OUTPUT_DIR / "SCHOOL_INCOME_LOCALGDP.csv"

if __name__ == "__main__":
    # Read cleaned data
    df = pd.read_csv(
        SCORECARD_PATH,
        comment="#",
        dtype={"county_fips": str}
    )

    gdp = pd.read_csv(
        GDP_PATH,
        dtype={"GeoFIPS": str}
    )

    income = pd.read_csv(
        INCOME_PATH,
        dtype={"GeoFIPS": str}
    )

    # Rename FIPS columns
    gdp = gdp.rename(columns={"GeoFIPS": "county_fips"})
    income = income.rename(columns={"GeoFIPS": "county_fips"})

    # Drop unnecessary county name columns
    gdp = gdp.drop(columns=["GeoName"])
    income = income.drop(columns=["GeoName"])

    # Rename yearly GDP and income variables
    for year in range(2010, 2025):
        gdp = gdp.rename(
            columns={str(year): f"gdp_{year}"}
        )

        income = income.rename(
            columns={str(year): f"income_{year}"}
        )

    # Match Scorecard with GDP
    df = df.merge(
        gdp,
        on="county_fips",
        how="left",
        validate="many_to_one"
    )

    # Match Scorecard with income
    df = df.merge(
        income,
        on="county_fips",
        how="left",
        validate="many_to_one"
    )

    # Save merged data
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    # Append merge results to the end of CSV
    with open(OUTPUT_PATH, "a", encoding="utf-8") as f:
        f.write("\n# Merge Summary:\n")
        f.write(f"# Total schools: {len(df)}\n")
        f.write(f"# GDP matched: {df['gdp_2024'].notna().sum()}\n")
        f.write(f"# GDP unmatched: {df['gdp_2024'].isna().sum()}\n")
        f.write(f"# Income matched: {df['income_2024'].notna().sum()}\n")
        f.write(f"# Income unmatched: {df['income_2024'].isna().sum()}\n")

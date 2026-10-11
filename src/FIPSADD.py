import os
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

IN_PATH = ROOT / "data" / "processed" / "scorecard.csv"
ZIP_PATH = ROOT / "data" / "raw" / "ZIP-COUNTY_062026.xlsx"
OUTPUT_DIR = ROOT / "data" / "processed"
OUTPUT_PATH = OUTPUT_DIR / "scorecard_with_fips.csv"

if __name__ == "__main__":
    df = pd.read_csv(
        IN_PATH,
        dtype={"zip5": str}
    )

    zip_county = pd.read_excel(
        ZIP_PATH,
        dtype={"zip": str, "geoid": str}
    )

    # Select the county with the highest total address ratio
    zip_county = zip_county.sort_values(
        "tot_ratio", ascending=False
    ).drop_duplicates(subset=["zip"])

    # Keep only necessary columns
    zip_county = zip_county[["zip", "geoid"]]

    # Match ZIP codes to County FIPS
    df = df.merge(
        zip_county,
        left_on="zip5",
        right_on="zip",
        how="left",
        validate="many_to_one"
    )

    # Rename and drop unnecessary columns
    df = df.rename(columns={"geoid": "county_fips"})
    df = df.drop(columns=["zip"])

    # Remove invalid County FIPS
    invalid_fips = ~df["county_fips"].str.fullmatch(
        r"\d{5}", na=False
    )
    df.loc[invalid_fips, "county_fips"] = pd.NA

    # Manually assign County FIPS
    manual_fips = {
        156295: "21151",  # Berea College
        159966: "22057",  # Nicholls State University
        160621: "22033",  # Southern University
        164580: "25021",  # Babson College
        199193: "37183",  # NC State University
        201885: "39061",  # University of Cincinnati
        221847: "47141",  # Tennessee Tech
        228246: "48113",  # Southern Methodist University
        234155: "51041"   # Virginia State University
    }

    # Fill missing or invalid FIPS
    manual_mask = (
        df["county_fips"].isna() &
        df["unitid"].isin(manual_fips)
    )

    df.loc[manual_mask, "county_fips"] = (
        df.loc[manual_mask, "unitid"].map(manual_fips)
    )

    # Save processed data
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
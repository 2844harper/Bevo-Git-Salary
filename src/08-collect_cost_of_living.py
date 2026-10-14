from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT / "data/raw/hud_2024.xlsx"
OUTPUT_FILE = ROOT / "data/processed/hud_fmr_clean.csv"


def clean_hud_fmr():
    # Load the local HUD rent table and preserve FIPS codes as strings.
    df = pd.read_excel(
        INPUT_FILE,
        sheet_name="FY24_FMRs_rev",
        dtype={"fips": str},
    )

    print("Original HUD records:", len(df))

    # Extract county codes and convert one- and two-bedroom rents to numeric values.
    df["county_fips"] = df["fips"].str[:5]

    df["fmr_1"] = pd.to_numeric(df["fmr_1"], errors="coerce")
    df["fmr_2"] = pd.to_numeric(df["fmr_2"], errors="coerce")

    # Average rents by county and count the HUD records in each county.
    cleaned = (
        df.groupby("county_fips", as_index=False)
        .agg(
            state=("stusps", "first"),
            county_name=("countyname", "first"),
            fmr_1br=("fmr_1", "mean"),
            fmr_2br=("fmr_2", "mean"),
            hud_record_count=("fips", "size"),
        )
    )

    # Round rents to two decimal places and label the data year.
    cleaned["fmr_1br"] = cleaned["fmr_1br"].round(2)
    cleaned["fmr_2br"] = cleaned["fmr_2br"].round(2)

    cleaned["year"] = 2024

    # Check for unique five-digit county codes and positive nonmissing rents.
    assert not cleaned["county_fips"].duplicated().any()
    assert cleaned["county_fips"].str.fullmatch(r"\d{5}").all()
    assert (cleaned["fmr_1br"].dropna() > 0).all()
    assert (cleaned["fmr_2br"].dropna() > 0).all()

    # Save the county-level rent table as a CSV.
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(OUTPUT_FILE, index=False)

    # Report the cleaned record counts and display a sample of rows.
    print("Cleaned county records:", len(cleaned))
    print(
        "Counties with multiple HUD records:",
        (cleaned["hud_record_count"] > 1).sum(),
    )
    print("Duplicate county FIPS:", cleaned["county_fips"].duplicated().sum())

    print("\nFirst five rows:")
    print(cleaned.head().to_string(index=False))

    print("\nSaved to:", OUTPUT_FILE)


if __name__ == "__main__":
    clean_hud_fmr()

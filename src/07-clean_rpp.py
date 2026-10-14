from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT / "data/raw/RPP.xlsx"
OUTPUT_FILE = ROOT / "data/processed/rpp_clean.csv"


def clean_rpp():

    # Load the BEA table and preserve geographic codes as strings.
    rpp = pd.read_excel(
        INPUT_FILE,
        sheet_name="Table",
        header=5,
        dtype={"GeoFIPS": str},
    )

    print("Original rows:", len(rpp))
    print("Columns:", rpp.columns.tolist())

    # Keep the all-items price index (LineCode 1).
    rpp["LineCode"] = pd.to_numeric(
        rpp["LineCode"], errors="coerce"
    )

    rpp = rpp[rpp["LineCode"] == 1].copy()

    # Standardize five-digit codes and remove invalid or aggregate codes.
    rpp["GeoFIPS"] = rpp["GeoFIPS"].str.strip().str.zfill(5)

    rpp = rpp[
        rpp["GeoFIPS"].str.fullmatch(r"\d{5}", na=False)
        & ~rpp["GeoFIPS"].isin(["00000", "00999"])
    ].copy()

    # Rename the geographic and 2024 price-index columns for later merges.
    rpp = rpp.rename(
        columns={
            "GeoFIPS": "cbsa",
            "GeoName": "metro_name",
            "2024": "rpp_2024",
        }
    )

    # Convert RPP to numeric values, keep the needed columns, and drop missing RPP.
    rpp["rpp_2024"] = pd.to_numeric(
        rpp["rpp_2024"], errors="coerce"
    )

    rpp = rpp[["cbsa", "metro_name", "rpp_2024"]]

    rpp = rpp.dropna(subset=["rpp_2024"])

    # Check that CBSA codes are unique and price indices are positive.
    assert not rpp["cbsa"].duplicated().any(), (
        "Duplicate CBSA identifiers found!"
    )

    assert (rpp["rpp_2024"] > 0).all(), (
        "RPP values must be positive!"
    )

    # Save the cleaned CSV and report its size and a sample of rows.
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    rpp.to_csv(OUTPUT_FILE, index=False)

    print("\nCleaned rows:", len(rpp))
    print("Duplicate CBSAs:", rpp["cbsa"].duplicated().sum())

    print("\nFirst five rows:")
    print(rpp.head())

    print("\nSaved to:", OUTPUT_FILE)


if __name__ == "__main__":
    clean_rpp()

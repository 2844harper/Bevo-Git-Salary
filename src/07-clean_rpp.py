from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT / "data/raw/2022 rpp.xlsx"
OUTPUT_FILE = ROOT / "data/processed/rpp_clean.csv"


def clean_rpp():
    """Read INPUT_FILE and write cleaned 2022 CBSA price indices to OUTPUT_FILE."""
    rpp = pd.read_excel(
        INPUT_FILE,
        sheet_name="Table",
        header=5,
        dtype={"GeoFIPS": str},
    )

    print("Original rows:", len(rpp))
    print("Columns:", rpp.columns.tolist())

    # Keep the all-items price index (LineCode 1).
    rpp["LineCode"] = pd.to_numeric(rpp["LineCode"], errors="coerce")

    rpp = rpp[rpp["LineCode"] == 1].copy()

    rpp["GeoFIPS"] = rpp["GeoFIPS"].str.strip().str.zfill(5)

    # Exclude national and aggregate codes rather than treating them as CBSAs.
    rpp = rpp[
        rpp["GeoFIPS"].str.fullmatch(r"\d{5}", na=False)
        & ~rpp["GeoFIPS"].isin(["00000", "00999"])
    ].copy()

    rpp = rpp.rename(
        columns={
            "GeoFIPS": "cbsa",
            "GeoName": "metro_name",
            "2022": "rpp_2022",
        }
    )

    rpp["rpp_2022"] = pd.to_numeric(rpp["rpp_2022"], errors="coerce")

    rpp = rpp[["cbsa", "metro_name", "rpp_2022"]]

    rpp = rpp.dropna(subset=["rpp_2022"])

    assert not rpp["cbsa"].duplicated().any(), "Duplicate CBSA identifiers found!"

    assert (rpp["rpp_2022"] > 0).all(), "RPP values must be positive!"

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    rpp.to_csv(OUTPUT_FILE, index=False)

    print("\nCleaned rows:", len(rpp))
    print("Duplicate CBSAs:", rpp["cbsa"].duplicated().sum())

    print("\nFirst five rows:")
    print(rpp.head())

    print("\nSaved to:", OUTPUT_FILE)


if __name__ == "__main__":
    clean_rpp()

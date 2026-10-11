import os
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

IN_PATH = ROOT / "data" / "raw" / "CAGDP1__ALL_AREAS_2001_2024.csv"
OUTPUT_DIR = ROOT / "data" / "processed"
OUTPUT_PATH = OUTPUT_DIR / "local_economic_data.csv"

if __name__ == "__main__":
    df = pd.read_csv(
        IN_PATH,
        encoding="cp1252",
        skipinitialspace=True,
        skipfooter=4,
        engine="python",
        dtype={"GeoFIPS": str},
        na_values=["(NA)", "(NM)"]
    )

    # Only keep Real GDP
    df = df[df["LineCode"] == 1].copy()

    # Only keep county-level data
    df = df[~df["GeoFIPS"].str.endswith("000")].copy()

    # Drop useless columns, and only keep years after 2010
    df = df.drop(columns=[
        "Region", "TableName", "LineCode",
        "IndustryClassification", "Description", "Unit"
    ] + [str(year) for year in range(2001, 2010)])


    # Calculate yearly GDP growth rates (2015-2024)
    for year in range(2015, 2025):
        df[f"growth_{year}"] = (
            df[str(year)] / df[str(year - 1)] - 1
        ) * 100

    # Calculate average annual growth rate over 10 years
    growth_cols = [f"growth_{year}" for year in range(2015, 2025)]

    df["GDP_growth_10y_avg"] = df[growth_cols].mean(
        axis=1, skipna=False
    )

    # Calculate 10-year CAGR
    df["GDP_growth_10y_CAGR"] = (
        (df["2024"] / df["2014"]) ** (1 / 10) - 1
    ) * 100

    # Save processed data
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

IN_PATH = ROOT / "data" / "raw" / "CAGDP1__ALL_AREAS_2001_2024.csv"
OUTPUT_DIR = ROOT / "data" / "processed"
OUTPUT_PATH = OUTPUT_DIR / "local_economic_data.csv"


def main():
    """Read BEA GDP records and save county levels and growth measures."""
    df = pd.read_csv(
        IN_PATH,
        encoding="cp1252",
        skipinitialspace=True,
        skipfooter=4,
        engine="python",
        dtype={"GeoFIPS": str},
        na_values=["(NA)", "(NM)"],
    )

    # BEA LineCode 1 contains real GDP; FIPS ending in 000 are aggregates.
    df = df[df["LineCode"] == 1].copy()

    df = df[~df["GeoFIPS"].str.endswith("000")].copy()

    df = df.drop(
        columns=[
            "Region",
            "TableName",
            "LineCode",
            "IndustryClassification",
            "Description",
            "Unit",
        ]
        + [str(year) for year in range(2001, 2010)]
    )

    # Calculate yearly GDP growth rates (2015-2024)
    for year in range(2015, 2025):
        df[f"growth_{year}"] = (df[str(year)] / df[str(year - 1)] - 1) * 100

    growth_cols = [f"growth_{year}" for year in range(2015, 2025)]

    df["GDP_growth_10y_avg"] = df[growth_cols].mean(axis=1, skipna=False)

    # CAGR measures compound annual growth from 2014 to 2024.
    df["GDP_growth_10y_CAGR"] = ((df["2024"] / df["2014"]) ** (1 / 10) - 1) * 100

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)


if __name__ == "__main__":
    main()

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

IN_PATH = ROOT / "data" / "raw" / "CAINC1__ALL_AREAS_1969_2024.csv"
OUTPUT_DIR = ROOT / "data" / "processed"
OUTPUT_PATH = OUTPUT_DIR / "local_income_data.csv"


def main():
    """Read BEA income records and save county levels and growth measures."""
    df = pd.read_csv(
        IN_PATH,
        encoding="cp1252",
        skipinitialspace=True,
        skipfooter=4,
        engine="python",
        dtype={"GeoFIPS": str},
        na_values=["(NA)", "(NM)"],
    )

    # BEA LineCode 3 contains per-capita income; FIPS ending in 000 are aggregates.
    df = df[df["LineCode"] == 3].copy()

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
        + [str(year) for year in range(1969, 2010)]
    )

    # Calculate yearly income growth rates (2015-2024)
    for year in range(2015, 2025):
        df[f"income_growth_{year}"] = (df[str(year)] / df[str(year - 1)] - 1) * 100

    growth_cols = [f"income_growth_{year}" for year in range(2015, 2025)]

    df["income_growth_10y_avg"] = df[growth_cols].mean(axis=1, skipna=False)

    # CAGR measures compound annual growth from 2014 to 2024.
    df["income_growth_10y_CAGR"] = ((df["2024"] / df["2014"]) ** (1 / 10) - 1) * 100

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)


if __name__ == "__main__":
    main()

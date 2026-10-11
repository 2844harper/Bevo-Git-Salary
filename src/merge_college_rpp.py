from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

SCHOOLS_FILE = ROOT / "data/processed/school_geography.csv"
RPP_FILE = ROOT / "data/processed/rpp_clean.csv"
OUTPUT_FILE = ROOT / "data/processed/college_rpp_adjusted.csv"


def merge_college_rpp():

    schools = pd.read_csv(
        SCHOOLS_FILE,
        dtype={"cbsa": str, "county_fips": str, "zip5": str},
    )

    rpp = pd.read_csv(
        RPP_FILE,
        dtype={"cbsa": str},
    )

    schools["cbsa"] = schools["cbsa"].str.zfill(5)
    rpp["cbsa"] = rpp["cbsa"].str.zfill(5)

    merged = schools.merge(
        rpp,
        on="cbsa",
        how="left",
        validate="many_to_one",
    )

    assert len(merged) == len(schools), (
        "Merge unexpectedly changed the number of colleges!"
    )

    for column in ["earnings_6yr", "earnings_10yr"]:
        merged[column + "_rpp_adj"] = (
            merged[column] / (merged["rpp_2024"] / 100)
        )

    print("Original colleges:", len(schools))
    print("Merged colleges:", len(merged))
    print("Colleges with RPP:", merged["rpp_2024"].notna().sum())
    print("Colleges without RPP:", merged["rpp_2024"].isna().sum())

    print("\nFirst five colleges:")
    print(
        merged[
            [
                "name",
                "earnings_10yr",
                "rpp_2024",
                "earnings_10yr_rpp_adj",
            ]
        ].head()
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUTPUT_FILE, index=False)

    print("\nSaved to:", OUTPUT_FILE)


if __name__ == "__main__":
    merge_college_rpp()

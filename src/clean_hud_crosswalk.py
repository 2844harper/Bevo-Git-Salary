from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT / "data/raw/ZIP-COUNTY_122024.xlsx"
OUTPUT_FILE = ROOT / "data/processed/zip_county_clean.csv"


def clean_hud_crosswalk():

    hud = pd.read_excel(
        INPUT_FILE,
        dtype={"zip": str, "geoid": str},
    )

    hud["zip"] = hud["zip"].str.zfill(5)
    hud["geoid"] = hud["geoid"].str.zfill(5)

    hud["res_ratio"] = pd.to_numeric(
        hud["res_ratio"], errors="coerce"
    )

    hud = hud.sort_values(
        ["zip", "res_ratio", "geoid"],
        ascending=[True, False, True],
    )

    hud_clean = hud.drop_duplicates(subset=["zip"], keep="first")

    hud_clean = hud_clean.rename(
        columns={"geoid": "county_fips"}
    )

    hud_clean = hud_clean[
        ["zip", "county_fips", "res_ratio"]
    ]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    hud_clean.to_csv(OUTPUT_FILE, index=False)

    print("Original rows:", len(hud))
    print("Cleaned rows:", len(hud_clean))
    print("Duplicate ZIPs:", hud_clean["zip"].duplicated().sum())
    print("\nFirst five rows:")
    print(hud_clean.head())
    print("\nSaved to:", OUTPUT_FILE)


if __name__ == "__main__":
    clean_hud_crosswalk()

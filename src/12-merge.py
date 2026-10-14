from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed"

SCHOOLS_FILE = DATA / "school_geography.csv"
RPP_FILE = DATA / "rpp_clean.csv"
HUD_FILE = DATA / "hud_fmr_clean.csv"

OUTPUT_FILE = DATA / "schools.csv"
UNMATCHED_FILE = DATA / "unmatched_schools.csv"


def merge_schools():
    # Load school geography, RPP, and HUD rents, preserving IDs and codes as strings.
    schools = pd.read_csv(
        SCHOOLS_FILE,
        dtype={"unitid": str, "cbsa": str, "county_fips": str},
    )

    rpp = pd.read_csv(
        RPP_FILE,
        dtype={"cbsa": str},
    )

    hud = pd.read_csv(
        HUD_FILE,
        dtype={"county_fips": str},
    )

    # Check that school IDs and lookup-table keys are unique.
    assert schools["unitid"].is_unique
    assert rpp["cbsa"].is_unique
    assert hud["county_fips"].is_unique

    # Attach local price indices by CBSA while retaining all schools.
    merged = schools.merge(
        rpp,
        on="cbsa",
        how="left",
        validate="many_to_one",
    )

    # Attach one- and two-bedroom rents and HUD record counts by county FIPS.
    hud_columns = [
        "county_fips",
        "fmr_1br",
        "fmr_2br",
        "hud_record_count",
    ]

    merged = merged.merge(
        hud[hud_columns],
        on="county_fips",
        how="left",
        validate="many_to_one",
    )

    # Adjust earnings for local prices by dividing by RPP / 100.
    for column in ["earnings_6yr", "earnings_10yr"]:
        merged[column + "_rpp_adj"] = (
            pd.to_numeric(merged[column], errors="coerce")
            / (merged["rpp_2024"] / 100)
        )

    # Flag missing CBSA, RPP, or two-bedroom rent and collect affected schools.
    merged["missing_cbsa"] = merged["cbsa"].isna()
    merged["missing_rpp"] = merged["rpp_2024"].isna()
    merged["missing_hud"] = merged["fmr_2br"].isna()

    unmatched = merged[
        merged[
            ["missing_cbsa", "missing_rpp", "missing_hud"]
        ].any(axis=1)
    ].copy()

    # Verify that the merges preserve school counts and unique IDs.
    assert len(merged) == len(schools)
    assert merged["unitid"].is_unique

    # Save the full school table and a separate table of schools with missing matches.
    merged.to_csv(OUTPUT_FILE, index=False)
    unmatched.to_csv(UNMATCHED_FILE, index=False)

    # Report match coverage and display sample merged records.
    print("Total schools:", len(merged))
    print("Schools with RPP:", merged["rpp_2024"].notna().sum())
    print("Schools with HUD rent:", merged["fmr_2br"].notna().sum())
    print("Schools missing CBSA:", merged["missing_cbsa"].sum())
    print("Schools missing RPP:", merged["missing_rpp"].sum())
    print("Schools missing HUD:", merged["missing_hud"].sum())
    print("Schools with any missing match:", len(unmatched))
    print("Duplicate UNITIDs:", merged["unitid"].duplicated().sum())

    print("\nFirst five schools:")
    print(
        merged[
            [
                "name",
                "earnings_10yr",
                "rpp_2024",
                "fmr_2br",
                "earnings_10yr_rpp_adj",
            ]
        ].head().to_string(index=False)
    )

    print("\nSaved:", OUTPUT_FILE)
    print("Saved:", UNMATCHED_FILE)


if __name__ == "__main__":
    merge_schools()

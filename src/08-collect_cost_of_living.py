from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT / "data/raw/FY22_FMRs_revised.xlsx"
OUTPUT_FILE = ROOT / "data/processed/hud_fmr_clean.csv"


def load_hud_fmr():
    """Return FY2022 rent records from INPUT_FILE as a DataFrame."""
    # Skip malformed date metadata in memory without changing the workbook.
    with ZipFile(INPUT_FILE) as source, BytesIO() as buffer:
        with ZipFile(buffer, "w") as target:
            for entry in source.infolist():
                if entry.filename != "docProps/core.xml":
                    target.writestr(entry, source.read(entry.filename))
        buffer.seek(0)
        return pd.read_excel(
            buffer,
            sheet_name="FY22_FMRs_revised",
            dtype={"fips2010": str},
        )


def clean_hud_fmr():
    """Read revised FY2022 HUD rents and write county averages to OUTPUT_FILE."""
    df = load_hud_fmr()

    print("Original HUD records:", len(df))

    # Pad county/town codes to ten digits before extracting five-digit county FIPS.
    df["county_fips"] = df["fips2010"].str.zfill(10).str[:5]

    df["fmr_1"] = pd.to_numeric(df["fmr_1"], errors="coerce")
    df["fmr_2"] = pd.to_numeric(df["fmr_2"], errors="coerce")

    cleaned = df.groupby("county_fips", as_index=False).agg(
        state=("state_alpha", "first"),
        county_name=("countyname", "first"),
        fmr_1br=("fmr_1", "mean"),
        fmr_2br=("fmr_2", "mean"),
        hud_record_count=("fips2010", "size"),
    )

    cleaned["fmr_1br"] = cleaned["fmr_1br"].round(2)
    cleaned["fmr_2br"] = cleaned["fmr_2br"].round(2)

    cleaned["year"] = 2022

    assert not cleaned["county_fips"].duplicated().any()
    assert cleaned["county_fips"].str.fullmatch(r"\d{5}").all()
    assert (cleaned["fmr_1br"].dropna() > 0).all()
    assert (cleaned["fmr_2br"].dropna() > 0).all()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(OUTPUT_FILE, index=False)

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

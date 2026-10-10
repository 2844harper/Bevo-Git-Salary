from pathlib import Path

import pandas as pd

RAW_PATH = Path("data/raw/scorecard_raw.csv")
BACHELORS = 3
MIN_ENROLLMENT = 1000
CLEAN_PATH = Path("data/processed/scorecard.csv")
TARGETS_PATH = Path("data/processed/school_targets.csv")
TARGET_COLUMNS = ["unitid", "name", "city", "state", "zip5", "control", "lat", "lon"]
OWNERSHIP_LABELS = {1: "public", 2: "private_nonprofit", 3: "private_forprofit"}
RENAME = {
    "id": "unitid",
    "school.name": "name",
    "school.city": "city",
    "school.state": "state",
    "school.zip": "zip",
    "school.ownership": "ownership",
    "school.degrees_awarded.predominant": "predominant_degree",
    "location.lat": "lat",
    "location.lon": "lon",
    "latest.student.size": "enrollment",
    "latest.admissions.admission_rate.overall": "admission_rate",
    "latest.completion.completion_rate_4yr_150nt": "completion_rate",
    "latest.aid.loan_principal": "median_debt",
    "latest.aid.pell_grant_rate": "pell_rate",
    "latest.cost.tuition.in_state": "tuition_in_state",
    "latest.cost.tuition.out_of_state": "tuition_out_of_state",
    "latest.cost.avg_net_price.overall": "net_price",
    "latest.cost.attendance.academic_year": "coa_published",
    "latest.earnings.6_yrs_after_entry.median": "earnings_6yr",
    "latest.earnings.10_yrs_after_entry.median": "earnings_10yr",
}


def load_raw():
    """Read the raw Scorecard CSV with ID and ZIP kept as strings."""
    return pd.read_csv(RAW_PATH, dtype={"id": str, "school.zip": str})


def clean(df):
    """Rename columns, build a 5-digit ZIP and a readable school type."""
    df = df.rename(columns=RENAME)
    df["zip5"] = df["zip"].str[:5].str.zfill(5)
    df["control"] = df["ownership"].map(OWNERSHIP_LABELS)
    return df.drop(columns="zip")


def filter_sample(df):
    """Keep bachelor's-focused, non-profit schools with enough students and earnings data."""
    keep = (
        (df["predominant_degree"] == BACHELORS)
        & df["ownership"].isin([1, 2])
        & (df["enrollment"] >= MIN_ENROLLMENT)
        & df["earnings_10yr"].notna()
    )
    return df[keep]


def save_targets(sample):
    """Save school IDs and locations used to join other data sources."""
    sample[TARGET_COLUMNS].to_csv(TARGETS_PATH, index=False)


if __name__ == "__main__":
    sample = filter_sample(clean(load_raw()))
    CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(CLEAN_PATH, index=False)
    save_targets(sample)
    print(len(sample), "schools kept")
    print(sample["control"].value_counts())

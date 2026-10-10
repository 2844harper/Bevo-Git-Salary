from pathlib import Path

import pandas as pd

RAW_PATH = Path("data/raw/scorecard_raw.csv")
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


if __name__ == "__main__":
    print(clean(load_raw()).shape)

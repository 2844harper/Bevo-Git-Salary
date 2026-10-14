import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

API_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"
RAW_PATH = Path("data/raw/scorecard_raw.csv")

# Select school information, costs, and earnings to download.
FIELDS = [
    "id",
    "school.name",
    "school.city",
    "school.state",
    "school.zip",
    "school.ownership",
    "school.degrees_awarded.predominant",
    "location.lat",
    "location.lon",
    "latest.student.size",
    "latest.admissions.admission_rate.overall",
    "latest.completion.completion_rate_4yr_150nt",
    "latest.aid.loan_principal",
    "latest.aid.pell_grant_rate",
    "latest.cost.tuition.in_state",
    "latest.cost.tuition.out_of_state",
    "latest.cost.avg_net_price.overall",
    "latest.cost.attendance.academic_year",
    "latest.earnings.6_yrs_after_entry.median",
    "latest.earnings.10_yrs_after_entry.median",
]


def fetch_page(api_key, page):
    """Request one page of up to 100 schools and check for API errors."""
    params = {
        "api_key": api_key,
        "fields": ",".join(FIELDS),
        "per_page": 100,
        "page": page,
    }
    response = requests.get(API_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def collect_all(api_key):
    """Download all pages and return them as one DataFrame."""
    records, page = [], 0
    while True:
        data = fetch_page(api_key, page)
        records.extend(data["results"])
        total = data["metadata"]["total"]
        if len(records) >= total:
            break
        page += 1
    return pd.DataFrame(records)


if __name__ == "__main__":
    # Get a key at https://api.data.gov/signup/ and save it as SCORECARD_API_KEY in .env.
    load_dotenv()
    df = collect_all(os.environ["SCORECARD_API_KEY"])
    # Save all downloaded records as a raw CSV, replacing the previous file.
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_PATH, index=False)

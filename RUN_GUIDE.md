# How to Run the Project

## 1. Get an API key (only for downloading new data)

Request a key at [api.data.gov](https://api.data.gov/signup/). Create a file named `.env` in the project root, add the line below, replace `your_key_here` with your own key, and save it:

```dotenv
SCORECARD_API_KEY=your_key_here
```

Keep your real key private and do not upload `.env` to GitHub. `BEA_API_KEY` is not needed because the BEA data files are already included.

If you use the existing `data/raw/scorecard_raw.csv`, you do not need a key and can skip script `01`.

## 2. Install the required packages

Install the packages listed in [requirements.txt](requirements.txt):

```bash
python -m pip install -r requirements.txt
```

## 3. Run the scripts in order

Run the files in `src/` one by one, following their numbers. Run from the project root so the data paths work correctly.

```text
01-collect_scorecard.py
02-clean_scorecard.py
03-fips-zip_pairup.py
04-GDP_Clean.py
05-Income_Clean.py
06-GDP-Income-addtoScorecard.py
07-clean_rpp.py
08-collect_cost_of_living.py
09-clean_county_cbsa.py
10-assign_college_cbsa.py
11-merge_college_rpp.py
12-merge.py
13-analysis.py
```

Start at `02` if you are using the existing raw data. Running the scripts again replaces their output files.

## 4. Output files

Script `01` saves `data/raw/scorecard_raw.csv`, the original school data downloaded from College Scorecard.

The cleaned and merged tables are saved in `data/processed/`:

| File | What it contains |
| --- | --- |
| `scorecard.csv` | Cleaned data for the selected schools, including costs and earnings. |
| `school_targets.csv` | School IDs, names, locations, and school types for matching with other data. |
| `scorecard_with_fips.csv` | School data with county FIPS codes added. |
| `local_economic_data.csv` | County GDP from 2010–2024 and annual and 10-year growth measures. |
| `local_income_data.csv` | County per-capita income from 2010–2024 and annual and 10-year growth measures. |
| `SCHOOL_INCOME_LOCALGDP.csv` | School data combined with county GDP and income. |
| `rpp_clean.csv` | Local price indices for 2024, with the U.S. average equal to 100. |
| `hud_fmr_clean.csv` | Average one- and two-bedroom HUD benchmark rents by county. |
| `county_cbsa_clean.csv` | A mapping from county codes to metropolitan or micropolitan area codes (CBSA). |
| `school_geography.csv` | School data with CBSA codes and area names added. |
| `college_rpp_adjusted.csv` | School data with local price indices and earnings adjusted for local prices. |
| `schools.csv` | School data combined with local price indices, adjusted earnings, and HUD rents. |
| `unmatched_schools.csv` | Schools missing a CBSA, price index, or two-bedroom rent match. |
| `college_metrics.csv` | Final school table with four-year costs, payback years, and earnings-to-cost ratios. |

The analysis also saves `artifacts/regression_results.txt`, containing the results of five regressions, and these charts in `artifacts/figures/`:

| File | What it shows |
| --- | --- |
| `fig_cost_vs_earnings.png` | Annual college cost versus median earnings 10 years after entry. |
| `fig_efficiency_by_control.png` | Earnings-to-cost ratios for public and private nonprofit schools. |
| `fig_payback_by_control.png` | Years of median earnings needed to cover four years of college cost. |
| `fig_county_income_vs_earnings.png` | County per-capita income versus graduate earnings. |
| `fig_gdp_growth_vs_earnings.png` | County GDP growth versus graduate earnings. |

## 5. Original dataset sources

The raw data files in `data/raw/` come from these websites:

| Dataset | File used in this project | Original website |
| --- | --- | --- |
| HUD Fair Market Rents, 2024 | `hud_2024.xlsx` | [HUD Fair Market Rents](https://www.huduser.gov/portal/datasets/fmr.html#data_2024) |
| HUD USPS ZIP–County Crosswalk | `ZIP-COUNTY_062026.xlsx` | [HUD USPS Crosswalk](https://www.huduser.gov/portal/datasets/usps_crosswalk.html) |
| Census metropolitan and micropolitan area definitions | `metropolitan.xlsx` | [Census Historical Delineation Files](https://www.census.gov/geographies/reference-files/time-series/demo/metro-micro/historical-delineation-files.html) |
| College Scorecard | `scorecard_raw.csv` | [College Scorecard Data](https://collegescorecard.ed.gov/data/) |
| BEA county GDP, personal income, and regional price parities | `CAGDP1__ALL_AREAS_2001_2024.csv`, `CAINC1__ALL_AREAS_1969_2024.csv`, `RPP.xlsx` | [BEA Regional Data Downloads](https://apps.bea.gov/regional/downloadzip.htm) |

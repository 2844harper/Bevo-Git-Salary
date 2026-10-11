# Bevo-Git-Salary

**Do more expensive colleges deliver higher earnings?**

A Python midterm project that joins U.S. college cost data with graduate earnings, local price levels, and county economic data — to ask which colleges give the best return per dollar.

## The questions

- **Main:** Do colleges that cost more (tuition + local living costs) deliver higher post-graduation earnings? Which schools are most cost-efficient?
- **Secondary:** Does the cost–earnings relationship differ between public and private schools?
- **Local economy:** Are colleges in richer or faster-growing counties more expensive, and do their graduates earn more?

## Team

| Part | Member | Job |
|------|--------|-----|
| A | Sehun | College Scorecard — collected and cleaned the 1,162-school base dataset |
| B | Linda Wu | Cost of living — BEA Regional Price Parities + HUD rents; price-adjusted ("real") earnings |
| C | Edward | County economics — BEA GDP & personal income by county, joined via HUD ZIP–county crosswalk |
| D | Harper | Analysis — cost metrics, regressions, figures, reproducibility |

## Data sources

| Source | What we use | Joined on |
|--------|-------------|-----------|
| College Scorecard (U.S. Dept. of Education) | Tuition, net price, published cost of attendance (COA), median earnings 6 & 10 yrs after entry, public/private control, enrollment | UNITID |
| BEA Regional Price Parities, 2024 | Metro-area price index (U.S. average = 100) | CBSA |
| HUD Fair Market Rents, FY2024 | Benchmark rents | County |
| BEA GDP by County & Personal Income by County | GDP, per-capita income, yearly growth rates, 10-yr average & CAGR (2010–2024) | County FIPS (via HUD ZIP–county crosswalk) |

Sample: 1,162 bachelor's-focused, non-profit schools with enrollment ≥ 1,000 and non-suppressed 10-year earnings (filters in `src/clean_scorecard.py`).

## How the pieces fit together

1. **A** builds the base table — one row per school with costs and earnings.
2. **B** maps each school to its metro area and attaches the local price index, so earnings are expressed in comparable ("real") dollars.
3. **C** maps each school to its county and attaches GDP, income, and growth rates — the local economic context.
4. **D** joins the B and C tables on `unitid`, builds cost metrics, runs the regressions, and draws the figures.

## Key terms, in plain words

- **Published COA** — the school's official sticker price for one academic year: tuition + fees + books + living expenses, already bundled together. We use it as-is; adding anything on top would double-count costs.
- **RPP** — a price *index*, not a dollar amount (U.S. average = 100). We only ever divide by it, never add it to costs.
- **Efficiency** = yearly earnings ÷ yearly cost. **Payback period** = 4-year total cost ÷ yearly earnings.

## Findings (Part D)

- **Pricier schools → higher earnings:** earnings_10yr = 40,797 + 0.41 × coa_published (R² = 0.34, N = 1,151). Each extra $1 of annual COA is associated with about $0.41 higher median yearly earnings 10 years after entry.
- **Public schools win on efficiency:** the cost–earnings slope is steeper for publics (interaction +0.40, p < 0.01); median efficiency 2.12 (public) vs 1.07 (private); median payback 1.9 vs 3.8 years. The top of the ranking is low-tuition publics such as CUNY Baruch (5.36).
- **Local economy:** county per-capita income moves with both graduate earnings (+0.17) and COA (+0.21); county GDP 10-year growth is significant for neither.
- Full regression tables: `artifacts/regression_results.txt`. Figures: `artifacts/figures/`.

## Limitations

1. Scorecard earnings cover mostly federal-aid recipients; some cells are privacy-suppressed.
2. COA is the sticker price, not the net price students actually pay.
3. 248 schools have no RPP (micropolitan / non-metro areas); 11 lack COA — excluded from metrics and regressions.
4. 43 schools could not be matched to counties (mostly Virginia + U.S. territories) — excluded and documented.
5. County economic data describes where the college sits, not necessarily where its graduates work.
6. Connecticut's newer county-equivalent codes don't match some older HUD county codes (18 schools without HUD matches).
7. FY2024 HUD rents are benchmarks, not rents students or graduates actually pay.
8. One snapshot in time and cross-sectional: these are associations, not causal proof.
9. A planned COA web-scraping validation was dropped by team decision (scraping ~30 school sites was too uncertain); the published-vs-Scorecard COA check was not done.

## Reproduce it

```bash
python -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python src/analysis.py
```

This rebuilds `data/processed/college_metrics.csv`, `artifacts/regression_results.txt`, and `artifacts/figures/*.png` from the processed tables. Verified in a clean environment on 2026-10-11. All code is `black`-formatted (config in `pyproject.toml`).

## Files

- `src/collect_scorecard.py`, `src/clean_scorecard.py` — Part A
- `src/collect_cost_of_living.py`, `src/clean_rpp.py`, `src/clean_hud_crosswalk.py`, `src/clean_county_cbsa.py`, `src/assign_college_cbsa.py`, `src/merge_college_rpp.py`, `src/merge.py` — Part B
- `src/GDPCleaning.py`, `src/INCOMECLEAN.py`, `src/FIPSADD.py`, `src/Final_Combine_For_PART_C.py` (+ `Working_Notes_PartC.md`) — Part C
- `src/analysis.py` — Part D
- `data/raw/` — raw downloads · `data/processed/` — cleaned and merged tables
- `artifacts/` — regression tables and figures

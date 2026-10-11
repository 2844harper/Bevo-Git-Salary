# Bevo-Git-Salary
python midterm project
   # Bevo-Git-Salary
   Do more expensive colleges deliver higher earnings?
      #PART B
         Part B adds regional cost of living to college-level data to compare
         college tuition and graduate earnings across different locations

         limitations
           1. Some schools are in micropolitan areas or regions not covered by the cleaned metropolitan RPP dataset
           2. Connecticut's newer county-equivalent geographic codes do not match some older HUD county codes, leaving 18 schools without HUD matches
           3. FY2024 HUD rents are benchmarks rather than actual rents paid by students or graduates

      #PART C Part
         push big data source here
         and also cleaning process record

      #PART D -- analysis (src/analysis.py)
         Part D joins the Part B table (college_rpp_adjusted.csv: Scorecard
         costs, RPP-adjusted earnings) with the Part C table
         (SCHOOL_INCOME_LOCALGDP.csv: county GDP / income + growth rates) on
         unitid, then computes cost metrics, runs the earnings-on-cost
         regressions, and saves figures.

         methods
           - Annual cost = Scorecard published COA (coa_published). It already
             bundles tuition, fees, books, supplies and living expenses, so
             nothing is added on top (no double counting, per team discussion).
             RPP is a price index, not dollars: it is only used as a divisor
             for real earnings, never added to costs.
           - total_cost_4yr = coa_published * 4
           - payback_years = total_cost_4yr / earnings_10yr (years of median
             post-graduation earnings needed to cover the 4-year sticker cost)
           - efficiency = earnings_10yr / coa_published (annual earnings per
             annual cost dollar); efficiency_rpp uses RPP-adjusted earnings
           - OLS with HC1 robust SE: (1) earnings_10yr ~ coa_published;
             (2) with public/private interaction; (3) RPP-adjusted earnings
             robustness; (4)-(5) county per-capita income + GDP 10-yr CAGR
             against earnings and against COA
           - outputs: data/processed/college_metrics.csv,
             artifacts/regression_results.txt, artifacts/figures/*.png

         findings (N = 1,162 schools: 523 public, 639 private_nonprofit)
           - Main spec: earnings_10yr = 40,797 + 0.41 * coa_published
             (R^2 = 0.34). Each extra dollar of annual COA is associated with
             about $0.41 higher median annual earnings 10 years after entry.
           - Public vs private: the cost-earnings slope is steeper for public
             schools (+0.40 vs private baseline, p < 0.01, R^2 = 0.49).
           - Cost-efficiency (earnings/cost): median public 2.12 vs private
             1.07; payback period: median public 1.9 yrs vs private 3.8 yrs.
             Most cost-efficient are low-tuition publics (CUNY Baruch 5.36,
             CUNY City College 4.59, ...).
           - Local economy: county per-capita income is positively related to
             both graduate earnings (+0.17 per $1) and COA (+0.21 per $1);
             county GDP 10-yr CAGR is not significant for either.

         limitations
           1. Scorecard earnings cover mostly federal-aid recipients; some
              cells are privacy-suppressed.
           2. COA is the sticker price, not the net price students pay.
           3. 248 schools lack RPP (micropolitan / non-metro areas); 11 lack
              COA and are excluded from metrics and regressions.
           4. County economic conditions describe where the college is, not
              necessarily where graduates work.
           5. Cross-sectional: associations, not causal effects.
           6. The COA web-scraping validation was dropped by team decision
              (10/10); the published-vs-Scorecard COA side check was not done.
           7. Mock data (D2) was skipped: real merged data was already
              available, and mock data was only for early development.

         reproducibility
           python -m venv venv && venv/bin/pip install -r requirements.txt
           && venv/bin/python src/analysis.py
           Tested in a clean venv on 2026-10-11: installs from
           requirements.txt and reproduces all outputs above.

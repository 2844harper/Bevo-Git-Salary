"""Part D analysis: cost vs. earnings by college.

Implements D3-D5 of the midterm project plan
("Midterm Project Plan: Cost vs. Earnings by College"):

  D3. Compute total cost, payback period and an efficiency score.
  D4. Regress earnings on cost (public vs private comparison), and examine
      how county GDP growth and per-capita income relate to college costs
      and graduate earnings.
  D5. Save figures to artifacts/.

Cost definitions follow the team's agreed revisions (Google Doc comments):
  - Annual cost = Scorecard COA (``coa_published``), which already bundles
    tuition, fees, books, supplies and living expenses, so nothing is added
    on top of it (no double counting).
  - RPP is a price *index*, never a dollar amount: it is only used as a
    divisor to express earnings in comparable dollars, never added to costs.
  - Efficiency = annual earnings / annual cost (earnings-cost ratio).

Inputs (built by Parts A-C, already merged into main):
  data/processed/college_rpp_adjusted.csv   (Part B: costs, RPP-adjusted earnings)
  data/processed/SCHOOL_INCOME_LOCALGDP.csv (Part C: county GDP / income levels + growth)

Outputs:
  data/processed/college_metrics.csv   (D3 metrics table)
  artifacts/regression_results.txt     (D4 regression tables)
  artifacts/figures/*.png              (D5 figures)
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]

RPP_FILE = ROOT / "data/processed/college_rpp_adjusted.csv"
COUNTY_FILE = ROOT / "data/processed/SCHOOL_INCOME_LOCALGDP.csv"
METRICS_FILE = ROOT / "data/processed/college_metrics.csv"
RESULTS_FILE = ROOT / "artifacts/regression_results.txt"
FIG_DIR = ROOT / "artifacts/figures"

PROGRAM_YEARS = 4  # a bachelor's degree is priced as 4 annual COAs


def load_analysis_table() -> pd.DataFrame:
    """Inner-join Part B and Part C tables on unitid; report coverage."""
    rpp = pd.read_csv(RPP_FILE, dtype={"unitid": str})
    county = pd.read_csv(COUNTY_FILE, dtype={"unitid": str})

    n_no_id = int(county["unitid"].isna().sum())
    if n_no_id:
        print(
            f"Dropping {n_no_id} county rows with missing unitid "
            f"(cannot be joined)."
        )
        county = county.dropna(subset=["unitid"])

    merged = rpp.merge(
        county[
            [
                "unitid",
                "county_fips",
                "income_2024",
                "GDP_growth_10y_avg",
                "GDP_growth_10y_CAGR",
                "income_growth_10y_avg",
                "income_growth_10y_CAGR",
            ]
        ],
        on="unitid",
        how="inner",
        validate="one_to_one",
        suffixes=("", "_county"),
    )
    print(
        f"Part B rows: {len(rpp)}, Part C rows: {len(county)}, "
        f"merged: {len(merged)}"
    )
    print("By control:\n", merged["control"].value_counts())
    return merged


def add_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """D3: total 4-year cost, payback period and efficiency scores."""
    df = df.copy()
    # Annual cost is the published COA itself (tuition + living already inside).
    df["annual_cost"] = df["coa_published"]
    df["total_cost_4yr"] = df["coa_published"] * PROGRAM_YEARS
    # Years of median post-graduation earnings needed to cover the degree cost.
    df["payback_years"] = df["total_cost_4yr"] / df["earnings_10yr"]
    # Earnings-cost ratio: annual earnings per annual cost dollar.
    df["efficiency"] = df["earnings_10yr"] / df["coa_published"]
    # Same ratio with RPP-adjusted ("true") earnings (Part B).
    df["efficiency_rpp"] = df["earnings_10yr_rpp_adj"] / df["coa_published"]

    n_missing_cost = int(df["coa_published"].isna().sum())
    n_missing_rpp = int(df["earnings_10yr_rpp_adj"].isna().sum())
    print(f"Schools missing COA (metrics undefined): {n_missing_cost}")
    print(f"Schools missing RPP (RPP metrics undefined): {n_missing_rpp}")

    summary = (
        df.groupby("control")[
            ["total_cost_4yr", "payback_years", "efficiency", "efficiency_rpp"]
        ]
        .median()
        .round(2)
    )
    print("\nMedian metrics by control:\n", summary)

    top = df.nlargest(10, "efficiency")[
        ["name", "control", "state", "coa_published", "earnings_10yr", "efficiency"]
    ]
    print("\nTop 10 most cost-efficient schools (earnings/cost):")
    print(top.to_string(index=False))
    return df


def _fit(formula: str, df: pd.DataFrame, subset: str):
    """OLS with heteroskedasticity-robust (HC1) standard errors."""
    data = df.dropna(subset=subset)
    model = smf.ols(formula, data=data).fit(cov_type="HC1")
    return model, len(data)


def run_regressions(df: pd.DataFrame) -> str:
    """D4: earnings-on-cost regressions, public vs private, county economics."""
    lines = []
    lines.append("PART D REGRESSION RESULTS")
    lines.append("=" * 60)

    specs = [
        (
            "(1) earnings_10yr ~ coa_published  [main spec]",
            "earnings_10yr ~ coa_published",
            ["earnings_10yr", "coa_published"],
        ),
        (
            "(2) earnings_10yr ~ coa_published * control  [public vs private]",
            "earnings_10yr ~ coa_published * control",
            ["earnings_10yr", "coa_published", "control"],
        ),
        (
            "(3) earnings_10yr_rpp_adj ~ coa_published * control  [RPP robustness]",
            "earnings_10yr_rpp_adj ~ coa_published * control",
            ["earnings_10yr_rpp_adj", "coa_published", "control"],
        ),
        (
            "(4) earnings_10yr ~ county income + GDP growth  [local economy]",
            "earnings_10yr ~ income_2024 + GDP_growth_10y_CAGR",
            ["earnings_10yr", "income_2024", "GDP_growth_10y_CAGR"],
        ),
        (
            "(5) coa_published ~ county income + GDP growth  [local economy]",
            "coa_published ~ income_2024 + GDP_growth_10y_CAGR",
            ["coa_published", "income_2024", "GDP_growth_10y_CAGR"],
        ),
    ]

    for title, formula, subset in specs:
        model, n = _fit(formula, df, subset)
        lines.append("")
        lines.append(title)
        lines.append(f"N = {n}, R-squared = {model.rsquared:.4f}")
        lines.append("-" * 60)
        for name in model.params.index:
            coef = model.params[name]
            se = model.bse[name]
            p = model.pvalues[name]
            stars = (
                "***" if p < 0.01 else ("**" if p < 0.05 else ("*" if p < 0.1 else ""))
            )
            lines.append(f"{name:45s} {coef:12.4f} ({se:9.4f}){stars}")
        lines.append("(HC1 robust SE in parentheses; * p<0.1, ** p<0.05, *** p<0.01)")

    text = "\n".join(lines)
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_FILE.write_text(text + "\n")
    print("\n" + text)
    print(f"\nSaved regression tables to: {RESULTS_FILE}")
    return text


def _scatter_with_fit(ax, df, x, y, hue, title, xlabel, ylabel):
    """Scatter by group with a per-group OLS fit line."""
    colors = {"public": "#1f77b4", "private_nonprofit": "#ff7f0e"}
    for group, sub in df.dropna(subset=[x, y, hue]).groupby(hue):
        ax.scatter(
            sub[x],
            sub[y],
            s=12,
            alpha=0.45,
            color=colors.get(group, "gray"),
            label=str(group),
        )
        slope, intercept = np.polyfit(sub[x], sub[y], 1)
        xs = np.array([sub[x].min(), sub[x].max()])
        ax.plot(
            xs, slope * xs + intercept, color=colors.get(group, "gray"), linewidth=1.5
        )
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(frameon=False, fontsize=9)


def make_figures(df: pd.DataFrame) -> None:
    """D5: save all figures to artifacts/figures/."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Cost vs earnings by control, with fit lines.
    fig, ax = plt.subplots(figsize=(8, 5.5))
    _scatter_with_fit(
        ax,
        df,
        "coa_published",
        "earnings_10yr",
        "control",
        "Cost of attendance vs. median earnings 10 yrs after entry",
        "Published cost of attendance, annual (USD)",
        "Median earnings 10 yrs after entry (USD)",
    )
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_cost_vs_earnings.png", dpi=150)
    plt.close(fig)

    # 2. Efficiency (earnings/cost) distribution by control.
    fig, ax = plt.subplots(figsize=(8, 5))
    eff = df.dropna(subset=["efficiency", "control"])
    hi = eff["efficiency"].quantile(0.99)
    for group, sub in eff[eff["efficiency"] <= hi].groupby("control"):
        ax.hist(sub["efficiency"], bins=30, alpha=0.55, label=str(group))
    ax.set_title("Distribution of cost-efficiency (annual earnings / annual cost)")
    ax.set_xlabel("Efficiency ratio")
    ax.set_ylabel("Number of schools")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_efficiency_by_control.png", dpi=150)
    plt.close(fig)

    # 3. Payback period by control (99th pct clip for display).
    fig, ax = plt.subplots(figsize=(7, 5))
    pay = df.dropna(subset=["payback_years", "control"])
    cap = pay["payback_years"].quantile(0.99)
    data = [
        g["payback_years"].clip(upper=cap).values for _, g in pay.groupby("control")
    ]
    ax.boxplot(
        data, tick_labels=[str(c) for c, _ in pay.groupby("control")], showfliers=False
    )
    ax.set_title("Payback period by control (years to cover 4-yr cost)")
    ax.set_ylabel("Years")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_payback_by_control.png", dpi=150)
    plt.close(fig)

    # 4. County per-capita income vs graduate earnings.
    fig, ax = plt.subplots(figsize=(8, 5.5))
    _scatter_with_fit(
        ax,
        df,
        "income_2024",
        "earnings_10yr",
        "control",
        "County per-capita income vs. graduate earnings",
        "County per-capita personal income, 2024 (USD)",
        "Median earnings 10 yrs after entry (USD)",
    )
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_county_income_vs_earnings.png", dpi=150)
    plt.close(fig)

    # 5. County GDP growth (10-yr CAGR, %) vs graduate earnings.
    fig, ax = plt.subplots(figsize=(8, 5.5))
    _scatter_with_fit(
        ax,
        df,
        "GDP_growth_10y_CAGR",
        "earnings_10yr",
        "control",
        "County GDP growth (10-yr CAGR) vs. graduate earnings",
        "County real GDP growth, 10-yr CAGR (%)",
        "Median earnings 10 yrs after entry (USD)",
    )
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_gdp_growth_vs_earnings.png", dpi=150)
    plt.close(fig)

    saved = sorted(p.name for p in FIG_DIR.glob("*.png"))
    print(f"\nSaved {len(saved)} figures to {FIG_DIR}/: {saved}")


def main() -> None:
    df = load_analysis_table()
    df = add_metrics(df)

    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(METRICS_FILE, index=False)
    print(f"\nSaved metrics table ({len(df)} schools) to: {METRICS_FILE}")

    run_regressions(df)
    make_figures(df)
    print("\nPart D analysis complete.")


if __name__ == "__main__":
    main()

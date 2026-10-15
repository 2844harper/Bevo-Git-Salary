"""Part D analysis: cost vs. earnings by college.

Implements D3-D5 of the midterm project plan
("Midterm Project Plan: Cost vs. Earnings by College"):

  D3. Compute total cost, payback period and an efficiency score.
  D4. Regress earnings on cost (public vs private comparison), and examine
      how county GDP growth and per-capita income relate to college costs
      and graduate earnings.
  D5. Save descriptive and regression figures to artifacts/figures/.

Cost definitions follow the team's agreed revisions (Google Doc comments):
  - Annual cost = Scorecard COA (``coa_published``), which already bundles
    tuition, fees, books, supplies and living expenses, so nothing is added
    on top of it (no double counting).
  - RPP is a 2022 price *index*, never a dollar amount: it is only used as
    a divisor to express earnings in comparable dollars, never added to costs.
  - Efficiency = annual earnings / annual cost (earnings-cost ratio).

County controls use observed 2022 income, log real GDP, and the unchanged
2014-2024 GDP CAGR. Scorecard earnings are 2020-2021 observations in 2022
dollars; COA retains its own reporting year. No county forecasts are used.

Inputs (built by Parts A-C):
  data/processed/college_rpp_adjusted.csv
    (Part B: costs, 2022-RPP-adjusted earnings)
  data/processed/SCHOOL_INCOME_LOCALGDP.csv
    (Part C: county GDP / income levels + growth)

Outputs:
  artifacts/regression_results.txt             (D4 regression tables)
  artifacts/figures/*.png                      (D5 descriptive figures)
  artifacts/figures/regression/*.png            (D5 model-based figures)

D3 metrics are calculated in memory; no CSV is written.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, StrMethodFormatter
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]

RPP_FILE = ROOT / "data/processed/college_rpp_adjusted.csv"
COUNTY_FILE = ROOT / "data/processed/SCHOOL_INCOME_LOCALGDP.csv"
OUTPUT_DIR = ROOT / "artifacts"
RESULTS_FILE = OUTPUT_DIR / "regression_results.txt"
FIG_DIR = OUTPUT_DIR / "figures"
REG_FIG_DIR = FIG_DIR / "regression"

PROGRAM_YEARS = 4  # a bachelor's degree is priced as 4 annual COAs

# Growth intentionally spans 2014-2024, beyond the observed 2022 county levels.
COMMON_COUNTY_CONTROLS = "income_2022 + log_gdp_2022 + GDP_growth_10y_CAGR"
COMMON_COUNTY_COLUMNS = ["income_2022", "log_gdp_2022", "GDP_growth_10y_CAGR"]


def load_analysis_table() -> pd.DataFrame:
    """Read the configured school/county CSVs and return one table by school ID."""
    rpp = pd.read_csv(
        RPP_FILE, dtype={"unitid": str, "county_fips": str, "cbsa": str, "zip5": str}
    )
    if "rpp_2022" not in rpp.columns:
        raise ValueError(
            "Expected rpp_2022; rebuild the inputs with scripts 07 and 11."
        )
    # Recalculate in memory so cached adjusted earnings cannot use another RPP year.
    price_index = pd.to_numeric(rpp["rpp_2022"], errors="coerce")
    rpp["rpp_2022"] = price_index.where(np.isfinite(price_index) & price_index.gt(0))
    rpp["earnings_10yr"] = pd.to_numeric(rpp["earnings_10yr"], errors="coerce")
    rpp["earnings_10yr_rpp_adj"] = rpp["earnings_10yr"] / (rpp["rpp_2022"] / 100)

    county = pd.read_csv(COUNTY_FILE, comment="#", dtype={"unitid": str})

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
                "income_2022",
                "gdp_2022",
                "GDP_growth_10y_CAGR",
            ]
        ],
        on="unitid",
        how="inner",
        validate="one_to_one",
    )
    # Keep observed 2022 levels; invalid GDP stays missing when taking its log.
    for column in ["income_2022", "gdp_2022", "GDP_growth_10y_CAGR"]:
        numeric = pd.to_numeric(merged[column], errors="coerce")
        merged[column] = numeric.where(np.isfinite(numeric))
    merged["log_gdp_2022"] = np.log(merged["gdp_2022"].where(merged["gdp_2022"] > 0))
    print(
        f"Part B rows: {len(rpp)}, Part C rows: {len(county)}, "
        f"merged: {len(merged)}"
    )
    print("By control:\n", merged["control"].value_counts())
    print("Schools with 2022 RPP:", merged["rpp_2022"].notna().sum())
    print("Schools with observed 2022 income:", merged["income_2022"].notna().sum())
    print("Schools with observed 2022 GDP:", merged["log_gdp_2022"].notna().sum())
    return merged


def add_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Return df's cost and earnings metrics, treating invalid amounts as missing."""
    df = df.copy()
    for column in ["coa_published", "earnings_10yr", "earnings_10yr_rpp_adj"]:
        numeric = pd.to_numeric(df[column], errors="coerce")
        df[column] = numeric.where(np.isfinite(numeric) & numeric.ge(0))

    df["annual_cost"] = df["coa_published"]
    df["total_cost_4yr"] = df["annual_cost"] * PROGRAM_YEARS
    positive_cost = df["annual_cost"].where(df["annual_cost"] > 0)
    positive_earnings = df["earnings_10yr"].where(df["earnings_10yr"] > 0)
    # This simple ratio does not align reported COA with earnings' price year.
    df["payback_years"] = df["total_cost_4yr"] / positive_earnings
    df["efficiency"] = df["earnings_10yr"] / positive_cost
    df["efficiency_rpp"] = df["earnings_10yr_rpp_adj"] / positive_cost

    n_missing_cost = int(df["coa_published"].isna().sum())
    n_missing_adjusted = int(df["earnings_10yr_rpp_adj"].isna().sum())
    print(f"Schools missing COA (metrics undefined): {n_missing_cost}")
    print(
        "Schools missing adjusted earnings (RPP metrics undefined): "
        f"{n_missing_adjusted}"
    )

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


def _fit(formula: str, df: pd.DataFrame, subset: list[str]):
    """Fit formula on df rows complete for subset; return HC1 results and N."""
    data = df[subset].replace([np.inf, -np.inf], np.nan)
    data = data.dropna()
    if data.empty:
        raise ValueError(f"No complete observations for model: {formula}")
    model = smf.ols(formula, data=data, missing="raise").fit(cov_type="HC1")
    return model, int(model.nobs)


def run_regressions(df: pd.DataFrame) -> dict:
    """Fit five models on df, save text tables, and return results by model number."""
    lines = [
        "PART D REGRESSION RESULTS - OBSERVED 2022 COUNTY LEVELS AND RPP",
        "=" * 72,
        "All five specifications include observed 2022 county per-capita income,",
        "log observed 2022 county real GDP, and unchanged 2014-2024 GDP CAGR.",
        "GDP is measured in thousands of chained 2017 USD; income is nominal USD.",
        "Model 2 is the main public/private specification; model 3 uses 2022 RPP.",
        "Scorecard earnings and COA retain their original observed reporting years.",
        "The 2014-2024 CAGR is retrospective and includes years after 2022.",
        "HC1 standard errors are not clustered by county; associations are not causal.",
        "Model 3 may have a smaller estimation sample because of missing RPP.",
    ]

    specs = [
        (
            "(1) college COA -> earnings | 2022 county controls [benchmark]",
            f"earnings_10yr ~ coa_published + {COMMON_COUNTY_CONTROLS}",
            ["earnings_10yr", "coa_published"] + COMMON_COUNTY_COLUMNS,
        ),
        (
            "(2) public/private interaction | 2022 county controls [main]",
            f"earnings_10yr ~ coa_published * control + {COMMON_COUNTY_CONTROLS}",
            ["earnings_10yr", "coa_published", "control"] + COMMON_COUNTY_COLUMNS,
        ),
        (
            "(3) 2022-RPP-adjusted earnings | 2022 county controls [robustness]",
            "earnings_10yr_rpp_adj ~ coa_published * control + "
            f"{COMMON_COUNTY_CONTROLS}",
            ["earnings_10yr_rpp_adj", "coa_published", "control"]
            + COMMON_COUNTY_COLUMNS,
        ),
        (
            "(4) earnings on observed 2022 county economy",
            f"earnings_10yr ~ {COMMON_COUNTY_CONTROLS}",
            ["earnings_10yr"] + COMMON_COUNTY_COLUMNS,
        ),
        (
            "(5) college COA on observed 2022 county economy",
            f"coa_published ~ {COMMON_COUNTY_CONTROLS}",
            ["coa_published"] + COMMON_COUNTY_COLUMNS,
        ),
    ]

    models = {}
    for number, (title, formula, subset) in enumerate(specs, start=1):
        model, n = _fit(formula, df, subset)
        models[number] = model
        lines.extend(
            [
                "",
                title,
                f"Formula: {formula}",
                f"N = {n}, R-squared = {model.rsquared:.4f}, "
                f"Adj. R-squared = {model.rsquared_adj:.4f}",
                "-" * 72,
            ]
        )
        for name in model.params.index:
            coef = model.params[name]
            se = model.bse[name]
            p = model.pvalues[name]
            stars = (
                "***" if p < 0.01 else ("**" if p < 0.05 else ("*" if p < 0.1 else ""))
            )
            lines.append(f"{name:45s} {coef:12.4f} ({se:9.4f}){stars}  p={p:.4g}")
        lines.append("(HC1 robust SE; * p<0.1, ** p<0.05, *** p<0.01)")

    text = "\n".join(lines)
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_FILE.write_text(text + "\n", encoding="utf-8")
    print("\n" + text)
    print(f"\nSaved regression tables to: {RESULTS_FILE}")
    return models


def _estimation_data(model) -> pd.DataFrame:
    """Return the school rows used to estimate the supplied fitted model."""
    return model.model.data.frame.loc[model.model.data.row_labels]


def _prediction_grid(model, column, values, control=None) -> pd.DataFrame:
    """Return a model grid for column/values and optional control, fixing medians."""
    sample = _estimation_data(model)
    columns = COMMON_COUNTY_COLUMNS + (
        ["coa_published"] if "coa_published" in model.params else []
    )
    reference = {name: sample[name].median() for name in columns}
    grid = pd.DataFrame(reference, index=range(len(values)))
    grid[column] = values
    if control is not None:
        grid["control"] = control
    return grid


def _prediction_curve(ax, model, grid, x, color, label):
    """Add model predictions for grid to ax at x with HC1 bands; return None."""
    prediction = model.get_prediction(grid).summary_frame(alpha=0.05)
    ax.plot(x, prediction["mean"].to_numpy(), color=color, label=label)
    ax.fill_between(
        x,
        prediction["mean_ci_lower"].to_numpy(),
        prediction["mean_ci_upper"].to_numpy(),
        color=color,
        alpha=0.18,
    )


def _save_figure(fig, path: Path) -> Path:
    """Save fig to path, close it even if saving fails, and return path."""
    try:
        fig.savefig(path, dpi=150)
    finally:
        plt.close(fig)
    return path


def _finish_regression_figure(fig, filename, note):
    """Save fig with note under filename, close it, and return the output path."""
    fig.text(0.5, 0.055, note, ha="center", fontsize=9)
    fig.text(
        0.5,
        0.015,
        "95% HC1 confidence intervals for the mean; not clustered by county. "
        "Associations, not causal effects.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.12, 1, 0.94))
    return _save_figure(fig, REG_FIG_DIR / filename)


def _cost_prediction_figure(models):
    """Plot fitted models 1-3 and return the saved cost-prediction figure path."""
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.8))
    fig.suptitle("Model-based cost-earnings relationships", fontsize=15)
    groups = [
        ("private_nonprofit", "Private nonprofit", "#ff7f0e"),
        ("public", "Public", "#1f77b4"),
    ]
    titles = {
        1: "All schools (benchmark)",
        2: "Public vs. private (main)",
        3: "2022-RPP earnings (robustness)",
    }
    for number, ax in enumerate(axes, start=1):
        model = models[number]
        sample = _estimation_data(model)
        curves = [(None, "All schools", "#444444")] if number == 1 else groups
        for control, label, color in curves:
            costs = (
                sample["coa_published"]
                if control is None
                else sample.loc[sample["control"] == control, "coa_published"]
            )
            if costs.empty:
                continue
            # Restrict each curve to its own group's central observed cost range.
            low, high = costs.quantile([0.05, 0.95])
            values = np.linspace(low, high, 100)
            grid = _prediction_grid(model, "coa_published", values, control)
            _prediction_curve(ax, model, grid, values, color, label)
        ax.set_title(f"Model {number}: {titles[number]}\nN = {int(model.nobs):,}")
        ax.set_xlabel("Annual cost of attendance (USD)")
        ax.set_ylabel(
            "Predicted RPP-adjusted earnings (2022 USD)"
            if number == 3
            else "Predicted historical earnings (2022 USD)"
        )
        ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
        ax.grid(alpha=0.2)
        ax.legend(frameon=False, fontsize=9)
    return _finish_regression_figure(
        fig,
        "fig_reg_cost_predictions.png",
        "County controls fixed at each model's sample medians; shaded bands are "
        "mean confidence intervals.\nCurves span each group's 5th-95th cost "
        "percentiles. Model 3 uses a different sample and reference profile.",
    )


def _county_effect_figure(model, number):
    """Plot county predictors for model number 4 or 5; return the figure path."""
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.8))
    sample = _estimation_data(model)
    outcome = "historical earnings" if number == 4 else "annual college cost"
    fig.suptitle(
        f"Model {number}: county conditions and predicted {outcome} "
        f"(N = {int(model.nobs):,})",
        fontsize=15,
    )
    labels = [
        "Observed county income per capita, 2022 (USD)",
        "Observed county real GDP, 2022\n(billions of chained 2017 USD; log scale)",
        "Historical county GDP CAGR, 2014-2024 (%)",
    ]
    for ax, column, xlabel in zip(axes, COMMON_COUNTY_COLUMNS, labels):
        low, high = sample[column].quantile([0.05, 0.95])
        values = np.linspace(low, high, 100)
        grid = _prediction_grid(model, column, values)
        # The model uses log GDP; display the original GDP unit on a log axis.
        x = np.exp(values) / 1_000_000 if column == "log_gdp_2022" else values
        _prediction_curve(ax, model, grid, x, "#1f77b4", "Predicted mean")
        if column == "log_gdp_2022":
            ax.set_xscale("log")
        elif column == "income_2022":
            ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
            ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.set_xlabel(xlabel)
        ax.set_ylabel(f"Predicted {outcome} (USD)")
        ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
        ax.grid(alpha=0.2)
    return _finish_regression_figure(
        fig,
        f"fig_reg_county_effects_model_{number}.png",
        "Other county controls fixed at this model's sample medians. Each "
        "predictor spans its 5th-95th percentiles.\nShaded bands describe "
        "uncertainty in the mean, not the prediction range for an individual school.",
    )


def make_regression_figures(models) -> None:
    """Save three prediction figures from fitted models; return None."""
    REG_FIG_DIR.mkdir(parents=True, exist_ok=True)
    saved = [
        _cost_prediction_figure(models),
        _county_effect_figure(models[4], 4),
        _county_effect_figure(models[5], 5),
    ]
    print(f"\nSaved {len(saved)} regression figures to {REG_FIG_DIR}/:")
    for path in saved:
        print(path.name)


def _scatter_with_fit(ax, df, x, y, hue, title, xlabel, ylabel):
    """Plot df[x] versus df[y] by hue on ax; fit lines where x varies; return None."""
    colors = {"public": "#1f77b4", "private_nonprofit": "#ff7f0e"}
    complete = df[[x, y, hue]].replace([np.inf, -np.inf], np.nan)
    complete = complete.dropna()
    for group, sub in complete.groupby(hue):
        ax.scatter(
            sub[x],
            sub[y],
            s=12,
            alpha=0.45,
            color=colors.get(group, "gray"),
            label=str(group),
        )
        if sub[x].nunique() >= 2:
            slope, intercept = np.polyfit(sub[x], sub[y], 1)
            xs = np.array([sub[x].min(), sub[x].max()])
            ax.plot(
                xs,
                slope * xs + intercept,
                color=colors.get(group, "gray"),
                linewidth=1.5,
            )
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(frameon=False, fontsize=9)


def make_figures(df: pd.DataFrame) -> None:
    """Save six descriptive figures from df; return None."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    scatter_specs = [
        (
            "fig_cost_vs_earnings.png",
            "coa_published",
            "Cost of attendance vs. median earnings 10 yrs after entry",
            "Published cost of attendance, annual (USD)",
        ),
        (
            "fig_county_income_vs_earnings.png",
            "income_2022",
            "Observed 2022 county income vs. Scorecard earnings",
            "Observed county per-capita personal income, 2022 (USD)",
        ),
        (
            "fig_gdp_growth_vs_earnings.png",
            "GDP_growth_10y_CAGR",
            "County GDP growth (10-yr CAGR) vs. graduate earnings",
            "County real GDP growth, 10-yr CAGR (%)",
        ),
        (
            "fig_county_gdp_2022_vs_earnings.png",
            "log_gdp_2022",
            "Observed 2022 county real GDP vs. Scorecard earnings",
            "Log county real GDP (2022 observed, thousands of chained 2017 USD)",
        ),
    ]
    saved = []
    for filename, column, title, xlabel in scatter_specs:
        fig, ax = plt.subplots(figsize=(8, 5.5))
        _scatter_with_fit(
            ax,
            df,
            column,
            "earnings_10yr",
            "control",
            title,
            xlabel,
            "Median earnings 10 yrs after entry (2022 USD)",
        )
        fig.tight_layout()
        saved.append(_save_figure(fig, FIG_DIR / filename))

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
    saved.append(_save_figure(fig, FIG_DIR / "fig_efficiency_by_control.png"))

    # Clip the top 1% of payback values for display only.
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
    saved.append(_save_figure(fig, FIG_DIR / "fig_payback_by_control.png"))

    names = sorted(path.name for path in saved)
    print(f"\nSaved {len(saved)} figures to {FIG_DIR}/: {names}")


def main() -> None:
    """Read configured inputs and save regression tables and plots; return None."""
    df = load_analysis_table()
    df = add_metrics(df)

    print(f"\nCalculated metrics for {len(df)} schools in memory; no CSV written.")

    models = run_regressions(df)
    make_figures(df)
    make_regression_figures(models)
    print("\nPart D observed-2022 county analysis complete.")


if __name__ == "__main__":
    main()

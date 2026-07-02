"""
Stage 6 — MDR-TB cascade shorter-window sub-analysis + required data-availability
Gantt chart (Stage-4 council mandate). Descriptive Mann-Kendall only for series
in the >=60%-missing tier; ARIMA-only forecast (AIC-selected, small-N appropriate)
for the <60%-missing MDR-cascade series on their own verified-continuous windows.
"""
import warnings
import numpy as np
import pandas as pd
import pymannkendall as mk
from pathlib import Path
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings("ignore")

OUT = Path(__file__).resolve().parent.parent / "outputs"
panel = pd.read_csv(OUT / "data" / "master_tb_national_panel.csv")
tier = pd.read_csv(OUT / "data" / "tb_series_forecast_tier_metadata.csv")

MDR_WINDOWS = {  # locked at Stage 4, docs/stage4_methodology.md §2
    "mdr_tb_started_treatment": (2008, 2024),
    "tx_success_mdr_pct": (2010, 2022),
    "new_cases_tested_rr_mdr_pct": (2011, 2024),
    "prev_treated_tested_rr_mdr_pct": (2010, 2024),
    "mdr_rr_tb_confirmed": (2010, 2024),
}
DESCRIPTIVE_ONLY = tier[tier["forecast_tier"] == "descriptive_only_excluded"]["variable"].tolist()

# --- Gantt-chart availability data (all TB indicators, full raw coverage) ---
tb_cols = [c for c in panel.columns if c not in ("year", "covid_era_flag")]
avail_rows = []
for col in tb_cols:
    nn = panel[["year", col]].dropna()
    if nn.empty:
        continue
    years_present = set(nn["year"])
    span_start, span_end = int(nn["year"].min()), int(nn["year"].max())
    full_span = set(range(span_start, span_end + 1))
    gaps = sorted(full_span - years_present)
    avail_rows.append({
        "variable": col, "first_year": span_start, "last_year": span_end,
        "n_points": len(nn), "n_gap_years_within_span": len(gaps),
        "gap_years": ",".join(map(str, gaps)) if gaps else "",
    })
avail_df = pd.DataFrame(avail_rows).sort_values("first_year")
avail_df.to_csv(OUT / "data" / "mdr_gantt_availability.csv", index=False)
print("Data-availability table (Gantt-chart source data) saved: mdr_gantt_availability.csv")
print(avail_df[avail_df["variable"].str.contains("mdr|MDR|xdr", case=False)].to_string(index=False))

# --- Descriptive-only tier: Mann-Kendall already computed in mann_kendall_trends.py; confirm here ---
print(f"\nDescriptive-only tier (>=60% missing, Mann-Kendall only, NO forecasting): {DESCRIPTIVE_ONLY}")

# --- MDR-cascade shorter-window ARIMA sub-forecast (small-N, ARIMA-only per council: rolling-origin
#     with N as low as 13-17 does not support a fair 3-model comparison at minimum-15yr initial window;
#     ARIMA-only descriptive forecast reported here as a distinct sub-analysis, clearly separated) ---
sub_results = []
for col, (start, end) in MDR_WINDOWS.items():
    sub = panel[(panel["year"] >= start) & (panel["year"] <= end)][["year", col]].dropna()
    if len(sub) < 5:
        continue
    mk_test = mk.original_test(sub[col].values)
    try:
        best_aic, best_fit = np.inf, None
        for p in range(3):
            for d in range(2):
                for q in range(2):
                    try:
                        fit = ARIMA(sub[col].values, order=(p, d, q)).fit()
                        if fit.aic < best_aic:
                            best_aic, best_fit = fit.aic, fit
                    except Exception:
                        continue
        one_step_forecast = float(best_fit.forecast(1)[0]) if best_fit else None
    except Exception:
        one_step_forecast = None
    sub_results.append({
        "variable": col, "window": f"{start}-{end}", "n_points": len(sub),
        "mk_trend": mk_test.trend, "mk_p": round(mk_test.p, 4), "sens_slope": round(mk_test.slope, 4),
        "arima_one_step_forecast_next_year": round(one_step_forecast, 2) if one_step_forecast else None,
    })

sub_df = pd.DataFrame(sub_results)
sub_df.to_csv(OUT / "tables" / "table3_mdr_subanalysis.csv", index=False)
print("\nMDR-TB cascade shorter-window sub-analysis (descriptive + ARIMA one-step, distinct from primary incidence forecast):")
print(sub_df.to_string(index=False))

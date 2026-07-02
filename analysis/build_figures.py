"""
Stage 6 — Figure production. Anti-slop: no pie charts, no 3D, no dual y-axes,
colourblind-safe (Okabe-Ito) palette, bars start at 0, titles state the finding,
direct labels preferred over legends where practical.
"""
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatch
from pathlib import Path
from libpysal.weights import Queen

OUT = Path(__file__).resolve().parent.parent / "outputs" / "figures"
DATA = Path(__file__).resolve().parent.parent / "outputs" / "data"
TABLES = Path(__file__).resolve().parent.parent / "outputs" / "tables"
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

# Okabe-Ito colourblind-safe palette
OI = {"blue": "#0072B2", "orange": "#E69F00", "green": "#009E73", "red": "#D55E00",
      "purple": "#CC79A7", "yellow": "#F0E442", "skyblue": "#56B4E9", "black": "#000000", "grey": "#999999"}

plt.rcParams.update({"font.size": 11, "font.family": "sans-serif", "axes.spines.top": False, "axes.spines.right": False,
                      "savefig.bbox": "tight"})


def wrap_title(ax_or_fig, text, width_chars=55, **kwargs):
    import textwrap
    wrapped = "\n".join(textwrap.wrap(text, width_chars))
    if hasattr(ax_or_fig, "set_title"):
        ax_or_fig.set_title(wrapped, **kwargs)
    else:
        ax_or_fig.suptitle(wrapped, **kwargs)

# ---------------------------------------------------------------------------
# Figure 1: National TB incidence trend, 2000-2024, with Sen's slope trend line
# ---------------------------------------------------------------------------
panel = pd.read_csv(DATA / "master_tb_national_panel.csv")
panel = panel[panel["year"].between(2000, 2024)]

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(panel["year"], panel["tb_incidence_per100k"], "o-", color=OI["blue"], linewidth=2, markersize=5, label="Observed incidence")
covid_years = panel[panel["covid_era_flag"] == 1]["year"]
ax.axvspan(2019.5, 2021.5, color=OI["red"], alpha=0.12, label="COVID-era window (2020-2021)")
x = panel["year"].values
y = panel["tb_incidence_per100k"].values
sen_slope = -4.0
intercept = y[0] - sen_slope * x[0]
ax.plot(x, intercept + sen_slope * x, "--", color=OI["grey"], linewidth=1.5, label="Sen's slope trend (-4.0/yr, p<0.0001)")
ax.set_ylim(0, None)
ax.set_xlabel("Year")
ax.set_ylabel("TB incidence per 100,000 population")
wrap_title(ax, "National TB incidence declined 42% from 2000 to 2024, a significant downward trend", width_chars=48)
ax.legend(loc="upper right", frameon=False)
fig.tight_layout()
fig.savefig(OUT / "figure1_incidence_trend.png", dpi=300)
plt.close(fig)
print("Saved figure1_incidence_trend.png")

# ---------------------------------------------------------------------------
# Figure 2: Rolling-origin CV forecast comparison, Model A vs B, per model
# ---------------------------------------------------------------------------
model_a = pd.read_csv(DATA / "forecast_folds_model_a.csv")
model_b = pd.read_csv(DATA / "forecast_folds_model_b.csv")
with open(DATA / "forecast_metrics_summary.json") as f:
    metrics = json.load(f)

fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=True)
models = [("arima_pred", "ARIMA", OI["blue"]), ("lstm_pred", "LSTM", OI["orange"]), ("xgb_pred", "XGBoost", OI["green"])]
for ax, (col, label, color) in zip(axes, models):
    ax.plot(model_a["fold_year"], model_a["true"], "ko-", label="Observed", markersize=5)
    ax.plot(model_a["fold_year"], model_a[col], "s--", color=color, label=f"{label} (Model A)", markersize=5)
    mae_a = metrics["model_a_full_panel"][col.split("_")[0]]["MAE"]
    mae_b = metrics["model_b_covid_excluded"][col.split("_")[0]]["MAE"]
    ax.set_title(f"{label}\nMAE={mae_a} (full panel) vs {mae_b} (COVID-excl.)")
    ax.set_xlabel("Fold year")
    if col == "arima_pred":
        ax.set_ylabel("TB incidence per 100,000")
    ax.legend(fontsize=8, frameon=False)
fig.suptitle("Rolling-origin forecasts: ARIMA tracks the smooth incidence decline far more closely than LSTM or XGBoost", y=1.02)
fig.tight_layout()
fig.savefig(OUT / "figure2_forecast_comparison.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print("Saved figure2_forecast_comparison.png")

# ---------------------------------------------------------------------------
# Figures 3-4: Choropleth + LISA cluster map (tvi_pca)
# ---------------------------------------------------------------------------
vuln = pd.read_csv(DATA / "master_district_vulnerability.csv")
cw = pd.read_csv(Path(__file__).resolve().parent.parent / "docs" / "district_crosswalk_261_to_260.csv")
gdf = gpd.read_file(RAW / "Ghana_New_260_District.geojson")
cw_small = cw[["master_sheet_district", "geojson_district"]].rename(columns={"master_sheet_district": "district"})
merged = vuln.merge(cw_small, on="district", how="left")
agg = merged.dropna(subset=["geojson_district"]).groupby("geojson_district").agg(
    tvi_pca=("tvi_pca", "mean"), tvi_equal=("tvi_equal", "mean")).reset_index()
gdf_join = gdf.merge(agg, left_on="DISTRICT", right_on="geojson_district", how="left")
gdf_join = gdf_join.dropna(subset=["tvi_pca"]).reset_index(drop=True)
w = Queen.from_dataframe(gdf_join, use_index=False)
if w.islands:
    gdf_join = gdf_join.drop(index=w.islands).reset_index(drop=True)
    w = Queen.from_dataframe(gdf_join, use_index=False)
w.transform = "r"

from esda.moran import Moran_Local
lisa = Moran_Local(gdf_join["tvi_pca"].values, w, permutations=999)
lisa_labels = {1: "High-High\n(high deprivation, clustered)", 2: "Low-High", 3: "Low-Low\n(low deprivation, clustered)", 4: "High-Low"}
gdf_join["lisa_label"] = np.where(lisa.p_sim < 0.05, gdf_join.index.map(lambda i: lisa_labels[lisa.q[i]]), "Not significant")

fig, ax = plt.subplots(figsize=(6.5, 8))
gdf_join.plot(column="tvi_pca", cmap="YlOrRd", linewidth=0.2, edgecolor="grey", ax=ax, legend=True,
              legend_kwds={"label": "TB-vulnerability index (TVI-PCA, standardised)", "shrink": 0.6})
ax.set_axis_off()
ax.set_title("District structural-vulnerability is concentrated in Ghana's northern regions\n(TVI-PCA, general deprivation index, 2021 — not observed TB burden)", fontsize=10)
fig.tight_layout()
fig.savefig(OUT / "figure3_tvi_choropleth.png", dpi=300)
plt.close(fig)
print("Saved figure3_tvi_choropleth.png")

lisa_colors = {"High-High\n(high deprivation, clustered)": OI["red"], "Low-Low\n(low deprivation, clustered)": OI["blue"],
               "Low-High": OI["skyblue"], "High-Low": OI["orange"], "Not significant": "#e0e0e0"}
fig, ax = plt.subplots(figsize=(6.5, 8))
for label, color in lisa_colors.items():
    sub = gdf_join[gdf_join["lisa_label"] == label]
    if len(sub):
        sub.plot(ax=ax, color=color, linewidth=0.2, edgecolor="grey")
handles = [mpatch.Patch(color=c, label=l.split("\n")[0]) for l, c in lisa_colors.items()]
ax.legend(handles=handles, loc="lower left", fontsize=8, frameon=False)
ax.set_axis_off()
n_sig = int((lisa.p_sim < 0.05).sum())
ax.set_title(f"LISA clusters: {n_sig} of {len(gdf_join)} districts show significant local clustering (p<0.05)", fontsize=10)
fig.tight_layout()
fig.savefig(OUT / "figure4_lisa_clusters.png", dpi=300)
plt.close(fig)
print("Saved figure4_lisa_clusters.png")

# ---------------------------------------------------------------------------
# Figure 5: SHAP importance bar chart
# ---------------------------------------------------------------------------
shap_imp = pd.read_csv(TABLES / "table4_shap_importance.csv").sort_values("mean_abs_shap")
fig, ax = plt.subplots(figsize=(7, 3.5))
bars = ax.barh(shap_imp["feature"], shap_imp["mean_abs_shap"], color=OI["blue"])
for bar, val in zip(bars, shap_imp["mean_abs_shap"]):
    ax.text(val + 0.3, bar.get_y() + bar.get_height() / 2, f"{val:.1f}", va="center", fontsize=9)
ax.set_xlim(0, None)
ax.set_xlabel("Mean |SHAP value|")
wrap_title(ax, "XGBoost incidence forecast relies almost entirely on the most distant (3-year) lag", width_chars=45)
fig.tight_layout()
fig.savefig(OUT / "figure5_shap_importance.png", dpi=300)
plt.close(fig)
print("Saved figure5_shap_importance.png")

# ---------------------------------------------------------------------------
# Figure 6: MDR-TB data-availability Gantt chart (required Stage-4 council deliverable)
# Shows the LOCKED, continuity-verified windows actually used in mdr_subanalysis.py
# (not the raw first-to-last availability span, which includes internal gap years).
# ---------------------------------------------------------------------------
avail = pd.read_csv(DATA / "mdr_gantt_availability.csv")
tier = pd.read_csv(DATA / "tb_series_forecast_tier_metadata.csv")

LOCKED_WINDOWS = {  # from docs/stage4_methodology.md §2 / mdr_subanalysis.py MDR_WINDOWS
    "mdr_tb_started_treatment": (2008, 2024),
    "tx_success_mdr_pct": (2010, 2022),
    "new_cases_tested_rr_mdr_pct": (2011, 2024),
    "prev_treated_tested_rr_mdr_pct": (2010, 2024),
    "mdr_rr_tb_confirmed": (2010, 2024),
}
DESCRIPTIVE_WINDOWS = {  # descriptive_only_excluded tier: raw available span (no forecasting window applies)
    "mdr_rr_tb_estimated_incident": (2015, 2024),
    "tx_success_xdr_pct": (2018, 2022),
}
mdr_rows = []
for var, (start, end) in {**LOCKED_WINDOWS, **DESCRIPTIVE_WINDOWS}.items():
    t = tier.loc[tier["variable"] == var, "forecast_tier"].values
    n_pts = avail.loc[avail["variable"] == var, "n_points"].values
    mdr_rows.append({"variable": var, "first_year": start, "last_year": end,
                      "forecast_tier": t[0] if len(t) else "descriptive_only_excluded",
                      "n_points": n_pts[0] if len(n_pts) else None})
avail_mdr = pd.DataFrame(mdr_rows).sort_values("first_year")

fig, ax = plt.subplots(figsize=(9, 4.5))
tier_colors = {"descriptive_only_excluded": OI["red"], "forecast_eligible": OI["blue"]}
for i, row in enumerate(avail_mdr.itertuples()):
    color = tier_colors.get(row.forecast_tier, OI["grey"])
    ax.barh(i, row.last_year - row.first_year, left=row.first_year, height=0.5, color=color)
    ax.text(row.last_year + 0.3, i, f"n={row.n_points}", va="center", fontsize=8)
ax.set_yticks(range(len(avail_mdr)))
ax.set_yticklabels(avail_mdr["variable"])
ax.set_xlabel("Year")
ax.set_xlim(2003, 2028)
handles = [mpatch.Patch(color=OI["red"], label="Descriptive only (Mann-Kendall), >=60% missing"),
           mpatch.Patch(color=OI["blue"], label="Forecast-eligible: LOCKED shorter-window sub-analysis")]
ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.15), fontsize=8, frameon=False, ncol=1)
wrap_title(ax, "MDR-TB cascade series use individually locked, continuity-verified data windows, not one forced common range", width_chars=52)
fig.tight_layout()
fig.savefig(OUT / "figure6_mdr_gantt.png", dpi=300)
plt.close(fig)
print("Saved figure6_mdr_gantt.png")

print(f"\nAll figures saved to {OUT}")

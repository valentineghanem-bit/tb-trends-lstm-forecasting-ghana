"""
Stage 1 — Master CSV builds, Project 19 (TB Trends/Forecasting Ghana).
Builds two master tables per the council-approved dual-track design:
  1. outputs/data/master_tb_national_panel.csv   — 1995-2024 national TB/HIV/health-system panel
  2. outputs/data/master_district_vulnerability.csv — 261-district structural TB-vulnerability index inputs
"""
import pandas as pd
import numpy as np
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT = Path(__file__).resolve().parent.parent / "outputs" / "data"
OUT.mkdir(parents=True, exist_ok=True)


def load_gho(fname):
    df = pd.read_csv(RAW / fname, skiprows=[1])
    df["YEAR (DISPLAY)"] = pd.to_numeric(df["YEAR (DISPLAY)"], errors="coerce")
    df["Numeric"] = pd.to_numeric(df["Numeric"], errors="coerce")
    return df


# ---------------------------------------------------------------------------
# 1. NATIONAL TB PANEL (1995-2024)
# ---------------------------------------------------------------------------
tb = load_gho("tuberculosis_indicators_gha.csv")

TB_SERIES = {
    "tb_incidence_per100k": "Incidence of tuberculosis (per 100 000 population per year)",
    "tb_incidence_hiv_pos_per100k": "Incidence of tuberculosis (per 100 000 population) (HIV-positive cases)",
    "tb_new_relapse_notified": "Tuberculosis - new and relapse cases",
    "tb_incident_cases_total": "Number of incident tuberculosis cases",
    "tb_incident_cases_children_0_14": "Number of incident tuberculosis cases in children aged 0 - 14",
    "tb_incident_cases_hiv_pos": "Number of incident tuberculosis cases,  (HIV-positive cases)",
    "tb_treatment_coverage_pct": "Tuberculosis treatment coverage",
    "mdr_rr_tb_estimated_incident": "Estimated number of MDR/RR-TB incident cases",
    "mdr_rr_tb_confirmed": "Confirmed cases of RR-/MDR-TB",
    "mdr_tb_started_treatment": "Cases started on MDR-TB treatment",
    "new_cases_tested_rr_mdr_pct": "New cases tested for RR-/MDR-TB (%)",
    "prev_treated_tested_rr_mdr_pct": "Previously treated cases tested for RR-/MDR-TB (%)",
    "tx_success_new_pct": "Treatment success rate: new TB cases",
    "tx_success_prev_treated_pct": "Treatment success rate: previously treated TB cases",
    "tx_success_mdr_pct": "Treatment success rate for patients treated for MDR-TB (%)",
    "tx_success_xdr_pct": "Treatment success rate: XDR-TB cases",
    "tx_success_hiv_pos_pct": "Treatment success rate: HIV-positive TB cases",
    "tb_known_hiv_status_pct": "TB patients with known HIV status (%)",
    "tb_tested_hiv_positive_pct": "Tested TB patients HIV-positive (%)",
    "tb_hiv_pos_on_art_pct": "HIV-positive TB patients on ART (antiretroviral therapy) (%)",
}

panel = pd.DataFrame({"year": range(1995, 2025)}).set_index("year")
for col, indicator in TB_SERIES.items():
    sub = tb[tb["GHO (DISPLAY)"] == indicator][["YEAR (DISPLAY)", "Numeric"]].dropna()
    sub = sub.groupby("YEAR (DISPLAY)")["Numeric"].mean()
    panel[col] = sub.reindex(panel.index)

# HIV covariates
hiv = load_gho("hiv_indicators_gha.csv")
HIV_SERIES = {
    "hiv_prevalence_adult_15_49_pct": "Prevalence of HIV among adults aged 15 to 49 (%)",
    "art_coverage_plhiv_pct": "Estimated antiretroviral therapy coverage among people living with HIV (%)",
}
for col, indicator in HIV_SERIES.items():
    sub = hiv[hiv["GHO (DISPLAY)"] == indicator][["YEAR (DISPLAY)", "Numeric"]].dropna()
    sub = sub.groupby("YEAR (DISPLAY)")["Numeric"].mean()
    panel[col] = sub.reindex(panel.index)

# Health financing covariates
fin = load_gho("health_financing_indicators_gha.csv")
FIN_SERIES = {
    "gghe_d_pct_gdp": "Domestic general government health expenditure (GGHE-D) as percentage of gross domestic product (GDP) (%)",
}
for col, indicator in FIN_SERIES.items():
    matches = fin[fin["GHO (DISPLAY)"] == indicator]
    sub = matches[["YEAR (DISPLAY)", "Numeric"]].dropna().groupby("YEAR (DISPLAY)")["Numeric"].mean()
    panel[col] = sub.reindex(panel.index)

# Health workforce covariate (physicians per 10,000 proxy — first matching series)
wf = load_gho("health_workforce_indicators_gha.csv")
phys = wf[wf["GHO (DISPLAY)"] == "Medical doctors (per 10,000)"]
if not phys.empty:
    sub = phys[["YEAR (DISPLAY)", "Numeric"]].dropna().groupby("YEAR (DISPLAY)")["Numeric"].mean()
    panel["medical_doctors_density"] = sub.reindex(panel.index)

# Life expectancy covariate
ghe = load_gho("global_health_estimates_life_expectancy_and_leading_causes_of_death_and_disability_indicators_gh.csv")
le = ghe[ghe["GHO (DISPLAY)"].str.contains("Life expectancy at birth", case=False, na=False)]
if not le.empty:
    both_sexes = le[le["DIMENSION (NAME)"].isna() | (le["DIMENSION (NAME)"] == "Both sexes")]
    src = both_sexes if not both_sexes.empty else le
    sub = src[["YEAR (DISPLAY)", "Numeric"]].dropna().groupby("YEAR (DISPLAY)")["Numeric"].mean()
    panel["life_expectancy_years"] = sub.reindex(panel.index)

# Council Stage-1 mandate: flag 2020-2021 as a candidate COVID-era TB
# reporting-disruption window. This is a structural annotation, not an
# imputation -- the sensitivity check itself (with/without this window) is
# executed at Stage 4, pending the Stage-2 literature citation confirming the
# pattern in Ghana/SSA specifically ([CLAIM NEEDED], logged to AIPOCH_Learning_Log.md).
panel["covid_era_flag"] = panel.index.isin([2020, 2021]).astype(int)

panel = panel.reset_index()
panel.to_csv(OUT / "master_tb_national_panel.csv", index=False)
print("National TB panel:", panel.shape)
print(panel.isna().mean().round(2).sort_values(ascending=False).head(15))

# Council Stage-1 mandate: two-tier MDR-TB forecast-eligibility metadata,
# computed on the 2000-2024 usable window only (not the raw 1995-2024 panel).
# Tier is missingness-based (council's binding 60% threshold, two tiers only).
# is_mdr_cascade_series is a separate, name-based flag: among the <60%-missing
# tier, MDR/XDR-cascade series get a Stage-4 shorter-window sub-analysis,
# while non-MDR core series (incidence, notified, coverage, tx success
# new/prev-treated, HIV/financing/workforce covariates) use the full
# 2000-2024 primary panel window.
MDR_CASCADE_COLS = {
    "mdr_rr_tb_estimated_incident", "mdr_rr_tb_confirmed", "mdr_tb_started_treatment",
    "new_cases_tested_rr_mdr_pct", "prev_treated_tested_rr_mdr_pct",
    "tx_success_mdr_pct", "tx_success_xdr_pct",
}
window = panel[panel["year"].between(2000, 2024)]
miss = window.drop(columns=["year", "covid_era_flag"]).isna().mean()
tier = pd.DataFrame({"variable": miss.index, "missing_pct_2000_2024": miss.values.round(3)})
tier["forecast_tier"] = np.where(
    tier["missing_pct_2000_2024"] >= 0.60, "descriptive_only_excluded", "forecast_eligible"
)
tier["is_mdr_cascade_series"] = tier["variable"].isin(MDR_CASCADE_COLS)
tier["stage4_window"] = np.select(
    [tier["forecast_tier"] == "descriptive_only_excluded",
     tier["is_mdr_cascade_series"] & (tier["forecast_tier"] == "forecast_eligible")],
    ["n/a (Mann-Kendall trend only)", "shorter_window_TBD_stage4"],
    default="2000-2024_primary",
)
tier.to_csv(OUT / "tb_series_forecast_tier_metadata.csv", index=False)
print("\nForecast-tier metadata:\n", tier.sort_values("missing_pct_2000_2024", ascending=False).to_string(index=False))

# ---------------------------------------------------------------------------
# 2. DISTRICT VULNERABILITY INDEX INPUTS (261 MMDAs)
# ---------------------------------------------------------------------------
ms = pd.read_excel(RAW / "Master_Sheet.xlsx")
ms = ms.rename(columns={
    "Metropolitan, Municipal, and District Assemblies (MMDA's)": "district",
    "Region": "region",
    "Class": "class_type",
    "Latitude": "latitude",
    "Longitude": "longitude",
    "Employed Population": "employed_pop",
    "Unemployed Population": "unemployed_pop",
    "Incidence of Poverty": "poverty_incidence",
    "Intensity of Poverty": "poverty_intensity",
    "Illiterate Population": "illiterate_pop",
    "Uninsured Population": "uninsured_pop",
    "Male Population 0-14": "male_0_14",
    "Female Population 0-14": "female_0_14",
    "Male Population 15-64": "male_15_64",
    "Female Population 15-64": "female_15_64",
    "Male Population 65+": "male_65plus",
    "Female Population 65+": "female_65plus",
    "Total Population": "total_population",
})
ms["literacy_rate"] = 1 - (ms["illiterate_pop"] / ms["total_population"])
ms["uninsured_rate"] = ms["uninsured_pop"] / ms["total_population"]
ms["unemployment_rate"] = ms["unemployed_pop"] / (ms["employed_pop"] + ms["unemployed_pop"])
ms["dependency_pop"] = (ms["male_0_14"] + ms["female_0_14"] + ms["male_65plus"] + ms["female_65plus"])
ms["working_age_pop"] = ms["male_15_64"] + ms["female_15_64"]
ms["dependency_ratio"] = ms["dependency_pop"] / ms["working_age_pop"]

ms.to_csv(OUT / "master_district_vulnerability.csv", index=False)
print("\nDistrict vulnerability master:", ms.shape)
print("Missing check:", ms[["poverty_incidence", "poverty_intensity", "literacy_rate", "uninsured_rate", "latitude", "longitude"]].isna().sum().to_dict())

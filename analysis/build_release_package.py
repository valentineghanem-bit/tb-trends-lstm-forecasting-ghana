"""
Stage 14 — Master CSV release package (FAIR-compliant Q1 deliverable).
Consolidates the two master datasets + spatial results into a versioned release
with a data dictionary (variable_provenance.csv), per Q1_DELIVERABLE_STANDARDS.md.
"""
import pandas as pd
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "outputs"
REL = OUT / "release"
REL.mkdir(exist_ok=True)

# --- 1. National TB panel (release copy) ---
panel = pd.read_csv(OUT / "data" / "master_tb_national_panel.csv")
panel.to_csv(REL / "tb_national_panel_2000_2024.csv", index=False)

# --- 2. District vulnerability master (release copy) ---
district = pd.read_csv(OUT / "data" / "master_district_vulnerability.csv")
district.to_csv(REL / "district_tb_vulnerability_261.csv", index=False)

# --- 3. Data dictionary ---
dict_rows = []

panel_defs = {
    "year": ("Calendar year", "WHO GHO", "1995-2024", "year", "int"),
    "tb_incidence_per100k": ("TB incidence rate", "WHO GHO", "1995-2024", "cases/100,000 pop", "float"),
    "tb_incidence_hiv_pos_per100k": ("TB incidence, HIV-positive stratum", "WHO GHO", "1995-2024", "cases/100,000 pop", "float"),
    "tb_new_relapse_notified": ("New + relapse TB cases notified", "WHO GHO", "1995-2024", "count", "float"),
    "tb_incident_cases_total": ("Total incident TB cases (WHO-modelled)", "WHO GHO", "1995-2024", "count", "float"),
    "tb_incident_cases_children_0_14": ("Incident TB cases, age 0-14", "WHO GHO", "1995-2024", "count", "float"),
    "tb_incident_cases_hiv_pos": ("Incident TB cases, HIV-positive", "WHO GHO", "1995-2024", "count", "float"),
    "tb_treatment_coverage_pct": ("TB treatment coverage", "WHO GHO", "1995-2024", "%", "float"),
    "mdr_rr_tb_estimated_incident": ("Estimated MDR/RR-TB incident cases", "WHO GHO", "1995-2024", "count", "float"),
    "mdr_rr_tb_confirmed": ("Confirmed MDR/RR-TB cases", "WHO GHO", "1995-2024", "count", "float"),
    "mdr_tb_started_treatment": ("MDR-TB cases started on treatment", "WHO GHO", "1995-2024", "count", "float"),
    "new_cases_tested_rr_mdr_pct": ("New cases tested for RR/MDR-TB", "WHO GHO", "1995-2024", "%", "float"),
    "prev_treated_tested_rr_mdr_pct": ("Previously-treated cases tested for RR/MDR-TB", "WHO GHO", "1995-2024", "%", "float"),
    "tx_success_new_pct": ("Treatment success, new TB cases", "WHO GHO", "1995-2024", "%", "float"),
    "tx_success_prev_treated_pct": ("Treatment success, previously-treated cases", "WHO GHO", "1995-2024", "%", "float"),
    "tx_success_mdr_pct": ("Treatment success, MDR-TB", "WHO GHO", "1995-2024", "%", "float"),
    "tx_success_xdr_pct": ("Treatment success, XDR-TB", "WHO GHO", "1995-2024", "%", "float"),
    "tx_success_hiv_pos_pct": ("Treatment success, HIV-positive TB", "WHO GHO", "1995-2024", "%", "float"),
    "tb_known_hiv_status_pct": ("TB patients with known HIV status", "WHO GHO", "1995-2024", "%", "float"),
    "tb_tested_hiv_positive_pct": ("TB patients tested HIV-positive", "WHO GHO", "1995-2024", "%", "float"),
    "tb_hiv_pos_on_art_pct": ("HIV-positive TB patients on ART", "WHO GHO", "1995-2024", "%", "float"),
    "hiv_prevalence_adult_15_49_pct": ("HIV prevalence, adults 15-49", "WHO GHO", "1995-2024", "%", "float"),
    "art_coverage_plhiv_pct": ("ART coverage among people living with HIV", "WHO GHO", "1995-2024", "%", "float"),
    "gghe_d_pct_gdp": ("Domestic government health expenditure", "WHO GHO (GHED)", "1995-2024", "% GDP", "float"),
    "medical_doctors_density": ("Medical doctors density", "WHO GHO (NHWA)", "1995-2024", "per 10,000 pop", "float"),
    "life_expectancy_years": ("Life expectancy at birth", "WHO GHE", "1995-2024", "years", "float"),
    "covid_era_flag": ("COVID-era disruption window indicator", "Derived (Stage 1)", "1995-2024", "0/1 flag (1 = 2020-2021)", "int"),
}
for col, (desc, src, yr, unit, dtype) in panel_defs.items():
    dict_rows.append({"file": "tb_national_panel_2000_2024.csv", "variable": col, "definition": desc,
                       "source": src, "years_covered": yr, "unit": unit, "dtype": dtype})

district_defs = {
    "district": ("MMDA district name", "Ghana Statistical Service 2021 PHC", "2021", "text", "str"),
    "region": ("Administrative region (16-region, post-2022)", "GSS 2021 PHC", "2021", "text", "str"),
    "class_type": ("Urban/rural district typology", "GSS 2021 PHC", "2021", "text", "str"),
    "latitude": ("District centroid latitude", "GSS 2021 PHC", "2021", "decimal degrees", "float"),
    "longitude": ("District centroid longitude", "GSS 2021 PHC", "2021", "decimal degrees", "float"),
    "poverty_incidence": ("Incidence of multidimensional poverty (Alkire-Foster)", "GSS 2021 PHC", "2021", "%", "float"),
    "poverty_intensity": ("Intensity of multidimensional poverty (Alkire-Foster)", "GSS 2021 PHC", "2021", "%", "float"),
    "literacy_rate": ("Literacy rate (1 - illiterate/total population)", "Derived, GSS 2021 PHC", "2021", "proportion", "float"),
    "uninsured_rate": ("Uninsured population rate", "Derived, GSS 2021 PHC", "2021", "proportion", "float"),
    "unemployment_rate": ("Unemployment rate", "Derived, GSS 2021 PHC", "2021", "proportion", "float"),
    "dependency_ratio": ("Age-dependency ratio (0-14 + 65+ / 15-64)", "Derived, GSS 2021 PHC", "2021", "ratio", "float"),
    "total_population": ("Total district population", "GSS 2021 PHC", "2021", "count", "int"),
    "tvi_pca": ("TB-Vulnerability Index, PCA composite (primary)", "Derived, Stage 3", "2021 (single cross-section)", "standardised score", "float"),
    "tvi_equal": ("TB-Vulnerability Index, equal-weighted composite (sensitivity)", "Derived, Stage 3", "2021 (single cross-section)", "standardised score", "float"),
}
for col, (desc, src, yr, unit, dtype) in district_defs.items():
    dict_rows.append({"file": "district_tb_vulnerability_261.csv", "variable": col, "definition": desc,
                       "source": src, "years_covered": yr, "unit": unit, "dtype": dtype})

dictionary = pd.DataFrame(dict_rows)
dictionary.to_csv(REL / "variable_provenance.csv", index=False)

print(f"Release package built: {REL}")
print(f"  tb_national_panel_2000_2024.csv: {panel.shape}")
print(f"  district_tb_vulnerability_261.csv: {district.shape}")
print(f"  variable_provenance.csv: {dictionary.shape} ({len(panel_defs)} + {len(district_defs)} variables documented)")
print(f"  Missingness check: panel {panel.isna().sum().sum()} cells, district {district.isna().sum().sum()} cells")

"""Stage 1 — Table 1 (descriptive summary), Project 19."""
import pandas as pd
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "outputs"
panel = pd.read_csv(OUT / "data" / "master_tb_national_panel.csv")
district = pd.read_csv(OUT / "data" / "master_district_vulnerability.csv")

# --- Table 1a: National TB panel, usable window 2000-2024 ---
core_cols = [
    "tb_incidence_per100k", "tb_incidence_hiv_pos_per100k", "tb_new_relapse_notified",
    "tb_incident_cases_total", "tb_treatment_coverage_pct", "tx_success_new_pct",
    "tx_success_prev_treated_pct", "hiv_prevalence_adult_15_49_pct", "art_coverage_plhiv_pct",
    "gghe_d_pct_gdp", "life_expectancy_years",
]
p = panel[panel["year"].between(2000, 2024)]
rows = []
for c in core_cols:
    s = p[c].dropna()
    rows.append({
        "variable": c, "n_years": len(s), "mean": round(s.mean(), 2), "sd": round(s.std(), 2),
        "min": round(s.min(), 2) if len(s) else None, "max": round(s.max(), 2) if len(s) else None,
        "first_year": int(p.loc[s.index, "year"].min()) if len(s) else None,
        "last_year": int(p.loc[s.index, "year"].max()) if len(s) else None,
    })
t1a = pd.DataFrame(rows)
t1a.to_csv(OUT / "tables" / "table1a_national_tb_panel_summary.csv", index=False)

# --- Table 1b: District vulnerability index inputs (261 MMDAs) ---
dist_cols = ["poverty_incidence", "poverty_intensity", "literacy_rate", "uninsured_rate",
             "unemployment_rate", "dependency_ratio", "total_population"]
rows = []
for c in dist_cols:
    s = district[c].dropna()
    rows.append({
        "variable": c, "n_districts": len(s), "mean": round(s.mean(), 3), "sd": round(s.std(), 3),
        "min": round(s.min(), 3), "median": round(s.median(), 3), "max": round(s.max(), 3),
    })
t1b = pd.DataFrame(rows)
t1b.to_csv(OUT / "tables" / "table1b_district_vulnerability_summary.csv", index=False)

print("Table 1a (national TB panel):")
print(t1a.to_string(index=False))
print("\nTable 1b (district vulnerability, n=261):")
print(t1b.to_string(index=False))
print("\nRegions represented:", district["region"].nunique(), "| Districts:", district["district"].nunique())

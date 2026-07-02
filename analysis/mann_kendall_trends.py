"""
Stage 6 — Mann-Kendall trend tests on all Track A national TB series.
Applied to every forecast_eligible and descriptive_only_excluded series,
each on its own available (non-null) window, per docs/stage4_methodology.md.
"""
import pandas as pd
import pymannkendall as mk
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "outputs"
panel = pd.read_csv(OUT / "data" / "master_tb_national_panel.csv")
panel = panel[panel["year"].between(2000, 2024)].reset_index(drop=True)
tier = pd.read_csv(OUT / "data" / "tb_series_forecast_tier_metadata.csv")

results = []
for _, row in tier.iterrows():
    col = row["variable"]
    sub = panel[["year", col]].dropna()
    if len(sub) < 4:
        continue  # MK requires a handful of points minimum
    test = mk.original_test(sub[col].values)
    results.append({
        "variable": col,
        "forecast_tier": row["forecast_tier"],
        "n_points": len(sub),
        "first_year": int(sub["year"].min()),
        "last_year": int(sub["year"].max()),
        "trend": test.trend,
        "p_value": round(test.p, 4),
        "sens_slope": round(test.slope, 4),
        "significant_at_0.05": test.p < 0.05,
    })

df = pd.DataFrame(results).sort_values("p_value")
df.to_csv(OUT / "tables" / "table2_mann_kendall_trends.csv", index=False)
print(df.to_string(index=False))
print(f"\n{df['significant_at_0.05'].sum()}/{len(df)} series show a significant trend at p<0.05")

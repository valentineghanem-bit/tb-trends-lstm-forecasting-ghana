"""
Stage 6 — Track B spatial analysis: Queen contiguity, Global Moran's I, Getis-Ord Gi*,
LISA on BOTH tvi_pca (primary) and tvi_equal (required robustness panel), per the
Stage-3 council mandate. Single 2021 cross-sectional timepoint only.
"""
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path
from libpysal.weights import Queen
from esda.moran import Moran, Moran_Local
from esda.getisord import G_Local

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT = Path(__file__).resolve().parent.parent / "outputs"

vuln = pd.read_csv(OUT / "data" / "master_district_vulnerability.csv")
cw = pd.read_csv(Path(__file__).resolve().parent.parent / "docs" / "district_crosswalk_261_to_260.csv")
gdf = gpd.read_file(RAW / "Ghana_New_260_District.geojson")

# Join: vuln.district -> crosswalk.master_sheet_district -> crosswalk.geojson_district -> gdf.DISTRICT
cw_small = cw[["master_sheet_district", "geojson_district"]].rename(columns={"master_sheet_district": "district"})
merged = vuln.merge(cw_small, on="district", how="left")
print("Unmatched districts:", merged["geojson_district"].isna().sum())

# Structural-gap districts: multiple master-sheet districts share one geojson polygon.
# Average TVI values for the shared polygon (documented, non-additive aggregation).
agg = merged.groupby("geojson_district").agg(
    tvi_pca=("tvi_pca", "mean"), tvi_equal=("tvi_equal", "mean"),
    n_source_districts=("district", "count")
).reset_index()
multi = agg[agg["n_source_districts"] > 1]
print(f"\n{len(multi)} polygon(s) aggregated from >1 source district (structural gap merges):")
print(multi)

gdf_join = gdf.merge(agg, left_on="DISTRICT", right_on="geojson_district", how="left")
print(f"\nGeoJSON polygons: {len(gdf)}, matched with TVI: {gdf_join['tvi_pca'].notna().sum()}")
gdf_join = gdf_join.dropna(subset=["tvi_pca", "tvi_equal"]).reset_index(drop=True)

# Queen contiguity weights, row-standardised
w = Queen.from_dataframe(gdf_join, use_index=False)
islands = w.islands
if islands:
    print(f"WARNING: {len(islands)} island polygon(s) with no queen neighbours — dropping for spatial stats.")
    gdf_join = gdf_join.drop(index=islands).reset_index(drop=True)
    w = Queen.from_dataframe(gdf_join, use_index=False)
w.transform = "r"

results = {}
for col in ["tvi_pca", "tvi_equal"]:
    y = gdf_join[col].values
    moran = Moran(y, w, permutations=999)
    lisa = Moran_Local(y, w, permutations=999)
    gi_star = G_Local(y, w, star=True, permutations=999)

    gdf_join[f"{col}_lisa_q"] = lisa.q  # 1=HH, 2=LH, 3=LL, 4=HL
    gdf_join[f"{col}_lisa_p"] = lisa.p_sim
    gdf_join[f"{col}_gi_star"] = gi_star.Zs
    gdf_join[f"{col}_gi_p"] = gi_star.p_sim

    lisa_labels = {1: "High-High", 2: "Low-High", 3: "Low-Low", 4: "High-Low"}
    gdf_join[f"{col}_lisa_label"] = np.where(
        gdf_join[f"{col}_lisa_p"] < 0.05,
        gdf_join[f"{col}_lisa_q"].map(lisa_labels),
        "Not significant",
    )

    results[col] = {
        "global_moran_I": round(float(moran.I), 4),
        "global_moran_p_sim": round(float(moran.p_sim), 4),
        "n_districts": len(gdf_join),
        "lisa_significant_clusters_p05": int((gdf_join[f"{col}_lisa_p"] < 0.05).sum()),
        "lisa_cluster_counts": gdf_join[f"{col}_lisa_label"].value_counts().to_dict(),
        "gi_star_hotspots_p05": int(((gdf_join[f"{col}_gi_p"] < 0.05) & (gdf_join[f"{col}_gi_star"] > 0)).sum()),
        "gi_star_coldspots_p05": int(((gdf_join[f"{col}_gi_p"] < 0.05) & (gdf_join[f"{col}_gi_star"] < 0)).sum()),
    }

print("\n=== Spatial statistics summary (both index versions, required robustness panel) ===")
print(json.dumps(results, indent=2))

with open(OUT / "data" / "spatial_stats_summary.json", "w") as f:
    json.dump(results, f, indent=2)

out_cols = ["DISTRICT", "REGION", "tvi_pca", "tvi_equal",
            "tvi_pca_lisa_label", "tvi_pca_gi_star", "tvi_pca_gi_p",
            "tvi_equal_lisa_label", "tvi_equal_gi_star", "tvi_equal_gi_p"]
gdf_join[out_cols].to_csv(OUT / "data" / "district_spatial_results.csv", index=False)
print(f"\nSaved: spatial_stats_summary.json, district_spatial_results.csv ({len(gdf_join)} districts)")

corr = np.corrcoef(gdf_join["tvi_pca_gi_star"], gdf_join["tvi_equal_gi_star"])[0, 1]
print(f"\nGi* z-score correlation between tvi_pca and tvi_equal: r={corr:.3f} (robustness check)")

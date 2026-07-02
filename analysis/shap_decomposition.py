"""
Stage 6 — SHAP decomposition on the XGBoost model (locked hyperparameters),
trained on the full 2000-2024 lagged-feature panel for tb_incidence_per100k.
Per Yang et al. 2022 precedent; scoped to XGBoost only (not LSTM/ARIMA).
"""
import json
import numpy as np
import pandas as pd
import shap
from pathlib import Path
from xgboost import XGBRegressor

OUT = Path(__file__).resolve().parent.parent / "outputs"
panel = pd.read_csv(OUT / "data" / "master_tb_national_panel.csv")
panel = panel[panel["year"].between(2000, 2024)].reset_index(drop=True)
with open(OUT / "data" / "locked_hyperparameters.json") as f:
    HP = json.load(f)

TARGET = "tb_incidence_per100k"
LOOKBACK = HP["lookback_years"]
series = panel[TARGET].values.astype("float64")


def make_lag_features(arr, lookback):
    X, y = [], []
    for i in range(len(arr) - lookback):
        X.append(arr[i:i + lookback])
        y.append(arr[i + lookback])
    return np.array(X), np.array(y)


X, y = make_lag_features(series, LOOKBACK)
feature_names = [f"lag_{LOOKBACK - i}yr" for i in range(LOOKBACK)]
Xdf = pd.DataFrame(X, columns=feature_names)

model = XGBRegressor(max_depth=HP["xgboost"]["max_depth"], n_estimators=HP["xgboost"]["n_estimators"],
                      learning_rate=HP["xgboost"]["learning_rate"], random_state=42, verbosity=0)
model.fit(Xdf, y)

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(Xdf)
assert shap_values.shape == Xdf.shape, f"SHAP shape mismatch: {shap_values.shape} vs {Xdf.shape}"

mean_abs_shap = np.abs(shap_values).mean(axis=0)
importance = pd.DataFrame({"feature": feature_names, "mean_abs_shap": mean_abs_shap.round(3)})
importance = importance.sort_values("mean_abs_shap", ascending=False)
importance.to_csv(OUT / "tables" / "table4_shap_importance.csv", index=False)

shap_df = pd.DataFrame(shap_values, columns=[f"shap_{c}" for c in feature_names])
shap_df.to_csv(OUT / "data" / "shap_values_xgb.csv", index=False)

print("SHAP mean |value| feature importance (XGBoost, tb_incidence_per100k, lookback=3yr):")
print(importance.to_string(index=False))
print(f"\nBase value (expected prediction): {explainer.expected_value:.2f}")

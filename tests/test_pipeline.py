"""Reproducibility sanity tests for the CI pipeline. Run after analysis/build_master.py
and analysis/build_vulnerability_index.py have (re)generated outputs/data/*.csv."""
import pandas as pd
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "outputs" / "data"


def test_national_panel_shape():
    df = pd.read_csv(DATA / "master_tb_national_panel.csv")
    assert len(df) == 30, "national panel should have 30 rows (1995-2024)"
    usable = df[df["year"].between(2000, 2024)]
    assert len(usable) == 25, "usable analytic window must be 25 years (2000-2024)"


def test_district_master_complete():
    df = pd.read_csv(DATA / "master_district_vulnerability.csv")
    assert len(df) == 261, "district master must have all 261 MMDAs"
    key_cols = ["poverty_incidence", "tvi_pca", "tvi_equal", "latitude", "longitude"]
    assert df[key_cols].isna().sum().sum() == 0, "key district variables must have zero missing"


def test_tvi_columns_present():
    df = pd.read_csv(DATA / "master_district_vulnerability.csv")
    assert "tvi_pca" in df.columns and "tvi_equal" in df.columns


def test_forecast_tier_metadata_covers_all_series():
    tier = pd.read_csv(DATA / "tb_series_forecast_tier_metadata.csv")
    assert set(tier["forecast_tier"].unique()) <= {"descriptive_only_excluded", "forecast_eligible"}


def test_locked_hyperparameters_exist():
    import json
    with open(DATA / "locked_hyperparameters.json") as f:
        hp = json.load(f)
    assert "lstm" in hp and "xgboost" in hp
    assert hp["lstm"]["n_layers"] == 1 and hp["lstm"]["hidden_units"] == 16

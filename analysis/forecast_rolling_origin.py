"""
Stage 6 — Rolling-origin CV forecasting: LSTM (locked), ARIMA (AIC-selected), XGBoost (locked).
Primary target: tb_incidence_per100k. Co-primary framing: all 3 models reported with full
per-fold distributions, never a single headline number. Also runs the binary COVID-era
sensitivity comparison (Model A full panel / Model B 2020-2021 excluded from training).
"""
import json
import warnings
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from pathlib import Path
from xgboost import XGBRegressor
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error

warnings.filterwarnings("ignore")

OUT = Path(__file__).resolve().parent.parent / "outputs"
panel = pd.read_csv(OUT / "data" / "master_tb_national_panel.csv")
panel = panel[panel["year"].between(2000, 2024)].reset_index(drop=True)
with open(OUT / "data" / "locked_hyperparameters.json") as f:
    HP = json.load(f)

TARGET = "tb_incidence_per100k"
LOOKBACK = HP["lookback_years"]
YEARS = panel["year"].values
SERIES = panel[TARGET].values.astype("float64")
COVID_FLAG = panel["covid_era_flag"].values


class SmallLSTM(nn.Module):
    def __init__(self, n_layers, hidden, dropout):
        super().__init__()
        self.lstm = nn.LSTM(input_size=1, hidden_size=hidden, num_layers=n_layers,
                             batch_first=True, dropout=dropout if n_layers > 1 else 0.0)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.dropout(out[:, -1, :])
        return self.fc(out)


def make_sequences(arr, lookback):
    X, y = [], []
    for i in range(len(arr) - lookback):
        X.append(arr[i:i + lookback])
        y.append(arr[i + lookback])
    return np.array(X), np.array(y)


def fit_lstm(train_vals, seed=42):
    mu, sigma = train_vals.mean(), train_vals.std()
    norm = (train_vals - mu) / sigma
    X, y = make_sequences(norm, LOOKBACK)
    X_t = torch.tensor(X, dtype=torch.float32).unsqueeze(-1)
    y_t = torch.tensor(y, dtype=torch.float32).unsqueeze(-1)
    torch.manual_seed(seed)
    model = SmallLSTM(HP["lstm"]["n_layers"], HP["lstm"]["hidden_units"], HP["lstm"]["dropout"])
    opt = torch.optim.Adam(model.parameters(), lr=HP["lstm"]["learning_rate"], weight_decay=HP["lstm"]["weight_decay_L2"])
    loss_fn = nn.MSELoss()
    for _ in range(HP["lstm"]["max_epochs"]):
        model.train()
        opt.zero_grad()
        loss = loss_fn(model(X_t), y_t)
        loss.backward()
        opt.step()
    model.eval()
    last_seq = torch.tensor((train_vals[-LOOKBACK:] - mu) / sigma, dtype=torch.float32).view(1, LOOKBACK, 1)
    with torch.no_grad():
        pred_norm = model(last_seq).item()
    return pred_norm * sigma + mu


def fit_arima_predict(train_vals):
    best_aic, best_order, best_fit = np.inf, None, None
    for p in range(3):
        for d in range(2):
            for q in range(3):
                try:
                    fit = ARIMA(train_vals, order=(p, d, q)).fit()
                    if fit.aic < best_aic:
                        best_aic, best_order, best_fit = fit.aic, (p, d, q), fit
                except Exception:
                    continue
    if best_fit is None:
        return train_vals[-1]  # naive fallback
    return best_fit.forecast(1)[0]


def fit_xgb_predict(train_vals):
    X, y = make_sequences(train_vals, LOOKBACK)
    m = XGBRegressor(max_depth=HP["xgboost"]["max_depth"], n_estimators=HP["xgboost"]["n_estimators"],
                      learning_rate=HP["xgboost"]["learning_rate"], random_state=42, verbosity=0)
    m.fit(X, y)
    last_seq = train_vals[-LOOKBACK:].reshape(1, -1)
    return m.predict(last_seq)[0]


def rolling_origin_cv(series_vals, covid_exclude=False, min_train=15):
    n = len(series_vals)
    rows = []
    for train_end in range(min_train, n):
        train = series_vals[:train_end]
        train_years_idx = np.arange(train_end)
        if covid_exclude:
            mask = COVID_FLAG[:train_end] == 0
            train_for_lstm_xgb = train[mask] if mask.sum() >= LOOKBACK + 2 else train
        else:
            train_for_lstm_xgb = train
        true_val = series_vals[train_end]
        lstm_pred = fit_lstm(train_for_lstm_xgb)
        arima_pred = fit_arima_predict(train)  # ARIMA uses full contiguous train (excluding breaks distorts ARIMA structure)
        xgb_pred = fit_xgb_predict(train_for_lstm_xgb)
        rows.append({"fold_year": int(YEARS[train_end]), "true": true_val,
                     "lstm_pred": lstm_pred, "arima_pred": arima_pred, "xgb_pred": xgb_pred})
    return pd.DataFrame(rows)


print("Running Model A (full panel) rolling-origin CV...")
model_a = rolling_origin_cv(SERIES, covid_exclude=False)
print("Running Model B (2020-2021 excluded from training) rolling-origin CV...")
model_b = rolling_origin_cv(SERIES, covid_exclude=True)


def summarize(df, label):
    metrics = {}
    for m in ["lstm", "arima", "xgb"]:
        mae = mean_absolute_error(df["true"], df[f"{m}_pred"])
        rmse = np.sqrt(mean_squared_error(df["true"], df[f"{m}_pred"]))
        mape = mean_absolute_percentage_error(df["true"], df[f"{m}_pred"]) * 100
        metrics[m] = {"MAE": round(mae, 2), "RMSE": round(rmse, 2), "MAPE_pct": round(mape, 2)}
    print(f"\n{label} — per-fold metrics (n={len(df)} folds):")
    print(pd.DataFrame(metrics).T)
    return metrics


metrics_a = summarize(model_a, "Model A (full 2000-2024 panel)")
metrics_b = summarize(model_b, "Model B (2020-2021 excluded from training)")

model_a.to_csv(OUT / "data" / "forecast_folds_model_a.csv", index=False)
model_b.to_csv(OUT / "data" / "forecast_folds_model_b.csv", index=False)

summary = {"target": TARGET, "n_folds": len(model_a), "model_a_full_panel": metrics_a, "model_b_covid_excluded": metrics_b}
with open(OUT / "data" / "forecast_metrics_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print("\nSaved: forecast_folds_model_a.csv, forecast_folds_model_b.csv, forecast_metrics_summary.json")

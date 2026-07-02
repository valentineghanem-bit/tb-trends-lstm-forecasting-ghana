"""
Stage 4 council mandate: pre-registered hyperparameter grid search for LSTM
and XGBoost, restricted to fold-1 ONLY (train 2000-2014, validate 2015) of the
rolling-origin CV scheme. Selection is final -- no re-tuning permitted on later
folds. Prevents architecture search from functioning as undisclosed overfitting
on N=25.
"""
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from pathlib import Path
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error

OUT = Path(__file__).resolve().parent.parent / "outputs" / "data"
panel = pd.read_csv(OUT / "master_tb_national_panel.csv")
panel = panel[panel["year"].between(2000, 2024)].reset_index(drop=True)

TARGET = "tb_incidence_per100k"
series = panel[TARGET].values.astype("float32")

# Fold-1 split per the rolling-origin scheme's minimum initial window
train_idx = panel["year"] <= 2014   # 2000-2014, 15 points
val_idx = panel["year"] == 2015     # 1 point (first held-out year)
train = series[train_idx.values]
val_year_val = series[val_idx.values][0]

mu, sigma = train.mean(), train.std()
train_norm = (train - mu) / sigma

LOOKBACK = 3  # short lookback given N=15 training points


def make_sequences(arr, lookback):
    X, y = [], []
    for i in range(len(arr) - lookback):
        X.append(arr[i:i + lookback])
        y.append(arr[i + lookback])
    return np.array(X), np.array(y)


X_train, y_train = make_sequences(train_norm, LOOKBACK)
X_train_t = torch.tensor(X_train, dtype=torch.float32).unsqueeze(-1)  # (n, lookback, 1)
y_train_t = torch.tensor(y_train, dtype=torch.float32).unsqueeze(-1)

# Predict 2015 using the last LOOKBACK years of training data
last_seq = torch.tensor((train[-LOOKBACK:] - mu) / sigma, dtype=torch.float32).view(1, LOOKBACK, 1)
val_true_norm = (val_year_val - mu) / sigma


class SmallLSTM(nn.Module):
    def __init__(self, n_layers, hidden):
        super().__init__()
        self.lstm = nn.LSTM(input_size=1, hidden_size=hidden, num_layers=n_layers,
                             batch_first=True, dropout=0.2 if n_layers > 1 else 0.0)
        self.dropout = nn.Dropout(0.2)
        self.fc = nn.Linear(hidden, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.dropout(out[:, -1, :])
        return self.fc(out)


grid = []
for n_layers in [1, 2]:
    for hidden in [8, 16]:
        for lr in [0.001, 0.01]:
            grid.append({"n_layers": n_layers, "hidden": hidden, "lr": lr})

results = []
torch.manual_seed(42)
for cfg in grid:
    model = SmallLSTM(cfg["n_layers"], cfg["hidden"])
    opt = torch.optim.Adam(model.parameters(), lr=cfg["lr"], weight_decay=1e-3)  # weight_decay = L2
    loss_fn = nn.MSELoss()
    best_val = np.inf
    patience, bad_epochs = 5, 0
    for epoch in range(200):
        model.train()
        opt.zero_grad()
        pred = model(X_train_t)
        loss = loss_fn(pred, y_train_t)
        loss.backward()
        opt.step()
        model.eval()
        with torch.no_grad():
            val_pred_norm = model(last_seq).item()
        val_err = (val_pred_norm - val_true_norm) ** 2
        if val_err < best_val:
            best_val = val_err
            bad_epochs = 0
        else:
            bad_epochs += 1
            if bad_epochs >= patience:
                break
    val_rmse_original_units = np.sqrt(best_val) * sigma
    results.append({**cfg, "epochs_run": epoch + 1, "fold1_val_rmse": round(float(val_rmse_original_units), 3)})

results_df = pd.DataFrame(results).sort_values("fold1_val_rmse")
print("LSTM grid search (fold-1 only, train 2000-2014, validate 2015):")
print(results_df.to_string(index=False))
best_lstm = results_df.iloc[0].to_dict()

# --- XGBoost lock (same fold-1-only procedure) ---
X_train_xgb = X_train  # (n, lookback) lag features
xgb_grid = []
for max_depth in [2, 3]:
    for n_estimators in [50, 100]:
        for learning_rate in [0.05, 0.1]:
            xgb_grid.append({"max_depth": max_depth, "n_estimators": n_estimators, "learning_rate": learning_rate})

xgb_results = []
for cfg in xgb_grid:
    m = XGBRegressor(**cfg, random_state=42, verbosity=0)
    m.fit(X_train_xgb, y_train)
    val_pred_norm = m.predict(last_seq.numpy().reshape(1, -1))[0]
    val_rmse = abs(val_pred_norm - val_true_norm) * sigma
    xgb_results.append({**cfg, "fold1_val_rmse": round(float(val_rmse), 3)})

xgb_df = pd.DataFrame(xgb_results).sort_values("fold1_val_rmse")
print("\nXGBoost grid search (fold-1 only):")
print(xgb_df.to_string(index=False))
best_xgb = xgb_df.iloc[0].to_dict()

locked = {
    "selection_procedure": "fold-1-only (train 2000-2014, validate 2015), no re-tuning on later folds",
    "target_series": TARGET,
    "lookback_years": LOOKBACK,
    "lstm": {
        "n_layers": int(best_lstm["n_layers"]), "hidden_units": int(best_lstm["hidden"]),
        "learning_rate": float(best_lstm["lr"]), "weight_decay_L2": 1e-3, "dropout": 0.2,
        "early_stopping_patience": 5, "max_epochs": 200,
        "fold1_val_rmse": float(best_lstm["fold1_val_rmse"]),
    },
    "xgboost": {
        "max_depth": int(best_xgb["max_depth"]), "n_estimators": int(best_xgb["n_estimators"]),
        "learning_rate": float(best_xgb["learning_rate"]),
        "fold1_val_rmse": float(best_xgb["fold1_val_rmse"]),
    },
}
with open(OUT / "locked_hyperparameters.json", "w") as f:
    json.dump(locked, f, indent=2)
print("\nLOCKED hyperparameters written to outputs/data/locked_hyperparameters.json:")
print(json.dumps(locked, indent=2))

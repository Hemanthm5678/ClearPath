import json
import os
from pathlib import Path
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score
import xgboost as xgb

def generate_synthetic_telemetry(n_samples: int = 2000):
    np.random.seed(42)
    X = []
    y = []

    # 1. Focused / Confident students (Label 0)
    n_focused = int(n_samples * 0.45)
    for _ in range(n_focused):
        dwell = np.random.uniform(4.0, 18.0)
        pause = np.random.uniform(0.5, 6.0)
        edits = np.random.choice([0, 1, 2], p=[0.75, 0.20, 0.05])
        switches = np.random.choice([0, 1], p=[0.85, 0.15])
        hints = 0
        lost = 0
        rapid = 0
        X.append([dwell, pause, edits, switches, hints, lost, rapid])
        y.append(0.0)

    # 2. Hesitant students (Label ~0.5)
    n_hesitant = int(n_samples * 0.25)
    for _ in range(n_hesitant):
        dwell = np.random.uniform(15.0, 35.0)
        pause = np.random.uniform(8.0, 18.0)
        edits = np.random.choice([1, 2, 3], p=[0.3, 0.5, 0.2])
        switches = np.random.choice([1, 2, 3], p=[0.5, 0.4, 0.1])
        hints = np.random.choice([0, 1], p=[0.7, 0.3])
        lost = 0
        rapid = np.random.choice([0, 1], p=[0.8, 0.2])
        X.append([dwell, pause, edits, switches, hints, lost, rapid])
        y.append(1.0 if np.random.rand() > 0.4 else 0.0)

    # 3. Confused students (Label 1)
    n_confused = n_samples - n_focused - n_hesitant
    for _ in range(n_confused):
        dwell = np.random.uniform(25.0, 75.0)
        pause = np.random.uniform(16.0, 45.0)
        edits = np.random.choice([3, 4, 5, 7], p=[0.2, 0.4, 0.3, 0.1])
        switches = np.random.choice([2, 3, 4, 6], p=[0.2, 0.4, 0.3, 0.1])
        hints = np.random.choice([1, 2, 3], p=[0.5, 0.3, 0.2])
        lost = np.random.choice([0, 1], p=[0.6, 0.4])
        rapid = np.random.choice([0, 2, 4, 6], p=[0.4, 0.3, 0.2, 0.1])
        X.append([dwell, pause, edits, switches, hints, lost, rapid])
        y.append(1.0)

    return np.array(X), np.array(y)

def train_and_save():
    print("Generating synthetic student telemetry...")
    X, y = generate_synthetic_telemetry(3000)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest = xgb.DMatrix(X_test, label=y_test)

    params = {
        "max_depth": 4,
        "eta": 0.1,
        "objective": "binary:logistic",
        "eval_metric": ["logloss", "auc"],
        "seed": 42
    }

    print("Training XGBoost confusion detector...")
    bst = xgb.train(params, dtrain, num_boost_round=60, evals=[(dtest, "test")], verbose_eval=False)

    preds = bst.predict(dtest)
    auc = roc_auc_score(y_test, preds)
    acc = accuracy_score(y_test, (preds >= 0.5).astype(int))

    print(f"Model trained successfully! Test AUC: {auc:.4f}, Accuracy: {acc:.4f}")

    models_dir = Path(__file__).resolve().parent.parent / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    out_path = models_dir / "detector.json"
    bst.save_model(str(out_path))
    print(f"Saved model to {out_path}")

if __name__ == "__main__":
    train_and_save()

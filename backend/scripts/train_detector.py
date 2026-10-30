"""
Confusion detector training pipeline.
  - Loads or simulates 20,000 attempts across 4 learner profiles
  - Splits data by learner (disjoint learner train/test sets to evaluate generalization)
  - Trains xgboost.XGBClassifier(n_estimators=120, max_depth=3, learning_rate=0.1)
  - Evaluates and prints F1 score and confusion matrix
  - Compares with the rule-based heuristic fallback
  - Saves trained model to models/detector.json
"""

import os
from pathlib import Path
import sys
from typing import Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
import xgboost as xgb

# Path resolution
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent if (SCRIPT_DIR.name == "scripts" and (SCRIPT_DIR.parent / "backend").exists()) else SCRIPT_DIR.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.signals import FEATURE_NAMES
from backend.app.confusion import compute_rule_score
from backend.scripts.simulate import simulate_dataset


def load_or_simulate_data(data_path: Optional[Path] = None) -> pd.DataFrame:
    """Loads existing 20,000 synthetic attempts or generates them."""
    if data_path is None:
        candidates = [
            ROOT_DIR / "data" / "synthetic_attempts.csv",
            ROOT_DIR / "backend" / "data" / "synthetic_attempts.csv",
            Path("data/synthetic_attempts.csv"),
            Path("backend/data/synthetic_attempts.csv"),
        ]
        for c in candidates:
            if c.exists() and c.stat().st_size > 0:
                data_path = c
                break

    if data_path is not None and data_path.exists():
        print(f"Loading simulated data from {data_path}...")
        df = pd.read_csv(data_path)
        if len(df) >= 20000:
            return df

    print("Generating fresh 20,000 simulated attempts across 4 profiles...")
    out_file = ROOT_DIR / "data" / "synthetic_attempts.csv"
    return simulate_dataset(total_attempts=20000, seed=42, output_path=out_file)


def train_and_evaluate(
    df: Optional[pd.DataFrame] = None,
    test_size: float = 0.20,
    random_seed: int = 42,
) -> Tuple[xgb.XGBClassifier, float, np.ndarray]:
    """
    Executes training split by learner, prints F1 and confusion matrix,
    and persists detector model to models/detector.json.
    """
    if df is None:
        df = load_or_simulate_data()

    print(f"\nTotal Dataset: {len(df)} rows across {df['learner_id'].nunique()} distinct learners.")

    # 1. Split strictly by learner to prevent cross-learner leakage
    unique_learners = df["learner_id"].unique()
    train_learners, test_learners = train_test_split(
        unique_learners,
        test_size=test_size,
        random_state=random_seed,
    )

    train_df = df[df["learner_id"].isin(train_learners)].copy()
    test_df = df[df["learner_id"].isin(test_learners)].copy()

    print(f"Train set: {len(train_df)} attempts ({len(train_learners)} learners)")
    print(f"Test set:  {len(test_df)} attempts ({len(test_learners)} learners)")

    feature_cols = FEATURE_NAMES
    X_train = train_df[feature_cols].values
    y_train = train_df["is_confused"].values
    X_test = test_df[feature_cols].values
    y_test = test_df["is_confused"].values

    # 2. Instantiate XGBoost Classifier exactly as specified
    # Model: xgboost.XGBClassifier(n_estimators=120, max_depth=3, learning_rate=0.1) on the 7 signals.
    model = xgb.XGBClassifier(
        n_estimators=120,
        max_depth=3,
        learning_rate=0.1,
        eval_metric="logloss",
        random_state=random_seed,
    )

    print("\nTraining XGBoost Classifier...")
    model.fit(X_train, y_train)

    # 3. Model Predictions on unseen learners
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.50).astype(int)

    f1 = float(f1_score(y_test, y_pred))
    auc = float(roc_auc_score(y_test, y_pred_proba))
    cm = confusion_matrix(y_test, y_pred)

    print("=" * 60)
    print("XGBoost Confusion Detector Evaluation (Split by Learner)")
    print("=" * 60)
    print(f"F1 Score:   {f1:.4f}")
    print(f"ROC AUC:    {auc:.4f}")
    print("\nConfusion Matrix:")
    print(f"                  Predicted Calm (0)  Predicted Confused (1)")
    print(f"Actual Calm (0)          {cm[0, 0]:<19} {cm[0, 1]:<20}")
    print(f"Actual Confused (1)      {cm[1, 0]:<19} {cm[1, 1]:<20}")
    print("-" * 60)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Calm", "Confused"]))

    # 4. Evaluate Rule Fallback Baseline on same test set
    print("=" * 60)
    print("Rule-Based Heuristic Fallback Evaluation")
    print("Formula: score = clip(0.02*think_time + 0.08*edits + 0.15*hints + 0.15*retries, 0, 1)")
    print("=" * 60)
    rule_scores = np.array([compute_rule_score(row) for row in X_test])
    rule_preds = (rule_scores >= 0.50).astype(int)
    rule_f1 = float(f1_score(y_test, rule_preds))
    rule_cm = confusion_matrix(y_test, rule_preds)

    print(f"Rule Fallback F1 Score: {rule_f1:.4f}")
    print("Rule Confusion Matrix:")
    print(f"                  Predicted Calm (0)  Predicted Confused (1)")
    print(f"Actual Calm (0)          {rule_cm[0, 0]:<19} {rule_cm[0, 1]:<20}")
    print(f"Actual Confused (1)      {rule_cm[1, 0]:<19} {rule_cm[1, 1]:<20}")

    # 5. Save model to models/detector.json
    out_paths = [
        ROOT_DIR / "models" / "detector.json",
        ROOT_DIR / "backend" / "models" / "detector.json",
    ]
    for p in out_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        model.save_model(str(p))
        print(f"Successfully saved model to: {p}")

    return model, f1, cm


if __name__ == "__main__":
    train_and_evaluate()

import os
from typing import Any, Dict, List, Optional
import numpy as np
from backend.app.config import settings

# Attempt to load XGBoost if available
_xgb_model = None

def load_detector_model():
    global _xgb_model
    model_path = settings.MODEL_DIR / "detector.json"
    if model_path.exists():
        try:
            import xgboost as xgb
            bst = xgb.Booster()
            bst.load_model(str(model_path))
            _xgb_model = bst
            return _xgb_model
        except Exception:
            _xgb_model = None
    return None

def score_confusion_rules(
    feature_vector: List[float],
    reasons: List[str]
) -> Dict[str, Any]:
    """
    Robust rule-based scoring engine when model is absent or as a verified baseline.
    Features: [dwell_sec, pause_sec, edit_count, option_switches, hint_clicks, lost_clicks, rapid_clicks]
    """
    dwell_sec, pause_sec, edits, switches, hints, lost, rapid = feature_vector

    score = 0.05  # Base level

    # Lost button clicked -> immediate high confusion
    if lost > 0:
        score += 0.50

    # Pause time
    if pause_sec >= 20.0:
        score += 0.35
    elif pause_sec >= 10.0:
        score += 0.20
    elif dwell_sec >= 30.0:
        score += 0.25

    # Edits / Backspaces
    if edits >= 4:
        score += 0.25
    elif edits >= 2:
        score += 0.15

    # Option switching
    if switches >= 3:
        score += 0.25
    elif switches >= 1:
        score += 0.10

    # Hints requested
    if hints > 0:
        score += 0.20

    # Rapid frustration clicks
    if rapid >= 3:
        score += 0.15

    # Clamp between 0.0 and 0.99
    final_score = min(0.99, max(0.02, round(score, 2)))

    # Determine state
    if final_score >= settings.THRESHOLD_CONFUSED:
        state = "confused"
    elif final_score >= settings.THRESHOLD_HESITANT:
        state = "hesitant"
    else:
        state = "focused"

    # Ensure reasons list has relevant details if score is elevated
    filtered_reasons = list(reasons)
    if state != "focused" and not filtered_reasons:
        if dwell_sec > 15:
            filtered_reasons.append(f"{int(dwell_sec)} s dwell")
        else:
            filtered_reasons.append("hesitation detected")

    return {
        "score": final_score,
        "state": state,
        "reasons": filtered_reasons,
    }

def detect_confusion(
    feature_vector: List[float],
    reasons: List[str]
) -> Dict[str, Any]:
    """
    Detects confusion using XGBoost model with fallback to the heuristic rule engine.
    """
    global _xgb_model
    if _xgb_model is None:
        load_detector_model()

    if _xgb_model is not None:
        try:
            import xgboost as xgb
            dmat = xgb.DMatrix(np.array([feature_vector]))
            preds = _xgb_model.predict(dmat)
            score = float(preds[0])
            score = round(min(0.99, max(0.02, score)), 2)

            if score >= settings.THRESHOLD_CONFUSED:
                state = "confused"
            elif score >= settings.THRESHOLD_HESITANT:
                state = "hesitant"
            else:
                state = "focused"

            return {
                "score": score,
                "state": state,
                "reasons": reasons,
            }
        except Exception:
            pass

    # Fallback to rule engine
    return score_confusion_rules(feature_vector, reasons)

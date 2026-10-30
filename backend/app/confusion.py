"""
Confusion detector implementation with XGBoost ML model and rule-based heuristic fallback.
Features:
  - EMA Smoothing: score = 0.6 * new + 0.4 * previous
  - Hysteresis thresholds: Enter "confused" at >= 0.65, Leave "confused" at < 0.45
  - Rule fallback: score = clip(0.02*think_time_s + 0.08*edit_count + 0.15*hint_count + 0.15*retry_count, 0, 1)
  - Returns top 3 plain text reasons
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np

from backend.app.config import ROOT_DIR, settings
from backend.app.signals import FEATURE_NAMES, generate_top_reasons

# In-memory session tracking for EMA smoothing & hysteresis state
_SESSION_STATES: Dict[str, Dict[str, Any]] = {}
_MODEL_INSTANCE: Optional[Any] = None


def get_model_path() -> Optional[Path]:
    """Finds available detector.json model file across possible locations."""
    candidates = [
        settings.MODEL_DIR / "detector.json",
        ROOT_DIR / "models" / "detector.json",
        Path("models/detector.json"),
        Path("backend/models/detector.json"),
    ]
    for p in candidates:
        if p.exists() and p.stat().st_size > 0:
            return p
    return None


def load_detector_model():
    """Loads XGBoost detector model from models/detector.json if available."""
    global _MODEL_INSTANCE
    model_path = get_model_path()
    if model_path is None:
        _MODEL_INSTANCE = None
        return None

    try:
        import xgboost as xgb
        clf = xgb.XGBClassifier()
        clf.load_model(str(model_path))
        _MODEL_INSTANCE = clf
        return _MODEL_INSTANCE
    except Exception:
        try:
            import xgboost as xgb
            bst = xgb.Booster()
            bst.load_model(str(model_path))
            _MODEL_INSTANCE = bst
            return _MODEL_INSTANCE
        except Exception:
            _MODEL_INSTANCE = None
            return None


def apply_ema(new_score: float, previous_score: Optional[float] = None) -> float:
    """
    Exponential Moving Average smoothing:
    score = 0.6 * new + 0.4 * previous
    """
    if previous_score is None:
        return float(np.clip(new_score, 0.0, 1.0))
    smoothed = 0.6 * new_score + 0.4 * previous_score
    return float(np.clip(smoothed, 0.0, 1.0))


def apply_hysteresis(score: float, previous_state: Optional[str] = None) -> str:
    """
    Hysteresis state transition:
      - Enter "confused" when score >= 0.65
      - Leave "confused" only when score < 0.45
      - Between 0.45 and 0.65, state is maintained
    """
    if previous_state == "confused":
        if score < 0.45:
            return "calm"
        return "confused"
    else:
        if score >= 0.65:
            return "confused"
        return "calm"


def compute_rule_score(feature_vector: List[float]) -> float:
    """
    Rule fallback formula:
    score = clip(0.02*think_time_s + 0.08*edit_count + 0.15*hint_count + 0.15*retry_count, 0, 1)
    """
    # Vector layout: [latency_s, think_time_s, edit_count, hint_count, retry_count, idle_ratio, recent_accuracy]
    if len(feature_vector) >= 5:
        think_time_s = float(feature_vector[1])
        edit_count = float(feature_vector[2])
        hint_count = float(feature_vector[3])
        retry_count = float(feature_vector[4])
    else:
        think_time_s = float(feature_vector[0]) if len(feature_vector) > 0 else 0.0
        edit_count = float(feature_vector[1]) if len(feature_vector) > 1 else 0.0
        hint_count = float(feature_vector[2]) if len(feature_vector) > 2 else 0.0
        retry_count = float(feature_vector[3]) if len(feature_vector) > 3 else 0.0

    raw_score = 0.02 * think_time_s + 0.08 * edit_count + 0.15 * hint_count + 0.15 * retry_count
    return float(np.clip(raw_score, 0.0, 1.0))


def score_confusion_rules(
    feature_vector: List[float],
    reasons: Optional[List[str]] = None,
    previous_score: Optional[float] = None,
    previous_state: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Rule-based confusion scoring with hysteresis and EMA smoothing.
    """
    raw_p = compute_rule_score(feature_vector)
    smoothed_score = apply_ema(raw_p, previous_score)
    state = apply_hysteresis(smoothed_score, previous_state)

    if reasons is None:
        signal_dict = {
            "latency_s": feature_vector[0] if len(feature_vector) > 0 else 0.0,
            "think_time_s": feature_vector[1] if len(feature_vector) > 1 else 0.0,
            "edit_count": feature_vector[2] if len(feature_vector) > 2 else 0.0,
            "hint_count": feature_vector[3] if len(feature_vector) > 3 else 0.0,
            "retry_count": feature_vector[4] if len(feature_vector) > 4 else 0.0,
            "idle_ratio": feature_vector[5] if len(feature_vector) > 5 else 0.0,
            "recent_accuracy": feature_vector[6] if len(feature_vector) > 6 else 1.0,
        }
        reasons = generate_top_reasons(signal_dict, max_reasons=3)

    top_reasons = reasons[:3]
    return {
        "score": round(smoothed_score, 4),
        "state": state,
        "p_confused": round(raw_p, 4),
        "reasons": top_reasons,
        "reasons_text": ", ".join(top_reasons),
        "is_confused": (state == "confused"),
        "source": "rule_fallback",
    }


class ConfusionDetector:
    """
    High-level Confusion Detector wrapping XGBoost ML inference,
    EMA smoothing, state hysteresis, and rule-based fallback.
    """

    def __init__(self, model_path: Optional[Union[str, Path]] = None):
        self.model = None
        if model_path:
            p = Path(model_path)
            if p.exists():
                try:
                    import xgboost as xgb
                    clf = xgb.XGBClassifier()
                    clf.load_model(str(p))
                    self.model = clf
                except Exception:
                    pass
        if self.model is None:
            self.model = load_detector_model()

    def predict_raw(self, feature_vector: List[float]) -> float:
        """Runs XGBoost inference or falls back to rule calculation."""
        if self.model is None:
            self.model = load_detector_model()

        if self.model is not None:
            try:
                import xgboost as xgb
                X = np.array([feature_vector[:7]], dtype=np.float32)
                if hasattr(self.model, "predict_proba"):
                    probs = self.model.predict_proba(X)
                    return float(probs[0, 1])
                elif hasattr(self.model, "predict"):
                    dmat = xgb.DMatrix(X)
                    preds = self.model.predict(dmat)
                    return float(preds[0])
            except Exception:
                pass

        return compute_rule_score(feature_vector)

    def detect(
        self,
        feature_vector: List[float],
        reasons: Optional[List[str]] = None,
        previous_score: Optional[float] = None,
        previous_state: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes full confusion detection pipeline:
          1. Raw p_confused via XGBoost (or rule fallback)
          2. EMA smoothing: score = 0.6 * new + 0.4 * previous
          3. Hysteresis: enter >= 0.65, leave < 0.45
          4. Top 3 plain text reasons
        """
        raw_p = self.predict_raw(feature_vector)
        smoothed_score = apply_ema(raw_p, previous_score)
        state = apply_hysteresis(smoothed_score, previous_state)

        if reasons is None:
            signal_dict = {
                "latency_s": feature_vector[0] if len(feature_vector) > 0 else 0.0,
                "think_time_s": feature_vector[1] if len(feature_vector) > 1 else 0.0,
                "edit_count": feature_vector[2] if len(feature_vector) > 2 else 0.0,
                "hint_count": feature_vector[3] if len(feature_vector) > 3 else 0.0,
                "retry_count": feature_vector[4] if len(feature_vector) > 4 else 0.0,
                "idle_ratio": feature_vector[5] if len(feature_vector) > 5 else 0.0,
                "recent_accuracy": feature_vector[6] if len(feature_vector) > 6 else 1.0,
            }
            reasons = generate_top_reasons(signal_dict, max_reasons=3)

        top_reasons = reasons[:3]
        return {
            "score": round(smoothed_score, 4),
            "state": state,
            "p_confused": round(raw_p, 4),
            "reasons": top_reasons,
            "reasons_text": ", ".join(top_reasons),
            "is_confused": (state == "confused"),
            "source": "model" if self.model is not None else "rule_fallback",
        }


# Global detector singleton
detector = ConfusionDetector()


def detect_confusion(
    feature_vector: List[float],
    reasons: Optional[List[str]] = None,
    previous_score: Optional[float] = None,
    previous_state: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Standard entrypoint used throughout API and tests.
    Maintains session history if session_id is provided.
    """
    global _SESSION_STATES

    if session_id and (previous_score is None or previous_state is None):
        stored = _SESSION_STATES.get(session_id, {})
        if previous_score is None:
            previous_score = stored.get("score")
        if previous_state is None:
            previous_state = stored.get("state")

    res = detector.detect(
        feature_vector=feature_vector,
        reasons=reasons,
        previous_score=previous_score,
        previous_state=previous_state,
    )

    if session_id:
        _SESSION_STATES[session_id] = {
            "score": res["score"],
            "state": res["state"],
            "reasons": res["reasons"],
        }

    return res

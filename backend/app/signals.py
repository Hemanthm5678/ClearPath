from typing import Any, Dict, List, Tuple
from backend.app.config import settings

FEATURE_NAMES = [
    "dwell_time_sec",
    "pause_duration_sec",
    "edit_count",
    "option_switches",
    "hint_clicks",
    "lost_clicks",
    "rapid_clicks",
]

def extract_features(raw_features: Dict[str, Any]) -> Tuple[List[float], List[str]]:
    """
    Transforms raw timing and count events into a clean numerical feature vector
    and generates human-readable reason explanations.
    Strictly timing and counts: NO camera, microphone, or PII.
    """
    # Extract values with safe defaults
    dwell_ms = float(raw_features.get("dwell_time_ms", 0.0))
    pause_ms = float(raw_features.get("pause_duration_ms", 0.0))
    edit_count = int(raw_features.get("edit_count", raw_features.get("backspaces", 0)))
    option_switches = int(raw_features.get("option_switches", 0))
    hint_clicks = int(raw_features.get("hint_clicks", raw_features.get("hints", 0)))
    lost_clicks = int(raw_features.get("lost_clicks", 0))
    rapid_clicks = int(raw_features.get("rapid_clicks", 0))

    dwell_sec = round(dwell_ms / 1000.0, 1)
    pause_sec = round(pause_ms / 1000.0, 1)

    feature_vector = [
        dwell_sec,
        pause_sec,
        float(edit_count),
        float(option_switches),
        float(hint_clicks),
        float(lost_clicks),
        float(rapid_clicks),
    ]

    # Generate reasons based on rule thresholds from config
    rules = settings.RULES
    reasons: List[str] = []

    dwell_trigger_sec = rules.get("dwell_time_trigger_ms", 25000) / 1000.0
    pause_trigger_sec = rules.get("pause_trigger_ms", 15000) / 1000.0

    if pause_sec >= pause_trigger_sec:
        reasons.append(f"{int(pause_sec)} s pause")
    elif dwell_sec >= dwell_trigger_sec:
        reasons.append(f"{int(dwell_sec)} s on question")

    if edit_count >= rules.get("edit_count_trigger", 4):
        reasons.append(f"{edit_count} edits")
    elif edit_count > 1:
        reasons.append(f"{edit_count} revisions")

    if option_switches >= rules.get("option_switch_trigger", 3):
        reasons.append(f"{option_switches} option changes")

    if hint_clicks >= rules.get("hint_click_trigger", 1):
        reasons.append("hint tapped")

    if lost_clicks >= rules.get("lost_click_trigger", 1):
        reasons.append("lost button tapped")

    if rapid_clicks >= 3:
        reasons.append(f"{rapid_clicks} rapid clicks")

    return feature_vector, reasons

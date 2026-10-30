"""
Telemetric signal extraction for ClearPath cognitive detector.
Extracts 7 passive behavioral signals:
  1. latency_s: Total response time / dwell time in seconds.
  2. think_time_s: Pause / hesitation duration before/between actions in seconds.
  3. edit_count: Total edits, revisions, or backspaces.
  4. hint_count: Total hints requested.
  5. retry_count: Number of repeated attempts / option switches on this question.
  6. idle_ratio: Ratio of think/idle time to total latency (think_time_s / latency_s).
  7. recent_accuracy: Accuracy over recent attempts ([0.0, 1.0]).

Strictly non-intrusive timing and counts: zero camera, zero microphone, zero personal data.
"""

from typing import Any, Dict, List, Optional, Tuple

FEATURE_NAMES = [
    "latency_s",
    "think_time_s",
    "edit_count",
    "hint_count",
    "retry_count",
    "idle_ratio",
    "recent_accuracy",
]


def extract_signals_dict(raw_features: Dict[str, Any]) -> Dict[str, float]:
    """
    Parses incoming telemetry from either standard dictionary names, frontend
    millisecond measurements, or simulated records into normalized numerical values.
    """
    if raw_features is None:
        raw_features = {}

    # 1. Latency (seconds)
    if "latency_s" in raw_features and raw_features["latency_s"] is not None:
        latency_s = float(raw_features["latency_s"])
    elif "dwell_time_ms" in raw_features and raw_features["dwell_time_ms"] is not None:
        latency_s = float(raw_features["dwell_time_ms"]) / 1000.0
    elif "dwell_time_sec" in raw_features and raw_features["dwell_time_sec"] is not None:
        latency_s = float(raw_features["dwell_time_sec"])
    elif "idle_time" in raw_features and raw_features["idle_time"] is not None:
        latency_s = float(raw_features["idle_time"])
    else:
        latency_s = 0.0

    # 2. Think time / Pause duration (seconds)
    if "think_time_s" in raw_features and raw_features["think_time_s"] is not None:
        think_time_s = float(raw_features["think_time_s"])
    elif "pause_duration_ms" in raw_features and raw_features["pause_duration_ms"] is not None:
        think_time_s = float(raw_features["pause_duration_ms"]) / 1000.0
    elif "pause_duration_sec" in raw_features and raw_features["pause_duration_sec"] is not None:
        think_time_s = float(raw_features["pause_duration_sec"])
    elif "idle_time" in raw_features and raw_features["idle_time"] is not None:
        think_time_s = float(raw_features["idle_time"])
    else:
        think_time_s = 0.0

    # 3. Edit count
    edit_count = float(
        raw_features.get("edit_count") or
        raw_features.get("backspaces") or 0.0
    )

    # 4. Hint count
    hint_count = float(
        raw_features.get("hint_count") or
        raw_features.get("hint_clicks") or
        raw_features.get("hints") or 0.0
    )

    # 5. Retry count / option switches
    retry_count = float(
        raw_features.get("retry_count") or
        raw_features.get("retries") or
        raw_features.get("option_switches") or 0.0
    )

    # 6. Idle ratio (think_time_s / latency_s, clamped to [0.0, 1.0])
    if "idle_ratio" in raw_features and raw_features["idle_ratio"] is not None:
        idle_ratio = float(raw_features["idle_ratio"])
    else:
        if latency_s > 0.0:
            idle_ratio = min(1.0, max(0.0, think_time_s / latency_s))
        else:
            idle_ratio = 0.0

    # 7. Recent accuracy ([0.0, 1.0])
    if "recent_accuracy" in raw_features and raw_features["recent_accuracy"] is not None:
        recent_accuracy = float(raw_features["recent_accuracy"])
    elif "accuracy" in raw_features and raw_features["accuracy"] is not None:
        recent_accuracy = float(raw_features["accuracy"])
    else:
        # Infer from retries and lost clicks if not explicitly passed
        lost = float(raw_features.get("lost_clicks") or 0.0)
        if lost > 0 or retry_count >= 2:
            recent_accuracy = 0.0
        elif retry_count == 1:
            recent_accuracy = 0.5
        else:
            recent_accuracy = 1.0
    recent_accuracy = min(1.0, max(0.0, recent_accuracy))

    return {
        "latency_s": round(max(0.0, latency_s), 2),
        "think_time_s": round(max(0.0, think_time_s), 2),
        "edit_count": round(max(0.0, edit_count), 2),
        "hint_count": round(max(0.0, hint_count), 2),
        "retry_count": round(max(0.0, retry_count), 2),
        "idle_ratio": round(min(1.0, max(0.0, idle_ratio)), 3),
        "recent_accuracy": round(recent_accuracy, 3),
    }


def generate_top_reasons(
    signals: Dict[str, float],
    raw_features: Optional[Dict[str, Any]] = None,
    max_reasons: int = 3,
) -> List[str]:
    """
    Identifies the top contributing behavioral factors to hesitation or confusion,
    returning up to `max_reasons` concise plain text descriptions.
    Example: ["25 s pause", "4 edits", "hint tapped"]
    """
    raw_features = raw_features or {}
    candidates: List[Tuple[float, str]] = []

    think_time = signals.get("think_time_s", 0.0)
    latency = signals.get("latency_s", 0.0)
    edits = signals.get("edit_count", 0.0)
    hints = signals.get("hint_count", 0.0)
    retries = signals.get("retry_count", 0.0)
    idle_ratio = signals.get("idle_ratio", 0.0)
    recent_acc = signals.get("recent_accuracy", 1.0)
    lost_clicks = float(raw_features.get("lost_clicks", 0))

    # Weight contributions based on rule heuristic importance
    if lost_clicks > 0:
        candidates.append((0.60, "lost button tapped"))

    if think_time >= 5.0:
        weight = 0.02 * think_time
        candidates.append((weight, f"{int(round(think_time))} s pause"))
    elif latency >= 20.0:
        weight = 0.01 * latency
        candidates.append((weight, f"{int(round(latency))} s on question"))

    if edits >= 1.0:
        weight = 0.08 * edits
        candidates.append((weight, f"{int(round(edits))} edits"))

    if hints >= 1.0:
        weight = 0.15 * hints
        text = "hint tapped" if hints == 1.0 else f"{int(round(hints))} hints tapped"
        candidates.append((weight, text))

    if retries >= 1.0:
        weight = 0.15 * retries
        text = "retry attempt" if retries == 1.0 else f"{int(round(retries))} retries"
        candidates.append((weight, text))

    if idle_ratio >= 0.65 and think_time >= 5.0:
        candidates.append((0.10, f"high idle ({int(round(idle_ratio * 100))}%)"))

    if recent_acc <= 0.4:
        candidates.append((0.15, f"low accuracy ({int(round(recent_acc * 100))}%)"))

    # Sort descending by contribution weight
    candidates.sort(key=lambda item: item[0], reverse=True)

    # Return top unique reasons
    reasons: List[str] = []
    seen = set()
    for _, text in candidates:
        if text not in seen:
            seen.add(text)
            reasons.append(text)
        if len(reasons) >= max_reasons:
            break

    return reasons


def format_reasons(reasons: List[str]) -> str:
    """Formats reasons list as human-readable comma-separated plain text."""
    return ", ".join(reasons)


def extract_features(raw_features: Dict[str, Any]) -> Tuple[List[float], List[str]]:
    """
    Transforms raw timing and count events into the 7-feature numerical vector
    and generates the top 3 plain text reasons.
    """
    signals = extract_signals_dict(raw_features)

    feature_vector = [
        signals["latency_s"],
        signals["think_time_s"],
        signals["edit_count"],
        signals["hint_count"],
        signals["retry_count"],
        signals["idle_ratio"],
        signals["recent_accuracy"],
    ]

    reasons = generate_top_reasons(signals, raw_features=raw_features, max_reasons=3)
    return feature_vector, reasons

"""
Telemetry & Cognitive State Engine for ClearPath.
Implements:
  1. Persona-Normalized & Complexity-Scaled Timing Metrics (Hint 1 & Hint 2)
  2. 5 Cognitive States: GAMING, BORED, CONFUSED, NATURALLY_SLOW, FOCUSED
  3. Closed-Loop Intervention Efficacy Verification (Hint 3)
"""

import time
from typing import Any, Dict, List, Optional, Tuple


def calculate_normalized_time_ratio(
    actual_time_sec: float,
    expected_time_sec: float,
    student_pace_factor: float = 1.0,
) -> float:
    """
    normalized_time_ratio = actual_time_sec / (expected_time_sec * student_pace_factor)
    """
    expected = max(5.0, float(expected_time_sec or 30.0))
    pace = max(0.4, min(3.0, float(student_pace_factor or 1.0)))
    ratio = float(actual_time_sec or 1.0) / (expected * pace)
    return round(max(0.01, min(10.0, ratio)), 3)


def update_student_pace(
    old_pace: float,
    actual_time_sec: float,
    expected_time_sec: float,
) -> float:
    """
    Per-student rolling baseline student_pace_factor (default 1.0).
    Updated via EMA on correct answers:
      0.7 * old_pace + 0.3 * (actual_time / expected_time_sec)
    """
    expected = max(5.0, float(expected_time_sec or 30.0))
    sample = float(actual_time_sec or expected) / expected
    new_pace = 0.7 * float(old_pace or 1.0) + 0.3 * sample
    return round(max(0.4, min(3.0, new_pace)), 2)


def classify_cognitive_state(
    actual_time_sec: float,
    expected_time_sec: float,
    complexity_weight: float,
    student_pace_factor: float,
    is_correct: Optional[bool] = None,
    option_switches: int = 0,
    hesitation_pauses: int = 0,
    hint_timestamps: Optional[List[float]] = None,
    event_type: str = "submit",
) -> Tuple[str, float, List[str], str]:
    """
    Classifies telemetry into one of 5 Cognitive States:
      1. GAMING
      2. BORED
      3. CONFUSED
      4. NATURALLY_SLOW
      5. FOCUSED

    Returns:
      (cognitive_state, confusion_score, top_reasons, breakdown_text)
    """
    actual_time_sec = max(0.5, float(actual_time_sec))
    expected_time_sec = max(5.0, float(expected_time_sec or 30.0))
    student_pace_factor = max(0.4, min(3.0, float(student_pace_factor or 1.0)))
    complexity_weight = max(1.0, float(complexity_weight or 1.0))

    ratio = calculate_normalized_time_ratio(actual_time_sec, expected_time_sec, student_pace_factor)
    reasons: List[str] = []

    # Check Hint Gaming (hint_click_rate > 2 within 6s OR hints_used >= 2 and time_after_last_hint < 3.0s)
    hint_timestamps = hint_timestamps or []
    now = time.time()
    hints_in_last_6s = [t for t in hint_timestamps if now - t <= 6.0]
    time_after_last_hint = (now - hint_timestamps[-2]) if len(hint_timestamps) >= 2 else 999.0

    is_gaming = (
        len(hints_in_last_6s) > 2
        or (len(hint_timestamps) >= 2 and time_after_last_hint < 3.0)
        or (event_type == "hint" and actual_time_sec < 2.5 and len(hint_timestamps) >= 2)
    )

    if is_gaming:
        reasons.append("rapid hint clicks (rate > 2 in 6s)")
        reasons.append("surface gaming detected")
        breakdown = f"Actual: {actual_time_sec:.0f}s | Expected: {expected_time_sec:.0f}s | Hints: {len(hint_timestamps)} rapid | Gaming Cooldown"
        return "GAMING", 0.72, reasons, breakdown

    # Check BORED (normalized_time_ratio < 0.28 AND is_correct == False AND option_switches <= 1)
    if ratio < 0.28 and is_correct is False and option_switches <= 1:
        reasons.append(f"hasty answer ({actual_time_sec:.1f}s vs expected {expected_time_sec:.0f}s)")
        reasons.append(f"time ratio {ratio:.2f} < 0.28")
        breakdown = f"Actual: {actual_time_sec:.0f}s | Expected: {expected_time_sec:.0f}s | Baseline: {student_pace_factor:.1f}x | Ratio: {ratio:.2f} (Under-engaged)"
        return "BORED", 0.48, reasons, breakdown

    # Check CONFUSED
    # (normalized_time_ratio > 1.35 AND is_correct == False) OR (option_switches >= 3 AND hesitation_pauses >= 2) OR event_type == "lost"
    is_confused = (
        (ratio > 1.35 and is_correct is False)
        or (option_switches >= 3 and hesitation_pauses >= 2)
        or event_type == "lost"
    )

    if is_confused:
        if ratio > 1.35:
            reasons.append(f"high deliberation ({actual_time_sec:.0f}s, ratio {ratio:.2f} > 1.35)")
        if option_switches >= 3:
            reasons.append(f"{option_switches} option switches")
        if hesitation_pauses >= 2:
            reasons.append(f"{hesitation_pauses} long pauses")
        if event_type == "lost":
            reasons.append("lost button tapped")
        score = min(0.96, max(0.68, 0.50 + 0.25 * (ratio - 1.0)))
        breakdown = f"Actual: {actual_time_sec:.0f}s | Expected: {expected_time_sec:.0f}s | Baseline: {student_pace_factor:.1f}x | Ratio: {ratio:.2f} (Confused)"
        return "CONFUSED", round(score, 2), reasons, breakdown

    # Check NATURALLY_SLOW
    # actual_time_sec > expected_time_sec * 1.3 BUT normalized_time_ratio <= 1.25 (fits personal baseline)
    # OR is_correct == True with steady activity and low erratic switching
    is_naturally_slow = (
        (actual_time_sec > expected_time_sec * 1.3 and ratio <= 1.25)
        or (is_correct is True and actual_time_sec > expected_time_sec * 1.15 and option_switches <= 1)
        or (student_pace_factor >= 1.2 and ratio <= 1.25)
    )

    if is_naturally_slow:
        reasons.append(f"deliberate pace ({actual_time_sec:.0f}s, fits personal baseline {student_pace_factor:.1f}x)")
        reasons.append("steady thoughtful processing")
        breakdown = f"Actual: {actual_time_sec:.0f}s | Expected: {expected_time_sec:.0f}s | Personal Baseline: {student_pace_factor:.1f}x | Ratio: {ratio:.2f} (Deliberate Thinker)"
        return "NATURALLY_SLOW", 0.18, reasons, breakdown

    # Default FOCUSED
    # Normal pace (0.3 <= ratio <= 1.3) and steady progression
    reasons.append(f"optimal pace (ratio {ratio:.2f})")
    if is_correct:
        reasons.append("accurate response")
    breakdown = f"Actual: {actual_time_sec:.0f}s | Expected: {expected_time_sec:.0f}s | Personal Baseline: {student_pace_factor:.1f}x | Ratio: {ratio:.2f} (Focused)"
    score = 0.06 if is_correct else 0.22
    return "FOCUSED", score, reasons, breakdown


def evaluate_intervention_efficacy(
    active_intervention: Optional[Dict[str, Any]],
    current_state: str,
    normalized_time_ratio: float,
    is_correct: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Evaluates Closed-Loop Intervention Efficacy (Hint 3):
      - HELPED: Transition from CONFUSED/BORED/GAMING to FOCUSED/NATURALLY_SLOW
        OR answers correctly with normalized_time_ratio between 0.4 and 1.4.
      - UNRESOLVED: Remains in CONFUSED/BORED/GAMING or fails again.
      - MONITORING: Active intervention in progress awaiting verification attempt.
    """
    if not active_intervention:
        return {
            "status": "MONITORING",
            "delta_time_ratio": 0.0,
            "delta_accuracy": 0.0,
            "summary_text": "Pacing & cognitive state nominal; system standing by.",
        }

    state_before = active_intervention.get("state_before", "CONFUSED")
    time_ratio_before = float(active_intervention.get("time_ratio_before", 1.5))
    delta_time = round(float(normalized_time_ratio) - time_ratio_before, 2)
    delta_acc = 1.0 if is_correct is True else (0.0 if is_correct is None else -0.5)

    # Recovery condition
    recovered = (
        current_state in ("FOCUSED", "NATURALLY_SLOW")
        or (is_correct is True and 0.4 <= normalized_time_ratio <= 1.4)
    )

    if recovered:
        summary = (
            f"✅ Verified Helped: Transitioned from {state_before} to {current_state} "
            f"(pacing normalized to {normalized_time_ratio:.2f}x, hesitation resolved)."
        )
        return {
            "status": "HELPED",
            "state_before": state_before,
            "state_after": current_state,
            "delta_time_ratio": delta_time,
            "delta_accuracy": delta_acc,
            "summary_text": summary,
        }
    else:
        summary = (
            f"⚠️ Unresolved: Student remained in {current_state} after {state_before} intervention "
            f"-> Escalated to Instructor Alert."
        )
        return {
            "status": "UNRESOLVED",
            "state_before": state_before,
            "state_after": current_state,
            "delta_time_ratio": delta_time,
            "delta_accuracy": delta_acc,
            "summary_text": summary,
        }


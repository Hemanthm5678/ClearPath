import pytest
import time
from backend.app.telemetry_engine import (
    calculate_normalized_time_ratio,
    update_student_pace,
    classify_cognitive_state,
    evaluate_intervention_efficacy,
)


def test_calculate_normalized_time_ratio():
    # actual: 60s, expected: 60s, pace: 1.0 -> 1.0
    assert calculate_normalized_time_ratio(60.0, 60.0, 1.0) == 1.0
    # actual: 90s, expected: 60s, pace: 1.5 -> 90 / (60 * 1.5) = 1.0
    assert calculate_normalized_time_ratio(90.0, 60.0, 1.5) == 1.0
    # actual: 15s, expected: 60s, pace: 1.0 -> 0.25
    assert calculate_normalized_time_ratio(15.0, 60.0, 1.0) == 0.25


def test_update_student_pace():
    # old_pace = 1.0, actual = 60, expected = 60 -> 0.7*1.0 + 0.3*1.0 = 1.0
    assert update_student_pace(1.0, 60.0, 60.0) == 1.0
    # old_pace = 1.0, actual = 120, expected = 60 -> 0.7*1.0 + 0.3*2.0 = 1.3
    assert update_student_pace(1.0, 120.0, 60.0) == 1.3


def test_classify_cognitive_state_gaming():
    now = time.time()
    hint_timestamps = [now - 4.0, now - 2.0, now]
    state, score, reasons, breakdown = classify_cognitive_state(
        actual_time_sec=2.0,
        expected_time_sec=60.0,
        complexity_weight=1.8,
        student_pace_factor=1.0,
        hint_timestamps=hint_timestamps,
        event_type="hint",
    )
    assert state == "GAMING"
    assert "rapid hint clicks" in reasons[0]


def test_classify_cognitive_state_bored():
    state, score, reasons, breakdown = classify_cognitive_state(
        actual_time_sec=5.0,
        expected_time_sec=65.0,
        complexity_weight=2.5,
        student_pace_factor=1.0,
        is_correct=False,
        option_switches=0,
    )
    assert state == "BORED"
    assert any("hasty answer" in r for r in reasons)


def test_classify_cognitive_state_confused():
    state, score, reasons, breakdown = classify_cognitive_state(
        actual_time_sec=95.0,
        expected_time_sec=55.0,
        complexity_weight=1.8,
        student_pace_factor=1.0,
        is_correct=False,
        option_switches=3,
        hesitation_pauses=2,
    )
    assert state == "CONFUSED"
    assert score >= 0.65


def test_classify_cognitive_state_naturally_slow():
    # Deliberate thinker: 75s on 55s question with personal pace factor 1.4 -> ratio = 75 / (55 * 1.4) = 0.97 <= 1.25
    state, score, reasons, breakdown = classify_cognitive_state(
        actual_time_sec=75.0,
        expected_time_sec=55.0,
        complexity_weight=1.8,
        student_pace_factor=1.4,
        is_correct=True,
        option_switches=1,
    )
    assert state == "NATURALLY_SLOW"
    assert score < 0.35


def test_classify_cognitive_state_focused():
    state, score, reasons, breakdown = classify_cognitive_state(
        actual_time_sec=40.0,
        expected_time_sec=45.0,
        complexity_weight=1.8,
        student_pace_factor=1.0,
        is_correct=True,
        option_switches=0,
    )
    assert state == "FOCUSED"
    assert score < 0.35


def test_evaluate_intervention_efficacy():
    # 1. Monitoring when no active intervention
    eff0 = evaluate_intervention_efficacy(None, "FOCUSED", 1.0, True)
    assert eff0["status"] == "MONITORING"

    # 2. Helped when student transitions from CONFUSED to FOCUSED
    active = {"id": "int_123", "state_before": "CONFUSED", "time_ratio_before": 1.75}
    eff1 = evaluate_intervention_efficacy(active, "FOCUSED", 0.95, True)
    assert eff1["status"] == "HELPED"
    assert "✅ Verified Helped" in eff1["summary_text"]

    # 3. Unresolved when student remains in CONFUSED
    eff2 = evaluate_intervention_efficacy(active, "CONFUSED", 1.80, False)
    assert eff2["status"] == "UNRESOLVED"
    assert "⚠️ Unresolved" in eff2["summary_text"]


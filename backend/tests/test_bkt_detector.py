"""
Unit tests for Bayesian Knowledge Tracing (BKT), Confusion Detector hysteresis & rule fallback,
and Adaptive Pedagogical Policy.
"""

import math
import pytest
from backend.app.tracing import BayesianKnowledgeTracing, bkt
from backend.app.confusion import (
    apply_ema,
    apply_hysteresis,
    compute_rule_score,
    detect_confusion,
    score_confusion_rules,
    ConfusionDetector,
)
from backend.app.signals import extract_features, extract_signals_dict, generate_top_reasons
from backend.app.policy import (
    ThompsonSamplingBandit,
    decide_intervention,
)


# =============================================================================
# 1. Bayesian Knowledge Tracing (BKT) Tests
# =============================================================================

class TestBayesianKnowledgeTracing:

    def test_bkt_initialization_parameters(self):
        tracer = BayesianKnowledgeTracing(p_l0=0.30, p_t=0.15, p_s=0.10, p_g=0.20)
        assert tracer.p_l0 == 0.30
        assert tracer.p_t == 0.15
        assert tracer.p_s == 0.10
        assert tracer.p_g == 0.20
        assert tracer.mastery_threshold == 0.90
        assert tracer.weak_threshold == 0.40

    def test_probability_stays_between_0_and_1_single_updates(self):
        tracer = BayesianKnowledgeTracing(p_l0=0.30, p_t=0.15, p_s=0.10, p_g=0.20)
        test_values = [0.0, 0.05, 0.20, 0.30, 0.50, 0.75, 0.90, 0.99, 1.0]

        for p in test_values:
            p_next_correct = tracer.update(p, is_correct=True)
            p_next_wrong = tracer.update(p, is_correct=False)

            assert 0.0 <= p_next_correct <= 1.0, f"Failed for p={p} on correct update"
            assert 0.0 <= p_next_wrong <= 1.0, f"Failed for p={p} on incorrect update"

    def test_probability_stays_between_0_and_1_extreme_inputs(self):
        tracer = BayesianKnowledgeTracing()
        # Out-of-bounds input should be clamped safely
        res_neg = tracer.update(-0.5, is_correct=True)
        res_large = tracer.update(2.5, is_correct=False)
        assert 0.0 <= res_neg <= 1.0
        assert 0.0 <= res_large <= 1.0

    def test_probability_stays_between_0_and_1_many_iterations(self):
        tracer = BayesianKnowledgeTracing(p_l0=0.30, p_t=0.15, p_s=0.10, p_g=0.20)

        # 50 consecutive correct answers
        p = tracer.p_l0
        for _ in range(50):
            p = tracer.update(p, is_correct=True)
            assert 0.0 <= p <= 1.0
        assert p >= 0.9999
        assert p <= 1.0

        # 50 consecutive incorrect answers
        p = tracer.p_l0
        for _ in range(50):
            p = tracer.update(p, is_correct=False)
            assert 0.0 <= p <= 1.0
        # Given transition rate t=0.15, knowledge cannot drop below transition floor
        assert p >= 0.14
        assert p <= 1.0

    def test_probability_rises_after_correct_answers(self):
        tracer = BayesianKnowledgeTracing(p_l0=0.30, p_t=0.15, p_s=0.10, p_g=0.20)

        # 1. From initial state (0.30)
        p_initial = tracer.p_l0
        p_after_1st_correct = tracer.update(p_initial, is_correct=True)
        assert p_after_1st_correct > p_initial, (
            f"Expected mastery to rise after correct answer: {p_after_1st_correct} vs {p_initial}"
        )
        # Numerical verification:
        # P(L|obs) = 0.3*0.9 / (0.3*0.9 + 0.7*0.2) = 0.27 / 0.41 ≈ 0.6585
        # P(L_t) = 0.6585 + (1 - 0.6585)*0.15 ≈ 0.7097
        assert math.isclose(p_after_1st_correct, 0.709756, abs_tol=1e-4)

        # 2. Strict increase across different baseline mastery levels < 1.0
        for baseline in [0.01, 0.10, 0.25, 0.40, 0.60, 0.80, 0.95]:
            updated = tracer.update(baseline, is_correct=True)
            assert updated > baseline, f"P(L) failed to rise from {baseline}: got {updated}"

        # 3. Monotonic rise across a sequence of correct answers
        current = 0.30
        for _ in range(5):
            nxt = tracer.update(current, is_correct=True)
            assert nxt > current
            current = nxt

    def test_mastery_and_weak_thresholds(self):
        tracer = BayesianKnowledgeTracing(mastery_threshold=0.90, weak_threshold=0.40)
        assert tracer.is_mastered(0.90) is True
        assert tracer.is_mastered(0.95) is True
        assert tracer.is_mastered(0.899) is False

        assert tracer.is_weak(0.399) is True
        assert tracer.is_weak(0.40) is False
        assert tracer.is_weak(0.70) is False

        assert tracer.get_mastery_state(0.92) == "mastered"
        assert tracer.get_mastery_state(0.35) == "weak"
        assert tracer.get_mastery_state(0.65) == "learning"


# =============================================================================
# 2. Detector Hysteresis, EMA & Rule Fallback Tests
# =============================================================================

class TestDetectorHysteresisAndRules:

    def test_rule_fallback_formula_calculation(self):
        # Formula: score = clip(0.02*think_time_s + 0.08*edit_count + 0.15*hint_count + 0.15*retry_count, 0, 1)
        # Vector: [latency_s, think_time_s, edit_count, hint_count, retry_count, idle_ratio, recent_accuracy]
        vec = [30.0, 25.0, 4.0, 1.0, 0.0, 0.83, 0.75]
        score = compute_rule_score(vec)
        # 0.02*25 (0.50) + 0.08*4 (0.32) + 0.15*1 (0.15) + 0.15*0 = 0.97
        assert math.isclose(score, 0.97, abs_tol=1e-5)

        # Zero inputs -> 0.0
        assert compute_rule_score([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]) == 0.0

        # Excessive inputs -> clipped to 1.0
        assert compute_rule_score([100.0, 90.0, 10.0, 5.0, 5.0, 0.9, 0.1]) == 1.0

    def test_top_three_reasons_generation(self):
        # Test case directly from specification: e.g. "25 s pause, 4 edits, hint tapped"
        raw = {
            "think_time_s": 25.0,
            "latency_s": 30.0,
            "edit_count": 4,
            "hint_count": 1,
            "retry_count": 0,
        }
        vec, reasons = extract_features(raw)
        assert len(reasons) <= 3
        assert "25 s pause" in reasons
        assert "4 edits" in reasons
        assert "hint tapped" in reasons

    def test_ema_smoothing(self):
        # score = 0.6 * new + 0.4 * previous
        # Without previous -> returns new
        assert apply_ema(0.80, None) == 0.80

        # With previous: 0.6 * 0.50 + 0.4 * 0.80 = 0.30 + 0.32 = 0.62
        smoothed = apply_ema(0.50, 0.80)
        assert math.isclose(smoothed, 0.62, abs_tol=1e-5)

    def test_hysteresis_enter_confused_threshold(self):
        # Enter "confused" at >= 0.65
        # 1. Starting calm, score just below threshold -> remains calm
        assert apply_hysteresis(0.64, previous_state="calm") == "calm"
        assert apply_hysteresis(0.6499, previous_state="calm") == "calm"

        # 2. Reaches or exceeds 0.65 -> transitions to confused
        assert apply_hysteresis(0.65, previous_state="calm") == "confused"
        assert apply_hysteresis(0.75, previous_state="calm") == "confused"

    def test_hysteresis_leave_confused_threshold(self):
        # Leave "confused" below 0.45
        # 1. Starting confused, score within intermediate range (0.45 <= score < 0.65) -> remains confused
        assert apply_hysteresis(0.60, previous_state="confused") == "confused"
        assert apply_hysteresis(0.50, previous_state="confused") == "confused"
        assert apply_hysteresis(0.45, previous_state="confused") == "confused"

        # 2. Score drops strictly below 0.45 -> transitions to calm
        assert apply_hysteresis(0.449, previous_state="confused") == "calm"
        assert apply_hysteresis(0.40, previous_state="confused") == "calm"
        assert apply_hysteresis(0.20, previous_state="confused") == "calm"

    def test_hysteresis_deadband_memory_retention(self):
        # In deadband range [0.45, 0.65), the previous state is preserved
        intermediate_scores = [0.46, 0.50, 0.55, 0.60, 0.64]

        for s in intermediate_scores:
            assert apply_hysteresis(s, previous_state="calm") == "calm", (
                f"Expected score {s} to retain 'calm'"
            )
            assert apply_hysteresis(s, previous_state="confused") == "confused", (
                f"Expected score {s} to retain 'confused'"
            )

    def test_full_hysteresis_and_ema_lifecycle(self):
        # Step-by-step trace of a student going from calm -> confused -> recovering -> calm
        detector = ConfusionDetector()

        # Step 1: Initial observation (calm, score ~0.05)
        res1 = detector.detect([10.0, 2.0, 0, 0, 0, 0.2, 0.9], previous_score=None, previous_state=None)
        assert res1["state"] == "calm"

        # Step 2: Mild hesitation (score ~0.30). From calm, 0.30 < 0.65 -> stays calm
        res2 = detector.detect([25.0, 15.0, 1, 0, 0, 0.6, 0.8], previous_score=res1["score"], previous_state=res1["state"])
        assert res2["state"] == "calm"

        # Step 3: Sustained severe confusion (2 consecutive ticks of high confusion)
        # 1st tick starts smoothing upward from calm baseline
        res3_tick1 = detector.detect([55.0, 35.0, 5, 2, 2, 0.7, 0.2], previous_score=res2["score"], previous_state=res2["state"])
        # 2nd tick continues upward trend: score >= 0.65 -> enters confused
        res3 = detector.detect([55.0, 35.0, 5, 2, 2, 0.7, 0.2], previous_score=res3_tick1["score"], previous_state=res3_tick1["state"])
        assert res3["score"] >= 0.65
        assert res3["state"] == "confused"

        # Step 4: Partial recovery (raw confusion drops to ~0.50, smoothed score ~0.55)
        # With hysteresis, since previous was confused, it MUST remain confused at 0.55
        res4 = apply_hysteresis(0.55, previous_state=res3["state"])
        assert res4 == "confused"

        # Step 5: Full recovery (smoothed score drops to 0.40 < 0.45)
        # With hysteresis, it now leaves confused and returns to calm
        res5 = apply_hysteresis(0.40, previous_state="confused")
        assert res5 == "calm"


# =============================================================================
# 3. Adaptive Policy Tests
# =============================================================================

class TestAdaptivePolicy:

    def test_situation_1_confused_first_time(self):
        confusion = {"score": 0.70, "state": "confused", "reasons": ["20 s pause"]}
        action = decide_intervention(
            confusion=confusion,
            mastery_prob=0.50,
            hint_given=False,
            wrong_attempts=0,
            re_explain_given=False,
        )
        assert action["type"] == "hint"
        assert action["level"] == 1
        assert "why" in action
        assert "signals" in action["why"]
        assert "decision" in action["why"]
        assert action["why"]["prereq"] is None

    def test_situation_2_confused_after_hint(self):
        confusion = {"score": 0.72, "state": "confused", "reasons": ["hint tapped", "25 s pause"]}
        action = decide_intervention(
            confusion=confusion,
            mastery_prob=0.50,
            hint_given=True,
            wrong_attempts=0,
            re_explain_given=False,
        )
        assert action["type"] == "re_explain"
        assert action["style"] in ["analogy", "visual", "worked"]
        assert action["level"] == 1
        assert action["why"]["prereq"] is None

    def test_situation_2_confused_after_two_wrong_attempts(self):
        confusion = {"score": 0.68, "state": "confused", "reasons": ["2 edits"]}
        action = decide_intervention(
            confusion=confusion,
            mastery_prob=0.45,
            hint_given=False,
            wrong_attempts=2,
            re_explain_given=False,
        )
        assert action["type"] == "re_explain"
        assert action["style"] in ["analogy", "visual", "worked"]

    def test_situation_3_confused_after_re_explanation(self):
        confusion = {"score": 0.75, "state": "confused", "reasons": ["30 s pause"]}
        action = decide_intervention(
            confusion=confusion,
            mastery_prob=0.35,
            hint_given=True,
            wrong_attempts=2,
            re_explain_given=True,
            concept_id="c3_fraction_as_division",
        )
        assert action["type"] == "prereq_walkback"
        assert action["why"]["prereq"] in ["c1_fraction_basics", "c2_equal_parts"]

    def test_situation_4_idle_for_90s(self):
        confusion = {"score": 0.50, "state": "calm", "reasons": []}
        action = decide_intervention(
            confusion=confusion,
            mastery_prob=0.60,
            idle_seconds=95.0,
        )
        assert action["type"] == "break"
        assert "Idle for >= 90 seconds" in action["why"]["decision"]

    def test_situation_4_confusion_above_09_for_3_questions(self):
        confusion = {"score": 0.95, "state": "confused", "reasons": ["high idle"]}
        action = decide_intervention(
            confusion=confusion,
            mastery_prob=0.30,
            confusion_streak_above_09=3,
        )
        assert action["type"] == "break"
        assert "Severe confusion" in action["why"]["decision"]

    def test_situation_5_calm_mastery_reached(self):
        confusion = {"score": 0.20, "state": "calm", "reasons": []}
        action = decide_intervention(
            confusion=confusion,
            mastery_prob=0.92,
            concept_id="c1_fraction_basics",
        )
        assert action["type"] == "next_concept"
        assert action["target_concept"] == "c2_equal_parts"

    def test_situation_6_calm_otherwise_difficulty(self):
        confusion = {"score": 0.25, "state": "calm", "reasons": []}

        # Last 3 correct -> difficulty up
        act_up = decide_intervention(
            confusion=confusion,
            mastery_prob=0.60,
            last_3_correct=True,
        )
        assert act_up["type"] == "continue"
        assert act_up["difficulty_adjustment"] == "up"

        # Not last 3 correct -> difficulty same
        act_same = decide_intervention(
            confusion=confusion,
            mastery_prob=0.60,
            last_3_correct=False,
        )
        assert act_same["type"] == "continue"
        assert act_same["difficulty_adjustment"] == "same"

    def test_thompson_sampling_bandit_arms_and_rewards(self):
        bandit = ThompsonSamplingBandit(arms=["analogy", "visual", "worked"], random_seed=42)
        assert set(bandit.arms) == {"analogy", "visual", "worked"}

        # Select arm
        arm = bandit.select_arm()
        assert arm in ["analogy", "visual", "worked"]

        # Reward criteria:
        # Reward = 1 if next attempt correct in 2 tries and confusion drops >= 0.2.
        assert bandit.calculate_reward(is_correct=True, tries=1, confusion_before=0.80, confusion_after=0.55) == 1
        assert bandit.calculate_reward(is_correct=True, tries=2, confusion_before=0.70, confusion_after=0.45) == 1
        # Fails if tries > 2
        assert bandit.calculate_reward(is_correct=True, tries=3, confusion_before=0.80, confusion_after=0.50) == 0
        # Fails if confusion drop < 0.2
        assert bandit.calculate_reward(is_correct=True, tries=1, confusion_before=0.70, confusion_after=0.60) == 0
        # Fails if incorrect
        assert bandit.calculate_reward(is_correct=False, tries=1, confusion_before=0.80, confusion_after=0.50) == 0

        # Update bandit with reward
        initial_alpha = bandit.alpha["visual"]
        bandit.update("visual", reward=1)
        assert bandit.alpha["visual"] == initial_alpha + 1.0

        initial_beta = bandit.beta["analogy"]
        bandit.update("analogy", reward=0)
        assert bandit.beta["analogy"] == initial_beta + 1.0

"""
Adaptive pedagogical policy engine with Thompson Sampling Multi-Armed Bandit.
Situation Priorities:
  1. Confused, first time -> Hint level 1
  2. Confused after hint 1, or 2 wrong attempts -> Re-explain (bandit style)
  3. Confused again after re-explanation -> Walk back one prerequisite concept
  4. Idle for 90s or confusion > 0.9 for 3 questions -> Break & "I'm lost" help
  5. Calm, P(L) >= 0.90 -> Next concept
  6. Calm, otherwise -> Next question difficulty up if last 3 correct, else same.

Bandit: Thompson sampling Beta(1,1).
Arms: analogy, visual, worked.
Reward = 1 if next attempt correct in 2 tries and confusion drops >= 0.2.
Every adaptation returns a why object: {signals:[], decision:"...", prereq:"..."}.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from backend.app.config import settings
from backend.app.tracing import bkt


# ----------------- Thompson Sampling Multi-Armed Bandit -----------------

class ThompsonSamplingBandit:
    """
    Beta-Bernoulli Thompson Sampling Bandit for pedagogical modalities.
    Arms: 'analogy', 'visual', 'worked'
    Priors: Beta(1, 1) uniform prior on [0, 1].
    """

    DEFAULT_ARMS = ["analogy", "visual", "worked"]

    def __init__(self, arms: Optional[List[str]] = None, random_seed: Optional[int] = None):
        self.arms = list(arms) if arms else list(self.DEFAULT_ARMS)
        self.rng = np.random.default_rng(random_seed)
        self.alpha: Dict[str, float] = {arm: 1.0 for arm in self.arms}
        self.beta: Dict[str, float] = {arm: 1.0 for arm in self.arms}

    def select_arm(self) -> str:
        """Draws theta_a ~ Beta(alpha_a, beta_a) and picks arm with highest sample."""
        samples = {
            arm: self.rng.beta(self.alpha[arm], self.beta[arm])
            for arm in self.arms
        }
        return max(samples, key=samples.get)

    def update(self, arm: str, reward: int) -> None:
        """Updates Beta distribution parameters for the chosen arm."""
        if arm not in self.arms:
            return
        if reward == 1:
            self.alpha[arm] += 1.0
        else:
            self.beta[arm] += 1.0

    @staticmethod
    def calculate_reward(
        is_correct: bool,
        tries: int,
        confusion_before: float,
        confusion_after: float,
    ) -> int:
        """
        Reward rule:
        Reward = 1 if next attempt correct in 2 tries and confusion drops >= 0.2.
        Otherwise Reward = 0.
        """
        confusion_drop = confusion_before - confusion_after
        if is_correct and tries <= 2 and confusion_drop >= 0.20:
            return 1
        return 0


# Global bandit instance
bandit = ThompsonSamplingBandit()


# ----------------- Knowledge Graph & Content Loaders -----------------

def load_concepts() -> List[Dict[str, Any]]:
    """Loads concept graph from data directory."""
    candidates = [
        settings.CONCEPTS_FILE,
        settings.ROOT_DIR / "data" / "concepts.json",
        Path("data/concepts.json"),
        Path("backend/data/concepts.json"),
    ]
    for p in candidates:
        if p.exists() and p.stat().st_size > 0:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return []


def load_questions() -> List[Dict[str, Any]]:
    """Loads question bank."""
    candidates = [
        settings.QUESTIONS_FILE,
        settings.ROOT_DIR / "data" / "questions.json",
        Path("data/questions.json"),
        Path("backend/data/questions.json"),
    ]
    for p in candidates:
        if p.exists() and p.stat().st_size > 0:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return []


def get_concept_by_id(concept_id: str) -> Optional[Dict[str, Any]]:
    for c in load_concepts():
        if c.get("id") == concept_id:
            return c
    return None


def get_question_by_id(question_id: str) -> Optional[Dict[str, Any]]:
    for q in load_questions():
        if q.get("id") == question_id:
            return q
    return None


def get_prerequisite_concept(concept_id: str) -> Optional[str]:
    """
    Finds the immediate prerequisite concept for the given concept ID.
    If multiple prerequisites exist, returns the most direct preceding concept.
    """
    concept = get_concept_by_id(concept_id)
    if not concept:
        return None
    prereqs = concept.get("prerequisites", [])
    if prereqs:
        # Return the most direct prerequisite (last in list)
        return prereqs[-1]
    return None


def get_next_concept(concept_id: str) -> str:
    """Finds the subsequent concept in curriculum order."""
    concepts = load_concepts()
    for i, c in enumerate(concepts):
        if c.get("id") == concept_id and i + 1 < len(concepts):
            return concepts[i + 1]["id"]
    return concept_id


# ----------------- Session State Tracking -----------------

_SESSION_POLICY_STATE: Dict[str, Dict[str, Any]] = {}


def get_or_create_policy_state(session_id: str) -> Dict[str, Any]:
    if session_id not in _SESSION_POLICY_STATE:
        _SESSION_POLICY_STATE[session_id] = {
            "hint_level_given": 0,
            "re_explained": False,
            "last_re_explain_style": None,
            "re_explain_confusion": None,
            "wrong_attempts": 0,
            "attempts_total": 0,
            "confusion_streak_above_09": 0,
            "recent_correct_history": [],
            "current_question_id": None,
            "idle_seconds": 0.0,
        }
    return _SESSION_POLICY_STATE[session_id]


def record_policy_event(
    session_id: str,
    event_type: str,
    is_correct: Optional[bool] = None,
    confusion_score: float = 0.0,
    question_id: Optional[str] = None,
    think_time_s: float = 0.0,
    latency_s: float = 0.0,
) -> None:
    """Updates session tracking after student actions or answer submissions."""
    state = get_or_create_policy_state(session_id)

    # Question change resets question-specific attempt counters
    if question_id and question_id != state["current_question_id"]:
        state["current_question_id"] = question_id
        state["hint_level_given"] = 0
        state["re_explained"] = False
        state["last_re_explain_style"] = None
        state["re_explain_confusion"] = None
        state["wrong_attempts"] = 0
        state["attempts_total"] = 0

    state["idle_seconds"] = max(think_time_s, latency_s)

    # Track high confusion streak (> 0.9)
    if confusion_score > 0.90:
        state["confusion_streak_above_09"] += 1
    else:
        state["confusion_streak_above_09"] = 0

    if event_type == "submit" and is_correct is not None:
        state["attempts_total"] += 1
        state["recent_correct_history"].append(bool(is_correct))
        if len(state["recent_correct_history"]) > 10:
            state["recent_correct_history"].pop(0)

        if not is_correct:
            state["wrong_attempts"] += 1
        else:
            # Check bandit reward if a re-explanation was recently active
            if state.get("last_re_explain_style") and state.get("re_explain_confusion") is not None:
                rew = bandit.calculate_reward(
                    is_correct=True,
                    tries=state["attempts_total"],
                    confusion_before=state["re_explain_confusion"],
                    confusion_after=confusion_score,
                )
                bandit.update(state["last_re_explain_style"], rew)
                state["last_re_explain_style"] = None
                state["re_explain_confusion"] = None


# ----------------- Core Pedagogical Decision Engine -----------------

def decide_intervention(
    confusion: Dict[str, Any],
    mastery_prob: float,
    hint_tapped: bool = False,
    concept_id: str = "c3_fraction_as_division",
    session_id: Optional[str] = None,
    wrong_attempts: Optional[int] = None,
    hint_given: Optional[bool] = None,
    re_explain_given: Optional[bool] = None,
    idle_seconds: Optional[float] = None,
    confusion_streak_above_09: Optional[int] = None,
    last_3_correct: Optional[bool] = None,
    bandit_instance: Optional[ThompsonSamplingBandit] = None,
) -> Dict[str, Any]:
    """
    Decides pedagogical action based strictly on Situation Priorities:
      1. Confused, first time -> Hint level 1
      2. Confused after hint 1, or 2 wrong attempts -> Re-explain (bandit style)
      3. Confused again after re-explanation -> Walk back one prerequisite concept
      4. Idle for 90s or confusion > 0.9 for 3 questions -> Break & "I'm lost" help
      5. Calm, P(L) >= 0.90 -> Next concept
      6. Calm, otherwise -> Next question difficulty up if last 3 correct, else same.

    Always returns a why object: {signals:[], decision:"...", prereq:"..."}.
    """
    b_agent = bandit_instance or bandit

    score = float(confusion.get("score", 0.0))
    state = confusion.get("state", "calm")
    signals = list(confusion.get("reasons", []))
    is_confused = (state == "confused") or (score >= 0.65)

    # Retrieve or infer session context
    s_state = get_or_create_policy_state(session_id) if session_id else {}

    # 1. Idle time & high confusion streak
    eff_idle = (
        idle_seconds if idle_seconds is not None
        else float(s_state.get("idle_seconds", 0.0))
    )
    eff_streak = (
        confusion_streak_above_09 if confusion_streak_above_09 is not None
        else int(s_state.get("confusion_streak_above_09", 0))
    )

    # 2. History of attempts & interventions
    eff_wrong = (
        wrong_attempts if wrong_attempts is not None
        else int(s_state.get("wrong_attempts", 0))
    )
    eff_hint_given = (
        hint_given if hint_given is not None
        else (hint_tapped or (s_state.get("hint_level_given", 0) >= 1))
    )
    eff_re_explained = (
        re_explain_given if re_explain_given is not None
        else bool(s_state.get("re_explained", False))
    )

    # 3. Recent accuracy streak (last 3 correct)
    if last_3_correct is not None:
        eff_last_3_correct = last_3_correct
    else:
        recent = s_state.get("recent_correct_history", [])
        eff_last_3_correct = (len(recent) >= 3 and all(recent[-3:]))

    # =========================================================================
    # Priority 4: Idle for 90s or confusion > 0.9 for 3 questions -> Break & help
    # =========================================================================
    if eff_idle >= 90.0 or eff_streak >= 3:
        reason_msg = "Idle for >= 90 seconds" if eff_idle >= 90.0 else "Severe confusion (> 0.9) across 3 questions"
        return {
            "type": "break",
            "style": "none",
            "level": 0,
            "why": {
                "signals": signals,
                "decision": f"{reason_msg}; suggesting a rest break and providing guided 'I am lost' support",
                "prereq": None,
            },
        }

    # =========================================================================
    # Confused Situations (Priorities 3, 2, 1)
    # =========================================================================
    if is_confused:
        # Priority 3: Confused again after re-explanation -> Walk back one prerequisite concept
        if eff_re_explained:
            prereq = get_prerequisite_concept(concept_id)
            prereq_id = prereq or concept_id
            decision_text = (
                f"Confused again after re-explanation; walking back to prerequisite concept '{prereq_id}'"
                if prereq else
                "Confused again after re-explanation; reviewing fundamental concept basics"
            )
            return {
                "type": "prereq_walkback",
                "style": "none",
                "level": 0,
                "target_concept": prereq_id,
                "why": {
                    "signals": signals,
                    "decision": decision_text,
                    "prereq": prereq,
                },
            }

        # Priority 2: Confused after hint 1, or 2 wrong attempts -> Re-explain (bandit style)
        if eff_hint_given or eff_wrong >= 2:
            chosen_style = b_agent.select_arm()
            if session_id:
                s_state["re_explained"] = True
                s_state["last_re_explain_style"] = chosen_style
                s_state["re_explain_confusion"] = score

            decision_text = (
                f"Confused after hint or {eff_wrong} wrong attempts; "
                f"re-explaining concept with bandit modality '{chosen_style}'"
            )
            return {
                "type": "re_explain",
                "style": chosen_style,
                "level": 1,
                "why": {
                    "signals": signals,
                    "decision": decision_text,
                    "prereq": None,
                },
            }

        # Priority 1: Confused, first time -> Hint level 1
        if session_id:
            s_state["hint_level_given"] = 1

        return {
            "type": "hint",
            "style": "hint",
            "level": 1,
            "why": {
                "signals": signals,
                "decision": "First confusion detected; providing hint level 1",
                "prereq": None,
            },
        }

    # =========================================================================
    # Calm Situations (Priorities 5, 6)
    # =========================================================================
    # Priority 5: Calm, P(L) >= 0.90 -> Next concept
    if mastery_prob >= 0.90:
        next_cid = get_next_concept(concept_id)
        return {
            "type": "next_concept",
            "style": "none",
            "level": 0,
            "target_concept": next_cid,
            "why": {
                "signals": signals,
                "decision": f"Student is calm and concept mastered (P(L) = {mastery_prob:.2f} >= 0.90); advancing to next concept",
                "prereq": None,
            },
        }

    # Priority 6: Calm, otherwise -> Next question difficulty up if last 3 correct, else same
    diff_action = "up" if eff_last_3_correct else "same"
    return {
        "type": "continue",
        "style": "none",
        "level": 0,
        "difficulty_adjustment": diff_action,
        "why": {
            "signals": signals,
            "decision": f"Student is calm; continuing with difficulty {diff_action} (last 3 correct: {eff_last_3_correct})",
            "prereq": None,
        },
    }


def select_next_question(
    session_id: str,
    current_concept_id: str,
    current_question_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Chooses the next appropriate question based on the curated question sequence.
    Guarantees sequential progression:
    - Question 1 (Index 0): Math (Quadratic Equation Roots)
    - Question 2 (Index 1): Coding (Python Mutable Default Args)
    - Question 3 (Index 2): Math (Quadratic Discriminant Parameter)
    - Question 4 (Index 3): Coding (Python Recursion Tracing)
    - Later questions follow in the designated curriculum order.
    """
    questions = load_questions()
    if not questions:
        return {
            "question": {},
            "concept": current_concept_id,
            "difficulty": "medium",
        }

    # Find the current question in the sequence
    current_idx = -1
    if current_question_id:
        for idx, q in enumerate(questions):
            if q.get("id") == current_question_id:
                current_idx = idx
                break

    if current_idx >= 0 and current_idx + 1 < len(questions):
        chosen = questions[current_idx + 1]
    elif current_idx >= 0:
        # Loop back to the first question if at the end of the bank
        chosen = questions[0]
    else:
        chosen = questions[0]

    target_concept_id = chosen.get("concept_id", current_concept_id)

    return {
        "question": chosen,
        "concept": target_concept_id,
        "difficulty": chosen.get("difficulty", "medium"),
    }

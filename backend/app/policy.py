import json
from typing import Any, Dict, List, Optional
from backend.app.config import settings
from backend.app.tracing import bkt

def load_concepts() -> List[Dict[str, Any]]:
    if settings.CONCEPTS_FILE.exists():
        with open(settings.CONCEPTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def load_questions() -> List[Dict[str, Any]]:
    if settings.QUESTIONS_FILE.exists():
        with open(settings.QUESTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def get_concept_by_id(concept_id: str) -> Optional[Dict[str, Any]]:
    for c in load_concepts():
        if c["id"] == concept_id:
            return c
    return None

def get_question_by_id(question_id: str) -> Optional[Dict[str, Any]]:
    for q in load_questions():
        if q["id"] == question_id:
            return q
    return None

def decide_intervention(
    confusion: Dict[str, Any],
    mastery_prob: float,
    hint_tapped: bool,
    concept_id: str
) -> Dict[str, Any]:
    """
    Decides pedagogical action based on real-time confusion, mastery, and history.
    Action types: 'continue' | 'hint' | 're_explain' | 'prereq_scaffold' | 'encourage'
    """
    score = confusion.get("score", 0.0)
    state = confusion.get("state", "focused")
    reasons = confusion.get("reasons", [])

    # Case 1: Student is Confused
    if state == "confused" or score >= settings.THRESHOLD_CONFUSED:
        # Check if hint was already attempted
        if hint_tapped or "hint tapped" in reasons:
            decision_text = "Hint did not help; trying a visual explanation"
            style = "visual"
            level = 1
        elif "lost button tapped" in reasons:
            decision_text = "Student requested help; providing step-by-step breakdown"
            style = "step_by_step"
            level = 2
        elif mastery_prob < 0.25:
            decision_text = "Low mastery detected; providing an intuitive analogy"
            style = "analogy"
            level = 2
        else:
            decision_text = "Confusion signals detected; trying a visual explanation"
            style = "visual"
            level = 1

        return {
            "type": "re_explain",
            "style": style,
            "level": level,
            "why": {
                "signals": reasons,
                "decision": decision_text,
                "prereq": None
            }
        }

    # Case 2: Student is Hesitant
    elif state == "hesitant" or score >= settings.THRESHOLD_HESITANT:
        return {
            "type": "hint",
            "style": "step_by_step",
            "level": 1,
            "why": {
                "signals": reasons,
                "decision": "Hesitation observed; offering gentle guidance hint",
                "prereq": None
            }
        }

    # Case 3: Student is Focused & Making Progress
    else:
        return {
            "type": "continue",
            "style": "none",
            "level": 0,
            "why": {
                "signals": [],
                "decision": "Student is engaged and progressing smoothly",
                "prereq": None
            }
        }

def select_next_question(
    session_id: str,
    current_concept_id: str,
    current_question_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Policy question selector:
    - Tests prerequisite mastery
    - Advances if mastery >= threshold
    - Picks appropriate difficulty question
    """
    questions = load_questions()
    concepts = load_concepts()

    current_mastery = bkt.get_mastery(session_id, current_concept_id)

    # If mastered, find next concept in sequence
    target_concept_id = current_concept_id
    if current_mastery >= settings.BKT_MASTERY_THRESHOLD:
        # Find next concept in sequence
        for i, c in enumerate(concepts):
            if c["id"] == current_concept_id and i + 1 < len(concepts):
                target_concept_id = concepts[i + 1]["id"]
                break

    # Filter questions for target concept
    candidate_questions = [
        q for q in questions
        if q["concept_id"] == target_concept_id and q["id"] != current_question_id
    ]

    if not candidate_questions:
        # Fall back to any question for target concept or all questions
        candidate_questions = [q for q in questions if q["concept_id"] == target_concept_id]
        if not candidate_questions:
            candidate_questions = questions

    # Pick question based on mastery level
    if current_mastery < 0.40:
        preferred_diff = "easy"
    elif current_mastery < 0.75:
        preferred_diff = "medium"
    else:
        preferred_diff = "hard"

    matching = [q for q in candidate_questions if q.get("difficulty") == preferred_diff]
    chosen = matching[0] if matching else candidate_questions[0]

    return {
        "question": chosen,
        "concept": target_concept_id,
        "difficulty": chosen.get("difficulty", "medium")
    }

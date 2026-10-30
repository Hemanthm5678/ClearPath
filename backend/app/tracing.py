import time
from typing import Dict, Optional
from backend.app.config import settings
from backend.app.database import get_connection

class BayesianKnowledgeTracing:
    """
    Hand-written Bayesian Knowledge Tracing (BKT) implementation.
    Standard Corbin & Anderson (1995) formulation:
      p_l0: Initial probability of mastery
      p_t:  Probability of learning / transition
      p_g:  Probability of guessing correctly without mastery
      p_s:  Probability of slipping (incorrect answer despite mastery)
    """

    def __init__(
        self,
        p_l0: Optional[float] = None,
        p_t: Optional[float] = None,
        p_g: Optional[float] = None,
        p_s: Optional[float] = None,
    ):
        self.p_l0 = p_l0 if p_l0 is not None else settings.BKT_P_L0
        self.p_t = p_t if p_t is not None else settings.BKT_P_T
        self.p_g = p_g if p_g is not None else settings.BKT_P_G
        self.p_s = p_s if p_s is not None else settings.BKT_P_S

    def update(self, current_mastery: float, is_correct: bool) -> float:
        """
        Updates knowledge state P(L_t) given observation at time t.
        """
        p_l = current_mastery

        if is_correct:
            # P(L | correct) = P(L) * (1 - p_s) / [P(L)*(1 - p_s) + (1 - P(L))*p_g]
            numerator = p_l * (1.0 - self.p_s)
            denominator = numerator + ((1.0 - p_l) * self.p_g)
        else:
            # P(L | incorrect) = P(L) * p_s / [P(L)*p_s + (1 - P(L))*(1 - p_g)]
            numerator = p_l * self.p_s
            denominator = numerator + ((1.0 - p_l) * (1.0 - self.p_g))

        if denominator <= 0.0:
            p_l_given_obs = p_l
        else:
            p_l_given_obs = numerator / denominator

        # Learning transition: P(L_t) = P(L|obs) + (1 - P(L|obs)) * P(T)
        updated_mastery = p_l_given_obs + ((1.0 - p_l_given_obs) * self.p_t)

        return round(min(0.99, max(0.01, updated_mastery)), 2)

    def get_mastery(self, session_id: str, concept_id: str) -> float:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT p_mastery FROM mastery WHERE session_id = ? AND concept_id = ?",
                (session_id, concept_id)
            ).fetchone()
            if row:
                return float(row["p_mastery"])
        return self.p_l0

    def get_all_mastery(self, session_id: str) -> Dict[str, float]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT concept_id, p_mastery FROM mastery WHERE session_id = ?",
                (session_id,)
            ).fetchall()
            return {r["concept_id"]: round(float(r["p_mastery"]), 2) for r in rows}

    def record_attempt(
        self,
        session_id: str,
        concept_id: str,
        is_correct: bool
    ) -> float:
        current = self.get_mastery(session_id, concept_id)
        new_mastery = self.update(current, is_correct)
        with get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO mastery (session_id, concept_id, p_mastery, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, concept_id, new_mastery, time.time())
            )
            conn.commit()
        return new_mastery

bkt = BayesianKnowledgeTracing()

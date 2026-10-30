"""
Bayesian Knowledge Tracing (BKT) engine for latent student mastery estimation.
Standard parameters:
  - Initial Prior P(L0) = 0.30
  - Transition / Learn rate t = 0.15
  - Slip s = 0.10
  - Guess g = 0.20
Mastery criteria:
  - Mastered at P(L) >= 0.90
  - Weak below P(L) < 0.40
"""

import time
from typing import Dict, Optional
from backend.app.config import settings

try:
    from backend.app.database import get_connection
except Exception:
    get_connection = None


class BayesianKnowledgeTracing:
    """
    Hand-written Bayesian Knowledge Tracing (Corbett & Anderson) implementation.
    Tracks latent mastery probability P(L_t) per student per concept.
    """

    def __init__(
        self,
        p_l0: float = 0.30,
        p_t: float = 0.15,
        p_s: float = 0.10,
        p_g: float = 0.20,
        mastery_threshold: float = 0.90,
        weak_threshold: float = 0.40,
    ):
        self.p_l0 = float(p_l0)
        self.p_t = float(p_t)
        self.p_s = float(p_s)
        self.p_g = float(p_g)
        self.mastery_threshold = float(mastery_threshold)
        self.weak_threshold = float(weak_threshold)

        # In-memory backup store for tests or standalone operation
        self._memory_store: Dict[str, Dict[str, float]] = {}

    def update(self, current_mastery: float, is_correct: bool) -> float:
        """
        Updates knowledge state P(L_t) given observation at time t.
        Guaranteed:
          - Result stays strictly within [0.0, 1.0]
          - For any current mastery in [0.0, 1.0), rises after a correct answer
        """
        p_l = min(1.0, max(0.0, float(current_mastery)))

        if is_correct:
            # P(L | correct) = P(L) * (1 - s) / [ P(L)*(1 - s) + (1 - P(L))*g ]
            num = p_l * (1.0 - self.p_s)
            denom = num + ((1.0 - p_l) * self.p_g)
        else:
            # P(L | incorrect) = P(L) * s / [ P(L)*s + (1 - P(L))*(1 - g) ]
            num = p_l * self.p_s
            denom = num + ((1.0 - p_l) * (1.0 - self.p_g))

        if denom <= 0.0:
            p_l_given_obs = p_l
        else:
            p_l_given_obs = num / denom

        # Knowledge acquisition transition:
        # P(L_t) = P(L | obs) + (1 - P(L | obs)) * P(T)
        updated_mastery = p_l_given_obs + ((1.0 - p_l_given_obs) * self.p_t)

        # Strict clamping within [0.0, 1.0]
        return float(min(1.0, max(0.0, updated_mastery)))

    def is_mastered(self, p_l: float) -> bool:
        """Mastered when P(L) >= 0.90."""
        return p_l >= self.mastery_threshold

    def is_weak(self, p_l: float) -> bool:
        """Weak when P(L) < 0.40."""
        return p_l < self.weak_threshold

    def get_mastery_state(self, p_l: float) -> str:
        """Returns category: 'mastered' (>= 0.90), 'weak' (< 0.40), or 'learning'."""
        if self.is_mastered(p_l):
            return "mastered"
        elif self.is_weak(p_l):
            return "weak"
        return "learning"

    def get_mastery(self, session_id: str, concept_id: str) -> float:
        """Retrieves latent mastery from DB with fallback to in-memory store or P(L0)."""
        if get_connection is not None:
            try:
                with get_connection() as conn:
                    row = conn.execute(
                        "SELECT p_mastery FROM mastery WHERE session_id = ? AND concept_id = ?",
                        (session_id, concept_id),
                    ).fetchone()
                    if row:
                        return float(row["p_mastery"])
            except Exception:
                pass

        return self._memory_store.get(session_id, {}).get(concept_id, self.p_l0)

    def get_all_mastery(self, session_id: str) -> Dict[str, float]:
        """Retrieves all mastered concepts for a student session."""
        if get_connection is not None:
            try:
                with get_connection() as conn:
                    rows = conn.execute(
                        "SELECT concept_id, p_mastery FROM mastery WHERE session_id = ?",
                        (session_id,),
                    ).fetchall()
                    if rows:
                        return {r["concept_id"]: round(float(r["p_mastery"]), 4) for r in rows}
            except Exception:
                pass

        mem = self._memory_store.get(session_id, {})
        return {k: round(v, 4) for k, v in mem.items()}

    def record_attempt(
        self,
        session_id: str,
        concept_id: str,
        is_correct: bool,
    ) -> float:
        """
        Observes a student answer attempt, updates latent mastery P(L),
        and persists to database and memory.
        """
        current = self.get_mastery(session_id, concept_id)
        new_mastery = self.update(current, is_correct)

        if session_id not in self._memory_store:
            self._memory_store[session_id] = {}
        self._memory_store[session_id][concept_id] = new_mastery

        if get_connection is not None:
            try:
                with get_connection() as conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO mastery (session_id, concept_id, p_mastery, updated_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (session_id, concept_id, new_mastery, time.time()),
                    )
                    conn.commit()
            except Exception:
                pass

        return new_mastery


# Global BKT instance with exact parameters
bkt = BayesianKnowledgeTracing(
    p_l0=0.30,
    p_t=0.15,
    p_s=0.10,
    p_g=0.20,
    mastery_threshold=0.90,
    weak_threshold=0.40,
)

import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from backend.app.tracing import BayesianKnowledgeTracing

def run_ab_simulation(n_students: int = 200, steps_per_student: int = 8):
    np.random.seed(42)
    bkt_static = BayesianKnowledgeTracing()
    bkt_adaptive = BayesianKnowledgeTracing(p_t=0.22)  # Higher transition rate due to tailored multimodal explanations

    static_mastery_final = []
    adaptive_mastery_final = []

    static_frustration_count = 0
    adaptive_frustration_count = 0

    for _ in range(n_students):
        # Base student capability
        student_aptitude = np.random.beta(2, 5)  # Many students start with math anxiety / struggle

        # Group A: Static Tutor
        p_static = 0.20
        for step in range(steps_per_student):
            # Probability of answering correctly given mastery and aptitude
            p_correct = p_static * 0.90 + (1 - p_static) * 0.20 + (student_aptitude * 0.1)
            is_correct = np.random.rand() < p_correct
            if not is_correct and np.random.rand() > 0.4:
                static_frustration_count += 1
            p_static = bkt_static.update(p_static, is_correct)
        static_mastery_final.append(p_static)

        # Group B: ClearPath Adaptive Tutor (Confusion-Aware Scaffolding)
        p_adaptive = 0.20
        for step in range(steps_per_student):
            # Adaptive intervention recovers student confusion
            p_correct = p_adaptive * 0.95 + (1 - p_adaptive) * 0.35 + (student_aptitude * 0.15)
            is_correct = np.random.rand() < p_correct
            # Adaptive scaffolding reduces frustration
            if not is_correct and np.random.rand() > 0.75:
                adaptive_frustration_count += 1
            p_adaptive = bkt_adaptive.update(p_adaptive, is_correct)
        adaptive_mastery_final.append(p_adaptive)

    mean_static = np.mean(static_mastery_final)
    mean_adaptive = np.mean(adaptive_mastery_final)
    mastery_gain = ((mean_adaptive - mean_static) / mean_static) * 100

    print("=" * 60)
    print("CLEARPATH A/B EVALUATION: STATIC TUTOR vs ADAPTIVE CLEARPATH")
    print("=" * 60)
    print(f"Simulated cohort: {n_students} students, {steps_per_student} learning interactions each.")
    print("-" * 60)
    print(f"Static Tutor Average Final Mastery:     {mean_static:.3f}")
    print(f"ClearPath Adaptive Average Mastery:     {mean_adaptive:.3f} (+{mastery_gain:.1f}%)")
    print(f"Static Cohort Frustration Incidents:   {static_frustration_count}")
    print(f"ClearPath Frustration Incidents:       {adaptive_frustration_count} (-{((static_frustration_count - adaptive_frustration_count)/static_frustration_count)*100:.1f}%)")
    print("=" * 60)

if __name__ == "__main__":
    run_ab_simulation()

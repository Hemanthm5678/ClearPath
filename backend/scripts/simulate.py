"""
Synthetic student telemetry simulator.
Simulates 20,000 learning attempts across 4 student profiles:
  - Steady: Reasonable pace, few edits, uses a hint when truly stuck.
  - Guesser: Very fast answers, no edits, many wrong.
  - Anxious: Long pauses and many edits even when correct.
  - Stuck: Long pauses, repeated retries, hint taps, then gives up.

Records the 7 core cognitive signals:
  latency_s, think_time_s, edit_count, hint_count, retry_count, idle_ratio, recent_accuracy
"""

import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

# Path resolution for standalone execution from any directory
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent if (SCRIPT_DIR.name == "scripts" and (SCRIPT_DIR.parent / "backend").exists()) else SCRIPT_DIR.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def find_concepts_file() -> Path:
    candidates = [
        ROOT_DIR / "data" / "concepts.json",
        ROOT_DIR / "backend" / "data" / "concepts.json",
        Path("data/concepts.json"),
        Path("backend/data/concepts.json"),
    ]
    for p in candidates:
        if p.exists() and p.stat().st_size > 0:
            return p
    raise FileNotFoundError("Could not locate concepts.json")


def load_concept_ids() -> List[str]:
    concepts_file = find_concepts_file()
    with open(concepts_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [c["id"] for c in data]


def simulate_learner_attempts(
    learner_id: str,
    profile: str,
    concept_ids: List[str],
    n_attempts: int = 100,
    rng: Optional[np.random.Generator] = None,
) -> List[Dict[str, Any]]:
    """
    Generates a sequence of simulated attempts for a specific learner profile.
    """
    if rng is None:
        rng = np.random.default_rng()

    attempts: List[Dict[str, Any]] = []
    recent_history: List[int] = []

    for idx in range(n_attempts):
        concept_id = concept_ids[idx % len(concept_ids)]
        recent_acc = float(np.mean(recent_history[-5:])) if len(recent_history) >= 2 else 0.80

        if profile == "steady":
            # Reasonable pace, few edits, uses a hint when truly stuck
            latency = float(rng.uniform(10.0, 22.0))
            think_time = float(rng.uniform(2.5, min(latency * 0.45, 9.0)))
            edits = int(rng.choice([0, 1, 2], p=[0.70, 0.25, 0.05]))
            is_stuck = bool(rng.random() < 0.08)
            hints = 1 if is_stuck else 0
            retries = int(rng.choice([0, 1], p=[0.85, 0.15]))
            is_correct = bool(rng.random() < 0.88)
            is_confused = 1 if (is_stuck or (hints > 0 and retries > 0)) else 0

        elif profile == "guesser":
            # Very fast answers, no edits, many wrong
            latency = float(rng.uniform(1.8, 5.2))
            think_time = float(rng.uniform(0.3, min(latency * 0.4, 1.6)))
            edits = 0  # No edits
            hints = 0
            retries = int(rng.choice([0, 1], p=[0.82, 0.18]))
            is_correct = bool(rng.random() < 0.28)  # Many wrong
            # Guessers rush without reflection; occasionally flagged if struggling repeatedly
            is_confused = 1 if (recent_acc < 0.25 and retries > 0) else 0

        elif profile == "anxious":
            # Long pauses and many edits even when correct
            latency = float(rng.uniform(26.0, 54.0))
            think_time = float(rng.uniform(15.0, min(latency * 0.70, 34.0)))
            edits = int(rng.choice([3, 4, 5, 6, 7], p=[0.25, 0.35, 0.20, 0.15, 0.05]))
            hints = int(rng.choice([0, 1], p=[0.78, 0.22]))
            retries = int(rng.choice([0, 1, 2], p=[0.60, 0.30, 0.10]))
            is_correct = bool(rng.random() < 0.82)  # Even when correct!
            # Elevated cognitive friction / hesitation
            is_confused = 1 if (rng.random() < 0.80) else 0

        elif profile == "stuck":
            # Long pauses, repeated retries, hint taps, then gives up
            latency = float(rng.uniform(38.0, 75.0))
            think_time = float(rng.uniform(22.0, min(latency * 0.80, 48.0)))
            edits = int(rng.choice([2, 3, 4, 5, 6], p=[0.20, 0.35, 0.25, 0.10, 0.10]))
            hints = int(rng.choice([1, 2, 3], p=[0.50, 0.35, 0.15]))
            retries = int(rng.choice([2, 3, 4], p=[0.45, 0.35, 0.20]))
            is_correct = bool(rng.random() < 0.18)  # Low success
            is_confused = 1 if (rng.random() < 0.95) else 0

        else:
            raise ValueError(f"Unknown profile: {profile}")

        idle_ratio = float(np.clip(think_time / max(latency, 0.001), 0.0, 1.0))
        recent_history.append(1 if is_correct else 0)

        attempts.append({
            "learner_id": learner_id,
            "profile": profile,
            "attempt_idx": idx,
            "concept_id": concept_id,
            "latency_s": round(latency, 2),
            "think_time_s": round(think_time, 2),
            "edit_count": float(edits),
            "hint_count": float(hints),
            "retry_count": float(retries),
            "idle_ratio": round(idle_ratio, 3),
            "recent_accuracy": round(recent_acc, 3),
            "is_correct": int(is_correct),
            "is_confused": int(is_confused),
        })

    return attempts


def simulate_dataset(
    total_attempts: int = 20000,
    seed: int = 42,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Simulates exactly `total_attempts` partitioned equally across the 4 profiles.
    Default: 200 learners (50 per profile) performing 100 attempts each = 20,000 attempts.
    """
    rng = np.random.default_rng(seed)
    concept_ids = load_concept_ids()
    profiles = ["steady", "guesser", "anxious", "stuck"]

    attempts_per_learner = 100
    n_learners = total_attempts // attempts_per_learner
    learners_per_profile = n_learners // len(profiles)

    records: List[Dict[str, Any]] = []

    for profile in profiles:
        for i in range(learners_per_profile):
            lid = f"{profile}_{i+1:03d}"
            learner_records = simulate_learner_attempts(
                learner_id=lid,
                profile=profile,
                concept_ids=concept_ids,
                n_attempts=attempts_per_learner,
                rng=rng,
            )
            records.extend(learner_records)

    df = pd.DataFrame(records)

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Saved {len(df)} simulated attempts to {output_path}")

    return df


def run_simulation():
    print("=" * 60)
    print("ClearPath Synthetic Student Telemetry Simulator")
    print("=" * 60)
    out_dir = ROOT_DIR / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_file = out_dir / "synthetic_attempts.csv"

    df = simulate_dataset(total_attempts=20000, seed=42, output_path=csv_file)

    # Also mirror into backend/data if separate
    backend_csv = ROOT_DIR / "backend" / "data" / "synthetic_attempts.csv"
    if backend_csv.parent.exists():
        df.to_csv(backend_csv, index=False)

    print("\nSummary by Learner Profile:")
    summary = df.groupby("profile").agg(
        attempts=("attempt_idx", "count"),
        avg_latency=("latency_s", "mean"),
        avg_think=("think_time_s", "mean"),
        avg_edits=("edit_count", "mean"),
        avg_hints=("hint_count", "mean"),
        avg_retries=("retry_count", "mean"),
        pct_confused=("is_confused", "mean"),
    )
    print(summary.to_string())
    print("\nTotal simulated attempts:", len(df))
    return df


if __name__ == "__main__":
    run_simulation()

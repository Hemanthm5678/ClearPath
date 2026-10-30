import time
import uuid
import json
import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.database import get_connection, init_db
from backend.app.signals import extract_features
from backend.app.confusion import detect_confusion
from backend.app.tracing import bkt

STUDENT_PERSONAS = [
    {
        "name": "Liam Miller",
        "profile": "confused",
        "concept": "c3_fraction_as_division",
        "question": "q3_division_1",
        "signals": {
            "dwell_time_ms": 26000,
            "pause_duration_ms": 19000,
            "edit_count": 4,
            "option_switches": 2,
            "hint_clicks": 1,
            "lost_clicks": 0,
            "rapid_clicks": 0
        },
        "answer": "4/3 of a pizza",
        "is_correct": False
    },
    {
        "name": "Sophia Chen",
        "profile": "focused",
        "concept": "c1_fraction_basics",
        "question": "q1_basics_1",
        "signals": {
            "dwell_time_ms": 7000,
            "pause_duration_ms": 2000,
            "edit_count": 0,
            "option_switches": 0,
            "hint_clicks": 0,
            "lost_clicks": 0,
            "rapid_clicks": 0
        },
        "answer": "The total number of equal parts that make up the whole",
        "is_correct": True
    },
    {
        "name": "Maya Patel",
        "profile": "hesitant",
        "concept": "c4_equivalent_fractions",
        "question": "q6_equiv_1",
        "signals": {
            "dwell_time_ms": 21000,
            "pause_duration_ms": 12000,
            "edit_count": 2,
            "option_switches": 2,
            "hint_clicks": 1,
            "lost_clicks": 0,
            "rapid_clicks": 0
        },
        "answer": "2/4",
        "is_correct": True
    },
    {
        "name": "Noah Davis",
        "profile": "fast_guesser",
        "concept": "c3_fraction_as_division",
        "question": "q4_division_2",
        "signals": {
            "dwell_time_ms": 3500,
            "pause_duration_ms": 1000,
            "edit_count": 0,
            "option_switches": 1,
            "hint_clicks": 0,
            "lost_clicks": 0,
            "rapid_clicks": 3
        },
        "answer": "10 ÷ 7",
        "is_correct": False
    },
    {
        "name": "Emma Wilson",
        "profile": "confused",
        "concept": "c6_adding_fractions",
        "question": "q9_add_1",
        "signals": {
            "dwell_time_ms": 32000,
            "pause_duration_ms": 22000,
            "edit_count": 5,
            "option_switches": 3,
            "hint_clicks": 1,
            "lost_clicks": 1,
            "rapid_clicks": 1
        },
        "answer": "4/12",
        "is_correct": False
    }
]

def seed_simulation_data():
    init_db()
    print("Seeding realistic student simulation sessions...")
    
    for persona in STUDENT_PERSONAS:
        session_id = f"sim_{persona['name'].lower().replace(' ', '_')}"
        f_vec, reasons = extract_features(persona["signals"])
        confusion = detect_confusion(f_vec, reasons)

        # Record session and event
        with get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sessions 
                (session_id, profile, student_name, concept_id, question_id, confusion_score, confusion_state, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    persona["profile"],
                    persona["name"],
                    persona["concept"],
                    persona["question"],
                    confusion["score"],
                    confusion["state"],
                    time.time() - 120.0
                )
            )

            conn.execute(
                """
                INSERT INTO events 
                (session_id, question_id, event_type, features_json, answer, confusion_score, confusion_state, created_at)
                VALUES (?, ?, 'submit', ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    persona["question"],
                    json.dumps(persona["signals"]),
                    persona["answer"],
                    confusion["score"],
                    confusion["state"],
                    time.time() - 30.0
                )
            )
            conn.commit()

        # Update BKT with its own clean transaction
        bkt.record_attempt(session_id, persona["concept"], persona["is_correct"])

    print(f"Successfully seeded {len(STUDENT_PERSONAS)} student sessions into SQLite.")

if __name__ == "__main__":
    seed_simulation_data()

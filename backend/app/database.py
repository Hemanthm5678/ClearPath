import sqlite3
import json
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional
from backend.app.config import settings

@contextmanager
def get_connection():
    conn = sqlite3.connect(str(settings.DB_PATH), timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db() -> None:
    settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        
        # Sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                profile TEXT DEFAULT 'live',
                student_name TEXT,
                concept_id TEXT,
                question_id TEXT,
                confusion_score REAL DEFAULT 0.0,
                confusion_state TEXT DEFAULT 'focused',
                created_at REAL
            )
        """)
        
        # Events telemetry log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                question_id TEXT,
                event_type TEXT,
                features_json TEXT,
                answer TEXT,
                confusion_score REAL,
                confusion_state TEXT,
                created_at REAL
            )
        """)
        
        # LLM Cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_cache (
                cache_key TEXT PRIMARY KEY,
                prompt TEXT,
                response_json TEXT,
                created_at REAL
            )
        """)
        
        # Student Mastery per concept (BKT)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mastery (
                session_id TEXT,
                concept_id TEXT,
                p_mastery REAL,
                updated_at REAL,
                PRIMARY KEY (session_id, concept_id)
            )
        """)
        
        # Stats counters (cache_hits, offline_used, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                stat_key TEXT PRIMARY KEY,
                stat_val INTEGER DEFAULT 0
            )
        """)
        
        # Initialize stats counters if not present
        cursor.execute("INSERT OR IGNORE INTO stats (stat_key, stat_val) VALUES ('cache_hits', 0)")
        cursor.execute("INSERT OR IGNORE INTO stats (stat_key, stat_val) VALUES ('offline_used', 0)")
        cursor.execute("INSERT OR IGNORE INTO stats (stat_key, stat_val) VALUES ('groq_calls', 0)")
        conn.commit()

def increment_stat(key: str, amount: int = 1) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE stats SET stat_val = stat_val + ? WHERE stat_key = ?",
            (amount, key)
        )
        conn.commit()

def get_stats() -> Dict[str, int]:
    with get_connection() as conn:
        rows = conn.execute("SELECT stat_key, stat_val FROM stats").fetchall()
        return {r["stat_key"]: r["stat_val"] for r in rows}

def get_cached_llm(cache_key: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT response_json FROM llm_cache WHERE cache_key = ?",
            (cache_key,)
        ).fetchone()
        if row:
            try:
                return json.loads(row["response_json"])
            except Exception:
                return None
    return None

def set_cached_llm(cache_key: str, prompt: str, response: Dict[str, Any]) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO llm_cache (cache_key, prompt, response_json, created_at) VALUES (?, ?, ?, ?)",
            (cache_key, prompt, json.dumps(response), time.time())
        )
        conn.commit()

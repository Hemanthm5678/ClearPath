import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.database import (
    get_connection,
    init_db,
)
from backend.app.signals import extract_features
from backend.app.confusion import detect_confusion
from backend.app.tracing import bkt
from backend.app.policy import (
    decide_intervention,
    get_concept_by_id,
    get_question_by_id,
    load_concepts,
    load_questions,
    record_policy_event,
    select_next_question,
)
from backend.app.llm.gateway import ask, get_health_status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clearpath.main")

# Initialize database schema
init_db()

app = FastAPI(
    title="ClearPath API",
    description="Confusion-aware adaptive tutor API for hackathon",
    version="1.0.0"
)

# CORS middleware for local Vite frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- In-memory session store --------------------

sessions: Dict[str, Dict] = {}

# -------------------- Pydantic Models --------------------


class SessionRequest(BaseModel):
    profile: Optional[str] = "live"


class SessionResponse(BaseModel):
    session_id: str
    concept: Dict[str, Any]
    question: Dict[str, Any]


class Features(BaseModel):
    idle_time: float = 0.0
    edit_count: float = 0.0
    retries: float = 0.0
    backspace_rate: float = 0.0
    focus_lost_count: float = 0.0
    dwell_time_ms: Optional[float] = None
    pause_duration_ms: Optional[float] = None
    option_switches: Optional[float] = None
    hint_count: Optional[float] = None
    lost_clicks: Optional[float] = None

    class Config:
        extra = "allow"


class EventRequest(BaseModel):
    session_id: str
    question_id: str
    type: str  # 'tick' | 'submit' | 'hint' | 'lost'
    features: Features = Field(default_factory=Features)
    answer: Optional[str] = None


class ConfusionModel(BaseModel):
    score: float
    state: str
    reasons: List[str]


class ActionWhy(BaseModel):
    signals: List[str] = []
    decision: str = ""
    prereq: Optional[str] = None


class ActionModel(BaseModel):
    type: str
    style: Optional[str] = "none"
    level: Optional[int] = 0
    why: Union[ActionWhy, Dict[str, Any], str] = Field(default_factory=ActionWhy)


class TutorModel(BaseModel):
    explanation: str
    check_question: str = ""
    visual_description: str = ""
    source: str = "offline_bank"


class EventResponse(BaseModel):
    confusion: ConfusionModel
    mastery: Dict[str, float]
    action: ActionModel
    tutor: Optional[TutorModel] = None


class QuestionResponse(BaseModel):
    question: Dict[str, Any]
    concept: str
    difficulty: str


class ExplainRequest(BaseModel):
    session_id: str
    style: Optional[str] = "visual"
    level: Optional[int] = 1
    question_id: Optional[str] = None


class ExplainResponse(BaseModel):
    explanation: str
    check_question: str = ""
    visual_description: str = ""
    source: str = "offline_bank"


class ChatRequest(BaseModel):
    session_id: str
    message: str
    question_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    source: str = "offline_bank"


class HeatmapCell(BaseModel):
    confusion: float
    why: str = ""
    state: Optional[str] = "focused"


class HeatmapResponse(BaseModel):
    students: List[Dict[str, Any]]
    concepts: List[Dict[str, Any]]
    cells: List[List[HeatmapCell]]


class HealthResponse(BaseModel):
    mode: str
    groq_ok: bool
    models: List[str]
    cache_hits: int
    offline_used: int


class SimulateRequest(BaseModel):
    persona: Optional[str] = "Alex"
    profile: Optional[str] = "confused"


class SimulateResponse(BaseModel):
    status: str = "ok"
    session_id: str
    student_name: str
    profile: str
    concept_id: str
    confusion_score: float
    confusion_state: str
    mastery: Dict[str, float]


# -------------------- Helper: LLM call with fallback --------------------


def _call_llm(prompt_name: str, context_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls the LLM gateway which handles Groq -> offline fallback.
    """
    return ask(prompt_name, context_dict)


# -------------------- Root Endpoint --------------------


@app.get("/")
def root():
    return {"app": "ClearPath", "status": "running"}


# -------------------- POST /api/session --------------------


@app.post("/api/session", response_model=SessionResponse)
def create_session(req: Optional[SessionRequest] = None):
    """Start a session."""
    profile = req.profile if req and req.profile else "live"
    session_id = f"s_{uuid.uuid4().hex[:10]}"

    concepts = load_concepts()
    questions = load_questions()

    if not concepts:
        concepts = [
            {"id": "c1_parts_of_a_whole", "name": "Parts of a Whole", "description": "Understanding fractions as parts of a single whole unit", "prerequisites": [], "order": 1},
            {"id": "c2_number_line", "name": "Fractions on a Number Line", "description": "Positioning fractions between whole numbers on a line", "prerequisites": ["c1_parts_of_a_whole"], "order": 2},
            {"id": "c3_fraction_as_division", "name": "Fraction as Division", "description": "Interpreting a/b as dividing a into b equal parts", "prerequisites": ["c1_parts_of_a_whole"], "order": 3},
        ]

    # Pick initial concept (default to fraction as division or first concept)
    initial_concept = concepts[2] if len(concepts) > 2 else concepts[0]
    concept_id = initial_concept["id"]

    # Filter questions for this concept
    concept_questions = [q for q in questions if q.get("concept_id") == concept_id]
    if not concept_questions:
        concept_questions = questions if questions else [{
            "id": "q_frac_div_1",
            "concept_id": concept_id,
            "difficulty": "medium",
            "prompt": "If 3 pizzas are shared equally among 4 friends, how much pizza does each friend get?",
            "type": "multiple_choice",
            "options": ["3/4 of a pizza", "4/3 of a pizza", "1/4 of a pizza", "1/3 of a pizza"],
            "correct_answer": "3/4 of a pizza",
            "hint": "Divide total items (3 pizzas) by total people (4 friends).",
            "step_by_step": "Step 1: Count pizzas (3). Step 2: Divide by people (4). Answer is 3/4."
        }]
    initial_question = concept_questions[0]

    initial_score = 0.75 if profile == "confused" else (0.45 if profile == "hesitant" else 0.05)
    initial_state = profile if profile in ("confused", "hesitant") else "calm"

    # Store session in memory
    sessions[session_id] = {
        "session_id": session_id,
        "profile": profile,
        "current_concept": concept_id,
        "current_concept_obj": initial_concept,
        "current_question": initial_question,
        "confusion_history": [{"score": initial_score, "state": initial_state, "reasons": []}],
    }

    # Also persist to database for heatmap / WebSocket reads
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions (session_id, profile, student_name, concept_id, question_id, confusion_score, confusion_state, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, profile, f"Student {session_id[-4:]}", concept_id, initial_question["id"], initial_score, initial_state, time.time()),
        )
        conn.commit()

    return SessionResponse(
        session_id=session_id,
        concept=initial_concept,
        question=initial_question,
    )


# -------------------- POST /api/events --------------------


@app.post("/api/events", response_model=EventResponse)
def ingest_event(req: EventRequest):
    """Send behaviour signals and answers."""
    # Validate session
    sess = sessions.get(req.session_id)
    if sess is None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT concept_id, question_id, profile FROM sessions WHERE session_id = ?",
                (req.session_id,),
            ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Session not found")
        concept_id = row["concept_id"] or "c3_fraction_as_division"
        question = get_question_by_id(row["question_id"]) or {}
        concept_obj = get_concept_by_id(concept_id) or {"id": concept_id, "name": "Fraction as Division"}
        sess = {
            "session_id": req.session_id,
            "profile": row["profile"] or "live",
            "current_concept": concept_id,
            "current_concept_obj": concept_obj,
            "current_question": question,
            "confusion_history": [],
        }
        sessions[req.session_id] = sess

    # 1. Prepare raw features dictionary (exclude None values)
    features_raw = req.features.model_dump(exclude_none=True) if hasattr(req.features, "model_dump") else {
        k: v for k, v in dict(req.features).items() if v is not None
    }
    
    # Map event types to signals
    if req.type == "hint":
        features_raw["hint_count"] = max(1.0, float(features_raw.get("hint_count") or 0.0) + 1.0)
    if req.type == "lost":
        features_raw["lost_clicks"] = max(1.0, float(features_raw.get("lost_clicks") or 0.0) + 1.0)

    # Normalize idle_time to latency_s and think_time_s
    idle_val = float(features_raw.get("idle_time") or 0.0)
    if "latency_s" not in features_raw and "dwell_time_ms" not in features_raw:
        features_raw["latency_s"] = idle_val
    if "think_time_s" not in features_raw and "pause_duration_ms" not in features_raw:
        features_raw["think_time_s"] = idle_val
    if "retry_count" not in features_raw and "retries" in features_raw:
        features_raw["retry_count"] = float(features_raw["retries"])

    feature_vec, reasons = extract_features(features_raw)

    if req.type == "lost" and "lost button tapped" not in reasons:
        reasons.insert(0, "lost button tapped")
    if req.type == "hint" and "hint tapped" not in reasons:
        reasons.insert(0, "hint tapped")

    # 2. Confusion detection (XGBoost + rule fallback)
    confusion = detect_confusion(feature_vec, reasons, session_id=req.session_id)
    if req.type == "lost":
        confusion["score"] = max(0.85, confusion["score"])
        confusion["state"] = "confused"

    # Store confusion in session history
    sess["confusion_history"].append({
        "score": confusion["score"],
        "state": confusion["state"],
        "reasons": confusion["reasons"],
        "timestamp": time.time(),
    })

    # 3. Retrieve concept & question context
    concept_id = sess["current_concept"]
    question = get_question_by_id(req.question_id) or sess.get("current_question", {})

    # 4. BKT mastery update on 'submit'
    if req.type == "submit" and req.answer is not None and question:
        correct_answer = str(question.get("correct_answer", "")).strip().lower()
        student_answer = str(req.answer).strip().lower()
        is_correct = (
            (correct_answer == student_answer)
            or (len(correct_answer) > 0 and correct_answer in student_answer)
            or (len(student_answer) > 0 and student_answer in correct_answer)
        ) if correct_answer else False
        bkt.record_attempt(req.session_id, concept_id, is_correct)
        record_policy_event(
            session_id=req.session_id,
            event_type="submit",
            is_correct=is_correct,
            confusion_score=confusion["score"],
            question_id=req.question_id,
            think_time_s=feature_vec[1],
            latency_s=feature_vec[0],
        )

    mastery_prob = bkt.get_mastery(req.session_id, concept_id)
    all_mastery = bkt.get_all_mastery(req.session_id)
    if not all_mastery:
        all_mastery = {concept_id: mastery_prob}

    # 5. Policy decision
    action_dict = decide_intervention(
        confusion=confusion,
        mastery_prob=mastery_prob,
        hint_tapped=(req.type == "hint"),
        concept_id=concept_id,
        session_id=req.session_id,
    )

    # Persist session state update to DB
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE sessions
            SET confusion_score = ?, confusion_state = ?, question_id = ?
            WHERE session_id = ?
            """,
            (confusion["score"], confusion["state"], req.question_id, req.session_id),
        )
        conn.execute(
            """
            INSERT INTO events (session_id, question_id, event_type, features_json, answer, confusion_score, confusion_state, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                req.session_id,
                req.question_id,
                req.type,
                json.dumps(features_raw),
                req.answer or "",
                confusion["score"],
                confusion["state"],
                time.time(),
            ),
        )
        conn.commit()

    # 6. Generate tutor response if re-explanation, hint, or lost required
    tutor_model: Optional[TutorModel] = None
    needs_tutor = action_dict.get("type") in ("re_explain", "hint", "break") or req.type in ("hint", "lost")
    
    if needs_tutor:
        concept_obj = get_concept_by_id(concept_id) or sess.get("current_concept_obj") or {"name": "Fraction as Division"}
        q_prompt = question.get("prompt", "") if question else "Explain this concept"
        
        style = action_dict.get("style", "visual")
        if style == "none" or not style:
            style = "simple_language" if req.type == "lost" else "visual"
        if style == "worked":
            style = "step_by_step"
            action_dict["style"] = "step_by_step"
        level = action_dict.get("level", 1) or 1

        tutor_data = _call_llm(
            "explain_concept",
            {
                "concept_name": concept_obj.get("name", "Fraction as Division"),
                "concept_id": concept_id,
                "question_id": req.question_id,
                "student_age": 10,
                "confusion_reasons": confusion["reasons"] or ["Student requested assistance"],
                "style": style,
                "level": level,
                "question_prompt": q_prompt,
            },
        )
        tutor_model = TutorModel(
            explanation=tutor_data.get("explanation", ""),
            check_question=tutor_data.get("check_question", ""),
            visual_description=tutor_data.get("visual_description", ""),
            source=tutor_data.get("source", "offline_bank"),
        )

    return EventResponse(
        confusion=ConfusionModel(
            score=confusion["score"],
            state=confusion["state"],
            reasons=confusion["reasons"],
        ),
        mastery=all_mastery,
        action=ActionModel(
            type=action_dict["type"],
            style=action_dict.get("style", "none"),
            level=action_dict.get("level", 0),
            why=action_dict.get("why", {}),
        ),
        tutor=tutor_model,
    )


# -------------------- GET /api/question/next --------------------


@app.get("/api/question/next", response_model=QuestionResponse)
def get_next_question(session_id: str = Query(...)):
    """Next question chosen by the policy."""
    sess = sessions.get(session_id)
    if sess is None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT concept_id, question_id FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Session not found")
        concept_id = row["concept_id"] or "c3_fraction_as_division"
        current_question_id = row["question_id"]
    else:
        concept_id = sess["current_concept"]
        current_question_id = sess["current_question"].get("id") if sess.get("current_question") else None

    next_choice = select_next_question(session_id, concept_id, current_question_id)

    # Update session in memory
    if sess is not None:
        sess["current_concept"] = next_choice["concept"]
        sess["current_question"] = next_choice["question"]
        concept_obj = get_concept_by_id(next_choice["concept"])
        if concept_obj:
            sess["current_concept_obj"] = concept_obj

    # Persist to DB
    with get_connection() as conn:
        conn.execute(
            "UPDATE sessions SET concept_id = ?, question_id = ? WHERE session_id = ?",
            (next_choice["concept"], next_choice["question"]["id"], session_id),
        )
        conn.commit()

    return QuestionResponse(
        question=next_choice["question"],
        concept=next_choice["concept"],
        difficulty=next_choice["difficulty"],
    )


# -------------------- POST /api/explain --------------------


@app.post("/api/explain", response_model=ExplainResponse)
def get_explanation(req: ExplainRequest):
    """Explain differently or in simple language."""
    sess = sessions.get(req.session_id)
    concept_id = "c3_fraction_as_division"
    question_id = req.question_id
    question_prompt = "Explain this concept"

    if sess is not None:
        concept_id = sess.get("current_concept") or concept_id
        if not question_id and sess.get("current_question"):
            question_id = sess["current_question"].get("id")
            question_prompt = sess["current_question"].get("prompt", question_prompt)
    else:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT concept_id, question_id FROM sessions WHERE session_id = ?",
                (req.session_id,),
            ).fetchone()
        if row is not None:
            concept_id = row["concept_id"] or concept_id
            if not question_id:
                question_id = row["question_id"]

    if question_id:
        q = get_question_by_id(question_id)
        if q:
            question_prompt = q.get("prompt", question_prompt)
            concept_id = q.get("concept_id", concept_id)

    concept_obj = get_concept_by_id(concept_id) or {"name": "Fraction as Division"}
    res = _call_llm(
        "explain_concept",
        {
            "concept_name": concept_obj.get("name", "Fraction as Division"),
            "concept_id": concept_id,
            "question_id": question_id,
            "student_age": 10,
            "confusion_reasons": ["User requested re-explanation"],
            "style": req.style or "visual",
            "level": req.level or 1,
            "question_prompt": question_prompt,
        },
    )

    return ExplainResponse(
        explanation=res.get("explanation", ""),
        check_question=res.get("check_question", ""),
        visual_description=res.get("visual_description", ""),
        source=res.get("source", "offline_bank"),
    )


# -------------------- POST /api/chat --------------------


@app.post("/api/chat", response_model=ChatResponse)
def student_chat(req: ChatRequest):
    """Student follow-up question."""
    sess = sessions.get(req.session_id)
    concept_id = "c3_fraction_as_division"
    question_id = req.question_id
    question_prompt = ""

    if sess is not None:
        concept_id = sess.get("current_concept") or concept_id
        if not question_id and sess.get("current_question"):
            question_id = sess["current_question"].get("id")
            question_prompt = sess["current_question"].get("prompt", "")
    else:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT concept_id, question_id FROM sessions WHERE session_id = ?",
                (req.session_id,),
            ).fetchone()
        if row is not None:
            concept_id = row["concept_id"] or concept_id
            if not question_id:
                question_id = row["question_id"]

    if question_id:
        q = get_question_by_id(question_id)
        if q:
            question_prompt = q.get("prompt", question_prompt)
            concept_id = q.get("concept_id", concept_id)

    concept_obj = get_concept_by_id(concept_id) or {"name": "Fraction as Division"}
    res = _call_llm(
        "chat_reply",
        {
            "chat_history": [],
            "concept": concept_obj.get("name", "Fraction as Division"),
            "concept_id": concept_id,
            "question_id": question_id,
            "question_prompt": question_prompt,
            "student_message": req.message,
        },
    )

    return ChatResponse(
        reply=res.get("reply", "Great thought! Keep exploring how the parts relate to the whole."),
        source=res.get("source", "offline_bank"),
    )


# -------------------- Persona Profiles for Dynamic Simulation --------------------

PERSONA_PROFILES = {
    "focused": {
        "name_prefix": "Maya (Steady)",
        "active_concept": "c4_equivalent_fractions",
        "question_id": "q6_equiv_1",
        "confusion_score": 0.08,
        "confusion_state": "calm",
        "mastery_map": {
            "c1_fraction_basics": 0.95,
            "c2_equal_parts": 0.92,
            "c3_fraction_as_division": 0.88,
            "c4_equivalent_fractions": 0.80,
            "c5_comparing_fractions": 0.68,
            "c6_adding_fractions": 0.52,
        },
    },
    "hesitant": {
        "name_prefix": "Jordan (Hesitant)",
        "active_concept": "c3_fraction_as_division",
        "question_id": "q3_division_1",
        "confusion_score": 0.48,
        "confusion_state": "hesitant",
        "mastery_map": {
            "c1_fraction_basics": 0.82,
            "c2_equal_parts": 0.70,
            "c3_fraction_as_division": 0.52,
            "c4_equivalent_fractions": 0.44,
            "c5_comparing_fractions": 0.36,
            "c6_adding_fractions": 0.28,
        },
    },
    "confused": {
        "name_prefix": "Alex (Stuck)",
        "active_concept": "c3_fraction_as_division",
        "question_id": "q3_division_1",
        "confusion_score": 0.88,
        "confusion_state": "confused",
        "mastery_map": {
            "c1_fraction_basics": 0.58,
            "c2_equal_parts": 0.36,
            "c3_fraction_as_division": 0.18,
            "c4_equivalent_fractions": 0.14,
            "c5_comparing_fractions": 0.12,
            "c6_adding_fractions": 0.10,
        },
    },
}


# -------------------- POST /api/simulate --------------------


@app.post("/api/simulate", response_model=SimulateResponse)
def simulate_student(req: SimulateRequest):
    """Simulates realistic telemetry and knowledge tracing across concepts for a student persona."""
    profile_key = (req.profile or "confused").lower()
    if "focus" in profile_key or "steady" in profile_key:
        p_key = "focused"
    elif "hesit" in profile_key:
        p_key = "hesitant"
    else:
        p_key = "confused"

    cfg = PERSONA_PROFILES.get(p_key, PERSONA_PROFILES["confused"])
    student_name = req.persona if req.persona and len(req.persona.strip()) > 0 else cfg["name_prefix"]
    session_id = f"sim_{p_key[:4]}_{uuid.uuid4().hex[:6]}"
    active_concept = cfg["active_concept"]
    question_id = cfg["question_id"]
    conf_score = cfg["confusion_score"]
    conf_state = cfg["confusion_state"]
    mastery_map = cfg["mastery_map"]

    # Write mastery records for all concepts
    for cid, m_val in mastery_map.items():
        bkt.set_mastery(session_id, cid, m_val)

    # Persist session to DB
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions (session_id, profile, student_name, concept_id, question_id, confusion_score, confusion_state, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, p_key, student_name, active_concept, question_id, conf_score, conf_state, time.time()),
        )
        features_sim = {
            "idle_time": 28.0 if p_key == "confused" else (14.0 if p_key == "hesitant" else 4.0),
            "edit_count": 4 if p_key == "confused" else (2 if p_key == "hesitant" else 0),
            "retries": 3 if p_key == "confused" else (1 if p_key == "hesitant" else 0),
        }
        conn.execute(
            """
            INSERT INTO events (session_id, question_id, event_type, features_json, answer, confusion_score, confusion_state, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, question_id, "submit", json.dumps(features_sim), "simulated answer", conf_score, conf_state, time.time()),
        )
        conn.commit()

    # Store in-memory session
    concept_obj = get_concept_by_id(active_concept) or {"id": active_concept, "name": "Fraction as Division"}
    question_obj = get_question_by_id(question_id) or {}
    sessions[session_id] = {
        "session_id": session_id,
        "profile": p_key,
        "student_name": student_name,
        "current_concept": active_concept,
        "current_concept_obj": concept_obj,
        "current_question": question_obj,
        "confusion_history": [{"score": conf_score, "state": conf_state, "reasons": []}],
    }

    return SimulateResponse(
        status="ok",
        session_id=session_id,
        student_name=student_name,
        profile=p_key,
        concept_id=active_concept,
        confusion_score=conf_score,
        confusion_state=conf_state,
        mastery=mastery_map,
    )


# -------------------- GET /api/class/heatmap --------------------


@app.get("/api/class/heatmap", response_model=HeatmapResponse)
def get_class_heatmap():
    """Teacher view data."""
    concepts = load_concepts()
    if not concepts:
        concepts = [
            {"id": "c1_fraction_basics", "name": "Fraction Basics", "order": 1},
            {"id": "c2_equal_parts", "name": "Equal Part Partitioning", "order": 2},
            {"id": "c3_fraction_as_division", "name": "Fraction as Division", "order": 3},
            {"id": "c4_equivalent_fractions", "name": "Equivalent Fractions", "order": 4},
            {"id": "c5_comparing_fractions", "name": "Comparing Fractions", "order": 5},
            {"id": "c6_adding_fractions", "name": "Adding Fractions", "order": 6},
        ]

    with get_connection() as conn:
        session_rows = conn.execute(
            """
            SELECT session_id, profile, student_name, concept_id, confusion_score, confusion_state
            FROM sessions
            ORDER BY created_at DESC
            LIMIT 15
            """
        ).fetchall()

    students: List[Dict[str, Any]] = []
    cells: List[List[HeatmapCell]] = []
    seen_ids = set()

    for s in session_rows:
        sid = s["session_id"]
        seen_ids.add(sid)
        s_name = s["student_name"] or f"Student {sid[:5]}"
        conf_score = float(s["confusion_score"] or 0.1)
        conf_state = s["confusion_state"] or "calm"
        s_profile = (s["profile"] or "live").lower()
        active_cid = s["concept_id"] or "c3_fraction_as_division"

        students.append({
            "id": sid,
            "name": s_name,
            "current_concept": active_cid,
            "score": conf_score,
            "state": conf_state,
        })

        # Find active concept order
        active_concept_obj = get_concept_by_id(active_cid)
        active_order = active_concept_obj.get("order", 3) if active_concept_obj else 3

        row_cells: List[HeatmapCell] = []
        for c in concepts:
            cid = c["id"]
            c_order = c.get("order", 1)

            # Check if explicit mastery exists in DB
            has_explicit = False
            p_mastery = 0.30
            with get_connection() as conn:
                m_row = conn.execute(
                    "SELECT p_mastery FROM mastery WHERE session_id = ? AND concept_id = ?",
                    (sid, cid)
                ).fetchone()
                if m_row is not None:
                    has_explicit = True
                    p_mastery = float(m_row["p_mastery"])

            if cid == active_cid:
                # Active concept uses live telemetry
                conf = conf_score
                st = conf_state
                why = f"Active problem: {st} (Mastery: {int(p_mastery * 100)}%)"
            elif has_explicit:
                # Concept with explicit student history
                if p_mastery >= 0.85:
                    conf = round(max(0.04, (1.0 - p_mastery) * 0.8), 2)
                elif p_mastery >= 0.60:
                    conf = round(0.15 + (0.85 - p_mastery) * 0.7, 2)
                elif p_mastery >= 0.35:
                    conf = round(0.35 + (0.60 - p_mastery) * 0.8, 2)
                else:
                    conf = round(min(0.95, 0.65 + (0.35 - p_mastery) * 0.9), 2)
                st = "confused" if conf >= 0.65 else ("hesitant" if conf >= 0.35 else "calm")
                why = f"Tested: {st} (Mastery: {int(p_mastery * 100)}%)"
            elif c_order < active_order:
                # Prerequisite concept completed earlier in curriculum
                if s_profile == "focused":
                    p_est = max(0.85, 0.95 - (active_order - c_order) * 0.02)
                    conf = round(max(0.04, 0.08 - (active_order - c_order) * 0.02), 2)
                elif s_profile == "hesitant":
                    p_est = max(0.65, 0.80 - (active_order - c_order) * 0.04)
                    conf = round(max(0.15, 0.25 - (active_order - c_order) * 0.04), 2)
                else:  # confused / struggling
                    p_est = max(0.40, 0.55 - (active_order - c_order) * 0.05)
                    conf = round(min(0.55, 0.45 + (active_order - c_order) * 0.03), 2)
                st = "confused" if conf >= 0.65 else ("hesitant" if conf >= 0.35 else "calm")
                why = f"Completed prerequisite (Mastery: {int(p_est * 100)}%)"
            else:
                # Upcoming concept ahead in curriculum
                if s_profile == "focused":
                    p_est = max(0.35, 0.65 - (c_order - active_order) * 0.10)
                    conf = round(min(0.30, 0.15 + (c_order - active_order) * 0.05), 2)
                elif s_profile == "hesitant":
                    p_est = max(0.20, 0.40 - (c_order - active_order) * 0.08)
                    conf = round(min(0.62, 0.45 + (c_order - active_order) * 0.06), 2)
                else:  # confused
                    p_est = max(0.08, 0.20 - (c_order - active_order) * 0.05)
                    conf = round(min(0.92, 0.75 + (c_order - active_order) * 0.06), 2)
                st = "confused" if conf >= 0.65 else ("hesitant" if conf >= 0.35 else "calm")
                why = f"Upcoming concept (Projected readiness: {int(p_est * 100)}%)"

            row_cells.append(HeatmapCell(confusion=conf, why=why, state=st))
        cells.append(row_cells)

    # In-memory sessions not yet in DB
    for sid, sess in sessions.items():
        if sid in seen_ids:
            continue
        seen_ids.add(sid)
        latest_conf = 0.1
        latest_st = "calm"
        if sess.get("confusion_history"):
            latest = sess["confusion_history"][-1]
            latest_conf = float(latest.get("score", 0.1))
            latest_st = str(latest.get("state", "calm"))

        students.append({
            "id": sid,
            "name": f"Student {sid[:5]}",
            "current_concept": sess.get("current_concept", ""),
            "score": latest_conf,
            "state": latest_st,
        })

        row_cells = []
        for c in concepts:
            cid = c["id"]
            p_mastery = bkt.get_mastery(sid, cid)
            if sess.get("current_concept") == cid:
                conf = latest_conf
                st = latest_st
                why = f"Active: {st} (Mastery: {int(p_mastery * 100)}%)"
            else:
                conf = round(max(0.05, 1.0 - p_mastery), 2)
                st = "confused" if conf > 0.65 else ("hesitant" if conf > 0.35 else "calm")
                why = f"Mastery: {int(p_mastery * 100)}%"
            row_cells.append(HeatmapCell(confusion=conf, why=why, state=st))
        cells.append(row_cells)

    return HeatmapResponse(
        students=students,
        concepts=concepts,
        cells=cells,
    )


# -------------------- GET /api/health --------------------


@app.get("/api/health", response_model=HealthResponse)
def health_check():
    """Status for the badge and rehearsal."""
    return HealthResponse(**get_health_status())


# -------------------- WebSocket /ws/{session_id} --------------------


@app.websocket("/ws/{session_id}")
async def websocket_meter(websocket: WebSocket, session_id: str):
    """Push confusion updates to the meter every 2 s."""
    await websocket.accept()
    logger.info(f"WebSocket client connected for session: {session_id}")
    try:
        while True:
            score = 0.05
            state = "calm"

            # Check in-memory session
            sess = sessions.get(session_id)
            if sess and sess.get("confusion_history"):
                latest = sess["confusion_history"][-1]
                score = float(latest.get("score", 0.05))
                state = str(latest.get("state", "calm"))
            else:
                # Check DB
                with get_connection() as conn:
                    row = conn.execute(
                        "SELECT confusion_score, confusion_state FROM sessions WHERE session_id = ?",
                        (session_id,),
                    ).fetchone()
                    if row:
                        score = float(row["confusion_score"] or 0.05)
                        state = str(row["confusion_state"] or "calm")

            await websocket.send_json({
                "score": round(score, 2),
                "state": state,
            })
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for session: {session_id}")
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")

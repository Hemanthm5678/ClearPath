import asyncio
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.app.telemetry_engine import (
    calculate_normalized_time_ratio,
    classify_cognitive_state,
    evaluate_intervention_efficacy,
    update_student_pace,
)
from backend.app.config import settings
from backend.app.database import (
    get_connection,
    init_db,
    create_user,
    get_user_by_email,
    get_user_by_id,
    verify_password,
    get_all_users,
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
from backend.app.llm.gateway import (
    ask,
    get_health_status,
    analyze_question_with_ai_tutor,
    update_offline_bank,
)

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
    student_name: Optional[str] = "Alex Chen"
    user_id: Optional[str] = None


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "student"


class LoginRequest(BaseModel):
    email: str
    password: str
    role: Optional[str] = None


class AuthResponse(BaseModel):
    status: str
    user: Dict[str, Any]
    token: str
    message: Optional[str] = None


class CreateQuestionRequest(BaseModel):
    concept_id: str
    prompt: str
    options: List[str]
    correct_answer: str
    difficulty: Optional[str] = "auto"



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
    cooldown_seconds: Optional[int] = 0


class TutorModel(BaseModel):
    explanation: str
    check_question: str = ""
    visual_description: str = ""
    source: str = "offline_bank"


class InterventionEfficacyModel(BaseModel):
    status: str = "MONITORING"
    delta_time_ratio: float = 0.0
    delta_accuracy: float = 0.0
    summary_text: str = ""


class TelemetryMetricsModel(BaseModel):
    actual_time_sec: float = 0.0
    expected_time_sec: float = 30.0
    complexity_weight: float = 1.0
    student_pace_factor: float = 1.0
    normalized_time_ratio: float = 1.0
    cognitive_state: str = "FOCUSED"
    cooldown_seconds: int = 0


class EventResponse(BaseModel):
    confusion: ConfusionModel
    mastery: Dict[str, float]
    action: ActionModel
    tutor: Optional[TutorModel] = None
    telemetry: Optional[TelemetryMetricsModel] = None
    intervention_efficacy: Optional[InterventionEfficacyModel] = None


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
    cognitive_state: Optional[str] = "FOCUSED"
    breakdown: Optional[str] = ""
    efficacy: Optional[Dict[str, Any]] = None


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
    question: Optional[Dict[str, Any]] = None


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


# -------------------- Auth & RBAC Endpoints --------------------


@app.post("/api/auth/signup", response_model=AuthResponse)
def signup(req: SignupRequest):
    if not req.email or not req.password or not req.name:
        raise HTTPException(status_code=400, detail="Name, email, and password are required")
    existing = get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    user = create_user(name=req.name, email=req.email, password=req.password, role=req.role or "student")
    token = f"cp_token_{user['id']}_{uuid.uuid4().hex[:12]}"
    return AuthResponse(status="ok", user=user, token=token, message=f"Welcome {user['name']}!")


@app.post("/api/auth/login", response_model=AuthResponse)
def login(req: LoginRequest):
    user = get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    safe_user = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "created_at": user["created_at"],
    }
    token = f"cp_token_{user['id']}_{uuid.uuid4().hex[:12]}"
    return AuthResponse(status="ok", user=safe_user, token=token, message="Login successful")


@app.get("/api/auth/demo-users")
def get_demo_users_endpoint():
    return {
        "students": [
            {
                "id": "u_student_alex",
                "name": "Alex Chen",
                "email": "alex@clearpath.edu",
                "role": "student",
                "password": "clearpath",
                "description": "Steady Cadet • Coding & Quadratic Algebra Explorer",
            },
            {
                "id": "u_student_maya",
                "name": "Maya Lin",
                "email": "maya@clearpath.edu",
                "role": "student",
                "password": "clearpath",
                "description": "High Velocity • Fast Cadence Solver",
            },
        ],
        "teachers": [
            {
                "id": "u_teacher_reed",
                "name": "Dr. Evelyn Reed",
                "email": "teacher@clearpath.edu",
                "role": "teacher",
                "password": "clearpath",
                "description": "Lead STEM Educator • Real-Time Matrix Diagnostic Specialist",
            }
        ],
    }


# -------------------- Teacher Question Authoring & AI Tutor Scaffolding --------------------


def _save_new_question_and_explanations(question_dict: Dict[str, Any], explanations_dict: Dict[str, Any]) -> None:
    qid = question_dict["id"]

    # 1. Update questions.json in both candidate directories
    q_paths = [
        settings.QUESTIONS_FILE,
        settings.ROOT_DIR / "data" / "questions.json",
        Path("data/questions.json"),
        Path("backend/data/questions.json"),
    ]
    saved_q = False
    for p in q_paths:
        try:
            if p.exists() and p.stat().st_size > 0:
                with open(p, "r", encoding="utf-8") as f:
                    curr_q = json.load(f)
                curr_q = [q for q in curr_q if q.get("id") != qid]
                curr_q.append(question_dict)
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(curr_q, f, indent=2, ensure_ascii=False)
                saved_q = True
        except Exception as e:
            logger.error(f"Error saving question to {p}: {e}")

    # 2. Update explanations.json in both candidate directories
    e_paths = [
        settings.EXPLANATIONS_FILE,
        settings.ROOT_DIR / "data" / "explanations.json",
        Path("data/explanations.json"),
        Path("backend/data/explanations.json"),
    ]
    for p in e_paths:
        try:
            if p.exists() and p.stat().st_size > 0:
                with open(p, "r", encoding="utf-8") as f:
                    curr_e = json.load(f)
                curr_e[qid] = {
                    "concept_id": question_dict.get("concept_id"),
                    "visual": {"level_1": explanations_dict.get("visual", {})},
                    "analogy": {"level_1": explanations_dict.get("analogy", {})},
                    "step_by_step": {"level_1": explanations_dict.get("step_by_step", {})},
                    "simple_language": {"level_1": explanations_dict.get("simple_language", {})},
                }
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(curr_e, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving explanations to {p}: {e}")

    # 3. Update in-memory offline bank
    update_offline_bank(qid, {
        "concept_id": question_dict.get("concept_id"),
        "visual": {"level_1": explanations_dict.get("visual", {})},
        "analogy": {"level_1": explanations_dict.get("analogy", {})},
        "step_by_step": {"level_1": explanations_dict.get("step_by_step", {})},
        "simple_language": {"level_1": explanations_dict.get("simple_language", {})},
    })


@app.post("/api/teacher/questions")
def teacher_create_question(req: CreateQuestionRequest):
    """
    Teacher authoring endpoint:
    Teacher enters question prompt + options + correct answer.
    AI Tutor auto-analyzes difficulty, timing, hint, and synthesizes all 4 multimodal scaffolding explanations.
    Immediately saves to quiz bank and makes available to students!
    """
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Question prompt is required")
    if not req.options or len(req.options) < 2:
        raise HTTPException(status_code=400, detail="At least 2 options are required")
    if not req.correct_answer or not req.correct_answer.strip():
        raise HTTPException(status_code=400, detail="Correct answer is required")

    concept = get_concept_by_id(req.concept_id)
    concept_name = concept["name"] if concept else req.concept_id

    # AI Tutor auto-analysis and multimodal scaffolding synthesis
    analysis = analyze_question_with_ai_tutor(
        prompt=req.prompt,
        options=req.options,
        correct_answer=req.correct_answer,
        concept_id=req.concept_id,
        concept_name=concept_name,
        user_difficulty=req.difficulty,
    )

    clean_prefix = req.concept_id.replace("c1_", "").replace("c2_", "").replace("c3_", "").replace("c4_", "").replace("c5_", "").replace("c6_", "").replace("c7_", "").replace("c8_", "")[:10]
    question_id = f"q_{clean_prefix}_{uuid.uuid4().hex[:6]}"

    new_question = {
        "id": question_id,
        "concept_id": req.concept_id,
        "domain": "coding" if "python" in req.concept_id else "math",
        "difficulty": analysis["complexity_tier"].lower(),
        "complexity_tier": analysis["complexity_tier"],
        "expected_time_sec": analysis["expected_time_sec"],
        "complexity_weight": analysis["complexity_weight"],
        "prompt": req.prompt.strip(),
        "type": "multiple_choice",
        "options": [opt.strip() for opt in req.options],
        "correct_answer": req.correct_answer.strip(),
        "hint": analysis["hint"],
        "step_by_step": analysis["step_by_step"],
        "created_by": "teacher",
        "created_at": time.time(),
    }

    _save_new_question_and_explanations(new_question, analysis["explanations"])

    return {
        "status": "ok",
        "question": new_question,
        "analysis": analysis,
        "message": f"Successfully created question for '{concept_name}'! AI Tutor has synthesized 4 multimodal scaffolds.",
    }


@app.get("/api/teacher/questions")
def teacher_list_questions():
    """Returns question bank and concept inventory for teacher management."""
    questions = load_questions()
    concepts = load_concepts()
    return {
        "total": len(questions),
        "concepts": concepts,
        "questions": questions,
    }


# -------------------- POST /api/session --------------------


@app.post("/api/session", response_model=SessionResponse)
def create_session(req: Optional[SessionRequest] = None):
    """Start a session."""
    profile = req.profile if req and req.profile else "live"
    student_name = (req.student_name.strip() if req and req.student_name and req.student_name.strip() else "Alex Chen")
    user_id = req.user_id if req and req.user_id else None
    session_id = f"s_{uuid.uuid4().hex[:10]}"

    concepts = load_concepts()
    questions = load_questions()

    if not concepts:
        concepts = [
            {"id": "c1_parts_of_a_whole", "name": "Parts of a Whole", "description": "Understanding fractions as parts of a single whole unit", "prerequisites": [], "order": 1},
            {"id": "c2_number_line", "name": "Fractions on a Number Line", "description": "Positioning fractions between whole numbers on a line", "prerequisites": ["c1_parts_of_a_whole"], "order": 2},
            {"id": "c3_fraction_as_division", "name": "Fraction as Division", "description": "Interpreting a/b as dividing a into b equal parts", "prerequisites": ["c1_parts_of_a_whole"], "order": 3},
        ]

    # Pick initial question (start with Question 1 at Index 0)
    initial_question = questions[0] if questions else {
        "id": "q_quad_roots_top",
        "concept_id": "c8_quadratic_algebra",
        "difficulty": "medium",
        "complexity_tier": "Medium",
        "expected_time_sec": 50,
        "complexity_weight": 1.8,
        "prompt": "Solve for the real roots of the quadratic equation: 2x² - 9x + 4 = 0. What are the values of x?",
        "type": "multiple_choice",
        "options": ["x = 4, x = 1/2", "x = -4, x = -1/2", "x = 2, x = 1", "x = 9/2, x = 2"],
        "correct_answer": "x = 4, x = 1/2",
        "hint": "Look at the coefficients: a = 2, b = -9, c = 4. Can you think of two numbers that multiply to +8 (a × c) and add up to -9 (b)? Once you find them, try splitting -9x into two terms!",
        "step_by_step": "To solve 2x² - 9x + 4 = 0 by factoring: multiply a × c = 2 × 4 = 8. Find two numbers that multiply to 8 and add to -9: those are -8 and -1. Split the middle term: 2x² - 8x - x + 4 = 0 → 2x(x - 4) - 1(x - 4) = 0 → (2x - 1)(x - 4) = 0. Setting each factor to 0 gives x = 4 and x = 1/2."
    }
    concept_id = initial_question.get("concept_id", "c8_quadratic_algebra")
    initial_concept = get_concept_by_id(concept_id) or (concepts[0] if concepts else {"id": concept_id, "name": "Quadratics & Deep Algebra"})

    initial_score = 0.75 if profile == "confused" else (0.45 if profile == "hesitant" else 0.05)
    initial_state = profile if profile in ("confused", "hesitant") else "calm"
    initial_cog_state = (
        "CONFUSED" if profile == "confused"
        else ("BORED" if profile == "bored"
        else ("GAMING" if profile == "gaming"
        else ("NATURALLY_SLOW" if profile == "naturally_slow"
        else "FOCUSED")))
    )
    initial_pace = 1.4 if profile == "naturally_slow" else 1.0

    # Store session in memory
    sessions[session_id] = {
        "session_id": session_id,
        "profile": profile,
        "student_name": student_name,
        "user_id": user_id,
        "current_concept": concept_id,
        "current_concept_obj": initial_concept,
        "current_question": initial_question,
        "confusion_history": [{"score": initial_score, "state": initial_state, "reasons": []}],
        "student_pace_factor": initial_pace,
        "cognitive_state": initial_cog_state,
        "hint_timestamps": [],
        "active_intervention": None,
        "last_efficacy": None,
        "last_breakdown": f"Actual: 0s | Expected: {initial_question.get('expected_time_sec', 30)}s | Baseline: {initial_pace:.1f}x",
    }

    # Also persist to database for heatmap / WebSocket reads
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions (session_id, profile, student_name, concept_id, question_id, confusion_score, confusion_state, student_pace_factor, cognitive_state, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, profile, student_name, concept_id, initial_question["id"], initial_score, initial_state, initial_pace, initial_cog_state, time.time()),
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
                "SELECT concept_id, question_id, profile, student_pace_factor, cognitive_state FROM sessions WHERE session_id = ?",
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
            "student_pace_factor": float(row["student_pace_factor"] or 1.0),
            "cognitive_state": str(row["cognitive_state"] or "FOCUSED"),
            "hint_timestamps": [],
            "active_intervention": None,
            "last_efficacy": None,
            "last_breakdown": "",
        }
        sessions[req.session_id] = sess

    # 1. Prepare raw features dictionary (exclude None values)
    features_raw = req.features.model_dump(exclude_none=True) if hasattr(req.features, "model_dump") else {
        k: v for k, v in dict(req.features).items() if v is not None
    }
    
    # Track hint timestamps in session
    hint_timestamps = sess.setdefault("hint_timestamps", [])
    if req.type == "hint":
        hint_timestamps.append(time.time())
        features_raw["hint_count"] = max(1.0, float(features_raw.get("hint_count") or 0.0) + 1.0)
    if req.type == "lost":
        features_raw["lost_clicks"] = max(1.0, float(features_raw.get("lost_clicks") or 0.0) + 1.0)

    # Normalize idle_time and dwell time to actual_time_sec
    idle_val = float(features_raw.get("idle_time") or 0.0)
    dwell_ms = float(features_raw.get("dwell_time_ms") or 0.0)
    actual_time_sec = max(idle_val, dwell_ms / 1000.0)
    if actual_time_sec <= 0.0:
        actual_time_sec = float(features_raw.get("latency_s") or 1.0)

    if "latency_s" not in features_raw and "dwell_time_ms" not in features_raw:
        features_raw["latency_s"] = actual_time_sec
    if "think_time_s" not in features_raw and "pause_duration_ms" not in features_raw:
        features_raw["think_time_s"] = actual_time_sec
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
    expected_time_sec = float(question.get("expected_time_sec", 30.0))
    complexity_weight = float(question.get("complexity_weight", 1.0))
    student_pace_factor = float(sess.get("student_pace_factor", 1.0))

    # 4. Check answer correctness on submit & update BKT
    is_correct = None
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

    # 5. Update rolling student pace factor via EMA on correct answers
    if req.type == "submit" and is_correct is True:
        student_pace_factor = update_student_pace(student_pace_factor, actual_time_sec, expected_time_sec)
        sess["student_pace_factor"] = student_pace_factor

    # Compute normalized time ratio
    norm_ratio = calculate_normalized_time_ratio(actual_time_sec, expected_time_sec, student_pace_factor)

    # 6. Classify Cognitive State (Hint 1 & Hint 2)
    option_switches = int(features_raw.get("option_switches") or features_raw.get("edit_count") or 0)
    hesitation_pauses = int(features_raw.get("lost_clicks") or 0) + (1 if actual_time_sec > 15.0 else 0)

    cog_state, cog_score, cog_reasons, breakdown_text = classify_cognitive_state(
        actual_time_sec=actual_time_sec,
        expected_time_sec=expected_time_sec,
        complexity_weight=complexity_weight,
        student_pace_factor=student_pace_factor,
        is_correct=is_correct,
        option_switches=option_switches,
        hesitation_pauses=hesitation_pauses,
        hint_timestamps=hint_timestamps,
        event_type=req.type,
    )
    sess["cognitive_state"] = cog_state
    sess["last_breakdown"] = breakdown_text

    # 7. Evaluate Closed-Loop Intervention Efficacy (Hint 3)
    active_intervention = sess.get("active_intervention")
    efficacy_result = evaluate_intervention_efficacy(
        active_intervention=active_intervention,
        current_state=cog_state,
        normalized_time_ratio=norm_ratio,
        is_correct=is_correct,
    )
    sess["last_efficacy"] = efficacy_result

    # If state requires intervention, initiate tracking
    if cog_state in ("CONFUSED", "BORED", "GAMING"):
        sess["active_intervention"] = {
            "id": f"int_{uuid.uuid4().hex[:6]}",
            "state_before": cog_state,
            "timestamp": time.time(),
            "question_id": req.question_id,
            "time_ratio_before": norm_ratio,
        }
    elif efficacy_result.get("status") == "HELPED":
        sess["active_intervention"] = None

    mastery_prob = bkt.get_mastery(req.session_id, concept_id)
    all_mastery = bkt.get_all_mastery(req.session_id)
    if not all_mastery:
        all_mastery = {concept_id: mastery_prob}

    # 8. Base Policy decision
    action_dict = decide_intervention(
        confusion=confusion,
        mastery_prob=mastery_prob,
        hint_tapped=(req.type == "hint"),
        concept_id=concept_id,
        session_id=req.session_id,
    )

    cooldown_seconds = 0
    tutor_model: Optional[TutorModel] = None

    # State-specific interventions (Hint 2 & Hint 3)
    if cog_state == "GAMING":
        cooldown_seconds = 10
        action_dict = {
            "type": "gaming_cooldown",
            "style": "none",
            "level": 0,
            "why": {
                "signals": ["rapid hint clicks > 2 in 6s", "gaming heuristic detected"],
                "decision": "Cooldown active: Read the code/equation step carefully before requesting the next hint",
            },
        }
        tutor_model = TutorModel(
            explanation="⚠️ Hint Cooldown Active (10s): Rapid hint clicking detected. Take a moment to trace through the code lines or equation terms carefully before requesting another hint.",
            check_question="Self-Check: What is the initial state or value of the variables before this execution step?",
            visual_description="Trace through the execution on scratch paper before tapping hint again.",
            source="telemetry_guard",
        )
    elif cog_state == "BORED":
        action_dict = {
            "type": "challenge_booster",
            "style": "none",
            "level": 0,
            "why": {
                "signals": [f"rapid answer ({actual_time_sec:.1f}s vs expected {expected_time_sec:.0f}s)", "low option switches"],
                "decision": "Under-engaged pacing: Triggering Rapid Challenge / Streak Booster",
            },
        }
        tutor_model = TutorModel(
            explanation="⚡ Rapid Challenge / Streak Booster! You answered in under 28% of expected time. Can you verify your answer by testing a quick edge case or boundary value?",
            check_question="Streak Check: What edge case or negative input could break this assumption?",
            visual_description="Sprint challenge active — double-check before locking in your answer!",
            source="telemetry_guard",
        )
    elif cog_state == "NATURALLY_SLOW":
        action_dict = {
            "type": "none",
            "style": "none",
            "level": 0,
            "why": {
                "signals": [f"actual time {actual_time_sec:.0f}s fits personal baseline ({student_pace_factor:.1f}x)"],
                "decision": "Status: Deliberate Thinker - Allowing uninterrupted processing time",
            },
        }
        if req.type not in ("hint", "lost"):
            tutor_model = None

    # Persist session state update to DB
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE sessions
            SET confusion_score = ?, confusion_state = ?, question_id = ?, student_pace_factor = ?, cognitive_state = ?
            WHERE session_id = ?
            """,
            (confusion["score"], confusion["state"], req.question_id, student_pace_factor, cog_state, req.session_id),
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

    # 9. Generate tutor response if re-explanation, hint, or lost required
    needs_tutor = (
        tutor_model is None
        and (
            action_dict.get("type") in ("re_explain", "hint", "break")
            or req.type in ("hint", "lost")
            or cog_state == "CONFUSED"
        )
        and cog_state not in ("GAMING", "BORED", "NATURALLY_SLOW")
    )
    
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
            cooldown_seconds=cooldown_seconds,
        ),
        tutor=tutor_model,
        telemetry=TelemetryMetricsModel(
            actual_time_sec=round(actual_time_sec, 1),
            expected_time_sec=round(expected_time_sec, 1),
            complexity_weight=complexity_weight,
            student_pace_factor=student_pace_factor,
            normalized_time_ratio=norm_ratio,
            cognitive_state=cog_state,
            cooldown_seconds=cooldown_seconds,
        ),
        intervention_efficacy=InterventionEfficacyModel(
            status=efficacy_result.get("status", "MONITORING"),
            delta_time_ratio=efficacy_result.get("delta_time_ratio", 0.0),
            delta_accuracy=efficacy_result.get("delta_accuracy", 0.0),
            summary_text=efficacy_result.get("summary_text", ""),
        ),
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
    "confused": {
        "name_prefix": "Alex (Confused / Stuck)",
        "active_concept": "c8_quadratic_algebra",
        "question_id": "q_quad_roots_top",
        "confusion_score": 0.88,
        "confusion_state": "confused",
        "cognitive_state": "CONFUSED",
        "student_pace_factor": 1.0,
        "actual_time": 82.0,
        "expected_time": 50.0,
        "mastery_map": {
            "c1_fraction_basics": 0.65,
            "c2_equal_parts": 0.50,
            "c3_fraction_as_division": 0.35,
            "c4_equivalent_fractions": 0.25,
            "c5_comparing_fractions": 0.20,
            "c6_adding_fractions": 0.15,
            "c7_python_tracing": 0.12,
            "c8_quadratic_algebra": 0.10,
        },
        "breakdown": "Actual: 82s | Expected: 50s (Quadratic Roots) | Baseline: 1.0x | Ratio: 1.64x (High Hesitation)",
        "efficacy": {
            "status": "UNRESOLVED",
            "state_before": "CONFUSED",
            "state_after": "CONFUSED",
            "delta_time_ratio": 0.52,
            "delta_accuracy": -0.5,
            "summary_text": "⚠️ Unresolved: Student struggling with quadratic factoring -> Step-by-step Socratic scaffolding dispatched.",
        },
    },
    "bored": {
        "name_prefix": "Taylor (Bored / Guessing)",
        "active_concept": "c7_python_tracing",
        "question_id": "q_code_mutable_top",
        "confusion_score": 0.46,
        "confusion_state": "hesitant",
        "cognitive_state": "BORED",
        "student_pace_factor": 1.0,
        "actual_time": 5.0,
        "expected_time": 45.0,
        "mastery_map": {
            "c1_fraction_basics": 0.70,
            "c2_equal_parts": 0.65,
            "c3_fraction_as_division": 0.60,
            "c4_equivalent_fractions": 0.55,
            "c5_comparing_fractions": 0.50,
            "c6_adding_fractions": 0.45,
            "c7_python_tracing": 0.30,
            "c8_quadratic_algebra": 0.35,
        },
        "breakdown": "Actual: 5s | Expected: 45s (Python Mutability) | Baseline: 1.0x | Ratio: 0.11x (Hasty Guessing)",
        "efficacy": {
            "status": "MONITORING",
            "state_before": "BORED",
            "state_after": "BORED",
            "delta_time_ratio": -0.80,
            "delta_accuracy": 0.0,
            "summary_text": "⚡ Rapid Challenge Dispatched: Encouraging precision and edge-case verification.",
        },
    },
    "gaming": {
        "name_prefix": "Casey (Hint Gaming)",
        "active_concept": "c8_quadratic_algebra",
        "question_id": "q_quad_param_top",
        "confusion_score": 0.72,
        "confusion_state": "confused",
        "cognitive_state": "GAMING",
        "student_pace_factor": 1.0,
        "actual_time": 2.5,
        "expected_time": 60.0,
        "mastery_map": {
            "c1_fraction_basics": 0.75,
            "c2_equal_parts": 0.60,
            "c3_fraction_as_division": 0.50,
            "c4_equivalent_fractions": 0.45,
            "c5_comparing_fractions": 0.40,
            "c6_adding_fractions": 0.30,
            "c7_python_tracing": 0.35,
            "c8_quadratic_algebra": 0.20,
        },
        "breakdown": "Actual: 2.5s | Expected: 60s (Hard Math) | Hints: 3 rapid in 4s | 10s Cooldown Active",
        "efficacy": {
            "status": "MONITORING",
            "state_before": "GAMING",
            "state_after": "GAMING",
            "delta_time_ratio": -0.90,
            "delta_accuracy": 0.0,
            "summary_text": "🔒 10s Hint Cooldown Enforced: Prompting self-check sub-question before next hint.",
        },
    },
    "naturally_slow": {
        "name_prefix": "Sam (Naturally Slow)",
        "active_concept": "c8_quadratic_algebra",
        "question_id": "q_quad_roots_top",
        "confusion_score": 0.18,
        "confusion_state": "calm",
        "cognitive_state": "NATURALLY_SLOW",
        "student_pace_factor": 1.4,
        "actual_time": 68.0,
        "expected_time": 50.0,
        "mastery_map": {
            "c1_fraction_basics": 0.90,
            "c2_equal_parts": 0.88,
            "c3_fraction_as_division": 0.82,
            "c4_equivalent_fractions": 0.78,
            "c5_comparing_fractions": 0.75,
            "c6_adding_fractions": 0.70,
            "c7_python_tracing": 0.65,
            "c8_quadratic_algebra": 0.72,
        },
        "breakdown": "Actual: 68s | Expected: 50s (Quad Roots) | Baseline: 1.4x | Ratio: 0.97x (Deliberate Thinker)",
        "efficacy": {
            "status": "HELPED",
            "state_before": "NATURALLY_SLOW",
            "state_after": "NATURALLY_SLOW",
            "delta_time_ratio": -0.15,
            "delta_accuracy": 1.0,
            "summary_text": "✅ Verified Autonomous: Deep deliberation aligns with personal baseline. Popups suppressed.",
        },
    },
    "focused": {
        "name_prefix": "Maya (Steady Cadence)",
        "active_concept": "c7_python_tracing",
        "question_id": "q_code_recursion_top",
        "confusion_score": 0.08,
        "confusion_state": "calm",
        "cognitive_state": "FOCUSED",
        "student_pace_factor": 1.0,
        "actual_time": 25.0,
        "expected_time": 55.0,
        "mastery_map": {
            "c1_fraction_basics": 0.98,
            "c2_equal_parts": 0.95,
            "c3_fraction_as_division": 0.92,
            "c4_equivalent_fractions": 0.88,
            "c5_comparing_fractions": 0.85,
            "c6_adding_fractions": 0.82,
            "c7_python_tracing": 0.86,
            "c8_quadratic_algebra": 0.80,
        },
        "breakdown": "Actual: 25s | Expected: 55s (Recursion) | Baseline: 1.0x | Ratio: 0.45x (Optimal Cadence)",
        "efficacy": {
            "status": "HELPED",
            "state_before": "FOCUSED",
            "state_after": "FOCUSED",
            "delta_time_ratio": 0.0,
            "delta_accuracy": 1.0,
            "summary_text": "✅ Verified Helped: Fast & accurate progression, high cognitive retention.",
        },
    },
}


# -------------------- POST /api/simulate --------------------


@app.post("/api/simulate", response_model=SimulateResponse)
def simulate_student(req: SimulateRequest):
    """Simulates realistic telemetry and knowledge tracing across concepts for a student persona."""
    profile_raw = (req.profile or "confused").lower()
    if "game" in profile_raw or "gaming" in profile_raw:
        p_key = "gaming"
    elif "bore" in profile_raw or "guess" in profile_raw:
        p_key = "bored"
    elif "slow" in profile_raw or "deliberate" in profile_raw:
        p_key = "naturally_slow"
    elif "focus" in profile_raw or "steady" in profile_raw:
        p_key = "focused"
    elif "hesit" in profile_raw:
        p_key = "bored"
    else:
        p_key = "confused"

    cfg = PERSONA_PROFILES.get(p_key, PERSONA_PROFILES["confused"])
    student_name = req.persona if req.persona and len(req.persona.strip()) > 0 else cfg["name_prefix"]
    session_id = f"sim_{p_key[:4]}_{uuid.uuid4().hex[:6]}"
    active_concept = cfg["active_concept"]
    question_id = cfg["question_id"]
    conf_score = cfg["confusion_score"]
    conf_state = cfg["confusion_state"]
    cog_state = cfg.get("cognitive_state", "FOCUSED")
    pace_factor = cfg.get("student_pace_factor", 1.0)
    mastery_map = cfg["mastery_map"]

    # Write mastery records for all concepts
    for cid, m_val in mastery_map.items():
        bkt.set_mastery(session_id, cid, m_val)

    # Persist session to DB
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions (session_id, profile, student_name, concept_id, question_id, confusion_score, confusion_state, student_pace_factor, cognitive_state, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, p_key, student_name, active_concept, question_id, conf_score, conf_state, pace_factor, cog_state, time.time()),
        )
        features_sim = {
            "idle_time": cfg.get("actual_time", 25.0),
            "edit_count": 4 if p_key == "confused" else (0 if p_key == "bored" else 2),
            "retries": 3 if p_key == "confused" else 0,
            "hint_count": 3 if p_key == "gaming" else 0,
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
    concept_obj = get_concept_by_id(active_concept) or {"id": active_concept, "name": "Python Output Tracing"}
    question_obj = get_question_by_id(question_id) or {}
    sessions[session_id] = {
        "session_id": session_id,
        "profile": p_key,
        "student_name": student_name,
        "current_concept": active_concept,
        "current_concept_obj": concept_obj,
        "current_question": question_obj,
        "confusion_history": [{"score": conf_score, "state": conf_state, "reasons": []}],
        "student_pace_factor": pace_factor,
        "cognitive_state": cog_state,
        "last_breakdown": cfg.get("breakdown", ""),
        "last_efficacy": cfg.get("efficacy", None),
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
        question=question_obj,
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
            {"id": "c7_python_tracing", "name": "Python Output Tracing", "order": 7},
            {"id": "c8_quadratic_algebra", "name": "Quadratic Algebra", "order": 8},
        ]

    with get_connection() as conn:
        session_rows = conn.execute(
            """
            SELECT session_id, profile, student_name, concept_id, confusion_score, confusion_state, student_pace_factor, cognitive_state
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
        cog_state = s["cognitive_state"] or "FOCUSED"
        s_profile = (s["profile"] or "live").lower()
        active_cid = s["concept_id"] or "c7_python_tracing"
        pace = float(s["student_pace_factor"] or 1.0)

        # Retrieve cached session metadata if available
        sess_mem = sessions.get(sid, {})
        profile_cfg = PERSONA_PROFILES.get(s_profile, PERSONA_PROFILES.get(cog_state.lower(), {}))
        s_breakdown = sess_mem.get("last_breakdown") or profile_cfg.get("breakdown") or f"Actual telemetry | Baseline: {pace:.1f}x"
        s_efficacy = sess_mem.get("last_efficacy") or profile_cfg.get("efficacy") or {
            "status": "MONITORING",
            "summary_text": "Live telemetry monitoring active.",
        }

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
                # Active concept uses live telemetry & state
                conf = conf_score
                st = conf_state
                cell_cog = cog_state
                cell_breakdown = s_breakdown
                cell_efficacy = s_efficacy
                why = f"Active problem: {cell_cog} (Mastery: {int(p_mastery * 100)}%)"
            elif has_explicit:
                # Concept with explicit student history
                if p_mastery >= 0.85:
                    conf = round(max(0.04, (1.0 - p_mastery) * 0.8), 2)
                    cell_cog = "FOCUSED"
                    cell_breakdown = f"Tested with high accuracy ({int(p_mastery * 100)}% mastery). Cognitive load minimal."
                    cell_efficacy = {"status": "HELPED", "summary_text": "✅ Verified: Concept retained with high accuracy."}
                elif p_mastery >= 0.60:
                    conf = round(0.15 + (0.85 - p_mastery) * 0.7, 2)
                    cell_cog = "NATURALLY_SLOW" if s_profile == "naturally_slow" else "FOCUSED"
                    cell_breakdown = f"Tested concept with steady pacing ({int(p_mastery * 100)}% mastery)."
                    cell_efficacy = {"status": "HELPED", "summary_text": "✅ Stable progression."}
                elif p_mastery >= 0.35:
                    conf = round(0.35 + (0.60 - p_mastery) * 0.8, 2)
                    cell_cog = "BORED" if s_profile == "bored" else "CONFUSED"
                    cell_breakdown = f"Moderate hesitation detected ({int(p_mastery * 100)}% mastery)."
                    cell_efficacy = {"status": "MONITORING", "summary_text": "Pedagogical intervention prepared."}
                else:
                    conf = round(min(0.95, 0.65 + (0.35 - p_mastery) * 0.9), 2)
                    cell_cog = "CONFUSED"
                    cell_breakdown = f"Struggling with concept prerequisites ({int(p_mastery * 100)}% mastery)."
                    cell_efficacy = {"status": "UNRESOLVED", "summary_text": "⚠️ Escalated to Instructor Alert."}
                st = "confused" if conf >= 0.65 else ("hesitant" if conf >= 0.35 else "calm")
                why = f"Tested: {cell_cog} (Mastery: {int(p_mastery * 100)}%)"
            elif c_order < active_order:
                # Prerequisite concept completed earlier in curriculum
                if s_profile == "focused":
                    p_est = max(0.85, 0.95 - (active_order - c_order) * 0.02)
                    conf = round(max(0.04, 0.08 - (active_order - c_order) * 0.02), 2)
                    cell_cog = "FOCUSED"
                elif s_profile == "naturally_slow":
                    p_est = max(0.75, 0.88 - (active_order - c_order) * 0.03)
                    conf = round(max(0.12, 0.18 - (active_order - c_order) * 0.02), 2)
                    cell_cog = "NATURALLY_SLOW"
                elif s_profile == "hesitant" or s_profile == "bored":
                    p_est = max(0.65, 0.80 - (active_order - c_order) * 0.04)
                    conf = round(max(0.15, 0.25 - (active_order - c_order) * 0.04), 2)
                    cell_cog = "BORED"
                else:  # confused / struggling
                    p_est = max(0.40, 0.55 - (active_order - c_order) * 0.05)
                    conf = round(min(0.55, 0.45 + (active_order - c_order) * 0.03), 2)
                    cell_cog = "CONFUSED"
                st = "confused" if conf >= 0.65 else ("hesitant" if conf >= 0.35 else "calm")
                cell_breakdown = f"Prerequisite completed (Estimated mastery: {int(p_est * 100)}%)."
                cell_efficacy = {"status": "HELPED", "summary_text": "✅ Prerequisite verified."}
                why = f"Completed prerequisite ({cell_cog}, Mastery: {int(p_est * 100)}%)"
            else:
                # Upcoming concept ahead in curriculum
                if s_profile == "focused":
                    p_est = max(0.35, 0.65 - (c_order - active_order) * 0.10)
                    conf = round(min(0.30, 0.15 + (c_order - active_order) * 0.05), 2)
                    cell_cog = "FOCUSED"
                elif s_profile == "naturally_slow":
                    p_est = max(0.30, 0.55 - (c_order - active_order) * 0.08)
                    conf = round(min(0.30, 0.18 + (c_order - active_order) * 0.04), 2)
                    cell_cog = "NATURALLY_SLOW"
                elif s_profile == "bored":
                    p_est = max(0.25, 0.45 - (c_order - active_order) * 0.06)
                    conf = round(min(0.50, 0.35 + (c_order - active_order) * 0.05), 2)
                    cell_cog = "BORED"
                elif s_profile == "gaming":
                    p_est = max(0.20, 0.40 - (c_order - active_order) * 0.08)
                    conf = round(min(0.65, 0.50 + (c_order - active_order) * 0.05), 2)
                    cell_cog = "GAMING"
                else:  # confused
                    p_est = max(0.08, 0.20 - (c_order - active_order) * 0.05)
                    conf = round(min(0.92, 0.75 + (c_order - active_order) * 0.06), 2)
                    cell_cog = "CONFUSED"
                st = "confused" if conf >= 0.65 else ("hesitant" if conf >= 0.35 else "calm")
                cell_breakdown = f"Upcoming curriculum concept (Projected readiness: {int(p_est * 100)}%)."
                cell_efficacy = {"status": "MONITORING", "summary_text": "Awaiting module entry."}
                why = f"Upcoming concept ({cell_cog}, Projected: {int(p_est * 100)}%)"

            row_cells.append(HeatmapCell(
                confusion=conf,
                why=why,
                state=st,
                cognitive_state=cell_cog,
                breakdown=cell_breakdown,
                efficacy=cell_efficacy,
            ))
        cells.append(row_cells)

    # In-memory sessions not yet in DB
    for sid, sess in sessions.items():
        if sid in seen_ids:
            continue
        seen_ids.add(sid)
        latest_conf = 0.1
        latest_st = "calm"
        latest_cog = sess.get("cognitive_state", "FOCUSED")
        if sess.get("confusion_history"):
            latest = sess["confusion_history"][-1]
            latest_conf = float(latest.get("score", 0.1))
            latest_st = str(latest.get("state", "calm"))

        students.append({
            "id": sid,
            "name": sess.get("student_name") or f"Student {sid[:5]}",
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
                cell_cog = latest_cog
                why = f"Active: {cell_cog} (Mastery: {int(p_mastery * 100)}%)"
            else:
                conf = round(max(0.05, 1.0 - p_mastery), 2)
                st = "confused" if conf > 0.65 else ("hesitant" if conf > 0.35 else "calm")
                cell_cog = "CONFUSED" if conf > 0.65 else "FOCUSED"
                why = f"Mastery: {int(p_mastery * 100)}%"
            row_cells.append(HeatmapCell(
                confusion=conf,
                why=why,
                state=st,
                cognitive_state=cell_cog,
                breakdown=sess.get("last_breakdown", ""),
                efficacy=sess.get("last_efficacy", None),
            ))
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
            cog_state = "FOCUSED"
            pace = 1.0
            cooldown = 0
            efficacy = None

            # Check in-memory session
            sess = sessions.get(session_id)
            if sess:
                if sess.get("confusion_history"):
                    latest = sess["confusion_history"][-1]
                    score = float(latest.get("score", 0.05))
                    state = str(latest.get("state", "calm"))
                cog_state = str(sess.get("cognitive_state", "FOCUSED"))
                pace = float(sess.get("student_pace_factor", 1.0))
                efficacy = sess.get("last_efficacy")
                if cog_state == "GAMING":
                    cooldown = 10
            else:
                # Check DB
                with get_connection() as conn:
                    row = conn.execute(
                        "SELECT confusion_score, confusion_state, cognitive_state, student_pace_factor FROM sessions WHERE session_id = ?",
                        (session_id,),
                    ).fetchone()
                    if row:
                        score = float(row["confusion_score"] or 0.05)
                        state = str(row["confusion_state"] or "calm")
                        cog_state = str(row["cognitive_state"] or "FOCUSED")
                        pace = float(row["student_pace_factor"] or 1.0)
                        if cog_state == "GAMING":
                            cooldown = 10

            await websocket.send_json({
                "score": round(score, 2),
                "state": state,
                "cognitive_state": cog_state,
                "student_pace_factor": round(pace, 2),
                "cooldown_seconds": cooldown,
                "intervention_efficacy": efficacy,
            })
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for session: {session_id}")
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")

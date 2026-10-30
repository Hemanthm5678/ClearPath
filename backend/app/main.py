import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
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
from backend.app.llm.prompts import build_chat_prompt, build_explain_prompt
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

# ----------------- Pydantic Models -----------------

class SessionRequest(BaseModel):
    profile: Optional[str] = "live"

class SessionResponse(BaseModel):
    session_id: str
    concept: Dict[str, Any]
    question: Dict[str, Any]

class EventRequest(BaseModel):
    session_id: str
    question_id: str
    type: str  # 'tick' | 'submit' | 'hint' | 'lost'
    features: Dict[str, Any] = Field(default_factory=dict)
    answer: Optional[str] = None

class ConfusionModel(BaseModel):
    score: float
    state: str
    reasons: List[str]

class ActionWhy(BaseModel):
    signals: List[str]
    decision: str
    prereq: Optional[str] = None

class ActionModel(BaseModel):
    type: str
    style: str
    level: int
    why: ActionWhy

class TutorModel(BaseModel):
    explanation: str
    check_question: str
    visual_description: str
    source: str

class EventResponse(BaseModel):
    confusion: ConfusionModel
    mastery: Dict[str, float]
    action: ActionModel
    tutor: Optional[TutorModel] = None

class NextQuestionResponse(BaseModel):
    question: Dict[str, Any]
    concept: str
    difficulty: str

class ExplainRequest(BaseModel):
    session_id: str
    style: Optional[str] = "visual"
    level: Optional[int] = 1

class ExplainResponse(BaseModel):
    explanation: str
    check_question: str
    visual_description: str
    source: str

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    source: str

class HeatmapCell(BaseModel):
    confusion: float
    state: str
    why: str

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

# ----------------- API Endpoints (Plain def for blocking I/O) -----------------

@app.post("/api/session", response_model=SessionResponse)
def create_session(req: SessionRequest):
    """Start a session"""
    session_id = f"s_{uuid.uuid4().hex[:10]}"
    concepts = load_concepts()
    questions = load_questions()

    initial_concept = concepts[2] if len(concepts) > 2 else concepts[0]  # default to c3_fraction_as_division
    concept_questions = [q for q in questions if q["concept_id"] == initial_concept["id"]]
    initial_question = concept_questions[0] if concept_questions else questions[0]

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions (session_id, profile, student_name, concept_id, question_id, confusion_score, confusion_state, created_at)
            VALUES (?, ?, ?, ?, ?, 0.05, 'focused', ?)
            """,
            (session_id, req.profile or "live", "Student", initial_concept["id"], initial_question["id"], time.time())
        )
        conn.commit()

    return SessionResponse(
        session_id=session_id,
        concept=initial_concept,
        question=initial_question
    )

@app.post("/api/events", response_model=EventResponse)
def ingest_event(req: EventRequest):
    """Send behaviour signals and answers"""
    # 1. Transform raw events -> feature vector and human readable reasons
    feature_vec, reasons = extract_features(req.features)
    hint_tapped = req.type == "hint" or "hint tapped" in reasons
    if req.type == "lost" and "lost button tapped" not in reasons:
        reasons.append("lost button tapped")

    # 2. Confusion detection (XGBoost + rule fallback)
    confusion = detect_confusion(feature_vec, reasons, session_id=req.session_id)

    # 3. Retrieve session context
    concept_id = "c3_fraction_as_division"
    with get_connection() as conn:
        row = conn.execute("SELECT concept_id, question_id FROM sessions WHERE session_id = ?", (req.session_id,)).fetchone()
        if row and row["concept_id"]:
            concept_id = row["concept_id"]

    # 4. Bayesian Knowledge Tracing on 'submit'
    question = get_question_by_id(req.question_id)
    if req.type == "submit" and req.answer is not None and question is not None:
        is_correct = (str(req.answer).strip().lower() == str(question.get("correct_answer")).strip().lower())
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
        hint_tapped=hint_tapped,
        concept_id=concept_id,
        session_id=req.session_id,
    )

    # Update session in DB
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE sessions 
            SET confusion_score = ?, confusion_state = ?, question_id = ?
            WHERE session_id = ?
            """,
            (confusion["score"], confusion["state"], req.question_id, req.session_id)
        )
        # Log event
        conn.execute(
            """
            INSERT INTO events (session_id, question_id, event_type, features_json, answer, confusion_score, confusion_state, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                req.session_id,
                req.question_id,
                req.type,
                json.dumps(req.features),
                req.answer or "",
                confusion["score"],
                confusion["state"],
                time.time()
            )
        )
        conn.commit()

    # 6. Generate tutor response if re-explanation or hint required
    tutor_data: Optional[Dict[str, Any]] = None
    if action_dict["type"] in ("re_explain", "hint"):
        concept_obj = get_concept_by_id(concept_id) or {"name": "Fractions"}
        q_prompt = question.get("prompt", "") if question else "Explain this concept"
        tutor_data = ask(
            "explain_concept",
            {
                "concept_name": concept_obj.get("name", "Fractions"),
                "concept_id": concept_id,
                "student_age": 10,
                "confusion_reasons": confusion["reasons"],
                "style": action_dict["style"],
                "level": action_dict["level"],
                "question_prompt": q_prompt
            }
        )

    tutor_model = None
    if tutor_data:
        tutor_model = TutorModel(
            explanation=tutor_data.get("explanation", ""),
            check_question=tutor_data.get("check_question", ""),
            visual_description=tutor_data.get("visual_description", ""),
            source=tutor_data.get("source", "offline_bank")
        )

    return EventResponse(
        confusion=ConfusionModel(**confusion),
        mastery=all_mastery,
        action=ActionModel(
            type=action_dict["type"],
            style=action_dict["style"],
            level=action_dict["level"],
            why=ActionWhy(**action_dict["why"])
        ),
        tutor=tutor_model
    )

@app.get("/api/question/next", response_model=NextQuestionResponse)
def get_next_question(session_id: str = Query(...)):
    """Next question chosen by the policy"""
    current_concept_id = "c3_fraction_as_division"
    current_question_id = None

    with get_connection() as conn:
        row = conn.execute("SELECT concept_id, question_id FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
        if row:
            current_concept_id = row["concept_id"] or current_concept_id
            current_question_id = row["question_id"]

    next_choice = select_next_question(session_id, current_concept_id, current_question_id)

    with get_connection() as conn:
        conn.execute(
            "UPDATE sessions SET concept_id = ?, question_id = ? WHERE session_id = ?",
            (next_choice["concept"], next_choice["question"]["id"], session_id)
        )
        conn.commit()

    return NextQuestionResponse(
        question=next_choice["question"],
        concept=next_choice["concept"],
        difficulty=next_choice["difficulty"]
    )

@app.post("/api/explain", response_model=ExplainResponse)
def get_explanation(req: ExplainRequest):
    """Explain differently or in simple language"""
    concept_id = "c3_fraction_as_division"
    question_prompt = "Four friends share 3 pizzas"

    with get_connection() as conn:
        row = conn.execute("SELECT concept_id, question_id FROM sessions WHERE session_id = ?", (req.session_id,)).fetchone()
        if row and row["concept_id"]:
            concept_id = row["concept_id"]
        if row and row["question_id"]:
            q = get_question_by_id(row["question_id"])
            if q:
                question_prompt = q.get("prompt", question_prompt)

    concept_obj = get_concept_by_id(concept_id) or {"name": "Fractions"}
    res = ask(
        "explain_concept",
        {
            "concept_name": concept_obj.get("name", "Fractions"),
            "concept_id": concept_id,
            "student_age": 10,
            "confusion_reasons": ["User requested re-explanation"],
            "style": req.style or "visual",
            "level": req.level or 1,
            "question_prompt": question_prompt
        }
    )

    return ExplainResponse(
        explanation=res.get("explanation", ""),
        check_question=res.get("check_question", ""),
        visual_description=res.get("visual_description", ""),
        source=res.get("source", "offline_bank")
    )

@app.post("/api/chat", response_model=ChatResponse)
def student_chat(req: ChatRequest):
    """Student follow-up question"""
    concept_id = "c3_fraction_as_division"
    question_prompt = "Division as fractions"

    with get_connection() as conn:
        row = conn.execute("SELECT concept_id, question_id FROM sessions WHERE session_id = ?", (req.session_id,)).fetchone()
        if row and row["concept_id"]:
            concept_id = row["concept_id"]
        if row and row["question_id"]:
            q = get_question_by_id(row["question_id"])
            if q:
                question_prompt = q.get("prompt", question_prompt)

    concept_obj = get_concept_by_id(concept_id) or {"name": "Fractions"}
    res = ask(
        "chat_reply",
        {
            "chat_history": [],
            "concept": concept_obj.get("name", "Fractions"),
            "concept_id": concept_id,
            "student_message": req.message
        }
    )

    return ChatResponse(
        reply=res.get("reply", "Great thought! Keep exploring and observe how the pieces divide evenly."),
        source=res.get("source", "offline_bank")
    )

@app.get("/api/class/heatmap", response_model=HeatmapResponse)
def get_class_heatmap():
    """Teacher view data"""
    concepts = load_concepts()
    
    with get_connection() as conn:
        session_rows = conn.execute(
            """
            SELECT session_id, student_name, concept_id, confusion_score, confusion_state 
            FROM sessions 
            ORDER BY created_at DESC 
            LIMIT 15
            """
        ).fetchall()

    students = []
    cells: List[List[HeatmapCell]] = []

    for s in session_rows:
        sid = s["session_id"]
        s_name = s["student_name"] or f"Student {sid[:5]}"
        students.append({
            "id": sid,
            "name": s_name,
            "current_concept": s["concept_id"],
            "score": s["confusion_score"] or 0.1,
            "state": s["confusion_state"] or "focused"
        })

        # Build row for each concept
        row_cells = []
        for c in concepts:
            cid = c["id"]
            p_mastery = bkt.get_mastery(sid, cid)
            
            # Confusion relative to concept mastery and active state
            if s["concept_id"] == cid:
                conf = float(s["confusion_score"] or 0.1)
                st = s["confusion_state"] or "focused"
                why = f"Active: {st} (Mastery: {int(p_mastery*100)}%)"
            else:
                conf = round(max(0.05, 1.0 - p_mastery), 2)
                st = "confused" if conf > 0.65 else ("hesitant" if conf > 0.35 else "focused")
                why = f"Mastery: {int(p_mastery*100)}%"

            row_cells.append(HeatmapCell(confusion=conf, state=st, why=why))

        cells.append(row_cells)

    return HeatmapResponse(
        students=students,
        concepts=concepts,
        cells=cells
    )

@app.get("/api/health", response_model=HealthResponse)
def health_check():
    """Status for the badge and rehearsal"""
    return HealthResponse(**get_health_status())

# ----------------- WebSocket for Real-time Meter Push -----------------

@app.websocket("/ws/{session_id}")
async def websocket_meter(websocket: WebSocket, session_id: str):
    """Push confusion updates to the meter every 2 s"""
    await websocket.accept()
    logger.info(f"WebSocket client connected for session: {session_id}")
    try:
        while True:
            score = 0.05
            state = "focused"
            with get_connection() as conn:
                row = conn.execute(
                    "SELECT confusion_score, confusion_state FROM sessions WHERE session_id = ?",
                    (session_id,)
                ).fetchone()
                if row:
                    score = float(row["confusion_score"] or 0.05)
                    state = row["confusion_state"] or "focused"

            await websocket.send_json({
                "score": score,
                "state": state
            })
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for session: {session_id}")
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")

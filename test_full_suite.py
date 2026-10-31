import json
import time
import sys
import uuid
from backend.app.config import settings

# Force offline mode for local deterministic testing
settings.GROQ_API_KEY = ""

from backend.app.database import get_connection, init_db, get_stats, get_cached_llm, set_cached_llm
from backend.app.signals import extract_features, extract_signals_dict, generate_top_reasons
from backend.app.confusion import detect_confusion
from backend.app.tracing import bkt, BayesianKnowledgeTracing
from backend.app.policy import (
    decide_intervention,
    select_next_question,
    load_concepts,
    load_questions,
    get_concept_by_id,
    get_question_by_id,
    bandit,
)
from backend.app.llm.gateway import ask, get_health_status, load_offline_bank
from backend.app.main import (
    create_session, SessionRequest,
    ingest_event, EventRequest, Features,
    get_next_question,
    get_explanation, ExplainRequest,
    student_chat, ChatRequest,
    get_class_heatmap,
    health_check,
    login, signup, get_demo_users_endpoint, LoginRequest, SignupRequest,
    teacher_create_question, teacher_list_questions, CreateQuestionRequest
)

results = []

def record(test_name, success, detail=""):
    results.append({"name": test_name, "success": success, "detail": detail})
    status = "PASS" if success else "FAIL"
    print(f"[{status}] {test_name}: {detail}", flush=True)

print("==================================================", flush=True)
print("  CLEARPATH COMPREHENSIVE END-TO-END SYSTEM AUDIT ", flush=True)
print("==================================================", flush=True)

# 1. DATABASE & SCHEMA INTEGRITY
try:
    init_db()
    with get_connection() as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    expected_tables = ["sessions", "events", "llm_cache", "mastery", "stats"]
    missing = [t for t in expected_tables if t not in tables]
    assert not missing, f"Missing tables: {missing}"
    record("1. Database Schema & Tables", True, f"All expected tables present: {tables}")
except Exception as e:
    record("1. Database Schema & Tables", False, str(e))

# 2. CONTENT INTEGRITY (Concepts & Question Banks)
try:
    concepts = load_concepts()
    assert len(concepts) >= 3, f"Expected >= 3 concepts, got {len(concepts)}"
    for c in concepts:
        assert "id" in c and "name" in c and "order" in c, f"Concept invalid: {c}"
    
    questions = load_questions()
    assert len(questions) >= 5, f"Expected >= 5 questions, got {len(questions)}"
    for q in questions:
        assert "id" in q and "concept_id" in q and "correct_answer" in q and "prompt" in q
    record("2. Content Banks (Concepts & Questions)", True, f"{len(concepts)} concepts, {len(questions)} questions verified")
except Exception as e:
    record("2. Content Banks (Concepts & Questions)", False, str(e))

# 3. OFFLINE FALLBACK BANK & LLM GATEWAY
try:
    bank = load_offline_bank()
    assert len(bank) >= 3, f"Offline bank empty or too small: {len(bank)}"
    exp_visual = ask("explain_concept", {"concept_id": "c3_fraction_as_division", "style": "visual", "level": 1})
    assert exp_visual["source"] in ("offline_bank", "cache")
    assert "explanation" in exp_visual and len(exp_visual["explanation"]) > 20
    
    exp_analogy = ask("explain_concept", {"concept_id": "c3_fraction_as_division", "style": "analogy", "level": 1})
    assert len(exp_analogy["explanation"]) > 20
    
    exp_steps = ask("explain_concept", {"concept_id": "c3_fraction_as_division", "style": "step_by_step", "level": 1})
    assert len(exp_steps["explanation"]) > 20
    
    exp_simple = ask("explain_concept", {"concept_id": "c3_fraction_as_division", "style": "simple_language", "level": 1})
    assert len(exp_simple["explanation"]) > 20

    chat_res = ask("chat_reply", {"concept_id": "c3_fraction_as_division", "student_message": "Why does division relate to fractions?"})
    assert "reply" in chat_res and len(chat_res["reply"]) > 10
    record("3. Offline Fallback Bank (All 4 Modalities + Chat)", True, "Visual, Analogy, Steps, Simple, Chat verified")
except Exception as e:
    record("3. Offline Fallback Bank (All 4 Modalities + Chat)", False, str(e))

# 4. TELEMETRY & BEHAVIORAL SIGNALS EXTRACTION
try:
    test_raw = {
        "idle_time": 18.0,
        "edit_count": 3,
        "retries": 2,
        "backspace_rate": 0.25,
        "focus_lost_count": 1,
    }
    vec, reasons = extract_features(test_raw)
    assert len(vec) == 7, f"Feature vector length {len(vec)} != 7"
    assert any("pause" in r or "edits" in r or "retries" in r for r in reasons)
    record("4. Telemetric Signal Extraction", True, f"Vector length 7, top reasons: {reasons}")
except Exception as e:
    record("4. Telemetric Signal Extraction", False, str(e))

# 5. COGNITIVE CONFUSION DETECTOR (XGBoost + Heuristic Rule Fallback)
try:
    # Calm feature vector (fast response, 0 edits, 0 retries)
    calm_vec, calm_reasons = extract_features({"idle_time": 3.0, "edit_count": 0, "retries": 0})
    calm_det = detect_confusion(calm_vec, calm_reasons)
    assert calm_det["score"] < 0.40, f"Expected calm score < 0.40, got {calm_det['score']}"
    assert calm_det["state"] in ("calm", "focused")

    # Confused feature vector (long hesitation 28s, 5 edits, 3 retries, lost clicked)
    conf_vec, conf_reasons = extract_features({"idle_time": 28.0, "edit_count": 5, "retries": 3, "lost_clicks": 1})
    conf_det = detect_confusion(conf_vec, conf_reasons)
    assert conf_det["score"] >= 0.65, f"Expected confused score >= 0.65, got {conf_det['score']}"
    assert conf_det["state"] in ("confused", "hesitant")
    record("5. Cognitive Confusion Detector", True, f"Calm score: {calm_det['score']} ({calm_det['state']}), Confused score: {conf_det['score']} ({conf_det['state']})")
except Exception as e:
    record("5. Cognitive Confusion Detector", False, str(e))

# 6. BAYESIAN KNOWLEDGE TRACING (BKT)
try:
    bkt_test = BayesianKnowledgeTracing()
    sid = f"fresh_student_{uuid.uuid4().hex[:6]}"
    cid = "c3_fraction_as_division"
    initial_p = bkt_test.get_mastery(sid, cid)
    assert initial_p == bkt_test.p_l0, f"Expected prior {bkt_test.p_l0}, got {initial_p}"
    
    # Correct attempt -> mastery increases
    p1 = bkt_test.record_attempt(sid, cid, is_correct=True)
    assert p1 > initial_p, f"Mastery did not increase on correct answer: {p1} <= {initial_p}"
    
    # Another correct attempt -> mastery increases further
    p2 = bkt_test.record_attempt(sid, cid, is_correct=True)
    assert p2 > p1, f"Mastery did not increase: {p2} <= {p1}"
    
    # Incorrect attempt -> mastery drops
    p3 = bkt_test.record_attempt(sid, cid, is_correct=False)
    assert p3 < p2, f"Mastery did not drop on incorrect answer: {p3} >= {p2}"
    record("6. Bayesian Knowledge Tracing (BKT)", True, f"P(L0)=0.20 -> P(L1)={p1:.3f} -> P(L2)={p2:.3f} -> P(L3)={p3:.3f}")
except Exception as e:
    record("6. Bayesian Knowledge Tracing (BKT)", False, str(e))

# 7. PEDAGOGICAL POLICY ENGINE & THOMPSON SAMPLING BANDIT
try:
    # Confused, first time -> Hint
    action_hint = decide_intervention(
        confusion={"score": 0.75, "state": "confused", "reasons": ["20 s pause"]},
        mastery_prob=0.30,
        hint_tapped=False,
        concept_id="c3_fraction_as_division",
        wrong_attempts=0,
        hint_given=False,
        re_explain_given=False,
    )
    assert action_hint["type"] == "hint", f"Expected 'hint', got {action_hint['type']}"
    assert "why" in action_hint

    # Confused after hint or 2 wrong attempts -> Re-explain (bandit style)
    action_reexp = decide_intervention(
        confusion={"score": 0.75, "state": "confused", "reasons": ["20 s pause"]},
        mastery_prob=0.30,
        hint_tapped=False,
        concept_id="c3_fraction_as_division",
        wrong_attempts=2,
        hint_given=True,
        re_explain_given=False,
    )
    assert action_reexp["type"] == "re_explain", f"Expected 're_explain', got {action_reexp['type']}"
    assert action_reexp["style"] in ("visual", "analogy", "step_by_step", "worked", "simple_language")

    # Calm & high mastery -> Next concept
    action_master = decide_intervention(
        confusion={"score": 0.05, "state": "calm", "reasons": []},
        mastery_prob=0.92,
        hint_tapped=False,
        concept_id="c3_fraction_as_division",
    )
    assert action_master["type"] in ("next_concept", "continue")
    record("7. Pedagogical Policy & Bandit", True, f"Hint: {action_hint['type']}, Re-explain: {action_reexp['type']} (style: {action_reexp.get('style')}), Mastery: {action_master['type']}")
except Exception as e:
    record("7. Pedagogical Policy & Bandit", False, str(e))

# 8. FULL FASTAPI ROUTE PIPELINE & API SPEC (SECTION 8)
try:
    # 8.1 POST /api/session
    s_res = create_session(SessionRequest(profile="live"))
    session_id = s_res.session_id
    question_id = s_res.question["id"]
    concept_id = s_res.concept["id"]
    assert session_id.startswith("s_")
    assert s_res.question["prompt"]
    record("8.1 POST /api/session", True, f"Session {session_id} started for concept {concept_id}")

    # 8.2 POST /api/events (Submit incorrect)
    wrong_res = ingest_event(EventRequest(
        session_id=session_id,
        question_id=question_id,
        type="submit",
        features=Features(idle_time=8.0, edit_count=1, retries=1),
        answer="1/3 of a pizza"
    ))
    assert wrong_res.confusion.score >= 0.0
    assert concept_id in wrong_res.mastery
    record("8.2 POST /api/events (Incorrect Submit)", True, f"Action: {wrong_res.action.type}, Confusion: {wrong_res.confusion.score}")

    # 8.3 POST /api/events (Hint)
    hint_res = ingest_event(EventRequest(
        session_id=session_id,
        question_id=question_id,
        type="hint",
        features=Features(idle_time=12.0)
    ))
    assert hint_res.tutor is not None
    assert len(hint_res.tutor.explanation) > 10
    record("8.3 POST /api/events (Hint)", True, f"Tutor provided hint: {hint_res.tutor.explanation[:40]}...")

    # 8.4 POST /api/events (I'm Lost)
    lost_res = ingest_event(EventRequest(
        session_id=session_id,
        question_id=question_id,
        type="lost",
        features=Features(idle_time=25.0)
    ))
    assert lost_res.confusion.score >= 0.70
    assert lost_res.tutor is not None
    record("8.4 POST /api/events (Lost)", True, f"Confusion spiked to {lost_res.confusion.score}, tutor dispatched")

    # 8.5 POST /api/events (Submit correct)
    corr_answer = s_res.question.get("correct_answer", "3/4 of a pizza")
    corr_res = ingest_event(EventRequest(
        session_id=session_id,
        question_id=question_id,
        type="submit",
        features=Features(idle_time=4.0, edit_count=0, retries=0),
        answer=corr_answer
    ))
    assert corr_res.confusion.score <= 0.35
    record("8.5 POST /api/events (Correct Submit)", True, f"Calm confusion {corr_res.confusion.score}, Mastery updated")

    # 8.6 GET /api/question/next
    next_res = get_next_question(session_id=session_id)
    assert next_res.question["id"]
    assert next_res.difficulty in ("easy", "medium", "hard")
    record("8.6 GET /api/question/next", True, f"Selected next question: {next_res.question['id']} (diff: {next_res.difficulty})")

    # 8.7 POST /api/explain (Visual, Analogy, Steps, Simple)
    for style in ["visual", "analogy", "step_by_step", "simple_language"]:
        exp = get_explanation(ExplainRequest(session_id=session_id, style=style, level=1))
        assert len(exp.explanation) > 20
        assert exp.source != ""
    record("8.7 POST /api/explain (All 4 Modalities)", True, "All 4 explanation styles returned valid multimodal scaffolding")

    # 8.8 POST /api/chat
    chat = student_chat(ChatRequest(session_id=session_id, message="How do I divide 3 pizzas among 4 people?"))
    assert len(chat.reply) > 15
    record("8.8 POST /api/chat", True, f"Reply: {chat.reply[:50]}... (Source: {chat.source})")

    # 8.9 GET /api/class/heatmap
    heatmap = get_class_heatmap()
    assert len(heatmap.students) > 0
    assert len(heatmap.concepts) > 0
    assert len(heatmap.cells) == len(heatmap.students)
    for row in heatmap.cells:
        assert len(row) == len(heatmap.concepts)
        for cell in row:
            assert hasattr(cell, "confusion")
            assert hasattr(cell, "why")
    record("8.9 GET /api/class/heatmap", True, f"Matrix size: {len(heatmap.students)} students x {len(heatmap.concepts)} concepts with diagnostic cells")

    # 8.10 GET /api/health
    health = health_check()
    assert health.mode != ""
    assert isinstance(health.models, list)
    assert isinstance(health.cache_hits, int)
    assert isinstance(health.offline_used, int)
    record("8.10 GET /api/health", True, f"Status: Mode={health.mode}, GroqOk={health.groq_ok}, CacheHits={health.cache_hits}, OfflineUsed={health.offline_used}")

    # 8.11 RBAC & User Authentication (Student & Teacher)
    demos = get_demo_users_endpoint()
    assert len(demos["students"]) >= 2
    assert len(demos["teachers"]) >= 1
    alex_login = login(LoginRequest(email="alex@clearpath.edu", password="clearpath"))
    assert alex_login.status == "ok"
    assert alex_login.user["role"] == "student"
    teacher_login = login(LoginRequest(email="teacher@clearpath.edu", password="clearpath"))
    assert teacher_login.status == "ok"
    assert teacher_login.user["role"] == "teacher"
    test_user_email = f"student_{uuid.uuid4().hex[:6]}@school.edu"
    student_signup = signup(SignupRequest(name="Jordan Smith", email=test_user_email, password="password123", role="student"))
    assert student_signup.status == "ok"
    assert student_signup.user["name"] == "Jordan Smith"
    record("8.11 RBAC & User Authentication", True, f"Student ({alex_login.user['name']}) & Teacher ({teacher_login.user['name']}) verified + Dynamic Signup")

    # 8.12 Teacher Question Authoring & AI Tutor Scaffolding
    author_res = teacher_create_question(CreateQuestionRequest(
        concept_id="c8_quadratic_algebra",
        prompt="What is the discriminant of the quadratic equation 3x² - 5x + 2 = 0?",
        options=["Δ = 1", "Δ = 49", "Δ = -1", "Δ = 25"],
        correct_answer="Δ = 1",
        difficulty="medium"
    ))
    assert author_res["status"] == "ok"
    assert "question" in author_res
    assert "analysis" in author_res
    created_qid = author_res["question"]["id"]
    analysis = author_res["analysis"]
    assert "explanations" in analysis
    assert all(k in analysis["explanations"] for k in ("visual", "analogy", "step_by_step", "simple_language"))

    # Verify that the student explanation endpoint can immediately retrieve the AI Tutor scaffolding for this new question!
    exp_visual = get_explanation(ExplainRequest(session_id=session_id, style="visual", question_id=created_qid, level=1))
    assert len(exp_visual.explanation) > 15

    q_list = teacher_list_questions()
    assert q_list["total"] >= 24
    record("8.12 Teacher Authoring & AI Scaffolding", True, f"Created {created_qid} with 4 AI Tutor modalities, verified in live student pipeline")

except Exception as e:
    record("8. Full Route Pipeline", False, str(e))

print("==================================================", flush=True)
total_tests = len(results)
passed_tests = sum(1 for r in results if r["success"])
failed_tests = total_tests - passed_tests
print(f"AUDIT SUMMARY: {passed_tests}/{total_tests} passed ({passed_tests/total_tests*100:.1f}%)", flush=True)
if failed_tests > 0:
    print(f"FAILED TESTS: {[r['name'] for r in results if not r['success']]}", flush=True)
    sys.exit(1)
else:
    print("ALL CORE BACKEND SYSTEMS ARE 100% OPERATIONAL!", flush=True)
print("==================================================", flush=True)


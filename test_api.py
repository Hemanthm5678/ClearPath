import pytest
from fastapi.testclient import TestClient
from backend.app.config import settings
# Ensure test runs reliably offline
settings.GROQ_API_KEY = ""
from backend.app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_api_session(client):
    res = client.post("/api/session", json={"profile": "live"})
    assert res.status_code == 200
    data = res.json()
    assert "session_id" in data
    assert "concept" in data
    assert "question" in data
    assert "id" in data["question"]
    assert "id" in data["concept"]

def test_api_events_submit(client):
    s_res = client.post("/api/session", json={"profile": "live"})
    s_data = s_res.json()
    sid = s_data["session_id"]
    qid = s_data["question"]["id"]

    res = client.post("/api/events", json={
        "session_id": sid,
        "question_id": qid,
        "type": "submit",
        "features": {
            "idle_time": 4.5,
            "edit_count": 2,
            "retries": 1,
            "backspace_rate": 0.2,
            "focus_lost_count": 0
        },
        "answer": "3/4 of a pizza"
    })
    assert res.status_code == 200
    data = res.json()
    assert "confusion" in data
    assert "score" in data["confusion"]
    assert "state" in data["confusion"]
    assert "reasons" in data["confusion"]
    assert "mastery" in data
    assert "action" in data
    assert "type" in data["action"]
    assert "why" in data["action"]

def test_api_events_hint_and_lost(client):
    s_res = client.post("/api/session", json={"profile": "live"})
    s_data = s_res.json()
    sid = s_data["session_id"]
    qid = s_data["question"]["id"]

    # Test hint
    res_hint = client.post("/api/events", json={
        "session_id": sid,
        "question_id": qid,
        "type": "hint",
        "features": {"idle_time": 10.0}
    })
    assert res_hint.status_code == 200
    assert res_hint.json()["tutor"] is not None

    # Test lost
    res_lost = client.post("/api/events", json={
        "session_id": sid,
        "question_id": qid,
        "type": "lost",
        "features": {"idle_time": 25.0}
    })
    assert res_lost.status_code == 200
    lost_data = res_lost.json()
    assert lost_data["confusion"]["score"] >= 0.7
    assert lost_data["tutor"] is not None

def test_api_question_next(client):
    s_res = client.post("/api/session", json={"profile": "live"})
    sid = s_res.json()["session_id"]

    res = client.get(f"/api/question/next?session_id={sid}")
    assert res.status_code == 200
    data = res.json()
    assert "question" in data
    assert "concept" in data
    assert "difficulty" in data

def test_api_explain(client):
    s_res = client.post("/api/session", json={"profile": "live"})
    sid = s_res.json()["session_id"]

    res = client.post("/api/explain", json={
        "session_id": sid,
        "style": "visual",
        "level": 1
    })
    assert res.status_code == 200
    data = res.json()
    assert "explanation" in data
    assert "source" in data

def test_api_chat(client):
    s_res = client.post("/api/session", json={"profile": "live"})
    sid = s_res.json()["session_id"]

    res = client.post("/api/chat", json={
        "session_id": sid,
        "message": "Can you explain this simpler?"
    })
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert "source" in data

def test_api_heatmap(client):
    res = client.get("/api/class/heatmap")
    assert res.status_code == 200
    data = res.json()
    assert "students" in data
    assert "concepts" in data
    assert "cells" in data
    assert len(data["cells"]) == len(data["students"])
    if data["cells"]:
        cell = data["cells"][0][0]
        assert "confusion" in cell
        assert "why" in cell

def test_api_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "mode" in data
    assert "groq_ok" in data
    assert "models" in data
    assert "cache_hits" in data
    assert "offline_used" in data

def test_websocket_meter(client):
    s_res = client.post("/api/session", json={"profile": "live"})
    sid = s_res.json()["session_id"]
    with client.websocket_connect(f"/ws/{sid}") as ws:
        msg = ws.receive_json()
        assert "score" in msg
        assert "state" in msg
        assert isinstance(msg["score"], (int, float))


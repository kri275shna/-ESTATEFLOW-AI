import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_chat_session():
    res = client.post("/api/v1/chat/sessions", json={
        "full_name": "Krunal Patel",
        "phone": "+919825099881",
        "preferred_language": "en"
    })
    assert res.status_code == 200
    data = res.json()
    assert "session_token" in data
    assert "welcome_message" in data
    assert "Harmony Enclave" in data["welcome_message"]


def test_multilingual_greetings():
    # 1. Hindi greeting
    s_hi = client.post("/api/v1/chat/sessions", json={"preferred_language": "hi"}).json()["session_token"]
    res_hi = client.post(f"/api/v1/chat/sessions/{s_hi}/messages", json={"content": "Namaste, kaise ho?"})
    assert res_hi.status_code == 200
    assert "नमस्ते" in res_hi.json()["reply"]

    # 2. Gujarati greeting
    s_gu = client.post("/api/v1/chat/sessions", json={"preferred_language": "gu"}).json()["session_token"]
    res_gu = client.post(f"/api/v1/chat/sessions/{s_gu}/messages", json={"content": "Kem cho bhai?"})
    assert res_gu.status_code == 200
    assert "નમસ્તે" in res_gu.json()["reply"]


def test_fact_sheet_grounding_amenities():
    token = client.post("/api/v1/chat/sessions", json={}).json()["session_token"]
    
    # Ask about clubhouse and pool
    res = client.post(f"/api/v1/chat/sessions/{token}/messages", json={
        "content": "What amenities and clubhouse facilities do you offer?"
    })
    assert res.status_code == 200
    data = res.json()
    assert "clubhouse" in data["reply"].lower()
    assert data["is_uncertain"] is False


def test_fact_sheet_grounding_rera():
    token = client.post("/api/v1/chat/sessions", json={}).json()["session_token"]
    
    # Ask about RERA number
    res = client.post(f"/api/v1/chat/sessions/{token}/messages", json={
        "content": "What is the RERA registration number and possession date?"
    })
    assert res.status_code == 200
    data = res.json()
    assert "gujrera" in data["reply"].lower() or "rera" in data["reply"].lower()


def test_discount_safety_rule():
    token = client.post("/api/v1/chat/sessions", json={}).json()["session_token"]
    
    # Demand 15% discount
    res = client.post(f"/api/v1/chat/sessions/{token}/messages", json={
        "content": "Can you give me 15% cash discount and cheaper rate?"
    })
    assert res.status_code == 200
    data = res.json()
    # Must refuse to invent discount and direct to sales executive
    assert "sales executive" in data["reply"].lower() or "સેલ્સ" in data["reply"] or "सेल्स" in data["reply"]


def test_unapproved_fact_safety_rule():
    token = client.post("/api/v1/chat/sessions", json={}).json()["session_token"]
    
    # Inquire about unverified detail
    res = client.post(f"/api/v1/chat/sessions/{token}/messages", json={
        "content": "Can I build a private helipad on top of tower B and how far is DPS school in meters?"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_uncertain"] is True
    assert data["is_flagged"] is True
    assert "sales executive will confirm" in data["reply"].lower()


def test_human_escalation_intent():
    s_res = client.post("/api/v1/chat/sessions", json={
        "full_name": "Jignesh Vora",
        "phone": "+919825099882",
        "preferred_language": "en"
    }).json()
    token = s_res["session_token"]
    
    # Request human
    res = client.post(f"/api/v1/chat/sessions/{token}/messages", json={
        "content": "I want to speak with a human sales executive please call me"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["action"] == "TRIGGER_HANDOFF"
    assert data["is_flagged"] is True

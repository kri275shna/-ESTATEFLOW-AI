import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.core.phone import normalize_indian_phone

client = TestClient(app)


def get_token(email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_phone_normalization():
    # 10 digits
    v, p, _ = normalize_indian_phone("9825158210")
    assert v and p == "+919825158210"

    # Leading zero
    v, p, _ = normalize_indian_phone("09825158210")
    assert v and p == "+919825158210"

    # With spaces & dashes
    v, p, _ = normalize_indian_phone("+91-98251-58210")
    assert v and p == "+919825158210"


def test_list_leads_unauthorized():
    res = client.get("/api/v1/leads")
    assert res.status_code == 401


def test_list_leads_sales_head():
    token = get_token("saleshead@estateflow.ai", "Head@123")
    res = client.get("/api/v1/leads", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "leads" in data
    assert data["total"] >= 20


def test_search_explicit_sample_leads():
    token = get_token("saleshead@estateflow.ai", "Head@123")
    
    # 1. Search Hardik Patel LD-58210
    res1 = client.get("/api/v1/leads?search=Hardik", headers={"Authorization": f"Bearer {token}"})
    assert res1.status_code == 200
    leads1 = res1.json()["leads"]
    assert len(leads1) >= 1
    assert leads1[0]["lead_reference"] == "LD-58210"

    # 2. Search Kavita Joshi LD-58224
    res2 = client.get("/api/v1/leads?search=LD-58224", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 200
    leads2 = res2.json()["leads"]
    assert len(leads2) == 1
    assert leads2[0]["full_name"] == "Kavita Joshi"
    assert leads2[0]["status"] == "VISITED"


import random

def test_duplicate_detection_workflow():
    suffix = random.randint(100000, 999999)
    raw_num = f"9825{suffix}"
    
    # First inquiry from Website
    res1 = client.post("/api/v1/leads", json={
        "full_name": f"Test Duplicate User {suffix}",
        "raw_phone": raw_num,
        "email": f"test.dup.{suffix}@example.com",
        "source": "Website",
        "preferred_bhk": "2 BHK",
        "budget_min": 6500000,
        "budget_max": 7500000
    })
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["is_duplicate"] is False
    lead_id = data1["lead"]["id"]

    # Second inquiry for same person with leading zero from Social media
    res2 = client.post("/api/v1/leads", json={
        "full_name": f"Test Duplicate User {suffix}",
        "raw_phone": f"0{raw_num}",  # Same number with leading 0
        "email": f"test.dup.{suffix}@example.com",
        "source": "Social media ad",
        "preferred_bhk": "3 BHK",  # Updated preference
        "budget_min": 8500000,
        "budget_max": 9500000
    })
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["is_duplicate"] is True
    assert data2["lead"]["id"] == lead_id
    assert len(data2["lead"]["duplicate_sources"]) >= 1
    assert "Social media ad" in data2["lead"]["duplicate_sources"][0]


def test_lead_assignment():
    admin_token = get_token("admin@estateflow.ai", "Admin@123")
    
    # Fetch demo users to get executive id
    users_res = client.get("/api/v1/auth/demo-users", headers={"Authorization": f"Bearer {admin_token}"})
    execs = [u for u in users_res.json() if u["role"] == "SALES_EXECUTIVE"]
    target_exec = execs[0]

    # Fetch a lead
    leads_res = client.get("/api/v1/leads?page_size=1", headers={"Authorization": f"Bearer {admin_token}"})
    lead_id = leads_res.json()["leads"][0]["id"]

    # Reassign lead
    assign_res = client.post(
        f"/api/v1/leads/{lead_id}/assign",
        json={"assigned_executive_id": target_exec["id"]},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert assign_res.status_code == 200
    assert "assigned" in assign_res.json()["message"]

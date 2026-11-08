import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_token(email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_list_handoffs_unauthorized():
    res = client.get("/api/v1/handoffs")
    assert res.status_code == 401


def test_list_handoffs_sales_head():
    token = get_token("saleshead@estateflow.ai", "Head@123")
    res = client.get("/api/v1/handoffs", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    handoffs = res.json()
    assert isinstance(handoffs, list)
    if len(handoffs) > 0:
        first = handoffs[0]
        assert "structured_summary" in first
        assert "status" in first


def test_sales_workspace_overview():
    token = get_token("rahul.sales@estateflow.ai", "Sales@123")
    res = client.get("/api/v1/handoffs/workspace/overview", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "kpis" in data
    assert "todays_visits" in data
    assert "upcoming_visits" in data
    assert "pending_handoffs" in data
    assert data["user_role"] == "SALES_EXECUTIVE"


def test_buyer_forbidden_from_workspace():
    token = get_token("buyer@estateflow.ai", "Buyer@123")
    res = client.get("/api/v1/handoffs/workspace/overview", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_update_handoff_resolution():
    token = get_token("admin@estateflow.ai", "Admin@123")
    # First get handoffs
    res = client.get("/api/v1/handoffs", headers={"Authorization": f"Bearer {token}"})
    handoffs = res.json()
    if len(handoffs) > 0:
        target_id = handoffs[0]["id"]
        res_update = client.patch(
            f"/api/v1/handoffs/{target_id}",
            json={"status": "RESOLVED", "notes": "Connected via call, sent brochure."},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res_update.status_code == 200
        assert res_update.json()["status"] == "RESOLVED"

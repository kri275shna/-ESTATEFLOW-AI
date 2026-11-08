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


def test_analytics_overview_unauthorized():
    res = client.get("/api/v1/analytics/overview")
    assert res.status_code == 401


def test_analytics_overview_sales_executive_forbidden():
    token = get_token("rahul.sales@estateflow.ai", "Sales@123")
    res = client.get("/api/v1/analytics/overview", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_analytics_overview_sales_head():
    token = get_token("saleshead@estateflow.ai", "Head@123")
    res = client.get("/api/v1/analytics/overview", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    # Verify summary KPIs
    summary = data["summary"]
    assert "total_leads" in summary
    assert summary["total_leads"] >= 20
    assert "show_up_rate" in summary
    assert "lead_to_visit_rate" in summary
    assert "cost_per_lead" in summary
    assert "cost_per_completed_visit" in summary

    # Verify target comparison
    assert "target_comparison" in data
    assert "first_response" in data["target_comparison"]

    # Verify funnel
    assert len(data["funnel"]) == 5

    # Verify sources
    assert len(data["source_distribution"]) >= 4

    # Verify leaderboard
    assert len(data["exec_leaderboard"]) >= 10

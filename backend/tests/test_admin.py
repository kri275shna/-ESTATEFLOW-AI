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


def test_list_facts_public():
    token = get_token("buyer@estateflow.ai", "Buyer@123")
    res = client.get("/api/v1/admin/facts", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.json()) >= 10


def test_create_update_fact_admin():
    token = get_token("admin@estateflow.ai", "Admin@123")

    # Get a project
    facts_res = client.get("/api/v1/admin/facts", headers={"Authorization": f"Bearer {token}"})
    project_id = facts_res.json()[0]["project_id"]

    # 1. Create Fact
    create_res = client.post(
        "/api/v1/admin/facts",
        json={
            "project_id": project_id,
            "category": "Amenities",
            "attribute_name": "EV Charging Stations",
            "approved_fact": "Dedicated EV charging bays installed in basement level 1.",
            "is_public": True
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_res.status_code == 201
    fact_id = create_res.json()["id"]

    # 2. Update Fact
    update_res = client.patch(
        f"/api/v1/admin/facts/{fact_id}",
        json={
            "approved_fact": "Dedicated fast EV charging bays (15 kW) installed in basement level 1."
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_res.status_code == 200
    assert "fast EV" in update_res.json()["approved_fact"]

    # 3. Check Audit Logs
    audit_res = client.get("/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert audit_res.status_code == 200
    assert len(audit_res.json()) >= 2

    # 4. Clean up / Delete Fact
    del_res = client.delete(f"/api/v1/admin/facts/{fact_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 200


def test_update_slot_capacity():
    token = get_token("admin@estateflow.ai", "Admin@123")

    slots_res = client.get("/api/v1/admin/slots", headers={"Authorization": f"Bearer {token}"})
    assert slots_res.status_code == 200
    slots = slots_res.json()
    assert len(slots) > 0

    target_slot = slots[0]
    update_res = client.patch(
        f"/api/v1/admin/slots/{target_slot['id']}",
        json={"max_capacity": 5, "is_blocked": False},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["max_capacity"] == 5

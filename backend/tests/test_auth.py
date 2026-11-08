import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token

client = TestClient(app)


def test_login_success_admin():
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@estateflow.ai",
        "password": "Admin@123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "ADMIN"
    assert data["email"] == "admin@estateflow.ai"


def test_login_success_sales_head():
    response = client.post("/api/v1/auth/login", json={
        "email": "saleshead@estateflow.ai",
        "password": "Head@123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "SALES_HEAD"


def test_login_success_sales_exec():
    response = client.post("/api/v1/auth/login", json={
        "email": "rahul.sales@estateflow.ai",
        "password": "Sales@123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "SALES_EXECUTIVE"


def test_login_invalid_password():
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@estateflow.ai",
        "password": "WrongPassword999"
    })
    assert response.status_code == 401
    assert "detail" in response.json()


def test_read_me_authenticated():
    # Login as admin
    login_res = client.post("/api/v1/auth/login", json={
        "email": "admin@estateflow.ai",
        "password": "Admin@123"
    })
    token = login_res.json()["access_token"]
    
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["email"] == "admin@estateflow.ai"
    assert user_data["role"] == "ADMIN"


def test_read_me_unauthorized():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_read_me_tampered_token():
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.payload"})
    assert response.status_code == 401


def test_demo_users_endpoint():
    response = client.get("/api/v1/auth/demo-users")
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 4
    roles = [u["role"] for u in users]
    assert "ADMIN" in roles
    assert "SALES_HEAD" in roles
    assert "SALES_EXECUTIVE" in roles

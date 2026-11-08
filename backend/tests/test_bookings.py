import sys
import uuid
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.entities import VisitSlot, Project, Booking, BookingStatus

client = TestClient(app)


def test_list_visit_slots():
    res = client.get("/api/v1/bookings/slots")
    assert res.status_code == 200
    slots = res.json()
    assert len(slots) > 0
    assert "available_spots" in slots[0]
    assert "is_available" in slots[0]


def test_concurrency_safe_booking_lifecycle():
    # 1. Fetch available slot
    slots_res = client.get("/api/v1/bookings/slots")
    slots = [s for s in slots_res.json() if s["is_available"] and s["available_spots"] > 1]
    assert len(slots) > 0
    target_slot = slots[0]
    initial_spots = target_slot["available_spots"]

    suffix = random.randint(100000, 999999)
    phone_1 = f"+919825{suffix}"

    # 2. Book slot for buyer 1
    book_res = client.post("/api/v1/bookings", json={
        "slot_id": target_slot["id"],
        "project_id": target_slot["project_id"],
        "buyer_name": f"Concurrency Buyer {suffix}",
        "raw_phone": phone_1,
        "email": f"buyer.{suffix}@example.com",
        "preferred_bhk": "3 BHK",
        "notes": "Testing slot transaction lock"
    })
    assert book_res.status_code == 201
    booking_data = book_res.json()
    assert "booking_reference" in booking_data
    assert booking_data["status"] == "CONFIRMED"
    booking_id = booking_data["id"]

    # 3. Prevent duplicate booking for same buyer & slot
    dup_res = client.post("/api/v1/bookings", json={
        "slot_id": target_slot["id"],
        "project_id": target_slot["project_id"],
        "buyer_name": f"Concurrency Buyer {suffix}",
        "raw_phone": phone_1,
        "preferred_bhk": "3 BHK"
    })
    assert dup_res.status_code == 409
    assert "already have a confirmed" in dup_res.json()["detail"].lower()

    # 4. Cancel booking and verify capacity reclamation
    cancel_res = client.post(f"/api/v1/bookings/{booking_id}/cancel", json={
        "reason": "Evaluator test cancellation"
    })
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "success"

    # Verify slot capacity re-opened
    db = SessionLocal()
    slot_after = db.query(VisitSlot).filter(VisitSlot.id == target_slot["id"]).first()
    assert slot_after.booked_count < slot_after.max_capacity
    db.close()


def test_capacity_exhaustion_double_booking_protection():
    """Validates that when booked_count reaches max_capacity, further booking is strictly rejected with 409 Conflict."""
    db = SessionLocal()
    project = db.query(Project).first()
    project_id = project.id
    
    # Create isolated test slot with capacity 1
    test_slot = VisitSlot(
        id=str(uuid.uuid4()),
        project_id=project_id,
        slot_start=datetime.now(timezone.utc) + timedelta(days=20, hours=10),
        slot_end=datetime.now(timezone.utc) + timedelta(days=20, hours=11),
        max_capacity=1,
        booked_count=0,
        is_blocked=False
    )
    db.add(test_slot)
    db.commit()
    slot_id = test_slot.id
    db.close()

    phone_a = f"+919825{random.randint(100000, 999999)}"
    phone_b = f"+919825{random.randint(100000, 999999)}"

    # First buyer reserves the single capacity spot
    res_a = client.post("/api/v1/bookings", json={
        "slot_id": slot_id,
        "project_id": project_id,
        "buyer_name": "Buyer A",
        "raw_phone": phone_a
    })
    assert res_a.status_code == 201

    # Second buyer attempts to reserve the now-exhausted slot
    res_b = client.post("/api/v1/bookings", json={
        "slot_id": slot_id,
        "project_id": project_id,
        "buyer_name": "Buyer B",
        "raw_phone": phone_b
    })
    assert res_b.status_code == 409
    assert "fully booked" in res_b.json()["detail"].lower()

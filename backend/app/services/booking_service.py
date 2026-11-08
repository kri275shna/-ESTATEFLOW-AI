import uuid
import random
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status

from app.models.entities import (
    VisitSlot, Booking, BookingStatus, Lead, LeadStatus,
    Project, User, UserRole
)
from app.core.phone import normalize_indian_phone
from app.services.lead_service import get_next_sales_executive, generate_lead_reference


def generate_booking_reference(db: Session) -> str:
    count = db.query(Booking).count() + 90210 + random.randint(1, 99)
    ref = f"BK-{count}"
    while db.query(Booking).filter(Booking.booking_reference == ref).first():
        count += 1
        ref = f"BK-{count}"
    return ref


def create_concurrency_safe_booking(
    db: Session,
    slot_id: str,
    buyer_name: str,
    raw_phone: str,
    project_id: str,
    email: Optional[str] = None,
    preferred_bhk: Optional[str] = "3 BHK",
    notes: Optional[str] = None
) -> Tuple[Booking, Lead]:
    """
    Concurrency-Safe Site-Visit Booking Engine.
    Executes inside an ACID transaction using row-level locking:
    1. Locks the specific visit_slot row with SELECT ... FOR UPDATE.
    2. Validates booked_count < max_capacity.
    3. Finds or creates the lead record using E.164 phone normalization.
    4. Validates that the lead does not already have an active booking for this slot.
    5. Inserts the booking and atomically increments booked_count.
    6. Assigns a salesperson and marks lead status as VISIT_BOOKED.
    """
    now = datetime.now(timezone.utc)

    # 1. Acquire exclusive row lock on slot
    # SQLAlchemy's with_for_update() executes 'SELECT ... FOR UPDATE' in PostgreSQL
    slot_query = db.query(VisitSlot).filter(VisitSlot.id == slot_id)
    # Check if database backend supports row locking
    try:
        slot = slot_query.with_for_update().first()
    except Exception:
        # Fallback for SQLite in local test mode
        slot = slot_query.first()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visit slot not found"
        )

    if slot.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This visit slot has been temporarily blocked by management"
        )

    # 2. Strict capacity check
    if slot.booked_count >= slot.max_capacity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Slot is fully booked. Maximum capacity of {slot.max_capacity} visitors reached."
        )

    # 3. Find or create lead
    is_valid, norm_phone, _ = normalize_indian_phone(raw_phone)
    if not is_valid:
        norm_phone = raw_phone.strip()

    lead = db.query(Lead).filter(Lead.normalized_phone == norm_phone).first()
    if not lead:
        assigned_exec = get_next_sales_executive(db)
        lead = Lead(
            id=str(uuid.uuid4()),
            lead_reference=generate_lead_reference(db),
            full_name=buyer_name.strip(),
            normalized_phone=norm_phone,
            raw_phone=raw_phone.strip(),
            email=email.strip() if email else None,
            source="Website",
            preferred_project_id=project_id,
            preferred_bhk=preferred_bhk,
            status=LeadStatus.VISIT_BOOKED,
            qualification_score=85,
            is_qualified=True,
            assigned_executive_id=assigned_exec.id if assigned_exec else None,
            consent_status=True,
            first_contact_at=now,
            last_contact_at=now,
            created_at=now
        )
        db.add(lead)
        db.flush()
    else:
        lead.status = LeadStatus.VISIT_BOOKED
        lead.qualification_score = max(lead.qualification_score, 85)
        lead.is_qualified = True
        lead.last_contact_at = now

    # 4. Prevent duplicate booking for same buyer & slot
    existing_booking = db.query(Booking).filter(
        Booking.lead_id == lead.id,
        Booking.slot_id == slot.id,
        Booking.status == BookingStatus.CONFIRMED
    ).first()

    if existing_booking:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You already have a confirmed site-visit booking ({existing_booking.booking_reference}) for this slot."
        )

    # 5. Atomically insert booking & increment slot booked_count
    salesperson_id = lead.assigned_executive_id
    if not salesperson_id:
        exec_user = get_next_sales_executive(db)
        salesperson_id = exec_user.id if exec_user else None
        lead.assigned_executive_id = salesperson_id

    booking = Booking(
        id=str(uuid.uuid4()),
        booking_reference=generate_booking_reference(db),
        lead_id=lead.id,
        project_id=project_id,
        slot_id=slot.id,
        assigned_salesperson_id=salesperson_id,
        status=BookingStatus.CONFIRMED,
        notes=notes,
        reminder_1_day_sent=False,
        reminder_2_hr_sent=False,
        confirmed_at=now,
        created_at=now
    )

    slot.booked_count += 1

    db.add(booking)
    db.commit()
    db.refresh(booking)
    db.refresh(slot)
    db.refresh(lead)

    return booking, lead


def cancel_booking(db: Session, booking_id: str, reason: str = "Buyer requested cancellation") -> Booking:
    """Cancels booking and reclaims slot capacity atomically."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status == BookingStatus.CANCELLED:
        return booking

    slot = db.query(VisitSlot).filter(VisitSlot.id == booking.slot_id).first()
    if slot and slot.booked_count > 0:
        slot.booked_count -= 1

    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = datetime.now(timezone.utc)
    booking.cancellation_reason = reason

    db.commit()
    db.refresh(booking)
    return booking

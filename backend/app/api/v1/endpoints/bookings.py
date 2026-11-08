from datetime import datetime, timezone, timedelta
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.entities import VisitSlot, Booking, BookingStatus, Lead, Project, User, UserRole
from app.schemas.bookings import (
    VisitSlotResponse, BookingCreate, BookingResponse,
    BookingCancelRequest, BookingStatusUpdate
)
from app.services.booking_service import create_concurrency_safe_booking, cancel_booking

router = APIRouter()


@router.get("/slots", response_model=List[VisitSlotResponse], summary="List available site-visit slots")
def list_visit_slots(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    days_ahead: int = Query(14, ge=1, le=30, description="Number of future days to show"),
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=days_ahead)

    query = db.query(VisitSlot).filter(
        VisitSlot.slot_start >= now - timedelta(hours=2),
        VisitSlot.slot_start <= end_date,
        VisitSlot.is_blocked == False
    )

    if project_id and project_id != "ALL":
        query = query.filter(VisitSlot.project_id == project_id)

    slots = query.order_by(VisitSlot.slot_start).all()

    result = []
    for s in slots:
        avail = max(0, s.max_capacity - s.booked_count)
        result.append({
            "id": s.id,
            "project_id": s.project_id,
            "project_name": s.project.name if s.project else "Project",
            "slot_start": s.slot_start,
            "slot_end": s.slot_end,
            "max_capacity": s.max_capacity,
            "booked_count": s.booked_count,
            "available_spots": avail,
            "is_available": avail > 0 and not s.is_blocked,
            "is_blocked": s.is_blocked
        })

    return result


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED, summary="Book a site visit with concurrency protection")
def book_site_visit(
    booking_in: BookingCreate,
    db: Session = Depends(get_db)
):
    booking, lead = create_concurrency_safe_booking(
        db=db,
        slot_id=booking_in.slot_id,
        buyer_name=booking_in.buyer_name,
        raw_phone=booking_in.raw_phone,
        project_id=booking_in.project_id,
        email=booking_in.email,
        preferred_bhk=booking_in.preferred_bhk,
        notes=booking_in.notes
    )

    salesperson = booking.assigned_salesperson

    return {
        "id": booking.id,
        "booking_reference": booking.booking_reference,
        "project_id": booking.project_id,
        "project_name": booking.project.name,
        "location": booking.project.location,
        "rera_number": booking.project.rera_number,
        "slot_id": booking.slot_id,
        "slot_start": booking.slot.slot_start,
        "slot_end": booking.slot.slot_end,
        "status": booking.status,
        "assigned_salesperson_id": salesperson.id if salesperson else None,
        "assigned_salesperson_name": salesperson.full_name if salesperson else "Sales Representative",
        "assigned_salesperson_phone": salesperson.phone if salesperson else "+919825000000",
        "lead_id": lead.id,
        "buyer_name": lead.full_name,
        "buyer_phone": lead.normalized_phone,
        "notes": booking.notes,
        "confirmed_at": booking.confirmed_at
    }


@router.get("", response_model=List[BookingResponse], summary="List all bookings with filters")
def list_bookings(
    project_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Booking)

    # Scoping: Sales executives only see their assigned bookings
    if current_user.role == UserRole.SALES_EXECUTIVE:
        query = query.filter(Booking.assigned_salesperson_id == current_user.id)

    if project_id and project_id != "ALL":
        query = query.filter(Booking.project_id == project_id)

    if status_filter and status_filter != "ALL":
        query = query.filter(Booking.status == status_filter)

    bookings = query.order_by(desc(Booking.created_at)).all()

    result = []
    for b in bookings:
        salesperson = b.assigned_salesperson
        result.append({
            "id": b.id,
            "booking_reference": b.booking_reference,
            "project_id": b.project_id,
            "project_name": b.project.name if b.project else "Project",
            "location": b.project.location if b.project else "Ahmedabad",
            "rera_number": b.project.rera_number if b.project else "",
            "slot_id": b.slot_id,
            "slot_start": b.slot.slot_start if b.slot else datetime.now(timezone.utc),
            "slot_end": b.slot.slot_end if b.slot else datetime.now(timezone.utc),
            "status": b.status,
            "assigned_salesperson_id": salesperson.id if salesperson else None,
            "assigned_salesperson_name": salesperson.full_name if salesperson else "Sales Representative",
            "assigned_salesperson_phone": salesperson.phone if salesperson else "",
            "lead_id": b.lead_id,
            "buyer_name": b.lead.full_name if b.lead else "Buyer",
            "buyer_phone": b.lead.normalized_phone if b.lead else "",
            "notes": b.notes,
            "confirmed_at": b.confirmed_at
        })

    return result


@router.post("/{booking_id}/cancel", summary="Cancel booking and reclaim slot capacity")
def cancel_site_visit(
    booking_id: str,
    req: BookingCancelRequest,
    db: Session = Depends(get_db)
):
    booking = cancel_booking(db, booking_id, req.reason or "Buyer requested cancellation")
    return {
        "status": "success",
        "message": f"Booking {booking.booking_reference} cancelled successfully. Slot capacity reclaimed.",
        "booking_reference": booking.booking_reference
    }


@router.patch("/{booking_id}/status", summary="Update booking visit status (Completed / No-Show)")
def update_booking_status(
    booking_id: str,
    status_update: BookingStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if current_user.role == UserRole.SALES_EXECUTIVE and booking.assigned_salesperson_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update bookings assigned to others")

    booking.status = status_update.status
    if status_update.notes:
        booking.notes = f"{booking.notes or ''}\n{status_update.notes}".strip()

    # If completed, update lead status to VISITED
    if status_update.status == BookingStatus.COMPLETED and booking.lead:
        booking.lead.status = LeadStatus.VISITED

    db.commit()
    return {
        "status": "success",
        "message": f"Booking {booking.booking_reference} status updated to {status_update.status}"
    }

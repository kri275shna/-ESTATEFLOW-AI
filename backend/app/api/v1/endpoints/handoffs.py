import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_

from app.core.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.entities import User, UserRole, Lead, LeadStatus, Conversation, Booking, BookingStatus, Handoff, VisitSlot, Project
from app.schemas.handoffs import HandoffResponse, HandoffUpdate

router = APIRouter()


@router.get("", response_model=List[HandoffResponse], summary="List escalated handoffs and flagged conversations")
def list_handoffs(
    status: Optional[str] = Query(None, description="Filter by status (PENDING, ACKNOWLEDGED, RESOLVED)"),
    priority: Optional[str] = Query(None, description="Filter by priority (URGENT, HIGH, NORMAL)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Handoff)

    # Scoping: sales executive only sees their own or unassigned
    if current_user.role == UserRole.SALES_EXECUTIVE:
        query = query.filter(
            (Handoff.assigned_to_user_id == current_user.id) | (Handoff.assigned_to_user_id == None)
        )

    if status:
        query = query.filter(Handoff.status == status.upper())
    if priority:
        query = query.filter(Handoff.priority == priority.upper())

    handoffs = query.order_by(
        desc(Handoff.status == "PENDING"),
        desc(Handoff.created_at)
    ).all()

    results = []
    for h in handoffs:
        lead = db.query(Lead).filter(Lead.id == h.lead_id).first()
        assigned_user = db.query(User).filter(User.id == h.assigned_to_user_id).first() if h.assigned_to_user_id else None

        results.append(HandoffResponse(
            id=h.id,
            lead_id=h.lead_id,
            conversation_id=h.conversation_id,
            assigned_to_user_id=h.assigned_to_user_id,
            reason=h.reason,
            priority=h.priority,
            structured_summary=h.structured_summary,
            recommended_action=h.recommended_action,
            status=h.status,
            created_at=h.created_at,
            resolved_at=h.resolved_at,
            lead_name=lead.full_name if lead else "Unknown Buyer",
            lead_phone=lead.normalized_phone if lead else None,
            lead_reference=lead.lead_reference if lead else None,
            assigned_to_name=assigned_user.full_name if assigned_user else "Unassigned"
        ))

    return results


@router.patch("/{handoff_id}", response_model=HandoffResponse, summary="Update or resolve handoff")
def update_handoff(
    handoff_id: str,
    update: HandoffUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    handoff = db.query(Handoff).filter(Handoff.id == handoff_id).first()
    if not handoff:
        raise HTTPException(status_code=404, detail="Handoff record not found")

    # Only assigned exec or admin/sales_head can update
    if current_user.role == UserRole.SALES_EXECUTIVE and handoff.assigned_to_user_id and handoff.assigned_to_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update handoffs assigned to you")

    if update.status:
        handoff.status = update.status.upper()
        if update.status.upper() == "RESOLVED":
            handoff.resolved_at = datetime.now(timezone.utc)
            # Update associated lead status if it was HUMAN_FOLLOWUP
            lead = db.query(Lead).filter(Lead.id == handoff.lead_id).first()
            if lead and lead.status == LeadStatus.HUMAN_FOLLOWUP:
                lead.status = LeadStatus.CONTACTED
                lead.last_contact_at = datetime.now(timezone.utc)

    if update.recommended_action is not None:
        handoff.recommended_action = update.recommended_action

    db.commit()
    db.refresh(handoff)

    lead = db.query(Lead).filter(Lead.id == handoff.lead_id).first()
    assigned_user = db.query(User).filter(User.id == handoff.assigned_to_user_id).first() if handoff.assigned_to_user_id else None

    return HandoffResponse(
        id=handoff.id,
        lead_id=handoff.lead_id,
        conversation_id=handoff.conversation_id,
        assigned_to_user_id=handoff.assigned_to_user_id,
        reason=handoff.reason,
        priority=handoff.priority,
        structured_summary=handoff.structured_summary,
        recommended_action=handoff.recommended_action,
        status=handoff.status,
        created_at=handoff.created_at,
        resolved_at=handoff.resolved_at,
        lead_name=lead.full_name if lead else "Unknown Buyer",
        lead_phone=lead.normalized_phone if lead else None,
        lead_reference=lead.lead_reference if lead else None,
        assigned_to_name=assigned_user.full_name if assigned_user else "Unassigned"
    )


@router.get("/workspace/overview", summary="Sales Executive personal workspace overview")
def get_sales_workspace(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == UserRole.BUYER:
        raise HTTPException(status_code=403, detail="Buyers do not have access to sales workspace")

    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)
    today_end = today_start + timedelta(days=1)
    seven_days_later = today_start + timedelta(days=7)

    # 1. Assigned leads count & breakdown
    lead_query = db.query(Lead)
    if current_user.role == UserRole.SALES_EXECUTIVE:
        lead_query = lead_query.filter(Lead.assigned_executive_id == current_user.id)

    total_leads = lead_query.count()
    new_leads = lead_query.filter(Lead.status == LeadStatus.NEW).count()
    qualified_leads = lead_query.filter(Lead.status == LeadStatus.QUALIFIED).count()
    needs_followup = lead_query.filter(Lead.status == LeadStatus.HUMAN_FOLLOWUP).count()
    uncontacted_48h = lead_query.filter(
        Lead.first_contact_at.is_(None),
        Lead.created_at < (now - timedelta(hours=48))
    ).count()

    # 2. Today's Site Visits
    booking_query = db.query(Booking).join(VisitSlot).join(Lead).join(Project)
    if current_user.role == UserRole.SALES_EXECUTIVE:
        booking_query = booking_query.filter(
            (Booking.assigned_salesperson_id == current_user.id) | (Lead.assigned_executive_id == current_user.id)
        )

    todays_bookings_raw = booking_query.filter(
        VisitSlot.slot_start >= today_start,
        VisitSlot.slot_start < today_end
    ).order_by(VisitSlot.slot_start).all()

    todays_visits = []
    for b in todays_bookings_raw:
        todays_visits.append({
            "booking_id": b.id,
            "booking_reference": b.booking_reference,
            "status": b.status,
            "lead_name": b.lead.full_name if b.lead else "Buyer",
            "lead_phone": b.lead.normalized_phone if b.lead else "",
            "lead_reference": b.lead.lead_reference if b.lead else "",
            "project_name": b.project.name if b.project else "Project",
            "slot_start": b.slot.slot_start.isoformat(),
            "slot_end": b.slot.slot_end.isoformat(),
            "notes": b.notes
        })

    # 3. Upcoming Site Visits (next 7 days)
    upcoming_bookings_raw = booking_query.filter(
        VisitSlot.slot_start >= today_end,
        VisitSlot.slot_start < seven_days_later,
        Booking.status == BookingStatus.CONFIRMED
    ).order_by(VisitSlot.slot_start).all()

    upcoming_visits = []
    for b in upcoming_bookings_raw:
        upcoming_visits.append({
            "booking_id": b.id,
            "booking_reference": b.booking_reference,
            "status": b.status,
            "lead_name": b.lead.full_name if b.lead else "Buyer",
            "lead_phone": b.lead.normalized_phone if b.lead else "",
            "project_name": b.project.name if b.project else "Project",
            "slot_start": b.slot.slot_start.isoformat(),
            "slot_end": b.slot.slot_end.isoformat(),
        })

    # 4. Pending Flagged Handoffs
    handoff_q = db.query(Handoff).filter(Handoff.status == "PENDING")
    if current_user.role == UserRole.SALES_EXECUTIVE:
        handoff_q = handoff_q.filter(
            (Handoff.assigned_to_user_id == current_user.id) | (Handoff.assigned_to_user_id == None)
        )
    pending_handoffs_raw = handoff_q.order_by(desc(Handoff.priority == "URGENT"), desc(Handoff.created_at)).limit(10).all()

    pending_handoffs = []
    for h in pending_handoffs_raw:
        lead = db.query(Lead).filter(Lead.id == h.lead_id).first()
        pending_handoffs.append({
            "id": h.id,
            "lead_id": h.lead_id,
            "lead_name": lead.full_name if lead else "Buyer",
            "lead_phone": lead.normalized_phone if lead else "",
            "lead_reference": lead.lead_reference if lead else "",
            "conversation_id": h.conversation_id,
            "reason": h.reason,
            "priority": h.priority,
            "structured_summary": h.structured_summary,
            "recommended_action": h.recommended_action,
            "created_at": h.created_at.isoformat()
        })

    return {
        "user_name": current_user.full_name,
        "user_role": current_user.role,
        "kpis": {
            "total_assigned_leads": total_leads,
            "new_leads": new_leads,
            "qualified_leads": qualified_leads,
            "needs_followup": needs_followup,
            "uncontacted_48h": uncontacted_48h,
            "today_visits_count": len(todays_visits),
            "pending_handoffs_count": len(pending_handoffs)
        },
        "todays_visits": todays_visits,
        "upcoming_visits": upcoming_visits,
        "pending_handoffs": pending_handoffs
    }

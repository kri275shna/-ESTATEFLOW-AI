import json
from datetime import datetime, timezone
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.entities import User, UserRole, Lead, LeadStatus, Conversation, Booking, Handoff
from app.schemas.leads import LeadCreate, LeadUpdate, LeadAssignRequest, LeadResponse, LeadListResponse
from app.services.lead_service import create_or_deduplicate_lead, query_leads

router = APIRouter()


@router.get("", response_model=LeadListResponse, summary="List leads with search, filtering, and role scoping")
def list_leads(
    search: Optional[str] = Query(None, description="Search by name, phone or lead ID"),
    source: Optional[str] = Query(None, description="Filter by source"),
    status: Optional[str] = Query(None, description="Filter by lead status"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    assigned_executive_id: Optional[str] = Query(None, description="Filter by assigned sales executive"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort descending"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(15, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Enforce role scoping: SALES_EXECUTIVE only sees assigned leads
    user_scope = current_user if current_user.role == UserRole.SALES_EXECUTIVE else None

    leads, total = query_leads(
        db=db,
        search=search,
        source=source,
        status=status,
        project_id=project_id,
        assigned_executive_id=assigned_executive_id,
        sort_by=sort_by,
        sort_desc=sort_desc,
        page=page,
        page_size=page_size,
        user_scope=user_scope
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return {
        "leads": leads,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.post("", summary="Create lead or detect duplicate enquiry")
def create_lead(
    lead_in: LeadCreate,
    db: Session = Depends(get_db)
):
    lead, is_duplicate = create_or_deduplicate_lead(db, lead_in)
    
    # Return formatted response
    return {
        "is_duplicate": is_duplicate,
        "action": "merged_attribution" if is_duplicate else "created",
        "lead": {
            "id": lead.id,
            "lead_reference": lead.lead_reference,
            "full_name": lead.full_name,
            "normalized_phone": lead.normalized_phone,
            "source": lead.source,
            "duplicate_sources": json.loads(lead.duplicate_source_history) if lead.duplicate_source_history else [],
            "status": lead.status,
            "assigned_executive_id": lead.assigned_executive_id,
        }
    }


@router.get("/{lead_id}", summary="Get detailed lead dossier with conversations and bookings")
def get_lead_details(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Access check: Sales executive cannot view leads assigned to someone else
    if current_user.role == UserRole.SALES_EXECUTIVE and lead.assigned_executive_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view leads assigned to other sales executives")

    # Fetch conversation messages
    conversations_data = []
    for conv in lead.conversations:
        messages = [
            {
                "id": m.id,
                "sender_type": m.sender_type,
                "content": m.content,
                "language": m.language,
                "is_uncertain": m.is_uncertain,
                "created_at": m.created_at
            }
            for m in conv.messages
        ]
        conversations_data.append({
            "id": conv.id,
            "session_token": conv.session_token,
            "preferred_language": conv.preferred_language,
            "is_flagged": conv.is_flagged,
            "flagged_reason": conv.flagged_reason,
            "is_handed_off": conv.is_handed_off,
            "messages": messages
        })

    # Fetch bookings
    bookings_data = [
        {
            "id": b.id,
            "booking_reference": b.booking_reference,
            "project_name": b.project.name if b.project else "",
            "slot_start": b.slot.slot_start if b.slot else None,
            "slot_end": b.slot.slot_end if b.slot else None,
            "status": b.status,
            "notes": b.notes,
            "confirmed_at": b.confirmed_at
        }
        for b in lead.bookings
    ]

    # Fetch handoffs
    handoffs_data = [
        {
            "id": h.id,
            "reason": h.reason,
            "priority": h.priority,
            "structured_summary": h.structured_summary,
            "recommended_action": h.recommended_action,
            "status": h.status,
            "created_at": h.created_at
        }
        for h in lead.handoffs
    ]

    return {
        "id": lead.id,
        "lead_reference": lead.lead_reference,
        "full_name": lead.full_name,
        "normalized_phone": lead.normalized_phone,
        "raw_phone": lead.raw_phone,
        "email": lead.email,
        "source": lead.source,
        "duplicate_sources": json.loads(lead.duplicate_source_history) if lead.duplicate_source_history else [],
        "preferred_project_id": lead.preferred_project_id,
        "preferred_project_name": lead.preferred_project.name if lead.preferred_project else None,
        "preferred_bhk": lead.preferred_bhk,
        "budget_min": float(lead.budget_min) if lead.budget_min else None,
        "budget_max": float(lead.budget_max) if lead.budget_max else None,
        "preferred_location": lead.preferred_location,
        "buying_timeline": lead.buying_timeline,
        "status": lead.status,
        "qualification_score": lead.qualification_score,
        "is_qualified": lead.is_qualified,
        "assigned_executive_id": lead.assigned_executive_id,
        "assigned_executive_name": lead.assigned_executive.full_name if lead.assigned_executive else "Unassigned",
        "consent_status": lead.consent_status,
        "first_contact_at": lead.first_contact_at,
        "last_contact_at": lead.last_contact_at,
        "created_at": lead.created_at,
        "conversations": conversations_data,
        "bookings": bookings_data,
        "handoffs": handoffs_data
    }


@router.patch("/{lead_id}", summary="Update lead details or status")
def update_lead(
    lead_id: str,
    lead_update: LeadUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if current_user.role == UserRole.SALES_EXECUTIVE and lead.assigned_executive_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit leads assigned to others")

    update_data = lead_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)

    lead.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(lead)
    return {"status": "success", "message": f"Lead {lead.lead_reference} updated successfully"}


@router.post("/{lead_id}/assign", summary="Assign lead to a sales executive (Sales Head/Admin only)")
def assign_lead(
    lead_id: str,
    assign_req: LeadAssignRequest,
    current_user: User = Depends(require_role([UserRole.SALES_HEAD, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    executive = db.query(User).filter(
        User.id == assign_req.assigned_executive_id,
        User.role == UserRole.SALES_EXECUTIVE
    ).first()
    if not executive:
        raise HTTPException(status_code=400, detail="Sales executive not found or invalid role")

    lead.assigned_executive_id = executive.id
    lead.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "status": "success",
        "message": f"Lead {lead.lead_reference} assigned to {executive.full_name}"
    }

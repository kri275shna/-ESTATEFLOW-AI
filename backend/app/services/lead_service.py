import json
import random
from datetime import datetime, timezone
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from app.models.entities import Lead, LeadStatus, LeadSource, User, UserRole, Project
from app.core.phone import normalize_indian_phone
from app.schemas.leads import LeadCreate, LeadUpdate


def generate_lead_reference(db: Session) -> str:
    """Generates unique real estate lead ID, e.g. LD-58251"""
    count = db.query(Lead).count() + 58210 + random.randint(1, 99)
    ref = f"LD-{count}"
    while db.query(Lead).filter(Lead.lead_reference == ref).first():
        count += 1
        ref = f"LD-{count}"
    return ref


def get_next_sales_executive(db: Session) -> Optional[User]:
    """Round-robin deterministic assignment across active sales executives"""
    executives = db.query(User).filter(
        User.role == UserRole.SALES_EXECUTIVE,
        User.is_active == True
    ).order_by(User.id).all()

    if not executives:
        return None

    # Find executive with least assigned leads
    exec_lead_counts = []
    for ex in executives:
        c = db.query(Lead).filter(Lead.assigned_executive_id == ex.id).count()
        exec_lead_counts.append((c, ex))
    
    exec_lead_counts.sort(key=lambda x: x[0])
    return exec_lead_counts[0][1]


def create_or_deduplicate_lead(db: Session, lead_in: LeadCreate) -> Tuple[Lead, bool]:
    """
    Core duplicate detection engine:
    1. Normalizes Indian phone number to E.164.
    2. Checks for existing lead by normalized_phone.
    3. If duplicate found: preserves original source, appends to duplicate_source_history, updates contact time.
    4. If new: creates new lead and assigns salesperson.
    """
    is_valid, normalized_phone, error_msg = normalize_indian_phone(lead_in.raw_phone)
    if not is_valid:
        normalized_phone = lead_in.raw_phone.strip()

    now = datetime.now(timezone.utc)
    existing_lead = db.query(Lead).filter(Lead.normalized_phone == normalized_phone).first()

    if existing_lead:
        # Buyer arrived through another source - record duplicate attribution
        history: List[str] = []
        if existing_lead.duplicate_source_history:
            try:
                history = json.loads(existing_lead.duplicate_source_history)
            except Exception:
                history = [existing_lead.duplicate_source_history]

        attribution_entry = f"{lead_in.source} ({now.strftime('%Y-%m-%d %H:%M')})"
        if attribution_entry not in history:
            history.append(attribution_entry)
        existing_lead.duplicate_source_history = json.dumps(history)

        # Update preferences if provided
        if lead_in.preferred_project_id:
            existing_lead.preferred_project_id = lead_in.preferred_project_id
        if lead_in.preferred_bhk:
            existing_lead.preferred_bhk = lead_in.preferred_bhk
        if lead_in.budget_min:
            existing_lead.budget_min = lead_in.budget_min
        if lead_in.budget_max:
            existing_lead.budget_max = lead_in.budget_max
        if lead_in.buying_timeline:
            existing_lead.buying_timeline = lead_in.buying_timeline

        existing_lead.last_contact_at = now
        db.commit()
        db.refresh(existing_lead)
        return existing_lead, True

    # New Lead creation
    assigned_exec = get_next_sales_executive(db)
    new_lead = Lead(
        lead_reference=generate_lead_reference(db),
        full_name=lead_in.full_name.strip(),
        normalized_phone=normalized_phone,
        raw_phone=lead_in.raw_phone.strip(),
        email=lead_in.email.strip() if lead_in.email else None,
        source=lead_in.source,
        duplicate_source_history=None,
        preferred_project_id=lead_in.preferred_project_id,
        preferred_bhk=lead_in.preferred_bhk,
        budget_min=lead_in.budget_min,
        budget_max=lead_in.budget_max,
        preferred_location=lead_in.preferred_location or "Ahmedabad",
        buying_timeline=lead_in.buying_timeline or "1-3 months",
        status=LeadStatus.NEW,
        qualification_score=50,
        is_qualified=False,
        assigned_executive_id=assigned_exec.id if assigned_exec else None,
        consent_status=lead_in.consent_status,
        first_contact_at=now,
        last_contact_at=now,
        created_at=now
    )

    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    return new_lead, False


def query_leads(
    db: Session,
    search: Optional[str] = None,
    source: Optional[str] = None,
    status: Optional[str] = None,
    project_id: Optional[str] = None,
    assigned_executive_id: Optional[str] = None,
    sort_by: str = "created_at",
    sort_desc: bool = True,
    page: int = 1,
    page_size: int = 15,
    user_scope: Optional[User] = None
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Search and filter leads with role-based scoping:
    - SALES_EXECUTIVE can only see their assigned leads.
    - SALES_HEAD and ADMIN see all leads.
    """
    query = db.query(Lead)

    # Scoping
    if user_scope and user_scope.role == UserRole.SALES_EXECUTIVE:
        query = query.filter(Lead.assigned_executive_id == user_scope.id)

    # Search (name, phone, lead_reference)
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Lead.full_name.ilike(search_pattern),
                Lead.lead_reference.ilike(search_pattern),
                Lead.raw_phone.ilike(search_pattern),
                Lead.normalized_phone.ilike(search_pattern),
            )
        )

    # Filters
    if source and source != "ALL":
        query = query.filter(Lead.source == source)
    if status and status != "ALL":
        query = query.filter(Lead.status == status)
    if project_id and project_id != "ALL":
        query = query.filter(Lead.preferred_project_id == project_id)
    if assigned_executive_id and assigned_executive_id != "ALL":
        query = query.filter(Lead.assigned_executive_id == assigned_executive_id)

    total = query.count()

    # Sorting
    sort_column = getattr(Lead, sort_by, Lead.created_at)
    if sort_desc:
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Pagination
    offset = (page - 1) * page_size
    leads = query.offset(offset).limit(page_size).all()

    # Enrich leads with project name and executive name
    result = []
    for lead in leads:
        lead_dict = {
            "id": lead.id,
            "lead_reference": lead.lead_reference,
            "full_name": lead.full_name,
            "normalized_phone": lead.normalized_phone,
            "raw_phone": lead.raw_phone,
            "email": lead.email,
            "source": lead.source,
            "duplicate_source_history": lead.duplicate_source_history,
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
            "opt_out": lead.opt_out,
            "first_contact_at": lead.first_contact_at,
            "last_contact_at": lead.last_contact_at,
            "created_at": lead.created_at,
            "updated_at": lead.updated_at,
        }
        result.append(lead_dict)

    return result, total

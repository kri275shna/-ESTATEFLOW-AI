import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.entities import User, UserRole, Project, PropertyFact, VisitSlot, AuditLog
from app.schemas.admin import (
    PropertyFactCreate, PropertyFactUpdate, PropertyFactResponse,
    SlotCapacityUpdate, AuditLogResponse
)

router = APIRouter()


@router.get("/facts", response_model=List[PropertyFactResponse], summary="List all approved property facts")
def list_property_facts(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(PropertyFact)
    if project_id:
        query = query.filter(PropertyFact.project_id == project_id)
    if category:
        query = query.filter(PropertyFact.category == category)

    facts = query.order_by(PropertyFact.project_id, PropertyFact.category).all()
    results = []
    for f in facts:
        proj = db.query(Project).filter(Project.id == f.project_id).first()
        results.append(PropertyFactResponse(
            id=f.id,
            project_id=f.project_id,
            project_name=proj.name if proj else "Unknown Project",
            category=f.category,
            attribute_name=f.attribute_name,
            approved_fact=f.approved_fact,
            is_public=f.is_public,
            updated_at=f.updated_at,
            updated_by=f.updated_by
        ))
    return results


@router.post("/facts", response_model=PropertyFactResponse, status_code=status.HTTP_201_CREATED, summary="Add new property fact")
def create_property_fact(
    req: PropertyFactCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SALES_HEAD])),
    db: Session = Depends(get_db)
):
    proj = db.query(Project).filter(Project.id == req.project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Target project not found")

    fact = PropertyFact(
        id=str(uuid.uuid4()),
        project_id=req.project_id,
        category=req.category,
        attribute_name=req.attribute_name,
        approved_fact=req.approved_fact,
        is_public=req.is_public,
        updated_by=current_user.id
    )
    db.add(fact)

    audit = AuditLog(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        action="CREATE_FACT",
        entity_type="property_fact",
        entity_id=fact.id,
        change_summary=f"Added fact [{req.category}] {req.attribute_name} for project {proj.name}"
    )
    db.add(audit)
    db.commit()
    db.refresh(fact)

    return PropertyFactResponse(
        id=fact.id,
        project_id=fact.project_id,
        project_name=proj.name,
        category=fact.category,
        attribute_name=fact.attribute_name,
        approved_fact=fact.approved_fact,
        is_public=fact.is_public,
        updated_at=fact.updated_at,
        updated_by=fact.updated_by
    )


@router.patch("/facts/{fact_id}", response_model=PropertyFactResponse, summary="Update approved property fact")
def update_property_fact(
    fact_id: str,
    req: PropertyFactUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SALES_HEAD])),
    db: Session = Depends(get_db)
):
    fact = db.query(PropertyFact).filter(PropertyFact.id == fact_id).first()
    if not fact:
        raise HTTPException(status_code=404, detail="Property fact not found")

    old_fact_summary = f"{fact.attribute_name}: {fact.approved_fact}"

    if req.category is not None:
        fact.category = req.category
    if req.attribute_name is not None:
        fact.attribute_name = req.attribute_name
    if req.approved_fact is not None:
        fact.approved_fact = req.approved_fact
    if req.is_public is not None:
        fact.is_public = req.is_public

    fact.updated_at = datetime.now(timezone.utc)
    fact.updated_by = current_user.id

    audit = AuditLog(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        action="UPDATE_FACT",
        entity_type="property_fact",
        entity_id=fact.id,
        change_summary=f"Updated fact from [{old_fact_summary}] to [{fact.attribute_name}: {fact.approved_fact}]"
    )
    db.add(audit)
    db.commit()
    db.refresh(fact)

    proj = db.query(Project).filter(Project.id == fact.project_id).first()
    return PropertyFactResponse(
        id=fact.id,
        project_id=fact.project_id,
        project_name=proj.name if proj else "Project",
        category=fact.category,
        attribute_name=fact.attribute_name,
        approved_fact=fact.approved_fact,
        is_public=fact.is_public,
        updated_at=fact.updated_at,
        updated_by=fact.updated_by
    )


@router.delete("/facts/{fact_id}", status_code=status.HTTP_200_OK, summary="Delete property fact")
def delete_property_fact(
    fact_id: str,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    fact = db.query(PropertyFact).filter(PropertyFact.id == fact_id).first()
    if not fact:
        raise HTTPException(status_code=404, detail="Property fact not found")

    audit = AuditLog(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        action="DELETE_FACT",
        entity_type="property_fact",
        entity_id=fact.id,
        change_summary=f"Deleted fact [{fact.category}] {fact.attribute_name}"
    )
    db.add(audit)
    db.delete(fact)
    db.commit()
    return {"message": "Fact deleted successfully", "id": fact_id}


@router.get("/slots", summary="List visit slots with capacity and status")
def list_slots(
    project_id: Optional[str] = Query(None),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SALES_HEAD])),
    db: Session = Depends(get_db)
):
    query = db.query(VisitSlot).join(Project)
    if project_id:
        query = query.filter(VisitSlot.project_id == project_id)

    slots = query.order_by(VisitSlot.slot_start).limit(100).all()
    return [
        {
            "id": s.id,
            "project_id": s.project_id,
            "project_name": s.project.name,
            "slot_start": s.slot_start.isoformat(),
            "slot_end": s.slot_end.isoformat(),
            "max_capacity": s.max_capacity,
            "booked_count": s.booked_count,
            "available_spots": s.max_capacity - s.booked_count,
            "is_blocked": s.is_blocked
        }
        for s in slots
    ]


@router.patch("/slots/{slot_id}", summary="Update slot capacity or block status")
def update_slot_capacity(
    slot_id: str,
    req: SlotCapacityUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SALES_HEAD])),
    db: Session = Depends(get_db)
):
    slot = db.query(VisitSlot).filter(VisitSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Visit slot not found")

    if req.max_capacity < slot.booked_count:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reduce capacity below currently booked count ({slot.booked_count})"
        )

    slot.max_capacity = req.max_capacity
    if req.is_blocked is not None:
        slot.is_blocked = req.is_blocked

    audit = AuditLog(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        action="UPDATE_SLOT",
        entity_type="visit_slot",
        entity_id=slot.id,
        change_summary=f"Set slot {slot.slot_start} capacity={slot.max_capacity}, blocked={slot.is_blocked}"
    )
    db.add(audit)
    db.commit()
    db.refresh(slot)

    return {
        "id": slot.id,
        "max_capacity": slot.max_capacity,
        "booked_count": slot.booked_count,
        "is_blocked": slot.is_blocked,
        "available_spots": slot.max_capacity - slot.booked_count
    }


@router.get("/audit-logs", response_model=List[AuditLogResponse], summary="List audit logs")
def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SALES_HEAD])),
    db: Session = Depends(get_db)
):
    logs = db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit).all()
    res = []
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first() if log.user_id else None
        res.append(AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_name=user.full_name if user else "System",
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            change_summary=log.change_summary,
            created_at=log.created_at
        ))
    return res

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class HandoffResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    lead_id: str
    conversation_id: Optional[str] = None
    assigned_to_user_id: Optional[str] = None
    reason: str
    priority: str
    structured_summary: str
    recommended_action: Optional[str] = None
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    lead_name: Optional[str] = None
    lead_phone: Optional[str] = None
    lead_reference: Optional[str] = None
    assigned_to_name: Optional[str] = None


class HandoffUpdate(BaseModel):
    status: Optional[str] = None  # "PENDING", "ACKNOWLEDGED", "RESOLVED"
    recommended_action: Optional[str] = None
    notes: Optional[str] = None

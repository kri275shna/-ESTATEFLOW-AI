from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class PropertyFactBase(BaseModel):
    category: str
    attribute_name: str
    approved_fact: str
    is_public: bool = True


class PropertyFactCreate(PropertyFactBase):
    project_id: str


class PropertyFactUpdate(BaseModel):
    category: Optional[str] = None
    attribute_name: Optional[str] = None
    approved_fact: Optional[str] = None
    is_public: Optional[bool] = None


class PropertyFactResponse(PropertyFactBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    project_name: Optional[str] = None
    updated_at: datetime
    updated_by: Optional[str] = None


class SlotCapacityUpdate(BaseModel):
    max_capacity: int
    is_blocked: Optional[bool] = None


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    change_summary: str
    created_at: datetime

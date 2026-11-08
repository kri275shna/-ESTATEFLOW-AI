from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class LeadBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    raw_phone: str = Field(..., min_length=10, max_length=50)
    email: Optional[str] = None
    source: str = "Website"
    preferred_project_id: Optional[str] = None
    preferred_bhk: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    preferred_location: Optional[str] = None
    buying_timeline: Optional[str] = None
    consent_status: bool = True


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    preferred_project_id: Optional[str] = None
    preferred_bhk: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    buying_timeline: Optional[str] = None
    status: Optional[str] = None
    assigned_executive_id: Optional[str] = None
    opt_out: Optional[bool] = None


class LeadAssignRequest(BaseModel):
    assigned_executive_id: str


class LeadResponse(BaseModel):
    id: str
    lead_reference: str
    full_name: str
    normalized_phone: str
    raw_phone: str
    email: Optional[str] = None
    source: str
    duplicate_source_history: Optional[str] = None
    duplicate_sources: List[str] = []
    
    preferred_project_id: Optional[str] = None
    preferred_project_name: Optional[str] = None
    preferred_bhk: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    preferred_location: Optional[str] = None
    buying_timeline: Optional[str] = None
    
    status: str
    qualification_score: int = 0
    is_qualified: bool = False
    
    assigned_executive_id: Optional[str] = None
    assigned_executive_name: Optional[str] = None
    
    consent_status: bool = True
    opt_out: bool = False
    first_contact_at: Optional[datetime] = None
    last_contact_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LeadListResponse(BaseModel):
    leads: List[LeadResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

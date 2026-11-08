from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class VisitSlotResponse(BaseModel):
    id: str
    project_id: str
    project_name: Optional[str] = None
    slot_start: datetime
    slot_end: datetime
    max_capacity: int
    booked_count: int
    available_spots: int
    is_available: bool
    is_blocked: bool

    class Config:
        from_attributes = True


class BookingCreate(BaseModel):
    slot_id: str
    project_id: str
    buyer_name: str = Field(..., min_length=2, max_length=255)
    raw_phone: str = Field(..., min_length=10, max_length=50)
    email: Optional[str] = None
    preferred_bhk: Optional[str] = "3 BHK"
    notes: Optional[str] = None


class BookingCancelRequest(BaseModel):
    reason: Optional[str] = "Buyer cancelled appointment"


class BookingStatusUpdate(BaseModel):
    status: str  # "COMPLETED", "NO_SHOW", "CANCELLED", "CONFIRMED"
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    id: str
    booking_reference: str
    project_id: str
    project_name: str
    location: str
    rera_number: str
    slot_id: str
    slot_start: datetime
    slot_end: datetime
    status: str
    assigned_salesperson_id: Optional[str] = None
    assigned_salesperson_name: Optional[str] = None
    assigned_salesperson_phone: Optional[str] = None
    lead_id: str
    buyer_name: str
    buyer_phone: str
    notes: Optional[str] = None
    confirmed_at: datetime

    class Config:
        from_attributes = True

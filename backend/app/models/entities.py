import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, Integer, Float, Text, DateTime, ForeignKey, 
    Numeric, UniqueConstraint, CheckConstraint, Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class UserRole:
    BUYER = "BUYER"
    SALES_EXECUTIVE = "SALES_EXECUTIVE"
    SALES_HEAD = "SALES_HEAD"
    ADMIN = "ADMIN"
    ALL_ROLES = [BUYER, SALES_EXECUTIVE, SALES_HEAD, ADMIN]


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default=UserRole.SALES_EXECUTIVE)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    assigned_leads = relationship("Lead", back_populates="assigned_executive", foreign_keys="Lead.assigned_executive_id")
    assigned_bookings = relationship("Booking", back_populates="assigned_salesperson", foreign_keys="Booking.assigned_salesperson_id")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(50), unique=True, index=True, nullable=False)  # "PROJECT-1", "PROJECT-2"
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    rera_number = Column(String(100), nullable=False)
    total_units = Column(Integer, default=210)
    min_price = Column(Numeric(12, 2), nullable=False)  # in INR
    max_price = Column(Numeric(12, 2), nullable=False)
    configurations = Column(String(100), default="2 BHK, 3 BHK")
    possession_date = Column(String(100), default="December 2026")
    brochure_url = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    facts = relationship("PropertyFact", back_populates="project", cascade="all, delete-orphan")
    slots = relationship("VisitSlot", back_populates="project", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="preferred_project")
    bookings = relationship("Booking", back_populates="project")


class PropertyFact(Base):
    __tablename__ = "property_facts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(100), nullable=False)  # "Pricing", "Configuration", "Amenities", "Location", "RERA"
    attribute_name = Column(String(100), nullable=False)  # "2 BHK Carpet Area", "Clubhouse", etc.
    approved_fact = Column(Text, nullable=False)
    is_public = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="facts")


class LeadStatus:
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    VISIT_BOOKED = "VISIT_BOOKED"
    VISITED = "VISITED"
    NOT_INTERESTED = "NOT_INTERESTED"
    LOST = "LOST"
    HUMAN_FOLLOWUP = "HUMAN_FOLLOWUP"


class LeadSource:
    PROPERTY_PORTAL = "Property portal"
    SOCIAL_MEDIA = "Social media"
    WEBSITE = "Website"
    HOARDING = "Hoarding"
    MANUAL_ENTRY = "Manual entry"


class Lead(Base):
    __tablename__ = "leads"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lead_reference = Column(String(50), unique=True, index=True, nullable=False)  # e.g., "LD-58210"
    full_name = Column(String(255), nullable=False, index=True)
    normalized_phone = Column(String(50), unique=True, index=True, nullable=False)  # E.164 e.g. +919825012345
    raw_phone = Column(String(50), nullable=False)
    email = Column(String(255), nullable=True)
    source = Column(String(100), nullable=False, default=LeadSource.WEBSITE)
    duplicate_source_history = Column(Text, nullable=True)  # JSON-encoded array of secondary sources
    
    preferred_project_id = Column(String(36), ForeignKey("projects.id"), nullable=True, index=True)
    preferred_bhk = Column(String(50), nullable=True)  # "2 BHK", "3 BHK"
    budget_min = Column(Numeric(12, 2), nullable=True)
    budget_max = Column(Numeric(12, 2), nullable=True)
    preferred_location = Column(String(255), nullable=True)
    buying_timeline = Column(String(100), nullable=True)  # "Immediate (0-1 mo)", "1-3 months", "3-6 months"
    purchase_reason = Column(String(100), nullable=True)  # "Self Use", "Investment"
    
    status = Column(String(50), nullable=False, default=LeadStatus.NEW, index=True)
    qualification_score = Column(Integer, default=0)
    is_qualified = Column(Boolean, default=False)
    
    assigned_executive_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    consent_status = Column(Boolean, default=True)  # DPDP Act 2023 consent
    opt_out = Column(Boolean, default=False)
    
    first_contact_at = Column(DateTime, nullable=True)
    last_contact_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    preferred_project = relationship("Project", back_populates="leads")
    assigned_executive = relationship("User", back_populates="assigned_leads", foreign_keys=[assigned_executive_id])
    conversations = relationship("Conversation", back_populates="lead", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="lead", cascade="all, delete-orphan")
    handoffs = relationship("Handoff", back_populates="lead", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lead_id = Column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=True, index=True)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    preferred_language = Column(String(20), default="en")  # "en", "hi", "gu"
    is_flagged = Column(Boolean, default=False, index=True)
    flagged_reason = Column(String(255), nullable=True)
    is_handed_off = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    lead = relationship("Lead", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    handoffs = relationship("Handoff", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_type = Column(String(50), nullable=False)  # "buyer", "assistant", "system"
    content = Column(Text, nullable=False)
    language = Column(String(20), default="en")
    is_uncertain = Column(Boolean, default=False)
    approved_facts_used = Column(Text, nullable=True)  # JSON list of fact IDs
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class VisitSlot(Base):
    __tablename__ = "visit_slots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    slot_start = Column(DateTime, nullable=False, index=True)
    slot_end = Column(DateTime, nullable=False)
    max_capacity = Column(Integer, default=3, nullable=False)
    booked_count = Column(Integer, default=0, nullable=False)
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("booked_count <= max_capacity", name="check_booked_within_capacity"),
        CheckConstraint("booked_count >= 0", name="check_booked_non_negative"),
        UniqueConstraint("project_id", "slot_start", name="uq_project_slot_time"),
    )

    # Relationships
    project = relationship("Project", back_populates="slots")
    bookings = relationship("Booking", back_populates="slot")


class BookingStatus:
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    booking_reference = Column(String(50), unique=True, index=True, nullable=False)  # e.g., "BK-90214"
    lead_id = Column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    slot_id = Column(String(36), ForeignKey("visit_slots.id"), nullable=False, index=True)
    assigned_salesperson_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    
    status = Column(String(50), nullable=False, default=BookingStatus.CONFIRMED, index=True)
    notes = Column(Text, nullable=True)
    
    reminder_1_day_sent = Column(Boolean, default=False)
    reminder_2_hr_sent = Column(Boolean, default=False)
    
    confirmed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_lead_slot_active", "lead_id", "slot_id", "status"),
    )

    # Relationships
    lead = relationship("Lead", back_populates="bookings")
    project = relationship("Project", back_populates="bookings")
    slot = relationship("VisitSlot", back_populates="bookings")
    assigned_salesperson = relationship("User", back_populates="assigned_bookings", foreign_keys=[assigned_salesperson_id])


class Handoff(Base):
    __tablename__ = "handoffs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lead_id = Column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=True, index=True)
    assigned_to_user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    
    reason = Column(String(255), nullable=False)  # "Buyer requested salesperson", "Uncertain fact inquiry", "High-intent buyer"
    priority = Column(String(50), default="HIGH")  # "URGENT", "HIGH", "NORMAL"
    structured_summary = Column(Text, nullable=False)  # Formatted dossier summary
    recommended_action = Column(String(255), nullable=True)
    status = Column(String(50), default="PENDING", index=True)  # "PENDING", "ACKNOWLEDGED", "RESOLVED"
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="handoffs")
    conversation = relationship("Conversation", back_populates="handoffs")
    assigned_to_user = relationship("User", foreign_keys=[assigned_to_user_id])


class MarketingSpend(Base):
    __tablename__ = "marketing_spend"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True, index=True)
    source = Column(String(100), nullable=False, index=True)  # "Property portal", "Social media", "Hoarding", "Website"
    month_year = Column(String(20), nullable=False, index=True)  # "2026-11"
    spend_amount = Column(Numeric(12, 2), nullable=False)  # in INR
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False)  # "UPDATE_FACT", "MANUAL_ASSIGN", "CANCEL_BOOKING"
    entity_type = Column(String(100), nullable=False)  # "property_fact", "lead", "booking"
    entity_id = Column(String(36), nullable=False)
    change_summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

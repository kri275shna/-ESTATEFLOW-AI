import uuid
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.entities import (
    Conversation, Message, Lead, LeadStatus, LeadSource,
    Handoff, User, UserRole, Project
)
from app.ai.provider import ai_service
from app.ai.qualification import calculate_qualification_score
from app.services.lead_service import get_next_sales_executive, generate_lead_reference
from app.core.phone import normalize_indian_phone

router = APIRouter()


class SessionInitRequest(BaseModel):
    full_name: Optional[str] = "Prospective Buyer"
    phone: Optional[str] = None
    preferred_language: str = "en"
    project_id: Optional[str] = None


class UserMessageRequest(BaseModel):
    content: str
    project_id: Optional[str] = None


class HandoffRequest(BaseModel):
    reason: Optional[str] = "Buyer explicitly requested to speak with sales executive"
    buyer_name: Optional[str] = None
    phone: Optional[str] = None


@router.post("/sessions", summary="Initialize or resume buyer chat session")
def create_chat_session(req: SessionInitRequest, db: Session = Depends(get_db)):
    session_token = f"chat-{uuid.uuid4().hex[:12]}"
    
    # Check if phone provided to link or create lead
    lead = None
    if req.phone:
        is_valid, norm_phone, _ = normalize_indian_phone(req.phone)
        lead = db.query(Lead).filter(Lead.normalized_phone == (norm_phone if is_valid else req.phone)).first()
        if not lead:
            sales_exec = get_next_sales_executive(db)
            lead = Lead(
                lead_reference=generate_lead_reference(db),
                full_name=req.full_name or "Website Visitor",
                normalized_phone=norm_phone if is_valid else req.phone,
                raw_phone=req.phone,
                source=LeadSource.WEBSITE,
                preferred_project_id=req.project_id,
                status=LeadStatus.NEW,
                assigned_executive_id=sales_exec.id if sales_exec else None,
                first_contact_at=datetime.now(timezone.utc),
                last_contact_at=datetime.now(timezone.utc)
            )
            db.add(lead)
            db.flush()

    conv = Conversation(
        id=str(uuid.uuid4()),
        lead_id=lead.id if lead else None,
        session_token=session_token,
        preferred_language=req.preferred_language,
        is_flagged=False
    )
    db.add(conv)
    db.flush()

    # Initial Welcome message
    welcome_texts = {
        "en": "Namaste! Welcome to Company A, residential developers in Ahmedabad. We offer two premium residential communities: Harmony Enclave in Shela (2 & 3 BHK, ₹65L–₹95L) and Skyline Serenity on SG Highway (2 & 3 BHK Luxury, ₹85L–₹1.2Cr). Are you interested in a 2 BHK or 3 BHK apartment?",
        "hi": "नमस्ते! अहमदाबाद में कंपनी ए (Company A) के आवासीय प्रोजेक्ट्स में आपका स्वागत है। हमारे पास दो प्रमुख प्रोजेक्ट्स हैं: शीला में 'हार्मनी एन्क्लेव' (₹65 लाख - ₹95 लाख) और एस.जी. हाईवे पर 'स्काईलाइन सेरेनिटी' (₹85 लाख - ₹1.2 करोड़)। क्या आप 2 BHK या 3 BHK में रुचि रखते हैं?",
        "gu": "નમસ્તે! અમદાવાદમાં કંપની એ (Company A) ના રેસિડેન્શિયલ પ્રોજેક્ટ્સમાં આપનું સ્વાગત છે. અમારી પાસે બે પ્રીમિયમ પ્રોજેક્ટ્સ છે: શેલા ખાતે 'હાર્મની એન્ક્લેવ' (₹65 લાખ - ₹95 લાખ) અને એસ.જી. હાઇવે પર 'સ્કાયલાઇન સેરેનિટી' (₹85 લાખ - ₹1.2 કરોડ). તમે 2 BHK કે 3 BHK માં રસ ધરાવો છો?"
    }

    welcome_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        sender_type="assistant",
        content=welcome_texts.get(req.preferred_language, welcome_texts["en"]),
        language=req.preferred_language
    )
    db.add(welcome_msg)
    db.commit()

    return {
        "session_token": session_token,
        "preferred_language": req.preferred_language,
        "lead_reference": lead.lead_reference if lead else None,
        "welcome_message": welcome_msg.content
    }


@router.get("/sessions/{session_token}", summary="Retrieve conversation history")
def get_session_history(session_token: str, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.session_token == session_token).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Chat session not found")

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

    return {
        "session_token": conv.session_token,
        "lead_id": conv.lead_id,
        "is_flagged": conv.is_flagged,
        "flagged_reason": conv.flagged_reason,
        "is_handed_off": conv.is_handed_off,
        "preferred_language": conv.preferred_language,
        "messages": messages
    }


@router.post("/sessions/{session_token}/messages", summary="Send message to AI assistant")
def send_chat_message(
    session_token: str,
    req: UserMessageRequest,
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.session_token == session_token).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Chat session not found")

    now = datetime.now(timezone.utc)

    # 1. Store User Message
    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        sender_type="buyer",
        content=req.content,
        language=conv.preferred_language,
        created_at=now
    )
    db.add(user_msg)
    db.flush()

    # Build history context
    history = [
        {"role": m.sender_type, "content": m.content}
        for m in conv.messages[-6:]
    ]

    # 2. Generate Grounded AI Response
    ai_result = ai_service.generate_response(
        db=db,
        user_message=req.content,
        conversation_history=history,
        project_id=req.project_id
    )

    # 3. Store Assistant Message
    assistant_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        sender_type="assistant",
        content=ai_result["reply"],
        language=ai_result.get("language", conv.preferred_language),
        is_uncertain=ai_result.get("is_uncertain", False),
        approved_facts_used=json.dumps(ai_result.get("facts_used", [])),
        created_at=datetime.now(timezone.utc)
    )
    db.add(assistant_msg)

    # 4. Handle Uncertain or Flagged Conversation (Safety Rule 10)
    if ai_result.get("is_uncertain") or ai_result.get("action") == "FLAGGED_FOR_REVIEW":
        conv.is_flagged = True
        conv.flagged_reason = ai_result.get("reason", "Inquiry required human clarification")

    # 5. Extract preferences and update lead qualification if lead exists
    prefs = ai_result.get("extracted_preferences", {})
    qualification_score = 0
    is_qualified = False

    if conv.lead:
        lead = conv.lead
        if prefs.get("preferred_bhk"):
            lead.preferred_bhk = prefs["preferred_bhk"]
        if prefs.get("budget_max"):
            lead.budget_max = prefs["budget_max"]
            lead.budget_min = prefs.get("budget_min", prefs["budget_max"] * 0.9)
        if prefs.get("buying_timeline"):
            lead.buying_timeline = prefs["buying_timeline"]

        # Recalculate score
        has_visit_interest = ai_result.get("action") in ["SHOW_BOOKING_SLOTS", "OFFER_SITE_VISIT"]
        score, qualified, breakdown = calculate_qualification_score(
            preferred_bhk=lead.preferred_bhk,
            budget_min=float(lead.budget_min) if lead.budget_min else None,
            budget_max=float(lead.budget_max) if lead.budget_max else None,
            buying_timeline=lead.buying_timeline,
            has_site_visit_interest=has_visit_interest
        )
        lead.qualification_score = score
        lead.is_qualified = qualified
        if qualified and lead.status == LeadStatus.NEW:
            lead.status = LeadStatus.QUALIFIED
        lead.last_contact_at = now
        qualification_score = score
        is_qualified = qualified

    # 6. Automatic Human Handoff Trigger if requested
    if ai_result.get("action") == "TRIGGER_HANDOFF":
        conv.is_handed_off = True
        conv.is_flagged = True
        conv.flagged_reason = ai_result.get("reason", "Buyer requested salesperson")
        
        if conv.lead:
            conv.lead.status = LeadStatus.HUMAN_FOLLOWUP
            # Ensure assigned executive
            if not conv.lead.assigned_executive_id:
                sales_exec = get_next_sales_executive(db)
                if sales_exec:
                    conv.lead.assigned_executive_id = sales_exec.id

            # Create Handoff Dossier
            handoff = Handoff(
                lead_id=conv.lead.id,
                conversation_id=conv.id,
                assigned_to_user_id=conv.lead.assigned_executive_id,
                reason=ai_result.get("reason", "Buyer requested human salesperson"),
                priority="HIGH",
                structured_summary=(
                    f"Buyer Name: {conv.lead.full_name}\n"
                    f"Phone: {conv.lead.normalized_phone}\n"
                    f"Configuration: {conv.lead.preferred_bhk or '2 or 3 BHK'}\n"
                    f"Budget: ₹{float(conv.lead.budget_min or 6500000)/100000:.0f}L - ₹{float(conv.lead.budget_max or 9500000)/100000:.0f}L\n"
                    f"Buying Timeline: {conv.lead.buying_timeline or '1-3 months'}\n"
                    f"Last Query: '{req.content}'\n"
                    f"Reason for Escalation: {ai_result.get('reason')}\n"
                    f"Recommended Action: Connect via call within 15 minutes to share customized floor plans and arrange site visit."
                ),
                recommended_action="Connect via call within 15 minutes to share customized floor plans and arrange site visit.",
                status="PENDING"
            )
            db.add(handoff)

    db.commit()

    return {
        "reply": assistant_msg.content,
        "action": ai_result.get("action", "NONE"),
        "language": ai_result.get("language", "en"),
        "is_uncertain": assistant_msg.is_uncertain,
        "is_flagged": conv.is_flagged,
        "qualification_score": qualification_score,
        "is_qualified": is_qualified,
        "timestamp": assistant_msg.created_at
    }


@router.post("/sessions/{session_token}/handoff", summary="Explicit buyer request for human salesperson")
def trigger_explicit_handoff(
    session_token: str,
    req: HandoffRequest,
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.session_token == session_token).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Chat session not found")

    now = datetime.now(timezone.utc)
    conv.is_handed_off = True
    conv.is_flagged = True
    conv.flagged_reason = req.reason

    # Link or update lead
    lead = conv.lead
    if not lead and req.phone:
        is_valid, norm_phone, _ = normalize_indian_phone(req.phone)
        lead = db.query(Lead).filter(Lead.normalized_phone == (norm_phone if is_valid else req.phone)).first()
        if not lead:
            sales_exec = get_next_sales_executive(db)
            lead = Lead(
                lead_reference=generate_lead_reference(db),
                full_name=req.buyer_name or "Prospective Buyer",
                normalized_phone=norm_phone if is_valid else req.phone,
                raw_phone=req.phone,
                source=LeadSource.WEBSITE,
                status=LeadStatus.HUMAN_FOLLOWUP,
                assigned_executive_id=sales_exec.id if sales_exec else None,
                first_contact_at=now,
                last_contact_at=now
            )
            db.add(lead)
            db.flush()
        conv.lead_id = lead.id

    if lead:
        lead.status = LeadStatus.HUMAN_FOLLOWUP
        if not lead.assigned_executive_id:
            sales_exec = get_next_sales_executive(db)
            if sales_exec:
                lead.assigned_executive_id = sales_exec.id

        handoff = Handoff(
            lead_id=lead.id,
            conversation_id=conv.id,
            assigned_to_user_id=lead.assigned_executive_id,
            reason=req.reason or "Explicit buyer request",
            priority="HIGH",
            structured_summary=(
                f"Buyer Name: {lead.full_name}\n"
                f"Phone: {lead.normalized_phone}\n"
                f"Configuration: {lead.preferred_bhk or 'Inquiry'}\n"
                f"Escalation Type: Buyer clicked 'Speak with Sales Executive'\n"
                f"Recommended Next Action: Call buyer immediately to assist with property queries."
            ),
            recommended_action="Call buyer immediately to assist with property queries.",
            status="PENDING"
        )
        db.add(handoff)

    # Add confirmation message in chat
    confirm_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        sender_type="assistant",
        content=(
            "Thank you! A dedicated sales executive has been assigned to your inquiry. "
            "They have received your conversation history and preferences, and will reach out to you shortly. "
            "You can also schedule an in-person site visit below."
        ),
        language=conv.preferred_language,
        created_at=now
    )
    db.add(confirm_msg)
    db.commit()

    return {
        "status": "success",
        "message": "Sales executive handoff initiated successfully",
        "assigned_executive_name": lead.assigned_executive.full_name if (lead and lead.assigned_executive) else "Sales Team"
    }

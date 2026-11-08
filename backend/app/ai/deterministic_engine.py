import re
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.ai.grounding import retrieve_relevant_facts, get_project_grounding_context
from app.ai.qualification import calculate_qualification_score

# Multilingual intent keywords
HUMAN_KEYWORDS = [
    "human", "person", "agent", "executive", "call me", "talk to someone", "representative",
    "salesperson", "sales person", "manus", "koik sathe vat", "call karo", "baat karni",
    "kisi se baat", "phone karo", "sales team"
]

DISCOUNT_KEYWORDS = [
    "discount", "cash discount", "special offer", "negotiate", "final price", 
    "kam karo", "chhut", "sasta", "cheaper", "concession", "best price", "kam rate"
]

BOOKING_KEYWORDS = [
    "visit", "book", "slot", "appointment", "see the flat", "mulaqat", "joie chhe", "aavu chhe",
    "site visit", "sample flat"
]

GUJARATI_DETECTORS = [
    "kem cho", "tamaru", "shu", "chhe", "mane", "ghare", "aavu", "joie", "ketla", "bhav"
]

HINDI_DETECTORS = [
    "namaste", "kaise ho", "kya", "hai", "mujhe", "ghar", "aana", "chahiye", "kitna", "daam"
]


def detect_language(text: str) -> str:
    lower = text.lower()
    # Check for Gujarati script (Unicode range \u0A80-\u0AFF)
    if re.search(r"[\u0A80-\u0AFF]", text):
        return "gu"
    # Check for Devanagari Hindi script (Unicode range \u0900-\u097F)
    if re.search(r"[\u0900-\u097F]", text):
        return "hi"
    if any(k in lower for k in GUJARATI_DETECTORS):
        return "gu"
    if any(k in lower for k in HINDI_DETECTORS):
        return "hi"
    return "en"


def parse_buyer_preferences(user_message: str) -> Dict[str, Any]:
    """Extracts preferred configuration, budget, and timeline from conversational text."""
    lower = user_message.lower()
    prefs: Dict[str, Any] = {}

    # BHK detection
    if "3 bhk" in lower or "3bhk" in lower:
        prefs["preferred_bhk"] = "3 BHK"
    elif "2 bhk" in lower or "2bhk" in lower:
        prefs["preferred_bhk"] = "2 BHK"

    # Budget detection (e.g. 70 lakh, 1.1 cr, 85L)
    lakh_match = re.search(r"(\d+(\.\d+)?)\s*(lakh|lac|l)", lower)
    cr_match = re.search(r"(\d+(\.\d+)?)\s*(cr|crore)", lower)
    if lakh_match:
        val = float(lakh_match.group(1)) * 100000
        prefs["budget_min"] = val * 0.9
        prefs["budget_max"] = val * 1.1
    elif cr_match:
        val = float(cr_match.group(1)) * 10000000
        prefs["budget_min"] = val * 0.95
        prefs["budget_max"] = val * 1.05

    # Timeline
    if "immediate" in lower or "ready" in lower or "this month" in lower or "now" in lower:
        prefs["buying_timeline"] = "Immediate (0-1 mo)"
    elif "month" in lower:
        prefs["buying_timeline"] = "1-3 months"

    return prefs


def process_deterministic_message(
    db: Session,
    user_message: str,
    conversation_history: List[Dict[str, str]],
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Multilingual Grounded Deterministic AI Assistant.
    Follows all 10 Mandatory Safety Rules.
    Never invents property info.
    """
    lower = user_message.lower().strip()
    lang = detect_language(user_message)
    prefs = parse_buyer_preferences(user_message)

    # 1. Check for Human Escalation Request (Safety Rule 8)
    if any(k in lower for k in HUMAN_KEYWORDS):
        replies = {
            "en": "I understand you would like to speak directly with our sales team. I have flagged your request and assigned a senior sales executive who will call you promptly on your registered contact number. Would you like to schedule an in-person site visit in the meantime?",
            "hi": "मैं समझता हूँ कि आप सीधे हमारी बिक्री टीम से बात करना चाहते हैं। मैंने आपके अनुरोध को प्राथमिकता पर दर्ज कर दिया है और एक वरिष्ठ सेल्स एग्जीक्यूटिव जल्द ही आपसे संपर्क करेंगे। क्या आप इस बीच साइट विज़िट बुक करना चाहेंगे?",
            "gu": "હું સમજી શકું છું કે તમે અમારી સેલ્સ ટીમ સાથે સીધી વાત કરવા માંગો છો. મેં તમારી વિનંતી નોંધી લીધી છે અને અમારા સિનિયર સેલ્સ એક્ઝિક્યુટિવ તમને ટૂંક સમયમાં સંપર્ક કરશે. શું તમે આ દરમિયાન સાઇટ વિઝિટ શેડ્યૂલ કરવા માંગો છો?"
        }
        return {
            "reply": replies.get(lang, replies["en"]),
            "action": "TRIGGER_HANDOFF",
            "reason": "Buyer requested human salesperson",
            "is_uncertain": False,
            "facts_used": [],
            "extracted_preferences": prefs,
            "language": lang
        }

    # 2. Check for Discount / Negotiation Demand (Safety Rule 3 & 6)
    if any(k in lower for k in DISCOUNT_KEYWORDS):
        replies = {
            "en": "Our projects offer competitive, transparent pricing in accordance with Gujarat RERA norms. Specific festive offers, floor rise adjustments, and payment schedules are confirmed exclusively in person with our sales executive. Would you like to schedule a site visit to discuss pricing?",
            "hi": "हमारे प्रोजेक्ट्स में गुजरात रेरा (GujRERA) मानकों के तहत पारदर्शी कीमतें हैं। विशेष फेस्टिव ऑफर्स और भुगतान योजना केवल हमारे सेल्स एग्जीક्यूटिव द्वारा आमने-सामने तय की जाती हैं। क्या आप साइट विઝिट का समय चुनना चाहेंगे?",
            "gu": "અમારા પ્રોજેક્ટ્સમાં ગુજરાત રેરા (GujRERA) ધોરણો મુજબ પારદર્શક કિંમતો છે. ખાસ ફેસ્ટિવ ઓફર્સ અને પેમેન્ટ સ્કેડ્યુલ સેલ્સ એક્ઝિક્યુટિવ સાથે રૂબરૂમાં નક્કી કરવામાં આવે છે. શું તમે સાઇટ વિઝિટ શેડ્યૂલ કરવા માંગો છો?"
        }
        return {
            "reply": replies.get(lang, replies["en"]),
            "action": "OFFER_SITE_VISIT",
            "reason": "Discount negotiation inquiry (strictly unapproved pricing protected)",
            "is_uncertain": True,
            "facts_used": [],
            "extracted_preferences": prefs,
            "language": lang
        }

    # 3. Check for Site Visit Booking Intent
    if any(k in lower for k in BOOKING_KEYWORDS):
        replies = {
            "en": "We would be delighted to host you for a private site tour and sample flat walkthrough at Company A properties. I have opened our genuine available visit slots below. Please choose your preferred date and time.",
            "hi": "हमें कंपनी ए (Company A) के प्रोजेक्ट्स पर आपका स्वागत करने में खुशी होगी। नीचे वास्तविक उपलब्ध स्लॉટ્સ प्रदर्शित हैं। कृपया अपनी सुविधा अनुसार तारीख और समय चुनें।",
            "gu": "કંપની એ (Company A) ના પ્રોજેક્ટ્સ પર સેમ્પલ ફ્લેટ જોવા માટે આપનું હાર્દિક સ્વાગત છે. નીચે વાસ્તવિક ઉપલબ્ધ સ્લોટ્સ આપેલા છે. કૃપા કરીને તમારી અનુકૂળતા મુજબ તારીખ અને સમય પસંદ કરો."
        }
        return {
            "reply": replies.get(lang, replies["en"]),
            "action": "SHOW_BOOKING_SLOTS",
            "is_uncertain": False,
            "facts_used": [],
            "extracted_preferences": prefs,
            "language": lang
        }

    # 4. Check for Greeting
    greeting_triggers = ["hi", "hello", "hey", "namaste", "kem cho", "kaise ho", "halo", "pranam", "good morning", "good evening"]
    is_greeting = any(g in lower for g in greeting_triggers) and not any(kw in lower for kw in ["bhk", "sqft", "price", "amenit", "rera", "carpet"])
    if is_greeting:
        replies = {
            "en": "Namaste! Welcome to Company A, residential developers in Ahmedabad. We have two premium residential projects: Harmony Enclave in Shela (₹65L–₹95L) and Skyline Serenity on SG Highway (₹85L–₹1.2Cr). Are you interested in a 2 BHK or 3 BHK apartment?",
            "hi": "नमस्ते! अहमदाबाद में कंपनी ए (Company A) के आवासीय प्रोजेक्ट्स में आपका स्वागत है। हमारे पास दो प्रीमियम प्रोजेक्ट्स हैं: शीला में 'हार्मनी एन्क्लेव' (₹65 लाख - ₹95 लाख) और एस.जी. हाईवे पर 'स्काईलाइन सेरेनिटी' (₹85 लाख - ₹1.2 करोड़)। क्या आप 2 BHK या 3 BHK में रुचि रखते हैं?",
            "gu": "નમસ્તે! અમદાવાદમાં કંપની એ (Company A) ના રેસિડેન્શિયલ પ્રોજેક્ટ્સમાં આપનું સ્વાગત છે. અમારી પાસે બે પ્રીમિયમ પ્રોજેક્ટ્સ છે: શેલા ખાતે 'હાર્મની એન્ક્લેવ' (₹65 લાખ - ₹95 લાખ) અને એસ.જી. હાઇવે પર 'સ્કાયલાઇન સેરેનિટી' (₹85 લાખ - ₹1.2 કરોડ). તમે 2 BHK કે 3 BHK માં રસ ધરાવો છો?"
        }
        return {
            "reply": replies.get(lang, replies["en"]),
            "action": "PROMPT_CONFIG",
            "is_uncertain": False,
            "facts_used": [],
            "extracted_preferences": prefs,
            "language": lang
        }

    # 5. Fact Sheet Retrieval Match (Strict Grounding)
    matched_facts = retrieve_relevant_facts(db, user_message, project_id)

    if matched_facts:
        fact_texts = [f["content"] for f in matched_facts[:2]]
        project_names = list(set(f["project_name"] for f in matched_facts))
        rera_nums = list(set(f["rera_number"] for f in matched_facts))

        combined_facts = " ".join(fact_texts)
        rera_mention = f" (GujRERA Reg: {', '.join(rera_nums)})" if rera_nums else ""

        if lang == "gu":
            reply = f"અમારા પ્રોજેક્ટની માન્ય માહિતી મુજબ: {combined_facts}{rera_mention} શું તમે સેમ્પલ ફ્લેટ જોવા માટે સાઇટ વિઝિટ બુક કરવા માંગો છો?"
        elif lang == "hi":
            reply = f"हमारे प्रोजेक्ट की स्वीकृत जानकारी के अनुसार: {combined_facts}{rera_mention} क्या आप सैंपल फ्लैट देखने के लिए साइट विज़िट बुक करना चाहेंगे?"
        else:
            reply = f"According to our approved project specifications for {', '.join(project_names)}: {combined_facts}{rera_mention} Would you like to schedule a site visit to experience the project in person?"

        return {
            "reply": reply,
            "action": "OFFER_SITE_VISIT",
            "is_uncertain": False,
            "facts_used": [f["fact_id"] for f in matched_facts],
            "extracted_preferences": prefs,
            "language": lang
        }

    # 6. Preference Capture (e.g., buyer just told us 3 BHK or 80 Lakh)
    if prefs.get("preferred_bhk") or prefs.get("budget_max"):
        bhk = prefs.get("preferred_bhk", "apartment")
        replies = {
            "en": f"Thank you! We have excellent {bhk} options at Harmony Enclave (Shela) starting from ₹65 Lakh, and Skyline Serenity (SG Highway) starting from ₹85 Lakh. Both feature approved master layouts with modern amenities. Would you like to schedule a site visit this week?",
            "hi": f"धन्यवाद! हमारे पास शीला (Shela) स्थित 'हार्मनी एन्क्लेव' में ₹65 लाख से और एस.જી. हाईवे स्थित 'स्काईलाइन सेरेनिटी' में ₹85 लाख से बेहतरीन {bhk} विकल्प उपलब्ध हैं। क्या आप इस सप्ताह साइट विઝિટ बुक करना चाहेंगे?",
            "gu": f"આભાર! અમારી પાસે શેલા સ્થિત 'હાર્મની એન્ક્લેવ' માં ₹65 લાખથી અને એસ.જી. હાઇવે સ્થિત 'સ્કાયલાઇન સેરેનિટી' માં ₹85 લાખથી ઉત્કૃષ્ટ {bhk} વિકલ્પો ઉપલબ્ધ છે. શું તમે આ અઠવાડિયે સાઇટ વિઝિટ શેડ્યૂલ કરવા માંગો છો?"
        }
        return {
            "reply": replies.get(lang, replies["en"]),
            "action": "OFFER_SITE_VISIT",
            "is_uncertain": False,
            "facts_used": [],
            "extracted_preferences": prefs,
            "language": lang
        }

    # 7. Unverified Query Fallback (Safety Rule 6 & 7: Never Hallucinate)
    unverified_replies = {
        "en": "I want to be completely accurate with you: that specific information is not currently listed in our approved project fact sheet. I have noted your question, and our sales executive will confirm this detail for you directly. Would you like to schedule a site visit to see the project first-hand?",
        "hi": "मैं आपको बिल्कुल सटीक जानकारी देना चाहता हूँ: यह विशिष्ट विवरण हमारे वर्तमान स्वीकृत प्रोजेक्ट फैक्ट शीट में दर्ज नहीं है। मैंने आपका प्रश्न नोट कर लिया है, और हमारे सेल्स एग्जीક्यूटिव सीधे इसकी पुष्टि करेंगे। क्या आप साइट विઝિટ बुक करना चाहेंगे?",
        "gu": "હું તમને તદ્દન સાચી માહિતી આપવા માંગુ છું: આ ચોક્કસ વિગત અમારી મંજૂર પ્રોજેક્ટ ફેક્ટ શીટમાં હાલ ઉપલબ્ધ નથી. મેં તમારી પૃચ્છા નોંધી લીધી છે અને અમારા સેલ્સ એક્ઝિક્યુટિવ તમને આ અંગે પુષ્ટિ કરશે. શું તમે સાઇટ વિઝિટ બુક કરવા માંગો છો?"
    }
    return {
        "reply": unverified_replies.get(lang, unverified_replies["en"]),
        "action": "FLAGGED_FOR_REVIEW",
        "reason": f"Inquiry outside approved fact sheet: '{user_message}'",
        "is_uncertain": True,
        "facts_used": [],
        "extracted_preferences": prefs,
        "language": lang
    }

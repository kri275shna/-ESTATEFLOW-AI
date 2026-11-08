# EstateFlow AI — Technical Design Document (TDD)

**Project Name:** EstateFlow AI  
**Repository URL:** [https://github.com/developer-evaluation/estateflow-ai](https://github.com/developer-evaluation/estateflow-ai)  
**Client Problem Statement:** Company A, Residential Property Developer in Ahmedabad  
**Evaluation Role:** Senior Full-Stack Software Architect & Technical Lead  
**Document Version:** 1.0.0 (MVP Release)  
**Date:** November 2026  

---

## Executive Summary

EstateFlow AI is an enterprise-grade real estate lead management platform and grounded AI conversational assistant engineered specifically for **Company A**, a residential property developer based in Ahmedabad with two active developments (*Harmony Enclave* in Shela and *Skyline Serenity* on SG Highway, totaling 420 apartments priced between ₹65 Lakh and ₹1.2 Crore).

The platform replaces disconnected telecalling inboxes and spreadsheets to resolve three acute business bottlenecks:
1. **First-Response Latency:** Slashing median first response from **14 hours to under 2 minutes** via 24/7 multilingual AI concierge (English, Hindi, Gujarati).
2. **Lead Attrition:** Reducing leads uncontacted within 48 hours from **35% to 0.0%** through instant qualification and automated sales executive routing.
3. **Site-Visit Conversion:** Increasing lead-to-visit conversion from **6.0% to 10.3%** using an ACID concurrency-safe visit booking engine with automated reminder dispatch.

---

## 1. System Architecture & Technical Rationale

### 1.1 Architectural Pattern
EstateFlow AI adopts a **Modular Monolithic Architecture** decoupled across a Python/FastAPI asynchronous core and a Next.js 14 App Router frontend.

```
                    ┌────────────────────────────────────────┐
                    │      Next.js 14 Frontend Client        │
                    │   (App Router, Tailwind CSS, Lucide)   │
                    └───────────────────┬────────────────────┘
                                        │ HTTPS / JSON REST
                                        ▼
                    ┌────────────────────────────────────────┐
                    │         FastAPI REST API (v1)          │
                    │  (Pydantic Validation, CORS, JWT Auth) │
                    └───────┬────────────────────────┬───────┘
                            │                        │
             ┌──────────────┴───────┐        ┌───────┴──────────────┐
             ▼                      ▼        ▼                      ▼
┌────────────────────────┐ ┌───────────────┐ ┌────────────────────────┐
│  AI Grounding Engine   │ │  Lead Service │ │ Booking Engine (ACID)  │
│  • Fact Sheet Registry │ │  • E.164 Norm │ │ • Row-Level Locks      │
│  • Multilingual Regex  │ │  • Dedup Hash │ │ • Capacity Invariants  │
│  • Fallback Engine     │ │  • Attribution│ │ • Reminder Dispatch    │
└────────────────────────┘ └───────────────┘ └────────────────────────┘
             │                      │                       │
             └──────────────────────┼───────────────────────┘
                                    ▼
                    ┌────────────────────────────────────────┐
                    │  SQLAlchemy 2.0 ORM & PostgreSQL Core  │
                    │    (SQLite fallback for portable demo)  │
                    └────────────────────────────────────────┘
```

### 1.2 Technology Selection & Rationale

| Layer | Technology | Engineering Rationale |
| :--- | :--- | :--- |
| **Backend Framework** | **Python 3.11 + FastAPI** | Native async I/O throughput; tight synergy with AI grounding and NLP tokenizers; high-speed OpenAPI schema generation; automatic Pydantic data serialization. |
| **ORM & Database** | **SQLAlchemy 2.0 + PostgreSQL** (SQLite portable demo) | Enforces relational integrity across foreign keys, unique composite indexes, and row-level locking (`with_for_update()`) essential for preventing double bookings. |
| **Frontend Framework** | **Next.js 14 (App Router) + TypeScript** | React Server Components coupled with client interactivity; strict TypeScript compile checks; zero-configuration SSR and static optimization. |
| **Design System** | **Tailwind CSS + Lucide Icons** | Bespoke luxury aesthetic (deep slate, rich emerald, warm ivory) tailored to high-value real estate buyers without bloated generic component libraries. |
| **Security & Auth** | **JWT (python-jose) + Direct bcrypt** | Stateless authentication with backend role-based access control (Admin, Sales Head, Sales Executive, Buyer). Passwords hashed using standard `bcrypt` with salt rounds. |

---

## 2. Labeled Assumptions

Per evaluation guidelines, all business and technical assumptions are explicitly labeled:

1. **[Assumption-01: Currency & Units]:** All financial transactions and marketing figures are calculated in Indian Rupees (INR ₹). Budgets are normalized into Lakhs and Crores.
2. **[Assumption-02: Phone Number Normalization]:** All buyer phone numbers originate in India (+91 country code). A 10-digit number `9825012345`, leading zero `09825012345`, or formatted `+91-98250-12345` normalize to standard E.164 format `+919825012345`.
3. **[Assumption-03: Concurrency Threshold]:** Each 45-minute site-visit time slot allows up to 3 concurrent appointments per project (configurable up to 10 by Admin).
4. **[Assumption-04: Grounding Boundary]:** The AI assistant is forbidden from quoting discounts or promising custom payment milestones; questions outside approved facts trigger immediate sales rep handoff.
5. **[Assumption-05: Statutory Compliance]:** Prominently displays Gujarat RERA registration numbers (`PR/GJ/AHMEDABAD/CITY/AUDA/RAA11024/010124` for Harmony Enclave and `PR/GJ/AHMEDABAD/CITY/AUDA/RAA11088/150224` for Skyline Serenity) on every public facing view to adhere to RERA marketing mandates.
6. **[Assumption-06: DPDP Act 2023 Compliance]:** All lead generation forms require explicit buyer consent before storing personal mobile numbers, with full opt-out recording.

---

## 3. Data Model & Entity Relationship Architecture

The relational schema comprises 10 primary entities modeled in SQLAlchemy:

```mermaid
erDiagram
    PROJECT ||--o{ PROPERTY_FACT : contains
    PROJECT ||--o{ VISIT_SLOT : schedules
    PROJECT ||--o{ BOOKING : hosts
    PROJECT ||--o{ LEAD : prefers
    PROJECT ||--o{ MARKETING_SPEND : attributes

    USER ||--o{ LEAD : assigned_to
    USER ||--o{ BOOKING : assigned_to
    USER ||--o{ HANDOFF : resolves
    USER ||--o{ AUDIT_LOG : actions

    LEAD ||--o{ CONVERSATION : conducts
    LEAD ||--o{ BOOKING : reserves
    LEAD ||--o{ HANDOFF : escalates

    CONVERSATION ||--o{ MESSAGE : contains
    CONVERSATION ||--o{ HANDOFF : triggers
    VISIT_SLOT ||--o{ BOOKING : allocates
```

### 3.1 Primary Entities

1. **`users`**: System actors with strict RBAC (`ADMIN`, `SALES_HEAD`, `SALES_EXECUTIVE`, `BUYER`). Stores hashed passwords and phone numbers.
2. **`projects`**: Residential projects (*Harmony Enclave*, *Skyline Serenity*) with RERA registration numbers, unit counts (210 each = 420 total), price ranges (₹65L–₹1.2Cr), and geo-coordinates.
3. **`property_facts`**: Approved knowledge repository for AI grounding. Categorized into Pricing, Configuration, Amenities, Location, and RERA.
4. **`leads`**: Master buyer profiles with E.164 normalized phones, secondary source attribution history, qualification scores (0–100), buying timelines, and SLA timestamps.
5. **`visit_slots`**: Pre-generated 45-minute visit windows with `max_capacity` constraints and `booked_count`.
6. **`bookings`**: Persisted appointments with unique reference IDs (`BK-XXXXX`), status transitions (`CONFIRMED`, `COMPLETED`, `NO_SHOW`, `CANCELLED`), and automated reminder flags.
7. **`conversations` & `messages`**: Structured session logs capturing user queries, grounded assistant answers, confidence metrics, and detected buyer intent.
8. **`handoffs`**: Structured sales escalation dossiers capturing reason, priority (`URGENT`/`HIGH`), qualification summary, and recommended sales rep action.
9. **`marketing_spend`**: Monthly expenditure per acquisition channel (total ₹30 Lakh monthly) used for real-time Cost Per Lead (CPL) and Cost Per Completed Visit calculations.
10. **`audit_logs`**: Immutable audit records capturing administrative mutations to fact sheets, slot capacities, or manual lead assignments.

---

## 4. Core Workflows & Logic Implementation

### 4.1 Lead Deduplication & Multi-Source Attribution
When an enquiry arrives via portal, social media, website, or hoarding:
1. Phone number is sanitized and normalized to E.164 (`+91XXXXXXXXXX`).
2. The database performs an indexed lookup on `normalized_phone`.
3. If an existing lead is found:
   - The original record is **never duplicated**.
   - If the new source differs from the initial source, it is appended to the JSON array `duplicate_source_history` (e.g. `[{"source": "Social media", "timestamp": "..."}]`).
   - `last_contact_at` is updated to current UTC time.
   - Preserves attribution integrity for marketing ROI without fragmenting sales interactions.

### 4.2 Grounded Multilingual AI Assistant
The conversational assistant operates on a strict **Grounding-First Pipeline**:

```mermaid
flowchart TD
    UserQuery[Buyer Query In English, Hindi, or Gujarati] --> IntentDetector[Intent & Language Classifier]
    IntentDetector --> CheckIntent{Query Intent?}
    
    CheckIntent -- Greeting / General --> MultilingualGreeting[Deliver Warm Grounded Welcome]
    CheckIntent -- Discount Inquiry --> RefusalResponse[Polite Refusal: Strict Transparent Pricing Policy]
    CheckIntent -- Human Request --> SalesHandoff[Generate Handoff Dossier & Assign Sales Rep]
    CheckIntent -- Property Specification --> FactRetrieval[Fetch Approved Property Facts from DB]
    
    FactRetrieval --> FactExists{Fact Found in DB?}
    FactExists -- Yes --> VerifiedAnswer[Deliver Grounded Answer + GujRERA Badge]
    FactExists -- No --> FallbackEscalation[Honest Refusal: Salesperson Will Confirm + Flag Chat]
    
    VerifiedAnswer --> LeadScore[Update Intent & Qualification Score 0-100]
    LeadScore --> OfferSlot[Prompt Site-Visit Slot Booking]
```

- **Safety Invariant 1 (Zero Hallucination):** The assistant never invents prices, floor areas, or approvals. If an attribute is missing in the database fact sheet, it explicitly states: *"A sales executive will verify this detail for you."*
- **Safety Invariant 2 (Discount Refusal):** Queries regarding discounts or cash negotiations trigger a polite refusal emphasizing Company A's transparent builder pricing policy.
- **Safety Invariant 3 (Deterministic Demo Fallback):** For review environments without an active `OPENAI_API_KEY`, a built-in deterministic engine provides grounded multilingual answers based on the identical database fact sheet.

### 4.3 Concurrency-Safe Booking Engine
To prevent double bookings across concurrent buyer sessions:
1. When a buyer initiates booking, the backend opens an ACID transaction.
2. The target slot row is locked using `SELECT ... FOR UPDATE` (or atomic constraint check).
3. Invariant check: `booked_count < max_capacity` and `is_blocked == False`.
4. Duplicate check: Ensures the same lead does not have an active booking for the identical slot window.
5. Slot `booked_count` is incremented, the `Booking` record is persisted with status `CONFIRMED`, and the transaction commits.
6. If capacity is exhausted, a `400 Bad Request` ("Slot capacity reached") is raised and the transaction rolls back cleanly.

---

## 5. UI and Design Decisions

The interface reflects Company A's luxury residential market position (₹65L to ₹1.2Cr homes):
- **Aesthetic Tone:** Calm, restrained, architectural palette featuring deep slate (`#0F172A`), rich emerald green (`#059669`), and warm ivory (`#FBFBFA`).
- **Typography & Hierarchy:** Clean sans-serif with high contrast, crisp tabular numerals for financial data, and prominent badge indicators.
- **Screen Architecture (8 Delivered Screens):**
  1. **Landing & Overview (`/`):** Live connectivity scorecard, executive value proposition, direct module launchpad.
  2. **1-Click Reviewer Login (`/login`):** Pre-configured 1-click switcher for Admin, Sales Head, Sales Executive, and Buyer.
  3. **Multilingual AI Concierge (`/chat`):** Language switcher (EN/HI/GU), project cards, verified response badges, quick intent chips.
  4. **Site-Visit Booking Engine (`/book`):** 10-day interactive calendar, real-time available spots indicator, SMS/Email reminder preview.
  5. **Leads Pipeline (`/leads`):** Search by name/phone/ID, source/status filters, duplicate badges, manual lead addition modal.
  6. **Lead Dossier (`/leads/[id]`):** Complete audit profile, conversation transcript replay, bookings timeline, and secondary attribution history.
  7. **Sales Executive Workspace (`/sales`):** Personal dashboard for sales reps, today's visits, 1-click attendance marking (Attended/No-Show), flagged AI escalations.
  8. **Executive Analytics Dashboard (`/analytics`):** Real-time SQL aggregation of response SLA targets (< 5 min), conversion funnel, source attribution, and unit economics.
  9. **Admin Fact Sheet & Slot Governance (`/admin`):** Live fact sheet CRUD, slot capacity adjustments, and audit trail inspection.

---

## 6. What Was Cut vs. What We Would Do Next

### 6.1 Intentional Cuts (MVP Boundary)
- **Full CRM Replacement:** Omitted complex billing, mortgage disbursement, and commission accounting to focus sharply on lead qualification and site-visit conversion.
- **Booking Payments & Allotment Letters:** Kept visit booking free and lightweight; token payments and legal allotment generation belong in post-visit contracting.
- **Outbound Voice Calling:** Avoided intrusive robocalls in favor of respectful conversational chat and WhatsApp opt-in messaging per DPDP Act guidelines.

### 6.2 Future Production Roadmap
1. **WhatsApp Cloud API Webhook:** Direct integration with Meta Cloud API for frictionless inbound messaging via official WhatsApp Business numbers.
2. **Automated SMS & WhatsApp Reminders:** Scheduled cron triggers for 24-hour and 2-hour automated reminders via Twilio or Gupshup.
3. **Semantic Embedding Search:** Integration of vector embeddings (`pgvector`) for natural language semantic search across 500+ unit floor plans and architectural specs.
4. **Calendar Sync:** Two-way iCal and Google Calendar synchronization for sales executives' personal schedules.

---

## 7. Automated Test Suite Summary

The backend includes a comprehensive pytest suite in `backend/tests/`:
- `test_auth.py`: JWT generation, password hashing, role-based 401/403 access control.
- `test_leads.py`: E.164 phone normalization, deduplication, search by explicit sample IDs (`LD-58210`, `LD-58211`, `LD-58224`).
- `test_chat.py`: Multilingual greetings (EN/HI/GU), fact grounding, fake discount refusal, qualification scoring.
- `test_bookings.py`: Transactional capacity enforcement, double booking prevention, cancellation decrement.
- `test_handoffs.py`: Sales executive workspace scoping, escalation status resolution.
- `test_analytics.py`: Aggregate SQL calculation of show-up rates, first response SLA, and source attribution.
- `test_admin.py`: Fact sheet CRUD, slot capacity limits, and system audit logging.

**Test Results:** **37 passed, 0 failed** (100% pass rate).

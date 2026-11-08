# EstateFlow AI — Deployment & Local Setup Guide

> **Client:** Company A, Residential Property Developer (Ahmedabad, Gujarat)  
> **Repository:** [https://github.com/kri275shna/-ESTATEFLOW-AI](https://github.com/kri275shna/-ESTATEFLOW-AI)  
> **Specification:** End-to-End Real Estate Lead Management & AI Assistant MVP  
> **Compliance:** Gujarat RERA & Digital Personal Data Protection (DPDP) Act 2023  

---

## 1. Demo Credentials for Reviewers

The database is pre-seeded with realistic Ahmedabad residential developer sample data (2 projects: *Harmony Enclave* in Shela and *Skyline Serenity* on SG Highway; 420 apartments aggregate; 11 sales reps; 29 leads including explicit records `LD-58210`, `LD-58211`, `LD-58224`; 132 visit slots; and marketing attribution).

| Role | Email Address | Password | Capabilities & Access Scope |
| :--- | :--- | :--- | :--- |
| **Admin (Director)** | `admin@estateflow.ai` | `Admin@123` | Full system governance, fact sheet CRUD, visit slot capacity, audit log review, user management |
| **Sales Head** | `saleshead@estateflow.ai` | `Head@123` | All leads, manual assignment, AI flagged conversation review, executive analytics KPI dashboard |
| **Sales Executive** | `rahul.sales@estateflow.ai` | `Sales@123` | Personal workspace, assigned leads only, today's visits, 1-click attendance marking (Attended/No-show) |
| **Buyer (Public)** | `buyer@estateflow.ai` | `Buyer@123` | Public multilingual AI chat (EN, HI, GU), browse approved facts, real-time site-visit booking |

> **Reviewer Convenience Feature:** On the login page (`/login`), you can click any of the 4 **"1-Click Reviewer Quick Fill"** buttons to log in instantly without typing passwords.

---

## 2. Local Setup (Step-by-Step)

### Prerequisites
- **Python 3.11+** installed
- **Node.js 18+** and **npm** installed
- **Git**

### Step A: Clone the Repository
```bash
git clone https://github.com/kri275shna/-ESTATEFLOW-AI.git
cd -ESTATEFLOW-AI
```

### Step B: Backend Setup (FastAPI & SQLAlchemy)
```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate a Python virtual environment
python -m venv venv

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize and seed database with sample data
python app/core/seed.py

# 5. Start the FastAPI development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend API and Swagger interactive documentation will be live at:
- **API Base:** `http://localhost:8000`
- **Swagger Docs:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/api/v1/health`

### Step C: Frontend Setup (Next.js 14 App Router)
Open a new terminal window:
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install Node dependencies
npm install

# 3. Run production build (or development server)
npm run dev
```
The frontend web application will be accessible at:
- **Frontend App:** `http://localhost:3000`

---

## 3. Running Automated Tests

Run the full pytest suite verifying Authentication, E.164 deduplication, Grounded Multilingual AI Assistant, ACID Booking Concurrency, Sales Handoffs, and Analytics:

```bash
cd backend
python -m pytest tests/ -v
```
All **37 test suites** execute with 100% pass rate.

---

## 4. Docker Deployment (Optional Alternative)

If you prefer running via Docker Compose:

```bash
# Build and launch all services (PostgreSQL, FastAPI Backend, Next.js Frontend)
docker-compose up --build -d

# Check running containers
docker-compose ps

# To stop the containers
docker-compose down
```

Services will be mapped to:
- **Frontend:** `http://localhost:3000`
- **Backend API:** `http://localhost:8000`
- **PostgreSQL Database:** `localhost:5432`

---

## 5. Environment Variables

Below is the complete list of environment variables required by the services.  
*(Per submission rules, variable names only are listed below; no real secrets are stored in this repository).*

### Backend Environment Variables (`backend/.env`)
| Variable Name | Description | Default / Example Purpose |
| :--- | :--- | :--- |
| `PROJECT_NAME` | Name of the deployed MVP application | `EstateFlow AI` |
| `ENVIRONMENT` | Deployment environment mode | `development` / `production` |
| `DATABASE_URL` | SQLAlchemy connection string | SQLite for local demo, PostgreSQL for production |
| `SECRET_KEY` | Secret key used for signing JWT tokens | Cryptographically random string |
| `ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiration duration in minutes | `1440` (24 hours) |
| `CORS_ORIGINS` | Allowed frontend origins for CORS | `http://localhost:3000` |
| `OPENAI_API_KEY` | Optional LLM provider API key | Grounded fallback engine active if omitted |
| `OPENAI_MODEL` | LLM model identifier | `gpt-4o-mini` |

### Frontend Environment Variables (`frontend/.env.local`)
| Variable Name | Description | Default / Example Purpose |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | Backend REST API endpoint URL | `http://localhost:8000/api/v1` |

---

## 6. Project Architecture Overview

```
estateflow-ai/
├── backend/
│   ├── app/
│   │   ├── ai/            # Grounding engine, multilingual intent detector, LLM provider
│   │   ├── api/           # Versioned REST API endpoints (v1)
│   │   ├── core/          # Config, security (bcrypt/JWT), phone normalization, seeding
│   │   ├── models/        # SQLAlchemy database entity models
│   │   ├── schemas/       # Pydantic request/response validation schemas
│   │   └── services/      # Business logic: deduplication, transactional booking lock
│   ├── tests/             # Pytest integration & unit test suite (37 tests)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js 14 App Router pages (/, /chat, /book, /leads, /sales, /analytics, /admin)
│   │   ├── components/    # Reusable UI components & navigation
│   │   └── lib/           # Auth tokens, API client helpers
│   ├── Dockerfile
│   └── package.json
├── docs/                  # Technical Design Document (TDD.md, TDD.pdf, TDD.docx)
├── docker-compose.yml
└── deployment.md
```

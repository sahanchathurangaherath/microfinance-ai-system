<div align="center">

# 🏦 Microfinance Management AI System

**Semi-Automated · AI-Assisted · Human-Controlled**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2-092E20?style=flat&logo=django&logoColor=white)](https://djangoproject.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.0_Flash-4285F4?style=flat&logo=google&logoColor=white)](https://ai.google.dev)

<br/>

> **AI assists. Humans decide. System records everything.**

A full-stack microfinance loan management platform with 6 AI agents that assist  
human officers across the complete client and loan lifecycle — from KYC onboarding  
through risk scoring, approval, disbursement, repayment tracking, fraud detection,  
and collections.

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [AI Agents](#-ai-agents)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Environment Variables](#-environment-variables)
- [Running the Services](#-running-the-services)
- [LLM Upgrade](#-llm-upgrade)
- [API Overview](#-api-overview)
- [Role System](#-role-system)
- [Loan Lifecycle](#-loan-lifecycle)
- [Phase Build Order](#-phase-build-order)
- [Testing](#-testing)
- [Documents](#-documents)

---

## 🔍 Overview

The Microfinance Management AI System manages the complete loan lifecycle for a
microfinance institution. Six AI agents run alongside human officers — each agent
assists, recommends, or alerts — but never takes autonomous action.

### What It Does

| Module | What Happens |
|---|---|
| Client Onboarding & KYC | A1 agent validates data completeness and consistency |
| Loan Application | Officers create and submit applications for AI screening |
| Risk Assessment | A2 agent scores creditworthiness 0–100 with full rationale |
| Recommendation | A3 agent recommends approve / reject / reduce / escalate |
| Approval Workflow | Analyst → Manager → Committee human approval chain |
| Disbursement | Finance staff process with manager sign-off |
| Repayment Tracking | A4 agent scans portfolio daily, classifies arrears |
| Collections | Officers work delinquency cases flagged by A4 |
| Fraud Detection | A5 agent runs 9 signal checks + LLM prosecutor/defense debate |
| Communications | A6 agent drafts personalized SMS/email for officer approval |
| Reporting | Role-based dashboards, KPI tracking, CSV export |
| Audit | Immutable logs for every agent action and human decision |
| Manual Mode | Full AI failure handling — system continues without AI |

### Core Principles

```
1. Build a strong operational core first — before introducing AI behavior
2. AI agents assist and recommend — human officers control all final decisions
3. High-stakes financial decisions remain under explicit business rules during MVP
4. Expand automation only where performance, explainability, and governance are proven
```

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Next.js Frontend                          │
│             TypeScript · Tailwind CSS · Port 3000            │
└──────────────────────────┬───────────────────────────────────┘
                           │  REST API (JWT)
┌──────────────────────────▼───────────────────────────────────┐
│                  Django + DRF Backend                        │
│                        Port 8000                             │
│                                                              │
│  users · clients · kyc · loans · repayments · approvals      │
│  collections · fraud · notifications · reports · audit       │
└─────────────────┬────────────────────────┬───────────────────┘
                  │ httpx + API Key         │ ORM
      ┌───────────▼──────────┐  ┌──────────▼─────────────┐
      │ FastAPI AI Service   │  │   PostgreSQL 15         │
      │      Port 8001       │  │      Port 5432          │
      │                      │  │                         │
      │  A1 · A2 · A3        │  │   50+ tables            │
      │  A4 · A5 · A6        │  │   11 domain schemas     │
      │  Gemini Client       │  └─────────────────────────┘
      │  Guardrails          │
      └──────────────────────┘
               │
       ┌───────▼────────┐
       │   Gemini API   │
       │ 2.0 Flash SDK  │
       └────────────────┘
```

**Key design rule:** Django is the only service that calls FastAPI.
FastAPI never calls Django and never writes directly to the database.
All AI outputs return as structured JSON — Django saves them through
the ORM with full audit logging.

---

## 🤖 AI Agents

| ID | Agent | Pattern | Key Output | KPI Target |
|---|---|---|---|---|
| A1 | Data Collection | Full LLM | KYC quality score + consistency flags | Accuracy ≥ 98% |
| A2 | Risk Assessment | Full LLM (ReAct) | Risk score 0–100 + full rationale | Prediction ≥ 90% |
| A3 | Recommendation | Full LLM (Few-Shot) | APPROVE / REJECT / REDUCE / ESCALATE | Acceptance ≥ 85% |
| A4 | Monitoring | Hybrid — Rule + LLM | Overdue cases + behaviour pattern | Alert accuracy ≥ 95% |
| A5 | Fraud Detection | Hybrid — Rule + LLM | Fraud score + prosecutor/defense debate | Detection ≥ 90% |
| A6 | Communication | Full LLM (multilingual) | Personalized SMS + email drafts | Delivery ≥ 98% |

### Non-Negotiable Agent Boundaries

```
✗  No agent may approve a loan, waive a penalty, or authorize a disbursement
✗  No customer communication is sent without officer review and confirmation
✗  Low confidence (< 0.65) always escalates — agents never guess
✗  A5 LLM output can only raise fraud severity, never lower it
✗  A6 output goes to NotificationQueue PENDING_APPROVAL — never sends directly
✓  Every agent action stored: timestamp · input hash · output JSON · rationale
```

### Why Two Different Agent Patterns?

**Full LLM** (A1, A2, A3, A6) — used when the decision requires reasoning
across context. Rules cannot detect income inconsistency, seasonal payment
patterns, or appropriate communication tone. Gemini can.

**Hybrid** (A4, A5) — used when the core decision is a deterministic fact.
Whether an installment is overdue is date arithmetic — not a judgment call.
Whether a NIC is duplicated is a database query — not probabilistic.
The rule layer provides the auditable, legally defensible fact.
The LLM layer adds behaviour prediction (A4) and false-positive
reduction (A5) on top.

---

## 🛠 Tech Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Runtime |
| Django + DRF | 4.2 | Core API, ORM, business logic |
| FastAPI | 0.104+ | AI agent service |
| PostgreSQL | 15 | Primary database |
| simplejwt | 5.x | JWT authentication |
| httpx | 0.25+ | Django → FastAPI calls |
| google-genai | 1.75.0 | Gemini 2.0 Flash SDK |
| tenacity | 8.2.3 | LLM retry with backoff |
| python-decouple | 3.8 | Environment config |

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| Next.js | 14 | React SSR staff portal |
| TypeScript | 5.x | Type safety |
| Tailwind CSS | 3.x | UI styling |

### Infrastructure
| Technology | Purpose |
|---|---|
| Docker Compose | All services containerized |
| Uvicorn | FastAPI ASGI server |
| Gunicorn | Django production server |
| Twilio | SMS delivery via A6 |
| Gmail SMTP | Email delivery via A6 |

---

## 📁 Project Structure

```
microfinance-ai-system/
│
├── backend/                         ← Django + DRF
│   ├── config/                      ← Django settings, URLs, WSGI
│   ├── apps/
│   │   ├── users/                   ← Staff accounts, RBAC
│   │   ├── clients/                 ← Client profiles, addresses
│   │   ├── kyc/                     ← KYC checklists, documents
│   │   ├── loans/                   ← Applications, risk, recommendations
│   │   ├── repayments/              ← Schedules, payments, receipts
│   │   ├── approvals/               ← Analyst → Manager → Committee chain
│   │   ├── collections/             ← Delinquency cases, PTP, escalation
│   │   ├── fraud/                   ← Alerts, investigations, compliance
│   │   ├── notifications/           ← Draft queue, approval, delivery log
│   │   ├── reports/                 ← Dashboard, KPIs, CSV export
│   │   └── audit/                   ← Immutable logs, manual mode, incidents
│   ├── requirements.txt
│   └── manage.py
│
├── ai_service/                      ← FastAPI AI Service
│   ├── agents/
│   │   ├── base_agent.py            ← BaseAgent with build_response(), low_confidence_response()
│   │   ├── data_collection_agent.py ← A1 — KYC validation
│   │   ├── risk_assessment_agent.py ← A2 — Risk scoring
│   │   ├── recommendation_agent.py  ← A3 — Loan recommendation
│   │   ├── monitoring_agent.py      ← A4 — Overdue detection
│   │   ├── fraud_detection_agent.py ← A5 — Fraud signals
│   │   └── communication_agent.py  ← A6 — Message drafting
│   ├── services/
│   │   ├── gemini_client.py         ← Gemini 2.0 Flash wrapper + retry
│   │   └── guardrails.py            ← Output validators for all 6 agents
│   ├── data/
│   │   └── recommendation_examples.json  ← Few-shot seed data for A3
│   ├── main.py                      ← FastAPI app, routes, health check
│   └── requirements.txt
│
├── frontend/                        ← Next.js 14
│   ├── app/                         ← App router pages
│   ├── components/                  ← Shared UI components
│   ├── lib/                         ← API client, auth helpers
│   └── package.json
│
├── docs/                            ← All project documentation
│   ├── MASTER_REFERENCE.md
│   ├── PHASE_01 → PHASE_15.md
│   ├── LLM_UPGRADE_PHASE_01_TO_05.md
│   ├── LLM_UPGRADE_PHASE_06_TO_10.md
│   ├── LLM_UPGRADE_PHASE_11_TO_15.md
│   └── MICROFINANCE_AI_SYSTEM_FULL_REPORT.md
│
├── docker-compose.yml
├── .env                             ← Never commit — copy from .env.example
├── .env.example
└── README.md
```

---

## ⚡ Quick Start

### Prerequisites

```bash
python --version    # 3.11+
node --version      # 18+
docker --version    # 24+
docker compose version  # 2.x
```

Install if missing:
- Python → https://python.org/downloads
- Node.js → https://nodejs.org
- Docker Desktop → https://docker.com/products/docker-desktop

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/microfinance-ai-system.git
cd microfinance-ai-system
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in the required values (see [Environment Variables](#-environment-variables)).

### 3. Start the Database

```bash
docker compose up db -d
```

Wait 10 seconds for PostgreSQL to be ready.

### 4. Set Up Django Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Backend running at → `http://localhost:8000`

### 5. Set Up FastAPI AI Service

```bash
# New terminal
cd ai_service
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

AI service running at → `http://localhost:8001`  
API docs at → `http://localhost:8001/docs`

### 6. Set Up Frontend

```bash
# New terminal
cd frontend
npm install
npm run dev
```

Frontend running at → `http://localhost:3000`

### 7. Verify Everything Works

```bash
# Test Django API
curl http://localhost:8000/api/auth/me/
# Expected: 401 Unauthorized (correct — not logged in yet)

# Test AI service health
curl http://localhost:8001/health
# Expected: {"status": "healthy", "agents": 6}

# Test Gemini connection (from ai_service directory)
python -c "
from services.gemini_client import call_gemini
result, _ = call_gemini('You are a test assistant.', 'Return JSON: {\"status\": \"ok\"}')
print(result)
"
# Expected: {'status': 'ok'}
```

### Alternative: Run Everything with Docker

```bash
docker compose up --build
```

All 4 services start together:
- Frontend → `http://localhost:3000`
- Backend → `http://localhost:8000`
- AI Service → `http://localhost:8001`
- Database → `localhost:5432`

---

## 🔧 Environment Variables

Copy `.env.example` to `.env` and fill in all values.

```env
# ── Django ────────────────────────────────────────────────────────
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# ── Database ──────────────────────────────────────────────────────
DB_NAME=microfinance_db
DB_USER=microfinance_user
DB_PASSWORD=microfinance_pass
DB_HOST=localhost
DB_PORT=5432

# ── AI Service ────────────────────────────────────────────────────
AI_SERVICE_URL=http://localhost:8001
AI_SERVICE_API_KEY=your-internal-api-key

# ── JWT ───────────────────────────────────────────────────────────
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# ── Frontend ──────────────────────────────────────────────────────
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# ── LLM (Gemini) ─────────────────────────────────────────────────
GEMINI_API_KEY=your-gemini-api-key
LLM_MODEL=gemini-2.0-flash
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2000
LLM_CONFIDENCE_THRESHOLD=0.65

# ── Per-Agent LLM Flags ───────────────────────────────────────────
# Set false to instantly revert any agent to rule-based logic
A1_USE_LLM=false
A2_USE_LLM=false
A3_USE_LLM=false
A4_USE_LLM=false
A5_USE_LLM=false
A6_USE_LLM=false

# ── Communications ────────────────────────────────────────────────
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

> **Gemini API Key** → https://aistudio.google.com/app/apikey (free tier available)

---

## 🚀 Running the Services

### Development (individual terminals)

```bash
# Terminal 1 — Database
docker compose up db -d

# Terminal 2 — Django Backend
cd backend && python manage.py runserver

# Terminal 3 — FastAPI AI Service
cd ai_service && uvicorn main:app --reload --port 8001

# Terminal 4 — Next.js Frontend
cd frontend && npm run dev
```

### Production (Docker Compose)

```bash
docker compose up --build -d
docker compose logs -f          # Follow all logs
docker compose logs backend -f  # Follow Django only
docker compose down             # Stop all services
```

### Database Migrations

```bash
cd backend

# After any model change
python manage.py makemigrations
python manage.py migrate

# After Phase 9 (A4 new fields on DelinquencyCase)
python manage.py makemigrations collections
python manage.py migrate

# After Phase 11 (A5 new fields on FraudAlert)
python manage.py makemigrations fraud
python manage.py migrate

# After Phase 12 (A6 preferred_language on Client)
python manage.py makemigrations clients
python manage.py migrate

# After Phase 14 (LLM metadata on AgentActionLog)
python manage.py makemigrations audit
python manage.py migrate
```

---

## 🧠 LLM Upgrade

The MVP runs with rule-based agent logic. The LLM upgrade replaces internal
agent reasoning with Gemini — one agent at a time, safely.

### Enable an Agent's LLM Mode

```env
# In .env — flip any flag to true, restart ai_service
A2_USE_LLM=true
```

```bash
# Restart AI service to pick up the flag change
cd ai_service && uvicorn main:app --reload --port 8001
```

### Rollback Instantly

```env
A2_USE_LLM=false   # ← set back to false, restart
```

No code change. No migration. No downtime. Takes 5 seconds.

### Recommended Enable Order

```
1. A2_USE_LLM=true   ← Start here. Highest accuracy impact.
2. A3_USE_LLM=true   ← After A2. A3 reads A2's LLM rationale.
3. A1_USE_LLM=true   ← KYC consistency checks
4. A6_USE_LLM=true   ← Multilingual personalized messaging
5. A5_USE_LLM=true   ← Fraud debate layer (rules always run too)
6. A4_USE_LLM=true   ← Behavioural pattern prediction (rules always run too)
```

### Upgrade Guide Files

| File | Covers |
|---|---|
| `docs/LLM_UPGRADE_PHASE_01_TO_05.md` | gemini_client.py, guardrails.py, A1, A2 |
| `docs/LLM_UPGRADE_PHASE_06_TO_10.md` | A3, A4 (monitoring prediction layer) |
| `docs/LLM_UPGRADE_PHASE_11_TO_15.md` | A5 hybrid, A6 multilingual, audit fields |

---

## 📡 API Overview

### Base URL
```
http://localhost:8000/api/
```

### Authentication
```bash
# Login
POST /api/auth/login/
Body: { "username": "officer1", "password": "pass" }
Response: { "access": "eyJ...", "refresh": "eyJ..." }

# Use token in all requests
Authorization: Bearer eyJ...

# Refresh token
POST /api/auth/refresh/
Body: { "refresh": "eyJ..." }
```

### Key Endpoints by Module

```
# Clients & KYC
POST   /api/clients/                          Register client
POST   /api/clients/{id}/kyc/submit/          Trigger A1 validation

# Loan Applications
POST   /api/loans/applications/               Create application
POST   /api/loans/applications/{id}/submit/   Submit for AI screening
POST   /api/loans/applications/{id}/risk-assess/   Trigger A2
POST   /api/loans/applications/{id}/recommend/     Trigger A3

# Approvals
POST   /api/approvals/{id}/risk-decision/     Analyst decision
POST   /api/approvals/{id}/manager-decision/  Manager decision
POST   /api/approvals/{id}/committee-vote/    Committee vote

# Disbursement & Payments
POST   /api/loans/disbursements/{id}/process/ Process disbursement
POST   /api/payments/                         Post payment

# Portfolio Monitoring
POST   /api/a4/scan/                          Trigger overdue scan
POST   /api/collections/create-from-scan/     Create delinquency cases

# Fraud
POST   /api/fraud/check/                      Trigger A5 check

# Communications
POST   /api/notifications/draft/              Draft via A6
POST   /api/notifications/{id}/approve/       Approve draft
POST   /api/notifications/{id}/send/          Send approved message

# Audit
GET    /api/audit/logs/                       Full audit trail
GET    /api/audit/agent-actions/              AI agent invocations
POST   /api/audit/system/manual-mode/enable/  Enable manual mode

# AI Service
GET    http://localhost:8001/health           AI service health
GET    http://localhost:8001/docs             FastAPI Swagger UI
```

**Total:** 95 endpoints across 13 modules.  
Full API map → `docs/MASTER_REFERENCE.md`

---

## 👥 Role System

8 staff roles with least-privilege RBAC:

| Role | Primary Responsibility |
|---|---|
| `admin` | Full system access, user management |
| `loan_officer` | Client registration, KYC, application submission |
| `risk_analyst` | Credit memo review, risk assessment decisions |
| `branch_manager` | High-risk approvals, escalation handling, exception resolution |
| `credit_committee` | Collective approval for loans above branch threshold |
| `collections_officer` | Delinquency management, PTP recording |
| `compliance_officer` | Fraud investigation, AML/KYC compliance |
| `finance_staff` | Disbursement processing, payment posting |

Create a user with a role:
```bash
cd backend
python manage.py shell
>>> from apps.users.models import User
>>> User.objects.create_user(
...     username='officer1',
...     password='secure123',
...     role='loan_officer'
... )
```

---

## 🔄 Loan Lifecycle

```
Client Registered
    ↓  A1 validates KYC
KYC Complete
    ↓  Loan Officer submits application
DRAFT → SUBMITTED
    ↓  A2 scores risk (0-100, LOW/MEDIUM/HIGH)
    ↓  A3 generates recommendation
AI_SCREENING → RISK_REVIEWED
    ↓  Risk Analyst reviews credit memo
MANAGER_REVIEW
    ↓  Branch Manager approves (small loans stop here)
COMMITTEE_REVIEW
    ↓  Credit Committee votes
APPROVED / REJECTED
    ↓  Finance staff verify conditions + process disbursement
LOAN ACTIVE
    ↓  A4 scans daily — flags overdue installments
    ↓  Collections officers work delinquency cases
    ↓  A5 monitors for fraud signals continuously
    ↓  A6 drafts reminders — officer approves — sent
LOAN CLOSED
```

---

## 📦 Phase Build Order

The system is built phase by phase. Phases 1–5 are complete.

```
✅  Phase 1   Project Setup — Docker, JWT, BaseAgent
✅  Phase 2   Users & Roles — RBAC, login, 8 roles
✅  Phase 3   Client Onboarding & KYC — A1 agent
✅  Phase 4   Loan Applications — status workflow
✅  Phase 5   Risk Assessment — A2 agent, credit memo
⬜  Phase 6   Recommendation — A3 agent, override audit
⬜  Phase 7   Approval Workflow — analyst → manager → committee
⬜  Phase 8   Disbursement — condition checklist, schedule generation
⬜  Phase 9   Repayments — payments, receipts, A4 monitoring
⬜  Phase 10  Collections — delinquency cases, PTP, escalation
⬜  Phase 11  Fraud Detection — A5 agent, investigation workflow
⬜  Phase 12  Communications — A6 agent, multilingual, send approval
⬜  Phase 13  Reporting & Dashboard — KPIs, role-based views, CSV export
⬜  Phase 14  Audit & Security — immutable logs, LLM metadata fields
⬜  Phase 15  Manual Mode — AI failure handling, incident management
⬜  Phase 16-A  LLM: A2 Gemini risk scoring
⬜  Phase 16-B  LLM: A3 few-shot recommendation
⬜  Phase 16-C  LLM: A1 KYC + A5 hybrid + A6 multilingual
⬜  Phase 16-D  Orchestrator: Manager Agent + Shared Memory Bus
```

Each phase has a dedicated guide in `docs/`.

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.loans
python manage.py test apps.audit

# With coverage
pip install coverage
coverage run manage.py test
coverage report
```

### AI Service Tests

```bash
cd ai_service

# Test Gemini connection
python -c "
from services.gemini_client import call_gemini
result, usage = call_gemini('You are a test assistant.', 'Return JSON: {\"status\": \"ok\"}')
print('Output:', result)
print('Tokens:', usage)
"

# Test A2 rule-based (A2_USE_LLM=false)
python -c "
from agents.risk_assessment_agent import RiskAssessmentAgent
agent = RiskAssessmentAgent()
result = agent.run({
    'loan_id': 1,
    'client_data': {'monthly_income': 50000, 'data_quality_score': 85,
                    'years_in_operation': 3, 'number_of_dependents': 2},
    'loan_data': {'requested_amount': 200000, 'requested_duration_months': 24,
                  'debt_to_income_ratio': 0.35},
    'repayment_history': {'previous_loans_count': 2, 'missed_payments': 0}
})
print(result)
"
```

### Postman Collection

Import the Postman collection from `docs/postman/` for all 95 endpoints
with pre-configured environment variables for token management.

Login flow:
1. POST `/api/auth/login/` → copy `access` token
2. Set `Authorization: Bearer {token}` in collection headers
3. Run any endpoint

---

## 📄 Documents

All project documentation is in the `docs/` folder:

| Document | Purpose |
|---|---|
| `MASTER_REFERENCE.md` | Complete API map, DB schema, role matrix |
| `PHASE_01` → `PHASE_15.md` | Step-by-step implementation guide per phase |
| `AI_Agent_Documentation.pdf` | Agent roles, responsibilities, KPI targets |
| `MF_AI_SOP_document.pdf` | SOP MF-AI-SOP-001 — operational procedures |
| `LLM_UPGRADE_PHASE_01_TO_05.md` | Code changes for Phases 1–5 LLM upgrade |
| `LLM_UPGRADE_PHASE_06_TO_10.md` | Code changes for Phases 6–10 LLM upgrade |
| `LLM_UPGRADE_PHASE_11_TO_15.md` | Code changes for Phases 11–15 LLM upgrade |
| `LLM_DESIGN_DECISION_EXPLAINED.md` | Why different agents use different patterns |
| `FULL_LLM_MULTI_AGENT_FINAL_ANSWER.md` | Final architecture decision |
| `MICROFINANCE_AI_SYSTEM_FULL_REPORT.md` | Complete technical project report |

---

## ⚠️ Important Notes

**Never commit `.env`** — it contains your Gemini API key and database credentials.
`.env` is in `.gitignore` by default. Use `.env.example` for sharing config structure.

**LLM flags default to `false`** — the system runs fully on rule-based logic out of the
box. Enable LLM per agent only after testing in your environment.

**Audit logs are immutable** — the system is designed so no officer or admin can
delete or modify audit entries. Do not add delete endpoints to the audit app.

**A5 hybrid is permanent** — the rule-based signal checks in A5 always run regardless
of `A5_USE_LLM`. This is by design for legal and compliance reasons.

---

## 📝 License

Internal project — PlusMark.lk. All rights reserved.

---

<div align="center">

**Built by [PlusMark.lk](https://plusmark.lk)**

*AI assists. Humans decide. System records everything.*

</div>

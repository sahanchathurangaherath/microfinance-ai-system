# Microfinance AI System

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.0.4-092E20?style=flat&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16.2.4-000000?style=flat&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

A full-stack microfinance platform designed for human-in-the-loop loan operations. It combines a Django backend, a FastAPI AI service, and a Next.js staff portal to support KYC, loan origination, approvals, repayments, collections, fraud monitoring, notifications, reporting, and audit logging.

This project is also a strong showcase of my AI engineering skills: agent-based orchestration, LLM integration, structured outputs, human-in-the-loop design, and production-style service architecture.

## Highlights

- End-to-end workflow for client onboarding, KYC review, loan applications, approvals, and repayments
- Django REST API for transactional operations, permissions, and auditability
- FastAPI AI service with six agents for data validation, risk scoring, recommendations, monitoring, fraud checks, and message drafting
- Next.js dashboard for staff-facing workflows and navigation
- Docker-based local environment for rapid setup and service orchestration

## AI skills showcased

- Agentic AI architecture: six specialized agents for distinct business tasks
- LLM integration: FastAPI endpoints designed to call AI models for reasoning and drafting
- Human-in-the-loop design: AI assists decisions, but human review remains central
- Structured outputs: AI responses are shaped for downstream system use rather than free-form chat
- Guardrail thinking: confidence thresholds, safe defaults, and rule-based fallback logic
- Multi-service AI engineering: backend, AI service, and frontend working together as one platform
- Practical software engineering: Dockerized deployment, API design, environment configuration, and modular code structure

## Core modules

- Client and KYC management
- Loan origination and approval stages
- Repayment monitoring and collections
- Fraud detection and notifications
- Reporting and audit logging

## Architecture at a glance

- Backend: Django + DRF
- AI service: FastAPI
- Frontend: Next.js
- Database: PostgreSQL
- Orchestration: Docker Compose

## Tech stack

- Python 3.11+
- Django 6.0.4 + Django REST Framework
- FastAPI
- PostgreSQL 15
- Next.js 16.2.4 + React 19 + TypeScript
- Docker Compose

## Project structure

```text
microfinance-ai-system/
├── backend/                # Django + DRF API and business logic
│   ├── apps/
│   │   ├── users/           # authentication and staff roles
│   │   ├── clients/        # client profiles and contact info
│   │   ├── kyc/            # KYC submissions and document review
│   │   ├── loans/          # loan applications and workflows
│   │   ├── approvals/      # analyst/manager/committee review
│   │   ├── repayments/     # payment schedules and repayment handling
│   │   ├── collections/    # delinquency and follow-up tasks
│   │   ├── fraud/          # fraud checks and investigations
│   │   ├── notifications/  # message drafts and delivery workflows
│   │   ├── reports/        # dashboards and exports
│   │   └── audit/          # immutable audit trail
│   └── config/             # Django settings and URL routing
├── ai_service/             # FastAPI service for AI agents
│   ├── agents/             # A1 to A6 agent implementations
│   ├── services/           # LLM and guardrail helpers
│   └── schemas/            # request/response models
├── frontend/               # Next.js staff portal
├── docker-compose.yml      # local service orchestration
└── README.md
```

## Loan lifecycle

```text
Client registration
   ↓
KYC submission and validation (A1)
   ↓
Loan application created
   ↓
Risk scoring (A2)
   ↓
Recommendation and decision support (A3)
   ↓
Human approval workflow
   ↓
Disbursement and repayment tracking
   ↓
Portfolio monitoring and collections (A4)
   ↓
Fraud detection and communications (A5, A6)
```

## AI agent features

| Agent | Purpose | What it does |
|---|---|---|
| A1 | Data Collection | Reviews client and KYC data for completeness and consistency |
| A2 | Risk Assessment | Produces a risk score and explanation for a loan request |
| A3 | Recommendation | Suggests approve, reject, reduce, or escalate decisions |
| A4 | Monitoring | Flags repayment issues and unusual behavior patterns |
| A5 | Fraud Detection | Checks fraud signals and helps escalate suspicious cases |
| A6 | Communication | Drafts personalized messages for officer review and approval |

## Role system

| Role | Main responsibility |
|---|---|
| admin | Full platform access and system administration |
| loan_officer | Client onboarding and application creation |
| risk_analyst | Review of risk assessments and credit recommendations |
| branch_manager | Approval authority for escalated cases |
| credit_committee | Final governance for high-value requests |
| collections_officer | Delinquency and repayment follow-up |
| compliance_officer | Fraud and compliance review |
| finance_staff | Disbursement and payment processing |

## Run in browser

Once the services are running, open:

- http://localhost:3000 for the frontend dashboard
- http://localhost:8000/api/docs/ for the Django API docs
- http://localhost:8001/docs for the FastAPI AI service docs

## Quick start

### 1. Clone and enter the project

```bash
git clone <repo-url>
cd microfinance-ai-system
```

### 2. Create environment variables

```bash
copy .env.example .env
```

Adjust the values in .env as needed. The example file already contains the local-LLM flags used by the AI service.

### 3. Start PostgreSQL

```bash
docker compose up db -d
```

### 4. Run the backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The API will be available at:
- http://localhost:8000/api/docs/
- http://localhost:8000/admin/

### 5. Run the AI service

```bash
cd ai_service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

Health check:
- http://localhost:8001/health
- http://localhost:8001/docs

### 6. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open the app at:
- http://localhost:3000

## Docker option

```bash
docker compose up --build
```

This starts the database, backend, AI service, and frontend together.

## Environment highlights

The project uses the following key settings from .env:

```env
SECRET_KEY=...
DEBUG=True
DB_NAME=microfinance_db
DB_USER=microfinance_user
DB_PASSWORD=microfinance_pass
AI_SERVICE_URL=http://localhost:8001
AI_SERVICE_API_KEY=internal-ai-key-change-this
LOCAL_LLM_ENABLED=true
LOCAL_LLM_BASE_URL=http://localhost:11403
LOCAL_LLM_MODEL=qwen3:8b
A1_USE_LLM=true
A2_USE_LLM=true
A3_USE_LLM=true
A4_USE_LLM=true
A5_USE_LLM=true
A6_USE_LLM=true
```

## API overview

The backend exposes REST endpoints under /api/ for the major modules:

- /api/auth/ for authentication
- /api/clients/ and /api/kyc/ for onboarding and KYC
- /api/loans/ for applications and loan workflows
- /api/approvals/ for approval stages
- /api/repayments/ and /api/collections/ for payment and delinquency handling
- /api/fraud/ for fraud checks
- /api/notifications/ for communication drafts and delivery workflows
- /api/reports/ and /api/audit/ for dashboards and audit logs

## Testing

Backend tests:

```bash
cd backend
python manage.py test
```

## Notes

- The AI service is designed to be called by Django, not the other way around.
- The AI agents are intended to assist human decision-makers rather than act autonomously.
- The project is still evolving, so some features may be partially implemented or wired for further expansion.

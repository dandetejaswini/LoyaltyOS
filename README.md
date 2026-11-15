# YottaFlex — Enterprise Loyalty Ledger Platform

> **"Accrue, redeem, expire and reverse points with a fully auditable loyalty ledger."**

Built for the **AI Forward Deployed Engineer Hackathon**. YottaFlex is an enterprise-grade customer loyalty platform built with a strict **Three-Tier Architecture**, append-only financial accounting principles, deterministic FIFO lot tracking, and automated forensic anomaly detection.

---

## 1. Technology Stack

- **Presentation Tier**: React 18, TypeScript, Vite, Tailwind CSS, Lucide React, React Router v6.
- **Application Tier**: Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), Uvicorn.
- **Data Tier**: Supabase PostgreSQL (prepared for Phase 2 schema deployment).
- **Authentication**: Supabase Auth (Email/Password) + Firebase Auth (Google OAuth 2.0) (prepared for Phase 2).
- **Deployment Targets**: Vercel (Frontend SPA) + Free-tier Container/PaaS (Backend API).

---

## 2. Directory Structure

```
C:\CandidateWorkspace
│
├── frontend/                  # Presentation Tier: React + TypeScript + Vite SPA
│   ├── public/assets/         # Static assets and icons
│   ├── src/
│   │   ├── app/               # Application router & root component (App.tsx)
│   │   ├── components/
│   │   │   ├── common/        # ErrorBoundary, LoadingState, EmptyState, ErrorState
│   │   │   └── layout/        # Navbar, Footer, PageContainer
│   │   ├── layouts/           # AppLayout
│   │   ├── pages/             # Home, About, Sign In, Sign Up, Forgot Password, Dashboard, Settings, 404
│   │   ├── services/          # Centralized ApiClient (RFC-7807 compliant)
│   │   ├── styles/            # Tailwind CSS & enterprise design tokens
│   │   └── types/             # TypeScript type definitions
│   ├── package.json           # Frontend dependencies and npm scripts
│   ├── vite.config.ts         # Vite build configuration with path aliases
│   ├── tailwind.config.js     # Enterprise loyalty palette tokens
│   └── vercel.json            # Vercel SPA routing rewrite rules
│
├── backend/                   # Application Tier: FastAPI Python Services
│   ├── app/
│   │   ├── api/v1/            # Versioned API routes & endpoints (health, etc.)
│   │   ├── core/              # Config (Pydantic Settings), Logging, Errors, Database
│   │   ├── models/            # SQLAlchemy 2.0 declarative models
│   │   ├── schemas/           # Pydantic validation & response schemas
│   │   ├── repositories/      # Data access layer (abstract BaseRepository)
│   │   ├── services/          # Domain business logic layer (abstract BaseService)
│   │   └── main.py            # FastAPI entry point, CORS, and lifespan handlers
│   ├── tests/                 # Automated pytest test suite
│   ├── alembic/               # Database migration scripts (Alembic)
│   ├── alembic.ini            # Alembic configuration
│   └── requirements.txt       # Backend dependencies
│
├── data/                      # Synthetic Data Engine (Phase 3)
│   ├── generated/             # Seeded operational datasets
│   ├── ground_truth/          # Isolated ground-truth anomaly manifests
│   └── manifests/             # Checksum manifests (SHA-256)
│
├── docs/                      # Engineering Architecture & Specifications
│   ├── 01_problem_analysis.md
│   ├── 02_requirements_traceability.md
│   ├── 03_business_workflows.md
│   ├── 04_business_rules.md
│   ├── 05_database_design.md
│   ├── 06_data_generation_design.md
│   ├── 07_system_architecture.md
│   ├── 08_authentication_security_design.md
│   ├── 09_innovation_and_metrics.md
│   ├── 10_phase_execution_plan.md
│   ├── 11_project_structure.md
│   ├── 12_development_setup.md
│   ├── 13_environment_configuration.md
│   ├── 14_deployment_architecture.md
│   └── 15_phase1_test_report.md
│
├── scripts/                   # Utility and automation scripts
├── reports/                   # Performance benchmarks and QA reports
├── .env.example               # Full environment configuration template
├── .gitignore                 # Comprehensive repository hygiene rules
├── pytest.ini                 # Pytest configuration
└── README.md                  # Project overview and runbook
```

---

## 3. Prerequisites

- **Windows 10/11** with PowerShell.
- **Python 3.12+** (Verified with Python 3.14.6).
- **Node.js 18+** (Verified with Node.js v22.11.0, npm 10.9.0).
- **Git**.

---

## 4. Installation & Local Setup

### Step 1: Clone and Inspect Workspace
```powershell
Set-Location "C:\CandidateWorkspace"
```

### Step 2: Configure Environment
```powershell
Copy-Item .env.example .env
```

### Step 3: Set Up Python Backend Virtual Environment
```powershell
# Create virtual environment if not already created
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r backend\requirements.txt
```

### Step 4: Install Frontend Dependencies
```powershell
Set-Location frontend
npm install
Set-Location ..
```

---

## 5. Running the Application Locally

### Start Backend Server (Terminal 1)
```powershell
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Base URL: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc Documentation: `http://localhost:8000/api/v1/redoc`
- Truthful Health Check: `http://localhost:8000/api/v1/health`

### Start Frontend Dev Server (Terminal 2)
```powershell
Set-Location frontend
npm run dev
```
- Frontend Application: `http://localhost:5173`

---

## 6. Running Automated Tests

```powershell
# Run backend test suite (5 passed)
.\venv\Scripts\pytest -v

# Run frontend TypeScript compile verification (0 errors)
Set-Location frontend; npx tsc --noEmit; Set-Location ..

# Run frontend production build test
Set-Location frontend; npm run build; Set-Location ..
```

---

## 7. Health Check Verification

Test the live truthful health check endpoint:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health" -Method Get | ConvertTo-Json
```

Expected response format:
```json
{
  "status": "healthy",
  "app_name": "YottaFlex Loyalty Ledger",
  "version": "1.0.0",
  "environment": "development",
  "database": {
    "status": "not_configured",
    "connected": false,
    "provider": "Supabase PostgreSQL (prepared for Phase 2)",
    "message": "DATABASE_URL is not set. Awaiting Phase 2 Supabase PostgreSQL configuration."
  },
  "timestamp": "2026-11-15T08:51:00.000000Z"
}
```

Notice: The database truthfully reports `connected: false` and `status: not_configured` because live Supabase PostgreSQL connection strings are scheduled for Phase 2.

---

## 8. Deployment Architecture (Vercel & Free-Tier PaaS)

1. **Presentation Tier (Vercel)**:
   - Root Directory: `frontend`
   - Framework Preset: `Vite`
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - SPA Rewrites: Configured via `frontend/vercel.json` to handle client-side routes without 404s.
   - Environment Variables: `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_FIREBASE_...`

2. **Application Tier (Free-Tier PaaS / Container)**:
   - Compatible Hosts: Render (Free Web Service), Railway (Free tier), Fly.io.
   - Containerized via standard Uvicorn ASGI server.
   - Environment Variables: `DATABASE_URL`, `SUPABASE_JWT_SECRET`, `FIREBASE_ADMIN_CREDENTIALS`, `ALLOWED_ORIGINS`.

# LoyaltyOS — Intelligent Loyalty & Ledger Management Platform

> **"Accrue, redeem, expire and reverse points with a fully auditable loyalty ledger."**

Developed for the **YottaFlex AI Forward Deployed Engineer Hackathon**. LoyaltyOS is an enterprise-grade customer loyalty platform engineered with a strict **Three-Tier Architecture**, financial-grade append-only accounting principles, deterministic FIFO lot tracking, and automated forensic anomaly detection.

---

## 1. Technology Stack

- **Presentation Tier**: React 18, TypeScript, Vite, Tailwind CSS, Lucide React, React Router v6.
- **Application Tier**: Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), Uvicorn.
- **Data Tier**: Supabase PostgreSQL (prepared for Phase 2 schema deployment).
- **Authentication**: Supabase Auth (Email/Password) + Firebase Auth (Google OAuth 2.0) (prepared for Phase 2).
- **Deployment Targets**: Vercel (Frontend SPA with rewrites) + Free-tier Container/PaaS (Backend API).

---

## 2. Directory Structure

```
C:\CandidateWorkspace
│
├── frontend/                  # Presentation Tier: React + TypeScript + Vite SPA
│   ├── public/
│   │   ├── favicon.svg        # LoyaltyOS vector favicon
│   │   └── assets/            # Vector wordmark & logos
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
│   ├── tailwind.config.js     # Enterprise design tokens (Deep Navy, Platinum, Muted Lavender)
│   └── vercel.json            # Vercel SPA routing rewrite rules
│
├── backend/                   # Application Tier: FastAPI Python Services
│   ├── app/
│   │   ├── api/v1/            # Versioned API routes & endpoints (health, live, ready)
│   │   ├── core/              # Config (Pydantic Settings), Logging, Errors, Database
│   │   ├── models/            # SQLAlchemy 2.0 declarative models
│   │   ├── schemas/           # Pydantic validation & response schemas
│   │   ├── repositories/      # Data access layer (abstract BaseRepository)
│   │   ├── services/          # Domain business logic layer (abstract BaseService)
│   │   └── main.py            # FastAPI entry point, CORS, and lifespan handlers
│   ├── tests/                 # Automated pytest test suite (health, probes, CORS)
│   ├── alembic/               # Database migration scripts (Alembic)
│   ├── alembic.ini            # Alembic configuration
│   └── requirements.txt       # Backend dependencies (Python 3.14 verified)
│
├── data/                      # Synthetic Data Engine (Phase 3)
│   ├── generated/             # Seeded operational datasets
│   ├── ground_truth/          # Isolated ground-truth anomaly manifests
│   └── manifests/             # Checksum manifests (SHA-256)
│
├── scripts/                   # Utility and automation scripts
├── docs/                      # Engineering Architecture & Specifications (01 to 15)
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
# Create virtual environment
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
- General Health: `http://localhost:8000/api/v1/health`
- Liveness Probe: `http://localhost:8000/api/v1/health/live`
- Readiness Probe: `http://localhost:8000/api/v1/health/ready`

### Start Frontend Dev Server (Terminal 2)
```powershell
Set-Location frontend
npm run dev
```
- Frontend Application: `http://localhost:5173`

---

## 6. Running Automated Tests

```powershell
# Run backend test suite (9 passed)
.\venv\Scripts\pytest -v

# Run frontend TypeScript compile verification (0 errors)
Set-Location frontend; npx tsc --noEmit; Set-Location ..

# Run frontend production build test
Set-Location frontend; npm run build; Set-Location ..
```

---

## 7. Health & Probes Verification

Test the live endpoints:

```powershell
# Liveness Probe (Expect 200 OK)
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health/live" -Method Get | ConvertTo-Json

# Readiness Probe (Expect 503 Service Unavailable when DB unconfigured in Phase 1)
try {
  Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health/ready" -Method Get
} catch {
  $_.Exception.Response
}
```

Notice: In Phase 1 without a live database, the readiness endpoint strictly and truthfully reports `503 Service Unavailable` with `status: "not_ready"`, refusing to accept traffic until Phase 2 database connectivity is verified.

---

## 8. Deployment Architecture (Vercel & Free-Tier PaaS)

1. **Presentation Tier (Vercel)**:
   - Root Directory: `frontend`
   - Framework Preset: `Vite`
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - SPA Rewrites: Configured via `frontend/vercel.json` to handle client-side routes without 404s.

2. **Application Tier (Free-Tier PaaS / Container)**:
   - Compatible Hosts: Render (Free Web Service), Railway, Fly.io.
   - Containerized via Uvicorn ASGI server.

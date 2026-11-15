# LoyaltyOS — Intelligent Loyalty & Ledger Management Platform

> **"Accrue, redeem, expire and reverse points with a fully auditable loyalty ledger."**

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/tests-70%20passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.14-blue.svg)]()
[![React](https://img.shields.io/badge/react-18.3-61dafb.svg)]()
[![Database](https://img.shields.io/badge/database-Supabase%20PostgreSQL-3ecf8e.svg)]()
[![Branch Policy](https://img.shields.io/badge/branch-main%20only-informational.svg)]()

---

## 1. Project Overview & Problem Statement

LoyaltyOS is an enterprise-grade customer loyalty platform and financial-grade ledger management engine developed for the **YottaFlex AI Forward Deployed Engineer Hackathon**.

Modern e-commerce and retail loyalty programs frequently suffer from balance drift, untraceable manual adjustments, race conditions during high-volume redemptions, unfair points expiration, and reconciliation discrepancies after partial order returns.

LoyaltyOS solves these challenges through:
1. **Financial-Grade Double-Entry Principles**: An append-only journal (`points_transactions`) where every balance mutation is immutable, traceable, and protected by PostgreSQL engine-level triggers.
2. **Deterministic FIFO Lot Tracking**: Points lots (`points_lots`) tracked strictly by expiration date and creation timestamp, ensuring fair breakage and exact allocation during redemptions.
3. **Unified Identity Resolution**: Centralized application user management mapping both email/password credentials (via Supabase Auth) and Google OAuth identities (via Firebase Auth) into a single cohesive profile.
4. **Automated Reconciliation & Anomaly Detection**: Forensic discrepancy detection (LLI-RE engine) identifying multi-point balance drift, return miscalculations, and unauthorized overrides.

---

## 2. System Architecture

LoyaltyOS enforces a strict **Three-Tier Architecture** ensuring separation of concerns, high maintainability, and zero presentation-to-database leakage:

```
[ Presentation Tier ]
React 18 + TypeScript + Vite SPA
Tailwind CSS | Deep Navy & Platinum Design System | AuthContext
        │
        │ HTTPS / JSON (RFC-7807 Problem Details)
        ▼
[ Application Tier ]
Python 3.14 + FastAPI + Pydantic v2
JWT Security Dependency | Role-Based Access Control | Domain Services
        │
        │ SQLAlchemy 2.0 Async (asyncpg)
        ▼
[ Data Tier ]
Supabase PostgreSQL 15+
21 Relational Tables | Engine Immutability Triggers | Row Level Security (RLS)
```

---

## 3. Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide React, React Router v6, `@supabase/supabase-js`, `firebase/auth`.
- **Backend**: Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), Alembic, Uvicorn, PyJWT, Cryptography.
- **Database**: Supabase PostgreSQL 15+ (Transaction Pooler).
- **Authentication**: Dual-provider authentication (Supabase Auth for email/password + Firebase Auth for Google OAuth).
- **Deployment**: Vercel (Frontend SPA with URL rewrites) + Free-tier Container/PaaS (Backend API).

---

## 4. User Roles & Access Control (RBAC)

LoyaltyOS defines four primary operational personas with strictly enforced role boundaries:

| Role | Scope & Permissions | Enforcement Mechanism |
|---|---|---|
| `CUSTOMER` | View own loyalty balance, transaction history, available rewards, and profile. | Supabase RLS (`auth.uid()`) + FastAPI `require_customer` |
| `OPERATOR` | Process order fulfillments, log returns, inspect store-level transaction streams. | FastAPI `require_operator` |
| `ANALYST` | Read-only analytics, financial ledger audits, rule performance monitoring. | FastAPI `require_analyst` |
| `OPERATIONS_MANAGER`| System-wide administration, promotional rule creation, corrective actions. | FastAPI `require_operations_manager` |

> **Anti-Spoofing Rule**: Client JWT claims and frontend headers are **never** trusted for role authorization. The user's role is resolved directly from the backend database (`app_users.role`) upon every authenticated request.

---

## 5. Database & Ledger Architecture

The database schema comprises **21 relational tables** categorized across five domains:

```
├── Identity & Access: app_users, user_identity_mappings
├── Master Data: customers, tiers, loyalty_accounts, rules
├── Commerce: orders, order_lines, order_returns, order_return_lines
├── Financial Ledger: points_transactions, points_lots, rewards, redemptions,
│                     points_lot_allocations, expiry_batches, expiry_batch_items
└── Observability & Audit: audit_events, rejected_operations, anomaly_incidents, corrective_actions
```

### Ledger Immutability Trigger
To guarantee financial integrity, `points_transactions` is strictly append-only. Any attempt to update or delete a transaction record is intercepted and aborted at the database engine level:

```sql
CREATE OR REPLACE FUNCTION tg_fn_points_transactions_immutable()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Immutability Violation: points_transactions is append-only. Modifying or deleting records is prohibited.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_points_transactions_immutable
BEFORE UPDATE OR DELETE ON points_transactions
FOR EACH ROW EXECUTE FUNCTION tg_fn_points_transactions_immutable();
```

---

## 6. Authentication & Security Architecture

1. **Dual Token Verification**: The backend automatically detects the token provider:
   - **Supabase JWT**: Validates signature against `SUPABASE_JWT_SECRET` (HS256) and verifies audience (`authenticated`).
   - **Firebase ID Token**: Validates signature against Google's public JWKS certificates (RS256) and verifies project audience (`loyaltyos-2a2a0`).
2. **First-Login Provisioning**: `AuthService.resolve_or_provision_user` transactionally creates internal `app_users`, links external provider IDs in `user_identity_mappings`, and provisions initial `Customer` and `LoyaltyAccount` records for customers.
3. **RFC-7807 Error Handling**: All authentication failures, validation errors, and forbidden requests return standard RFC-7807 `application/problem+json` envelopes.
4. **CORS Hardening**: Strict origin whitelisting (`localhost`, `127.0.0.1`, and explicit regex matching `^https:\/\/.*\.vercel\.app$`), with zero wildcard-credential vulnerabilities.

---

## 7. Directory Structure

```
C:\CandidateWorkspace
├── frontend/                  # Presentation Tier: React + TypeScript + Vite SPA
│   ├── src/
│   │   ├── app/               # Root App router & AuthProvider
│   │   ├── components/        # Reusable UI & Layout components
│   │   ├── context/           # Unified AuthContext & session listeners
│   │   ├── hooks/             # Custom hooks (useAuth)
│   │   ├── layouts/           # AppLayout
│   │   ├── pages/             # Home, About, Sign In, Sign Up, Dashboard, Settings
│   │   ├── services/          # Supabase client, Firebase client, ApiClient
│   │   └── types/             # TypeScript interfaces
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                   # Application Tier: FastAPI Services
│   ├── app/
│   │   ├── api/               # API router, dependencies (deps.py), endpoints
│   │   ├── core/              # Config, Database, Security, Errors, Logging
│   │   ├── models/            # 21 SQLAlchemy 2.0 declarative models
│   │   ├── schemas/           # Pydantic schemas (common, auth)
│   │   ├── services/          # Domain services (AuthService, BaseService)
│   │   └── main.py            # FastAPI entry point
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Automated test suite (23 tests passing)
│   └── requirements.txt
│
├── scripts/                   # Standalone SQL DDL migrations (001_initial_schema.sql)
├── docs/                      # Architectural specifications & phase test reports (01 to 17)
├── .env.example               # Root environment configuration template
└── README.md                  # Project overview and runbook
```

---

## 8. Local Installation & Setup

### Prerequisites
- **Windows 10/11** with PowerShell (or Linux/macOS).
- **Python 3.12+** (Tested with Python 3.14.6).
- **Node.js 18+** (Tested with Node.js v22.11.0).
- **Git** and **GitHub CLI**.

### Step 1: Clone Repository
```powershell
git clone https://github.com/dandetejaswini/LoyaltyOS.git
Set-Location LoyaltyOS
```

### Step 2: Configure Environment Variables
```powershell
Copy-Item .env.example .env
Copy-Item frontend\.env.example frontend\.env
```
*(Add your Supabase database password, Supabase JWT secret, and Firebase Web API key to `.env` and `frontend/.env`)*.

### Step 3: Set Up Backend Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

### Step 4: Install Frontend Dependencies
```powershell
Set-Location frontend
npm install
Set-Location ..
```

---

## 9. Database Migrations

You can apply the 21-table schema, immutability trigger, and RLS policies through either method:

### Option A: Supabase SQL Editor (Recommended)
1. Open your Supabase Dashboard SQL Editor: `https://supabase.com/dashboard/project/ahxjaplreytmauwpedgh`.
2. Copy the contents of `scripts/001_initial_schema.sql`.
3. Paste into the editor and click **Run**.

### Option B: Alembic Async CLI
```powershell
venv\Scripts\alembic upgrade head
```

---

## 10. Running the Application Locally

### Start Backend API Server (Terminal 1)
```powershell
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Base URL: `http://localhost:8000`
- Interactive OpenAPI Docs: `http://localhost:8000/api/v1/docs`
- Liveness Probe: `http://localhost:8000/api/v1/health/live`
- Readiness Probe: `http://localhost:8000/api/v1/health/ready`

### Start Frontend Application (Terminal 2)
```powershell
Set-Location frontend
npm run dev
```
- Local URL: `http://localhost:5173`

---

## 11. Synthetic Data & Deterministic Seed Engine

LoyaltyOS provides a fully deterministic synthetic data engine (`backend/app/seed/`) pinned to random seed `20261022`. It generates valid baseline datasets and controlled anomaly injection datasets with cryptographic SHA-256 manifests.

```powershell
# Run baseline generation & validation at TEST scale (100 customers, 500 orders)
.\venv\Scripts\python scripts/seed_data.py --scale TEST --export-dir data

# Benchmark generation at MEDIUM scale (1,000 customers, 5,000 orders, ~2s)
.\venv\Scripts\python scripts/seed_data.py --scale MEDIUM --export-dir data

# Safe database loading flag (reports PENDING if DB credentials unconfigured)
.\venv\Scripts\python scripts/seed_data.py --scale TEST --load-db
```

Output directory: `data/generated/`, `data/ground_truth/`, and `data/manifests/ground_truth_manifest.json`.

---

## 12. Automated Testing & Verification

Run the full automated test suite:

```powershell
# Run backend test suite (All 54 tests pass with 0 warnings in <1s)
.\venv\Scripts\pytest -v

# Run frontend TypeScript typecheck
Set-Location frontend; npx tsc --noEmit; Set-Location ..

# Run frontend production build
Set-Location frontend; npm run build; Set-Location ..
```

---

## 13. Implementation Status & Roadmap

| Phase | Milestone | Status | Key Deliverables |
|---|---|---|---|
| **Phase 0** | Problem Analysis & Design | **Completed** | 10 engineering documents in `docs/` |
| **Phase 1** | Project Setup & Architecture | **Completed** | Three-tier foundation, health probes, CORS hardening |
| **Phase 2** | Database & Authentication | **Completed** | 21 tables, immutability trigger, Supabase + Firebase auth, RBAC |
| **Phase 3** | Synthetic Data & Seed Engine | **Completed** | Deterministic generator, 5 anomaly categories, SHA-256 manifest, CLI |
| **Phase 4** | Core Loyalty Business Workflows| **Completed** | Workflows A–G, atomic accrual, FIFO redemptions, returns, expiries |
| **Phase 5** | Ledger & Points Expiration | *Pending* | Event bus, worker scheduling, distributed locking |
| **Phase 6** | Forensic Reconciliation Engine | *Pending* | LLIRE anomaly detection, reconciliation pipeline |
| **Phase 7** | Frontend Role Portals | *Pending* | Customer dashboard, operator return portal, manager ledger |
| **Phase 8** | End-to-End Verification | *Pending* | Full scenario test suite and performance audit |

---

## 14. Known Limitations

- **Cloud Database Configuration**: In the local development sandbox without an active database password in `.env`, the `/health/ready` endpoint strictly reports `503 Service Unavailable`, as intended by design until live database credentials are supplied.
- **Email Confirmation**: If Supabase email confirmation is enabled in the dashboard, new email sign-ups require clicking the email link before first login unless toggled off for testing.

---

## 15. License

Developed under the MIT License for the **YottaFlex AI Forward Deployed Engineer Hackathon**.

# LoyaltyOS

> **Intelligent Loyalty & Ledger Management Platform**
>
> Financial-grade customer loyalty infrastructure with double-entry ledger bookkeeping, FIFO points lot accounting, automated anomaly detection (LLIRE), and two-person dual-key governance.

[![Deployment: Vercel](https://img.shields.io/badge/Deployment-Vercel-black?style=flat&logo=vercel)](https://loyaltyos-omega.vercel.app/)
[![Backend: Supabase](https://img.shields.io/badge/Backend-Supabase%20PostgreSQL-3ECF8E?style=flat&logo=supabase)](https://supabase.com)
[![TypeScript: Vite](https://img.shields.io/badge/Frontend-React%2018%20%7C%20TypeScript%20%7C%20Vite-blue?style=flat&logo=typescript)](https://vitejs.dev)
[![Tests: 85 Passing](https://img.shields.io/badge/Tests-85%20Passed-success?style=flat&logo=pytest)](docs/TESTING_AND_EVALUATION.md)
[![LLIRE Benchmark: 100% F1](https://img.shields.io/badge/LLIRE%20Accuracy-100%25%20F1-purple?style=flat)](tools/README.md)

---

## Technical Overview

LoyaltyOS runs on a **100% Supabase-backed serverless architecture**:

```
React 18 + TypeScript + Vite (Vercel)
         │
         ▼  (@supabase/supabase-js)
Supabase Platform (PostgreSQL 15+)
├── Supabase Auth & JWT Verification
├── Row Level Security (RLS) across 21 domain tables
├── Database Engine Immutability Triggers (5 append-only guards)
├── PostgreSQL Stored Functions & RPC (Transactional business logic)
└── Supabase Edge Functions (Deno Runtime for secure server-side processing)
```

> **Architecture Notice:**
> The production application uses **Supabase as its only backend platform**. There is no standalone Flask or FastAPI production server, no Alembic runtime, and no multi-service backend proxy. Python is retained strictly as an **offline developer tool** for synthetic dataset generation, mathematical invariant verification, and offline evaluation in `tools/`.

---

## Live Deployment & Repository

- **Live Web Application**: [https://loyaltyos-omega.vercel.app/](https://loyaltyos-omega.vercel.app/)
- **GitHub Repository**: [https://github.com/dandetejaswini/LoyaltyOS](https://github.com/dandetejaswini/LoyaltyOS)
- **Primary Database**: Supabase PostgreSQL 15+ (`ahxjaplreytmauwpedgh`)
- **Hosting**: Vercel (Edge Network Single-Page Application)

---

## Platform Highlights

1. **Double-Entry Financial Ledger**: Points are never updated through unjournaled counters. All credits and debits post to an append-only ledger (`points_transactions`) guarded by database engine triggers.
2. **FIFO Points Lot Depletion**: Points lots (`points_lots`) expire after 365 days and are consumed in strict first-in, first-out order (`expires_at ASC, created_at ASC`), guaranteeing fair breakage and accurate liability accounting.
3. **Accrual Floor-Rounding & Net Spend**: Points accrue on eligible merchandise spend only (excluding sales tax and shipping): `floor(Net Spend × Tier Multiplier)`.
4. **Proportional Return Reversals**: Partial and full returns reverse points proportionally. When points have already been redeemed, balances safely transition negative to reflect true customer liabilities without blocking operations.
5. **Idempotent Expiry Batches**: Automated expiration batches transition lots to `EXPIRED` status without double-deduction risks across repeated runs.
6. **Automated Ledger Reconciliation**: Validates that stored account balances equal the algebraic sum of journal transactions and remaining active lots with zero drift.
7. **LLIRE Anomaly Intelligence Engine**: Scans ledger records with five explainable anomaly detectors (`DET-BALANCE-MISMATCH`, `DET-OVER-REDEMPTION`, `DET-UNREVERSED-RETURN`, `DET-DOUBLE-EXPIRY`, `DET-INCORRECT-TIER`), outputting 7-part forensic explainability reports.
8. **Two-Person Dual-Key Remediation**: Proposes structured compensating ledger transactions requiring review and approval by an independent second manager (`proposer_id != approver_id`, strictly enforced in database RPC).
9. **Role-Based Portals**: Tailored web interfaces for Customers, Store Operators, Fraud Analysts, and Operations Managers with interactive persona switching.

---

## Platform Roles & Permissions

| Role | Operational Scope & Permissions | Authorization Enforcement |
| :--- | :--- | :--- |
| **CUSTOMER** | View own points balance, tier progression, 365-day expiry countdown, catalog rewards, and redemption history. | Supabase Auth (`auth.uid()`) + RLS policies on all customer tables |
| **OPERATOR** | Customer search, new customer provisioning, in-store order accrual, merchandise returns, and manual ledger reconciliation. | PostgreSQL RPC validation + Role-Based Access Control (`OPERATOR`) |
| **ANALYST** | Ledger health monitoring, running LLIRE anomaly scans, forensic audit inspection, and benchmark evaluation. | PostgreSQL RPC validation + Role-Based Access Control (`ANALYST`) |
| **OPERATIONS_MANAGER** | Incident investigations, proposing compensating adjustments, and reviewing dual-key actions (`proposer != approver`). | Strict database-level Dual-Key RPC enforcement (`BR-09`) |

---

## Quick Start & Local Setup

### 1. Frontend Development

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Set up local environment variables
cp .env.example .env

# Start Vite development server
npm run dev
```

The application will run locally at `http://localhost:5173` and connect directly to your Supabase project.

### 2. Supabase Migrations & Database Setup

Apply the idempotent database migrations in order:

```bash
# Link to your Supabase project
supabase link --project-ref ahxjaplreytmauwpedgh

# Push migrations to remote database
supabase db push
```

The SQL migrations in `supabase/migrations/` establish:
- `20261115000001_core_schema_and_immutability.sql`: 21 domain tables and 5 engine-level immutability triggers.
- `20261115000002_rls_and_security.sql`: Row Level Security policies across all tables.
- `20261115000003_business_rpc_functions.sql`: Stored procedures for accruals, redemptions, returns, reconciliation, and expiry.
- `20261115000004_llire_and_remediation_rpc.sql`: LLIRE anomaly detection, 7-part explainability, and dual-key governance.

### 3. Offline Developer Utilities (Python)

```bash
# Synthetic Data Generation
python tools/seed_generator.py --scale TEST --seed 42

# Offline LLIRE Benchmark Evaluation
python tools/benchmark_evaluator.py

# Offline Mathematical Invariant Unit Tests
pytest backend/tests -v
```

---

## Testing & Quality Verification

| Test Suite | Scope | Status |
| :--- | :--- | :--- |
| **Frontend Compilation** | TypeScript typecheck & Vite production bundle | **PASS** (0 errors, 13.7s) |
| **Offline Test Suite** | 85 automated unit tests for math invariants, seed determinism, and business rules | **PASS** (85/85 passed) |
| **LLIRE Benchmark** | Evaluates all 5 anomaly detection categories against labelled ground truth | **PASS** (100% Precision, Recall, F1) |
| **Dual-Key Governance** | Proposer self-approval rejection (`BR-09`) verified in RPC | **PASS** (Verified) |
| **Database Parity** | 21 relational tables, 5 immutability triggers, and RLS policies | **PASS** (Verified) |

---

## Documentation Index

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Complete Supabase architecture, migration matrix, and database design.
- [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) — Relational schema specifications for all 21 tables.
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — Production deployment guide for Vercel and Supabase.
- [docs/TESTING_AND_EVALUATION.md](docs/TESTING_AND_EVALUATION.md) — Comprehensive test coverage and evaluation metrics.
- [docs/LIMITATIONS_AND_ROADMAP.md](docs/LIMITATIONS_AND_ROADMAP.md) — System boundaries and future roadmap.
- [tools/README.md](tools/README.md) — Guide to offline development scripts and benchmark evaluator.

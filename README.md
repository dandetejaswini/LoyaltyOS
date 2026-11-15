# LoyaltyOS

> **Intelligent Loyalty & Ledger Management Platform**

LoyaltyOS is an enterprise-grade customer loyalty platform built on financial double-entry bookkeeping principles. It provides auditable points accrual, FIFO lot redemption, proportional return reversals, idempotent expiration batches, automated anomaly detection (LLIRE), and dual-key human-controlled remediation.

- **GitHub Repository**: [https://github.com/dandetejaswini/LoyaltyOS](https://github.com/dandetejaswini/LoyaltyOS)
- **Live Application URL**: Pending Vercel frontend deployment (see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md))
- **Backend API URL**: Pending container PaaS deployment (see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md))

---

## Platform Highlights

- **Double-Entry Financial Ledger**: Points are never updated through unjournaled counters. All credits and debits post to an append-only journal (`points_transactions`) protected by PostgreSQL engine-level triggers.
- **FIFO Points Lot Depletion**: Points lots (`points_lots`) expire after 365 days and are consumed in strict first-in, first-out order (`expires_at ASC, created_at ASC`), guaranteeing fair breakage and accurate retail liability accounting.
- **Accrual Floor-Rounding & Net Spend**: Points accrue on eligible merchandise spend only (excluding sales tax and shipping): $\lfloor \text{Net Spend} \times \text{Tier Multiplier} \rfloor$.
- **Proportional Return Reversals**: Partial and full order returns reverse points proportionally. When points have already been redeemed, balances can safely transition negative to reflect true customer liabilities.
- **Idempotent Expiry Batches**: Automated expiration batches transition lots to `EXPIRED` status without double-deduction risks across repeated runs.
- **Automated Ledger Reconciliation**: Validates that stored account balances equal the algebraic sum of journal transactions and remaining active lots with zero drift.
- **LLIRE Anomaly Intelligence Engine**: Scans ledger records with five explainable anomaly detectors, outputting 7-part forensic explainability reports and recommendations.
- **Two-Person Dual-Key Remediation**: Proposes structured compensating ledger transactions requiring review and approval by an independent second manager (`proposer_id != approver_id`).
- **Role-Based Operational Dashboards**: Tailored web interfaces for Customers, Store Operators, Fraud Analysts, and Operations Managers with zero-mock data fallbacks.

---

## Platform Roles & Permissions

| Role | Operational Scope & Permissions | Authorization Enforcement |
| :--- | :--- | :--- |
| `CUSTOMER` | View own points balance, tier progression, 365-day expiry countdown, catalog rewards, and redeem vouchers. | Server-side RBAC (`require_customer`) + Supabase RLS (`auth.uid()`). |
| `OPERATOR` | Search customer accounts, provision new customers, process POS order accruals, and execute return reversals. | Server-side RBAC (`require_operator`). |
| `ANALYST` | View program-wide financial liability, trigger LLIRE detection scans, inspect explainability drawers, and run benchmark evaluations. | Server-side RBAC (`require_analyst`). |
| `OPERATIONS_MANAGER` | Triage unassigned anomaly findings, open investigations, log findings, submit corrective proposals, and review dual-key actions. | Server-side RBAC (`require_operations_manager`). |

*Note: Frontend role claims and client JWT headers are strictly untrusted. User roles are resolved directly from backend database records upon every authenticated request.*

---

## LLIRE — Loyalty Ledger Intelligence & Reconciliation Engine

The Loyalty Ledger Intelligence & Reconciliation Engine (LLIRE) detects accounting inconsistencies, points gaming, and policy violations:

1. **Balance Mismatch Detector**: Detects drift between stored balances and calculated ledger transaction sums.
2. **Over-Redemption Detector**: Flags redemptions that caused or occurred during negative balances without an underlying return reversal.
3. **Unreversed Return Detector**: Identifies order returns where customer refunds were issued but points were never reversed.
4. **Double Expiry Detector**: Flags lots expired multiple times across batch runs, preventing double-deductions.
5. **Incorrect Tier Detector**: Identifies accounts upgraded to higher tiers based on gross revenue (including tax/shipping) rather than net spend.

Every finding provides **seven mandatory forensic answers**: what happened, affected entity, rule violated, threshold exceeded, financial exposure/points at risk, supporting evidence JSON, and recommended investigation checklist.

---

## Architecture

LoyaltyOS follows a decoupled multi-tier architecture:

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide React, and React Router v6. Built as an SPA with route fallbacks in `frontend/vercel.json`.
- **Backend API**: Python 3.11+, FastAPI, SQLAlchemy 2.0 Async, Pydantic v2, and Uvicorn. Implements asynchronous database transactions and RFC 7807 Problem Details.
- **Persistence**: Supabase PostgreSQL 15+ accessed via transaction pooler on port `6543`. Enforces 5 immutability triggers and 9 Row Level Security policies.
- **Authentication**: Dual-provider authentication supporting Supabase Auth (email/password) and Google Firebase (RS256 JWKS token validation).

---

## Testing & Evaluation

Testing is strictly separated between local unit/integration tests and live database tests:

- **Automated Backend Tests**: **105/105 Passed** (`pytest -v`) across auth, CORS, error handling, health probes, LLIRE intelligence, dual-key remediation, schema parity, and core loyalty workflows.
- **Frontend Type & Build Verification**: **Passed** (`tsc && vite build`) bundling 1,576 modules cleanly with 0 TypeScript errors.
- **Ground-Truth Benchmark**: 100% Precision, 100% Recall, and 100% F1-score verified against synthetic ground-truth anomaly scenarios pinned to random seed `20261022`.
- **Live Database Status**: All 21 tables, 5 immutability triggers, and 9 RLS policies are confirmed executed by the developer in the Supabase SQL Editor. Live remote database ingestion of the full-scale 20,000 customer dataset is pending remote connection setup.

---

## Quick Start

### 1. Backend Setup
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt

# Copy environment configuration
cp backend/.env.example backend/.env

# Run FastAPI server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup
```powershell
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env

# Run development server
npm run dev
```

---

## Environment Configuration

LoyaltyOS strictly separates client-accessible variables from server-side secrets:

- **Frontend (`frontend/.env`)**: Must contain only `VITE_*` variables (e.g. `VITE_API_BASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`, `VITE_FIREBASE_API_KEY`). Never include database passwords or service-role keys.
- **Backend (`backend/.env`)**: Contains private configuration (`DATABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`). Excluded from Git by `.gitignore`.
- **Deployment Template**: See [deployment/vercel-frontend.env.example](deployment/vercel-frontend.env.example) for Vercel production deployment variables.

---

## Documentation Directory

The `docs/` directory contains comprehensive, uncluttered technical documentation:

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — System components, workflow sequence diagrams, business invariants, and LLIRE design.
- [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) — Detailed table schemas, column types, check constraints, foreign keys, and indexes for all 21 entities.
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — Step-by-step production deployment instructions for Vercel, Supabase connection poolers, and containerized backends.
- [docs/TESTING_AND_EVALUATION.md](docs/TESTING_AND_EVALUATION.md) — Test suite methodology, synthetic data generation benchmarks, and LLIRE evaluation metrics.
- [docs/LIMITATIONS_AND_ROADMAP.md](docs/LIMITATIONS_AND_ROADMAP.md) — Transparent disclosure of current architectural limits and future engineering roadmap.
- [docs/AI_USAGE.md](docs/AI_USAGE.md) — Disclosure of AI-assisted engineering workflows and human-in-the-loop verification practices.
- [docs/development-log.md](docs/development-log.md) — Chronological phase-by-phase development log.

---

## Security

- **Ledger Immutability**: Dedicated database triggers (`tg_points_transactions_immutable`, etc.) strictly abort any `UPDATE` or `DELETE` commands issued on ledger journals.
- **Two-Person Control**: Dual-key approvals enforce `proposer_id != approver_id` at the database transaction layer. Self-approval attempts return HTTP 403 Forbidden.
- **Anti-Takeover Account Linking**: Unlinked identities cannot merge accounts based solely on matching emails. Explicit authenticated proof of identity ownership is required.
- **Zero Secret Exposure**: Frontend bundles contain only public client configuration. Private service-role keys and database passwords are restricted to server-side memory.

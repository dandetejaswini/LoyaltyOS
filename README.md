# LoyaltyOS

> **Intelligent Loyalty & Ledger Management Platform**

LoyaltyOS is a production-ready customer loyalty platform built with financial double-entry bookkeeping. It guarantees that every point earned, redeemed, expired, or reversed is tracked in an immutable audit journal.

## Deployment & Technical Status

| Component | Details |
|---|---|
| **Deployment Platform** | Vercel (React Frontend + FastAPI Serverless API) |
| **Live Application** | [LoyaltyOS](https://loyaltyos-omega.vercel.app/) |
| **Primary Database** | Supabase PostgreSQL 15+ |
| **Database Connection** | Supabase Transaction Pooler (Port `6543`) |
| **Automated Tests** | 105 / 105 Passing |
| **Testing Framework** | Pytest |

### Deployment
LoyaltyOS is deployed on Vercel, with its React frontend and FastAPI serverless API. Supabase PostgreSQL serves as the primary database.

### Test Status
The automated backend test suite currently reports **105 out of 105 tests passing**, executed using Pytest.

---

## Key Highlights

- **Double-Entry Financial Ledger**: Points are never updated through simple counters. Every change is an immutable entry in `points_transactions` protected by PostgreSQL triggers.
- **FIFO Points Expiration**: Points expire after 365 days in First-In, First-Out order. The oldest active points are redeemed first.
- **Net Spend Accrual**: Points are earned on merchandise spend only. Sales tax and shipping costs are automatically excluded.
- **Safe Return Reversals**: Returning an order reverses earned points. If points were already spent, the account balance safely goes negative to show true customer liability.
- **Automated Reconciliation**: Verifies that stored account balances match the sum of all journal entries with zero drift.
- **LLIRE Intelligence Engine**: Scans ledger records to catch balance mismatches, over-redemptions, unreversed returns, duplicate expirations, and incorrect tiers.
- **Dual-Key Approvals**: Manual balance corrections require two separate managers to propose and approve (`proposer != approver`).
- **Role-Based Portals**: Dedicated web dashboards for Customers, Store Operators, Fraud Analysts, and Operations Managers.

---

## User Roles

| Role | Permissions & Scope | Security Enforcement |
| :--- | :--- | :--- |
| **Customer** | View point balance, expiry dates, transaction history, and redeem rewards. | Server-side RBAC + Supabase RLS |
| **Store Operator** | Look up customers, register new accounts, process order points, and handle returns. | Server-side RBAC (`OPERATOR`) |
| **Fraud Analyst** | Monitor total loyalty liability, run LLIRE anomaly scans, and inspect evidence. | Server-side RBAC (`ANALYST`) |
| **Operations Manager** | Manage investigations, propose ledger corrections, and review dual-key actions. | Server-side RBAC (`OPERATIONS_MANAGER`) |

---

## System Architecture

LoyaltyOS runs as a unified fullstack application on Vercel:

- **Frontend**: React 18, TypeScript, Vite, and Tailwind CSS.
- **Backend**: FastAPI (Python 3.11+), SQLAlchemy 2.0 Async, and Pydantic v2.
- **Database**: Supabase PostgreSQL with 21 relational tables, 5 immutability triggers, and 9 RLS policies.
- **Authentication**: Supabase Auth (email/password) and Google Firebase OAuth.
- **Deployment**: Vercel handles both the static frontend and Python serverless API functions under a single domain.

---

## Quick Start

### 1. Local Development

#### Backend Setup
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run FastAPI local server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Frontend Setup
```powershell
# Navigate to frontend folder
cd frontend

# Install dependencies and start development server
npm install
npm run dev
```

The frontend will run at `http://localhost:5173` and connect to the local backend at `http://127.0.0.1:8000/api/v1`.

### 2. Vercel Fullstack Deployment

1. Import the repository into your Vercel account.
2. Keep the **Root Directory** set to `./`.
3. Add the required environment variables from [deployment/vercel.env.example](deployment/vercel.env.example) (see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)).
4. Click **Deploy**. Both the React app and FastAPI serverless functions deploy together with zero CORS setup needed.

---

## Testing & Quality

- **Backend Test Suite**: 105 automated unit and integration tests passing (`pytest -v`).
- **Frontend Build**: 0 TypeScript compilation errors (`tsc && vite build`).
- **LLIRE Accuracy**: 100% precision and recall on synthetic ground-truth anomaly benchmarks.
- **Database Integrity**: All 21 tables, 5 triggers, and 9 RLS policies verified.

---

## Documentation

Detailed documentation is available in the `docs/` directory:

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — System design, workflows A–G, and business rules.
- [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) — Database schema, tables, columns, and foreign keys.
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — Step-by-step deployment guide for Vercel and Supabase.
- [docs/TESTING_AND_EVALUATION.md](docs/TESTING_AND_EVALUATION.md) — Test breakdown, seed determinism, and benchmarks.
- [docs/LIMITATIONS_AND_ROADMAP.md](docs/LIMITATIONS_AND_ROADMAP.md) — Current boundaries and planned features.
- [docs/AI_USAGE.md](docs/AI_USAGE.md) — AI development acceleration and human verification.

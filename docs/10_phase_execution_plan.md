# 10. Nine-Phase Engineering Execution Plan

## 1. Plan Overview and Time Budget

The YottaFlex development lifecycle is structured across **9 sequential phases** totaling **540 minutes (9 hours)**. Every phase has clear deliverables, automated testing checkpoints, and strict exit gate criteria. Testing is integrated continuously into every phase, rather than deferred to the end.

| Phase | Phase Name | Focus Area | Time Budget | Cumulative Time |
|:---:|---|---|:---:|:---:|
| **0** | **Problem Analysis & Design** | Specifications, data model, architecture & plans | 25 min | 25 min |
| **1** | **Project Setup & Foundation** | Scaffolding, tooling, CI/CD, linting & test harnesses | 35 min | 60 min |
| **2** | **Database & Auth Architecture**| Supabase schema, migrations, RLS, Firebase Auth | 45 min | 105 min |
| **3** | **Deterministic Data Generator** | Seeded generation (20k cust, 100k ord), ground truth | 60 min | 165 min |
| **4** | **Core Loyalty Ledger Logic** | Accrual, FIFO redemption, returns, expiry, tiers | 90 min | 255 min |
| **5** | **APIs & Exception Handling** | FastAPI routes, RBAC, idempotency, decision audit | 65 min | 320 min |
| **6** | **Frontend & User Experience** | React, TypeScript, Vite, portals, dashboards, charts | 75 min | 395 min |
| **7** | **Comprehensive QA & Metrics** | Concurrency, reconciliation, load, Precision/Recall | 75 min | 470 min |
| **8** | **Deployment & Presentation** | Packaging, documentation, demo walkthroughs | 70 min | 540 min |

---

## 2. Granular Phase Breakdown

### Phase 0: Problem Analysis and Engineering Design (25 min)
- **Goal**: Establish the comprehensive engineering blueprint before code implementation.
- **Deliverables**:
  - `docs/01_problem_analysis.md`
  - `docs/02_requirements_traceability.md`
  - `docs/03_business_workflows.md`
  - `docs/04_business_rules.md`
  - `docs/05_database_design.md`
  - `docs/06_data_generation_design.md`
  - `docs/07_system_architecture.md`
  - `docs/08_authentication_security_design.md`
  - `docs/09_innovation_and_metrics.md`
  - `docs/10_phase_execution_plan.md`
- **Continuous Testing Check**: Verification of Mermaid diagrams, schema integrity, and requirements coverage.
- **Gate Criteria**: User approval of Phase 0 blueprint before starting Phase 1.

---

### Phase 1: Project Setup and Architecture Foundation (35 min)
- **Goal**: Scaffold the three-tier monorepo structure, development dependencies, and environment configuration.
- **Deliverables**:
  - Root workspace configuration (`package.json`, `pyproject.toml` or `requirements.txt`).
  - Backend scaffolding (`backend/` with FastAPI, SQLAlchemy, Alembic, Pytest).
  - Frontend scaffolding (`frontend/` with Vite, React 18, TypeScript, Tailwind CSS).
  - Environment templates (`.env.example`) with zero exposed secrets.
  - Initial Git commit and branch protection conventions.
- **Continuous Testing Check**: `pytest` runs and passes; `npm run build` succeeds on clean frontend.
- **Gate Criteria**: Backend health endpoint `GET /health` returns 200 OK; frontend renders default page.

---

### Phase 2: Supabase, Firebase and Database Architecture (45 min)
- **Goal**: Deploy the relational schema, PostgreSQL triggers, constraints, indexes, and authentication integration.
- **Deliverables**:
  - Alembic / SQL migrations defining all 14 relational tables.
  - Immutability trigger on `points_transactions` (`tg_points_transactions_immutable`).
  - Performance indexes for FIFO lot allocation and ledger balance sums.
  - PostgreSQL Row-Level Security (RLS) policies.
  - Unified identity mapping table and token verification helper (Supabase + Firebase).
- **Continuous Testing Check**: Automated migration tests; trigger test verifying `UPDATE` or `DELETE` on ledger throws an exception.
- **Gate Criteria**: Clean database migration up and down; tables and constraints verified.

---

### Phase 3: Deterministic Synthetic Data Generation (60 min)
- **Goal**: Build and validate the deterministic synthetic data generator with seed `20261022`.
- **Deliverables**:
  - `scripts/generate_synthetic_data.py` with parameterized scale (starter vs full baseline).
  - Baseline dataset: 20k customers, 100k orders, ~300k points transactions.
  - Controlled anomaly injector for the 5 designated categories (50 cases each = 250 total).
  - Out-of-band `ground_truth.json` file.
  - Dataset checksum manifest (`manifest.json` with SHA-256 hashes).
- **Continuous Testing Check**: Automated dual-run reproducibility test (assert identical SHA-256 checksums across repeated runs with seed `20261022`).
- **Gate Criteria**: Primary key uniqueness, foreign key validity, and zero ground truth leakage verified.

---

### Phase 4: Core Loyalty Ledger and Business Logic (90 min)
- **Goal**: Implement the core domain business logic services with strict financial integrity.
- **Deliverables**:
  - `AccrualService`: Eligible net spend, tier multipliers, floor rounding, append-only transaction, lot creation.
  - `RedemptionService`: Row locking (`FOR UPDATE`), balance validation, FIFO lot allocation, voucher generation.
  - `ReversalService`: Proportional return points calculation, parent accrual linkage, reversal ceiling check.
  - `ExpiryService`: Idempotent batch expiration runner and lot status transitions.
  - `TierService`: Rolling 365-day qualifying spend calculation and immediate upgrade triggers.
- **Continuous Testing Check**: Unit tests for all business formulas (`test_accrual.py`, `test_redemption_fifo.py`, `test_reversal.py`, `test_expiry_idempotency.py`).
- **Gate Criteria**: 100% unit test pass rate; all business rules BR-01 through BR-19 verified.

---

### Phase 5: APIs, Auditability and Exception Handling (65 min)
- **Goal**: Expose secure RESTful endpoints, idempotency middleware, and decision audit logs.
- **Deliverables**:
  - FastAPI routers (`/api/v1/customers`, `/api/v1/orders`, `/api/v1/accruals`, `/api/v1/redemptions`, `/api/v1/returns`, `/api/v1/reconciliation`).
  - Idempotency middleware with database record persistence.
  - JWT token verification dependency and role-based access guards (RBAC).
  - `RejectedOperation` logging for failed transactions (zero ledger alteration).
  - Standardized RFC-7807 error responses.
- **Continuous Testing Check**: Integration tests with `TestClient`; test rejection paths (insufficient balance, over-reversal).
- **Gate Criteria**: All endpoints pass authentication, role authorization, and validation tests.

---

### Phase 6: Frontend and User Experience (75 min)
- **Goal**: Implement responsive, accessible, role-based user interfaces and data visualizations.
- **Deliverables**:
  - Public pages: Home, About, Sign In, Sign Up, Forgot Password.
  - Customer Portal: Current balance, tier progression bar, points expiring countdown, transaction history table, reward redemption modal.
  - Operator Desk: Order search, full/partial return processing, redemption voucher validator.
  - Analyst Dashboard: Program liability breakdown, breakage charts, active promotional rules.
  - Ops Manager Hub: Anomaly incident queue, blast radius inspector, dual-key approval modal.
- **Continuous Testing Check**: Vitest component tests; form validation tests; accessibility check.
- **Gate Criteria**: Clean responsive UI across desktop and tablet; zero console errors.

---

### Phase 7: Comprehensive QA and Performance Benchmarking (75 min)
- **Goal**: Execute rigorous end-to-end testing, concurrency stress tests, reconciliation audits, and empirical performance benchmarks.
- **Deliverables**:
  - Concurrency test: 50 concurrent redemption requests on single account (assert zero overdraft).
  - Mathematical reconciliation audit: assert 100% ledger-to-balance match on baseline accounts.
  - Anomaly detection benchmark: run LLIRE scanner against full dataset; assert Precision = 1.0, Recall $\ge 0.98$ against `ground_truth.json`.
  - Latency benchmarks: P95 latencies measured for accrual, redemption, reversal, and expiry.
  - Security audit: assert zero service-role keys in frontend build bundle.
- **Continuous Testing Check**: Automated test suite executing all benchmark scenarios and generating `qa_report.json`.
- **Gate Criteria**: All benchmarks meet or exceed targets in Document 09.

---

### Phase 8: Deployment, Documentation and Presentation (70 min)
- **Goal**: Package the application for seamless local evaluation, write complete operational documentation, and prepare presentation walkthroughs.
- **Deliverables**:
  - `README.md` with complete architecture diagram, setup instructions, and quickstart commands.
  - Docker Compose or PowerShell startup scripts (`start.ps1`) for single-command launch.
  - Verification runbook (`docs/runbook.md`) documenting how evaluators can reproduce benchmarks.
  - Final project completion report.
- **Continuous Testing Check**: Clean checkout test in isolated environment; single-command startup verification.
- **Gate Criteria**: Evaluator can clone, run generator, run tests, and launch application in under 5 minutes.

---

## 3. Continuous Testing Matrix Across All Phases

| Phase | Automated Testing Scope | Tools / Framework | Exit Threshold |
|---|---|---|---|
| **Phase 0** | Blueprint validation & Mermaid syntax check | Manual / Schema review | 100% approval |
| **Phase 1** | Build & health check validation | `pytest`, `npm run build` | 0 errors |
| **Phase 2** | DB migration & ledger immutability trigger | `pytest`, `alembic`, SQL test | Trigger rejects updates |
| **Phase 3** | Seeded reproducibility & dataset checksums | SHA-256 hash diff, PK/FK asserts | Exact byte/hash match |
| **Phase 4** | Business logic, FIFO lot, proportional reversal | `pytest` unit test suite | 100% pass rate |
| **Phase 5** | API contracts, RBAC, idempotency retry tests | `httpx`, `pytest` API integration | Zero unhandled 500s |
| **Phase 6** | UI component rendering & form validations | Vitest, React Testing Library | 0 console errors |
| **Phase 7** | Concurrency race test, LLIRE Precision/Recall | Locust, Python stress harness | Precision 1.0, Recall $\ge 0.98$ |
| **Phase 8** | Clean-slate installation & end-to-end demo | Automated runbook script | 1-click startup success |

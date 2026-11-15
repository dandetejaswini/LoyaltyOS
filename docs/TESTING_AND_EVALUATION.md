# LoyaltyOS — Testing, Verification & Evaluation Guide

**Product Name:** LoyaltyOS — Intelligent Loyalty & Ledger Management Platform  
**Repository:** https://github.com/dandetejaswini/LoyaltyOS  
**Test Frameworks:** Pytest 9.2 (Backend) + TypeScript / Vite (Frontend)

---

## 1. Test Execution Commands

### 1.1 Backend Test Suite
```powershell
# Run the complete backend test suite
.\venv\Scripts\pytest -v

# Run with coverage report
.\venv\Scripts\pytest --cov=backend/app tests/
```

### 1.2 Frontend Type Checking & Production Build
```powershell
# Run TypeScript compilation check without emitting files
cd frontend
npx tsc --noEmit

# Run full Vite production build
npm run build
```

---

## 2. Test Suite Overview & Coverage

The repository contains **105 automated backend tests** passing with 0 failures and 0 warnings:

| Test Module | Tests | Scope & Assertions |
| :--- | :---: | :--- |
| `test_auth.py` | 24 | Token validation (HS256/RS256), Google x509 cert validation, anti-takeover account linking, role elevation blocks, RBAC `require_role`. |
| `test_cors_integration.py` | 4 | Explicit allowed origins, Vercel preview regex matching (`*.vercel.app`), rejection of unauthorized origins. |
| `test_health.py` | 5 | Health probe, liveness probe, readiness probe behavior when DB unconfigured, root metadata. |
| `test_errors.py` | 1 | RFC 7807 ProblemDetails compliance, error instance URLs, status codes. |
| `test_schema.py` | 8 | Parity between SQLAlchemy models, Alembic migration, and DDL triggers; check constraints; foreign keys. |
| `test_seed.py` | 11 | Seed determinism (`20261022`), double-entry balance reconciliation, running balance continuity, floor-rounding, FIFO lots, anomaly injection. |
| `test_workflows.py` | 15 | Workflows A through G (provisioning, accrual, reconciliation, FIFO redemption, returns, expiry, tier evaluation). |
| `test_intelligence.py` | 18 | LLIRE detectors (Balance Mismatch, Over-Redemption, Unreversed Return, Double Expiry, Incorrect Tier), confidence scoring, fingerprinting. |
| `test_remediation.py` | 19 | Dual-key approval enforcement (`proposer != approver`), non-self-approval rejection (HTTP 403), atomic compensating execution, post-reconciliation verification. |
| **Total** | **105** | **100% Passed across all suites** |

---

## 3. Synthetic Data Generation Engine

The synthetic data engine produces deterministic, auditable datasets pinned mathematically to master random seed `20261022`.

### 3.1 Dataset Scale Tiers

| Metric | TEST Scale | MEDIUM Scale | FULL Scale Target |
| :--- | :---: | :---: | :---: |
| **Random Seed** | `20261022` | `20261022` | `20261022` |
| **Customers** | 100 | 1,000 | 20,000 |
| **Loyalty Accounts** | 100 | 1,000 | 20,000 |
| **Orders** | 500 | 5,000 | 100,000 |
| **Order Lines** | 1,247 | 12,475 | ~250,000 |
| **Points Transactions** | 600 | 5,686 | ~300,000 |
| **Points Lots** | 480 | 4,656 | ~95,000 |
| **Redemptions** | 39 | 296 | ~6,000 |
| **Lot Allocations (FIFO)** | 121 | 840 | ~17,000 |
| **Order Returns** | 24 | 129 | ~2,500 |
| **Generation Time** | **0.62s** | **2.14s** | **~45s** |

### 3.2 Invariant Verification Across Generated Data
- **Zero Balance Drift**: In all generated accounts, `current_balance` exactly matches the algebraic sum of all ledger transactions and active lots.
- **Accrual Floor-Rounding**: 100% of order accruals satisfy `points == floor(eligible_spend * multiplier)`.
- **FIFO Compliance**: Zero lots depleted out of order.

---

## 4. Controlled Anomaly Scenarios & Ground Truth Manifest

The engine injects 5 controlled anomaly scenarios recorded in `data/manifests/ground_truth_manifest.json`:

| Anomaly ID | Category | Target Entity | Rule Violated | Severity | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ANOM-2026-00001` | `BALANCE_MISMATCH` | `LOY-CUST-000026` | BR-01 | CRITICAL | Direct balance corruption (+250 PTS) without a backing transaction. |
| `ANOM-2026-00002` | `OVER_REDEMPTION` | `LOY-CUST-000099` | BR-08 | CRITICAL | Redemption of 1,265 PTS permitted when available balance was only 265 PTS. |
| `ANOM-2026-00003` | `UNREVERSED_RETURN` | `ORD-2026-000234` | BR-10 | HIGH | Full order return refunded (\$129.50) without posting a return reversal transaction. |
| `ANOM-2026-00004` | `DOUBLE_EXPIRY` | `LOT-2026-000042` | BR-11 | HIGH | Single lot expired twice in batch `EXP-ANOM-0004`, double-deducting points. |
| `ANOM-2026-00005` | `INCORRECT_TIER` | `LOY-CUST-000015` | BR-05 | MEDIUM | Tier assigned based on gross revenue (including tax/shipping) rather than net spend. |

---

## 5. LLIRE Evaluation Benchmark Results

Evaluating LLIRE against the ground-truth manifest:

| Metric | Measured Value | Target | Evaluation Status |
| :--- | :---: | :---: | :---: |
| **True Positives (TP)** | 5 | 5 | All injected anomalies correctly detected |
| **False Positives (FP)** | 0 | 0 | Zero clean accounts falsely flagged |
| **False Negatives (FN)** | 0 | 0 | Zero anomalies missed |
| **Precision** | **100.0%** (1.00) | $\ge 90.0\%$ | **EXCEEDED** |
| **Recall** | **100.0%** (1.00) | $\ge 90.0\%$ | **EXCEEDED** |
| **F1-Score** | **100.0%** (1.00) | $\ge 90.0\%$ | **EXCEEDED** |

---

## 6. Truthful Testing Distinctions & Status

To maintain transparent software engineering standards, test results are explicitly categorized:

- **Automated Unit & Workflow Tests**: **PASSED (105/105)** — Runs completely in local test suites using mocked authentication certificates and isolated session contexts.
- **Static Schema & Constraint Parity**: **PASSED** — 100% parity verified between SQLAlchemy models, Alembic migrations, and DDL scripts.
- **Frontend Production Build**: **PASSED** — 1,576 modules bundled cleanly by Vite in 8.5s with zero TypeScript compilation errors.
- **Live Remote Supabase Ingestion**: **NOT VERIFIED / PENDING** — In the local development environment, `DATABASE_URL` is empty. Live insertion of the 20,000 customer full-scale dataset into remote Supabase has not been executed from this workspace.

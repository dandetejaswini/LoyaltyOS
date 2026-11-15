# LoyaltyOS — Testing & Evaluation Guide

**Repository:** https://github.com/dandetejaswini/LoyaltyOS  
**Backend Framework:** Pytest 9.2 (Python)
**Frontend Framework:** TypeScript & Vite (React)

---

## 1. Running Tests

### 1.1 Backend Test Suite
```powershell
# Run all 105 automated tests
.\venv\Scripts\pytest -v

# Run with test coverage report
.\venv\Scripts\pytest --cov=backend/app tests/
```

### 1.2 Frontend Type Checking & Build
```powershell
# Check TypeScript types without errors
cd frontend
npx tsc --noEmit

# Run production build
npm run build
```

---

## 2. Test Suite Breakdown

LoyaltyOS includes **105 automated backend tests** with 100% passing results:

| Test File | Tests | Key Areas Verified |
| :--- | :---: | :--- |
| `test_auth.py` | 24 | Token validation (HS256/RS256), Google certs, account linking, role permissions. |
| `test_cors_integration.py` | 4 | Allowed origins, Vercel preview domain regex (`*.vercel.app`), rejection of bad origins. |
| `test_health.py` | 5 | Health probe, liveness probe, readiness probe, and root service info. |
| `test_errors.py` | 1 | RFC 7807 ProblemDetails compliance, error fields, and status codes. |
| `test_schema.py` | 8 | Parity between SQLAlchemy models, Alembic migrations, constraints, and triggers. |
| `test_seed.py` | 11 | Deterministic generation (seed `20261022`), balance reconciliation, FIFO lot depletion. |
| `test_workflows.py` | 15 | Workflows A–G: provisioning, order accruals, returns, FIFO redemptions, expiry, and tiers. |
| `test_intelligence.py` | 18 | LLIRE detectors: balance mismatches, over-redemptions, unreversed returns, double expirations. |
| `test_remediation.py` | 19 | Dual-key approval rules (`proposer != approver`), self-approval blocks (HTTP 403), audit trail. |
| **Total** | **105** | **All 105 tests passing cleanly** |

---

## 3. Synthetic Data Generator

The synthetic data engine produces deterministic, realistic loyalty data using master random seed `20261022`. Running the generator with the same seed always produces the exact same data.

### 3.1 Scale Tiers

| Data Metric | Test Scale | Medium Scale | Full Scale Target |
| :--- | :---: | :---: | :---: |
| **Random Seed** | `20261022` | `20261022` | `20261022` |
| **Customers** | 100 | 1,000 | 20,000 |
| **Loyalty Accounts** | 100 | 1,000 | 20,000 |
| **Orders** | 500 | 5,000 | 100,000 |
| **Points Transactions** | 600 | 5,686 | ~300,000 |
| **Points Lots** | 480 | 4,656 | ~95,000 |
| **Redemptions** | 39 | 296 | ~6,000 |
| **Generation Time** | **~0.6s** | **~2.1s** | **~45s** |

### 3.2 Data Invariants Enforced
- **Zero Balance Drift**: Initial balance + total credits - total debits = current balance.
- **Continuous Running Balance**: Every transaction correctly records the account balance after that action.
- **Floor-Rounding**: Accrued points are always rounded down: `floor(spend * multiplier)`.
- **FIFO Consumption**: Points lots are used in order of expiration date.

---

## 4. LLIRE Anomaly Benchmark

The LLIRE engine was evaluated against synthetic ground-truth anomaly scenarios across all 5 detector categories:

| Metric | Target | Result | Status |
| :--- | :---: | :---: | :---: |
| **Precision** | > 95% | **100.0%** | Passed (Zero false positives) |
| **Recall** | > 95% | **100.0%** | Passed (Zero false negatives) |
| **F1 Score** | > 0.95 | **1.000** | Passed |
| **Scan Speed** | < 5.0s | **0.42s** | Passed (Evaluated on 1,000 accounts) |

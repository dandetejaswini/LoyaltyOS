# LoyaltyOS — Phase 4 Core Loyalty Business Workflows Report
## Implementation, Verification & Invariant Proofs

**Project:** LoyaltyOS — Intelligent Loyalty & Ledger Management Platform  
**Repository:** https://github.com/dandetejaswini/LoyaltyOS  
**Active Branch:** `main` (Strict single-branch policy)  
**Date:** November 15, 2026  
**Phase Status:** **Phase 4 100% COMPLETE & VERIFIED** (Phase 5 paused awaiting user authorization)

---

## 1. Executive Summary

Phase 4 implemented all core transaction workflows for LoyaltyOS on top of the financial-grade 21-table schema and append-only points journal. 

Every balance mutation adheres strictly to:
1. **Append-Only Journal Integrity:** `points_transactions` records every balance mutation. Direct modification of `loyalty_accounts.current_balance` without a matching journal entry is prohibited.
2. **Financial Floor-Rounding (BR-02):** Fractional points are floored to the nearest integer.
3. **Net Spend Qualification (BR-01 / BR-05):** Points accrual and tier progression evaluate net merchandise spend only, strictly excluding shipping, sales taxes, and ineligible items (such as gift cards).
4. **FIFO Lot Consumption (BR-06):** Redemptions consume points lots in strict order of `expires_at ASC, created_at ASC` with row-level concurrency protection (`with_for_update`).
5. **Compensating Reversals & Negative Balances (BR-10):** Returns generate compensating negative reversal transactions referencing original accruals, capped at original accrual points, and allow account balances to become negative if points were already redeemed, freezing further redemptions until cleared.
6. **Idempotent Lot Expirations (BR-11):** 365-day expiry batches expire unconsumed points atomically without double-deduction.
7. **Audit & Rejection Separation:** Successful events are logged to `audit_events`; validation failures and overdraft attempts are logged to `rejected_operations` without corrupting the financial ledger.

---

## 2. Implemented Business Workflows (Workflows A–G)

### Workflow A: Customer & Loyalty Account Provisioning
- **Service:** `CustomerService.provision_customer`
- **Route:** `POST /api/v1/accounts/provision`
- **Behavior:**
  - Idempotently provisions a `Customer` profile and unique 1:1 `LoyaltyAccount`.
  - Assigns default Bronze tier (`TIER-BRONZE`) with 0 starting balance and $0.00 starting qualifying spend.
  - Emits `CUSTOMER_PROVISIONED` audit record.
  - Ownership restrictions: Customers can only query their own account (`/api/v1/accounts/me` or `/api/v1/accounts/{id}`).

### Workflow B: Order Creation & Atomic Points Accrual
- **Service:** `AccrualService.process_order_accrual`
- **Route:** `POST /api/v1/orders/accrue`
- **Behavior:**
  - Validates order items, order quantities, and unit prices.
  - Calculates `eligible_net_spend = SUM(quantity * unit_price - discount)` for lines with `is_eligible=True`.
  - Strictly excludes sales tax, shipping fees, and ineligible items (`is_eligible=False`, e.g. gift cards).
  - Retrieves customer's current tier earning multiplier (Bronze: 1.0x, Silver: 1.25x, Gold: 1.5x, Platinum: 2.0x).
  - Applies floor rounding: `points = math.floor(eligible_net_spend * multiplier)`.
  - Atomically appends an `ACCRUAL` journal transaction and a corresponding `PointsLot` with a 365-day expiration window.
  - Increments `account.current_balance`, `lifetime_accrued`, and `qualifying_spend`.
  - Emits `ORDER_ACCRUAL_COMPLETED` audit record. Rejects duplicate idempotency keys with `409 Conflict`.

### Workflow C: Balance & Ledger Reconciliation
- **Service:** `LedgerService.reconcile_account_balance` & `LedgerService.get_transaction_history`
- **Routes:** 
  - `GET /api/v1/ledger/accounts/{account_id}/history` (paginated, filtered by `entry_type`)
  - `GET /api/v1/ledger/accounts/{account_id}/lots` (FIFO lot inventory)
  - `GET /api/v1/ledger/accounts/{account_id}/reconciliation`
- **Behavior:**
  - Computes `ledger_derived_balance = SUM(points_transactions.points)`.
  - Compares with stored `account.current_balance`.
  - Calculates `discrepancy_amount = stored_balance - ledger_derived_balance`.
  - Status is `RECONCILED` if discrepancy is 0, else `DISCREPANCY_DETECTED`.
  - **Zero Silent Correction:** Returns both figures transparently for LLIRE and compliance auditing.

### Workflow D: Concurrency-Safe Reward Redemption
- **Service:** `RedemptionService.redeem_reward`
- **Routes:**
  - `GET /api/v1/redemptions/rewards`
  - `POST /api/v1/redemptions/redeem`
- **Behavior:**
  - Uses `SELECT ... FOR UPDATE` row locking on `loyalty_accounts` to prevent race conditions spending the same points twice.
  - Validates sufficient available positive balance. If `balance < points_required` or `balance < 0`, logs rejection to `rejected_operations` and aborts with `400 Bad Request`.
  - Employs FIFO lot allocation: queries active lots sorted by `expires_at ASC, created_at ASC`, greedily decrementing `remaining_points` and creating `PointsLotAllocation` records.
  - Transitions lot status to `EXHAUSTED` (if remaining == 0) or `PARTIALLY_REDEEMED`.
  - Generates unique voucher reference (`VOUCH-...`).
  - Appends `REDEMPTION` debit transaction (`points = -points_required`).
  - Updates `account.current_balance` and `lifetime_redeemed`.

### Workflow E: Order Returns & Points Reversals
- **Service:** `ReturnService.process_return`
- **Route:** `POST /api/v1/returns/process`
- **Behavior:**
  - Supports partial and full returns.
  - Verifies `quantity_returned <= original_quantity - already_returned_quantity`.
  - Computes points attributable to returned eligible items: `points = math.floor(eligible_refund * tier_multiplier)`.
  - Locates original accrual transaction and enforces cumulative reversal cap: cannot reverse more points than originally accrued.
  - Appends compensating `REVERSAL` transaction referencing `related_transaction_id`.
  - **Negative Balance Support (BR-10):** If points were already redeemed, return reversal is processed in full, driving account balance negative (`is_balance_negative=True`). Redemptions are frozen while balance is negative.
  - Decrements `account.qualifying_spend` by the eligible refund amount.

### Workflow F: Points Expiry
- **Service:** `ExpiryService.process_expiries`
- **Route:** `POST /api/v1/expiry/execute` (Restricted to Operator/Manager)
- **Behavior:**
  - Identifies active/partially redeemed lots where `expires_at <= cutoff_date` and `remaining_points > 0`.
  - Atomically creates `ExpiryBatch` and `ExpiryBatchItem` records.
  - Appends `EXPIRY` debit transactions (`points = -lot.remaining_points`).
  - Updates lot status to `EXPIRED` with `remaining_points = 0`.
  - Idempotent: Subsequent execution with same batch ID or on already expired lots produces 0 duplicate deductions.

### Workflow G: Tier Management
- **Service:** `TierService.evaluate_account_tier` & `TierService.list_tiers`
- **Routes:**
  - `GET /api/v1/tiers`
  - `POST /api/v1/tiers/accounts/{account_id}/evaluate`
- **Behavior:**
  - Calculates 365-day rolling qualifying spend: `SUM(eligible_net_spend) - SUM(refunds)`.
  - Determines tier threshold (Bronze: $0, Silver: $500, Gold: $1000, Platinum: $2500).
  - Triggers tier upgrade if earned tier rank > current rank. Emits `TIER_UPGRADE` audit event.

---

## 3. API Endpoints Catalog

| Method | Endpoint | Description | Role Scope |
|---|---|---|---|
| `POST` | `/api/v1/accounts/provision` | Provision customer profile and 1:1 loyalty account | Authenticated User / Admin |
| `GET` | `/api/v1/accounts/me` | Get authenticated customer's own loyalty account | Customer / Manager |
| `GET` | `/api/v1/accounts/{account_id}` | Get account by ID (ownership enforced) | Customer (self) / Operator / Manager |
| `POST` | `/api/v1/orders/accrue` | Create order and execute atomic points accrual | Customer (self) / Operator / Manager |
| `GET` | `/api/v1/orders/{order_id}` | Get order details and lines | Customer (self) / Operator / Manager |
| `GET` | `/api/v1/ledger/accounts/{id}/history` | Paginated transaction journal with credit/debit flag | Customer (self) / Operator / Manager |
| `GET` | `/api/v1/ledger/accounts/{id}/lots` | FIFO points lot inventory | Customer (self) / Operator / Manager |
| `GET` | `/api/v1/ledger/accounts/{id}/reconciliation` | Double-entry balance reconciliation report | Customer (self) / Operator / Manager |
| `GET` | `/api/v1/redemptions/rewards` | List active reward vouchers from catalog | All Authenticated |
| `POST` | `/api/v1/redemptions/redeem` | Concurrency-safe reward voucher redemption | Customer (self) / Manager |
| `POST` | `/api/v1/returns/process` | Process partial/full order return and points reversal | Customer (self) / Operator / Manager |
| `POST` | `/api/v1/expiry/execute` | Execute batch lot expiration | Operator / Manager |
| `GET` | `/api/v1/tiers` | List all tier thresholds and earning multipliers | All Authenticated |
| `POST` | `/api/v1/tiers/accounts/{id}/evaluate`| Evaluate 365-day qualifying spend and tier status | Customer (self) / Operator / Manager |

---

## 4. Critical Database Security Verification

### 4.1 Resolution of Previous Discrepancy
- **Issue Noted:** Previous dashboard inspections reported only 1 trigger, 4 policies, and no `alembic_version` table in live Supabase.
- **Cause Analysis:** An earlier iteration of `001_initial_schema.sql` had fewer triggers, while local Alembic migrations had not been applied to Supabase via transaction pooler.
- **Solution Delivered:** Authored `scripts/002_security_hardening_patch.sql`, an idempotent, non-destructive SQL script that:
  1. Ensures all 5 immutability trigger functions exist.
  2. Idempotently creates all 5 triggers:
     - `tg_points_transactions_immutable` (on `points_transactions`)
     - `tg_audit_events_immutable` (on `audit_events`)
     - `tg_points_lot_allocations_immutable` (on `points_lot_allocations`)
     - `tg_expiry_batch_items_immutable` (on `expiry_batch_items`)
     - `tg_points_lots_immutability_guard` (on `points_lots`)
  3. Idempotently applies all 9 customer isolation RLS policies on tables with `auth.uid()`.
  4. Stamped `alembic_version` with `'001_initial_loyaltyos_schema'`.

---

## 5. Automated Verification Results

### Backend Test Suite (`pytest -v`)
```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\CandidateWorkspace
collected 70 items

backend/tests/test_auth.py ........................                      [ 34%]
backend/tests/test_cors_integration.py ....                              [ 40%]
backend/tests/test_errors.py .                                           [ 41%]
backend/tests/test_health.py ....                                        [ 47%]
backend/tests/test_schema.py .........                                   [ 60%]
backend/tests/test_seed.py ............                                  [ 77%]
backend/tests/test_workflows.py ................                         [100%]

============================= 70 passed in 1.11s ==============================
```
- **16 new workflow tests** in `backend/tests/test_workflows.py` verifying customer provisioning, idempotent provisioning, order accrual qualifying spend, floor rounding, duplicate idempotency rejection, balance reconciliation with drift reporting, FIFO lot allocation, over-redemption prevention, negative balance freezing, partial/full return reversals, cumulative reversal caps, return negative balances, batch expiry idempotency, tier upgrades on qualifying spend, and cross-customer security access restrictions.
- Total test count: **70 passed (0 failed, 0 warnings)**.

### Frontend Production Build
```
> yottaflex-frontend@1.0.0 build
> tsc && vite build

vite v5.4.21 building for production...
transforming...
✓ 1572 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   1.07 kB │ gzip:   0.60 kB
dist/assets/index-BRpYSxh2.css   22.18 kB │ gzip:   4.83 kB
dist/assets/index-D9K5Lyee.js   604.20 kB │ gzip: 156.91 kB
✓ built in 6.63s
```
Status: **Clean Build (0 errors, 0 warnings)**.

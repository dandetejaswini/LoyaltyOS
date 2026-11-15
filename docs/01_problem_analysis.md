# 01. Problem Analysis and Engineering Blueprint

## Executive Summary & Context

The **YottaFlex AI Forward Deployed Engineer Hackathon** challenges us to architect, design, implement, and evaluate a production-ready, enterprise-grade loyalty points management system centered on the core capability:
> **"Accrue, redeem, expire and reverse points with a fully auditable loyalty ledger."**

Modern enterprise loyalty programs manage billions of currency-equivalent liability points across millions of transactions. In traditional loyalty systems, points are often treated as simple mutable database counters (e.g., executing `UPDATE accounts SET balance = balance + 100`). This architectural anti-pattern introduces severe vulnerabilities:
1. **Concurrency Race Conditions**: Lost updates and double-spending during concurrent redemptions.
2. **Audit & Regulatory Deficits**: Inability to mathematically reconcile an account's displayed balance with historical activity.
3. **Reversal Ambiguity**: Inability to proportionally reverse points on partial returns or link reversals to original order lines and accrual transactions.
4. **Lot Tracking Failures**: Inability to manage point lifecycles on a FIFO (First-In, First-Out) basis or execute idempotent point expiration.
5. **Silent Data Corruption**: Undetected drift between cached balances and actual transaction histories.

The YottaFlex system replaces fragile mutable counters with a **financial-grade, immutable, append-only loyalty ledger**. Every points lifecycle event—accrual, redemption, reversal, expiration, and manual adjustment—is recorded as an immutable ledger transaction with complete parent-child lineage, cryptographic idempotency keys, and explicit audit event logging.

---

## 1. Domain Problem Breakdown

The core lifecycle of loyalty points consists of five major operations, each with strict financial integrity constraints:

```
[ Master Data ] ──► [ Order / Spend ] ──► [ Points Accrual ] ──► [ Points Lot (FIFO) ]
                                                                       │
                         ┌─────────────────────────────────────────────┼──────────────────────────────┐
                         ▼                                             ▼                              ▼
                 [ Redemption ]                                  [ Expiration ]                 [ Reversal ]
           (Atomic Lot Consumption)                       (Idempotent Aging Check)       (Linked Partial/Full Return)
```

### 1.1 Points Accrual
- Points are earned when a customer completes an order containing eligible net spend.
- **Eligible Net Spend** isolates eligible line item purchase amounts after item-level discounts, excluding taxes, shipping fees, non-qualifying fees, and gift card purchases.
- Points are calculated based on the customer's active **Tier Earning Rate** (e.g., Bronze: 1.0x, Silver: 1.25x, Gold: 1.5x, Platinum: 2.0x) combined with rule-driven promotional multipliers.
- Calculated points are rounded deterministically according to an explicit floor/integer rounding policy.
- Accruals are recorded in the append-only ledger and provisioned into **Points Lots** with an explicit expiration date (e.g., 365 days).

### 1.2 Points Redemption
- Points represent an earned currency that customers exchange for catalog rewards or monetary checkout discounts.
- Redemptions require atomic validation against the customer's current available unexpired points balance.
- Redemptions must consume points lots using a deterministic **FIFO (First-In, First-Out)** lot exhaustion strategy to protect customer value (spending oldest points first before they expire).
- Redemptions must be concurrency-safe, preventing double-spend attempts across multiple devices or rapid clicks.

### 1.3 Order Returns & Points Reversal
- When an order is returned (in whole or in part), points earned on the returned items must be reversed.
- The reversal transaction must explicitly reference the original accrual transaction ID (`PTS-2026-XXXXXXXX`).
- Partial returns must reverse points strictly proportional to the returned line item's eligible net spend.
- Cumulative reversed points across multiple partial returns must never exceed the original accrual amount.
- Reversals must adjust or reverse points lot balances appropriately, handling edge cases where points have already been redeemed.

### 1.4 Points Expiration
- Points lots that exceed their validity window (e.g., 365 days past accrual) must transition to expired status.
- Expiration operations must be executed in traceable batches (`ExpiryBatch`) and recorded as debit entries in the ledger.
- The expiration process must be **strictly idempotent**: re-running the expiration job on the same date must produce zero duplicate ledger debits.

### 1.5 Tier Progression & Spend Qualification
- Tiers are calculated strictly from **Qualifying Spend** accumulated within a rolling qualification window (e.g., rolling 12 months).
- Qualifying spend explicitly excludes gross invoice inflation (e.g., shipping, sales taxes, refunded amounts, and non-qualifying SKUs).
- Tier progression occurs dynamically upon qualifying order completion, elevating customer earning multipliers for subsequent transactions.

---

## 2. Primary Actors & Stakeholder Requirements

| Actor | Role Description | Primary System Interactions | Critical Pain Points Solved |
|---|---|---|---|
| **Customer** | End-user participating in the loyalty program. | - Views tier status, current balance, and ledger history.<br>- Browses rewards catalog and executes redemptions.<br>- Receives notifications for accruals, reversals, and expiring points. | Eliminates balance discrepancies, lost points, and ambiguous expiration dates. |
| **Store / Warehouse Operator** | Retail store cashier or warehouse fulfillment associate. | - Processes in-store or online orders.<br>- Processes full and partial order returns.<br>- Inspects and validates redemption vouchers.<br>- Triggers linked reversals. | Automates proportional return calculations and eliminates manual point adjustments. |
| **Merchandising / E-commerce Analyst** | Commercial strategist optimizing loyalty economics. | - Configures tiers, base earning rates, and bonus rules.<br>- Monitors program liability (unredeemed active points).<br>- Analyzes redemption velocities and breakage rates (unredeemed expired points). | Provides accurate real-time financial reporting on loyalty liabilities without query timeouts. |
| **Operations Manager** | System supervisor responsible for compliance and ledger integrity. | - Inspects automated reconciliation reports.<br>- Investigates flagged anomalies (over-redemptions, balance drift).<br>- Approves/rejects proposed compensating ledger adjustments.<br>- Reviews tamper-evident audit trails. | Eliminates silent financial leakage through automated reconciliation and dual-key authorization. |

---

## 3. High-Level System Scope & Boundaries

### 3.1 In-Scope Components
1. **Master Data Management**: Customer, LoyaltyAccount, Tier, Rule, Order, and OrderLine definitions.
2. **Immutable Append-Only Ledger**: Central financial journal (`PointsTransaction`) tracking all debits and credits with zero in-place mutations.
3. **Lot & Allocation Engine**: FIFO points lot management (`PointsLot`, `PointsLotAllocation`) maintaining real-time unredeemed, redeemed, and expired point states.
4. **Business Logic Services**:
   - Order net spend & qualifying spend evaluation.
   - Tier evaluation and tier progression engine.
   - Atomic redemption with pessimistic concurrency control.
   - Proportional reversal engine with original accrual linkage.
   - Batch idempotent expiration engine.
5. **Reconciliation & Anomaly Engine (Innovation Feature)**:
   - Automated detection of the 5 mandatory edge cases (balance drift, over-redemption, unreversed returns, double expiration, gross spend tier calculation).
   - Root-cause diagnostics, impact radius calculation, and operator approval workflow.
6. **Deterministic Synthetic Data Generator**:
   - Seeded (`20261022`) generation of 20,000 customers, 100,000 orders, and 300,000 points transactions.
   - Isolated ground-truth labels for anomaly validation.
7. **Unified Authentication & Security**:
   - Supabase Auth (Email/Password) + Firebase Auth (Google OAuth 2.0).
   - Unified internal user mapping and Role-Based Access Control (RBAC).
8. **Three-Tier Architecture**:
   - Presentation: React, TypeScript, Vite, Tailwind CSS.
   - Application: Python, FastAPI, Pydantic, SQLAlchemy.
   - Data: Supabase PostgreSQL with constraints, RLS, and indexes.

### 3.2 Out-of-Scope Boundaries
- Direct physical hardware drivers (receipt printers, barcode scanners, physical payment terminals).
- Actual banking card payment settlement (represented via standardized order payment status flags).
- Multi-currency forex conversion (all monetary transactions normalized to USD).

---

## 4. Architectural Drivers & Constraints

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ARCHITECTURAL DRIVERS                            │
├─────────────────────────┬─────────────────────────┬─────────────────────────┤
│    LEDGER IMMUTABILITY  │   CONCURRENCY SAFETY    │   TRACEABILITY & AUDIT  │
│  Append-only journal.   │  Pessimistic row locks  │  Every state transition │
│  No UPDATE or DELETE on │  (FOR UPDATE) during    │  logged in AuditEvent.  │
│  financial rows.        │  redemption to prevent  │  Zero silent logic or   │
│  Compensating entries   │  double-spending races. │  unrecorded decisions.  │
│  for adjustments.       │                         │                         │
├─────────────────────────┼─────────────────────────┼─────────────────────────┤
│   IDEMPOTENT EXECUTION  │   MATHEMATICAL ACCURACY │   SEPARATION OF CONCERNS│
│  Unique idempotency     │  Cached balances must   │  Presentation, API, and │
│  keys for all writes    │  strictly reconcile     │  Database tiers strictly│
│  prevent duplicate      │  with the sum of ledger │  isolated with clear    │
│  transactions on retry. │  entries at all times.  │  interface contracts.   │
└─────────────────────────┴─────────────────────────┴─────────────────────────┘
```

1. **Free-Tier & Open-Source Constraint**: The entire solution uses exclusively free-tier or open-source technologies (PostgreSQL / Supabase free tier, Firebase free tier, Python FastAPI, React Vite).
2. **Deterministic Reproducibility**: Given seed `20261022`, the synthetic generator must produce identical records across multiple executions, verifiable via SHA-256 dataset checksums.
3. **Ground-Truth Isolation**: Injected anomalies must be recorded in an out-of-band `ground_truth.json` file. The anomaly detection engine must evaluate raw operational data without access to ground-truth labels.
4. **Audit Decision Trail**: Rejected or failed transactions (e.g., redemption attempt exceeding balance) must be captured in an auditable decision log without generating erroneous ledger entries.

---

## 5. Evaluation Criteria & Verification Strategy

The engineering quality of the YottaFlex solution will be evaluated against six empirical benchmarks:

1. **Mathematical Ledger Consistency**:
   $$\forall \text{ Account } a, \quad \text{CachedBalance}(a) = \sum \text{LedgerCredits}(a) - \sum \text{LedgerDebits}(a)$$
   Reconciliation script must report 0 undetected balance variances across baseline accounts.
2. **Concurrency Resistance**: 100 concurrent redemption requests on an account with 500 points must execute exactly valid redemptions totaling $\le 500$ points and reject the remainder without deadlocks or negative balances.
3. **Reversal Linkage Integrity**: 100% of reversal transactions must reference a valid parent accrual ID, and cumulative reversals must never exceed original accrual points.
4. **Idempotency Guarantee**: Submitting duplicate HTTP requests with identical `Idempotency-Key` headers must return identical cached responses with zero duplicate database rows.
5. **Anomaly Engine Precision & Recall**:
   $$\text{Precision} = \frac{TP}{TP + FP} = 1.0, \quad \text{Recall} = \frac{TP}{TP + FN} \ge 0.98$$
   All 5 injected anomaly categories must be correctly identified and categorized against the isolated ground-truth file.
6. **Zero-Knowledge Token Security**: Backend must reject forged or unverified JWTs and enforce strict role boundaries across all API endpoints.

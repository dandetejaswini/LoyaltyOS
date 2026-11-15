# 02. Requirements Traceability Matrix & Specifications

## 1. Traceability Matrix Overview

This document defines the complete functional, non-functional, security, data-integrity, auditability, performance, and evaluation requirements for the YottaFlex loyalty ledger platform. Every requirement maps directly to business goals, actors, entities, acceptance criteria, and concrete test scenarios.

---

## 2. Functional Requirements (FR)

| Req ID | Exact Requirement | Business Purpose | Relevant Actor | Proposed Implementation | Related Entity / Service | Acceptance Criterion | Test Scenario | Priority |
|---|---|---|---|---|---|---|---|---|
| **FR-01** | Provision and maintain master data: Customer, Tier, Rule, Reward, and Order catalog. | Establishes root entities required for all transactional and event processing. | Analyst, Operator, Customer | REST endpoints and relational master tables with immutable primary keys. | `Customer`, `Tier`, `Rule`, `Reward`, `Order`, MasterDataService | All master records possess valid PKs, timestamps, and active status flags. | Create customer, tier, and rule; verify foreign keys and persistence. | **Critical** |
| **FR-02** | Provision a dedicated LoyaltyAccount for each registered Customer upon onboarding. | Provides an isolated ledger boundary and balance container for each customer. | Customer, System | Automatically created during customer onboarding or via idempotent account creation API. | `LoyaltyAccount`, AccountService | Exactly one active `LoyaltyAccount` per customer (`customer_id` unique constraint). | Register new customer; verify `LOY-<customer_id>` generated with 0 initial balance. | **Critical** |
| **FR-03** | Calculate Points Accrual strictly from Eligible Net Spend. | Prevents granting unearned points on taxes, shipping, or pre-discount prices. | Customer, Operator | `Eligible Net Spend = SUM(line_total - item_discounts)` excluding shipping, tax, and non-eligible SKUs. | `OrderLine`, `PointsTransaction`, AccrualService | Points calculated solely on eligible net spend; tax and shipping excluded. | Submit order of $120 ($100 items, $10 tax, $10 shipping); verify base spend evaluated is $100. | **Critical** |
| **FR-04** | Apply Tier-specific earning rates and active Rule multipliers to points calculation. | Incentivizes spend progression by rewarding higher-tier customers with bonus earning rates. | Customer, Analyst | `Points = FLOOR(eligible_net_spend * tier_multiplier * rule_multiplier)`. | `Tier`, `Rule`, AccrualService | Accrual accurately reflects active tier multiplier (Bronze: 1.0x, Silver: 1.25x, Gold: 1.5x, Platinum: 2.0x). | Gold customer spends $100 net; verify points awarded = 150 (1.5x). | **Critical** |
| **FR-05** | Record points accrual as an immutable append-only ledger transaction with lot provisioning. | Establishes auditability and tracks point expiration lifecycle via individual lots. | System, Customer | Insert into `PointsTransaction` with `entry_type='ACCRUAL'` and create linked `PointsLot` with `expires_at`. | `PointsTransaction`, `PointsLot`, LedgerService | Ledger entry created with positive amount; `PointsLot` created with identical points and 365-day expiry. | Execute accrual; verify `PointsTransaction` and `PointsLot` rows exist with identical point amounts. | **Critical** |
| **FR-06** | Validate Points Redemption against available, unexpired, unredeemed points balance. | Prevents fraudulent over-redemption and negative point balances. | Customer, Operator | Query active unexpired points sum; lock account row; check `available_balance >= requested_points`. | `LoyaltyAccount`, `PointsLot`, RedemptionService | Redemption permitted only if requested points $\le$ available balance; otherwise rejected with 422. | Customer with 200 points attempts to redeem 300 points; verify rejection with `INSUFFICIENT_BALANCE`. | **Critical** |
| **FR-07** | Allocate redemption deductions across active Points Lots using a strict FIFO policy. | Protects customer value by consuming points closest to expiration first. | Customer, System | Sort active lots by `expires_at ASC, created_at ASC`; deduct points; update lot remaining points and status. | `PointsLot`, `PointsLotAllocation`, RedemptionService | Oldest unexpired lots are exhausted first; allocation records link redemption to specific lots. | Customer has Lot A (100 pts, exp 30 days) and Lot B (100 pts, exp 60 days); redeem 150 pts; verify Lot A exhausted (100) and Lot B partially redeemed (50). | **Critical** |
| **FR-08** | Process Full Order Returns by reversing 100% of earned points referencing the original accrual. | Nullifies rewards on cancelled purchases and prevents gaming of return policies. | Operator, System | Lookup original accrual transaction; insert reversal ledger entry referencing parent `transaction_id`. | `PointsTransaction`, `PointsLot`, ReversalService | Reversal transaction created with `entry_type='REVERSAL'` referencing original `related_transaction_id`. | Full return of order; verify reversal transaction created with exact original points and linked parent ID. | **Critical** |
| **FR-09** | Process Partial Order Returns by reversing points proportionally to returned line eligible net spend. | Ensures fair, accurate point adjustments when only a subset of items are returned. | Operator, System | Calculate returned line proportion: `ROUND((returned_line_net / total_eligible_net) * original_points)`. | `OrderLine`, `PointsTransaction`, ReversalService | Cumulative reversed points across partial returns never exceed original accrual points. | Order with Item 1 ($60, 60 pts) and Item 2 ($40, 40 pts). Return Item 1; verify exactly 60 points reversed. | **Critical** |
| **FR-10** | Expire points in traceable batches when lot expiration timestamp is reached. | Manages loyalty program liabilities and enforces program expiration rules. | Operations Manager, System | Scheduled/triggered batch queries lots where `expires_at <= NOW()` and `status IN ('ACTIVE', 'PARTIALLY_REDEEMED')`. | `PointsLot`, `ExpiryBatch`, `PointsTransaction`, ExpiryService | Expired points deducted via `entry_type='EXPIRY'`; lot status set to `EXPIRED`. | Run expiry on expired lot of 50 remaining points; verify ledger debit of 50 and lot marked `EXPIRED`. | **Critical** |
| **FR-11** | Enforce strict idempotency on points expiration jobs. | Prevents duplicate point deductions if batch job is retried or interrupted. | Operations Manager, System | Filter only lots with remaining points > 0 and status != 'EXPIRED'; unique batch key constraint. | `ExpiryBatch`, `PointsLot`, ExpiryService | Running expiry job multiple times on the same date produces 0 duplicate ledger debits. | Execute expiry job twice back-to-back; verify second run processes 0 lots and adds 0 ledger entries. | **Critical** |
| **FR-12** | Track Qualifying Spend separately from Gross Spend for tier progression. | Prevents artificial tier inflation from taxes, shipping fees, or refunded amounts. | Customer, Analyst | `Qualifying Spend = SUM(eligible_net_spend) - SUM(returned_net_spend)` within rolling 12 months. | `LoyaltyAccount`, `Tier`, TierService | Tier status determined solely by cumulative qualifying spend within window. | Customer spends $500 items + $100 tax; qualifying spend increases by $500, not $600. | **High** |
| **FR-13** | Evaluate and apply immediate Tier Upgrade when qualifying spend crosses threshold. | Delights customers with immediate status recognition and unlocks higher earning rates. | Customer, System | After order completion, evaluate `qualifying_spend >= next_tier.spend_threshold`; update account tier. | `LoyaltyAccount`, `Tier`, TierService | Customer tier updated immediately upon qualifying order; new tier multiplier active for next order. | Silver customer ($950 spend) completes $60 order (Gold threshold $1000); verify tier upgraded to Gold. | **High** |
| **FR-14** | Enforce Tier Downgrade and retention evaluation on an annual qualification cycle. | Maintains program economics and encourages sustained customer engagement. | System, Analyst | Periodic check of qualifying spend within the last 365 days; downgrade if threshold not maintained. | `LoyaltyAccount`, `Tier`, TierService | If rolling spend is below threshold upon expiration, tier downgraded to appropriate lower level. | Gold customer with only $200 spend in past 12 months evaluated; downgraded to Bronze or Silver. | **Medium** |
| **FR-15** | Provide a Rewards Catalog and process Reward Redemption issuance. | Enables customers to convert points into tangible value (coupons, gift vouchers, items). | Customer, Analyst | Reward catalog with point cost; validate availability; issue unique redemption voucher code. | `Reward`, `Redemption`, RedemptionService | Redemption record created with voucher code, status `ISSUED`, and linked to ledger debit. | Redeem 500 points for $5 coupon; verify redemption record created with unique voucher code. | **High** |
| **FR-16** | Record rejected operations as auditable decisions without modifying ledger state. | Preserves security forensics and compliance audit trails without corrupting ledger math. | Operations Manager, Security | Insert into `RejectedOperation` with reason, requested payload, customer ID, and timestamp. | `RejectedOperation`, `AuditEvent`, AuditService | Rejected attempts logged with error code and details; `PointsTransaction` count remains unchanged. | Attempt redemption exceeding balance; verify rejection logged in `RejectedOperation` and ledger untouched. | **High** |

---

## 3. Non-Functional Requirements (NFR)

| Req ID | Category | Exact Requirement | Target Metric | Architectural Strategy | Priority |
|---|---|---|---|---|---|
| **NFR-01** | **Performance** | Points accrual latency under nominal load. | P95 latency < 50ms | Single ACID database transaction; optimized indexes on account and order tables. | **Critical** |
| **NFR-02** | **Performance** | Points redemption latency under nominal load. | P95 latency < 100ms | Pessimistic row locking on `LoyaltyAccount`; minimal index-supported lot queries. | **Critical** |
| **NFR-03** | **Scalability** | Support baseline synthetic dataset without performance degradation. | 20,000 customers, 100,000 orders, 300,000 transactions | Composite B-tree indexes, foreign key indexes, batch insertion pipelines. | **High** |
| **NFR-04** | **Availability** | Graceful degradation under database connection or downstream transient failures. | Error response within 500ms with standard RFC-7807 problem details | Connection pooling, retry policies with exponential backoff, health check endpoints. | **High** |
| **NFR-05** | **Maintainability** | Clean architecture with strict separation of presentation, business, and data layers. | 0 business logic in frontend; pure services in backend | FastAPI modular routers -> Service layer -> Repository layer -> PostgreSQL. | **High** |
| **NFR-06** | **Cost / Licensing** | Zero proprietary paid enterprise dependencies. | 100% Free-Tier / Open-Source | Supabase (Free tier PostgreSQL), Firebase Auth (Free tier), Python, React/Vite. | **Critical** |

---

## 4. Security Requirements (SEC)

| Req ID | Exact Requirement | Business Purpose | Implementation Mechanism | Acceptance Criterion | Priority |
|---|---|---|---|---|---|
| **SEC-01** | Dual Identity Provider support with unified internal mapping. | Allows seamless customer login via email/password (Supabase) or Google (Firebase). | `UserIdentityMapping` table mapping Supabase UID and Firebase UID to internal `user_id`. | Single customer account maintained regardless of authentication method used. | **Critical** |
| **SEC-02** | Zero frontend trust; mandatory server-side JWT verification. | Prevents identity spoofing and privilege escalation attacks. | FastAPI authentication dependency validates Supabase/Firebase cryptographic signatures. | Requests without valid Bearer token rejected with 401 Unauthorized; token claims extracted securely. | **Critical** |
| **SEC-03** | Role-Based Access Control (RBAC) across all protected routes. | Restricts administrative operations (rules, reconciliations, approvals) to authorized staff. | User roles: `CUSTOMER`, `OPERATOR`, `ANALYST`, `OPERATIONS_MANAGER`. Route-level role guards. | Customer calling operator reversal API receives 403 Forbidden. | **Critical** |
| **SEC-04** | Row-Level Security (RLS) enforcement at the database tier. | Enforces defense-in-depth data isolation directly in PostgreSQL. | Supabase RLS policies ensuring customers can only SELECT their own account, transactions, and lots. | Direct database queries using user context cannot view another customer's ledger records. | **High** |
| **SEC-05** | Safe credential management and zero secret leakage. | Protects infrastructure against unauthorized administrative access. | Service-role keys, private keys, and DB passwords stored strictly in backend `.env`; never bundled in frontend. | Frontend bundle inspection reveals zero API private keys or service-role secrets. | **Critical** |
| **SEC-06** | Minimal OAuth permission scope for Google sign-in. | Protects user privacy and adheres to principle of least privilege. | Firebase Google OAuth configured requesting only `openid`, `email`, `profile`. | Sign-in dialog does not prompt for Gmail, Google Drive, or external permissions. | **High** |
| **SEC-07** | Identity conflict and account collision prevention. | Prevents account hijacking via unverified matching email addresses. | Only link accounts if primary provider email is verified; require explicit linking workflow. | Existing email/password account cannot be hijacked by an unverified third-party OAuth account. | **High** |

---

## 5. Data-Integrity Requirements (DIR)

| Req ID | Exact Requirement | Business Purpose | Implementation Mechanism | Acceptance Criterion | Priority |
|---|---|---|---|---|---|
| **DIR-01** | Strict append-only immutability of the points ledger. | Ensures forensic tamper-resistance and accounting compliance. | No SQL `UPDATE` or `DELETE` statements allowed on `PointsTransaction`. Database triggers prevent updates. | Any `UPDATE` or `DELETE` executed against `PointsTransaction` throws an exception. | **Critical** |
| **DIR-02** | Complete referential integrity across all parent-child relationships. | Prevents orphaned transactions or broken audit lineages. | Foreign keys enforced with `ON DELETE RESTRICT` on all ledger-related tables. | Deletion of a Customer or Order with existing points transactions is blocked by database FK. | **Critical** |
| **DIR-03** | Mandatory idempotency keys for all state-changing endpoints. | Prevents double-accrual or double-redemption caused by network retries. | Client sends `Idempotency-Key` header; backend stores key in `idempotency_records` table with unique constraint. | Re-submitting identical idempotency key returns original cached response without re-executing logic. | **Critical** |
| **DIR-04** | Atomic database transactions for multi-table updates. | Eliminates partial state updates (e.g., points deducted but voucher not created). | Python context manager `async with session.begin():` wrapping ledger writes, lot updates, and balance caches. | Any unhandled exception triggers a full rollback; no orphaned rows created. | **Critical** |
| **DIR-05** | Reversal ceiling constraint: cumulative reversals $\le$ original accrual. | Prevents fraudulent over-reversals that artificially drain customer points. | Reversal service validates `SUM(existing_reversals) + requested_reversal <= original_accrual_points`. | Attempting to reverse more points than originally earned is rejected with 422 Unprocessable Entity. | **Critical** |
| **DIR-06** | Points lot balance integrity: `remaining_points <= initial_points` and $\ge 0$. | Prevents mathematical inconsistency in lot tracking. | Check constraint on `PointsLot`: `CHECK (remaining_points >= 0 AND remaining_points <= initial_points)`. | Database check constraint prevents negative remaining points on any lot. | **Critical** |

---

## 6. Auditability Requirements (AUD)

| Req ID | Exact Requirement | Business Purpose | Implementation Mechanism | Acceptance Criterion | Priority |
|---|---|---|---|---|---|
| **AUD-01** | Comprehensive audit event logging for all state transitions. | Guarantees complete non-repudiation and forensic auditability. | Every business service logs to `AuditEvent` table with actor, action, entity, before/after state, and timestamp. | Audit event created synchronously or via post-commit hook for every accrual, redemption, reversal, and expiry. | **Critical** |
| **AUD-02** | Cryptographic or sequential ID conventions across all entities. | Ensures human-readable, deterministic, and traceable entity tracking. | Prefixes: `LOY-`, `ORD-2026-`, `PTS-2026-`, `RDM-2026-`, `EXP-2026-`, `AUD-2026-`. Zero-padded integers. | All entity IDs conform to designated pattern and remain immutable. | **High** |
| **AUD-03** | Formal recording of rejected transactions as non-ledger decisions. | Enables security monitoring of brute-force redemption or return fraud. | Dedicated `RejectedOperation` table capturing rejected requests, actor, reason code, and payload. | Rejected operations are fully queryable by Operations Manager without affecting ledger math. | **High** |
| **AUD-04** | Complete audit trail for operator corrective actions. | Ensures that administrative balance corrections are traceable and authorized. | `CorrectiveAction` table tracking anomaly ID, operator ID, approval timestamp, and compensating transaction ID. | Compensating ledger adjustment must reference approved corrective action record. | **Critical** |

---

## 7. Performance Requirements (PR)

| Req ID | Metric | Threshold | Testing Strategy | Priority |
|---|---|---|---|---|
| **PR-01** | Accrual Processing Throughput | $\ge 200$ transactions/sec on local instance | Locust / pytest-benchmark simulating bulk order completions. | **High** |
| **PR-02** | Concurrent Redemption Latency | P99 < 150ms under 50 simultaneous workers | Concurrent request test script targeting shared accounts with row locks. | **Critical** |
| **PR-03** | Batch Expiry Throughput | $\ge 1,000$ expired lots processed per second | Batch execution benchmark measuring SQL lot selection and bulk ledger debit inserts. | **High** |
| **PR-04** | Reconciliation Engine Runtime | $< 30$ seconds across 300,000 transaction records | Vectorized SQL queries (`GROUP BY account_id`) comparing ledger sums against cached balances. | **High** |
| **PR-05** | API Average Response Time | $< 50$ms for read queries, $< 100$ms for transactional writes | Automated API load test measuring TTFB (Time to First Byte). | **High** |

---

## 8. Evaluation & Synthetic Data Requirements (EVR)

| Req ID | Exact Requirement | Verification Target | Implementation Strategy | Priority |
|---|---|---|---|---|
| **EVR-01** | Deterministic generation with fixed random seed `20261022`. | 100% byte-for-byte or row-for-row match across repeated runs. | Seed Python `random` and `faker` libraries with `20261022`; sort output rows deterministically. | **Critical** |
| **EVR-02** | Target scale generation: 20k customers, 100k orders, 300k points transactions. | Exact row count validation within $\pm 1\%$ of specification. | Parameterized generator script with configurable scale factor (1% starter vs 100% full). | **Critical** |
| **EVR-03** | Explicit injection of 5 designated anomaly categories. | 1. Balance drift<br>2. Over-redemption<br>3. Return without reversal<br>4. Double expiration<br>5. Gross spend tier calc | Controlled anomaly injector inserting exact labeled test cases into raw dataset. | **Critical** |
| **EVR-04** | Strict isolation of ground-truth labels. | Zero ground truth leakage into operational database tables or detection inputs. | Ground truth stored in separate `ground_truth.json` / `ground_truth.csv`; anomaly detector runs blind. | **Critical** |
| **EVR-05** | Anomaly detection performance against ground truth. | Precision = 1.0 (0 false positives), Recall $\ge 0.98$ on injected anomalies. | Automated evaluation script comparing detected anomalies against ground truth file. | **Critical** |

---

## 9. Explicit Assumptions & Unspecified Business Policies

In accordance with engineering guidelines, every necessary assumption is explicitly defined, justified, and documented below:

### Assumption 1: Points Expiration Validity Period
- **Policy**: Points lots expire exactly **365 days (1 year)** from the date of accrual at 23:59:59 UTC, unless extended by special promotion rules.
- **Rationale**: Industry standard for retail loyalty programs; ensures predictable liability accounting.

### Assumption 2: Points-Lot Allocation Strategy
- **Policy**: Points lots are consumed on a **FIFO (First-In, First-Out)** basis ordered by `expires_at ASC, created_at ASC`.
- **Rationale**: Maximizes customer value by automatically spending points nearest to expiration, minimizing accidental breakage.

### Assumption 3: Tier Qualification Window & Downgrade Cycle
- **Policy**: Tier qualification is calculated on a **Rolling 365-Day Window** of qualifying spend. Tiers upgrade immediately upon crossing spend thresholds. Downgrades are assessed at the end of each customer's 12-month membership anniversary.
- **Rationale**: Prevents erratic daily tier fluctuations while rewarding recent customer spend.

### Assumption 4: Points Rounding Policy
- **Policy**: Points earned are calculated using **Integer Floor Rounding** (`FLOOR(spend * rate)`).
- **Rationale**: Eliminates fractional point liability on financial ledgers and prevents round-up gaming on micro-transactions.

### Assumption 5: Negative Balance Policy on Order Returns
- **Policy**: If an order return reverses points that have already been redeemed (leaving available balance < 0), the account balance is permitted to reflect a **negative balance** (`available_points < 0`). While negative, all further redemptions are blocked until new accruals bring the balance back $\ge 0$.
- **Rationale**: Financial integrity requires that unearned benefits must be deducted even if already spent; prevents return fraud where customers redeem points and immediately return merchandise.

### Assumption 6: Excluded Categories from Eligible Net Spend
- **Policy**: Sales tax, shipping and handling fees, delivery tips, and gift card purchases are strictly excluded from eligible net spend and qualifying spend. Item-level promo codes and coupons are deducted from gross line price to determine net spend.
- **Rationale**: Standard retail loyalty practice; companies cannot issue loyalty liability on pass-through taxes or unearned gift card liabilities.

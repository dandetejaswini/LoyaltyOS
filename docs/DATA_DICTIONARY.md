# LoyaltyOS — Data Dictionary

**Database:** Supabase PostgreSQL 15+
**ORM:** SQLAlchemy 2.0 Async (`postgresql+asyncpg`)  
**Total Entities:** 21 Relational Tables

---

## 1. Table Grouping

- **Identity & Access (2 Tables)**: `app_users`, `user_identity_mappings`
- **Retail & Loyalty Master (8 Tables)**: `customers`, `tiers`, `loyalty_accounts`, `rules`, `orders`, `order_lines`, `order_returns`, `order_return_lines`
- **Ledger & Expiry (7 Tables)**: `points_transactions`, `points_lots`, `rewards`, `redemptions`, `points_lot_allocations`, `expiry_batches`, `expiry_batch_items`
- **Audit & Remediation (4 Tables)**: `audit_events`, `rejected_operations`, `anomaly_incidents`, `corrective_actions`

---

## 2. Table Schemas

### 2.1 Identity & Access

#### `app_users`
Stores user profile information and assigned roles.
- `id` (UUID, Primary Key): Unique internal user ID.
- `email` (VARCHAR(255), Unique, Not Null): Primary email address.
- `full_name` (VARCHAR(255)): User display name.
- `role` (VARCHAR(30), Not Null): Role (`CUSTOMER`, `OPERATOR`, `ANALYST`, `OPERATIONS_MANAGER`).
- `is_active` (BOOLEAN, Default True): Account active flag.
- `created_at` / `updated_at` (TIMESTAMPTZ): Timestamps.

#### `user_identity_mappings`
Links third-party login providers to internal user accounts.
- `id` (UUID, Primary Key): Unique mapping ID.
- `user_id` (UUID, Foreign Key -> `app_users.id`): Associated system user.
- `provider` (VARCHAR(50), Not Null): Auth provider (`supabase_password`, `firebase_google`).
- `provider_uid` (VARCHAR(255), Not Null): Unique user identifier from provider.
- `created_at` (TIMESTAMPTZ): Link creation timestamp.

---

### 2.2 Retail & Loyalty Master

#### `customers`
Stores customer retail profiles.
- `id` (UUID, Primary Key): Customer ID.
- `user_id` (UUID, Foreign Key -> `app_users.id`): Linked user identity.
- `email` (VARCHAR(255), Unique, Not Null): Customer email.
- `phone` (VARCHAR(50)): Customer contact number.
- `created_at` / `updated_at` (TIMESTAMPTZ): Timestamps.

#### `tiers`
Defines loyalty tiers, spend requirements, and point multipliers.
- `id` (UUID, Primary Key): Tier ID.
- `name` (VARCHAR(50), Unique, Not Null): Tier name (`BRONZE`, `SILVER`, `GOLD`, `PLATINUM`).
- `rank` (INTEGER, Unique, Not Null): Tier level hierarchy (1 to 4).
- `min_spend` (NUMERIC(10,2), Not Null): Minimum qualifying spend required.
- `earning_multiplier` (NUMERIC(4,2), Not Null): Points multiplier (e.g. 1.00, 1.20, 1.50, 2.00).

#### `loyalty_accounts`
Stores the active balance and lifetime metrics for each customer.
- `id` (UUID, Primary Key): Account ID.
- `customer_id` (UUID, Foreign Key -> `customers.id`, Unique): Account owner.
- `tier_id` (UUID, Foreign Key -> `tiers.id`): Current loyalty tier.
- `current_balance` (INTEGER, Not Null, Default 0): Active points balance. Can be negative on returns.
- `lifetime_accrued` (INTEGER, Not Null, Default 0): Total points earned over time.
- `lifetime_redeemed` (INTEGER, Not Null, Default 0): Total points redeemed.
- `qualifying_spend` (NUMERIC(10,2), Not Null, Default 0): 365-day merchandise spend for tier status.
- `status` (VARCHAR(20), Default 'ACTIVE'): Status (`ACTIVE`, `FROZEN`, `CLOSED`).
- `created_at` / `updated_at` (TIMESTAMPTZ): Timestamps.

#### `rules`
Stores configurable business rules for accruals and bonuses.
- `id` (UUID, Primary Key): Rule ID.
- `rule_name` (VARCHAR(100), Not Null): Name of rule.
- `rule_type` (VARCHAR(50), Not Null): Type (`BASE_ACCRUAL`, `MULTIPLIER`, `BONUS`).
- `is_active` (BOOLEAN, Default True): Active toggle.
- `multiplier` (NUMERIC(4,2)): Optional earning multiplier.
- `bonus_points` (INTEGER): Optional fixed bonus points.

#### `orders`
Records customer store orders.
- `id` (UUID, Primary Key): Order ID.
- `customer_id` (UUID, Foreign Key -> `customers.id`): Purchasing customer.
- `order_date` (TIMESTAMPTZ, Not Null): Timestamp of purchase.
- `gross_amount` (NUMERIC(10,2), Not Null): Total checkout price.
- `tax_amount` (NUMERIC(10,2), Default 0): Sales tax amount (excluded from points).
- `shipping_amount` (NUMERIC(10,2), Default 0): Shipping cost (excluded from points).
- `discount_amount` (NUMERIC(10,2), Default 0): Applied discount.
- `eligible_net_spend` (NUMERIC(10,2), Not Null): Spend qualifying for points (`gross - tax - shipping - discount`).
- `status` (VARCHAR(30), Default 'COMPLETED'): Order status.
- `accrual_status` (VARCHAR(30), Default 'PENDING'): Accrual state (`PENDING`, `ACCRUED`).

#### `order_lines`
Individual items purchased within an order.
- `id` (UUID, Primary Key): Order line ID.
- `order_id` (UUID, Foreign Key -> `orders.id`): Parent order.
- `sku` (VARCHAR(100), Not Null): Product SKU.
- `product_name` (VARCHAR(255), Not Null): Item name.
- `category` (VARCHAR(100), Not Null): Merchandise category.
- `quantity` (INTEGER, Not Null): Items purchased.
- `unit_price` (NUMERIC(10,2), Not Null): Price per unit.
- `net_amount` (NUMERIC(10,2), Not Null): Total line price.
- `is_eligible` (BOOLEAN, Default True): Indicates if line earns points.

#### `order_returns`
Tracks customer product returns and refunds.
- `id` (UUID, Primary Key): Return ID.
- `order_id` (UUID, Foreign Key -> `orders.id`): Original order.
- `return_type` (VARCHAR(20), Not Null): Return type (`FULL`, `PARTIAL`).
- `total_refund_amount` (NUMERIC(10,2), Not Null): Refund amount issued.
- `points_reversed` (INTEGER, Not Null): Points deducted for return.
- `status` (VARCHAR(30), Default 'COMPLETED'): Return status.
- `created_at` (TIMESTAMPTZ): Return timestamp.

#### `order_return_lines`
Specific merchandise items returned in a refund.
- `id` (UUID, Primary Key): Return line ID.
- `return_id` (UUID, Foreign Key -> `order_returns.id`): Parent return record.
- `order_line_id` (UUID, Foreign Key -> `order_lines.id`): Returned order line.
- `quantity` (INTEGER, Not Null): Number of units returned.
- `refund_amount` (NUMERIC(10,2), Not Null): Line refund value.

---

### 2.3 Double-Entry Ledger & Expiry

#### `points_transactions` *(Append-Only Ledger Journal)*
The core immutable audit journal for all balance updates.
- `id` (UUID, Primary Key): Unique transaction ID.
- `account_id` (UUID, Foreign Key -> `loyalty_accounts.id`): Target account.
- `order_id` (UUID, Foreign Key -> `orders.id`, Nullable): Linked order if accrual.
- `entry_type` (VARCHAR(30), Not Null): Type (`ACCRUAL`, `REDEMPTION`, `REVERSAL`, `EXPIRY`, `ADJUSTMENT_CREDIT`, `ADJUSTMENT_DEBIT`).
- `direction` (VARCHAR(10), Not Null): Direction (`CREDIT`, `DEBIT`).
- `points` (INTEGER, Not Null): Points amount. Always positive.
- `running_balance` (INTEGER, Not Null): Account balance immediately after this entry.
- `idempotency_key` (VARCHAR(255), Unique, Not Null): Unique key preventing duplicate processing.
- `notes` (TEXT): Audit explanation.
- `created_at` (TIMESTAMPTZ, Default NOW()): Immutable creation timestamp.
- **Trigger**: `tg_points_transactions_immutable` aborts any `UPDATE` or `DELETE` attempt.

#### `points_lots` *(FIFO Depletion Tracker)*
Tracks individual points batches to enforce first-in, first-out expiration.
- `id` (UUID, Primary Key): Lot ID.
- `transaction_id` (UUID, Foreign Key -> `points_transactions.id`): Originating credit entry.
- `account_id` (UUID, Foreign Key -> `loyalty_accounts.id`): Account owner.
- `initial_points` (INTEGER, Not Null): Starting point count.
- `remaining_points` (INTEGER, Not Null): Unspent points remaining in this lot.
- `status` (VARCHAR(30), Default 'ACTIVE'): Status (`ACTIVE`, `PARTIALLY_REDEEMED`, `EXHAUSTED`, `EXPIRED`, `REVERSED`).
- `expires_at` (TIMESTAMPTZ, Not Null): Expiry date (created + 365 days).
- `created_at` (TIMESTAMPTZ): Lot creation date.

#### `rewards`
Catalog of vouchers and perks available for customer redemption.
- `id` (UUID, Primary Key): Reward ID.
- `name` (VARCHAR(100), Not Null): Reward title.
- `reward_type` (VARCHAR(50), Not Null): Type (`VOUCHER`, `MERCHANDISE`, `EXPERIENCE`).
- `points_required` (INTEGER, Not Null): Point cost to redeem.
- `monetary_value` (NUMERIC(10,2), Not Null): Equivalent currency value.
- `is_active` (BOOLEAN, Default True): Active status.

#### `redemptions`
Completed reward redemptions.
- `id` (UUID, Primary Key): Redemption ID.
- `account_id` (UUID, Foreign Key -> `loyalty_accounts.id`): Redeeming account.
- `reward_id` (UUID, Foreign Key -> `rewards.id`): Chosen reward.
- `transaction_id` (UUID, Foreign Key -> `points_transactions.id`): Associated debit transaction.
- `points_redeemed` (INTEGER, Not Null): Points spent.
- `voucher_code` (VARCHAR(100), Unique, Not Null): Cryptographic single-use voucher code.
- `status` (VARCHAR(30), Default 'COMPLETED'): Status.
- `created_at` (TIMESTAMPTZ): Redemption timestamp.

#### `points_lot_allocations` *(Append-Only)*
Links redemptions to the specific points lots depleted under FIFO rules.
- `id` (UUID, Primary Key): Allocation ID.
- `redemption_id` (UUID, Foreign Key -> `redemptions.id`): Parent redemption.
- `lot_id` (UUID, Foreign Key -> `points_lots.id`): Depleted lot.
- `points_allocated` (INTEGER, Not Null): Points deducted from this lot.
- `created_at` (TIMESTAMPTZ): Allocation timestamp.

#### `expiry_batches`
Audit records for automated expiration runs.
- `id` (UUID, Primary Key): Batch ID.
- `batch_date` (DATE, Not Null): Date of execution.
- `total_accounts_affected` (INTEGER, Default 0): Accounts with expired points.
- `total_points_expired` (INTEGER, Default 0): Total points removed.
- `status` (VARCHAR(30), Default 'COMPLETED'): Batch status.
- `created_at` (TIMESTAMPTZ): Execution timestamp.

#### `expiry_batch_items` *(Append-Only)*
Details each lot expired in an expiry batch.
- `id` (UUID, Primary Key): Item ID.
- `batch_id` (UUID, Foreign Key -> `expiry_batches.id`): Parent batch.
- `lot_id` (UUID, Foreign Key -> `points_lots.id`): Expired lot.
- `account_id` (UUID, Foreign Key -> `loyalty_accounts.id`): Affected account.
- `points_expired` (INTEGER, Not Null): Points deducted.
- `transaction_id` (UUID, Foreign Key -> `points_transactions.id`): Linked journal entry.

---

### 2.4 Audit, Intelligence & Remediation

#### `audit_events` *(Append-Only)*
Security and administrative action log.
- `id` (UUID, Primary Key): Audit event ID.
- `actor_id` (UUID, Foreign Key -> `app_users.id`, Nullable): User who performed the action.
- `event_type` (VARCHAR(100), Not Null): Action name (e.g. `USER_LOGIN`, `CORRECTIVE_ACTION_APPROVED`).
- `entity_type` (VARCHAR(50), Not Null): Affected table name.
- `entity_id` (VARCHAR(100), Not Null): Primary key of affected record.
- `payload` (JSONB, Default '{}'): Event context details.
- `created_at` (TIMESTAMPTZ): Event timestamp.

#### `rejected_operations`
Tracks invalid or blocked transactions (e.g. insufficient points, self-approval attempts).
- `id` (UUID, Primary Key): Record ID.
- `account_id` (UUID, Foreign Key -> `loyalty_accounts.id`, Nullable): Account involved.
- `operation_type` (VARCHAR(50), Not Null): Attempted action.
- `rejection_reason` (TEXT, Not Null): Error explanation.
- `payload` (JSONB): Attempted request payload.
- `created_at` (TIMESTAMPTZ): Timestamp.

#### `anomaly_incidents`
Issues detected by the LLIRE intelligence engine.
- `id` (UUID, Primary Key): Incident ID.
- `detector_name` (VARCHAR(100), Not Null): Detector that flagged the issue.
- `entity_type` (VARCHAR(50), Not Null): Affected object type (`ACCOUNT`, `ORDER`, `LOT`).
- `entity_id` (VARCHAR(100), Not Null): ID of affected object.
- `severity` (VARCHAR(20), Not Null): Severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- `discrepancy_amount` (NUMERIC(10,2), Default 0): Financial or points discrepancy.
- `evidence_payload` (JSONB, Not Null): Complete 7-answer diagnostic payload.
- `fingerprint` (VARCHAR(64), Not Null): SHA-256 hash preventing duplicate incident creation.
- `status` (VARCHAR(30), Default 'DETECTED'): Incident state (`DETECTED`, `INVESTIGATING`, `PENDING_APPROVAL`, `RESOLVED`, `DISMISSED`).
- `created_at` / `updated_at` (TIMESTAMPTZ): Timestamps.

#### `corrective_actions`
Tracks proposed and approved ledger adjustments for detected anomalies.
- `id` (UUID, Primary Key): Action ID.
- `incident_id` (UUID, Foreign Key -> `anomaly_incidents.id`): Associated anomaly.
- `account_id` (UUID, Foreign Key -> `loyalty_accounts.id`): Account being corrected.
- `action_type` (VARCHAR(50), Not Null): Correction type (`ADJUSTMENT_CREDIT`, `ADJUSTMENT_DEBIT`, `ACCOUNT_FREEZE`, `ACCOUNT_UNFREEZE`).
- `adjustment_points` (INTEGER): Points adjustment amount.
- `justification` (TEXT, Not Null): Business reason for the correction.
- `proposer_id` (UUID, Foreign Key -> `app_users.id`, Not Null): Manager who created proposal.
- `approver_id` (UUID, Foreign Key -> `app_users.id`, Nullable): Second manager who approved.
- `approval_status` (VARCHAR(30), Default 'PENDING_APPROVAL'): State (`PENDING_APPROVAL`, `APPROVED`, `REJECTED`).
- `rejection_reason` (TEXT): Reason if rejected.
- `transaction_id` (UUID, Foreign Key -> `points_transactions.id`, Nullable): Executed compensating transaction.
- `created_at` / `updated_at` (TIMESTAMPTZ): Timestamps.
- **Rule**: `proposer_id != approver_id` is enforced by database constraint and application logic.

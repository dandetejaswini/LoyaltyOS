# LoyaltyOS — Data Dictionary

**Product Name:** LoyaltyOS — Intelligent Loyalty & Ledger Management Platform  
**Target Database:** Supabase PostgreSQL 15+  
**ORM:** SQLAlchemy 2.0 Async (`postgresql+asyncpg`)  
**Total Relational Entities:** 21 Tables

---

## 1. Entity Module Overview

```
Identity & Access (2 Tables)
├── app_users
└── user_identity_mappings

Retail & Loyalty Master (8 Tables)
├── customers
├── tiers
├── loyalty_accounts
├── rules
├── orders
├── order_lines
├── order_returns
└── order_return_lines

Double-Entry Ledger & Expiry (7 Tables)
├── points_transactions (Append-Only)
├── points_lots (FIFO Depletion Guard)
├── rewards
├── redemptions
├── points_lot_allocations (Append-Only)
├── expiry_batches
└── expiry_batch_items (Append-Only)

Intelligence, Audit & Remediation (4 Tables)
├── audit_events (Append-Only)
├── rejected_operations
├── anomaly_incidents
└── corrective_actions
```

---

## 2. Table Specifications

### 2.1 Identity & Access Module

#### `app_users`
Stores internal system user accounts and authoritative role assignments.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY` | Unique internal user identifier. |
| `email` | `VARCHAR(255)` | `UNIQUE, NOT NULL` | Verified primary email address. |
| `full_name` | `VARCHAR(255)` | `NULLABLE` | Display name of user. |
| `role` | `VARCHAR(30)` | `NOT NULL, DEFAULT 'CUSTOMER'` | `CHECK (role IN ('CUSTOMER', 'OPERATOR', 'ANALYST', 'OPERATIONS_MANAGER'))`. |
| `is_active` | `BOOLEAN` | `NOT NULL, DEFAULT TRUE` | Active account status flag. |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT NOW()` | Record creation timestamp. |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT NOW()` | Last update timestamp. |

*Indexes:* `idx_app_users_email` (B-tree on `email`).  
*Security:* RLS enabled (`user_read_own_record`: `auth.uid() = id`).

#### `user_identity_mappings`
Maps external authentication providers (Supabase Password, Firebase Google) to internal `app_users`.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY` | Mapping record identifier. |
| `user_id` | `UUID` | `NOT NULL, FK -> app_users.id` | Internal user reference (ON DELETE RESTRICT). |
| `provider` | `VARCHAR(30)` | `NOT NULL` | `CHECK (provider IN ('SUPABASE_PASSWORD', 'FIREBASE_GOOGLE'))`. |
| `provider_uid`| `VARCHAR(255)` | `NOT NULL` | External subject ID from token. |
| `email` | `VARCHAR(255)` | `NOT NULL` | Provider email address. |
| `email_verified`| `BOOLEAN` | `NOT NULL, DEFAULT FALSE` | Email verification flag from provider. |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT NOW()` | Linked timestamp. |
| `last_sign_in_at`| `TIMESTAMPTZ`| `NULLABLE` | Most recent authenticated sign-in. |

*Constraints:* `UNIQUE (provider, provider_uid)`.  
*Indexes:* `idx_user_mappings_user`, `idx_user_mappings_email`.  
*Security:* RLS enabled (`mapping_read_own_identities`: `auth.uid() = user_id`).

---

### 2.2 Retail & Loyalty Master Module

#### `customers`
Customer retail profile linked 1:1 with an `app_users` record.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `customer_id` | `VARCHAR(32)` | `PRIMARY KEY` | Business customer identifier (`CUST-XXXXXX`). |
| `user_id` | `UUID` | `UNIQUE, NULLABLE, FK -> app_users.id` | Associated authentication user account. |
| `email` | `VARCHAR(255)` | `UNIQUE, NOT NULL` | Contact email address. |
| `first_name` | `VARCHAR(100)` | `NOT NULL` | Customer first name. |
| `last_name` | `VARCHAR(100)` | `NOT NULL` | Customer last name. |
| `phone` | `VARCHAR(20)` | `NULLABLE` | Contact phone number. |
| `status` | `VARCHAR(20)` | `NOT NULL, DEFAULT 'ACTIVE'` | `CHECK (status IN ('ACTIVE', 'SUSPENDED', 'MERGED', 'DELETED'))`. |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT NOW()` | Creation timestamp. |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT NOW()` | Last update timestamp. |

*Security:* RLS enabled (`customer_read_own_profile`: `auth.uid() = user_id`).

#### `tiers`
Loyalty program tier thresholds and multiplier definitions.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `tier_id` | `VARCHAR(32)` | `PRIMARY KEY` | Identifier (`TIER-BRONZE`, `TIER-SILVER`, etc.). |
| `name` | `VARCHAR(50)` | `NOT NULL` | Tier display name. |
| `rank` | `INT` | `NOT NULL, UNIQUE` | Progression rank (`1` = Bronze, `4` = Platinum). |
| `min_spend` | `NUMERIC(12,2)` | `NOT NULL, CHECK (min_spend >= 0)` | Qualifying spend threshold in rolling 365 days. |
| `earning_multiplier`| `NUMERIC(4,2)`| `NOT NULL, CHECK (earning_multiplier >= 1.0)` | Multiplier applied to net spend points. |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT NOW()` | Creation timestamp. |

#### `loyalty_accounts`
The primary financial account holding real-time customer balances.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `account_id` | `VARCHAR(32)` | `PRIMARY KEY` | Unique account identifier (`LOY-CUST-XXXXXX`). |
| `customer_id` | `VARCHAR(32)` | `NOT NULL, FK -> customers.customer_id` | Customer owner reference. |
| `tier_id` | `VARCHAR(32)` | `NOT NULL, FK -> tiers.tier_id` | Current assigned loyalty tier. |
| `current_balance`| `INT` | `NOT NULL, DEFAULT 0` | Available points balance. Can be negative post-return. |
| `lifetime_accrued`| `INT` | `NOT NULL, DEFAULT 0, CHECK (lifetime_accrued >= 0)` | Cumulative points earned since account inception. |
| `lifetime_redeemed`| `INT`| `NOT NULL, DEFAULT 0, CHECK (lifetime_redeemed >= 0)`| Cumulative points redeemed. |
| `qualifying_spend`| `NUMERIC(12,2)`| `NOT NULL, DEFAULT 0, CHECK (qualifying_spend >= 0)` | 365-day net spend contributing to tier rank. |
| `status` | `VARCHAR(20)` | `NOT NULL, DEFAULT 'ACTIVE'` | `CHECK (status IN ('ACTIVE', 'FROZEN', 'CLOSED'))`. |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT NOW()` | Account opening timestamp. |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT NOW()` | Last update timestamp. |

*Security:* RLS enabled (`customer_read_own_account`: customer lookup via `auth.uid()`).

#### `orders` & `order_lines`
Stores retail POS orders and line items. Net spend calculates points accrual.

- `orders`: `order_id` (PK), `customer_id` (FK), `gross_amount`, `tax_amount`, `shipping_amount`, `discount_amount`, `eligible_net_spend`, `status`, `accrual_status`.
- `order_lines`: `order_line_id` (PK), `order_id` (FK), `sku`, `category`, `quantity`, `unit_price`, `item_discount`, `is_eligible`.
- *Security:* RLS enabled (`customer_read_own_orders`, `customer_read_own_order_lines`).

#### `order_returns` & `order_return_lines`
Captures return events and tracks proportional points reversals.

- `order_returns`: `return_id` (PK), `order_id` (FK), `return_type` (`FULL`/`PARTIAL`), `total_refund_amount`, `points_reversed`, `status`.
- `order_return_lines`: `return_line_id` (PK), `return_id` (FK), `order_line_id` (FK), `quantity_returned`, `refund_amount`.

---

### 2.3 Double-Entry Ledger & Expiry Module

#### `points_transactions`
**Append-only** immutable ledger journal recording all credits and debits.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `transaction_id`| `VARCHAR(32)`| `PRIMARY KEY` | Ledger journal transaction ID (`TX-XXXXXX`). |
| `account_id` | `VARCHAR(32)` | `NOT NULL, FK -> loyalty_accounts` | Target loyalty account. |
| `order_id` | `VARCHAR(32)` | `NULLABLE, FK -> orders` | Related order for accrual/return. |
| `entry_type` | `VARCHAR(30)` | `NOT NULL` | `CHECK (entry_type IN ('ACCRUAL', 'REDEMPTION', 'REVERSAL', 'EXPIRY', 'ADJUSTMENT_CREDIT', 'ADJUSTMENT_DEBIT'))`. |
| `direction` | `VARCHAR(10)` | `NOT NULL` | `CHECK (direction IN ('CREDIT', 'DEBIT'))`. |
| `points` | `INT` | `NOT NULL, CHECK (points <> 0)` | Quantity of points (signed: positive or negative). |
| `running_balance`| `INT` | `NOT NULL` | Account balance immediately after transaction. |
| `idempotency_key`| `VARCHAR(100)`| `UNIQUE, NOT NULL` | Client idempotency key preventing duplicate processing. |
| `notes` | `TEXT` | `NULLABLE` | Business or remediation audit note. |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT NOW()` | Immutable ledger entry timestamp. |

*Immutability Guard:* PostgreSQL trigger `tg_points_transactions_immutable` raises an exception on any `UPDATE` or `DELETE`.  
*Security:* RLS enabled (`customer_read_own_transactions`).

#### `points_lots`
Tracks individual points batches for FIFO depletion and 365-day expiration.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `lot_id` | `VARCHAR(32)` | `PRIMARY KEY` | Unique lot identifier (`LOT-XXXXXX`). |
| `transaction_id`| `VARCHAR(32)`| `NOT NULL, FK -> points_transactions`| Originating accrual transaction. |
| `account_id` | `VARCHAR(32)` | `NOT NULL, FK -> loyalty_accounts` | Owning loyalty account. |
| `initial_points`| `INT` | `NOT NULL, CHECK (initial_points > 0)`| Original credited points. |
| `remaining_points`| `INT` | `NOT NULL, CHECK (remaining_points >= 0)`| Unredeemed points balance in lot. |
| `status` | `VARCHAR(20)` | `NOT NULL, DEFAULT 'ACTIVE'` | `CHECK (status IN ('ACTIVE', 'PARTIALLY_REDEEMED', 'EXHAUSTED', 'EXPIRED', 'REVERSED'))`. |
| `expires_at` | `TIMESTAMPTZ` | `NOT NULL` | Expiration cutoff timestamp (accrual + 365 days). |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT NOW()` | Creation timestamp. |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT NOW()` | Last depletion update timestamp. |

*Immutability Guard:* Trigger `tg_points_lots_immutability_guard` blocks `DELETE`, core field edits, and prevents `remaining_points` from increasing.  
*Security:* RLS enabled (`customer_read_own_lots`).

#### `rewards` & `redemptions`
Catalog of redeemable items and redeemed voucher records.

- `rewards`: `reward_id` (PK), `name`, `reward_type`, `points_required`, `monetary_value`, `stock_quantity`, `is_active`.
- `redemptions`: `redemption_id` (PK), `account_id` (FK), `reward_id` (FK), `transaction_id` (FK), `points_redeemed`, `voucher_code` (UNIQUE), `status`.
- *Security:* RLS enabled (`customer_read_own_redemptions`).

#### `points_lot_allocations`
Append-only linkage recording exact lot deductions per redemption.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `allocation_id`| `VARCHAR(32)`| `PRIMARY KEY` | Allocation record ID. |
| `lot_id` | `VARCHAR(32)` | `NOT NULL, FK -> points_lots` | Depleted lot reference. |
| `redemption_id`| `VARCHAR(32)` | `NULLABLE, FK -> redemptions` | Consuming redemption reference. |
| `transaction_id`| `VARCHAR(32)`| `NOT NULL, FK -> points_transactions`| Ledger debit transaction reference. |
| `points_allocated`| `INT` | `NOT NULL, CHECK (points_allocated > 0)`| Points deducted from lot. |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT NOW()` | Allocation timestamp. |

*Immutability Guard:* Trigger `tg_points_lot_allocations_immutable` blocks `UPDATE` and `DELETE`.

#### `expiry_batches` & `expiry_batch_items`
Audit trail of batch expiration executions.

- `expiry_batches`: `batch_id` (PK), `cutoff_date`, `total_lots_processed`, `total_points_expired`, `status`.
- `expiry_batch_items`: `item_id` (PK), `batch_id` (FK), `lot_id` (FK), `transaction_id` (FK), `points_expired`.
- *Immutability Guard:* Trigger `tg_expiry_batch_items_immutable` blocks `UPDATE` and `DELETE`.

---

### 2.4 Intelligence, Audit & Remediation Module

#### `audit_events`
Immutable security and administrative audit event trail.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `event_id` | `VARCHAR(32)` | `PRIMARY KEY` | Audit event identifier. |
| `user_id` | `UUID` | `NULLABLE, FK -> app_users` | Actor who performed the action. |
| `event_type` | `VARCHAR(50)` | `NOT NULL` | Event classification (`ORDER_ACCRUAL`, `PROPOSAL_APPROVED`, etc.). |
| `entity_type` | `VARCHAR(50)` | `NOT NULL` | Target entity (`account`, `order`, `anomaly`). |
| `entity_id` | `VARCHAR(64)` | `NOT NULL` | Target entity ID. |
| `old_value` | `JSONB` | `NULLABLE` | Pre-operation state snapshot. |
| `new_value` | `JSONB` | `NULLABLE` | Post-operation state snapshot. |
| `metadata` | `JSONB` | `NULLABLE` | Client IP, user agent, execution context. |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT NOW()` | Immutable log timestamp. |

*Immutability Guard:* Trigger `tg_audit_events_immutable` blocks `UPDATE` and `DELETE`.

#### `rejected_operations`
Captures rejected API operations (e.g. duplicate idempotency, self-approval attempts, insufficient points).

- Columns: `rejection_id` (PK), `operation_type`, `entity_id`, `reason_code`, `rejection_details` (JSONB), `attempted_by`, `created_at`.

#### `anomaly_incidents`
Stores anomalies flagged by the LLIRE intelligence engine.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `incident_id` | `VARCHAR(32)` | `PRIMARY KEY` | Incident identifier (`ANOM-XXXXXX`). |
| `issue_type` | `VARCHAR(50)` | `NOT NULL` | Anomaly category (`BALANCE_MISMATCH`, `OVER_REDEMPTION`, etc.). |
| `entity_type` | `VARCHAR(30)` | `NOT NULL` | Target entity type (`account`, `order`, `lot`). |
| `entity_id` | `VARCHAR(64)` | `NOT NULL` | Target entity ID. |
| `variance_amount`| `NUMERIC(12,2)`| `NOT NULL, DEFAULT 0` | Measured discrepancy or points at risk. |
| `status` | `VARCHAR(20)` | `NOT NULL, DEFAULT 'DETECTED'` | `CHECK (status IN ('DETECTED', 'INVESTIGATING', 'RESOLVED', 'DISMISSED'))`. |
| `investigator_id`| `UUID` | `NULLABLE, FK -> app_users` | Assigned operations manager. |
| `fingerprint` | `VARCHAR(64)` | `UNIQUE, NOT NULL` | SHA-256 hash preventing duplicate incident creation across scans. |
| `details` | `JSONB` | `NOT NULL, DEFAULT '{}'` | Evidence payload, rule violated, and recommendations. |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT NOW()` | Detection timestamp. |
| `resolved_at` | `TIMESTAMPTZ` | `NULLABLE` | Remediation resolution timestamp. |

#### `corrective_actions`
Stores human-controlled dual-key corrective action proposals and outcomes.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `action_id` | `VARCHAR(32)` | `PRIMARY KEY` | Action record ID (`ACT-XXXXXX`). |
| `incident_id` | `VARCHAR(32)` | `NOT NULL, FK -> anomaly_incidents`| Associated anomaly incident. |
| `action_type` | `VARCHAR(30)` | `NOT NULL` | `CHECK (action_type IN ('ADJUSTMENT_CREDIT', 'ADJUSTMENT_DEBIT', 'REVERSAL_REVIEW', 'ACCOUNT_FREEZE', 'ACCOUNT_UNFREEZE', 'DISMISS_FINDING'))`. |
| `proposed_points`| `INT` | `NOT NULL, DEFAULT 0` | Compensating points adjustment. |
| `proposed_by` | `VARCHAR(64)` | `NOT NULL` | Proposer user ID. |
| `approval_status`| `VARCHAR(20)`| `NOT NULL, DEFAULT 'PENDING_APPROVAL'` | `CHECK (approval_status IN ('PENDING_APPROVAL', 'APPROVED', 'REJECTED'))`. |
| `approver_id` | `VARCHAR(64)` | `NULLABLE` | Distinct reviewer ID (`approver_id <> proposed_by`). |
| `rejection_reason`| `TEXT` | `NULLABLE` | Mandatory business rationale if rejected. |
| `execution_status`| `VARCHAR(20)`| `NOT NULL, DEFAULT 'PENDING'` | `CHECK (execution_status IN ('PENDING', 'EXECUTED', 'FAILED'))`. |
| `compensating_tx_id`| `VARCHAR(32)`| `NULLABLE, FK -> points_transactions`| Executed compensating ledger transaction. |
| `notes` | `TEXT` | `NULLABLE` | Audit justification notes ($\ge 10$ characters). |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT NOW()` | Proposal timestamp. |
| `executed_at` | `TIMESTAMPTZ` | `NULLABLE` | Execution timestamp. |

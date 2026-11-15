# LoyaltyOS — Data Dictionary

**Database:** Supabase PostgreSQL 15+
**ORM:** SQLAlchemy 2.0 Async (`postgresql+asyncpg`)  
**Total Entities:** 21 Relational Tables

---

## 1. Entity Module Overview

| Module | Table Name | Purpose | Immutability Trigger |
| :--- | :--- | :--- | :---: |
| **Identity & Access** | `app_users` | User credentials and RBAC roles | — |
| | `user_identity_mappings` | OAuth / password identity links | — |
| **Retail & Loyalty Master** | `customers` | Customer retail profiles | — |
| | `tiers` | Tier levels and earning multipliers | — |
| | `loyalty_accounts` | Live points balances and spend metrics | — |
| | `rules` | Accrual rules and promotional bonuses | — |
| | `orders` | Customer checkout purchases | — |
| | `order_lines` | Individual purchased items | — |
| | `order_returns` | Product returns and refunds | — |
| | `order_return_lines` | Returned line items | — |
| **Double-Entry Ledger** | `points_transactions` | Immutable journal for credits and debits | Yes (`tg_points_transactions_immutable`) |
| | `points_lots` | 365-day FIFO lot expiration tracker | — |
| | `rewards` | Redemption perk catalog | — |
| | `redemptions` | Customer perk redemptions and vouchers | — |
| | `points_lot_allocations` | Audit map of FIFO lots depleted per redemption | Yes (`tg_points_lot_allocations_immutable`) |
| | `expiry_batches` | Records automated expiration batch runs | — |
| | `expiry_batch_items` | Individual lots expired in a batch | Yes (`tg_expiry_batch_items_immutable`) |
| **Audit & Remediation** | `audit_events` | Security and administrative audit trail | Yes (`tg_audit_events_immutable`) |
| | `rejected_operations` | Blocked operations (e.g. self-approval) | Yes (`tg_rejected_operations_immutable`) |
| | `anomaly_incidents` | LLIRE detected issues and evidence | — |
| | `corrective_actions` | Proposed and approved dual-key corrections | — |

---

## 2. Table Specifications

### 2.1 Identity & Access Module

#### `app_users`
Stores user profile information and assigned roles.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Unique internal user ID |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | Primary email address |
| `full_name` | VARCHAR(255) | NULLABLE | User display name |
| `role` | VARCHAR(30) | NOT NULL | Role: `CUSTOMER`, `OPERATOR`, `ANALYST`, `OPERATIONS_MANAGER` |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Active account flag |
| `created_at` | TIMESTAMPTZ | NOT NULL | Record creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Last update timestamp |

#### `user_identity_mappings`
Maps external login providers (Supabase Password, Google Firebase) to internal users.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Unique mapping ID |
| `user_id` | UUID | FK -> `app_users.id`, NOT NULL | Internal user reference |
| `provider` | VARCHAR(50) | NOT NULL | Provider name (`supabase_password`, `firebase_google`) |
| `provider_uid` | VARCHAR(255) | NOT NULL | User ID given by the external provider |
| `created_at` | TIMESTAMPTZ | NOT NULL | Mapping creation timestamp |

---

### 2.2 Retail & Loyalty Master Module

#### `customers`
Stores customer retail profiles.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Customer identifier |
| `user_id` | UUID | FK -> `app_users.id`, NULLABLE | Associated user account |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | Primary customer contact email |
| `phone` | VARCHAR(50) | NULLABLE | Contact phone number |
| `created_at` | TIMESTAMPTZ | NOT NULL | Customer record creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Last update timestamp |

#### `tiers`
Defines loyalty tiers, spend requirements, and point multipliers.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Tier identifier |
| `name` | VARCHAR(50) | UNIQUE, NOT NULL | Tier level: `BRONZE`, `SILVER`, `GOLD`, `PLATINUM` |
| `rank` | INTEGER | UNIQUE, NOT NULL | Level ranking (1, 2, 3, 4) |
| `min_spend` | NUMERIC(10,2) | NOT NULL | Minimum 365-day merchandise spend needed |
| `earning_multiplier` | NUMERIC(4,2) | NOT NULL | Points multiplier (e.g. 1.00, 1.20, 1.50, 2.00) |

#### `loyalty_accounts`
Stores active balance and lifetime metrics for each customer.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Account identifier |
| `customer_id` | UUID | FK -> `customers.id`, UNIQUE, NOT NULL | Account owner |
| `tier_id` | UUID | FK -> `tiers.id`, NOT NULL | Current loyalty tier |
| `current_balance` | INTEGER | NOT NULL, DEFAULT 0 | Active point balance (can be negative after returns) |
| `lifetime_accrued` | INTEGER | NOT NULL, DEFAULT 0 | Total points earned over time |
| `lifetime_redeemed`| INTEGER | NOT NULL, DEFAULT 0 | Total points spent |
| `qualifying_spend` | NUMERIC(10,2) | NOT NULL, DEFAULT 0 | Rolling 365-day spend for tier qualification |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'ACTIVE' | Account state: `ACTIVE`, `FROZEN`, `CLOSED` |
| `created_at` | TIMESTAMPTZ | NOT NULL | Account creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Last update timestamp |

#### `rules`
Stores configurable loyalty rules and bonus point promotions.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Rule identifier |
| `rule_name` | VARCHAR(100) | NOT NULL | Descriptive rule name |
| `rule_type` | VARCHAR(50) | NOT NULL | Rule category: `BASE_ACCRUAL`, `MULTIPLIER`, `BONUS` |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Active toggle |
| `multiplier` | NUMERIC(4,2) | NULLABLE | Promotional earning multiplier |
| `bonus_points` | INTEGER | NULLABLE | Flat bonus point award |

#### `orders`
Records customer store orders.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Order identifier |
| `customer_id` | UUID | FK -> `customers.id`, NOT NULL | Purchasing customer |
| `order_date` | TIMESTAMPTZ | NOT NULL | Order placement timestamp |
| `gross_amount` | NUMERIC(10,2) | NOT NULL | Total checkout price |
| `tax_amount` | NUMERIC(10,2) | NOT NULL, DEFAULT 0 | Sales tax (excluded from points) |
| `shipping_amount` | NUMERIC(10,2) | NOT NULL, DEFAULT 0 | Shipping fee (excluded from points) |
| `discount_amount` | NUMERIC(10,2) | NOT NULL, DEFAULT 0 | Discount deducted |
| `eligible_net_spend`| NUMERIC(10,2) | NOT NULL | Eligible spend = `gross - tax - shipping - discount` |
| `status` | VARCHAR(30) | NOT NULL, DEFAULT 'COMPLETED' | Order status |
| `accrual_status` | VARCHAR(30) | NOT NULL, DEFAULT 'PENDING' | Points status: `PENDING`, `ACCRUED` |

#### `order_lines`
Individual items purchased within an order.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Order line identifier |
| `order_id` | UUID | FK -> `orders.id`, NOT NULL | Parent order |
| `sku` | VARCHAR(100) | NOT NULL | Product SKU code |
| `product_name` | VARCHAR(255) | NOT NULL | Merchandise item name |
| `category` | VARCHAR(100) | NOT NULL | Item product category |
| `quantity` | INTEGER | NOT NULL | Number of units purchased |
| `unit_price` | NUMERIC(10,2) | NOT NULL | Unit retail price |
| `net_amount` | NUMERIC(10,2) | NOT NULL | Total line cost (`unit_price * quantity`) |
| `is_eligible` | BOOLEAN | NOT NULL, DEFAULT TRUE | Flag indicating if item earns loyalty points |

#### `order_returns`
Tracks customer returns and refund events.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Return identifier |
| `order_id` | UUID | FK -> `orders.id`, NOT NULL | Original purchase order |
| `return_type` | VARCHAR(20) | NOT NULL | Return scope: `FULL`, `PARTIAL` |
| `total_refund_amount`| NUMERIC(10,2) | NOT NULL | Total monetary refund issued |
| `points_reversed` | INTEGER | NOT NULL | Points reversed for this return |
| `status` | VARCHAR(30) | NOT NULL, DEFAULT 'COMPLETED' | Return status |
| `created_at` | TIMESTAMPTZ | NOT NULL | Return processing timestamp |

#### `order_return_lines`
Specific merchandise items returned.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Return line identifier |
| `return_id` | UUID | FK -> `order_returns.id`, NOT NULL | Parent return record |
| `order_line_id` | UUID | FK -> `order_lines.id`, NOT NULL | Original order line returned |
| `quantity` | INTEGER | NOT NULL | Units returned |
| `refund_amount` | NUMERIC(10,2) | NOT NULL | Monetary refund for this item |

---

### 2.3 Double-Entry Ledger & Expiry Module

#### `points_transactions` *(Append-Only Ledger Journal)*
The immutable core financial journal for all point transactions.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Unique transaction ID |
| `account_id` | UUID | FK -> `loyalty_accounts.id`, NOT NULL | Affected loyalty account |
| `order_id` | UUID | FK -> `orders.id`, NULLABLE | Linked order (for accruals and returns) |
| `entry_type` | VARCHAR(30) | NOT NULL | `ACCRUAL`, `REDEMPTION`, `REVERSAL`, `EXPIRY`, `ADJUSTMENT_CREDIT`, `ADJUSTMENT_DEBIT` |
| `direction` | VARCHAR(10) | NOT NULL | Direction: `CREDIT`, `DEBIT` |
| `points` | INTEGER | NOT NULL | Points amount (always positive) |
| `running_balance` | INTEGER | NOT NULL | Balance immediately after this entry |
| `idempotency_key` | VARCHAR(255) | UNIQUE, NOT NULL | Key preventing duplicate processing |
| `notes` | TEXT | NULLABLE | Audit explanation or reference ID |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Immutable transaction timestamp |

*Note: Protected by trigger `tg_points_transactions_immutable` (blocks all `UPDATE` and `DELETE` queries).*

#### `points_lots` *(FIFO Depletion Tracker)*
Tracks individual batches of points to enforce 365-day expiration in FIFO order.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Lot identifier |
| `transaction_id` | UUID | FK -> `points_transactions.id`, NOT NULL | Originating credit transaction |
| `account_id` | UUID | FK -> `loyalty_accounts.id`, NOT NULL | Account owner |
| `initial_points` | INTEGER | NOT NULL | Starting point count |
| `remaining_points` | INTEGER | NOT NULL | Unspent points remaining in this lot |
| `status` | VARCHAR(30) | NOT NULL, DEFAULT 'ACTIVE' | `ACTIVE`, `PARTIALLY_REDEEMED`, `EXHAUSTED`, `EXPIRED`, `REVERSED` |
| `expires_at` | TIMESTAMPTZ | NOT NULL | Expiry date (created + 365 days) |
| `created_at` | TIMESTAMPTZ | NOT NULL | Lot creation timestamp |

#### `rewards`
Perks catalog available for customer redemption.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Reward identifier |
| `name` | VARCHAR(100) | NOT NULL | Reward title |
| `reward_type` | VARCHAR(50) | NOT NULL | Type: `VOUCHER`, `MERCHANDISE`, `EXPERIENCE` |
| `points_required` | INTEGER | NOT NULL | Cost in points to redeem |
| `monetary_value` | NUMERIC(10,2) | NOT NULL | Currency equivalent value |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Active perk flag |

#### `redemptions`
Completed reward redemptions.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Redemption identifier |
| `account_id` | UUID | FK -> `loyalty_accounts.id`, NOT NULL | Redeeming account |
| `reward_id` | UUID | FK -> `rewards.id`, NOT NULL | Selected reward perk |
| `transaction_id` | UUID | FK -> `points_transactions.id`, NOT NULL | Associated debit transaction in journal |
| `points_redeemed` | INTEGER | NOT NULL | Points deducted |
| `voucher_code` | VARCHAR(100) | UNIQUE, NOT NULL | Single-use coupon code |
| `status` | VARCHAR(30) | NOT NULL, DEFAULT 'COMPLETED' | Redemption status |
| `created_at` | TIMESTAMPTZ | NOT NULL | Redemption timestamp |

#### `points_lot_allocations` *(Append-Only)*
Maps redemptions to the specific points lots depleted under FIFO rules.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Allocation identifier |
| `redemption_id` | UUID | FK -> `redemptions.id`, NOT NULL | Parent redemption |
| `lot_id` | UUID | FK -> `points_lots.id`, NOT NULL | Depleted lot |
| `points_allocated` | INTEGER | NOT NULL | Points deducted from this lot |
| `created_at` | TIMESTAMPTZ | NOT NULL | Allocation timestamp |

*Note: Protected by trigger `tg_points_lot_allocations_immutable`.*

#### `expiry_batches`
Audit records for automated expiration batch runs.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Batch identifier |
| `batch_date` | DATE | NOT NULL | Date of expiration run |
| `total_accounts_affected` | INTEGER | NOT NULL, DEFAULT 0 | Count of accounts with expired points |
| `total_points_expired` | INTEGER | NOT NULL, DEFAULT 0 | Sum of expired points removed |
| `status` | VARCHAR(30) | NOT NULL, DEFAULT 'COMPLETED' | Batch status |
| `created_at` | TIMESTAMPTZ | NOT NULL | Run timestamp |

#### `expiry_batch_items` *(Append-Only)*
Details each lot expired during a batch run.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Item identifier |
| `batch_id` | UUID | FK -> `expiry_batches.id`, NOT NULL | Parent batch |
| `lot_id` | UUID | FK -> `points_lots.id`, NOT NULL | Expired lot |
| `account_id` | UUID | FK -> `loyalty_accounts.id`, NOT NULL | Affected account |
| `points_expired` | INTEGER | NOT NULL | Points deducted |
| `transaction_id` | UUID | FK -> `points_transactions.id`, NOT NULL | Journal transaction record |

*Note: Protected by trigger `tg_expiry_batch_items_immutable`.*

---

### 2.4 Audit, Intelligence & Remediation Module

#### `audit_events` *(Append-Only)*
Security and administrative audit trail.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Audit event identifier |
| `actor_id` | UUID | FK -> `app_users.id`, NULLABLE | User who performed the action |
| `event_type` | VARCHAR(100) | NOT NULL | Action name (e.g. `USER_LOGIN`, `CORRECTIVE_ACTION_APPROVED`) |
| `entity_type` | VARCHAR(50) | NOT NULL | Target table name |
| `entity_id` | VARCHAR(100) | NOT NULL | ID of target record |
| `payload` | JSONB | NOT NULL, DEFAULT '{}' | Context details and parameters |
| `created_at` | TIMESTAMPTZ | NOT NULL | Event timestamp |

*Note: Protected by trigger `tg_audit_events_immutable`.*

#### `rejected_operations` *(Append-Only)*
Records invalid, blocked, or unauthorized transaction attempts.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Record identifier |
| `account_id` | UUID | FK -> `loyalty_accounts.id`, NULLABLE | Involved account |
| `operation_type` | VARCHAR(50) | NOT NULL | Attempted operation name |
| `rejection_reason`| TEXT | NOT NULL | Error explanation |
| `payload` | JSONB | NULLABLE | Request parameters attempted |
| `created_at` | TIMESTAMPTZ | NOT NULL | Rejection timestamp |

*Note: Protected by trigger `tg_rejected_operations_immutable`.*

#### `anomaly_incidents`
Issues detected by the LLIRE intelligence engine.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Incident identifier |
| `detector_name` | VARCHAR(100) | NOT NULL | Detector that raised the flag |
| `entity_type` | VARCHAR(50) | NOT NULL | Target object: `ACCOUNT`, `ORDER`, `LOT` |
| `entity_id` | VARCHAR(100) | NOT NULL | Target object ID |
| `severity` | VARCHAR(20) | NOT NULL | Severity: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `discrepancy_amount`| NUMERIC(10,2) | NOT NULL, DEFAULT 0 | Financial or point amount at risk |
| `evidence_payload`| JSONB | NOT NULL | 7-part explainability diagnostic report |
| `fingerprint` | VARCHAR(64) | NOT NULL | SHA-256 hash preventing duplicate incident creation |
| `status` | VARCHAR(30) | NOT NULL, DEFAULT 'DETECTED' | `DETECTED`, `INVESTIGATING`, `PENDING_APPROVAL`, `RESOLVED`, `DISMISSED` |
| `created_at` | TIMESTAMPTZ | NOT NULL | Detection timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Last update timestamp |

#### `corrective_actions`
Tracks proposed and approved ledger adjustments under dual-key control.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY | Action identifier |
| `incident_id` | UUID | FK -> `anomaly_incidents.id`, NOT NULL | Linked anomaly incident |
| `account_id` | UUID | FK -> `loyalty_accounts.id`, NOT NULL | Corrected account |
| `action_type` | VARCHAR(50) | NOT NULL | `ADJUSTMENT_CREDIT`, `ADJUSTMENT_DEBIT`, `ACCOUNT_FREEZE`, `ACCOUNT_UNFREEZE` |
| `adjustment_points`| INTEGER | NULLABLE | Points adjustment amount |
| `justification` | TEXT | NOT NULL | Manager's business justification |
| `proposer_id` | UUID | FK -> `app_users.id`, NOT NULL | First manager who proposed action |
| `approver_id` | UUID | FK -> `app_users.id`, NULLABLE | Second manager who reviewed and approved |
| `approval_status` | VARCHAR(30) | NOT NULL, DEFAULT 'PENDING_APPROVAL' | `PENDING_APPROVAL`, `APPROVED`, `REJECTED` |
| `rejection_reason`| TEXT | NULLABLE | Mandatory reason if rejected |
| `transaction_id` | UUID | FK -> `points_transactions.id`, NULLABLE | Executed compensating journal transaction |
| `created_at` | TIMESTAMPTZ | NOT NULL | Proposal creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Approval/rejection timestamp |

*Note: Enforces two-person control (`proposer_id != approver_id`) at database and API layers.*

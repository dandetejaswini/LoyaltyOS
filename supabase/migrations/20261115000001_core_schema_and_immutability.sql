-- ==============================================================================
-- LoyaltyOS — Intelligent Loyalty & Ledger Management Platform
-- Migration: 20261115000001_core_schema_and_immutability.sql
-- Target Engine: Supabase PostgreSQL (PostgreSQL 15+)
-- Description: Establishes all 21 core tables, foreign keys, indexes,
--              PostgreSQL immutability triggers, and initial tiers seed.
-- ==============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================================================================
-- 1. IDENTITY & ACCESS MANAGEMENT
-- ==============================================================================

-- 1.1 App Users (Internal Application User Record)
CREATE TABLE IF NOT EXISTS app_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    role VARCHAR(30) NOT NULL DEFAULT 'CUSTOMER',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_app_user_role CHECK (role IN ('CUSTOMER', 'OPERATOR', 'ANALYST', 'OPERATIONS_MANAGER'))
);

CREATE INDEX IF NOT EXISTS idx_app_users_email ON app_users(email);

-- 1.2 User Identity Mappings (Supabase / Firebase Unified Identity)
CREATE TABLE IF NOT EXISTS user_identity_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_users(id) ON DELETE RESTRICT,
    provider VARCHAR(30) NOT NULL,
    provider_uid VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    email_verified BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_sign_in_at TIMESTAMPTZ,
    CONSTRAINT uq_provider_identity UNIQUE (provider, provider_uid),
    CONSTRAINT chk_provider_name CHECK (provider IN ('SUPABASE_PASSWORD', 'FIREBASE_GOOGLE', 'SUPABASE_OAUTH'))
);

CREATE INDEX IF NOT EXISTS idx_user_mappings_user ON user_identity_mappings(user_id);
CREATE INDEX IF NOT EXISTS idx_user_mappings_email ON user_identity_mappings(email);

-- ==============================================================================
-- 2. LOYALTY MASTER DATA
-- ==============================================================================

-- 2.1 Customers
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(32) PRIMARY KEY,
    user_id UUID UNIQUE REFERENCES app_users(id) ON DELETE RESTRICT,
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_customer_status CHECK (status IN ('ACTIVE', 'SUSPENDED', 'CLOSED'))
);

CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);

-- 2.2 Tiers
CREATE TABLE IF NOT EXISTS tiers (
    tier_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    rank INT NOT NULL UNIQUE,
    min_spend NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    earning_multiplier NUMERIC(4, 2) NOT NULL DEFAULT 1.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed default tiers (BR-02)
INSERT INTO tiers (tier_id, name, rank, min_spend, earning_multiplier)
VALUES
    ('TIER-BRONZE', 'Bronze', 1, 0.00, 1.00),
    ('TIER-SILVER', 'Silver', 2, 500.00, 1.25),
    ('TIER-GOLD', 'Gold', 3, 1000.00, 1.50),
    ('TIER-PLATINUM', 'Platinum', 4, 2500.00, 2.00)
ON CONFLICT (tier_id) DO UPDATE 
SET name = EXCLUDED.name,
    rank = EXCLUDED.rank,
    min_spend = EXCLUDED.min_spend,
    earning_multiplier = EXCLUDED.earning_multiplier;

-- 2.3 Loyalty Accounts
CREATE TABLE IF NOT EXISTS loyalty_accounts (
    account_id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) NOT NULL UNIQUE REFERENCES customers(customer_id) ON DELETE RESTRICT,
    tier_id VARCHAR(32) NOT NULL DEFAULT 'TIER-BRONZE' REFERENCES tiers(tier_id) ON DELETE RESTRICT,
    current_balance INT NOT NULL DEFAULT 0,
    lifetime_accrued INT NOT NULL DEFAULT 0,
    lifetime_redeemed INT NOT NULL DEFAULT 0,
    qualifying_spend NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_account_status CHECK (status IN ('ACTIVE', 'SUSPENDED', 'CLOSED'))
);

CREATE INDEX IF NOT EXISTS idx_loyalty_accounts_customer ON loyalty_accounts(customer_id);

-- 2.4 Program Rules
CREATE TABLE IF NOT EXISTS rules (
    rule_id VARCHAR(32) PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL UNIQUE,
    rule_type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT true,
    effective_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_to TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================================================================
-- 3. COMMERCE & ORDERS
-- ==============================================================================

-- 3.1 Orders
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    order_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    gross_amount NUMERIC(12, 2) NOT NULL,
    tax_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    shipping_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    discount_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    eligible_net_spend NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) NOT NULL DEFAULT 'COMPLETED',
    accrual_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_order_status CHECK (status IN ('PENDING', 'COMPLETED', 'CANCELLED', 'RETURNED', 'PARTIALLY_RETURNED')),
    CONSTRAINT chk_accrual_status CHECK (accrual_status IN ('PENDING', 'ACCRUED', 'EXCLUDED', 'REVERSED'))
);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);

-- 3.2 Order Lines
CREATE TABLE IF NOT EXISTS order_lines (
    order_line_id VARCHAR(40) PRIMARY KEY,
    order_id VARCHAR(32) NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    line_number INT NOT NULL,
    sku VARCHAR(50) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    quantity INT NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    item_discount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    net_amount NUMERIC(12, 2) NOT NULL,
    is_eligible BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_order_line UNIQUE (order_id, line_number)
);

CREATE INDEX IF NOT EXISTS idx_order_lines_order ON order_lines(order_id);

-- 3.3 Order Returns
CREATE TABLE IF NOT EXISTS order_returns (
    return_id VARCHAR(32) PRIMARY KEY,
    order_id VARCHAR(32) NOT NULL REFERENCES orders(order_id) ON DELETE RESTRICT,
    return_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    refund_amount NUMERIC(12, 2) NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_order_returns_order ON order_returns(order_id);

-- 3.4 Order Return Lines
CREATE TABLE IF NOT EXISTS order_return_lines (
    return_line_id VARCHAR(40) PRIMARY KEY,
    return_id VARCHAR(32) NOT NULL REFERENCES order_returns(return_id) ON DELETE CASCADE,
    order_line_id VARCHAR(40) NOT NULL REFERENCES order_lines(order_line_id) ON DELETE RESTRICT,
    quantity_returned INT NOT NULL,
    refund_amount NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_order_return_lines_return ON order_return_lines(return_id);

-- ==============================================================================
-- 4. FINANCIAL LEDGER & POINTS LOT ENGINE
-- ==============================================================================

-- 4.1 Points Transactions (Append-Only Journal)
CREATE TABLE IF NOT EXISTS points_transactions (
    transaction_id VARCHAR(40) PRIMARY KEY,
    account_id VARCHAR(32) NOT NULL REFERENCES loyalty_accounts(account_id) ON DELETE RESTRICT,
    order_id VARCHAR(32) REFERENCES orders(order_id) ON DELETE RESTRICT,
    related_transaction_id VARCHAR(40) REFERENCES points_transactions(transaction_id) ON DELETE RESTRICT,
    rule_id VARCHAR(32) REFERENCES rules(rule_id) ON DELETE RESTRICT,
    entry_type VARCHAR(30) NOT NULL,
    points INT NOT NULL,
    running_balance INT NOT NULL,
    idempotency_key VARCHAR(128) UNIQUE,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_tx_entry_type CHECK (entry_type IN ('ACCRUAL', 'REDEMPTION', 'REVERSAL', 'EXPIRY', 'ADJUSTMENT_CREDIT', 'ADJUSTMENT_DEBIT'))
);

CREATE INDEX IF NOT EXISTS idx_tx_account ON points_transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_tx_order ON points_transactions(order_id);
CREATE INDEX IF NOT EXISTS idx_tx_created ON points_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_tx_idempotency ON points_transactions(idempotency_key);

-- 4.2 Points Lots (FIFO Expiration Tracking)
CREATE TABLE IF NOT EXISTS points_lots (
    lot_id VARCHAR(40) PRIMARY KEY,
    transaction_id VARCHAR(40) NOT NULL REFERENCES points_transactions(transaction_id) ON DELETE RESTRICT,
    account_id VARCHAR(32) NOT NULL REFERENCES loyalty_accounts(account_id) ON DELETE RESTRICT,
    initial_points INT NOT NULL,
    remaining_points INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_lot_points CHECK (remaining_points >= 0 AND remaining_points <= initial_points),
    CONSTRAINT chk_lot_status CHECK (status IN ('ACTIVE', 'PARTIALLY_REDEEMED', 'EXHAUSTED', 'EXPIRED'))
);

CREATE INDEX IF NOT EXISTS idx_lots_account_fifo ON points_lots(account_id, expires_at ASC, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_lots_expiry ON points_lots(expires_at, status);

-- 4.3 Rewards Catalog
CREATE TABLE IF NOT EXISTS rewards (
    reward_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    reward_type VARCHAR(50) NOT NULL,
    points_required INT NOT NULL,
    monetary_value NUMERIC(10, 2) NOT NULL,
    stock_quantity INT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_reward_points CHECK (points_required > 0)
);

-- Seed standard rewards catalog
INSERT INTO rewards (reward_id, name, reward_type, points_required, monetary_value, stock_quantity, is_active)
VALUES
    ('REW-VOUCH-10', '$10 Instant Checkout Voucher', 'DISCOUNT_VOUCHER', 500, 10.00, 1000, true),
    ('REW-VOUCH-25', '$25 Premium Cart Credit', 'DISCOUNT_VOUCHER', 1000, 25.00, 500, true),
    ('REW-EXP-SHIP', 'Free Priority Express Shipping', 'SHIPPING_WAIVER', 250, 5.00, NULL, true)
ON CONFLICT (reward_id) DO NOTHING;

-- 4.4 Redemptions
CREATE TABLE IF NOT EXISTS redemptions (
    redemption_id VARCHAR(40) PRIMARY KEY,
    account_id VARCHAR(32) NOT NULL REFERENCES loyalty_accounts(account_id) ON DELETE RESTRICT,
    reward_id VARCHAR(32) NOT NULL REFERENCES rewards(reward_id) ON DELETE RESTRICT,
    transaction_id VARCHAR(40) NOT NULL REFERENCES points_transactions(transaction_id) ON DELETE RESTRICT,
    points_redeemed INT NOT NULL,
    voucher_code VARCHAR(64) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'COMPLETED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_redemption_status CHECK (status IN ('PENDING', 'COMPLETED', 'CANCELLED', 'USED'))
);

CREATE INDEX IF NOT EXISTS idx_redemptions_account ON redemptions(account_id);
CREATE INDEX IF NOT EXISTS idx_redemptions_voucher ON redemptions(voucher_code);

-- 4.5 Points Lot Allocations (FIFO Consumption Traceability)
CREATE TABLE IF NOT EXISTS points_lot_allocations (
    allocation_id VARCHAR(40) PRIMARY KEY,
    redemption_id VARCHAR(40) NOT NULL REFERENCES redemptions(redemption_id) ON DELETE RESTRICT,
    lot_id VARCHAR(40) NOT NULL REFERENCES points_lots(lot_id) ON DELETE RESTRICT,
    points_allocated INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_points_allocated CHECK (points_allocated > 0)
);

CREATE INDEX IF NOT EXISTS idx_allocations_redemption ON points_lot_allocations(redemption_id);
CREATE INDEX IF NOT EXISTS idx_allocations_lot ON points_lot_allocations(lot_id);

-- 4.6 Expiry Batches
CREATE TABLE IF NOT EXISTS expiry_batches (
    batch_id VARCHAR(64) PRIMARY KEY,
    cutoff_date TIMESTAMPTZ NOT NULL,
    total_lots_processed INT NOT NULL DEFAULT 0,
    total_points_expired INT NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'COMPLETED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_expiry_batch_status CHECK (status IN ('IN_PROGRESS', 'COMPLETED', 'FAILED'))
);

-- 4.7 Expiry Batch Items
CREATE TABLE IF NOT EXISTS expiry_batch_items (
    item_id VARCHAR(64) PRIMARY KEY,
    batch_id VARCHAR(64) NOT NULL REFERENCES expiry_batches(batch_id) ON DELETE CASCADE,
    lot_id VARCHAR(40) NOT NULL REFERENCES points_lots(lot_id) ON DELETE RESTRICT,
    transaction_id VARCHAR(40) NOT NULL REFERENCES points_transactions(transaction_id) ON DELETE RESTRICT,
    points_expired INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_points_expired CHECK (points_expired > 0)
);

CREATE INDEX IF NOT EXISTS idx_expiry_items_batch ON expiry_batch_items(batch_id);
CREATE INDEX IF NOT EXISTS idx_expiry_items_lot ON expiry_batch_items(lot_id);

-- ==============================================================================
-- 5. AUDIT TRAIL & OPERATIONAL RESILIENCE
-- ==============================================================================

-- 5.1 Audit Events (Immutable Append-Only Audit Trail)
CREATE TABLE IF NOT EXISTS audit_events (
    event_id VARCHAR(40) PRIMARY KEY,
    actor_id VARCHAR(64) NOT NULL,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(64) NOT NULL,
    metadata_payload JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_events(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_events(action);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_events(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_events(created_at);

-- 5.2 Rejected Operations
CREATE TABLE IF NOT EXISTS rejected_operations (
    operation_id VARCHAR(40) PRIMARY KEY,
    account_id VARCHAR(32) REFERENCES loyalty_accounts(account_id) ON DELETE SET NULL,
    actor_id VARCHAR(64) NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    error_code VARCHAR(50) NOT NULL,
    error_message TEXT NOT NULL,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rejected_error_code ON rejected_operations(error_code);

-- 5.3 Anomaly Incidents (LLIRE Detection)
CREATE TABLE IF NOT EXISTS anomaly_incidents (
    incident_id VARCHAR(40) PRIMARY KEY,
    issue_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(64) NOT NULL,
    variance_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    details JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'DETECTED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    CONSTRAINT chk_anomaly_status CHECK (status IN ('DETECTED', 'INVESTIGATING', 'RESOLVED', 'DISMISSED'))
);

CREATE INDEX IF NOT EXISTS idx_anomaly_status_type ON anomaly_incidents(status, issue_type);

-- 5.4 Corrective Actions (Dual-Key Remediation)
CREATE TABLE IF NOT EXISTS corrective_actions (
    action_id VARCHAR(40) PRIMARY KEY,
    incident_id VARCHAR(40) NOT NULL REFERENCES anomaly_incidents(incident_id) ON DELETE RESTRICT,
    operator_id VARCHAR(64) NOT NULL,
    compensating_transaction_id VARCHAR(40) REFERENCES points_transactions(transaction_id) ON DELETE SET NULL,
    decision VARCHAR(20) NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_action_decision CHECK (decision IN ('PENDING_APPROVAL', 'APPROVED', 'REJECTED'))
);

CREATE INDEX IF NOT EXISTS idx_corrective_incident ON corrective_actions(incident_id);

-- ==============================================================================
-- 6. DATABASE ENGINE IMMUTABILITY TRIGGERS
-- ==============================================================================

-- 6.1 Ledger Journal Immutability: points_transactions (Append-Only)
CREATE OR REPLACE FUNCTION tg_fn_points_transactions_immutable()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Immutability Violation: points_transactions is append-only. Modifying or deleting records is prohibited.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_points_transactions_immutable ON points_transactions;
CREATE TRIGGER tg_points_transactions_immutable
BEFORE UPDATE OR DELETE ON points_transactions
FOR EACH ROW EXECUTE FUNCTION tg_fn_points_transactions_immutable();

-- 6.2 Audit Trail Immutability: audit_events (Append-Only)
CREATE OR REPLACE FUNCTION tg_fn_audit_events_immutable()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Immutability Violation: audit_events is append-only. Modifying or deleting audit history is prohibited.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_audit_events_immutable ON audit_events;
CREATE TRIGGER tg_audit_events_immutable
BEFORE UPDATE OR DELETE ON audit_events
FOR EACH ROW EXECUTE FUNCTION tg_fn_audit_events_immutable();

-- 6.3 Points Lot Allocations Immutability (Append-Only)
CREATE OR REPLACE FUNCTION tg_fn_points_lot_allocations_immutable()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Immutability Violation: points_lot_allocations is append-only. Modifying or deleting allocations is prohibited.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_points_lot_allocations_immutable ON points_lot_allocations;
CREATE TRIGGER tg_points_lot_allocations_immutable
BEFORE UPDATE OR DELETE ON points_lot_allocations
FOR EACH ROW EXECUTE FUNCTION tg_fn_points_lot_allocations_immutable();

-- 6.4 Expiry Batch Items Immutability (Append-Only)
CREATE OR REPLACE FUNCTION tg_fn_expiry_batch_items_immutable()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Immutability Violation: expiry_batch_items is append-only. Modifying or deleting batch items is prohibited.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_expiry_batch_items_immutable ON expiry_batch_items;
CREATE TRIGGER tg_expiry_batch_items_immutable
BEFORE UPDATE OR DELETE ON expiry_batch_items
FOR EACH ROW EXECUTE FUNCTION tg_fn_expiry_batch_items_immutable();

-- 6.5 Points Lots Guard: Protect core immutable fields & prevent deletion
CREATE OR REPLACE FUNCTION tg_fn_points_lots_immutability_guard()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        RAISE EXCEPTION 'Immutability Violation: points_lots records cannot be deleted. Historical lot tracking must be preserved.';
    ELSIF (TG_OP = 'UPDATE') THEN
        IF OLD.lot_id <> NEW.lot_id OR
           OLD.transaction_id <> NEW.transaction_id OR
           OLD.account_id <> NEW.account_id OR
           OLD.initial_points <> NEW.initial_points OR
           OLD.created_at <> NEW.created_at THEN
            RAISE EXCEPTION 'Immutability Violation: Immutable columns of points_lots (lot_id, transaction_id, account_id, initial_points, created_at) cannot be modified.';
        END IF;
        IF (NEW.remaining_points > OLD.remaining_points) THEN
            RAISE EXCEPTION 'Business Rule Violation: Points lot remaining balance cannot increase.';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_points_lots_immutability_guard ON points_lots;
CREATE TRIGGER tg_points_lots_immutability_guard
BEFORE UPDATE OR DELETE ON points_lots
FOR EACH ROW EXECUTE FUNCTION tg_fn_points_lots_immutability_guard();

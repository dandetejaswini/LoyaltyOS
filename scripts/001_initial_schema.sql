-- ==============================================================================
-- LoyaltyOS — Intelligent Loyalty & Ledger Management Platform
-- Initial Schema Migration Script (Phase 2 Security & Ledger Foundation)
-- Target Engine: Supabase PostgreSQL (PostgreSQL 15+)
-- Description: Establishes 21 core tables, foreign key constraints, indexes,
--              PostgreSQL immutability triggers, and Row Level Security (RLS).
-- ==============================================================================

-- Enable UUID extension if not enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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
    CONSTRAINT chk_provider_name CHECK (provider IN ('SUPABASE_PASSWORD', 'FIREBASE_GOOGLE'))
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

-- Seed default tiers as defined in BR-02
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
    CONSTRAINT chk_account_status CHECK (status IN ('ACTIVE', 'FROZEN', 'CLOSED'))
);

CREATE INDEX IF NOT EXISTS idx_loyalty_accounts_customer ON loyalty_accounts(customer_id);

-- 2.4 Rules (Promotions & Multipliers)
CREATE TABLE IF NOT EXISTS rules (
    rule_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    multiplier NUMERIC(4, 2) NOT NULL DEFAULT 1.00,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================================================================
-- 3. ORDERS & COMMERCE ENTITIES
-- ==============================================================================

-- 3.1 Orders
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    order_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    gross_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    tax_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    shipping_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    discount_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    eligible_net_spend NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) NOT NULL DEFAULT 'COMPLETED',
    accrual_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_order_status CHECK (status IN ('COMPLETED', 'CANCELLED', 'RETURNED')),
    CONSTRAINT chk_accrual_status CHECK (accrual_status IN ('PENDING', 'ACCRUED', 'EXCLUDED'))
);

CREATE INDEX IF NOT EXISTS idx_orders_customer_date ON orders(customer_id, order_date);

-- 3.2 Order Lines
CREATE TABLE IF NOT EXISTS order_lines (
    order_line_id VARCHAR(40) PRIMARY KEY,
    order_id VARCHAR(32) NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    line_number INT NOT NULL,
    sku VARCHAR(50) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price NUMERIC(12, 2) NOT NULL,
    item_discount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    net_amount NUMERIC(12, 2) NOT NULL,
    is_eligible BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_order_lines_order ON order_lines(order_id);

-- 3.3 Order Returns
CREATE TABLE IF NOT EXISTS order_returns (
    return_id VARCHAR(32) PRIMARY KEY,
    order_id VARCHAR(32) NOT NULL REFERENCES orders(order_id) ON DELETE RESTRICT,
    return_type VARCHAR(20) NOT NULL,
    total_refund_amount NUMERIC(12, 2) NOT NULL,
    points_reversed INT NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'PROCESSED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_return_type CHECK (return_type IN ('FULL', 'PARTIAL'))
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

CREATE INDEX IF NOT EXISTS idx_return_lines_return ON order_return_lines(return_id);

-- ==============================================================================
-- 4. FINANCIAL LEDGER & POINTS JOURNAL
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
    idempotency_key VARCHAR(100) NOT NULL UNIQUE,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_ledger_entry_type CHECK (
        entry_type IN ('ACCRUAL', 'REDEMPTION', 'REVERSAL', 'EXPIRY', 'ADJUSTMENT_CREDIT', 'ADJUSTMENT_DEBIT')
    ),
    CONSTRAINT chk_points_nonzero CHECK (points <> 0)
);

CREATE INDEX IF NOT EXISTS idx_pts_account_created ON points_transactions(account_id, created_at);
CREATE INDEX IF NOT EXISTS idx_pts_order ON points_transactions(order_id);
CREATE INDEX IF NOT EXISTS idx_pts_related ON points_transactions(related_transaction_id);
CREATE INDEX IF NOT EXISTS idx_pts_idempotency ON points_transactions(idempotency_key);

-- 4.2 Points Lots (FIFO Tracking & Expiration - Partially Mutable State)
CREATE TABLE IF NOT EXISTS points_lots (
    lot_id VARCHAR(40) PRIMARY KEY,
    transaction_id VARCHAR(40) NOT NULL UNIQUE REFERENCES points_transactions(transaction_id) ON DELETE RESTRICT,
    account_id VARCHAR(32) NOT NULL REFERENCES loyalty_accounts(account_id) ON DELETE RESTRICT,
    initial_points INT NOT NULL,
    remaining_points INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_lot_initial_positive CHECK (initial_points > 0),
    CONSTRAINT chk_lot_remaining_valid CHECK (remaining_points >= 0 AND remaining_points <= initial_points),
    CONSTRAINT chk_lot_status CHECK (status IN ('ACTIVE', 'PARTIALLY_REDEEMED', 'EXHAUSTED', 'EXPIRED', 'REVERSED'))
);

CREATE INDEX IF NOT EXISTS idx_lots_fifo ON points_lots(account_id, expires_at, created_at);
CREATE INDEX IF NOT EXISTS idx_lots_expiry_scan ON points_lots(expires_at, status);

-- 4.3 Rewards Catalog
CREATE TABLE IF NOT EXISTS rewards (
    reward_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    reward_type VARCHAR(30) NOT NULL DEFAULT 'DISCOUNT_VOUCHER',
    points_required INT NOT NULL,
    monetary_value NUMERIC(8, 2) NOT NULL DEFAULT 0.00,
    stock_quantity INT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_reward_points_positive CHECK (points_required > 0)
);

-- 4.4 Redemptions
CREATE TABLE IF NOT EXISTS redemptions (
    redemption_id VARCHAR(32) PRIMARY KEY,
    account_id VARCHAR(32) NOT NULL REFERENCES loyalty_accounts(account_id) ON DELETE RESTRICT,
    reward_id VARCHAR(32) NOT NULL REFERENCES rewards(reward_id) ON DELETE RESTRICT,
    transaction_id VARCHAR(40) NOT NULL UNIQUE REFERENCES points_transactions(transaction_id) ON DELETE RESTRICT,
    points_redeemed INT NOT NULL,
    voucher_code VARCHAR(64) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'ISSUED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    CONSTRAINT chk_redemption_points_positive CHECK (points_redeemed > 0),
    CONSTRAINT chk_redemption_status CHECK (status IN ('ISSUED', 'USED', 'CANCELLED', 'EXPIRED'))
);

CREATE INDEX IF NOT EXISTS idx_redemptions_account ON redemptions(account_id);
CREATE INDEX IF NOT EXISTS idx_redemptions_voucher ON redemptions(voucher_code);

-- 4.5 Points Lot Allocations (Append-Only Bridge)
CREATE TABLE IF NOT EXISTS points_lot_allocations (
    allocation_id VARCHAR(40) PRIMARY KEY,
    lot_id VARCHAR(40) NOT NULL REFERENCES points_lots(lot_id) ON DELETE RESTRICT,
    redemption_id VARCHAR(32) REFERENCES redemptions(redemption_id) ON DELETE RESTRICT,
    transaction_id VARCHAR(40) NOT NULL REFERENCES points_transactions(transaction_id) ON DELETE RESTRICT,
    points_allocated INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_allocation_points_positive CHECK (points_allocated > 0)
);

CREATE INDEX IF NOT EXISTS idx_lot_alloc_lot ON points_lot_allocations(lot_id);
CREATE INDEX IF NOT EXISTS idx_lot_alloc_redemption ON points_lot_allocations(redemption_id);

-- 4.6 Expiry Batches
CREATE TABLE IF NOT EXISTS expiry_batches (
    batch_id VARCHAR(32) PRIMARY KEY,
    cutoff_date TIMESTAMPTZ NOT NULL,
    total_lots_processed INT NOT NULL DEFAULT 0,
    total_points_expired INT NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'IN_PROGRESS',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_expiry_batch_status CHECK (status IN ('IN_PROGRESS', 'COMPLETED', 'FAILED'))
);

-- 4.7 Expiry Batch Items (Append-Only)
CREATE TABLE IF NOT EXISTS expiry_batch_items (
    item_id VARCHAR(40) PRIMARY KEY,
    batch_id VARCHAR(32) NOT NULL REFERENCES expiry_batches(batch_id) ON DELETE CASCADE,
    lot_id VARCHAR(40) NOT NULL REFERENCES points_lots(lot_id) ON DELETE RESTRICT,
    transaction_id VARCHAR(40) NOT NULL REFERENCES points_transactions(transaction_id) ON DELETE RESTRICT,
    points_expired INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_expiry_items_batch ON expiry_batch_items(batch_id);

-- ==============================================================================
-- 5. AUDIT, LOGGING & OBSERVABILITY
-- ==============================================================================

-- 5.1 Audit Events (Append-Only Audit Trail)
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

-- ==============================================================================
-- 6. OPERATIONAL RESILIENCE & ANOMALY RESOLUTION
-- ==============================================================================

-- 6.1 Anomaly Incidents
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

-- 6.2 Corrective Actions
CREATE TABLE IF NOT EXISTS corrective_actions (
    action_id VARCHAR(40) PRIMARY KEY,
    incident_id VARCHAR(40) NOT NULL REFERENCES anomaly_incidents(incident_id) ON DELETE RESTRICT,
    operator_id VARCHAR(64) NOT NULL,
    compensating_transaction_id VARCHAR(40) REFERENCES points_transactions(transaction_id) ON DELETE SET NULL,
    decision VARCHAR(20) NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_action_decision CHECK (decision IN ('APPROVED', 'REJECTED'))
);

CREATE INDEX IF NOT EXISTS idx_corrective_incident ON corrective_actions(incident_id);

-- ==============================================================================
-- 7. DATABASE ENGINE IMMUTABILITY TRIGGERS
-- ==============================================================================

-- 7.1 Ledger Journal Immutability: points_transactions (Append-Only)
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

-- 7.2 Audit Trail Immutability: audit_events (Append-Only)
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

-- 7.3 Lot Allocations Immutability: points_lot_allocations (Append-Only)
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

-- 7.4 Expiry Batch Items Immutability: expiry_batch_items (Append-Only)
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

-- 7.5 Points Lots Guard: Protect immutable lot columns and prevent deletion
CREATE OR REPLACE FUNCTION tg_fn_points_lots_immutability_guard()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Immutability Violation: points_lots records cannot be deleted. Historical lot tracking must be preserved.';
    ELSIF TG_OP = 'UPDATE' THEN
        -- Verify that core immutable fields were not altered
        IF OLD.lot_id <> NEW.lot_id OR
           OLD.transaction_id <> NEW.transaction_id OR
           OLD.account_id <> NEW.account_id OR
           OLD.initial_points <> NEW.initial_points OR
           OLD.created_at <> NEW.created_at THEN
            RAISE EXCEPTION 'Immutability Violation: Immutable columns of points_lots (lot_id, transaction_id, account_id, initial_points, created_at) cannot be modified.';
        END IF;
        -- Ensure remaining_points does not exceed initial_points
        IF NEW.remaining_points > OLD.initial_points THEN
            RAISE EXCEPTION 'Constraint Violation: remaining_points cannot exceed initial_points.';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_points_lots_immutability_guard ON points_lots;
CREATE TRIGGER tg_points_lots_immutability_guard
BEFORE UPDATE OR DELETE ON points_lots
FOR EACH ROW EXECUTE FUNCTION tg_fn_points_lots_immutability_guard();

-- ==============================================================================
-- 8. ROW-LEVEL SECURITY (RLS) POLICIES
-- ==============================================================================

-- Enable RLS across sensitive customer, identity, commerce and ledger tables
ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_identity_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE loyalty_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE points_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE points_lots ENABLE ROW LEVEL SECURITY;
ALTER TABLE redemptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;

-- 8.1 App Users: Customers may only view their own user record
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'user_read_own_record' AND tablename = 'app_users') THEN
        CREATE POLICY user_read_own_record ON app_users
            FOR SELECT USING (auth.uid() = id);
    END IF;
END $$;

-- 8.2 Identity Mappings: Customers may only inspect their own identity mappings
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'mapping_read_own_identities' AND tablename = 'user_identity_mappings') THEN
        CREATE POLICY mapping_read_own_identities ON user_identity_mappings
            FOR SELECT USING (auth.uid() = user_id);
    END IF;
END $$;

-- 8.3 Customers: Profile read isolation
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_profile' AND tablename = 'customers') THEN
        CREATE POLICY customer_read_own_profile ON customers
            FOR SELECT USING (auth.uid() = user_id);
    END IF;
END $$;

-- 8.4 Loyalty Accounts: Customer read isolation
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_account' AND tablename = 'loyalty_accounts') THEN
        CREATE POLICY customer_read_own_account ON loyalty_accounts
            FOR SELECT USING (customer_id IN (SELECT customer_id FROM customers WHERE user_id = auth.uid()));
    END IF;
END $$;

-- 8.5 Points Transactions: Ledger read isolation
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_transactions' AND tablename = 'points_transactions') THEN
        CREATE POLICY customer_read_own_transactions ON points_transactions
            FOR SELECT USING (account_id IN (
                SELECT la.account_id FROM loyalty_accounts la
                JOIN customers c ON c.customer_id = la.customer_id
                WHERE c.user_id = auth.uid()
            ));
    END IF;
END $$;

-- 8.6 Points Lots: Lot tracking read isolation
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_lots' AND tablename = 'points_lots') THEN
        CREATE POLICY customer_read_own_lots ON points_lots
            FOR SELECT USING (account_id IN (
                SELECT la.account_id FROM loyalty_accounts la
                JOIN customers c ON c.customer_id = la.customer_id
                WHERE c.user_id = auth.uid()
            ));
    END IF;
END $$;

-- 8.7 Redemptions: Voucher and redemption read isolation
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_redemptions' AND tablename = 'redemptions') THEN
        CREATE POLICY customer_read_own_redemptions ON redemptions
            FOR SELECT USING (account_id IN (
                SELECT la.account_id FROM loyalty_accounts la
                JOIN customers c ON c.customer_id = la.customer_id
                WHERE c.user_id = auth.uid()
            ));
    END IF;
END $$;

-- 8.8 Orders: Customer order read isolation
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_orders' AND tablename = 'orders') THEN
        CREATE POLICY customer_read_own_orders ON orders
            FOR SELECT USING (customer_id IN (SELECT customer_id FROM customers WHERE user_id = auth.uid()));
    END IF;
END $$;

-- 8.9 Order Lines: Line items read isolation
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_order_lines' AND tablename = 'order_lines') THEN
        CREATE POLICY customer_read_own_order_lines ON order_lines
            FOR SELECT USING (order_id IN (
                SELECT o.order_id FROM orders o
                JOIN customers c ON c.customer_id = o.customer_id
                WHERE c.user_id = auth.uid()
            ));
    END IF;
END $$;

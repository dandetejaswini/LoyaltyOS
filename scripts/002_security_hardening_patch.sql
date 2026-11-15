-- ============================================================================
-- LoyaltyOS — Security Hardening & Parity Patch
-- Script: scripts/002_security_hardening_patch.sql
-- Purpose: Safely and idempotently apply missing immutability triggers,
--          RLS policies, and Alembic version stamping to an existing database.
-- Note: Does NOT drop or truncate any tables or data.
-- ============================================================================

-- 1. Ensure Immutability Trigger Functions Exist
CREATE OR REPLACE FUNCTION tg_fn_points_transactions_immutable()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Immutability Violation: points_transactions is append-only. Modifying or deleting records is prohibited.';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION tg_fn_audit_events_immutable()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Immutability Violation: audit_events is append-only. Modifying or deleting historical audit records is prohibited.';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION tg_fn_points_lot_allocations_immutable()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Immutability Violation: points_lot_allocations is append-only. Modifying or deleting allocations is prohibited.';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION tg_fn_expiry_batch_items_immutable()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Immutability Violation: expiry_batch_items is append-only. Modifying or deleting expiry items is prohibited.';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION tg_fn_points_lots_immutability_guard()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        RAISE EXCEPTION 'Immutability Violation: points_lots records cannot be deleted.';
    END IF;

    IF (NEW.lot_id <> OLD.lot_id OR 
        NEW.transaction_id <> OLD.transaction_id OR 
        NEW.account_id <> OLD.account_id OR 
        NEW.initial_points <> OLD.initial_points OR 
        NEW.created_at <> OLD.created_at) THEN
        RAISE EXCEPTION 'Immutability Violation: Core immutable fields on points_lots cannot be altered.';
    END IF;

    IF (NEW.remaining_points > OLD.remaining_points) THEN
        RAISE EXCEPTION 'Business Rule Violation: Points lot remaining balance cannot increase.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Idempotently Apply All 5 Triggers
DROP TRIGGER IF EXISTS tg_points_transactions_immutable ON points_transactions;
CREATE TRIGGER tg_points_transactions_immutable
BEFORE UPDATE OR DELETE ON points_transactions
FOR EACH ROW
EXECUTE FUNCTION tg_fn_points_transactions_immutable();

DROP TRIGGER IF EXISTS tg_audit_events_immutable ON audit_events;
CREATE TRIGGER tg_audit_events_immutable
BEFORE UPDATE OR DELETE ON audit_events
FOR EACH ROW
EXECUTE FUNCTION tg_fn_audit_events_immutable();

DROP TRIGGER IF EXISTS tg_points_lot_allocations_immutable ON points_lot_allocations;
CREATE TRIGGER tg_points_lot_allocations_immutable
BEFORE UPDATE OR DELETE ON points_lot_allocations
FOR EACH ROW
EXECUTE FUNCTION tg_fn_points_lot_allocations_immutable();

DROP TRIGGER IF EXISTS tg_expiry_batch_items_immutable ON expiry_batch_items;
CREATE TRIGGER tg_expiry_batch_items_immutable
BEFORE UPDATE OR DELETE ON expiry_batch_items
FOR EACH ROW
EXECUTE FUNCTION tg_fn_expiry_batch_items_immutable();

DROP TRIGGER IF EXISTS tg_points_lots_immutability_guard ON points_lots;
CREATE TRIGGER tg_points_lots_immutability_guard
BEFORE UPDATE OR DELETE ON points_lots
FOR EACH ROW
EXECUTE FUNCTION tg_fn_points_lots_immutability_guard();

-- 3. Idempotently Apply All 9 Customer Data Isolation RLS Policies
ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_identity_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE loyalty_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE points_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE points_lots ENABLE ROW LEVEL SECURITY;
ALTER TABLE redemptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_lines ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'user_read_own_record' AND tablename = 'app_users') THEN
        CREATE POLICY user_read_own_record ON app_users
        FOR SELECT
        USING (auth.uid() = id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'mapping_read_own_identities' AND tablename = 'user_identity_mappings') THEN
        CREATE POLICY mapping_read_own_identities ON user_identity_mappings
        FOR SELECT
        USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_profile' AND tablename = 'customers') THEN
        CREATE POLICY customer_read_own_profile ON customers
        FOR SELECT
        USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_account' AND tablename = 'loyalty_accounts') THEN
        CREATE POLICY customer_read_own_account ON loyalty_accounts
        FOR SELECT
        USING (customer_id IN (SELECT customer_id FROM customers WHERE user_id = auth.uid()));
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_transactions' AND tablename = 'points_transactions') THEN
        CREATE POLICY customer_read_own_transactions ON points_transactions
        FOR SELECT
        USING (
            account_id IN (
                SELECT la.account_id 
                FROM loyalty_accounts la 
                JOIN customers c ON c.customer_id = la.customer_id 
                WHERE c.user_id = auth.uid()
            )
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_lots' AND tablename = 'points_lots') THEN
        CREATE POLICY customer_read_own_lots ON points_lots
        FOR SELECT
        USING (
            account_id IN (
                SELECT la.account_id 
                FROM loyalty_accounts la 
                JOIN customers c ON c.customer_id = la.customer_id 
                WHERE c.user_id = auth.uid()
            )
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_redemptions' AND tablename = 'redemptions') THEN
        CREATE POLICY customer_read_own_redemptions ON redemptions
        FOR SELECT
        USING (
            account_id IN (
                SELECT la.account_id 
                FROM loyalty_accounts la 
                JOIN customers c ON c.customer_id = la.customer_id 
                WHERE c.user_id = auth.uid()
            )
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_orders' AND tablename = 'orders') THEN
        CREATE POLICY customer_read_own_orders ON orders
        FOR SELECT
        USING (customer_id IN (SELECT customer_id FROM customers WHERE user_id = auth.uid()));
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_order_lines' AND tablename = 'order_lines') THEN
        CREATE POLICY customer_read_own_order_lines ON order_lines
        FOR SELECT
        USING (
            order_id IN (
                SELECT o.order_id 
                FROM orders o 
                JOIN customers c ON c.customer_id = o.customer_id 
                WHERE c.user_id = auth.uid()
            )
        );
    END IF;
END $$;

-- 4. Stamp Alembic Version Table if Not Present
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

INSERT INTO alembic_version (version_num)
VALUES ('001_initial_loyaltyos_schema')
ON CONFLICT (version_num) DO NOTHING;

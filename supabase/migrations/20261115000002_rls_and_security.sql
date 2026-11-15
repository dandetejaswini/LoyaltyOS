-- ==============================================================================
-- LoyaltyOS — Intelligent Loyalty & Ledger Management Platform
-- Migration: 20261115000002_rls_and_security.sql
-- Target Engine: Supabase PostgreSQL (PostgreSQL 15+)
-- Description: Establishes Role-Based Access Control (RBAC) helper functions
--              and comprehensive Row-Level Security (RLS) policies for all 21 tables.
-- ==============================================================================

-- ==============================================================================
-- 1. SECURITY DEFINER ROLE RESOLUTION FUNCTIONS
-- ==============================================================================

-- 1.1 Securely resolves the application role of the authenticated caller
CREATE OR REPLACE FUNCTION fn_get_auth_role()
RETURNS VARCHAR AS $$
DECLARE
    v_role VARCHAR;
BEGIN
    SELECT role INTO v_role
    FROM app_users
    WHERE id = auth.uid() AND is_active = true;

    RETURN COALESCE(v_role, 'CUSTOMER');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE SET search_path = public;

-- 1.2 Securely resolves the customer_id associated with the authenticated caller
CREATE OR REPLACE FUNCTION fn_get_auth_customer_id()
RETURNS VARCHAR AS $$
DECLARE
    v_customer_id VARCHAR;
BEGIN
    SELECT customer_id INTO v_customer_id
    FROM customers
    WHERE user_id = auth.uid() AND status = 'ACTIVE';

    RETURN v_customer_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE SET search_path = public;

-- 1.3 Securely resolves the account_id associated with the authenticated caller
CREATE OR REPLACE FUNCTION fn_get_auth_account_id()
RETURNS VARCHAR AS $$
DECLARE
    v_account_id VARCHAR;
BEGIN
    SELECT la.account_id INTO v_account_id
    FROM loyalty_accounts la
    JOIN customers c ON c.customer_id = la.customer_id
    WHERE c.user_id = auth.uid() AND la.status = 'ACTIVE';

    RETURN v_account_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE SET search_path = public;

-- ==============================================================================
-- 2. ENABLE ROW-LEVEL SECURITY ON ALL 21 TABLES
-- ==============================================================================

ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_identity_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE loyalty_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_returns ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_return_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE points_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE points_lots ENABLE ROW LEVEL SECURITY;
ALTER TABLE rewards ENABLE ROW LEVEL SECURITY;
ALTER TABLE redemptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE points_lot_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE expiry_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE expiry_batch_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE rejected_operations ENABLE ROW LEVEL SECURITY;
ALTER TABLE anomaly_incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE corrective_actions ENABLE ROW LEVEL SECURITY;

-- ==============================================================================
-- 3. RLS POLICIES FOR REFERENCE / MASTER TABLES (PUBLIC READ)
-- ==============================================================================

-- 3.1 Tiers: Anyone authenticated can read tiers
DROP POLICY IF EXISTS p_tiers_select ON tiers;
CREATE POLICY p_tiers_select ON tiers
    FOR SELECT TO authenticated, anon
    USING (true);

-- 3.2 Rewards: Anyone authenticated can read active rewards
DROP POLICY IF EXISTS p_rewards_select ON rewards;
CREATE POLICY p_rewards_select ON rewards
    FOR SELECT TO authenticated, anon
    USING (is_active = true OR fn_get_auth_role() IN ('OPERATOR', 'OPERATIONS_MANAGER'));

-- 3.3 Rules: Anyone authenticated can view active program rules
DROP POLICY IF EXISTS p_rules_select ON rules;
CREATE POLICY p_rules_select ON rules
    FOR SELECT TO authenticated
    USING (is_active = true OR fn_get_auth_role() = 'OPERATIONS_MANAGER');

-- ==============================================================================
-- 4. RLS POLICIES FOR APP USERS & IDENTITIES
-- ==============================================================================

DROP POLICY IF EXISTS p_app_users_select ON app_users;
CREATE POLICY p_app_users_select ON app_users
    FOR SELECT TO authenticated
    USING (
        auth.uid() = id 
        OR fn_get_auth_role() IN ('OPERATOR', 'OPERATIONS_MANAGER', 'ANALYST')
    );

DROP POLICY IF EXISTS p_user_mappings_select ON user_identity_mappings;
CREATE POLICY p_user_mappings_select ON user_identity_mappings
    FOR SELECT TO authenticated
    USING (
        auth.uid() = user_id 
        OR fn_get_auth_role() = 'OPERATIONS_MANAGER'
    );

-- ==============================================================================
-- 5. RLS POLICIES FOR CUSTOMERS & LOYALTY ACCOUNTS
-- ==============================================================================

DROP POLICY IF EXISTS p_customers_select ON customers;
CREATE POLICY p_customers_select ON customers
    FOR SELECT TO authenticated
    USING (
        auth.uid() = user_id 
        OR fn_get_auth_role() IN ('OPERATOR', 'OPERATIONS_MANAGER', 'ANALYST')
    );

DROP POLICY IF EXISTS p_loyalty_accounts_select ON loyalty_accounts;
CREATE POLICY p_loyalty_accounts_select ON loyalty_accounts
    FOR SELECT TO authenticated
    USING (
        customer_id = fn_get_auth_customer_id()
        OR fn_get_auth_role() IN ('OPERATOR', 'OPERATIONS_MANAGER', 'ANALYST')
    );

-- ==============================================================================
-- 6. RLS POLICIES FOR COMMERCE: ORDERS & RETURNS
-- ==============================================================================

DROP POLICY IF EXISTS p_orders_select ON orders;
CREATE POLICY p_orders_select ON orders
    FOR SELECT TO authenticated
    USING (
        customer_id = fn_get_auth_customer_id()
        OR fn_get_auth_role() IN ('OPERATOR', 'OPERATIONS_MANAGER', 'ANALYST')
    );

DROP POLICY IF EXISTS p_order_lines_select ON order_lines;
CREATE POLICY p_order_lines_select ON order_lines
    FOR SELECT TO authenticated
    USING (
        order_id IN (
            SELECT o.order_id FROM orders o
            WHERE o.customer_id = fn_get_auth_customer_id()
        )
        OR fn_get_auth_role() IN ('OPERATOR', 'OPERATIONS_MANAGER', 'ANALYST')
    );

DROP POLICY IF EXISTS p_order_returns_select ON order_returns;
CREATE POLICY p_order_returns_select ON order_returns
    FOR SELECT TO authenticated
    USING (
        order_id IN (
            SELECT o.order_id FROM orders o
            WHERE o.customer_id = fn_get_auth_customer_id()
        )
        OR fn_get_auth_role() IN ('OPERATOR', 'OPERATIONS_MANAGER', 'ANALYST')
    );

DROP POLICY IF EXISTS p_order_return_lines_select ON order_return_lines;
CREATE POLICY p_order_return_lines_select ON order_return_lines
    FOR SELECT TO authenticated
    USING (
        return_id IN (
            SELECT ret.return_id FROM order_returns ret
            JOIN orders o ON o.order_id = ret.order_id
            WHERE o.customer_id = fn_get_auth_customer_id()
        )
        OR fn_get_auth_role() IN ('OPERATOR', 'OPERATIONS_MANAGER', 'ANALYST')
    );

-- ==============================================================================
-- 7. RLS POLICIES FOR FINANCIAL LEDGER: TRANSACTIONS, LOTS & REDEMPTIONS
-- ==============================================================================

DROP POLICY IF EXISTS p_points_transactions_select ON points_transactions;
CREATE POLICY p_points_transactions_select ON points_transactions
    FOR SELECT TO authenticated
    USING (
        account_id = fn_get_auth_account_id()
        OR fn_get_auth_role() IN ('OPERATOR', 'OPERATIONS_MANAGER', 'ANALYST')
    );

DROP POLICY IF EXISTS p_points_lots_select ON points_lots;
CREATE POLICY p_points_lots_select ON points_lots
    FOR SELECT TO authenticated
    USING (
        account_id = fn_get_auth_account_id()
        OR fn_get_auth_role() IN ('OPERATOR', 'OPERATIONS_MANAGER', 'ANALYST')
    );

DROP POLICY IF EXISTS p_redemptions_select ON redemptions;
CREATE POLICY p_redemptions_select ON redemptions
    FOR SELECT TO authenticated
    USING (
        account_id = fn_get_auth_account_id()
        OR fn_get_auth_role() IN ('OPERATOR', 'OPERATIONS_MANAGER')
    );

DROP POLICY IF EXISTS p_points_lot_allocations_select ON points_lot_allocations;
CREATE POLICY p_points_lot_allocations_select ON points_lot_allocations
    FOR SELECT TO authenticated
    USING (
        redemption_id IN (
            SELECT r.redemption_id FROM redemptions r
            WHERE r.account_id = fn_get_auth_account_id()
        )
        OR fn_get_auth_role() IN ('OPERATOR', 'OPERATIONS_MANAGER', 'ANALYST')
    );

DROP POLICY IF EXISTS p_expiry_batches_select ON expiry_batches;
CREATE POLICY p_expiry_batches_select ON expiry_batches
    FOR SELECT TO authenticated
    USING (
        fn_get_auth_role() IN ('OPERATOR', 'OPERATIONS_MANAGER', 'ANALYST')
    );

DROP POLICY IF EXISTS p_expiry_batch_items_select ON expiry_batch_items;
CREATE POLICY p_expiry_batch_items_select ON expiry_batch_items
    FOR SELECT TO authenticated
    USING (
        fn_get_auth_role() IN ('OPERATOR', 'OPERATIONS_MANAGER', 'ANALYST')
    );

-- ==============================================================================
-- 8. RLS POLICIES FOR LLIRE ANOMALIES & AUDIT LOGS
-- ==============================================================================

DROP POLICY IF EXISTS p_anomaly_incidents_select ON anomaly_incidents;
CREATE POLICY p_anomaly_incidents_select ON anomaly_incidents
    FOR SELECT TO authenticated
    USING (
        (fn_get_auth_role() = 'CUSTOMER' AND entity_id = fn_get_auth_account_id())
        OR fn_get_auth_role() IN ('ANALYST', 'OPERATIONS_MANAGER')
    );

DROP POLICY IF EXISTS p_corrective_actions_select ON corrective_actions;
CREATE POLICY p_corrective_actions_select ON corrective_actions
    FOR SELECT TO authenticated
    USING (
        fn_get_auth_role() = 'OPERATIONS_MANAGER'
    );

DROP POLICY IF EXISTS p_audit_events_select ON audit_events;
CREATE POLICY p_audit_events_select ON audit_events
    FOR SELECT TO authenticated
    USING (
        fn_get_auth_role() IN ('OPERATIONS_MANAGER', 'ANALYST')
    );

DROP POLICY IF EXISTS p_rejected_operations_select ON rejected_operations;
CREATE POLICY p_rejected_operations_select ON rejected_operations
    FOR SELECT TO authenticated
    USING (
        account_id = fn_get_auth_account_id()
        OR fn_get_auth_role() IN ('OPERATOR', 'OPERATIONS_MANAGER', 'ANALYST')
    );

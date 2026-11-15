-- ==============================================================================
-- LoyaltyOS — Intelligent Loyalty & Ledger Management Platform
-- Migration: 20261115000003_business_rpc_functions.sql
-- Target Engine: Supabase PostgreSQL (PostgreSQL 15+)
-- Description: Core transactional loyalty business logic implemented as
--              atomic, concurrency-safe PostgreSQL stored functions (RPC).
-- ==============================================================================

-- ==============================================================================
-- 1. HELPER: AUDIT EVENT LOGGER
-- ==============================================================================
CREATE OR REPLACE FUNCTION fn_log_audit_event(
    p_actor_id TEXT,
    p_action TEXT,
    p_entity_type TEXT,
    p_entity_id TEXT,
    p_metadata JSONB DEFAULT NULL,
    p_ip_address TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO audit_events (
        event_id,
        actor_id,
        action,
        entity_type,
        entity_id,
        metadata_payload,
        ip_address,
        created_at
    ) VALUES (
        'AUD-' || TO_CHAR(NOW() AT TIME ZONE 'UTC', 'YYYYMMDD') || '-' || UPPER(SUBSTR(MD5(RANDOM()::TEXT), 1, 8)),
        p_actor_id,
        p_action,
        p_entity_type,
        p_entity_id,
        p_metadata,
        p_ip_address,
        NOW()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- ==============================================================================
-- 2. PROFILE RESOLUTION & ONBOARDING (fn_get_my_profile)
-- ==============================================================================
CREATE OR REPLACE FUNCTION fn_get_my_profile()
RETURNS JSONB AS $$
DECLARE
    v_user_id UUID;
    v_user RECORD;
    v_customer RECORD;
    v_account RECORD;
    v_res JSONB;
BEGIN
    v_user_id := auth.uid();
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Authentication required: caller has no active Supabase Auth session.';
    END IF;

    -- Look up internal app_user
    SELECT * INTO v_user FROM app_users WHERE id = v_user_id;

    -- If app_user does not exist, provision default user profile from auth.users
    IF v_user IS NULL THEN
        INSERT INTO app_users (id, email, full_name, role, is_active, created_at, updated_at)
        SELECT 
            v_user_id,
            COALESCE(email, 'user_' || SUBSTR(v_user_id::text, 1, 8) || '@loyaltyos.internal'),
            COALESCE(raw_user_meta_data->>'full_name', email),
            'CUSTOMER',
            true,
            NOW(),
            NOW()
        FROM auth.users
        WHERE id = v_user_id
        RETURNING * INTO v_user;
    END IF;

    -- Resolve customer record
    SELECT * INTO v_customer FROM customers WHERE user_id = v_user_id;

    -- If user is customer and customer record does not exist, auto-provision
    IF v_customer IS NULL AND v_user.role = 'CUSTOMER' THEN
        INSERT INTO customers (customer_id, user_id, email, first_name, last_name, status, created_at, updated_at)
        VALUES (
            'CUST-' || UPPER(SUBSTR(MD5(v_user_id::text), 1, 8)),
            v_user_id,
            v_user.email,
            COALESCE(SPLIT_PART(v_user.full_name, ' ', 1), 'Loyalty'),
            COALESCE(NULLIF(SUBSTR(v_user.full_name, LENGTH(SPLIT_PART(v_user.full_name, ' ', 1)) + 2), ''), 'Member'),
            'ACTIVE',
            NOW(),
            NOW()
        )
        RETURNING * INTO v_customer;

        -- Create associated loyalty account
        INSERT INTO loyalty_accounts (account_id, customer_id, tier_id, current_balance, lifetime_accrued, lifetime_redeemed, qualifying_spend, status, created_at, updated_at)
        VALUES (
            'LOY-' || v_customer.customer_id,
            v_customer.customer_id,
            'TIER-BRONZE',
            0,
            0,
            0,
            0.00,
            'ACTIVE',
            NOW(),
            NOW()
        )
        RETURNING * INTO v_account;
    ELSE
        SELECT * INTO v_account FROM loyalty_accounts WHERE customer_id = v_customer.customer_id;
    END IF;

    v_res := jsonb_build_object(
        'id', v_user.id,
        'email', v_user.email,
        'full_name', v_user.full_name,
        'role', v_user.role,
        'is_active', v_user.is_active,
        'created_at', v_user.created_at
    );

    IF v_customer IS NOT NULL THEN
        v_res := v_res || jsonb_build_object(
            'customer', jsonb_build_object(
                'customer_id', v_customer.customer_id,
                'email', v_customer.email,
                'first_name', v_customer.first_name,
                'last_name', v_customer.last_name,
                'status', v_customer.status,
                'loyalty_account', CASE WHEN v_account IS NOT NULL THEN jsonb_build_object(
                    'account_id', v_account.account_id,
                    'tier_id', v_account.tier_id,
                    'current_balance', v_account.current_balance,
                    'lifetime_accrued', v_account.lifetime_accrued,
                    'lifetime_redeemed', v_account.lifetime_redeemed,
                    'qualifying_spend', v_account.qualifying_spend,
                    'status', v_account.status
                ) ELSE NULL END
            )
        );
    END IF;

    RETURN v_res;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- ==============================================================================
-- 3. CUSTOMER PROVISIONING (fn_provision_customer)
-- ==============================================================================
CREATE OR REPLACE FUNCTION fn_provision_customer(
    p_email TEXT,
    p_first_name TEXT,
    p_last_name TEXT,
    p_phone TEXT DEFAULT NULL,
    p_role TEXT DEFAULT 'CUSTOMER'
)
RETURNS JSONB AS $$
DECLARE
    v_user_id UUID;
    v_cust_id TEXT;
    v_account_id TEXT;
    v_caller_role TEXT;
    v_existing_user RECORD;
    v_existing_cust RECORD;
BEGIN
    v_caller_role := fn_get_auth_role();
    IF v_caller_role NOT IN ('OPERATOR', 'OPERATIONS_MANAGER') AND auth.uid() IS NOT NULL THEN
        -- Allow self-provisioning if caller has no customer profile
        NULL;
    END IF;

    -- Check if email exists
    SELECT * INTO v_existing_cust FROM customers WHERE email = LOWER(TRIM(p_email));
    IF v_existing_cust IS NOT NULL THEN
        RAISE EXCEPTION 'Customer with email % already exists.', p_email;
    END IF;

    -- Provision App User
    SELECT * INTO v_existing_user FROM app_users WHERE email = LOWER(TRIM(p_email));
    IF v_existing_user IS NULL THEN
        v_user_id := gen_random_uuid();
        INSERT INTO app_users (id, email, full_name, role, is_active)
        VALUES (v_user_id, LOWER(TRIM(p_email)), TRIM(p_first_name || ' ' || p_last_name), p_role, true);
    ELSE
        v_user_id := v_existing_user.id;
    END IF;

    -- Provision Customer
    v_cust_id := 'CUST-' || UPPER(SUBSTR(MD5(p_email || NOW()::TEXT), 1, 8));
    INSERT INTO customers (customer_id, user_id, email, first_name, last_name, phone, status)
    VALUES (v_cust_id, v_user_id, LOWER(TRIM(p_email)), TRIM(p_first_name), TRIM(p_last_name), p_phone, 'ACTIVE');

    -- Provision Loyalty Account
    v_account_id := 'LOY-' || v_cust_id;
    INSERT INTO loyalty_accounts (account_id, customer_id, tier_id, current_balance, lifetime_accrued, lifetime_redeemed, qualifying_spend, status)
    VALUES (v_account_id, v_cust_id, 'TIER-BRONZE', 0, 0, 0, 0.00, 'ACTIVE');

    PERFORM fn_log_audit_event(
        COALESCE(auth.uid()::TEXT, 'SYSTEM'),
        'CUSTOMER_PROVISIONED',
        'CUSTOMER',
        v_cust_id,
        jsonb_build_object('account_id', v_account_id, 'email', p_email)
    );

    RETURN jsonb_build_object(
        'customer_id', v_cust_id,
        'user_id', v_user_id,
        'account_id', v_account_id,
        'email', p_email,
        'status', 'ACTIVE'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- ==============================================================================
-- 4. ORDER POINTS ACCRUAL (fn_accrue_order_points)
-- ==============================================================================
CREATE OR REPLACE FUNCTION fn_accrue_order_points(
    p_customer_id TEXT,
    p_order_id TEXT,
    p_lines JSONB,
    p_tax_amount NUMERIC DEFAULT 0.00,
    p_shipping_amount NUMERIC DEFAULT 0.00,
    p_discount_amount NUMERIC DEFAULT 0.00,
    p_idempotency_key TEXT DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_account RECORD;
    v_tier RECORD;
    v_multiplier NUMERIC;
    v_eligible_net NUMERIC := 0.00;
    v_merch_gross NUMERIC := 0.00;
    v_line RECORD;
    v_line_net NUMERIC;
    v_line_idx INT := 1;
    v_points_to_accrue INT;
    v_new_balance INT;
    v_tx_id TEXT;
    v_lot_id TEXT;
    v_order_id TEXT;
    v_now TIMESTAMPTZ := NOW();
    v_existing_tx RECORD;
BEGIN
    -- 1. Idempotency Check
    IF p_idempotency_key IS NOT NULL THEN
        SELECT * INTO v_existing_tx FROM points_transactions WHERE idempotency_key = p_idempotency_key;
        IF v_existing_tx IS NOT NULL THEN
            RETURN jsonb_build_object(
                'status', 'ALREADY_PROCESSED',
                'transaction_id', v_existing_tx.transaction_id,
                'points_accrued', v_existing_tx.points,
                'running_balance', v_existing_tx.running_balance,
                'message', 'Transaction was previously accrued under this idempotency key.'
            );
        END IF;
    END IF;

    -- 2. Resolve Customer Account & Lock Row
    SELECT la.*, c.status as cust_status 
    INTO v_account
    FROM loyalty_accounts la
    JOIN customers c ON c.customer_id = la.customer_id
    WHERE la.customer_id = p_customer_id
    FOR UPDATE;

    IF v_account IS NULL THEN
        RAISE EXCEPTION 'Customer % or loyalty account not found.', p_customer_id;
    END IF;

    IF v_account.status <> 'ACTIVE' THEN
        RAISE EXCEPTION 'Loyalty account % is not active (Status: %).', v_account.account_id, v_account.status;
    END IF;

    -- 3. Resolve Tier Multiplier
    SELECT * INTO v_tier FROM tiers WHERE tier_id = v_account.tier_id;
    v_multiplier := COALESCE(v_tier.earning_multiplier, 1.00);

    -- 4. Process Order Lines & Compute Eligible Net Spend
    FOR v_line IN SELECT * FROM jsonb_to_recordset(p_lines) AS x(
        sku TEXT,
        product_name TEXT,
        category TEXT,
        quantity INT,
        unit_price NUMERIC,
        item_discount NUMERIC,
        is_eligible BOOLEAN
    ) LOOP
        v_line_net := GREATEST(0.00, (v_line.quantity * v_line.unit_price) - COALESCE(v_line.item_discount, 0.00));
        v_merch_gross := v_merch_gross + (v_line.quantity * v_line.unit_price);

        IF COALESCE(v_line.is_eligible, true) THEN
            v_eligible_net := v_eligible_net + v_line_net;
        END IF;
    END LOOP;

    -- 5. Calculate Points with Floor-Rounding (BR-03)
    v_points_to_accrue := FLOOR(v_eligible_net * v_multiplier)::INT;

    -- 6. Insert Order
    v_order_id := COALESCE(p_order_id, 'ORD-' || TO_CHAR(v_now AT TIME ZONE 'UTC', 'YYYYMMDD') || '-' || UPPER(SUBSTR(MD5(RANDOM()::TEXT), 1, 6)));
    
    INSERT INTO orders (
        order_id, customer_id, order_date, gross_amount, tax_amount, shipping_amount,
        discount_amount, eligible_net_spend, status, accrual_status, created_at
    ) VALUES (
        v_order_id,
        p_customer_id,
        v_now,
        GREATEST(0.00, v_merch_gross + p_tax_amount + p_shipping_amount - p_discount_amount),
        p_tax_amount,
        p_shipping_amount,
        p_discount_amount,
        v_eligible_net,
        'COMPLETED',
        CASE WHEN v_points_to_accrue > 0 THEN 'ACCRUED' ELSE 'EXCLUDED' END,
        v_now
    )
    ON CONFLICT (order_id) DO NOTHING;

    -- Insert Order Lines
    FOR v_line IN SELECT * FROM jsonb_to_recordset(p_lines) AS x(
        sku TEXT, product_name TEXT, category TEXT, quantity INT,
        unit_price NUMERIC, item_discount NUMERIC, is_eligible BOOLEAN
    ) LOOP
        INSERT INTO order_lines (
            order_line_id, order_id, line_number, sku, product_name, category,
            quantity, unit_price, item_discount, net_amount, is_eligible, created_at
        ) VALUES (
            'ORDL-' || v_order_id || '-' || LPAD(v_line_idx::TEXT, 2, '0'),
            v_order_id,
            v_line_idx,
            v_line.sku,
            v_line.product_name,
            v_line.category,
            v_line.quantity,
            v_line.unit_price,
            COALESCE(v_line.item_discount, 0.00),
            GREATEST(0.00, (v_line.quantity * v_line.unit_price) - COALESCE(v_line.item_discount, 0.00)),
            COALESCE(v_line.is_eligible, true),
            v_now
        )
        ON CONFLICT (order_id, line_number) DO NOTHING;
        v_line_idx := v_line_idx + 1;
    END LOOP;

    -- 7. If points accrue, append to Journal and create FIFO Lot
    IF v_points_to_accrue > 0 THEN
        v_new_balance := v_account.current_balance + v_points_to_accrue;
        v_tx_id := 'PTS-' || TO_CHAR(v_now AT TIME ZONE 'UTC', 'YYYYMMDD') || '-' || UPPER(SUBSTR(MD5(RANDOM()::TEXT), 1, 8));
        v_lot_id := 'LOT-' || TO_CHAR(v_now AT TIME ZONE 'UTC', 'YYYYMMDD') || '-' || UPPER(SUBSTR(MD5(RANDOM()::TEXT), 1, 8));

        INSERT INTO points_transactions (
            transaction_id, account_id, order_id, entry_type, points,
            running_balance, idempotency_key, notes, created_at
        ) VALUES (
            v_tx_id,
            v_account.account_id,
            v_order_id,
            'ACCRUAL',
            v_points_to_accrue,
            v_new_balance,
            p_idempotency_key,
            'Points accrued for order ' || v_order_id || ' ($' || v_eligible_net || ' eligible spend @ ' || v_multiplier || 'x)',
            v_now
        );

        INSERT INTO points_lots (
            lot_id, transaction_id, account_id, initial_points, remaining_points,
            status, expires_at, created_at, updated_at
        ) VALUES (
            v_lot_id,
            v_tx_id,
            v_account.account_id,
            v_points_to_accrue,
            v_points_to_accrue,
            'ACTIVE',
            v_now + INTERVAL '365 days',
            v_now,
            v_now
        );

        UPDATE loyalty_accounts
        SET current_balance = v_new_balance,
            lifetime_accrued = lifetime_accrued + v_points_to_accrue,
            qualifying_spend = qualifying_spend + v_eligible_net,
            updated_at = v_now
        WHERE account_id = v_account.account_id;
    ELSE
        v_new_balance := v_account.current_balance;
    END IF;

    PERFORM fn_log_audit_event(
        COALESCE(auth.uid()::TEXT, 'SYSTEM'),
        'ORDER_ACCRUAL',
        'ORDER',
        v_order_id,
        jsonb_build_object('points_accrued', v_points_to_accrue, 'eligible_net', v_eligible_net, 'multiplier', v_multiplier)
    );

    RETURN jsonb_build_object(
        'order_id', v_order_id,
        'points_accrued', v_points_to_accrue,
        'eligible_net_spend', v_eligible_net,
        'tier_multiplier', v_multiplier,
        'running_balance', v_new_balance,
        'transaction_id', v_tx_id,
        'status', 'COMPLETED'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- ==============================================================================
-- 5. REWARD REDEMPTION (fn_redeem_reward)
-- ==============================================================================
CREATE OR REPLACE FUNCTION fn_redeem_reward(
    p_account_id TEXT,
    p_reward_id TEXT,
    p_idempotency_key TEXT DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_account RECORD;
    v_reward RECORD;
    v_lot RECORD;
    v_points_needed INT;
    v_allocated_total INT := 0;
    v_take INT;
    v_new_balance INT;
    v_tx_id TEXT;
    v_rdm_id TEXT;
    v_voucher_code TEXT;
    v_now TIMESTAMPTZ := NOW();
    v_existing_tx RECORD;
BEGIN
    -- 1. Idempotency Check
    IF p_idempotency_key IS NOT NULL THEN
        SELECT * INTO v_existing_tx FROM points_transactions WHERE idempotency_key = p_idempotency_key;
        IF v_existing_tx IS NOT NULL THEN
            SELECT * INTO v_existing_tx FROM redemptions WHERE transaction_id = v_existing_tx.transaction_id;
            RETURN jsonb_build_object(
                'status', 'ALREADY_PROCESSED',
                'redemption_id', v_existing_tx.redemption_id,
                'voucher_code', v_existing_tx.voucher_code,
                'points_redeemed', v_existing_tx.points_redeemed,
                'message', 'Redemption was already completed under this idempotency key.'
            );
        END IF;
    END IF;

    -- 2. Concurrency-Safe Account Lock
    SELECT * INTO v_account FROM loyalty_accounts WHERE account_id = p_account_id FOR UPDATE;
    IF v_account IS NULL THEN
        RAISE EXCEPTION 'Loyalty account % does not exist.', p_account_id;
    END IF;

    IF v_account.status <> 'ACTIVE' THEN
        RAISE EXCEPTION 'Account % is frozen or suspended. Redemptions are prohibited.', p_account_id;
    END IF;

    IF v_account.current_balance < 0 THEN
        RAISE EXCEPTION 'Account balance is negative (% pts). Redemptions frozen until liabilities cleared.', v_account.current_balance;
    END IF;

    -- 3. Reward Validation
    SELECT * INTO v_reward FROM rewards WHERE reward_id = p_reward_id FOR UPDATE;
    IF v_reward IS NULL OR NOT v_reward.is_active THEN
        RAISE EXCEPTION 'Reward % is unavailable.', p_reward_id;
    END IF;

    IF v_reward.stock_quantity IS NOT NULL AND v_reward.stock_quantity <= 0 THEN
        RAISE EXCEPTION 'Reward % is out of stock.', v_reward.name;
    END IF;

    v_points_needed := v_reward.points_required;
    IF v_account.current_balance < v_points_needed THEN
        RAISE EXCEPTION 'Insufficient points: % available, % required.', v_account.current_balance, v_points_needed;
    END IF;

    -- 4. FIFO Lot Consumption (expires_at ASC, created_at ASC)
    v_now := NOW();
    v_tx_id := 'PTS-' || TO_CHAR(v_now AT TIME ZONE 'UTC', 'YYYYMMDD') || '-' || UPPER(SUBSTR(MD5(RANDOM()::TEXT), 1, 8));
    v_rdm_id := 'RDM-' || TO_CHAR(v_now AT TIME ZONE 'UTC', 'YYYYMMDD') || '-' || UPPER(SUBSTR(MD5(RANDOM()::TEXT), 1, 6));
    v_voucher_code := 'VOUCH-' || UPPER(SUBSTR(MD5(RANDOM()::TEXT), 1, 6)) || '-' || (FLOOR(RANDOM() * 900000 + 100000))::INT;
    v_new_balance := v_account.current_balance - v_points_needed;

    -- Create Ledger Transaction (Debit)
    INSERT INTO points_transactions (
        transaction_id, account_id, entry_type, points, running_balance,
        idempotency_key, notes, created_at
    ) VALUES (
        v_tx_id,
        p_account_id,
        'REDEMPTION',
        -v_points_needed,
        v_new_balance,
        p_idempotency_key,
        'Redeemed for: ' || v_reward.name,
        v_now
    );

    -- Create Redemption Record
    INSERT INTO redemptions (
        redemption_id, account_id, reward_id, transaction_id, points_redeemed,
        voucher_code, status, created_at
    ) VALUES (
        v_rdm_id,
        p_account_id,
        p_reward_id,
        v_tx_id,
        v_points_needed,
        v_voucher_code,
        'COMPLETED',
        v_now
    );

    -- Greedily Allocate from Active Lots
    FOR v_lot IN (
        SELECT * FROM points_lots
        WHERE account_id = p_account_id 
          AND remaining_points > 0 
          AND status IN ('ACTIVE', 'PARTIALLY_REDEEMED')
          AND expires_at > v_now
        ORDER BY expires_at ASC, created_at ASC
        FOR UPDATE
    ) LOOP
        IF v_allocated_total >= v_points_needed THEN
            EXIT;
        END IF;

        v_take := LEAST(v_lot.remaining_points, v_points_needed - v_allocated_total);
        v_allocated_total := v_allocated_total + v_take;

        INSERT INTO points_lot_allocations (
            allocation_id, redemption_id, lot_id, points_allocated, created_at
        ) VALUES (
            'ALL-' || TO_CHAR(v_now AT TIME ZONE 'UTC', 'YYYYMMDD') || '-' || UPPER(SUBSTR(MD5(RANDOM()::TEXT), 1, 8)),
            v_rdm_id,
            v_lot.lot_id,
            v_take,
            v_now
        );

        UPDATE points_lots
        SET remaining_points = remaining_points - v_take,
            status = CASE WHEN remaining_points - v_take = 0 THEN 'EXHAUSTED' ELSE 'PARTIALLY_REDEEMED' END,
            updated_at = v_now
        WHERE lot_id = v_lot.lot_id;
    END LOOP;

    -- Update Loyalty Account
    UPDATE loyalty_accounts
    SET current_balance = v_new_balance,
        lifetime_redeemed = lifetime_redeemed + v_points_needed,
        updated_at = v_now
    WHERE account_id = p_account_id;

    -- Decrement stock if tracked
    IF v_reward.stock_quantity IS NOT NULL THEN
        UPDATE rewards SET stock_quantity = stock_quantity - 1 WHERE reward_id = p_reward_id;
    END IF;

    PERFORM fn_log_audit_event(
        COALESCE(auth.uid()::TEXT, 'SYSTEM'),
        'REWARD_REDEEMED',
        'REDEMPTION',
        v_rdm_id,
        jsonb_build_object('reward_id', p_reward_id, 'points_redeemed', v_points_needed, 'voucher_code', v_voucher_code)
    );

    RETURN jsonb_build_object(
        'redemption_id', v_rdm_id,
        'transaction_id', v_tx_id,
        'account_id', p_account_id,
        'reward_id', p_reward_id,
        'points_redeemed', v_points_needed,
        'voucher_code', v_voucher_code,
        'running_balance', v_new_balance,
        'status', 'COMPLETED'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- ==============================================================================
-- 6. ORDER RETURN & PROPORTIONAL REVERSAL (fn_process_order_return)
-- ==============================================================================
CREATE OR REPLACE FUNCTION fn_process_order_return(
    p_order_id TEXT,
    p_return_lines JSONB,
    p_idempotency_key TEXT DEFAULT NULL,
    p_reason TEXT DEFAULT 'Merchandise Return'
)
RETURNS JSONB AS $$
DECLARE
    v_order RECORD;
    v_account RECORD;
    v_tier RECORD;
    v_multiplier NUMERIC;
    v_orig_accrual RECORD;
    v_orig_accrual_pts INT := 0;
    v_already_reversed_pts INT := 0;
    v_remaining_reversible INT := 0;
    v_return_id TEXT;
    v_total_refund NUMERIC := 0.00;
    v_eligible_refund NUMERIC := 0.00;
    v_line RECORD;
    v_ord_line RECORD;
    v_line_refund NUMERIC;
    v_points_to_reverse INT;
    v_new_balance INT;
    v_tx_id TEXT;
    v_now TIMESTAMPTZ := NOW();
    v_existing_tx RECORD;
BEGIN
    -- 1. Idempotency Check
    IF p_idempotency_key IS NOT NULL THEN
        SELECT * INTO v_existing_tx FROM points_transactions WHERE idempotency_key = p_idempotency_key;
        IF v_existing_tx IS NOT NULL THEN
            RETURN jsonb_build_object(
                'status', 'ALREADY_PROCESSED',
                'transaction_id', v_existing_tx.transaction_id,
                'points_reversed', v_existing_tx.points,
                'running_balance', v_existing_tx.running_balance,
                'message', 'Return was previously processed under this idempotency key.'
            );
        END IF;
    END IF;

    -- 2. Retrieve Order & Account
    SELECT * INTO v_order FROM orders WHERE order_id = p_order_id;
    IF v_order IS NULL THEN
        RAISE EXCEPTION 'Order % not found.', p_order_id;
    END IF;

    SELECT la.* INTO v_account
    FROM loyalty_accounts la
    JOIN customers c ON c.customer_id = la.customer_id
    WHERE c.customer_id = v_order.customer_id
    FOR UPDATE;

    SELECT * INTO v_tier FROM tiers WHERE tier_id = v_account.tier_id;
    v_multiplier := COALESCE(v_tier.earning_multiplier, 1.00);

    -- 3. Calculate Remaining Reversible Points
    SELECT * INTO v_orig_accrual FROM points_transactions 
    WHERE order_id = p_order_id AND entry_type = 'ACCRUAL';
    v_orig_accrual_pts := COALESCE(v_orig_accrual.points, 0);

    SELECT ABS(COALESCE(SUM(points), 0))::INT INTO v_already_reversed_pts
    FROM points_transactions 
    WHERE order_id = p_order_id AND entry_type = 'REVERSAL';

    v_remaining_reversible := GREATEST(0, v_orig_accrual_pts - v_already_reversed_pts);

    -- 4. Process Return Lines
    v_return_id := 'RET-' || TO_CHAR(v_now AT TIME ZONE 'UTC', 'YYYYMMDD') || '-' || UPPER(SUBSTR(MD5(RANDOM()::TEXT), 1, 6));

    FOR v_line IN SELECT * FROM jsonb_to_recordset(p_return_lines) AS x(
        order_line_id TEXT,
        quantity_returned INT,
        refund_amount NUMERIC
    ) LOOP
        SELECT * INTO v_ord_line FROM order_lines WHERE order_line_id = v_line.order_line_id;
        v_line_refund := COALESCE(v_line.refund_amount, v_line.quantity_returned * v_ord_line.unit_price);
        v_total_refund := v_total_refund + v_line_refund;

        IF v_ord_line.is_eligible THEN
            v_eligible_refund := v_eligible_refund + v_line_refund;
        END IF;
    END LOOP;

    -- Compute proportional reversal points
    v_points_to_reverse := LEAST(v_remaining_reversible, FLOOR(v_eligible_refund * v_multiplier)::INT);

    -- Insert Order Return
    INSERT INTO order_returns (return_id, order_id, return_date, refund_amount, reason, created_at)
    VALUES (v_return_id, p_order_id, v_now, v_total_refund, p_reason, v_now);

    -- Insert Return Lines
    FOR v_line IN SELECT * FROM jsonb_to_recordset(p_return_lines) AS x(
        order_line_id TEXT, quantity_returned INT, refund_amount NUMERIC
    ) LOOP
        INSERT INTO order_return_lines (return_line_id, return_id, order_line_id, quantity_returned, refund_amount, created_at)
        VALUES (
            'RETL-' || v_return_id || '-' || UPPER(SUBSTR(MD5(RANDOM()::TEXT), 1, 6)),
            v_return_id,
            v_line.order_line_id,
            v_line.quantity_returned,
            COALESCE(v_line.refund_amount, 0.00),
            v_now
        );
    END LOOP;

    -- If points reversed, post Reversal Debit to Ledger
    IF v_points_to_reverse > 0 THEN
        v_new_balance := v_account.current_balance - v_points_to_reverse;
        v_tx_id := 'PTS-' || TO_CHAR(v_now AT TIME ZONE 'UTC', 'YYYYMMDD') || '-' || UPPER(SUBSTR(MD5(RANDOM()::TEXT), 1, 8));

        INSERT INTO points_transactions (
            transaction_id, account_id, order_id, related_transaction_id,
            entry_type, points, running_balance, idempotency_key, notes, created_at
        ) VALUES (
            v_tx_id,
            v_account.account_id,
            p_order_id,
            v_orig_accrual.transaction_id,
            'REVERSAL',
            -v_points_to_reverse,
            v_new_balance,
            p_idempotency_key,
            'Proportional return reversal for order ' || p_order_id || ' (-' || v_points_to_reverse || ' pts)',
            v_now
        );

        UPDATE loyalty_accounts
        SET current_balance = v_new_balance,
            updated_at = v_now
        WHERE account_id = v_account.account_id;
    ELSE
        v_new_balance := v_account.current_balance;
    END IF;

    PERFORM fn_log_audit_event(
        COALESCE(auth.uid()::TEXT, 'SYSTEM'),
        'ORDER_RETURN_PROCESSED',
        'ORDER_RETURN',
        v_return_id,
        jsonb_build_object('order_id', p_order_id, 'points_reversed', v_points_to_reverse, 'new_balance', v_new_balance)
    );

    RETURN jsonb_build_object(
        'return_id', v_return_id,
        'order_id', p_order_id,
        'points_reversed', v_points_to_reverse,
        'remaining_reversible_points', v_remaining_reversible - v_points_to_reverse,
        'running_balance', v_new_balance,
        'status', 'COMPLETED'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- ==============================================================================
-- 7. 3-WAY RECONCILIATION ENGINE (fn_reconcile_account)
-- ==============================================================================
CREATE OR REPLACE FUNCTION fn_reconcile_account(
    p_account_id TEXT
)
RETURNS JSONB AS $$
DECLARE
    v_account RECORD;
    v_stored_balance INT;
    v_journal_balance INT;
    v_active_lots_balance INT;
    v_discrepancy INT;
    v_breakdown JSONB;
BEGIN
    SELECT * INTO v_account FROM loyalty_accounts WHERE account_id = p_account_id;
    IF v_account IS NULL THEN
        RAISE EXCEPTION 'Account % not found.', p_account_id;
    END IF;

    v_stored_balance := v_account.current_balance;

    -- 1. Sum of all immutable journal entries
    SELECT COALESCE(SUM(points), 0)::INT INTO v_journal_balance
    FROM points_transactions
    WHERE account_id = p_account_id;

    -- 2. Sum of unexpired active lots
    SELECT COALESCE(SUM(remaining_points), 0)::INT INTO v_active_lots_balance
    FROM points_lots
    WHERE account_id = p_account_id 
      AND status IN ('ACTIVE', 'PARTIALLY_REDEEMED')
      AND expires_at > NOW();

    -- 3. Invariant check: stored == journal
    v_discrepancy := v_stored_balance - v_journal_balance;

    -- Breakdown by entry_type
    SELECT jsonb_object_agg(entry_type, total) INTO v_breakdown FROM (
        SELECT entry_type, COALESCE(SUM(points), 0)::INT as total
        FROM points_transactions
        WHERE account_id = p_account_id
        GROUP BY entry_type
    ) b;

    RETURN jsonb_build_object(
        'account_id', p_account_id,
        'customer_id', v_account.customer_id,
        'stored_balance', v_stored_balance,
        'ledger_derived_balance', v_journal_balance,
        'active_lots_balance', v_active_lots_balance,
        'discrepancy_amount', v_discrepancy,
        'is_reconciled', (v_discrepancy = 0),
        'status', CASE WHEN v_discrepancy = 0 THEN 'RECONCILED' ELSE 'DISCREPANCY_DETECTED' END,
        'breakdown', COALESCE(v_breakdown, '{}'::jsonb),
        'evaluation_time', NOW()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- ==============================================================================
-- 8. TIER EVALUATION (fn_evaluate_account_tier)
-- ==============================================================================
CREATE OR REPLACE FUNCTION fn_evaluate_account_tier(
    p_account_id TEXT
)
RETURNS JSONB AS $$
DECLARE
    v_account RECORD;
    v_qualifying_spend NUMERIC;
    v_eligible_tier RECORD;
    v_previous_tier TEXT;
    v_upgraded BOOLEAN := false;
BEGIN
    SELECT * INTO v_account FROM loyalty_accounts WHERE account_id = p_account_id FOR UPDATE;
    IF v_account IS NULL THEN
        RAISE EXCEPTION 'Account % not found.', p_account_id;
    END IF;

    v_previous_tier := v_account.tier_id;

    -- Calculate rolling 365-day qualifying spend from completed orders
    SELECT COALESCE(SUM(eligible_net_spend), 0.00) INTO v_qualifying_spend
    FROM orders
    WHERE customer_id = v_account.customer_id
      AND order_date >= NOW() - INTERVAL '365 days'
      AND status = 'COMPLETED';

    -- Find eligible tier with highest rank where min_spend <= qualifying_spend
    SELECT * INTO v_eligible_tier 
    FROM tiers 
    WHERE min_spend <= v_qualifying_spend 
    ORDER BY rank DESC 
    LIMIT 1;

    IF v_eligible_tier IS NOT NULL AND v_eligible_tier.tier_id <> v_previous_tier THEN
        UPDATE loyalty_accounts
        SET tier_id = v_eligible_tier.tier_id,
            qualifying_spend = v_qualifying_spend,
            updated_at = NOW()
        WHERE account_id = p_account_id;
        v_upgraded := true;

        PERFORM fn_log_audit_event(
            COALESCE(auth.uid()::TEXT, 'SYSTEM'),
            'TIER_EVALUATED',
            'LOYALTY_ACCOUNT',
            p_account_id,
            jsonb_build_object('previous_tier', v_previous_tier, 'new_tier', v_eligible_tier.tier_id, 'qualifying_spend', v_qualifying_spend)
        );
    END IF;

    RETURN jsonb_build_object(
        'account_id', p_account_id,
        'previous_tier_id', v_previous_tier,
        'new_tier_id', COALESCE(v_eligible_tier.tier_id, v_previous_tier),
        'qualifying_spend', v_qualifying_spend,
        'upgraded', v_upgraded
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- ==============================================================================
-- 9. POINTS EXPIRY BATCH EXECUTION (fn_expire_points_lots)
-- ==============================================================================
CREATE OR REPLACE FUNCTION fn_expire_points_lots(
    p_cutoff_date TIMESTAMPTZ DEFAULT NOW(),
    p_idempotency_key TEXT DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_batch_id TEXT;
    v_lot RECORD;
    v_account RECORD;
    v_total_lots INT := 0;
    v_total_points INT := 0;
    v_tx_id TEXT;
    v_item_id TEXT;
    v_new_balance INT;
    v_now TIMESTAMPTZ := NOW();
    v_existing_batch RECORD;
BEGIN
    v_batch_id := COALESCE(p_idempotency_key, 'EXP-' || TO_CHAR(v_now AT TIME ZONE 'UTC', 'YYYYMMDD-HH24MISS'));

    -- Check if batch was already processed
    SELECT * INTO v_existing_batch FROM expiry_batches WHERE batch_id = v_batch_id;
    IF v_existing_batch IS NOT NULL THEN
        RETURN jsonb_build_object(
            'status', 'ALREADY_PROCESSED',
            'batch_id', v_batch_id,
            'total_lots_processed', v_existing_batch.total_lots_processed,
            'total_points_expired', v_existing_batch.total_points_expired
        );
    END IF;

    INSERT INTO expiry_batches (batch_id, cutoff_date, total_lots_processed, total_points_expired, status, created_at)
    VALUES (v_batch_id, p_cutoff_date, 0, 0, 'IN_PROGRESS', v_now);

    FOR v_lot IN (
        SELECT * FROM points_lots
        WHERE expires_at <= p_cutoff_date
          AND remaining_points > 0
          AND status IN ('ACTIVE', 'PARTIALLY_REDEEMED')
        ORDER BY expires_at ASC
        FOR UPDATE
    ) LOOP
        v_total_lots := v_total_lots + 1;
        v_total_points := v_total_points + v_lot.remaining_points;

        SELECT * INTO v_account FROM loyalty_accounts WHERE account_id = v_lot.account_id FOR UPDATE;
        v_new_balance := v_account.current_balance - v_lot.remaining_points;

        v_tx_id := 'PTS-' || TO_CHAR(v_now AT TIME ZONE 'UTC', 'YYYYMMDD') || '-' || UPPER(SUBSTR(MD5(RANDOM()::TEXT), 1, 8));
        v_item_id := 'EXP-ITEM-' || v_batch_id || '-' || LPAD(v_total_lots::TEXT, 4, '0');

        INSERT INTO points_transactions (
            transaction_id, account_id, entry_type, points, running_balance,
            idempotency_key, notes, created_at
        ) VALUES (
            v_tx_id,
            v_lot.account_id,
            'EXPIRY',
            -v_lot.remaining_points,
            v_new_balance,
            'IDEM-' || v_item_id,
            'Points expired in batch ' || v_batch_id || ' for lot ' || v_lot.lot_id,
            v_now
        );

        INSERT INTO expiry_batch_items (
            item_id, batch_id, lot_id, transaction_id, points_expired, created_at
        ) VALUES (
            v_item_id,
            v_batch_id,
            v_lot.lot_id,
            v_tx_id,
            v_lot.remaining_points,
            v_now
        );

        UPDATE points_lots
        SET remaining_points = 0,
            status = 'EXPIRED',
            updated_at = v_now
        WHERE lot_id = v_lot.lot_id;

        UPDATE loyalty_accounts
        SET current_balance = v_new_balance,
            updated_at = v_now
        WHERE account_id = v_lot.account_id;
    END LOOP;

    UPDATE expiry_batches
    SET total_lots_processed = v_total_lots,
        total_points_expired = v_total_points,
        status = 'COMPLETED'
    WHERE batch_id = v_batch_id;

    PERFORM fn_log_audit_event(
        COALESCE(auth.uid()::TEXT, 'SYSTEM'),
        'EXPIRY_BATCH_EXECUTED',
        'EXPIRY_BATCH',
        v_batch_id,
        jsonb_build_object('total_lots', v_total_lots, 'total_points_expired', v_total_points)
    );

    RETURN jsonb_build_object(
        'batch_id', v_batch_id,
        'cutoff_date', p_cutoff_date,
        'total_lots_processed', v_total_lots,
        'total_points_expired', v_total_points,
        'status', 'COMPLETED'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

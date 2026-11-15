"""initial_loyaltyos_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-15 14:38:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Identity & Access: app_users
    op.create_table(
        'app_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(30), server_default='CUSTOMER', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('CUSTOMER', 'OPERATOR', 'ANALYST', 'OPERATIONS_MANAGER')", name='chk_app_user_role'),
    )
    op.create_index('idx_app_users_email', 'app_users', ['email'])

    # 2. Identity & Access: user_identity_mappings
    op.create_table(
        'user_identity_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('app_users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('provider', sa.String(30), nullable=False),
        sa.Column('provider_uid', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('email_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_sign_in_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('provider', 'provider_uid', name='uq_provider_identity'),
        sa.CheckConstraint("provider IN ('SUPABASE_PASSWORD', 'FIREBASE_GOOGLE')", name='chk_provider_name'),
    )
    op.create_index('idx_user_mappings_user', 'user_identity_mappings', ['user_id'])
    op.create_index('idx_user_mappings_email', 'user_identity_mappings', ['email'])

    # 3. Master: customers
    op.create_table(
        'customers',
        sa.Column('customer_id', sa.String(32), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('app_users.id', ondelete='RESTRICT'), unique=True, nullable=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('status', sa.String(20), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('ACTIVE', 'SUSPENDED', 'CLOSED')", name='chk_customer_status'),
    )
    op.create_index('idx_customers_email', 'customers', ['email'])

    # 4. Master: tiers
    op.create_table(
        'tiers',
        sa.Column('tier_id', sa.String(32), primary_key=True),
        sa.Column('name', sa.String(50), unique=True, nullable=False),
        sa.Column('rank', sa.Integer(), unique=True, nullable=False),
        sa.Column('min_spend', sa.Numeric(12, 2), server_default='0.00', nullable=False),
        sa.Column('earning_multiplier', sa.Numeric(4, 2), server_default='1.00', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 5. Master: loyalty_accounts
    op.create_table(
        'loyalty_accounts',
        sa.Column('account_id', sa.String(32), primary_key=True),
        sa.Column('customer_id', sa.String(32), sa.ForeignKey('customers.customer_id', ondelete='RESTRICT'), unique=True, nullable=False),
        sa.Column('tier_id', sa.String(32), sa.ForeignKey('tiers.tier_id', ondelete='RESTRICT'), server_default='TIER-BRONZE', nullable=False),
        sa.Column('current_balance', sa.Integer(), server_default='0', nullable=False),
        sa.Column('lifetime_accrued', sa.Integer(), server_default='0', nullable=False),
        sa.Column('lifetime_redeemed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('qualifying_spend', sa.Numeric(12, 2), server_default='0.00', nullable=False),
        sa.Column('status', sa.String(20), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('ACTIVE', 'FROZEN', 'CLOSED')", name='chk_account_status'),
    )
    op.create_index('idx_loyalty_accounts_customer', 'loyalty_accounts', ['customer_id'])

    # 6. Master: rules
    op.create_table(
        'rules',
        sa.Column('rule_id', sa.String(32), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('multiplier', sa.Numeric(4, 2), server_default='1.00', nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 7. Master: orders
    op.create_table(
        'orders',
        sa.Column('order_id', sa.String(32), primary_key=True),
        sa.Column('customer_id', sa.String(32), sa.ForeignKey('customers.customer_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('order_date', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('gross_amount', sa.Numeric(12, 2), server_default='0.00', nullable=False),
        sa.Column('tax_amount', sa.Numeric(12, 2), server_default='0.00', nullable=False),
        sa.Column('shipping_amount', sa.Numeric(12, 2), server_default='0.00', nullable=False),
        sa.Column('discount_amount', sa.Numeric(12, 2), server_default='0.00', nullable=False),
        sa.Column('eligible_net_spend', sa.Numeric(12, 2), server_default='0.00', nullable=False),
        sa.Column('status', sa.String(20), server_default='COMPLETED', nullable=False),
        sa.Column('accrual_status', sa.String(20), server_default='PENDING', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('COMPLETED', 'CANCELLED', 'RETURNED')", name='chk_order_status'),
        sa.CheckConstraint("accrual_status IN ('PENDING', 'ACCRUED', 'EXCLUDED')", name='chk_accrual_status'),
    )
    op.create_index('idx_orders_customer_date', 'orders', ['customer_id', 'order_date'])

    # 8. Master: order_lines
    op.create_table(
        'order_lines',
        sa.Column('order_line_id', sa.String(40), primary_key=True),
        sa.Column('order_id', sa.String(32), sa.ForeignKey('orders.order_id', ondelete='CASCADE'), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('sku', sa.String(50), nullable=False),
        sa.Column('product_name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('quantity', sa.Integer(), server_default='1', nullable=False),
        sa.Column('unit_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('item_discount', sa.Numeric(12, 2), server_default='0.00', nullable=False),
        sa.Column('net_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('is_eligible', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_order_lines_order', 'order_lines', ['order_id'])

    # 9. Returns: order_returns
    op.create_table(
        'order_returns',
        sa.Column('return_id', sa.String(32), primary_key=True),
        sa.Column('order_id', sa.String(32), sa.ForeignKey('orders.order_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('return_type', sa.String(20), nullable=False),
        sa.Column('total_refund_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('points_reversed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('status', sa.String(20), server_default='PROCESSED', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("return_type IN ('FULL', 'PARTIAL')", name='chk_return_type'),
    )
    op.create_index('idx_order_returns_order', 'order_returns', ['order_id'])

    # 10. Returns: order_return_lines
    op.create_table(
        'order_return_lines',
        sa.Column('return_line_id', sa.String(40), primary_key=True),
        sa.Column('return_id', sa.String(32), sa.ForeignKey('order_returns.return_id', ondelete='CASCADE'), nullable=False),
        sa.Column('order_line_id', sa.String(40), sa.ForeignKey('order_lines.order_line_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('quantity_returned', sa.Integer(), nullable=False),
        sa.Column('refund_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_return_lines_return', 'order_return_lines', ['return_id'])

    # 11. Ledger: points_transactions (Append-Only Journal)
    op.create_table(
        'points_transactions',
        sa.Column('transaction_id', sa.String(40), primary_key=True),
        sa.Column('account_id', sa.String(32), sa.ForeignKey('loyalty_accounts.account_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('order_id', sa.String(32), sa.ForeignKey('orders.order_id', ondelete='RESTRICT'), nullable=True),
        sa.Column('related_transaction_id', sa.String(40), sa.ForeignKey('points_transactions.transaction_id', ondelete='RESTRICT'), nullable=True),
        sa.Column('rule_id', sa.String(32), sa.ForeignKey('rules.rule_id', ondelete='RESTRICT'), nullable=True),
        sa.Column('entry_type', sa.String(30), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('running_balance', sa.Integer(), nullable=False),
        sa.Column('idempotency_key', sa.String(100), unique=True, nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "entry_type IN ('ACCRUAL', 'REDEMPTION', 'REVERSAL', 'EXPIRY', 'ADJUSTMENT_CREDIT', 'ADJUSTMENT_DEBIT')",
            name='chk_ledger_entry_type'
        ),
        sa.CheckConstraint("points <> 0", name='chk_points_nonzero'),
    )
    op.create_index('idx_pts_account_created', 'points_transactions', ['account_id', 'created_at'])
    op.create_index('idx_pts_order', 'points_transactions', ['order_id'])
    op.create_index('idx_pts_related', 'points_transactions', ['related_transaction_id'])
    op.create_index('idx_pts_idempotency', 'points_transactions', ['idempotency_key'])

    # PostgreSQL Immutability Trigger on points_transactions (Append-Only Enforcement)
    op.execute("""
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
    """)

    # 12. Ledger: points_lots (FIFO tracking & Expiration)
    op.create_table(
        'points_lots',
        sa.Column('lot_id', sa.String(40), primary_key=True),
        sa.Column('transaction_id', sa.String(40), sa.ForeignKey('points_transactions.transaction_id', ondelete='RESTRICT'), unique=True, nullable=False),
        sa.Column('account_id', sa.String(32), sa.ForeignKey('loyalty_accounts.account_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('initial_points', sa.Integer(), nullable=False),
        sa.Column('remaining_points', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), server_default='ACTIVE', nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("initial_points > 0", name='chk_lot_initial_positive'),
        sa.CheckConstraint("remaining_points >= 0 AND remaining_points <= initial_points", name='chk_lot_remaining_valid'),
        sa.CheckConstraint("status IN ('ACTIVE', 'PARTIALLY_REDEEMED', 'EXHAUSTED', 'EXPIRED', 'REVERSED')", name='chk_lot_status'),
    )
    op.create_index('idx_lots_fifo', 'points_lots', ['account_id', 'expires_at', 'created_at'])
    op.create_index('idx_lots_expiry_scan', 'points_lots', ['expires_at', 'status'])

    # 13. Rewards catalog: rewards
    op.create_table(
        'rewards',
        sa.Column('reward_id', sa.String(32), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('reward_type', sa.String(30), server_default='DISCOUNT_VOUCHER', nullable=False),
        sa.Column('points_required', sa.Integer(), nullable=False),
        sa.Column('monetary_value', sa.Numeric(8, 2), server_default='0.00', nullable=False),
        sa.Column('stock_quantity', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("points_required > 0", name='chk_reward_points_positive'),
    )

    # 14. Redemptions: redemptions
    op.create_table(
        'redemptions',
        sa.Column('redemption_id', sa.String(32), primary_key=True),
        sa.Column('account_id', sa.String(32), sa.ForeignKey('loyalty_accounts.account_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('reward_id', sa.String(32), sa.ForeignKey('rewards.reward_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('transaction_id', sa.String(40), sa.ForeignKey('points_transactions.transaction_id', ondelete='RESTRICT'), unique=True, nullable=False),
        sa.Column('points_redeemed', sa.Integer(), nullable=False),
        sa.Column('voucher_code', sa.String(64), unique=True, nullable=False),
        sa.Column('status', sa.String(20), server_default='ISSUED', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("points_redeemed > 0", name='chk_redemption_points_positive'),
        sa.CheckConstraint("status IN ('ISSUED', 'USED', 'CANCELLED', 'EXPIRED')", name='chk_redemption_status'),
    )
    op.create_index('idx_redemptions_account', 'redemptions', ['account_id'])
    op.create_index('idx_redemptions_voucher', 'redemptions', ['voucher_code'])

    # 15. Bridge: points_lot_allocations
    op.create_table(
        'points_lot_allocations',
        sa.Column('allocation_id', sa.String(40), primary_key=True),
        sa.Column('lot_id', sa.String(40), sa.ForeignKey('points_lots.lot_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('redemption_id', sa.String(32), sa.ForeignKey('redemptions.redemption_id', ondelete='RESTRICT'), nullable=True),
        sa.Column('transaction_id', sa.String(40), sa.ForeignKey('points_transactions.transaction_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('points_allocated', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("points_allocated > 0", name='chk_allocation_points_positive'),
    )
    op.create_index('idx_lot_alloc_lot', 'points_lot_allocations', ['lot_id'])
    op.create_index('idx_lot_alloc_redemption', 'points_lot_allocations', ['redemption_id'])

    # 16. Expiry: expiry_batches
    op.create_table(
        'expiry_batches',
        sa.Column('batch_id', sa.String(32), primary_key=True),
        sa.Column('cutoff_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_lots_processed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_points_expired', sa.Integer(), server_default='0', nullable=False),
        sa.Column('status', sa.String(20), server_default='IN_PROGRESS', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('IN_PROGRESS', 'COMPLETED', 'FAILED')", name='chk_expiry_batch_status'),
    )

    # 17. Expiry: expiry_batch_items
    op.create_table(
        'expiry_batch_items',
        sa.Column('item_id', sa.String(40), primary_key=True),
        sa.Column('batch_id', sa.String(32), sa.ForeignKey('expiry_batches.batch_id', ondelete='CASCADE'), nullable=False),
        sa.Column('lot_id', sa.String(40), sa.ForeignKey('points_lots.lot_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('transaction_id', sa.String(40), sa.ForeignKey('points_transactions.transaction_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('points_expired', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_expiry_items_batch', 'expiry_batch_items', ['batch_id'])

    # 18. Audit: audit_events
    op.create_table(
        'audit_events',
        sa.Column('event_id', sa.String(40), primary_key=True),
        sa.Column('actor_id', sa.String(64), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(64), nullable=False),
        sa.Column('metadata_payload', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_audit_actor', 'audit_events', ['actor_id'])
    op.create_index('idx_audit_entity', 'audit_events', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_created', 'audit_events', ['created_at'])

    # 19. Audit: rejected_operations
    op.create_table(
        'rejected_operations',
        sa.Column('operation_id', sa.String(40), primary_key=True),
        sa.Column('account_id', sa.String(32), sa.ForeignKey('loyalty_accounts.account_id', ondelete='SET NULL'), nullable=True),
        sa.Column('actor_id', sa.String(64), nullable=False),
        sa.Column('operation_type', sa.String(50), nullable=False),
        sa.Column('error_code', sa.String(50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('payload', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_rejected_error_code', 'rejected_operations', ['error_code'])

    # 20. Operational: anomaly_incidents
    op.create_table(
        'anomaly_incidents',
        sa.Column('incident_id', sa.String(40), primary_key=True),
        sa.Column('issue_type', sa.String(50), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(64), nullable=False),
        sa.Column('variance_amount', sa.Numeric(12, 2), server_default='0.00', nullable=False),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(20), server_default='DETECTED', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('DETECTED', 'INVESTIGATING', 'RESOLVED', 'DISMISSED')", name='chk_anomaly_status'),
    )
    op.create_index('idx_anomaly_status_type', 'anomaly_incidents', ['status', 'issue_type'])

    # 21. Operational: corrective_actions
    op.create_table(
        'corrective_actions',
        sa.Column('action_id', sa.String(40), primary_key=True),
        sa.Column('incident_id', sa.String(40), sa.ForeignKey('anomaly_incidents.incident_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('operator_id', sa.String(64), nullable=False),
        sa.Column('compensating_transaction_id', sa.String(40), sa.ForeignKey('points_transactions.transaction_id', ondelete='SET NULL'), nullable=True),
        sa.Column('decision', sa.String(20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("decision IN ('APPROVED', 'REJECTED')", name='chk_action_decision'),
    )
    op.create_index('idx_corrective_incident', 'corrective_actions', ['incident_id'])

    # ==============================================================================
    # Database Engine Immutability Triggers
    # ==============================================================================

    # 1. Audit Trail Immutability: audit_events (Append-Only)
    op.execute("""
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
    """)

    # 2. Lot Allocations Immutability: points_lot_allocations (Append-Only)
    op.execute("""
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
    """)

    # 3. Expiry Batch Items Immutability: expiry_batch_items (Append-Only)
    op.execute("""
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
    """)

    # 4. Points Lots Guard: Protect immutable lot columns and prevent deletion
    op.execute("""
    CREATE OR REPLACE FUNCTION tg_fn_points_lots_immutability_guard()
    RETURNS TRIGGER AS $$
    BEGIN
        IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'Immutability Violation: points_lots records cannot be deleted. Historical lot tracking must be preserved.';
        ELSIF TG_OP = 'UPDATE' THEN
            IF OLD.lot_id <> NEW.lot_id OR
               OLD.transaction_id <> NEW.transaction_id OR
               OLD.account_id <> NEW.account_id OR
               OLD.initial_points <> NEW.initial_points OR
               OLD.created_at <> NEW.created_at THEN
                RAISE EXCEPTION 'Immutability Violation: Immutable columns of points_lots (lot_id, transaction_id, account_id, initial_points, created_at) cannot be modified.';
            END IF;
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
    """)

    # ==============================================================================
    # Row Level Security (RLS) Enablement and Policies
    # ==============================================================================
    op.execute("""
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

    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'user_read_own_record' AND tablename = 'app_users') THEN
            CREATE POLICY user_read_own_record ON app_users FOR SELECT USING (auth.uid() = id);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'mapping_read_own_identities' AND tablename = 'user_identity_mappings') THEN
            CREATE POLICY mapping_read_own_identities ON user_identity_mappings FOR SELECT USING (auth.uid() = user_id);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_profile' AND tablename = 'customers') THEN
            CREATE POLICY customer_read_own_profile ON customers FOR SELECT USING (auth.uid() = user_id);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_account' AND tablename = 'loyalty_accounts') THEN
            CREATE POLICY customer_read_own_account ON loyalty_accounts FOR SELECT USING (customer_id IN (SELECT customer_id FROM customers WHERE user_id = auth.uid()));
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_transactions' AND tablename = 'points_transactions') THEN
            CREATE POLICY customer_read_own_transactions ON points_transactions FOR SELECT USING (account_id IN (
                SELECT la.account_id FROM loyalty_accounts la
                JOIN customers c ON c.customer_id = la.customer_id
                WHERE c.user_id = auth.uid()
            ));
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_lots' AND tablename = 'points_lots') THEN
            CREATE POLICY customer_read_own_lots ON points_lots FOR SELECT USING (account_id IN (
                SELECT la.account_id FROM loyalty_accounts la
                JOIN customers c ON c.customer_id = la.customer_id
                WHERE c.user_id = auth.uid()
            ));
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_redemptions' AND tablename = 'redemptions') THEN
            CREATE POLICY customer_read_own_redemptions ON redemptions FOR SELECT USING (account_id IN (
                SELECT la.account_id FROM loyalty_accounts la
                JOIN customers c ON c.customer_id = la.customer_id
                WHERE c.user_id = auth.uid()
            ));
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_orders' AND tablename = 'orders') THEN
            CREATE POLICY customer_read_own_orders ON orders FOR SELECT USING (customer_id IN (SELECT customer_id FROM customers WHERE user_id = auth.uid()));
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'customer_read_own_order_lines' AND tablename = 'order_lines') THEN
            CREATE POLICY customer_read_own_order_lines ON order_lines FOR SELECT USING (order_id IN (
                SELECT o.order_id FROM orders o
                JOIN customers c ON c.customer_id = o.customer_id
                WHERE c.user_id = auth.uid()
            ));
        END IF;
    END $$;
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS tg_points_lots_immutability_guard ON points_lots;")
    op.execute("DROP FUNCTION IF EXISTS tg_fn_points_lots_immutability_guard();")
    op.execute("DROP TRIGGER IF EXISTS tg_expiry_batch_items_immutable ON expiry_batch_items;")
    op.execute("DROP FUNCTION IF EXISTS tg_fn_expiry_batch_items_immutable();")
    op.execute("DROP TRIGGER IF EXISTS tg_points_lot_allocations_immutable ON points_lot_allocations;")
    op.execute("DROP FUNCTION IF EXISTS tg_fn_points_lot_allocations_immutable();")
    op.execute("DROP TRIGGER IF EXISTS tg_audit_events_immutable ON audit_events;")
    op.execute("DROP FUNCTION IF EXISTS tg_fn_audit_events_immutable();")
    op.execute("DROP TRIGGER IF EXISTS tg_points_transactions_immutable ON points_transactions;")
    op.execute("DROP FUNCTION IF EXISTS tg_fn_points_transactions_immutable();")
    
    op.drop_table('corrective_actions')
    op.drop_table('anomaly_incidents')
    op.drop_table('rejected_operations')
    op.drop_table('audit_events')
    op.drop_table('expiry_batch_items')
    op.drop_table('expiry_batches')
    op.drop_table('points_lot_allocations')
    op.drop_table('redemptions')
    op.drop_table('rewards')
    op.drop_table('points_lots')
    op.drop_table('points_transactions')
    op.drop_table('order_return_lines')
    op.drop_table('order_returns')
    op.drop_table('order_lines')
    op.drop_table('orders')
    op.drop_table('rules')
    op.drop_table('loyalty_accounts')
    op.drop_table('tiers')
    op.drop_table('customers')
    op.drop_table('user_identity_mappings')
    op.drop_table('app_users')

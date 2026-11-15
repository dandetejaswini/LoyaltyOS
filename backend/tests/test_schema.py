import os
from pathlib import Path
import pytest
from backend.app.core.database import Base
# Import all models to ensure metadata registration
import backend.app.models  # noqa: F401


def test_schema_model_registration():
    """Verify that all 21 core domain tables are registered on Base.metadata."""
    tables = Base.metadata.tables.keys()

    expected_tables = {
        # Identity
        "app_users",
        "user_identity_mappings",
        # Master
        "customers",
        "tiers",
        "loyalty_accounts",
        "rules",
        "orders",
        "order_lines",
        "order_returns",
        "order_return_lines",
        # Ledger
        "points_transactions",
        "points_lots",
        "rewards",
        "redemptions",
        "points_lot_allocations",
        "expiry_batches",
        "expiry_batch_items",
        # Audit & Operations
        "audit_events",
        "rejected_operations",
        "anomaly_incidents",
        "corrective_actions",
    }

    assert len(tables) >= 21
    missing = expected_tables - set(tables)
    assert not missing, f"Missing tables in SQLAlchemy metadata: {missing}"


def test_points_transactions_constraints():
    """Verify points_transactions table constraints and foreign keys."""
    table = Base.metadata.tables["points_transactions"]
    col_names = {c.name for c in table.columns}

    required_columns = {
        "transaction_id",
        "account_id",
        "order_id",
        "related_transaction_id",
        "rule_id",
        "entry_type",
        "points",
        "running_balance",
        "idempotency_key",
        "notes",
        "created_at",
    }
    assert required_columns.issubset(col_names)


def test_points_lots_constraints():
    """Verify points_lots table constraints."""
    table = Base.metadata.tables["points_lots"]
    col_names = {c.name for c in table.columns}

    required_columns = {
        "lot_id",
        "transaction_id",
        "account_id",
        "initial_points",
        "remaining_points",
        "status",
        "expires_at",
        "created_at",
        "updated_at",
    }
    assert required_columns.issubset(col_names)


def test_identity_mappings_constraints():
    """Verify user_identity_mappings table constraints."""
    table = Base.metadata.tables["user_identity_mappings"]
    col_names = {c.name for c in table.columns}

    required_columns = {
        "id",
        "user_id",
        "provider",
        "provider_uid",
        "email",
        "email_verified",
        "created_at",
        "last_sign_in_at",
    }
    assert required_columns.issubset(col_names)


def test_audit_events_constraints():
    """Verify audit_events table structure."""
    table = Base.metadata.tables["audit_events"]
    col_names = {c.name for c in table.columns}
    assert {"event_id", "actor_id", "action", "entity_type", "entity_id", "created_at"}.issubset(col_names)


def test_points_lot_allocations_constraints():
    """Verify points_lot_allocations bridge table structure."""
    table = Base.metadata.tables["points_lot_allocations"]
    col_names = {c.name for c in table.columns}
    assert {"allocation_id", "lot_id", "transaction_id", "points_allocated"}.issubset(col_names)


def test_expiry_batch_items_constraints():
    """Verify expiry_batch_items table structure."""
    table = Base.metadata.tables["expiry_batch_items"]
    col_names = {c.name for c in table.columns}
    assert {"item_id", "batch_id", "lot_id", "points_expired"}.issubset(col_names)


def test_immutability_triggers_parity_between_ddl_and_supabase():
    """
    Verifies that all 5 database engine immutability triggers are defined
    identically in both scripts/001_initial_schema.sql and Supabase core migration.
    """
    workspace_root = Path(__file__).resolve().parent.parent.parent
    sql_path = workspace_root / "scripts" / "001_initial_schema.sql"
    supabase_path = workspace_root / "supabase" / "migrations" / "20261115000001_core_schema_and_immutability.sql"

    assert sql_path.exists(), f"SQL DDL script missing at {sql_path}"
    assert supabase_path.exists(), f"Supabase migration missing at {supabase_path}"

    sql_content = sql_path.read_text(encoding="utf-8")
    supabase_content = supabase_path.read_text(encoding="utf-8")

    expected_triggers = [
        "tg_points_transactions_immutable",
        "tg_audit_events_immutable",
        "tg_points_lot_allocations_immutable",
        "tg_expiry_batch_items_immutable",
        "tg_points_lots_immutability_guard",
    ]

    for trigger in expected_triggers:
        assert trigger in sql_content, f"Trigger '{trigger}' missing in scripts/001_initial_schema.sql"
        assert trigger in supabase_content, f"Trigger '{trigger}' missing in Supabase migration"


def test_rls_policies_parity_between_ddl_and_supabase():
    """
    Verifies that Row Level Security (RLS) enablement and customer isolation policies
    are defined in both scripts/001_initial_schema.sql and Supabase RLS migration.
    """
    workspace_root = Path(__file__).resolve().parent.parent.parent
    sql_path = workspace_root / "scripts" / "001_initial_schema.sql"
    supabase_path = workspace_root / "supabase" / "migrations" / "20261115000002_rls_and_security.sql"

    sql_content = sql_path.read_text(encoding="utf-8")
    supabase_content = supabase_path.read_text(encoding="utf-8")

    expected_policies = [
        "user_read_own_record",
        "mapping_read_own_identities",
        "customer_read_own_profile",
        "customer_read_own_account",
        "customer_read_own_transactions",
        "customer_read_own_lots",
        "customer_read_own_redemptions",
        "customer_read_own_orders",
        "customer_read_own_order_lines",
    ]

    for policy in expected_policies:
        assert policy in sql_content, f"Policy '{policy}' missing in scripts/001_initial_schema.sql"

    # Verify RLS policies are enabled across all tables in Supabase migration
    assert "ENABLE ROW LEVEL SECURITY" in supabase_content
    assert "p_customers_select" in supabase_content
    assert "p_loyalty_accounts_select" in supabase_content
    assert "p_points_transactions_select" in supabase_content
    assert "p_points_lots_select" in supabase_content
    assert "p_redemptions_select" in supabase_content
    assert "p_orders_select" in supabase_content

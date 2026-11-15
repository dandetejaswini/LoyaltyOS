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

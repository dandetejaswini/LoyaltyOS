from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Ledger Journal Schemas
# ============================================================================

class PointsTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: str
    account_id: str
    order_id: Optional[str] = None
    related_transaction_id: Optional[str] = None
    rule_id: Optional[str] = None
    entry_type: str  # ACCRUAL, REDEMPTION, REVERSAL, EXPIRY, ADJUSTMENT_CREDIT, ADJUSTMENT_DEBIT
    direction: str   # CREDIT (+) or DEBIT (-)
    points: int
    running_balance: int
    idempotency_key: str
    notes: Optional[str] = None
    created_at: datetime


class TransactionHistoryPage(BaseModel):
    items: List[PointsTransactionResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class PointsLotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lot_id: str
    transaction_id: str
    account_id: str
    initial_points: int
    remaining_points: int
    status: str  # ACTIVE, PARTIALLY_REDEEMED, EXHAUSTED, EXPIRED, REVERSED
    expires_at: datetime
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Rewards & Redemption Schemas
# ============================================================================

class RewardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reward_id: str
    name: str
    reward_type: str
    points_required: int
    monetary_value: Decimal
    stock_quantity: Optional[int] = None
    is_active: bool


class RedemptionRequest(BaseModel):
    account_id: str
    reward_id: str
    idempotency_key: str = Field(..., min_length=5, max_length=100)


class PointsLotAllocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    allocation_id: str
    lot_id: str
    redemption_id: Optional[str] = None
    transaction_id: str
    points_allocated: int
    created_at: datetime


class RedemptionResponse(BaseModel):
    redemption_id: str
    account_id: str
    reward_id: str
    reward_name: str
    points_redeemed: int
    voucher_code: str
    status: str
    transaction_id: str
    new_balance: int
    allocations: List[PointsLotAllocationResponse]
    created_at: datetime
    expires_at: Optional[datetime] = None


# ============================================================================
# Points Expiry Schemas
# ============================================================================

class ExpiryExecutionRequest(BaseModel):
    cutoff_date: Optional[datetime] = None  # Defaults to UTC now if omitted
    idempotency_key: str = Field(..., min_length=5, max_length=100)


class ExpiryBatchItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: str
    batch_id: str
    lot_id: str
    transaction_id: str
    points_expired: int
    created_at: datetime


class ExpiryBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    batch_id: str
    cutoff_date: datetime
    total_lots_processed: int
    total_points_expired: int
    status: str
    items_count: int
    created_at: datetime


# ============================================================================
# Reconciliation Schemas (BR-01 Double-Entry Proof)
# ============================================================================

class ReconciliationReport(BaseModel):
    account_id: str
    customer_id: str
    stored_balance: int
    ledger_derived_balance: int
    discrepancy_amount: int
    is_reconciled: bool
    status: str  # RECONCILED or DISCREPANCY_DETECTED
    breakdown: dict  # accrual_pts, redemption_pts, reversal_pts, expiry_pts, adjustment_pts
    evaluation_time: datetime

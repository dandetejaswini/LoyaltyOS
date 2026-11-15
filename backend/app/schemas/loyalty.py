from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Customer & Account Schemas
# ============================================================================

class CustomerCreateRequest(BaseModel):
    customer_id: Optional[str] = Field(None, description="Optional custom ID (e.g. CUST-000001); generated if omitted")
    email: str = Field(..., min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: str
    user_id: Optional[str] = None
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class LoyaltyAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: str
    customer_id: str
    tier_id: str
    current_balance: int
    lifetime_accrued: int
    lifetime_redeemed: int
    qualifying_spend: Decimal
    status: str
    created_at: datetime
    updated_at: datetime


class CustomerProvisionResponse(BaseModel):
    customer: CustomerResponse
    account: LoyaltyAccountResponse
    is_new: bool = True


# ============================================================================
# Order & Accrual Schemas
# ============================================================================

class OrderLineCreate(BaseModel):
    line_number: int = Field(..., ge=1)
    sku: str = Field(..., min_length=1, max_length=50)
    product_name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=50)
    quantity: int = Field(1, ge=1)
    unit_price: Decimal = Field(..., ge=Decimal("0.00"))
    item_discount: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"))
    is_eligible: bool = Field(True, description="False for gift cards, vouchers, deposits")


class OrderLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_line_id: str
    order_id: str
    line_number: int
    sku: str
    product_name: str
    category: str
    quantity: int
    unit_price: Decimal
    item_discount: Decimal
    net_amount: Decimal
    is_eligible: bool
    created_at: datetime


class OrderCreateRequest(BaseModel):
    order_id: Optional[str] = Field(None, description="Optional external order ID (e.g. ORD-2026-000001)")
    customer_id: str
    idempotency_key: str = Field(..., min_length=5, max_length=100)
    tax_amount: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"))
    shipping_amount: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"))
    discount_amount: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"))
    lines: List[OrderLineCreate] = Field(..., min_length=1)


class OrderAccrualResponse(BaseModel):
    order_id: str
    customer_id: str
    account_id: str
    gross_amount: Decimal
    tax_amount: Decimal
    shipping_amount: Decimal
    discount_amount: Decimal
    eligible_net_spend: Decimal
    tier_id: str
    tier_multiplier: Decimal
    points_accrued: int
    new_balance: int
    transaction_id: str
    lot_id: str
    lot_expires_at: datetime
    lines: List[OrderLineResponse]
    created_at: datetime


# ============================================================================
# Order Return Schemas
# ============================================================================

class ReturnLineCreate(BaseModel):
    order_line_id: str
    quantity_returned: int = Field(..., ge=1)


class OrderReturnRequest(BaseModel):
    return_id: Optional[str] = None
    order_id: str
    idempotency_key: str = Field(..., min_length=5, max_length=100)
    reason: Optional[str] = None
    lines: List[ReturnLineCreate] = Field(..., min_length=1)


class OrderReturnResponse(BaseModel):
    return_id: str
    order_id: str
    return_type: str
    total_refund_amount: Decimal
    points_reversed: int
    new_balance: int
    status: str
    reversal_transaction_id: str
    is_balance_negative: bool
    redemptions_frozen: bool
    created_at: datetime


# ============================================================================
# Tier Schemas
# ============================================================================

class TierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tier_id: str
    name: str
    rank: int
    min_spend: Decimal
    earning_multiplier: Decimal


class TierCalculationResponse(BaseModel):
    account_id: str
    customer_id: str
    current_tier_id: str
    previous_tier_id: Optional[str] = None
    qualifying_spend_365d: Decimal
    multiplier: Decimal
    is_upgrade: bool
    is_downgrade: bool
    evaluation_time: datetime

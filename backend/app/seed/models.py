"""
Data transfer objects and entity representations for the Synthetic Data Engine.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any


@dataclass
class SyntheticCustomer:
    customer_id: str
    email: str
    first_name: str
    last_name: str
    phone: str
    status: str
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SyntheticLoyaltyAccount:
    account_id: str
    customer_id: str
    tier_id: str
    current_balance: int
    lifetime_accrued: int
    lifetime_redeemed: int
    qualifying_spend: str  # Decimal string representation
    status: str
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SyntheticOrderLine:
    order_line_id: str
    order_id: str
    line_number: int
    sku: str
    product_name: str
    category: str
    quantity: int
    unit_price: str
    item_discount: str
    net_amount: str
    is_eligible: bool
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SyntheticOrder:
    order_id: str
    customer_id: str
    order_date: str
    gross_amount: str
    tax_amount: str
    shipping_amount: str
    discount_amount: str
    eligible_net_spend: str
    status: str
    accrual_status: str
    created_at: str
    lines: List[SyntheticOrderLine] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("lines", None)
        return d


@dataclass
class SyntheticPointsTransaction:
    transaction_id: str
    account_id: str
    order_id: Optional[str]
    related_transaction_id: Optional[str]
    rule_id: Optional[str]
    entry_type: str
    points: int
    running_balance: int
    idempotency_key: str
    notes: Optional[str]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SyntheticPointsLot:
    lot_id: str
    transaction_id: str
    account_id: str
    initial_points: int
    remaining_points: int
    status: str
    expires_at: str
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SyntheticRedemption:
    redemption_id: str
    account_id: str
    reward_id: str
    transaction_id: str
    points_redeemed: int
    voucher_code: str
    status: str
    created_at: str
    expires_at: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SyntheticLotAllocation:
    allocation_id: str
    lot_id: str
    redemption_id: Optional[str]
    transaction_id: str
    points_allocated: int
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SyntheticOrderReturnLine:
    return_line_id: str
    return_id: str
    order_line_id: str
    quantity_returned: int
    refund_amount: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SyntheticOrderReturn:
    return_id: str
    order_id: str
    return_type: str
    total_refund_amount: str
    points_reversed: int
    status: str
    created_at: str
    lines: List[SyntheticOrderReturnLine] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("lines", None)
        return d


@dataclass
class SyntheticExpiryBatchItem:
    item_id: str
    batch_id: str
    lot_id: str
    transaction_id: str
    points_expired: int
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SyntheticExpiryBatch:
    batch_id: str
    cutoff_date: str
    total_lots_processed: int
    total_points_expired: int
    status: str
    created_at: str
    items: List[SyntheticExpiryBatchItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("items", None)
        return d


@dataclass
class InjectedAnomaly:
    anomaly_id: str
    category: str
    affected_entities: Dict[str, Any]
    expected_value: Any
    injected_value: Any
    rule_violated: str
    severity: str
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

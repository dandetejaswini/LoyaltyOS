import uuid
from datetime import datetime, timezone
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Boolean, DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.app.core.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(32), primary_key=True)  # CUST-000001
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id", ondelete="RESTRICT"),
        unique=True,
        nullable=True,
        index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'SUSPENDED', 'CLOSED')", name="chk_customer_status"),
    )

    user: Mapped[Optional["AppUser"]] = relationship("AppUser", back_populates="customer")
    loyalty_account: Mapped["LoyaltyAccount"] = relationship("LoyaltyAccount", back_populates="customer", uselist=False)
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="customer")


class Tier(Base):
    __tablename__ = "tiers"

    tier_id: Mapped[str] = mapped_column(String(32), primary_key=True)  # TIER-BRONZE
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    min_spend: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    earning_multiplier: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("1.00"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    loyalty_accounts: Mapped[List["LoyaltyAccount"]] = relationship("LoyaltyAccount", back_populates="tier")


class LoyaltyAccount(Base):
    __tablename__ = "loyalty_accounts"

    account_id: Mapped[str] = mapped_column(String(32), primary_key=True)  # LOY-CUST-000001
    customer_id: Mapped[str] = mapped_column(String(32), ForeignKey("customers.customer_id", ondelete="RESTRICT"), unique=True, nullable=False)
    tier_id: Mapped[str] = mapped_column(String(32), ForeignKey("tiers.tier_id", ondelete="RESTRICT"), default="TIER-BRONZE", nullable=False)
    current_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lifetime_accrued: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lifetime_redeemed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    qualifying_spend: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'FROZEN', 'CLOSED')", name="chk_account_status"),
    )

    customer: Mapped["Customer"] = relationship("Customer", back_populates="loyalty_account")
    tier: Mapped["Tier"] = relationship("Tier", back_populates="loyalty_accounts")
    transactions: Mapped[List["PointsTransaction"]] = relationship("PointsTransaction", back_populates="account")
    lots: Mapped[List["PointsLot"]] = relationship("PointsLot", back_populates="account")
    redemptions: Mapped[List["Redemption"]] = relationship("Redemption", back_populates="account")


class Rule(Base):
    __tablename__ = "rules"

    rule_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    multiplier: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("1.00"), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String(32), primary_key=True)  # ORD-2026-000001
    customer_id: Mapped[str] = mapped_column(String(32), ForeignKey("customers.customer_id", ondelete="RESTRICT"), nullable=False, index=True)
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    shipping_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    eligible_net_spend: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="COMPLETED", nullable=False)
    accrual_status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    __table_args__ = (
        CheckConstraint("status IN ('COMPLETED', 'CANCELLED', 'RETURNED')", name="chk_order_status"),
        CheckConstraint("accrual_status IN ('PENDING', 'ACCRUED', 'EXCLUDED')", name="chk_accrual_status"),
    )

    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")
    lines: Mapped[List["OrderLine"]] = relationship("OrderLine", back_populates="order", cascade="all, delete-orphan")
    returns: Mapped[List["OrderReturn"]] = relationship("OrderReturn", back_populates="order")


class OrderLine(Base):
    __tablename__ = "order_lines"

    order_line_id: Mapped[str] = mapped_column(String(40), primary_key=True)  # ORDL-2026-000001-01
    order_id: Mapped[str] = mapped_column(String(32), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False, index=True)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    sku: Mapped[str] = mapped_column(String(50), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    item_discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_eligible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="lines")


class OrderReturn(Base):
    __tablename__ = "order_returns"

    return_id: Mapped[str] = mapped_column(String(32), primary_key=True)  # RET-2026-000001
    order_id: Mapped[str] = mapped_column(String(32), ForeignKey("orders.order_id", ondelete="RESTRICT"), nullable=False, index=True)
    return_type: Mapped[str] = mapped_column(String(20), nullable=False)
    total_refund_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    points_reversed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PROCESSED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    __table_args__ = (
        CheckConstraint("return_type IN ('FULL', 'PARTIAL')", name="chk_return_type"),
    )

    order: Mapped["Order"] = relationship("Order", back_populates="returns")
    lines: Mapped[List["OrderReturnLine"]] = relationship("OrderReturnLine", back_populates="order_return", cascade="all, delete-orphan")


class OrderReturnLine(Base):
    __tablename__ = "order_return_lines"

    return_line_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    return_id: Mapped[str] = mapped_column(String(32), ForeignKey("order_returns.return_id", ondelete="CASCADE"), nullable=False, index=True)
    order_line_id: Mapped[str] = mapped_column(String(40), ForeignKey("order_lines.order_line_id", ondelete="RESTRICT"), nullable=False)
    quantity_returned: Mapped[int] = mapped_column(Integer, nullable=False)
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    order_return: Mapped["OrderReturn"] = relationship("OrderReturn", back_populates="lines")

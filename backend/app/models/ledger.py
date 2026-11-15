from datetime import datetime, timezone
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Boolean, DateTime, ForeignKey, Text, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class PointsTransaction(Base):
    """
    Core append-only financial journal.
    Strictly forbids UPDATE and DELETE in business operations and database triggers.
    """
    __tablename__ = "points_transactions"

    transaction_id: Mapped[str] = mapped_column(String(40), primary_key=True)  # PTS-2026-00000001
    account_id: Mapped[str] = mapped_column(String(32), ForeignKey("loyalty_accounts.account_id", ondelete="RESTRICT"), nullable=False, index=True)
    order_id: Mapped[Optional[str]] = mapped_column(String(32), ForeignKey("orders.order_id", ondelete="RESTRICT"), nullable=True, index=True)
    related_transaction_id: Mapped[Optional[str]] = mapped_column(String(40), ForeignKey("points_transactions.transaction_id", ondelete="RESTRICT"), nullable=True, index=True)
    rule_id: Mapped[Optional[str]] = mapped_column(String(32), ForeignKey("rules.rule_id", ondelete="RESTRICT"), nullable=True)
    entry_type: Mapped[str] = mapped_column(String(30), nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)  # Signed (+ for accrual/credit, - for redemption/reversal/expiry)
    running_balance: Mapped[int] = mapped_column(Integer, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False, index=True)

    __table_args__ = (
        CheckConstraint(
            "entry_type IN ('ACCRUAL', 'REDEMPTION', 'REVERSAL', 'EXPIRY', 'ADJUSTMENT_CREDIT', 'ADJUSTMENT_DEBIT')",
            name="chk_ledger_entry_type"
        ),
        CheckConstraint("points <> 0", name="chk_points_nonzero"),
    )

    account: Mapped["LoyaltyAccount"] = relationship("LoyaltyAccount", back_populates="transactions")
    lot: Mapped[Optional["PointsLot"]] = relationship("PointsLot", back_populates="transaction", uselist=False)
    redemption: Mapped[Optional["Redemption"]] = relationship("Redemption", back_populates="transaction", uselist=False)


class PointsLot(Base):
    """
    Individual earned points lots tracked for FIFO consumption and batch expiration.
    """
    __tablename__ = "points_lots"

    lot_id: Mapped[str] = mapped_column(String(40), primary_key=True)  # LOT-2026-00000001
    transaction_id: Mapped[str] = mapped_column(String(40), ForeignKey("points_transactions.transaction_id", ondelete="RESTRICT"), unique=True, nullable=False)
    account_id: Mapped[str] = mapped_column(String(32), ForeignKey("loyalty_accounts.account_id", ondelete="RESTRICT"), nullable=False, index=True)
    initial_points: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining_points: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    __table_args__ = (
        CheckConstraint("initial_points > 0", name="chk_lot_initial_positive"),
        CheckConstraint("remaining_points >= 0 AND remaining_points <= initial_points", name="chk_lot_remaining_valid"),
        CheckConstraint("status IN ('ACTIVE', 'PARTIALLY_REDEEMED', 'EXHAUSTED', 'EXPIRED', 'REVERSED')", name="chk_lot_status"),
    )

    transaction: Mapped["PointsTransaction"] = relationship("PointsTransaction", back_populates="lot")
    account: Mapped["LoyaltyAccount"] = relationship("LoyaltyAccount", back_populates="lots")
    allocations: Mapped[List["PointsLotAllocation"]] = relationship("PointsLotAllocation", back_populates="lot")


class Reward(Base):
    __tablename__ = "rewards"

    reward_id: Mapped[str] = mapped_column(String(32), primary_key=True)  # RWD-0001
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    reward_type: Mapped[str] = mapped_column(String(30), default="DISCOUNT_VOUCHER", nullable=False)
    points_required: Mapped[int] = mapped_column(Integer, nullable=False)
    monetary_value: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0.00"), nullable=False)
    stock_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    __table_args__ = (
        CheckConstraint("points_required > 0", name="chk_reward_points_positive"),
    )

    redemptions: Mapped[List["Redemption"]] = relationship("Redemption", back_populates="reward")


class Redemption(Base):
    __tablename__ = "redemptions"

    redemption_id: Mapped[str] = mapped_column(String(32), primary_key=True)  # RDM-2026-000001
    account_id: Mapped[str] = mapped_column(String(32), ForeignKey("loyalty_accounts.account_id", ondelete="RESTRICT"), nullable=False, index=True)
    reward_id: Mapped[str] = mapped_column(String(32), ForeignKey("rewards.reward_id", ondelete="RESTRICT"), nullable=False)
    transaction_id: Mapped[str] = mapped_column(String(40), ForeignKey("points_transactions.transaction_id", ondelete="RESTRICT"), unique=True, nullable=False)
    points_redeemed: Mapped[int] = mapped_column(Integer, nullable=False)
    voucher_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ISSUED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("points_redeemed > 0", name="chk_redemption_points_positive"),
        CheckConstraint("status IN ('ISSUED', 'USED', 'CANCELLED', 'EXPIRED')", name="chk_redemption_status"),
    )

    account: Mapped["LoyaltyAccount"] = relationship("LoyaltyAccount", back_populates="redemptions")
    reward: Mapped["Reward"] = relationship("Reward", back_populates="redemptions")
    transaction: Mapped["PointsTransaction"] = relationship("PointsTransaction", back_populates="redemption")
    allocations: Mapped[List["PointsLotAllocation"]] = relationship("PointsLotAllocation", back_populates="redemption")


class PointsLotAllocation(Base):
    """
    Many-to-Many bridge table tracking exact points consumed from each PointsLot by Redemptions.
    """
    __tablename__ = "points_lot_allocations"

    allocation_id: Mapped[str] = mapped_column(String(40), primary_key=True)  # ALL-2026-00000001
    lot_id: Mapped[str] = mapped_column(String(40), ForeignKey("points_lots.lot_id", ondelete="RESTRICT"), nullable=False, index=True)
    redemption_id: Mapped[Optional[str]] = mapped_column(String(32), ForeignKey("redemptions.redemption_id", ondelete="RESTRICT"), nullable=True, index=True)
    transaction_id: Mapped[str] = mapped_column(String(40), ForeignKey("points_transactions.transaction_id", ondelete="RESTRICT"), nullable=False)
    points_allocated: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    __table_args__ = (
        CheckConstraint("points_allocated > 0", name="chk_allocation_points_positive"),
    )

    lot: Mapped["PointsLot"] = relationship("PointsLot", back_populates="allocations")
    redemption: Mapped[Optional["Redemption"]] = relationship("Redemption", back_populates="allocations")


class ExpiryBatch(Base):
    __tablename__ = "expiry_batches"

    batch_id: Mapped[str] = mapped_column(String(32), primary_key=True)  # EXP-2026-000001
    cutoff_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_lots_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_points_expired: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="IN_PROGRESS", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    __table_args__ = (
        CheckConstraint("status IN ('IN_PROGRESS', 'COMPLETED', 'FAILED')", name="chk_expiry_batch_status"),
    )

    items: Mapped[List["ExpiryBatchItem"]] = relationship("ExpiryBatchItem", back_populates="batch", cascade="all, delete-orphan")


class ExpiryBatchItem(Base):
    __tablename__ = "expiry_batch_items"

    item_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    batch_id: Mapped[str] = mapped_column(String(32), ForeignKey("expiry_batches.batch_id", ondelete="CASCADE"), nullable=False, index=True)
    lot_id: Mapped[str] = mapped_column(String(40), ForeignKey("points_lots.lot_id", ondelete="RESTRICT"), nullable=False)
    transaction_id: Mapped[str] = mapped_column(String(40), ForeignKey("points_transactions.transaction_id", ondelete="RESTRICT"), nullable=False)
    points_expired: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    batch: Mapped["ExpiryBatch"] = relationship("ExpiryBatch", back_populates="items")

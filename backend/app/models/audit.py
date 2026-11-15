from datetime import datetime, timezone
from typing import Optional, Any
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from backend.app.core.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class AuditEvent(Base):
    """
    Immutable forensic audit log tracking all business operations and actor decisions.
    """
    __tablename__ = "audit_events"

    event_id: Mapped[str] = mapped_column(String(40), primary_key=True)  # AUD-2026-00000001
    actor_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    metadata_payload: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False, index=True)


class RejectedOperation(Base):
    """
    Captures validation and business rule rejections (e.g. overdraft attempts)
    without corrupting or polluting the points ledger.
    """
    __tablename__ = "rejected_operations"

    operation_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    account_id: Mapped[Optional[str]] = mapped_column(String(32), ForeignKey("loyalty_accounts.account_id", ondelete="SET NULL"), nullable=True, index=True)
    actor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    operation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    error_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False, index=True)


class AnomalyIncident(Base):
    """
    Tracks anomalies detected by the Loyalty Ledger Intelligence & Reconciliation Engine (LLIRE).
    """
    __tablename__ = "anomaly_incidents"

    incident_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    issue_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    variance_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    details: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="DETECTED", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("status IN ('DETECTED', 'INVESTIGATING', 'RESOLVED', 'DISMISSED')", name="chk_anomaly_status"),
    )

    corrective_actions: Mapped[list["CorrectiveAction"]] = relationship("CorrectiveAction", back_populates="incident")


class CorrectiveAction(Base):
    """
    Dual-key operator corrective action records linking incident to compensating ledger adjustments.
    """
    __tablename__ = "corrective_actions"

    action_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(40), ForeignKey("anomaly_incidents.incident_id", ondelete="RESTRICT"), nullable=False, index=True)
    operator_id: Mapped[str] = mapped_column(String(64), nullable=False)
    compensating_transaction_id: Mapped[Optional[str]] = mapped_column(String(40), ForeignKey("points_transactions.transaction_id", ondelete="SET NULL"), nullable=True)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    __table_args__ = (
        CheckConstraint("decision IN ('APPROVED', 'REJECTED')", name="chk_action_decision"),
    )

    incident: Mapped["AnomalyIncident"] = relationship("AnomalyIncident", back_populates="corrective_actions")

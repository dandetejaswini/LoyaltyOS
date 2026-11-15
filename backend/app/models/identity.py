import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.app.core.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class AppUser(Base):
    """
    Central application user entity across all authentication providers.
    Every Supabase or Firebase authenticated user resolves to exactly one AppUser.
    """
    __tablename__ = "app_users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="CUSTOMER"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    __table_args__ = (
        CheckConstraint("role IN ('CUSTOMER', 'OPERATOR', 'ANALYST', 'OPERATIONS_MANAGER')", name="chk_app_user_role"),
    )

    # Relationships
    identities: Mapped[List["UserIdentityMapping"]] = relationship("UserIdentityMapping", back_populates="user", cascade="all, delete-orphan")
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="user", uselist=False)


class UserIdentityMapping(Base):
    """
    Maps external auth provider identities (Supabase Auth UID or Firebase Google UID)
    to the internal AppUser.
    """
    __tablename__ = "user_identity_mappings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    provider_uid: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    last_sign_in_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("provider", "provider_uid", name="uq_provider_identity"),
        CheckConstraint("provider IN ('SUPABASE_PASSWORD', 'FIREBASE_GOOGLE')", name="chk_provider_name"),
    )

    # Relationships
    user: Mapped["AppUser"] = relationship("AppUser", back_populates="identities")

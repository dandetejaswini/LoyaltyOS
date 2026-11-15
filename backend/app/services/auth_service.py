import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.errors import ConflictError, BadRequestError, ForbiddenError
from backend.app.core.security import TokenPayload
from backend.app.models.identity import AppUser, UserIdentityMapping, get_utc_now
from backend.app.models.loyalty import Customer, LoyaltyAccount


class AuthService:
    """
    Handles secure user identity resolution, first-login provisioning,
    and explicit authenticated account linking.
    Prevents automatic cross-provider account merging.
    """

    @staticmethod
    def _determine_role(email: str) -> str:
        """
        Determines user role from verified email against configurable administration lists.
        Defaults strictly to 'CUSTOMER'.
        """
        email_clean = email.lower().strip()
        if email_clean in [e.lower() for e in settings.ADMIN_EMAILS]:
            return "OPERATIONS_MANAGER"
        if email_clean in [e.lower() for e in settings.OPERATOR_EMAILS]:
            return "OPERATOR"
        if email_clean in [e.lower() for e in settings.ANALYST_EMAILS]:
            return "ANALYST"
        return "CUSTOMER"

    @classmethod
    async def resolve_or_provision_user(
        cls,
        db: AsyncSession,
        payload: TokenPayload
    ) -> AppUser:
        """
        Idempotently resolves an external auth token to an internal AppUser.

        Security Rules:
        1. If (provider, provider_uid) already mapped -> Returns existing AppUser.
        2. If (provider, provider_uid) NOT mapped:
           - If email already exists in app_users under another provider:
             REJECTS automatic account linking. Requires explicit authenticated linking.
           - If email does not exist: Provisions new AppUser + Mapping.
        3. Concurrency-safe: handles race conditions via transaction savepoint / retry.
        """
        email = payload.email.lower().strip()

        # 1. Check if identity mapping already exists for (provider, provider_uid)
        mapping_stmt = (
            select(UserIdentityMapping)
            .where(
                UserIdentityMapping.provider == payload.provider,
                UserIdentityMapping.provider_uid == payload.provider_uid,
            )
        )
        result = await db.execute(mapping_stmt)
        mapping = result.scalar_one_or_none()

        if mapping:
            # Identity mapping exists: update last sign in timestamp
            mapping.last_sign_in_at = get_utc_now()
            user_stmt = (
                select(AppUser)
                .options(selectinload(AppUser.customer).selectinload(Customer.loyalty_account))
                .where(AppUser.id == mapping.user_id)
            )
            user_res = await db.execute(user_stmt)
            user = user_res.scalar_one_or_none()
            if user:
                if payload.full_name and not user.full_name:
                    user.full_name = payload.full_name
                await db.commit()
                return user

        # 2. Check if an AppUser already exists with this email address
        user_stmt = (
            select(AppUser)
            .options(selectinload(AppUser.customer).selectinload(Customer.loyalty_account))
            .where(AppUser.email == email)
        )
        user_res = await db.execute(user_stmt)
        existing_user = user_res.scalar_one_or_none()

        if existing_user:
            # SECURITY ENFORCEMENT: Automatic cross-provider account merging based solely
            # on matching email is prohibited to prevent account takeover.
            logger.warning(
                f"Account linking conflict: Provider {payload.provider} (uid: {payload.provider_uid}) "
                f"attempted automatic login for existing email '{email}'. Explicit linking required."
            )
            raise ConflictError(
                detail=f"An account with email '{email}' already exists. Automatic cross-provider account "
                       f"merging is prohibited for security. Please sign in with your primary credentials "
                       f"and link this {payload.provider} account from your profile settings."
            )

        # 3. New user provisioning with concurrency race handling
        try:
            role = cls._determine_role(email)
            user = AppUser(
                id=uuid.uuid4(),
                email=email,
                full_name=payload.full_name,
                role=role,
                is_active=True,
                created_at=get_utc_now(),
                updated_at=get_utc_now(),
            )
            db.add(user)
            await db.flush()

            # Create identity mapping
            identity_mapping = UserIdentityMapping(
                id=uuid.uuid4(),
                user_id=user.id,
                provider=payload.provider,
                provider_uid=payload.provider_uid,
                email=email,
                email_verified=payload.email_verified,
                created_at=get_utc_now(),
                last_sign_in_at=get_utc_now(),
            )
            db.add(identity_mapping)

            # 4. If CUSTOMER, provision Customer and initial LoyaltyAccount
            if role == "CUSTOMER":
                names = (payload.full_name or "Loyal Customer").split()
                first_name = names[0] if names else "Loyal"
                last_name = " ".join(names[1:]) if len(names) > 1 else "Customer"

                customer_id = f"CUST-{uuid.uuid4().hex[:8].upper()}"
                customer = Customer(
                    customer_id=customer_id,
                    user_id=user.id,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    status="ACTIVE",
                    created_at=get_utc_now(),
                    updated_at=get_utc_now(),
                )
                db.add(customer)
                await db.flush()

                account = LoyaltyAccount(
                    account_id=f"LOY-{customer_id}",
                    customer_id=customer_id,
                    tier_id="TIER-BRONZE",
                    current_balance=0,
                    lifetime_accrued=0,
                    lifetime_redeemed=0,
                    qualifying_spend=Decimal("0.00"),
                    status="ACTIVE",
                    created_at=get_utc_now(),
                    updated_at=get_utc_now(),
                )
                db.add(account)

            await db.commit()

            # Re-fetch user with relationships loaded
            refresh_stmt = (
                select(AppUser)
                .options(selectinload(AppUser.customer).selectinload(Customer.loyalty_account))
                .where(AppUser.id == user.id)
            )
            final_res = await db.execute(refresh_stmt)
            return final_res.scalar_one()

        except IntegrityError as e:
            # Concurrent provisioning race condition: rollback and query mapped user
            await db.rollback()
            logger.info(f"Concurrent provisioning detected for {email}. Fetching mapped user: {e}")
            res_retry = await db.execute(mapping_stmt)
            mapping_retry = res_retry.scalar_one_or_none()
            if mapping_retry:
                user_res = await db.execute(
                    select(AppUser)
                    .options(selectinload(AppUser.customer).selectinload(Customer.loyalty_account))
                    .where(AppUser.id == mapping_retry.user_id)
                )
                return user_res.scalar_one()
            raise ConflictError(detail="Concurrent account creation detected. Please retry request.")

    @classmethod
    async def link_provider_identity(
        cls,
        db: AsyncSession,
        current_user: AppUser,
        secondary_payload: TokenPayload,
    ) -> AppUser:
        """
        Explicitly and securely links a secondary authentication provider to an authenticated AppUser.

        Security Invariants:
        1. Both primary and secondary identities must be cryptographically verified.
        2. The secondary provider UID must NOT be already mapped to a different user.
        3. The primary user's role CANNOT be elevated through account linking.
        """
        if not current_user or not current_user.is_active:
            raise ForbiddenError(detail="Active authenticated session required to link identities.")

        # Check if this exact provider identity is already mapped anywhere
        existing_mapping_stmt = (
            select(UserIdentityMapping)
            .where(
                UserIdentityMapping.provider == secondary_payload.provider,
                UserIdentityMapping.provider_uid == secondary_payload.provider_uid,
            )
        )
        res = await db.execute(existing_mapping_stmt)
        existing_mapping = res.scalar_one_or_none()

        if existing_mapping:
            if existing_mapping.user_id == current_user.id:
                # Idempotent: already linked to this user
                return current_user
            else:
                # Mapped to a different user: reject
                raise ConflictError(
                    detail=f"This {secondary_payload.provider} identity is already linked to another LoyaltyOS account."
                )

        # SECURITY INVARIANT: Existing roles cannot be elevated through account linking.
        # current_user.role remains preserved regardless of secondary email.
        initial_role = current_user.role

        new_mapping = UserIdentityMapping(
            id=uuid.uuid4(),
            user_id=current_user.id,
            provider=secondary_payload.provider,
            provider_uid=secondary_payload.provider_uid,
            email=secondary_payload.email,
            email_verified=secondary_payload.email_verified,
            created_at=get_utc_now(),
            last_sign_in_at=get_utc_now(),
        )
        db.add(new_mapping)
        await db.commit()

        # Confirm role was not altered
        assert current_user.role == initial_role

        logger.info(
            f"Successfully linked {secondary_payload.provider} (uid: {secondary_payload.provider_uid}) "
            f"to user {current_user.id} ({current_user.email}). Role preserved: {current_user.role}"
        )

        # Refresh user with all relationships loaded
        refresh_stmt = (
            select(AppUser)
            .options(
                selectinload(AppUser.customer).selectinload(Customer.loyalty_account),
                selectinload(AppUser.identities)
            )
            .where(AppUser.id == current_user.id)
        )
        final_res = await db.execute(refresh_stmt)
        return final_res.scalar_one()

    @classmethod
    async def get_user_profile(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> Optional[AppUser]:
        stmt = (
            select(AppUser)
            .options(selectinload(AppUser.customer).selectinload(Customer.loyalty_account))
            .where(AppUser.id == user_id)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

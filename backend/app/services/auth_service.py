import uuid
from decimal import Decimal
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.security import TokenPayload
from backend.app.models.identity import AppUser, UserIdentityMapping, get_utc_now
from backend.app.models.loyalty import Customer, LoyaltyAccount


class AuthService:
    """
    Handles user identity resolution, first-login provisioning,
    and profile fetching across Supabase and Firebase authentication providers.
    """

    @staticmethod
    def _determine_role(email: str) -> str:
        """
        Determines user role from verified email against configurable administration lists.
        Defaults to 'CUSTOMER'.
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
        If the user or identity mapping does not exist, provisions them transactionally.
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
            # Identity mapping exists: update last sign in
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

        # 2. Check if AppUser exists by email
        user_stmt = (
            select(AppUser)
            .options(selectinload(AppUser.customer).selectinload(Customer.loyalty_account))
            .where(AppUser.email == email)
        )
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()

        if user:
            # User exists: link this new provider identity to the existing AppUser
            new_mapping = UserIdentityMapping(
                user_id=user.id,
                provider=payload.provider,
                provider_uid=payload.provider_uid,
                email=email,
                email_verified=payload.email_verified,
                last_sign_in_at=get_utc_now(),
            )
            db.add(new_mapping)
            if payload.full_name and not user.full_name:
                user.full_name = payload.full_name
            await db.commit()
            return user

        # 3. New user provisioning
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
            # Derive names
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

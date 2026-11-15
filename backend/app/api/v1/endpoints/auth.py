from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import decode_and_validate_token, TokenPayload
from backend.app.api.deps import get_current_user, get_token_payload
from backend.app.services.auth_service import AuthService
from backend.app.models.identity import AppUser
from backend.app.schemas.auth import (
    UserProfileResponse,
    CustomerSummary,
    LoyaltyAccountSummary,
    AuthSyncRequest,
    AuthSyncResponse,
    LinkIdentityRequest,
    LinkIdentityResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])


def _format_user_profile(user: AppUser) -> UserProfileResponse:
    customer_summary = None
    if user.customer:
        account_summary = None
        if user.customer.loyalty_account:
            la = user.customer.loyalty_account
            account_summary = LoyaltyAccountSummary(
                account_id=la.account_id,
                tier_id=la.tier_id,
                current_balance=la.current_balance,
                lifetime_accrued=la.lifetime_accrued,
                lifetime_redeemed=la.lifetime_redeemed,
                qualifying_spend=la.qualifying_spend,
                status=la.status,
            )
        customer_summary = CustomerSummary(
            customer_id=user.customer.customer_id,
            email=user.customer.email,
            first_name=user.customer.first_name,
            last_name=user.customer.last_name,
            status=user.customer.status,
            loyalty_account=account_summary,
        )

    return UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        customer=customer_summary,
        created_at=user.created_at,
    )


@router.get("/me", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def get_my_profile(
    current_user: AppUser = Depends(get_current_user),
) -> UserProfileResponse:
    """
    Returns the authenticated user's profile, role, and customer/loyalty details.
    Accepts Bearer JWT from Supabase (email/password) or Firebase (Google).
    """
    return _format_user_profile(current_user)


@router.post("/sync", response_model=AuthSyncResponse, status_code=status.HTTP_200_OK)
async def sync_user_identity(
    req: AuthSyncRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthSyncResponse:
    """
    Explicit endpoint to synchronize and provision external identity with LoyaltyOS backend.
    """
    payload = await decode_and_validate_token(req.id_token)
    user = await AuthService.resolve_or_provision_user(db, payload)
    return AuthSyncResponse(
        user=_format_user_profile(user),
        message=f"Identity successfully synchronized for provider {payload.provider}.",
    )


@router.post("/link-identity", response_model=LinkIdentityResponse, status_code=status.HTTP_200_OK)
async def link_secondary_identity(
    req: LinkIdentityRequest,
    current_user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LinkIdentityResponse:
    """
    Explicitly links a secondary authenticated provider (e.g. Google OAuth) to the
    currently authenticated user's account.
    Requires cryptographic verification of the secondary token.
    Role elevation is strictly prohibited.
    """
    secondary_payload = await decode_and_validate_token(req.link_token)
    updated_user = await AuthService.link_provider_identity(db, current_user, secondary_payload)
    return LinkIdentityResponse(
        user=_format_user_profile(updated_user),
        linked_provider=secondary_payload.provider,
        message=f"Successfully linked {secondary_payload.provider} to your LoyaltyOS account.",
    )

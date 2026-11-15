from typing import List, Optional, Callable
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.errors import UnauthorizedError, ForbiddenError
from backend.app.core.security import decode_and_validate_token, TokenPayload
from backend.app.services.auth_service import AuthService
from backend.app.models.identity import AppUser


async def get_token_header(
    authorization: Optional[str] = Header(None, description="Bearer token from Supabase or Firebase")
) -> str:
    if not authorization:
        raise UnauthorizedError(detail="Missing Authorization header. Expected 'Bearer <token>'.")
    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError(detail="Invalid Authorization header format. Expected 'Bearer <token>'.")
    return parts[1]


async def get_token_payload(
    token: str = Depends(get_token_header)
) -> TokenPayload:
    return await decode_and_validate_token(token)


async def get_current_user(
    payload: TokenPayload = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db),
) -> AppUser:
    """
    Resolves the external token payload to an internal AppUser.
    Creates or maps user on first sign-in.
    """
    user = await AuthService.resolve_or_provision_user(db, payload)
    if not user.is_active:
        raise ForbiddenError(detail="User account is deactivated. Contact system administrator.")
    return user


def require_role(allowed_roles: List[str]) -> Callable:
    """
    Enforces RBAC: verifies current user has one of the allowed roles.
    Allowed roles: 'CUSTOMER', 'OPERATOR', 'ANALYST', 'OPERATIONS_MANAGER'.
    """
    async def role_dependency(
        current_user: AppUser = Depends(get_current_user)
    ) -> AppUser:
        if current_user.role not in allowed_roles:
            raise ForbiddenError(
                detail=f"Access denied: role '{current_user.role}' lacks required permissions. Required: {', '.join(allowed_roles)}."
            )
        return current_user

    return role_dependency


# Convenience shortcuts for role enforcement
require_customer = require_role(["CUSTOMER", "OPERATIONS_MANAGER"])
require_operator = require_role(["OPERATOR", "OPERATIONS_MANAGER"])
require_analyst = require_role(["ANALYST", "OPERATIONS_MANAGER"])
require_operations_manager = require_role(["OPERATIONS_MANAGER"])

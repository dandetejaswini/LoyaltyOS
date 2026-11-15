import time
import uuid
import jwt
import pytest
from httpx import AsyncClient

from backend.app.core.config import settings
from backend.app.core.errors import UnauthorizedError, ForbiddenError
from backend.app.core.security import decode_and_validate_token, TokenPayload
from backend.app.services.auth_service import AuthService
from backend.app.models.identity import AppUser
from backend.app.api.deps import require_role


@pytest.mark.asyncio
async def test_auth_me_unauthenticated(client: AsyncClient):
    """Accessing /auth/me without an Authorization header returns 401 ProblemDetails."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"
    data = response.json()
    assert data["status"] == 401
    assert "Authorization" in data["detail"]


@pytest.mark.asyncio
async def test_auth_me_invalid_header_format(client: AsyncClient):
    """Providing a malformed Authorization header returns 401 ProblemDetails."""
    response = await client.get("/api/v1/auth/me", headers={"Authorization": "Basic invalid-credentials"})
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == 401
    assert "Bearer" in data["detail"]


@pytest.mark.asyncio
async def test_decode_empty_token():
    """Empty token raises UnauthorizedError."""
    with pytest.raises(UnauthorizedError) as exc_info:
        await decode_and_validate_token("")
    assert "Missing or empty" in exc_info.value.detail


@pytest.mark.asyncio
async def test_decode_malformed_token():
    """Malformed token string raises UnauthorizedError."""
    with pytest.raises(UnauthorizedError) as exc_info:
        await decode_and_validate_token("this-is-not-a-jwt-token")
    assert "Malformed" in exc_info.value.detail


@pytest.mark.asyncio
async def test_supabase_token_expiration():
    """Expired Supabase token raises UnauthorizedError."""
    expired_payload = {
        "sub": "supabase-user-123",
        "email": "user@example.com",
        "aud": "authenticated",
        "iss": "https://ahxjaplreytmauwpedgh.supabase.co/auth/v1",
        "exp": int(time.time()) - 300,  # Expired 5 minutes ago
    }
    secret = "test-secret-key-12345-very-secure-32bytes-min"
    token = jwt.encode(expired_payload, secret, algorithm="HS256")

    # Temporarily set test secret
    orig_secret = settings.SUPABASE_JWT_SECRET
    settings.SUPABASE_JWT_SECRET = secret
    try:
        with pytest.raises(UnauthorizedError) as exc_info:
            await decode_and_validate_token(token)
        assert "expired" in exc_info.value.detail.lower()
    finally:
        settings.SUPABASE_JWT_SECRET = orig_secret


@pytest.mark.asyncio
async def test_supabase_token_valid():
    """Valid Supabase JWT decodes to TokenPayload with SUPABASE_PASSWORD provider."""
    secret = "test-secret-key-12345-very-secure-32bytes-min"
    valid_payload = {
        "sub": "supabase-user-456",
        "email": "alice@example.com",
        "aud": "authenticated",
        "iss": "https://ahxjaplreytmauwpedgh.supabase.co/auth/v1",
        "exp": int(time.time()) + 3600,
        "user_metadata": {
            "full_name": "Alice Cooper",
        },
    }
    token = jwt.encode(valid_payload, secret, algorithm="HS256")

    orig_secret = settings.SUPABASE_JWT_SECRET
    settings.SUPABASE_JWT_SECRET = secret
    try:
        payload = await decode_and_validate_token(token)
        assert payload.provider == "SUPABASE_PASSWORD"
        assert payload.provider_uid == "supabase-user-456"
        assert payload.email == "alice@example.com"
        assert payload.full_name == "Alice Cooper"
    finally:
        settings.SUPABASE_JWT_SECRET = orig_secret


@pytest.mark.asyncio
async def test_firebase_token_validation_claims():
    """Firebase ID token claims parsing and provider detection."""
    # Create an expired Firebase-like token
    expired_fb_payload = {
        "sub": "firebase-uid-789",
        "email": "bob@gmail.com",
        "aud": settings.FIREBASE_PROJECT_ID or "loyaltyos-2a2a0",
        "iss": f"https://securetoken.google.com/{settings.FIREBASE_PROJECT_ID or 'loyaltyos-2a2a0'}",
        "exp": int(time.time()) - 600,
    }
    headers = {"kid": "mock-kid-123"}
    # Sign with dummy secret for HMAC test (header kid present)
    token = jwt.encode(expired_fb_payload, "dummy-test-secret-at-least-32-chars-long!", algorithm="HS256", headers=headers)

    with pytest.raises(UnauthorizedError) as exc_info:
        await decode_and_validate_token(token)
    assert "expired" in exc_info.value.detail.lower()


def test_auth_service_role_determination():
    """Role determination logic enforces correct assignment based on verified email."""
    assert AuthService._determine_role("admin@loyaltyos.internal") == "OPERATIONS_MANAGER"
    assert AuthService._determine_role("manager@loyaltyos.internal") == "OPERATIONS_MANAGER"
    assert AuthService._determine_role("operator@loyaltyos.internal") == "OPERATOR"
    assert AuthService._determine_role("warehouse@loyaltyos.internal") == "OPERATOR"
    assert AuthService._determine_role("analyst@loyaltyos.internal") == "ANALYST"
    assert AuthService._determine_role("shopper@example.com") == "CUSTOMER"
    assert AuthService._determine_role("random.person@gmail.com") == "CUSTOMER"


@pytest.mark.asyncio
async def test_rbac_require_role_authorized():
    """Authorized role passes RBAC check."""
    user = AppUser(
        id=uuid.uuid4(),
        email="operator@loyaltyos.internal",
        role="OPERATOR",
        is_active=True,
    )
    guard = require_role(["OPERATOR", "OPERATIONS_MANAGER"])
    result = await guard(current_user=user)
    assert result == user


@pytest.mark.asyncio
async def test_rbac_require_role_forbidden():
    """Unauthorized role is rejected with 403 ForbiddenError."""
    user = AppUser(
        id=uuid.uuid4(),
        email="customer@example.com",
        role="CUSTOMER",
        is_active=True,
    )
    guard = require_role(["OPERATOR", "OPERATIONS_MANAGER"])
    with pytest.raises(ForbiddenError) as exc_info:
        await guard(current_user=user)
    assert exc_info.value.status_code == 403
    assert "Access denied" in exc_info.value.detail

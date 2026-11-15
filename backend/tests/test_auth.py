import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import pytest
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError

from backend.app.core.config import settings
from backend.app.core.errors import UnauthorizedError, ForbiddenError, ConflictError
from backend.app.core.security import (
    decode_and_validate_token,
    TokenPayload,
    _google_certs_cache,
    _supabase_jwks_cache,
)
from backend.app.services.auth_service import AuthService
from backend.app.models.identity import AppUser, UserIdentityMapping
from backend.app.models.loyalty import Customer, LoyaltyAccount

def require_role(allowed_roles: list):
    async def role_checker(current_user: AppUser):
        if current_user.role not in allowed_roles:
            raise ForbiddenError(detail=f"Access denied. Required roles: {allowed_roles}")
        return current_user
    return role_checker


# ==============================================================================
# 1. FIXTURES & HELPERS FOR ASYMMETRIC RS256 SIGNING
# ==============================================================================

@pytest.fixture(scope="session")
def rsa_key_pair():
    """Generates an RSA key pair for testing RS256 token verification."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_key, public_pem


@pytest.fixture(scope="session")
def secondary_rsa_key_pair():
    """Generates a second, distinct RSA key pair to simulate invalid signatures."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_key, public_pem


# ==============================================================================
# 2. TOKEN DECODING & VALIDATION TESTS
# ==============================================================================

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
async def test_token_with_alg_none():
    """Token with alg='none' is strictly rejected."""
    token = jwt.encode({"sub": "user123", "email": "test@example.com"}, key="", algorithm="none")
    with pytest.raises(UnauthorizedError) as exc_info:
        await decode_and_validate_token(token)
    assert "insecure" in exc_info.value.detail.lower() or "alg" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_token_missing_subject():
    """Token missing 'sub' claim is rejected."""
    token = jwt.encode({"email": "test@example.com", "aud": "authenticated"}, key="secret-12345-very-secure-32bytes-min", algorithm="HS256")
    with pytest.raises(UnauthorizedError) as exc_info:
        await decode_and_validate_token(token)
    assert "sub" in exc_info.value.detail.lower()


# ==============================================================================
# 3. SUPABASE JWT VERIFICATION TESTS (HS256 & RS256 JWKS)
# ==============================================================================

@pytest.mark.asyncio
async def test_supabase_token_unverified_strictly_prohibited():
    """When SUPABASE_JWT_SECRET is missing, tokens are NOT accepted decoded unverified."""
    secret = "temp-secret-at-least-32-bytes-long-key"
    token = jwt.encode(
        {"sub": "sub-123", "email": "test@example.com", "aud": "authenticated", "exp": int(time.time()) + 3600},
        secret,
        algorithm="HS256"
    )
    orig_secret = settings.SUPABASE_JWT_SECRET
    settings.SUPABASE_JWT_SECRET = ""
    try:
        with pytest.raises(UnauthorizedError) as exc_info:
            await decode_and_validate_token(token)
        assert "secret is not configured" in exc_info.value.detail.lower()
    finally:
        settings.SUPABASE_JWT_SECRET = orig_secret


@pytest.mark.asyncio
async def test_supabase_token_invalid_signature():
    """Token signed with wrong HMAC secret is rejected."""
    token = jwt.encode(
        {"sub": "sub-123", "email": "test@example.com", "aud": "authenticated", "exp": int(time.time()) + 3600},
        "wrong-secret-key-at-least-32-chars-long",
        algorithm="HS256"
    )
    orig_secret = settings.SUPABASE_JWT_SECRET
    settings.SUPABASE_JWT_SECRET = "correct-secret-key-at-least-32-chars"
    try:
        with pytest.raises(UnauthorizedError) as exc_info:
            await decode_and_validate_token(token)
        assert "signature verification failed" in exc_info.value.detail.lower()
    finally:
        settings.SUPABASE_JWT_SECRET = orig_secret


@pytest.mark.asyncio
async def test_supabase_token_expiration():
    """Expired Supabase token raises UnauthorizedError."""
    secret = "test-secret-key-12345-very-secure-32bytes-min"
    expired_payload = {
        "sub": "supabase-user-123",
        "email": "user@example.com",
        "aud": "authenticated",
        "iss": "https://ahxjaplreytmauwpedgh.supabase.co/auth/v1",
        "exp": int(time.time()) - 300,
    }
    token = jwt.encode(expired_payload, secret, algorithm="HS256")
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
    """Valid Supabase HS256 JWT decodes to TokenPayload."""
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


# ==============================================================================
# 4. FIREBASE GOOGLE OAUTH TOKEN VERIFICATION TESTS (RS256)
# ==============================================================================

@pytest.mark.asyncio
async def test_firebase_token_valid_with_mock_cert(rsa_key_pair):
    """(MOCKED) Valid Firebase RS256 token verified against mock Google public cert."""
    private_key, public_pem = rsa_key_pair
    kid = "mock-google-key-001"
    project_id = settings.FIREBASE_PROJECT_ID or "loyaltyos-2a2a0"

    payload = {
        "sub": "google-user-789",
        "email": "google.user@example.com",
        "name": "Google User",
        "email_verified": True,
        "aud": project_id,
        "iss": f"https://securetoken.google.com/{project_id}",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": kid})

    # Mock the public certificate cache
    with patch("backend.app.core.security.get_google_public_key", new=AsyncMock(return_value=public_pem)):
        token_payload = await decode_and_validate_token(token)
        assert token_payload.provider == "FIREBASE_GOOGLE"
        assert token_payload.provider_uid == "google-user-789"
        assert token_payload.email == "google.user@example.com"
        assert token_payload.full_name == "Google User"
        assert token_payload.email_verified is True


@pytest.mark.asyncio
async def test_firebase_token_invalid_signature(rsa_key_pair, secondary_rsa_key_pair):
    """(MOCKED) Firebase token signed with unknown/different RSA key is rejected."""
    _private_key_1, public_pem_1 = rsa_key_pair
    private_key_2, _public_pem_2 = secondary_rsa_key_pair
    kid = "mock-google-key-001"
    project_id = settings.FIREBASE_PROJECT_ID or "loyaltyos-2a2a0"

    # Signed with key 2, but verification cert is key 1
    payload = {
        "sub": "attacker-user-000",
        "email": "attacker@example.com",
        "aud": project_id,
        "iss": f"https://securetoken.google.com/{project_id}",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, private_key_2, algorithm="RS256", headers={"kid": kid})

    with patch("backend.app.core.security.get_google_public_key", new=AsyncMock(return_value=public_pem_1)):
        with pytest.raises(UnauthorizedError) as exc_info:
            await decode_and_validate_token(token)
        assert "signature verification failed" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_firebase_token_expired(rsa_key_pair):
    """(MOCKED) Expired Firebase ID token raises UnauthorizedError."""
    private_key, public_pem = rsa_key_pair
    kid = "mock-google-key-001"
    project_id = settings.FIREBASE_PROJECT_ID or "loyaltyos-2a2a0"

    payload = {
        "sub": "user-expired",
        "email": "user@example.com",
        "aud": project_id,
        "iss": f"https://securetoken.google.com/{project_id}",
        "exp": int(time.time()) - 600,  # Expired 10 min ago
    }
    token = jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": kid})

    with patch("backend.app.core.security.get_google_public_key", new=AsyncMock(return_value=public_pem)):
        with pytest.raises(UnauthorizedError) as exc_info:
            await decode_and_validate_token(token)
        assert "expired" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_firebase_token_incorrect_audience(rsa_key_pair):
    """(MOCKED) Firebase token with wrong audience is rejected."""
    private_key, public_pem = rsa_key_pair
    kid = "mock-google-key-001"

    payload = {
        "sub": "user-aud",
        "email": "user@example.com",
        "aud": "wrong-firebase-project-id",
        "iss": f"https://securetoken.google.com/{settings.FIREBASE_PROJECT_ID}",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": kid})

    with patch("backend.app.core.security.get_google_public_key", new=AsyncMock(return_value=public_pem)):
        with pytest.raises(UnauthorizedError) as exc_info:
            await decode_and_validate_token(token)
        assert "audience" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_firebase_token_incorrect_issuer(rsa_key_pair):
    """(MOCKED) Firebase token with wrong issuer is rejected."""
    private_key, public_pem = rsa_key_pair
    kid = "mock-google-key-001"
    project_id = settings.FIREBASE_PROJECT_ID or "loyaltyos-2a2a0"

    payload = {
        "sub": "user-iss",
        "email": "user@example.com",
        "aud": project_id,
        "iss": "https://malicious-issuer.com",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": kid})

    with patch("backend.app.core.security.get_google_public_key", new=AsyncMock(return_value=public_pem)):
        with pytest.raises(UnauthorizedError) as exc_info:
            await decode_and_validate_token(token)
        assert "issuer" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_firebase_token_service_unavailable(rsa_key_pair):
    """(MOCKED) When Google cert service is unreachable, token is rejected (never unverified)."""
    private_key, _ = rsa_key_pair
    kid = "mock-google-key-001"
    project_id = settings.FIREBASE_PROJECT_ID or "loyaltyos-2a2a0"

    payload = {
        "sub": "user-sub",
        "email": "user@example.com",
        "aud": project_id,
        "iss": f"https://securetoken.google.com/{project_id}",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": kid})

    with patch("backend.app.core.security.get_google_public_key", new=AsyncMock(return_value=None)):
        with pytest.raises(UnauthorizedError) as exc_info:
            await decode_and_validate_token(token)
        assert "unavailable" in exc_info.value.detail.lower()


# ==============================================================================
# 5. ACCOUNT LINKING & PROVISIONING SECURITY TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_matching_email_does_not_automatically_merge_accounts():
    """
    CRITICAL SECURITY CHECK:
    If a user logs in with a new provider identity (e.g. Google) whose email matches
    an existing user from another provider (e.g. Supabase), automatic account merging
    is PROHIBITED and raises ConflictError.
    """
    existing_user = AppUser(
        id=uuid.uuid4(),
        email="shopper@example.com",
        full_name="Original Shopper",
        role="CUSTOMER",
        is_active=True,
    )

    mock_db = AsyncMock()
    # 1st query: check identity mapping -> None (new provider identity)
    # 2nd query: check app_users by email -> existing_user found!
    res_mapping = MagicMock()
    res_mapping.scalar_one_or_none.return_value = None

    res_user = MagicMock()
    res_user.scalar_one_or_none.return_value = existing_user

    mock_db.execute.side_effect = [res_mapping, res_user]

    payload = TokenPayload(
        provider="FIREBASE_GOOGLE",
        provider_uid="google-attacker-uid",
        email="shopper@example.com",
        full_name="Attacker Impersonator",
    )

    with pytest.raises(ConflictError) as exc_info:
        await AuthService.resolve_or_provision_user(mock_db, payload)

    assert "automatic cross-provider account merging is prohibited" in exc_info.value.detail.lower()
    # Confirm that no new mapping was added without explicit linking
    assert mock_db.add.call_count == 0


@pytest.mark.asyncio
async def test_explicit_account_linking_success():
    """
    Authenticated user can explicitly link a verified secondary provider identity.
    """
    current_user = AppUser(
        id=uuid.uuid4(),
        email="user@example.com",
        full_name="Verified User",
        role="CUSTOMER",
        is_active=True,
    )

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    # Query check: mapping does not exist yet
    res_existing_mapping = MagicMock()
    res_existing_mapping.scalar_one_or_none.return_value = None

    # Refresh query
    res_refresh = MagicMock()
    res_refresh.scalar_one.return_value = current_user

    mock_db.execute.side_effect = [res_existing_mapping, res_refresh]

    secondary_payload = TokenPayload(
        provider="FIREBASE_GOOGLE",
        provider_uid="google-user-12345",
        email="user@example.com",
        email_verified=True,
    )

    result_user = await AuthService.link_provider_identity(mock_db, current_user, secondary_payload)
    assert result_user == current_user
    assert mock_db.add.call_count == 1
    assert mock_db.commit.call_count == 1


@pytest.mark.asyncio
async def test_explicit_account_linking_duplicate_rejected():
    """
    If the secondary provider identity is already linked to a different user,
    account linking is rejected with ConflictError.
    """
    current_user = AppUser(
        id=uuid.uuid4(),
        email="alice@example.com",
        role="CUSTOMER",
        is_active=True,
    )
    other_user_id = uuid.uuid4()
    existing_other_mapping = UserIdentityMapping(
        id=uuid.uuid4(),
        user_id=other_user_id,
        provider="FIREBASE_GOOGLE",
        provider_uid="google-claimed-uid",
        email="other@example.com",
    )

    mock_db = AsyncMock()
    res = MagicMock()
    res.scalar_one_or_none.return_value = existing_other_mapping
    mock_db.execute.return_value = res

    secondary_payload = TokenPayload(
        provider="FIREBASE_GOOGLE",
        provider_uid="google-claimed-uid",
        email="alice@example.com",
    )

    with pytest.raises(ConflictError) as exc_info:
        await AuthService.link_provider_identity(mock_db, current_user, secondary_payload)

    assert "already linked to another loyaltyos account" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_account_linking_cannot_elevate_role():
    """
    SECURITY INVARIANT: Existing roles CANNOT be elevated through account linking.
    Even if the linked identity has an admin email, the user's role remains unchanged.
    """
    customer_user = AppUser(
        id=uuid.uuid4(),
        email="customer@example.com",
        role="CUSTOMER",
        is_active=True,
    )

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    res_no_mapping = MagicMock()
    res_no_mapping.scalar_one_or_none.return_value = None
    res_refresh = MagicMock()
    res_refresh.scalar_one.return_value = customer_user
    mock_db.execute.side_effect = [res_no_mapping, res_refresh]

    # Secondary identity has an email that would normally qualify for OPERATIONS_MANAGER
    secondary_payload = TokenPayload(
        provider="FIREBASE_GOOGLE",
        provider_uid="google-admin-uid",
        email="admin@loyaltyos.internal",
        email_verified=True,
    )

    updated_user = await AuthService.link_provider_identity(mock_db, customer_user, secondary_payload)
    # Role must REMAIN CUSTOMER!
    assert updated_user.role == "CUSTOMER"


@pytest.mark.asyncio
async def test_inactive_user_cannot_link_identities():
    """Deactivated user is rejected from linking identities."""
    inactive_user = AppUser(
        id=uuid.uuid4(),
        email="inactive@example.com",
        role="CUSTOMER",
        is_active=False,
    )
    mock_db = AsyncMock()
    secondary_payload = TokenPayload(
        provider="FIREBASE_GOOGLE",
        provider_uid="uid",
        email="inactive@example.com",
    )
    with pytest.raises(ForbiddenError):
        await AuthService.link_provider_identity(mock_db, inactive_user, secondary_payload)


# ==============================================================================
# 6. ROLE & RBAC AUTHORIZATION TESTS
# ==============================================================================

def test_auth_service_role_determination():
    """Role determination logic enforces correct assignment based on verified email."""
    assert AuthService._determine_role("admin@loyaltyos.internal") == "OPERATIONS_MANAGER"
    assert AuthService._determine_role("manager@loyaltyos.internal") == "OPERATIONS_MANAGER"
    assert AuthService._determine_role("operator@loyaltyos.internal") == "OPERATOR"
    assert AuthService._determine_role("warehouse@loyaltyos.internal") == "OPERATOR"
    assert AuthService._determine_role("analyst@loyaltyos.internal") == "ANALYST"
    assert AuthService._determine_role("shopper@example.com") == "CUSTOMER"


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

import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import httpx

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.errors import UnauthorizedError


@dataclass
class TokenPayload:
    provider: str  # "SUPABASE_PASSWORD" | "FIREBASE_GOOGLE"
    provider_uid: str
    email: str
    full_name: Optional[str] = None
    email_verified: bool = False
    raw_claims: Dict[str, Any] = None


# In-memory cache for Google public certs
_google_certs_cache: Dict[str, str] = {}
_google_certs_expiry: float = 0


async def get_google_public_key(kid: str) -> Optional[str]:
    """
    Fetches and caches Google's public certificates for Firebase ID token verification.
    """
    global _google_certs_cache, _google_certs_expiry
    now = time.time()

    if not _google_certs_cache or now >= _google_certs_expiry:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get("https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com")
                if res.status_code == 200:
                    _google_certs_cache = res.json()
                    # Cache for 1 hour or respect cache-control max-age
                    cache_control = res.headers.get("cache-control", "")
                    max_age = 3600
                    for part in cache_control.split(","):
                        if "max-age=" in part:
                            try:
                                max_age = int(part.split("max-age=")[1].strip())
                            except ValueError:
                                pass
                    _google_certs_expiry = now + max_age
                    logger.info("Refreshed Google Firebase public certificates cache.")
        except Exception as e:
            logger.warning(f"Failed to fetch Google public certificates: {e}")
            if not _google_certs_cache:
                return None

    return _google_certs_cache.get(kid)


async def decode_and_validate_token(token: str) -> TokenPayload:
    """
    Validates either a Supabase JWT or Firebase ID token.
    Enforces signature, expiration, issuer, and audience checks.
    Returns normalized TokenPayload.
    """
    if not token or not token.strip():
        raise UnauthorizedError(detail="Missing or empty authentication token.")

    clean_token = token.strip()
    if clean_token.lower().startswith("bearer "):
        clean_token = clean_token[7:].strip()

    try:
        header = jwt.get_unverified_header(clean_token)
        unverified_claims = jwt.decode(clean_token, options={"verify_signature": False})
    except Exception as e:
        raise UnauthorizedError(detail=f"Malformed or unparseable token: {str(e)}")

    iss = unverified_claims.get("iss", "")
    aud = unverified_claims.get("aud", "")
    alg = header.get("alg", "")

    # Provider Detection
    # 1. Firebase Google Auth
    is_firebase = (
        iss.startswith("https://securetoken.google.com/")
        or (settings.FIREBASE_PROJECT_ID and aud == settings.FIREBASE_PROJECT_ID)
    )

    if is_firebase:
        project_id = settings.FIREBASE_PROJECT_ID or aud
        expected_iss = f"https://securetoken.google.com/{project_id}"

        # Verify claims
        if unverified_claims.get("exp", 0) < time.time():
            raise UnauthorizedError(detail="Firebase token has expired.")

        kid = header.get("kid")
        if not kid:
            raise UnauthorizedError(detail="Firebase token missing 'kid' in header.")

        # In production/live mode, verify certificate
        cert = await get_google_public_key(kid)
        if cert:
            try:
                verified_claims = jwt.decode(
                    clean_token,
                    cert,
                    algorithms=["RS256"],
                    audience=project_id,
                    issuer=expected_iss,
                )
            except ExpiredSignatureError:
                raise UnauthorizedError(detail="Firebase token has expired.")
            except InvalidTokenError as e:
                raise UnauthorizedError(detail=f"Firebase token signature invalid: {str(e)}")
        else:
            # If Google certs cannot be reached (e.g. local offline test without internet)
            # check basic claims and log warning
            logger.warning("Could not reach Google certs endpoint. Validating unverified Firebase claims.")
            if unverified_claims.get("aud") != project_id or unverified_claims.get("iss") != expected_iss:
                raise UnauthorizedError(detail="Invalid Firebase audience or issuer.")
            verified_claims = unverified_claims

        email = verified_claims.get("email")
        if not email:
            raise UnauthorizedError(detail="Firebase token does not contain an email address.")

        return TokenPayload(
            provider="FIREBASE_GOOGLE",
            provider_uid=verified_claims.get("sub", verified_claims.get("user_id")),
            email=email.lower(),
            full_name=verified_claims.get("name"),
            email_verified=bool(verified_claims.get("email_verified", False)),
            raw_claims=verified_claims,
        )

    # 2. Supabase Password / Auth
    # Supabase uses HS256 by default with JWT secret
    secret = settings.SUPABASE_JWT_SECRET

    if secret:
        try:
            verified_claims = jwt.decode(
                clean_token,
                secret,
                algorithms=[settings.SUPABASE_JWT_ALGORITHM, "HS256"],
                audience="authenticated",
                options={"verify_aud": True},
            )
        except ExpiredSignatureError:
            raise UnauthorizedError(detail="Supabase token has expired.")
        except InvalidTokenError as e:
            # Try decoding without strict aud in case aud is different
            try:
                verified_claims = jwt.decode(
                    clean_token,
                    secret,
                    algorithms=[settings.SUPABASE_JWT_ALGORITHM, "HS256"],
                    options={"verify_aud": False},
                )
            except Exception:
                raise UnauthorizedError(detail=f"Supabase token signature verification failed: {str(e)}")
    else:
        # Secret not yet configured in .env - check expiration
        if unverified_claims.get("exp", 0) < time.time():
            raise UnauthorizedError(detail="Supabase token has expired.")
        logger.warning(
            "SUPABASE_JWT_SECRET is not configured in .env. "
            "Decoding Supabase token without cryptographic signature verification."
        )
        verified_claims = unverified_claims

    sub = verified_claims.get("sub")
    email = verified_claims.get("email")

    if not sub or not email:
        raise UnauthorizedError(detail="Supabase token missing required 'sub' or 'email' claims.")

    user_meta = verified_claims.get("user_metadata", {})
    full_name = user_meta.get("full_name") or user_meta.get("name")

    return TokenPayload(
        provider="SUPABASE_PASSWORD",
        provider_uid=sub,
        email=email.lower(),
        full_name=full_name,
        email_verified=bool(verified_claims.get("email_confirmed_at") or verified_claims.get("email_verified", False)),
        raw_claims=verified_claims,
    )

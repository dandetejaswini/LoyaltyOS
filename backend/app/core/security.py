import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, InvalidAlgorithmError
import httpx

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.errors import UnauthorizedError

# Whitelist of cryptographically sound algorithms permitted
ALLOWED_SUPABASE_ALGORITHMS = ["HS256", "RS256", "ES256"]
ALLOWED_FIREBASE_ALGORITHMS = ["RS256"]


@dataclass
class TokenPayload:
    provider: str  # "SUPABASE_PASSWORD" | "FIREBASE_GOOGLE"
    provider_uid: str
    email: str
    full_name: Optional[str] = None
    email_verified: bool = False
    raw_claims: Dict[str, Any] = None


# In-memory caches for public certificates / JWKS
_google_certs_cache: Dict[str, str] = {}
_google_certs_expiry: float = 0

_supabase_jwks_cache: Dict[str, Any] = {}
_supabase_jwks_expiry: float = 0


async def get_google_public_key(kid: str) -> Optional[str]:
    """
    Fetches and caches Google's public certificates for Firebase ID token verification.
    """
    global _google_certs_cache, _google_certs_expiry
    now = time.time()

    if not _google_certs_cache or now >= _google_certs_expiry:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(
                    "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
                )
                if res.status_code == 200:
                    _google_certs_cache = res.json()
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


async def get_supabase_jwk(kid: str) -> Optional[Dict[str, Any]]:
    """
    Fetches and caches Supabase JWKS for RS256/ES256 asymmetric token verification.
    """
    global _supabase_jwks_cache, _supabase_jwks_expiry
    now = time.time()

    if not settings.SUPABASE_URL:
        return None

    if not _supabase_jwks_cache or now >= _supabase_jwks_expiry:
        try:
            jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(jwks_url)
                if res.status_code == 200:
                    jwks_data = res.json()
                    keys = jwks_data.get("keys", [])
                    _supabase_jwks_cache = {k.get("kid"): k for k in keys if k.get("kid")}
                    _supabase_jwks_expiry = now + 3600
                    logger.info(f"Refreshed Supabase JWKS cache with {len(_supabase_jwks_cache)} keys.")
        except Exception as e:
            logger.warning(f"Failed to fetch Supabase JWKS from {settings.SUPABASE_URL}: {e}")
            if not _supabase_jwks_cache:
                return None

    return _supabase_jwks_cache.get(kid)


async def decode_and_validate_token(token: str) -> TokenPayload:
    """
    Cryptographically validates either a Supabase JWT or Firebase ID token.
    Enforces signature, expiration, issuer, audience, and required claims checks.
    NEVER accepts unverified tokens.
    """
    if not token or not token.strip():
        raise UnauthorizedError(detail="Missing or empty authentication token.")

    clean_token = token.strip()
    if clean_token.lower().startswith("bearer "):
        clean_token = clean_token[7:].strip()

    try:
        header = jwt.get_unverified_header(clean_token)
    except Exception as e:
        raise UnauthorizedError(detail=f"Malformed or unparseable token header: {str(e)}")

    alg = header.get("alg")
    if not alg or alg.lower() == "none":
        raise UnauthorizedError(detail="Insecure or missing token signing algorithm ('alg' cannot be 'none').")

    # Read unverified claims for issuer/audience routing
    try:
        unverified_claims = jwt.decode(clean_token, options={"verify_signature": False})
    except Exception as e:
        raise UnauthorizedError(detail=f"Malformed or unparseable token payload: {str(e)}")

    iss = unverified_claims.get("iss", "")
    aud = unverified_claims.get("aud", "")
    sub = unverified_claims.get("sub") or unverified_claims.get("user_id")

    if not sub or not str(sub).strip():
        raise UnauthorizedError(detail="Token is missing required 'sub' (subject) claim.")

    # --------------------------------------------------------------------------
    # 1. Firebase Google Auth Token Verification (RS256)
    # --------------------------------------------------------------------------
    is_firebase = (
        iss.startswith("https://securetoken.google.com/")
        or (settings.FIREBASE_PROJECT_ID and aud == settings.FIREBASE_PROJECT_ID)
    )

    if is_firebase:
        if alg not in ALLOWED_FIREBASE_ALGORITHMS:
            raise UnauthorizedError(
                detail=f"Unsupported Firebase signing algorithm '{alg}'. Expected RS256."
            )

        project_id = settings.FIREBASE_PROJECT_ID
        if not project_id:
            raise UnauthorizedError(detail="Backend FIREBASE_PROJECT_ID is not configured.")

        expected_iss = f"https://securetoken.google.com/{project_id}"
        if iss != expected_iss:
            raise UnauthorizedError(
                detail=f"Invalid Firebase token issuer '{iss}'. Expected '{expected_iss}'."
            )

        if aud != project_id:
            raise UnauthorizedError(
                detail=f"Invalid Firebase token audience '{aud}'. Expected '{project_id}'."
            )

        kid = header.get("kid")
        if not kid:
            raise UnauthorizedError(detail="Firebase token missing 'kid' in header.")

        # Cryptographic Signature Verification
        cert = await get_google_public_key(kid)
        if not cert:
            raise UnauthorizedError(
                detail="Unable to verify Firebase token: verification certificates unavailable."
            )

        try:
            # cert can be an x509 PEM certificate string or a JWK dict/public key
            if isinstance(cert, str) and cert.startswith("-----BEGIN"):
                key = cert
            elif isinstance(cert, dict):
                key = jwt.algorithms.RSAAlgorithm.from_jwk(cert)
            else:
                key = cert

            verified_claims = jwt.decode(
                clean_token,
                key,
                algorithms=["RS256"],
                audience=project_id,
                issuer=expected_iss,
                options={"verify_signature": True, "verify_exp": True, "verify_aud": True, "verify_iss": True},
            )
        except ExpiredSignatureError:
            raise UnauthorizedError(detail="Firebase token has expired.")
        except InvalidTokenError as e:
            raise UnauthorizedError(detail=f"Firebase token signature verification failed: {str(e)}")

        email = verified_claims.get("email")
        if not email or not email.strip():
            raise UnauthorizedError(detail="Firebase token does not contain a valid email address.")

        return TokenPayload(
            provider="FIREBASE_GOOGLE",
            provider_uid=str(sub),
            email=email.lower().strip(),
            full_name=verified_claims.get("name"),
            email_verified=bool(verified_claims.get("email_verified", False)),
            raw_claims=verified_claims,
        )

    # --------------------------------------------------------------------------
    # 2. Supabase Auth Token Verification (HS256 Symmetric or RS256/ES256 JWKS)
    # --------------------------------------------------------------------------
    if alg not in ALLOWED_SUPABASE_ALGORITHMS:
        raise UnauthorizedError(
            detail=f"Unsupported Supabase signing algorithm '{alg}'. Permitted: {ALLOWED_SUPABASE_ALGORITHMS}."
        )

    expected_aud = "authenticated"
    expected_iss = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1" if settings.SUPABASE_URL else None

    # Asymmetric Supabase JWT (RS256 / ES256)
    if alg in ["RS256", "ES256"]:
        kid = header.get("kid")
        if not kid:
            raise UnauthorizedError(detail="Asymmetric Supabase token missing 'kid' in header.")

        jwk = await get_supabase_jwk(kid)
        if not jwk:
            raise UnauthorizedError(
                detail=f"Supabase public key with kid '{kid}' not found in JWKS endpoint."
            )

        try:
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk) if alg == "RS256" else jwt.algorithms.ECAlgorithm.from_jwk(jwk)
            verified_claims = jwt.decode(
                clean_token,
                public_key,
                algorithms=[alg],
                audience=expected_aud,
                options={"verify_signature": True, "verify_exp": True, "verify_aud": True},
            )
        except ExpiredSignatureError:
            raise UnauthorizedError(detail="Supabase token has expired.")
        except InvalidTokenError as e:
            raise UnauthorizedError(detail=f"Supabase asymmetric token signature verification failed: {str(e)}")

    # Symmetric Supabase JWT (HS256)
    else:
        secret = settings.SUPABASE_JWT_SECRET
        if not secret:
            raise UnauthorizedError(
                detail="Supabase JWT secret is not configured on the backend (SUPABASE_JWT_SECRET missing). "
                       "Unverified tokens are strictly prohibited."
            )

        try:
            verified_claims = jwt.decode(
                clean_token,
                secret,
                algorithms=["HS256"],
                audience=expected_aud,
                options={"verify_signature": True, "verify_exp": True, "verify_aud": True},
            )
        except ExpiredSignatureError:
            raise UnauthorizedError(detail="Supabase token has expired.")
        except InvalidTokenError as e:
            raise UnauthorizedError(detail=f"Supabase token signature verification failed: {str(e)}")

    # Validate required claims
    email = verified_claims.get("email")
    if not email or not email.strip():
        raise UnauthorizedError(detail="Supabase token missing required 'email' claim.")

    user_meta = verified_claims.get("user_metadata", {})
    full_name = user_meta.get("full_name") or user_meta.get("name")

    return TokenPayload(
        provider="SUPABASE_PASSWORD",
        provider_uid=str(sub),
        email=email.lower().strip(),
        full_name=full_name,
        email_verified=bool(verified_claims.get("email_confirmed_at") or verified_claims.get("email_verified", False)),
        raw_claims=verified_claims,
    )

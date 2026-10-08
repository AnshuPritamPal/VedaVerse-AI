"""JWT creation, validation, and authenticated-user dependency."""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.config import settings
from app.services.auth_service import UserStoreUnavailable, auth_service


bearer_scheme = HTTPBearer(auto_error=False)
SUPPORTED_HMAC_ALGORITHMS = {"HS256", "HS384", "HS512"}


class TokenConfigurationError(RuntimeError):
    """Raised when required signing settings are missing or unsafe."""


class AccessTokenExpired(Exception):
    """Raised when a JWT has expired."""


class AccessTokenInvalid(Exception):
    """Raised when a JWT cannot be decoded or has no valid subject."""


def _validate_jwt_settings() -> None:
    if not settings.jwt_secret_key:
        raise TokenConfigurationError("JWT_SECRET_KEY is not configured.")
    if len(settings.jwt_secret_key) < 32:
        raise TokenConfigurationError("JWT_SECRET_KEY must contain at least 32 characters.")
    if settings.jwt_algorithm not in SUPPORTED_HMAC_ALGORITHMS:
        raise TokenConfigurationError("JWT_ALGORITHM must be HS256, HS384, or HS512.")
    if settings.access_token_expire_minutes <= 0:
        raise TokenConfigurationError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive.")


def create_access_token(user_id: str) -> str:
    """Create a signed bearer token with configured expiration."""
    _validate_jwt_settings()
    now = datetime.now(timezone.utc)
    claims = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(
        claims,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Validate signature, algorithm, expiry, and subject claim."""
    _validate_jwt_settings()
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "iat", "sub"]},
        )
    except ExpiredSignatureError as exc:
        raise AccessTokenExpired from exc
    except InvalidTokenError as exc:
        raise AccessTokenInvalid from exc

    if not isinstance(claims.get("sub"), str) or not claims["sub"]:
        raise AccessTokenInvalid
    return claims


def _unauthorized(detail: str = "Invalid or expired access token.") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    """Require a valid bearer token and resolve its subject from MongoDB."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("Bearer token required.")

    try:
        claims = decode_access_token(credentials.credentials)
    except (AccessTokenExpired, AccessTokenInvalid) as exc:
        raise _unauthorized() from exc
    except TokenConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Token authentication is not configured.",
        ) from exc

    try:
        user = await auth_service.get_user_by_id(claims["sub"])
    except UserStoreUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User lookup is unavailable.",
        ) from exc

    if user is None:
        raise _unauthorized("User for this access token was not found.")
    return user

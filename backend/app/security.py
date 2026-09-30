"""Authentication, JWT rotation, bcrypt hashing, AES-256 field encryption, and RBAC."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import StrEnum
from functools import wraps
import hashlib
import hmac
from typing import Any, Callable
import uuid

import bcrypt
from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

BCRYPT_ROUNDS = 12
ERR_INVALID_CREDENTIALS = "Invalid or expired authentication token"
ERR_FORBIDDEN_ROLE = "Insufficient role privileges for this operation"


class RoleEnum(StrEnum):
    """Role enumeration eliminating magic role strings across the codebase."""

    ADMIN = "ADMIN"
    PLANNER = "PLANNER"
    VIEWER = "VIEWER"
    PARTNER = "PARTNER"


class TokenTypeEnum(StrEnum):
    """JWT token type discriminator."""

    ACCESS = "access"
    REFRESH = "refresh"


class AuthenticatedUser(dict[str, Any]):
    """Dictionary-compatible principal object supporting attribute access (user.role, user.org_id)."""

    @property
    def sub(self) -> str:
        return str(self.get("sub", ""))

    @property
    def role(self) -> str:
        return str(self.get("role", ""))

    @property
    def org_id(self) -> Any:
        return self.get("org_id")

    @property
    def region(self) -> str:
        return str(self.get("region", "SOUTH"))


bearer_scheme = HTTPBearer(auto_error=False)
_revoked_jti: set[str] = set()


def _get_cipher() -> Fernet:
    """Initialize AES-256 Fernet cipher from environment key."""
    return Fernet(settings.fernet_key.encode("utf-8"))


def encrypt_sensitive(plaintext: str) -> str:
    """Encrypt sensitive string data at rest using Fernet."""
    return _get_cipher().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_sensitive(ciphertext: str) -> str:
    """Decrypt sensitive ciphertext string from storage."""
    return _get_cipher().decrypt(ciphertext.encode("utf-8")).decode("utf-8")


def hash_password(plain_password: str) -> str:
    """Hash a user password using bcrypt with cost factor 12."""
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def _build_jwt(
    subject: str,
    role: str,
    org_id: str | int | None,
    token_type: TokenTypeEnum,
    delta: timedelta,
    region: str = "SOUTH",
) -> str:
    """Create a signed JWT with expiration and unique JTI."""
    now = datetime.now(timezone.utc)
    claims: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "org_id": org_id,
        "region": region,
        "type": token_type.value,
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + delta).timestamp()),
    }
    return jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(
    subject: str,
    role: str,
    org_id: str | int | None = None,
    region: str = "SOUTH",
) -> str:
    """Issue a 15-minute access JWT."""
    delta = timedelta(minutes=settings.access_token_expire_minutes)
    return _build_jwt(subject, role, org_id, TokenTypeEnum.ACCESS, delta, region=region)


def create_refresh_token(
    subject: str,
    role: str,
    org_id: str | int | None = None,
    region: str = "SOUTH",
) -> str:
    """Issue a 7-day refresh JWT supporting rotation."""
    delta = timedelta(days=settings.refresh_token_expire_days)
    return _build_jwt(subject, role, org_id, TokenTypeEnum.REFRESH, delta, region=region)


def decode_token(token: str, expected_type: TokenTypeEnum = TokenTypeEnum.ACCESS) -> AuthenticatedUser:
    """Decode and validate a JWT, enforcing token type and revocation check."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ERR_INVALID_CREDENTIALS) from exc

    if payload.get("type") != expected_type.value or payload.get("jti") in _revoked_jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ERR_INVALID_CREDENTIALS)
    return AuthenticatedUser(payload)


def rotate_refresh_token(refresh_token: str) -> tuple[str, str]:
    """Invalidate a used refresh token and issue a fresh access + refresh token pair."""
    payload = decode_token(refresh_token, expected_type=TokenTypeEnum.REFRESH)
    _revoked_jti.add(str(payload.get("jti")))
    sub = str(payload["sub"])
    role = str(payload["role"])
    org_id = payload.get("org_id")
    region = str(payload.get("region", "SOUTH"))
    return (
        create_access_token(sub, role, org_id, region=region),
        create_refresh_token(sub, role, org_id, region=region),
    )


def get_current_principal(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    """Extract and validate the current authenticated principal from the Authorization header."""
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ERR_INVALID_CREDENTIALS)
    return decode_token(creds.credentials, expected_type=TokenTypeEnum.ACCESS)


get_current_user = get_current_principal


def require_role(*allowed_roles: str) -> Callable[..., Any]:
    """Enforce role membership as either a route decorator or FastAPI dependency."""
    allowed_set = {str(r) for r in allowed_roles}

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            principal: dict[str, Any] | None = kwargs.get("principal") or kwargs.get("user")
            if principal is None or principal.get("role") not in allowed_set:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=ERR_FORBIDDEN_ROLE)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_partner_context(user: AuthenticatedUser = Depends(get_current_user)) -> dict[str, Any]:
    """Return {'org_id': ..., 'region': ...} if user.role == PARTNER, else raise HTTPException(403)."""
    if user.role != "PARTNER" or user.org_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Partner role with valid org_id scope is required",
        )
    raw_org = user.org_id
    org_id_int = int(raw_org) if str(raw_org).isdigit() else raw_org
    return {
        "org_id": org_id_int,
        "region": user.region,
        "actor": user.sub,
    }


def sign_payload(payload: str, secret: str) -> str:
    """Compute HMAC-SHA256 hex digest over payload using secret."""
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_signature(payload: str, signature: str, secret: str) -> bool:
    """Constant-time HMAC-SHA256 signature verification using hmac.compare_digest."""
    expected = sign_payload(payload, secret)
    return hmac.compare_digest(expected, signature)

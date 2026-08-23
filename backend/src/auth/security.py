"""
JWT token creation / verification + bcrypt password hashing.

All cryptographic concerns live here so the rest of the codebase never
touches raw tokens or plain-text passwords directly.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import bcrypt
from jose import jwt

from src.infrastructure.config import config

# ---------------------------------------------------------------------------
# Password hashing — direct bcrypt (bcrypt 5.x)
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Hash a plain-text password using bcrypt and return the hash as a string."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------
_SECRET    = config.env.JWT_SECRET
_ALGORITHM = config.env.JWT_ALGORITHM
_ACCESS_MINUTES  = config.env.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
_REFRESH_DAYS    = config.env.JWT_REFRESH_TOKEN_EXPIRE_DAYS


def create_access_token(data: Dict[str, Any]) -> str:
    """
    Create a short-lived (30 min) JWT access token.

    Payload keys:
        sub  – user email (subject)
        role – user role
        type – "access"
    """
    payload = data.copy()
    payload.update({
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=_ACCESS_MINUTES),
    })
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a long-lived (7 day) JWT refresh token.

    Payload keys:
        sub  – user email
        type – "refresh"
    """
    payload = {"sub": data["sub"], "type": "refresh"}
    payload["exp"] = datetime.now(timezone.utc) + timedelta(days=_REFRESH_DAYS)
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT token.

    Raises:
        JWTError – if the token is invalid or expired.
    """
    return jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])

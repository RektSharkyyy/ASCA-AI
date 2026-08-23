"""
FastAPI dependency injection helpers for JWT authentication.

Usage:
    @router.get("/protected")
    async def protected_route(user = Depends(get_current_user)):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.security import decode_token
from src.infrastructure.db import get_db_session
from src.infrastructure.logging import logger
from src.infrastructure.models import UserModel

_bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> UserModel:
    """
    Validates the Bearer JWT and returns the active UserModel.

    Raises HTTP 401 on any token or DB failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        email: str | None = payload.get("sub")
        token_type: str   = payload.get("type", "")
        if not email or token_type != "access":
            raise credentials_exception
    except JWTError as exc:
        logger.warning(f"[auth] JWT decode error: {exc}")
        raise credentials_exception

    result = await db.execute(select(UserModel).where(UserModel.email == email))
    user: UserModel | None = result.scalars().first()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


async def require_admin(user: UserModel = Depends(get_current_user)) -> UserModel:
    """Dependency that requires the user to have the 'admin' role."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires administrator privileges.",
        )
    return user

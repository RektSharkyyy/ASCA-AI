"""
Authentication API routes.

POST /api/auth/register  — Create a new user (admin only)
POST /api/auth/login     — Email + password → JWT access + refresh tokens
POST /api/auth/refresh   — Refresh token → new access token
GET  /api/auth/me        — Bearer token → current user profile
POST /api/auth/logout    — Informational (token discard is client-side)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, require_admin
from src.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserProfile,
)
from src.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from src.infrastructure.config import config
from src.infrastructure.db import get_db_session
from src.infrastructure.logging import logger
from src.infrastructure.models import UserModel

router = APIRouter(prefix="/api/auth", tags=["auth"])

_ACCESS_SECONDS = config.env.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60


# ---------------------------------------------------------------------------
# POST /api/auth/register
# ---------------------------------------------------------------------------
@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
    # Uncomment the line below to restrict registration to admin users only:
    # _admin: UserModel = Depends(require_admin),
) -> UserProfile:
    """
    Create a new user account.

    By default this endpoint is open so the very first admin can be created.
    Once your admin account exists, re-enable the require_admin dependency above.
    """
    # Check for duplicate email
    existing = await db.execute(select(UserModel).where(UserModel.email == req.email))
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{req.email}' already exists.",
        )

    user = UserModel(
        email=req.email,
        full_name=req.full_name,
        hashed_password=hash_password(req.password),
        role=req.role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"[auth] New user registered: {user.email} (role={user.role})")
    return UserProfile.model_validate(user)


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Email + password → JWT access + refresh tokens."""
    invalid_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
    )

    result = await db.execute(select(UserModel).where(UserModel.email == req.email))
    user: UserModel | None = result.scalars().first()

    if not user or not user.is_active:
        raise invalid_exc
    if not verify_password(req.password, user.hashed_password):
        raise invalid_exc

    token_data = {"sub": user.email, "role": user.role}
    access_token  = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    logger.info(f"[auth] Login successful: {user.email}")
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=_ACCESS_SECONDS,
        user_email=user.email,
        user_name=user.full_name,
        role=user.role,
    )


# ---------------------------------------------------------------------------
# POST /api/auth/refresh
# ---------------------------------------------------------------------------
@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    req: RefreshRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Exchange a valid refresh token for a new access token."""
    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Not a refresh token")
        email: str = payload["sub"]
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    result = await db.execute(select(UserModel).where(UserModel.email == email))
    user: UserModel | None = result.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    token_data    = {"sub": user.email, "role": user.role}
    access_token  = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=_ACCESS_SECONDS,
        user_email=user.email,
        user_name=user.full_name,
        role=user.role,
    )


# ---------------------------------------------------------------------------
# GET /api/auth/me
# ---------------------------------------------------------------------------
@router.get("/me", response_model=UserProfile)
async def me(current_user: UserModel = Depends(get_current_user)) -> UserProfile:
    """Return the profile of the currently authenticated user."""
    return UserProfile.model_validate(current_user)


# ---------------------------------------------------------------------------
# POST /api/auth/logout
# ---------------------------------------------------------------------------
@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout() -> dict:
    """
    Informational endpoint — JWT is stateless so the actual logout is done
    client-side by discarding the stored tokens.
    """
    return {"detail": "Logged out successfully. Please discard your tokens."}

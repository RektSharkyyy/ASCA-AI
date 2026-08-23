"""
Pydantic request / response schemas for the auth API routes.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email:     str = Field(..., description="Unique user email address")
    full_name: str = Field(..., min_length=2, description="User's full name")
    password:  str = Field(..., min_length=8, description="Password (min 8 chars)")
    role:      Literal["viewer", "admin"] = "viewer"


class LoginRequest(BaseModel):
    email:    str = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid refresh token")


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    int  # seconds (access token)
    user_email:    str
    user_name:     str
    role:          str


class UserProfile(BaseModel):
    id:         int
    email:      str
    full_name:  str
    role:       str
    is_active:  bool
    created_at: datetime

    class Config:
        from_attributes = True

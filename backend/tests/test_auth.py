import pytest
import httpx
from src.auth.security import hash_password, verify_password, create_access_token, decode_token
from src.infrastructure.models import UserModel

def test_password_hashing_and_verification():
    """Test bcrypt hashing and verification accuracy."""
    raw_password = "SecretFarmerPassword@2026"
    hashed = hash_password(raw_password)
    
    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False

def test_jwt_token_generation_and_decoding():
    """Test JWT creation and payload decoding."""
    payload = {"sub": "trader@dambulla.lk", "role": "trader", "id": 42}
    token = create_access_token(data=payload)
    
    assert isinstance(token, str)
    assert len(token) > 20
    
    decoded = decode_token(token)
    assert decoded["sub"] == "trader@dambulla.lk"
    assert decoded["role"] == "trader"
    assert decoded["id"] == 42
    assert "exp" in decoded

@pytest.mark.asyncio
async def test_login_api_success(async_client: httpx.AsyncClient, test_admin_user: UserModel):
    """Test POST /api/auth/login with valid credentials."""
    response = await async_client.post(
        "/api/auth/login",
        json={"email": "admin@asca.ai", "password": "Admin@123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user_email"] == "admin@asca.ai"
    assert data["role"] == "admin"

@pytest.mark.asyncio
async def test_login_api_invalid_password(async_client: httpx.AsyncClient, test_admin_user: UserModel):
    """Test POST /api/auth/login rejects invalid credentials."""
    response = await async_client.post(
        "/api/auth/login",
        json={"email": "admin@asca.ai", "password": "WrongPassword!"}
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_api_nonexistent_user(async_client: httpx.AsyncClient):
    """Test POST /api/auth/login rejects non-existent user."""
    response = await async_client.post(
        "/api/auth/login",
        json={"email": "unknown_farmer@nowhere.com", "password": "AnyPassword"}
    )
    assert response.status_code == 401

import asyncio
import pytest
import pytest_asyncio
import httpx
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.api.main import app
from src.infrastructure.db import Base, get_db_session
from src.infrastructure.models import UserModel
from src.auth.security import hash_password, create_access_token

# Use in-memory SQLite for test isolation
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        admin_user = UserModel(
            email="admin@asca.ai",
            full_name="ASCA Administrator",
            hashed_password=hash_password("Admin@123"),
            role="admin",
            is_active=True
        )
        session.add(admin_user)
        await session.commit()
        
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture
async def test_admin_user(db_session: AsyncSession) -> UserModel:
    from sqlalchemy import select
    res = await db_session.execute(select(UserModel).where(UserModel.email == "admin@asca.ai"))
    return res.scalar_one()

@pytest.fixture
def auth_token() -> str:
    return create_access_token(data={"sub": "admin@asca.ai", "role": "admin", "id": 1})

@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    return {"Authorization": f"Bearer {auth_token}"}

@pytest_asyncio.fixture
async def async_client(test_engine) -> AsyncGenerator[httpx.AsyncClient, None]:
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    
    async def override_get_db():
        async with async_session() as session:
            yield session
            
    app.dependency_overrides[get_db_session] = override_get_db
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield client
        
    app.dependency_overrides.clear()

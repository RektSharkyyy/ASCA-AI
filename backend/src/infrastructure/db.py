import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.infrastructure.config import config
from src.infrastructure.logging import logger

# Ensure data directory exists
db_url = config.env.DATABASE_URL

if "sqlite" in db_url:
    db_path = db_url.split("///")[-1]
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def init_db():
    logger.info("Initializing Database Tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database Tables Initialized successfully.")
        
        # Auto-seed default admin user if not present
        from src.infrastructure.models import UserModel
        from src.auth.security import hash_password
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserModel).where(UserModel.email == "admin@asca.ai"))
            user = result.scalar_one_or_none()
            if not user:
                admin_user = UserModel(
                    email="admin@asca.ai",
                    full_name="ASCA System Administrator",
                    hashed_password=hash_password("Admin@123"),
                    role="admin",
                    is_active=True,
                )
                session.add(admin_user)
                await session.commit()
                logger.info("Default admin user created: admin@asca.ai / Admin@123")
    except Exception as e:
        logger.error(f"Database init error: {e}")


async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


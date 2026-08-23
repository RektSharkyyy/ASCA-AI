from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.infrastructure.db import Base


class UserModel(Base):
    """Application user table — stores credentials and roles."""
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email           = Column(String(255), unique=True, index=True, nullable=False)
    full_name       = Column(String(150), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role            = Column(String(50), default="viewer", nullable=False)  # viewer | admin
    is_active       = Column(Boolean, default=True, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)

class MarketDataModel(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    center_id = Column(String(50), index=True) # e.g. DAMBULLA, THAMBUTHTHEGAMA
    crop_name = Column(String(100), index=True)
    wholesale_price_lkr = Column(Float, nullable=False)
    supply_volume_tons = Column(Float, nullable=False)
    predicted_price_lkr = Column(Float, nullable=True)
    is_surplus_anomaly = Column(Boolean, default=False)

class B2BBuyerModel(Base):
    __tablename__ = "b2b_buyers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    buyer_code = Column(String(50), unique=True, index=True)
    company_name = Column(String(150), nullable=False)
    buyer_type = Column(String(100)) # e.g., Sauce Factory, Canning, Juice Plant
    preferred_crops = Column(Text, nullable=False) # JSON or Comma-separated list
    daily_capacity_tons = Column(Float, nullable=False)
    location = Column(String(150), nullable=False)
    max_distance_km = Column(Float, default=150.0)
    min_shelf_life_days = Column(Integer, default=2)
    contact_phone = Column(String(50), nullable=True)
    telegram_chat_id = Column(String(50), nullable=True)

class SurplusMatchModel(Base):
    __tablename__ = "surplus_matches"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    center_id = Column(String(50), nullable=False)
    crop_name = Column(String(100), nullable=False)
    surplus_volume_tons = Column(Float, nullable=False)
    buyer_code = Column(String(50), ForeignKey("b2b_buyers.buyer_code"))
    fefo_risk_score = Column(Float, nullable=False) # 0.0 to 1.0
    negotiation_status = Column(String(50), default="PENDING") # PENDING, MATCHED, ACCEPTED, DECLINED

class ExecutiveBlueprintModel(Base):
    __tablename__ = "executive_blueprints"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    forecast_horizon_days = Column(Integer, default=14)
    summary_text = Column(Text, nullable=False)
    pydantic_validated = Column(Boolean, default=True)
    confidence_score = Column(Float, default=1.0)
    telegram_broadcast_status = Column(String(50), default="PENDING")


class ChatHistoryModel(Base):
    """Stores per-user chat/search history, strictly isolated by user_id."""
    __tablename__ = "chat_history"

    id           = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id      = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id   = Column(String(100), nullable=False, index=True)
    centre_id    = Column(String(50), nullable=True)
    query        = Column(Text, nullable=False)
    answer       = Column(Text, nullable=False)
    route        = Column(String(50), nullable=True)
    in_scope     = Column(Boolean, default=True)
    chart_data   = Column(Text, nullable=True)   # JSON-serialised ChartPayload
    latency_ms   = Column(Integer, nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("UserModel", backref="chat_logs")
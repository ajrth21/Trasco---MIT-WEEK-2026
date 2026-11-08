import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=False)
    role = Column(String(20), default="USER")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    preference = relationship("SecurityPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    detections = relationship("DetectionLog", back_populates="user", cascade="all, delete-orphan")


class SecurityPreference(Base):
    __tablename__ = "security_preferences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    avatar_enabled = Column(Boolean, default=True)
    avatar_theme = Column(String(50), default="CYBER_GUARDIAN")
    audio_alert_enabled = Column(Boolean, default=True)
    risk_threshold = Column(String(20), default="MEDIUM")
    auto_scan_urls = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="preference")


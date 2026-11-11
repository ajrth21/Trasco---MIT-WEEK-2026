import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base


class DetectionLog(Base):
    __tablename__ = "detection_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    visitor_id = Column(String(32), nullable=True, index=True)
    scan_type = Column(String(20), nullable=False)  # URL, TEXT, IMAGE
    target_hash = Column(String(64), index=True, nullable=True)  # SHA256 of content
    sanitized_snippet = Column(String(255), nullable=False)
    risk_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, UNKNOWN
    risk_score = Column(Integer, nullable=False, default=-1)  # 0 to 100, or -1 as database-safe fallback for uncompleted/failed scans
    threat_category = Column(String(50), nullable=False, default="UNKNOWN")  # Threat category or UNKNOWN for failed scans
    detection_indicators = Column(JSON, nullable=False, default=list)
    recommendations = Column(JSON, nullable=False, default=list)
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="detections")


class ThreatStatistic(Base):
    __tablename__ = "threat_statistics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    record_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    category = Column(String(50), nullable=False)
    risk_level = Column(String(20), nullable=False)
    count = Column(Integer, default=1)

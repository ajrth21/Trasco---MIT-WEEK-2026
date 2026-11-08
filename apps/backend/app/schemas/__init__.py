"""Pydantic Request & Response Validation Schemas
Mirrors the TypeScript contracts defined in packages/shared-types.
"""
from app.schemas.detection import AnalyzeRequest, AnalyzeResponse, DetectionIndicator, AvatarGuidance
from app.schemas.auth import UserRegister, UserLogin, Token, UserOut, SecurityPreferenceOut, SecurityPreferenceUpdate
from app.schemas.analytics import SecurityOverviewResponse, RiskBreakdown, ThreatDistribution, DailyScanTrend, ScanHistoryItem

__all__ = [
    "AnalyzeRequest", "AnalyzeResponse", "DetectionIndicator", "AvatarGuidance",
    "UserRegister", "UserLogin", "Token", "UserOut", "SecurityPreferenceOut", "SecurityPreferenceUpdate",
    "SecurityOverviewResponse", "RiskBreakdown", "ThreatDistribution", "DailyScanTrend", "ScanHistoryItem"
]

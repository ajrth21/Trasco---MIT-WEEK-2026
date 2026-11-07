from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DetectionIndicator(BaseModel):
    indicator: str
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    explanation: str


class AvatarGuidance(BaseModel):
    mood: str = "IDLE_VIGILANT"  # IDLE_VIGILANT, CAUTION_ALERT, CRITICAL_SHIELD, ANALYZING
    speechText: str
    accentColor: str = "#10B981"
    recommendedActionPrimary: Optional[str] = None
    recommendedActionSecondary: Optional[str] = None


class AnalyzeRequest(BaseModel):
    scanType: str = Field(..., description="URL, TEXT, or IMAGE")
    content: str = Field(..., description="Content to analyze (URL string, message text, or base64 data URL)")
    metadata: Optional[Dict[str, Any]] = None


class AnalyzeResponse(BaseModel):
    scanId: str
    riskLevel: str  # LOW, MEDIUM, HIGH
    riskScore: int  # 0 - 100
    threatCategory: str
    summary: str
    detectionIndicators: List[DetectionIndicator]
    recommendedActions: List[str]
    avatarGuidance: AvatarGuidance
    analyzedAt: str
    latencyMs: Optional[float] = None


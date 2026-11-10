from typing import List, Optional, Dict, Any, Literal
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


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class AnalyzeRequest(BaseModel):
    scanType: Literal["URL", "TEXT"] = Field(..., description="URL or TEXT")
    content: str = Field(..., description="Content to analyze (URL string, message text, or base64 data URL)")
    metadata: Optional[Dict[str, Any]] = None


class AnalyzeImageRequest(BaseModel):
    scanType: Literal["IMAGE"] = "IMAGE"
    content: str = Field(..., description="Base64 Data URL (e.g. data:image/png;base64,...)")
    mimeType: str = Field(..., description="Declared MIME type (image/jpeg, image/png, image/webp)")
    fileName: Optional[str] = Field(None, description="Original filename if available")
    metadata: Optional[Dict[str, Any]] = None


class AnalyzeResponse(BaseModel):
    success: bool = True
    status: str = "COMPLETED"  # COMPLETED, INVALID_REQUEST, INVALID_IMAGE, ANALYSIS_UNAVAILABLE, ANALYSIS_FAILED
    scanId: Optional[str] = None
    riskLevel: str  # LOW, MEDIUM, HIGH, UNKNOWN
    riskScore: Optional[int] = None  # 0 - 100 on COMPLETED, null on failure
    threatCategory: Optional[str] = None
    summary: str
    detectionIndicators: List[DetectionIndicator] = Field(default_factory=list)
    recommendedActions: List[str] = Field(default_factory=list)
    avatarGuidance: AvatarGuidance
    error: Optional[ErrorDetail] = None
    analyzedAt: str
    latencyMs: Optional[float] = None

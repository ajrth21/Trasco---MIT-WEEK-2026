from typing import List, Any
from pydantic import BaseModel


class RiskBreakdown(BaseModel):
    lowRiskCount: int
    mediumRiskCount: int
    highRiskCount: int
    totalScans: int


class ThreatDistribution(BaseModel):
    category: str
    count: int
    percentage: float


class DailyScanTrend(BaseModel):
    date: str
    scans: int
    threatsPrevented: int


class ScanHistoryItem(BaseModel):
    id: str
    scanType: str
    sanitizedSnippet: str
    riskLevel: str
    riskScore: int
    threatCategory: str
    createdAt: str

    class Config:
        from_attributes = True


class SecurityOverviewResponse(BaseModel):
    securityHygieneScore: int
    riskBreakdown: RiskBreakdown
    threatDistribution: List[ThreatDistribution]
    weeklyTrends: List[DailyScanTrend]
    recentHistory: List[ScanHistoryItem]
    keyAdvice: List[str]


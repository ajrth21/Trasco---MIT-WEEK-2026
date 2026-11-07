export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export interface DetectionIndicator {
  indicator: string;
  severity: string;
  explanation: string;
}

export interface AvatarGuidance {
  mood: string;
  speechText: string;
  accentColor: string;
}

export interface AnalyzeResponse {
  scanId: string;
  riskLevel: RiskLevel;
  riskScore: number;
  threatCategory: string;
  summary: string;
  detectionIndicators: DetectionIndicator[];
  recommendedActions: string[];
  avatarGuidance: AvatarGuidance;
  analyzedAt: string;
  latencyMs?: number;
}

export interface ScanHistoryItem {
  id: string;
  scanType: 'URL' | 'TEXT' | 'IMAGE';
  sanitizedSnippet: string;
  riskLevel: RiskLevel;
  riskScore: number;
  threatCategory: string;
  createdAt: string;
}

export interface ThreatDistribution {
  category: string;
  count: number;
  percentage: number;
}

export interface DailyScanTrend {
  date: string;
  scans: number;
  threatsPrevented: number;
}

export interface SecurityOverviewData {
  securityHygieneScore: number;
  riskBreakdown: {
    lowRiskCount: number;
    mediumRiskCount: number;
    highRiskCount: number;
    totalScans: number;
  };
  threatDistribution: ThreatDistribution[];
  weeklyTrends: DailyScanTrend[];
  recentHistory: ScanHistoryItem[];
  keyAdvice: string[];
}


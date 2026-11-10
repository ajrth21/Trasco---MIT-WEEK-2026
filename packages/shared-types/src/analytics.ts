/**
 * TRASCO Analytics & Security Hygiene Types
 */

import { RiskLevel, ThreatCategory } from './detection';

export interface ThreatDistribution {
  category: ThreatCategory | string;
  count: number;
  percentage: number;
}

export interface RiskBreakdown {
  lowRiskCount: number;
  mediumRiskCount: number;
  highRiskCount: number;
  totalScans: number;
  unknownRiskCount?: number;
}

export interface DailyScanTrend {
  date: string;
  scans: number;
  threatsPrevented: number;
}

export interface ScanHistoryItem {
  id: string;
  scanType: 'URL' | 'TEXT' | 'IMAGE';
  sanitizedSnippet: string;
  riskLevel: RiskLevel;
  riskScore: number | null;
  threatCategory: ThreatCategory | string | null;
  createdAt: string;
}

export interface SecurityOverviewResponse {
  securityHygieneScore: number; // 0 to 100
  riskBreakdown: RiskBreakdown;
  threatDistribution: ThreatDistribution[];
  weeklyTrends: DailyScanTrend[];
  recentHistory: ScanHistoryItem[];
  keyAdvice: string[];
}


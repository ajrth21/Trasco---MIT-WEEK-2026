/**
 * TRASCO Core Detection Types & Contracts
 */

export type ScanType = 'URL' | 'TEXT' | 'IMAGE';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export type ThreatCategory = 
  | 'SAFE'
  | 'PHISHING_URL'
  | 'TYPOSQUATTING'
  | 'FAKE_JOB_OFFER'
  | 'OTP_THEFT'
  | 'DEPOSIT_SCAM'
  | 'FAKE_TRANSFER_SLIP'
  | 'SOCIAL_ENGINEERING'
  | 'MALICIOUS_DOWNLOAD'
  | 'SUSPICIOUS_PROMOTION'
  | 'PINJOL_ILLEGAL'
  | 'INVESTMENT_FRAUD'
  | 'EMERGENCY_IMPERSONATION'
  | 'UNKNOWN_THREAT';

export type SeverityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface DetectionIndicator {
  indicator: string;
  severity: SeverityLevel;
  explanation: string;
}

export type AvatarMood = 
  | 'IDLE_VIGILANT'   // Green / Blue: Normal safe state
  | 'CAUTION_ALERT'   // Amber: Suspicious activity detected
  | 'CRITICAL_SHIELD' // Crimson: Imminent threat, blocks/shields user
  | 'ANALYZING';      // Pulse animation during scan

export interface AvatarGuidance {
  mood: AvatarMood;
  speechText: string;
  accentColor: string;
  recommendedActionPrimary?: string;
  recommendedActionSecondary?: string;
}

export interface AnalyzeRequest {
  scanType: ScanType;
  content: string; // URL string, text message, or base64 data URL for image
  metadata?: {
    sourceDomain?: string;
    clientTimestamp?: string;
    userAgent?: string;
    mode?: 'passive_heuristic' | 'active_deep';
  };
}

export interface AnalyzeResponse {
  scanId: string;
  riskLevel: RiskLevel;
  riskScore: number; // 0 to 100
  threatCategory: ThreatCategory;
  summary: string;
  detectionIndicators: DetectionIndicator[];
  recommendedActions: string[];
  avatarGuidance: AvatarGuidance;
  analyzedAt: string;
  latencyMs?: number;
}

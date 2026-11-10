/**
 * TRASCO Core Detection Types & Contracts (v0.3.2 Canonical Baseline)
 */

export type ScanType = 'URL' | 'TEXT' | 'IMAGE';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'UNKNOWN';

export type ProcessingStatus =
  | 'COMPLETED'
  | 'INVALID_REQUEST'
  | 'INVALID_IMAGE'
  | 'ANALYSIS_UNAVAILABLE'
  | 'ANALYSIS_FAILED';

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

export type CanonicalErrorCode =
  | 'REQUEST_BODY_TOO_LARGE'
  | 'PAYLOAD_VALIDATION_ERROR'
  | 'INVALID_REQUEST_PAYLOAD'
  | 'INVALID_DATA_URL'
  | 'UNSUPPORTED_IMAGE_FORMAT'
  | 'MIME_SIGNATURE_MISMATCH'
  | 'IMAGE_PAYLOAD_TOO_LARGE'
  | 'IMAGE_TOO_LARGE'
  | 'IMAGE_DIMENSIONS_EXCEEDED'
  | 'IMAGE_PIXEL_LIMIT_EXCEEDED'
  | 'IMAGE_DECODE_FAILED'
  | 'INVALID_BASE64'
  | 'AI_KEY_NOT_CONFIGURED'
  | 'AI_QUOTA_EXHAUSTED'
  | 'VISION_SERVICE_UNAVAILABLE'
  | 'VISION_TIMEOUT'
  | 'INVALID_AI_RESPONSE'
  | 'INTERNAL_ANALYSIS_ERROR';

export interface ErrorDetail {
  code: CanonicalErrorCode | string;
  message: string;
  details?: Record<string, unknown> | null;
}

export type SeverityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface DetectionIndicator {
  indicator: string;
  severity: SeverityLevel;
  explanation: string;
}

export type AvatarMood = 
  | 'IDLE_VIGILANT'   // Green / Blue: Normal safe state
  | 'CAUTION_ALERT'   // Amber: Suspicious activity or analysis incomplete
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

export interface AnalyzeImageRequest {
  scanType: 'IMAGE';
  content: string; // Base64 data URL (e.g. data:image/png;base64,...)
  mimeType: 'image/jpeg' | 'image/png' | 'image/webp' | string;
  fileName?: string | null;
  metadata?: {
    sourceDomain?: string;
    clientTimestamp?: string;
    userAgent?: string;
    mode?: 'passive_heuristic' | 'active_deep';
  };
}

export interface AnalyzeResponse {
  success: boolean;
  status: ProcessingStatus;
  scanId: string | null;
  riskLevel: RiskLevel;
  riskScore: number | null; // 0 to 100 on COMPLETED, null on non-COMPLETED
  threatCategory: ThreatCategory | string | null;
  summary: string;
  detectionIndicators: DetectionIndicator[];
  recommendedActions: string[];
  avatarGuidance: AvatarGuidance;
  error: ErrorDetail | null;
  analyzedAt: string;
  latencyMs?: number | null;
}

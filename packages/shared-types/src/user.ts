/**
 * TRASCO User & Security Preferences Types
 */

export interface UserProfile {
  id: string;
  email: string;
  displayName: string;
  role: 'USER' | 'ADMIN';
  createdAt: string;
}

export interface SecurityPreferences {
  avatarEnabled: boolean;
  avatarTheme: 'CYBER_GUARDIAN' | 'MINIMAL_PILL';
  audioAlertEnabled: boolean;
  riskThreshold: 'LOW' | 'MEDIUM' | 'HIGH';
  autoScanSuspiciousUrls: boolean;
}

export interface AuthResponse {
  token: string;
  tokenType: string;
  user: UserProfile;
}


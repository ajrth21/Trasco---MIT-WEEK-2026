import { SecurityOverviewData, AnalyzeResponse, ScanHistoryItem } from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? 'http://localhost:8000' : '');

export async function fetchSecurityOverview(): Promise<SecurityOverviewData> {
  const res = await fetch(`${BASE_URL}/api/v1/analytics/overview`, {
    headers: { 'X-Trasco-Source': 'Dashboard-Client' }
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch analytics (HTTP ${res.status})`);
  }
  return await res.json();
}

export async function fetchFullHistory(): Promise<any[]> {
  try {
    const res = await fetch(`${BASE_URL}/api/v1/analytics/history`, {
      headers: { 'X-Trasco-Source': 'Dashboard-Client' }
    });
    if (!res.ok) throw new Error('Failed to fetch history');
    return await res.json();
  } catch (err) {
    return [];
  }
}

export async function scanContent(scanType: string, content: string): Promise<AnalyzeResponse> {
  const endpoint = scanType === 'IMAGE' ? '/api/v1/detect/analyze-image' : '/api/v1/detect/analyze';
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'X-Trasco-Source': 'Dashboard-Client'
    },
    body: JSON.stringify({ scanType, content })
  });
  if (!res.ok) {
    throw new Error(`Scan failed with status ${res.status}`);
  }
  return await res.json();
}

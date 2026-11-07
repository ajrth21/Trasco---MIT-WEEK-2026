import { SecurityOverviewData, AnalyzeResponse, ScanHistoryItem } from '../types';

const BASE_URL = 'http://localhost:8000';

export async function fetchSecurityOverview(): Promise<SecurityOverviewData> {
  try {
    const res = await fetch(`${BASE_URL}/api/v1/analytics/overview`, {
      headers: { 'X-Trasco-Source': 'Dashboard-Client' }
    });
    if (!res.ok) throw new Error('Failed to fetch analytics');
    return await res.json();
  } catch (err) {
    console.warn('Backend unavailable, using fallback mock data for dashboard view', err);
    return {
      securityHygieneScore: 84,
      riskBreakdown: {
        lowRiskCount: 14,
        mediumRiskCount: 4,
        highRiskCount: 2,
        totalScans: 20
      },
      threatDistribution: [
        { category: 'SAFE', count: 14, percentage: 70 },
        { category: 'FAKE_JOB_OFFER', count: 3, percentage: 15 },
        { category: 'OTP_THEFT', count: 2, percentage: 10 },
        { category: 'TYPOSQUATTING', count: 1, percentage: 5 }
      ],
      weeklyTrends: [
        { date: 'Sen', scans: 2, threatsPrevented: 0 },
        { date: 'Sel', scans: 4, threatsPrevented: 1 },
        { date: 'Rab', scans: 3, threatsPrevented: 0 },
        { date: 'Kam', scans: 5, threatsPrevented: 1 },
        { date: 'Jum', scans: 2, threatsPrevented: 0 },
        { date: 'Sab', scans: 3, threatsPrevented: 0 },
        { date: 'Min', scans: 1, threatsPrevented: 0 }
      ],
      recentHistory: [
        {
          id: '1',
          scanType: 'TEXT',
          sanitizedSnippet: 'Tawaran kerja like video TikTok komisi 500rb/hari...',
          riskLevel: 'HIGH',
          riskScore: 94,
          threatCategory: 'FAKE_JOB_OFFER',
          createdAt: '2026-11-08 02:40'
        },
        {
          id: '2',
          scanType: 'URL',
          sanitizedSnippet: 'https://klikbca-hadiah-gebiyar.xyz/login',
          riskLevel: 'HIGH',
          riskScore: 92,
          threatCategory: 'TYPOSQUATTING',
          createdAt: '2026-11-08 02:15'
        },
        {
          id: '3',
          scanType: 'URL',
          sanitizedSnippet: 'https://www.klikbca.com',
          riskLevel: 'LOW',
          riskScore: 0,
          threatCategory: 'SAFE',
          createdAt: '2026-11-08 01:30'
        }
      ],
      keyAdvice: [
        'Jangan pernah membagikan kode OTP atau PIN m-banking kepada siapa pun.',
        'Waspadai skema tugas paruh waktu like video yang meminta deposit uang jaminan.',
        'Selalu periksa domain perbankan resmi berakhiran .co.id atau .id sebelum login.'
      ]
    };
  }
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


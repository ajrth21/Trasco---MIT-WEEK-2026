# TRASCO REST API Specification

> **Base URL:** `http://localhost:8000` (Default Local Port)  
> **API Version:** `v1.0.0`  
> **Protocol:** HTTP / JSON  
> **Handshake Header:** `X-Trasco-Source: Extension-Local` or `Dashboard-Client`  

---

## 1. Authentication & Security Handshake

All API endpoints running on `http://localhost:8000` are protected by the TRASCO Local Firewall Gatekeeper. Requests originating from browser contexts must provide a valid client identifier header:

| Header | Required Value | Description |
|---|---|---|
| `Content-Type` | `application/json` | Standard JSON payload format. |
| `X-Trasco-Source` | `Extension-Local` or `Dashboard-Client` | Identifies authorized client components and protects against unauthorized web origin scraping. |

---

## 2. Implemented Endpoints (Primary Flask Runner)

### A. System Health Check
Returns the operational status of the threat intelligence engine.

- **Endpoint:** `GET /health`
- **Auth Required:** No
- **Headers:** None required
- **Success Response (200 OK):**
```json
{
  "service": "TRASCO Backend API (Dual-Engine)",
  "status": "healthy",
  "timestamp": "2026-11-08T04:44:35.894805+00:00",
  "version": "1.0.0"
}
```

---

### B. Analyze Content (URL & Text Scam Detection)
Analyzes an incoming URL or text message for phishing indicators, typosquatting, social engineering, or scam patterns.

- **Endpoint:** `POST /api/v1/detect/analyze`
- **Auth Required:** Yes (`X-Trasco-Source` header required for browser requests)
- **Request Body (`AnalyzeRequest`):**
```json
{
  "scanType": "TEXT", // "URL" | "TEXT"
  "content": "Lowongan kerja freelance like video TikTok komisi 500rb/hari, transfer deposit 50rb dan kirimkan kode OTP SMS Anda.",
  "metadata": {
    "sourceDomain": "web.whatsapp.com",
    "mode": "active_deep" // "active_deep" | "passive_heuristic"
  }
}
```

- **Success Response (200 OK) (`AnalyzeResponse`):**
```json
{
  "scanId": "72af571c-bccc-4a53-9d04-c4f3f4bc6d84",
  "riskLevel": "HIGH", // "LOW" | "MEDIUM" | "HIGH"
  "riskScore": 95,     // 0 to 100
  "threatCategory": "OTP_THEFT",
  "summary": "Terdeteksi ancaman siber berisiko tinggi (OTP THEFT). Pola ancaman sesuai basis data modus penipuan.",
  "detectionIndicators": [
    {
      "indicator": "Permintaan Informasi Rahasia (OTP / PIN)",
      "severity": "CRITICAL",
      "explanation": "Pesan secara eksplisit meminta kode OTP atau PIN yang merupakan kredensial keamanan pribadi."
    },
    {
      "indicator": "Modus Lowongan Kerja Fiktif (Like & Subscribe)",
      "severity": "HIGH",
      "explanation": "Pola janji upah instan hanya dengan like/subscribe adalah modus klasik penipuan digital."
    },
    {
      "indicator": "Tuntutan Deposit / Uang Muka",
      "severity": "CRITICAL",
      "explanation": "Pesan meminta pengiriman uang jaminan/deposit di muka dengan dalih keuntungan besar."
    }
  ],
  "recommendedActions": [
    "JANGAN membagikan data pribadi, kode OTP, atau transfer dana.",
    "Segera tutup halaman atau hentikan komunikasi dengan kontak ini.",
    "Laporkan kontak atau domain ini ke pihak berwenang."
  ],
  "avatarGuidance": {
    "mood": "CRITICAL_SHIELD", // "IDLE_VIGILANT" | "CAUTION_ALERT" | "CRITICAL_SHIELD" | "ANALYZING"
    "speechText": "Bahaya! Ini adalah pola penipuan siber. Segera hentikan interaksi sekarang!",
    "accentColor": "#EF4444",
    "recommendedActionPrimary": "JANGAN membagikan data pribadi, kode OTP, atau transfer dana.",
    "recommendedActionSecondary": "Pelajari Modus Ini"
  },
  "analyzedAt": "2026-11-08T04:44:35.900473+00:00",
  "latencyMs": 2.84
}
```

- **Error Responses:**
  - `400 Bad Request`: `{"error": "Content is required"}`
  - `403 Forbidden`: `{"error": "Unauthorized request origin. Blocked by TRASCO local firewall."}`

---

### C. Analyze Image (Fake Transfer Slip & Visual Threat Verification)
Analyzes transaction slips or promotional flyers for anomalies and visual signs of forgery.

- **Endpoint:** `POST /api/v1/detect/analyze-image`
- **Auth Required:** Yes (`X-Trasco-Source` header required)
- **Request Body:**
```json
{
  "scanType": "IMAGE",
  "content": "data:image/jpeg;base64,...", // Base64 data URI or image URL
  "metadata": {
    "sourceDomain": "instagram.com"
  }
}
```
- **Success Response (200 OK):**
```json
{
  "scanId": "3b29c9a1-8d21-4f9e-b810-72c1a89d7e01",
  "riskLevel": "HIGH",
  "riskScore": 88,
  "threatCategory": "FAKE_TRANSFER_SLIP",
  "summary": "Indikasi bukti transfer palsu terdeteksi melalui inkonsistensi font pada nominal dan tata letak.",
  "detectionIndicators": [
    {
      "indicator": "Tipografi Nominal Tidak Selaras",
      "severity": "HIGH",
      "explanation": "Karakter angka pada nominal transaksi memiliki ukuran dan ketajaman yang berbeda dari template m-banking asli."
    }
  ],
  "recommendedActions": [
    "Periksa saldo langsung melalui aplikasi mobile banking atau mutasi rekening resmi.",
    "Jangan kirimkan barang atau lakukan konfirmasi sebelum dana efektif masuk."
  ],
  "avatarGuidance": {
    "mood": "CRITICAL_SHIELD",
    "speechText": "Perhatian! Bukti transfer ini menunjukkan kejanggalan visual. Cek mutasi rekening Anda sekarang.",
    "accentColor": "#EF4444",
    "recommendedActionPrimary": "Cek Mutasi Rekening",
    "recommendedActionSecondary": "Pelajari Modus"
  },
  "analyzedAt": "2026-11-08T04:45:00.000000+00:00",
  "latencyMs": 145.2
}
```

---

### D. Security Analytics Overview
Retrieves aggregated telemetry and personal security hygiene scores.

- **Endpoint:** `GET /api/v1/analytics/overview`
- **Auth Required:** Yes (`X-Trasco-Source: Dashboard-Client`)
- **Success Response (200 OK) (`SecurityOverviewResponse`):**
```json
{
  "securityHygieneScore": 88,
  "riskBreakdown": {
    "totalScans": 25,
    "lowRiskCount": 18,
    "mediumRiskCount": 5,
    "highRiskCount": 2
  },
  "threatDistribution": [
    { "category": "SAFE", "count": 18, "percentage": 72 },
    { "category": "FAKE_JOB_OFFER", "count": 3, "percentage": 12 },
    { "category": "TYPOSQUATTING", "count": 2, "percentage": 8 },
    { "category": "OTP_THEFT", "count": 2, "percentage": 8 }
  ],
  "weeklyTrends": [
    { "date": "Sen", "scans": 3, "threatsPrevented": 0 },
    { "date": "Sel", "scans": 5, "threatsPrevented": 1 },
    { "date": "Rab", "scans": 4, "threatsPrevented": 0 },
    { "date": "Kam", "scans": 6, "threatsPrevented": 1 },
    { "date": "Jum", "scans": 3, "threatsPrevented": 0 },
    { "date": "Sab", "scans": 2, "threatsPrevented": 0 },
    { "date": "Min", "scans": 2, "threatsPrevented": 0 }
  ],
  "recentHistory": [],
  "keyAdvice": [
    "Pertahankan kebiasaan memeriksa domain resmi sebelum memasukkan kredensial perbankan.",
    "Jangan pernah membagikan kode OTP atau mentransfer biaya pendaftaran lowongan kerja."
  ]
}
```

---

### E. Detection History
Retrieves recent detection logs with PII redacted.

- **Endpoint:** `GET /api/v1/analytics/history`
- **Auth Required:** Yes (`X-Trasco-Source: Dashboard-Client`)
- **Query Parameters:** Optional (default limits to recent 30 items)
- **Success Response (200 OK):**
```json
[
  {
    "id": "72af571c-bccc-4a53-9d04-c4f3f4bc6d84",
    "scanType": "TEXT",
    "sanitizedSnippet": "Lowongan kerja freelance like video TikTok komisi 500rb/hari, transfer deposit 50rb dan kirimkan kode OTP SMS Anda.",
    "riskLevel": "HIGH",
    "riskScore": 95,
    "threatCategory": "OTP_THEFT",
    "indicators": "[...]",
    "recommendations": "[...]",
    "createdAt": "2026-11-08T04:44:35.912478"
  }
]
```

---

## 3. Optional Endpoints (FastAPI Alternative Runner)

The repository also includes FastAPI routers under `apps/backend/app/api/v1/`:
- `POST /api/v1/auth/register` — User account registration
- `POST /api/v1/auth/login` — OAuth2 Password Bearer JWT login
- `GET /api/v1/preferences/` — User security preferences retrieval
- `PUT /api/v1/preferences/` — User security preferences update

> **Note:** In the primary hackathon demo configuration running `flask_app.py`, user authentication is non-blocking (anonymous zero-friction mode) to allow immediate demonstration without forced registration.


# TRASCO Project Discovery & Foundation Validation Report

> **Document:** Discovery Audit & Architecture Baseline
> **Status:** Discovery Complete — Awaiting Product Clarifications
> **Date:** 2026-11-09

---

## 1. Verified Implementation Status (Audit Aktual)

| Komponen | Status Implementasi | Bukti Verifikasi |
|---|:---:|---|
| **Heuristic Engine (URL & Text)** | **VERIFIED** | 7 pattern regex Indonesia, Shannon entropy, brand typosquatting. 6 unit tests lulus. |
| **PII Scrubber (UU PDP)** | **VERIFIED** | Sensor NIK, No HP fleksibel (spasi/tanda hubung), email, OTP, no rekening. 5 unit tests lulus. |
| **Origin Isolation & Gatekeeper (SEC-01)** | **VERIFIED** | Allowlist CORS ketat, loopback binding 127.0.0.1, header verification. 8 tests lulus. |
| **Universal Risk Floor (SEC-02)** | **VERIFIED** | Nilai heuristik menjadi batas bawah mutlak melawan prompt injection. 6 tests lulus. |
| **Phone Number Scrubbing Hardening (SEC-03)** | **VERIFIED** | Regresi regex nomor telepon (+62, spasi, tanda hubung) tanpa false positive. 9 tests lulus. |
| **Extension MV3 (Core & Service Worker)** | **VERIFIED** | LRU Cache 10m, Debounce 400ms, context menu scan teks/gambar, badge toolbar status. |
| **Extension Avatar (Content Script)** | **VERIFIED** | Closed Shadow DOM host, safe DOM API (0% dynamic innerHTML), Web Speech API TTS (`id-ID`). |
| **Extension Popup UI** | **VERIFIED** | Real-time heartbeat check ke `GET /health`, quick scanner interface. |
| **Web Dashboard (React + Vite)** | **VERIFIED** | TypeScript clean compile, production bundle Vite sukses (39 modules). |
| **Shared Contracts (@trasco/shared-types)**| **VERIFIED** | Tipe `AnalyzeRequest`, `AnalyzeResponse`, `ThreatCategory` terpetakan lintas aplikasi. |
| **CI/CD Pipeline (GitHub Actions)** | **VERIFIED** | `.github/workflows/ci.yml` lolos 100% pada remote GitHub Actions (Run ID `42495184515`). |
| **Gemini AI Integration (Multimodal)** | **PARTIALLY IMPLEMENTED** | Kode integrasi di `gemini_service.py` & `image_analyzer.py` tersedia, tetapi default fallback lokal karena tanpa API key. |
| **Dashboard Live History Polling** | **PARTIALLY IMPLEMENTED** | Endpoint backend `/api/v1/analytics/history` aktif, frontend memiliki fallback mock jika server mati. |
| **User Authentication & Cloud Sync** | **NOT IMPLEMENTED** | Schema ORM & Pydantic ada (`User`, `SecurityPreference`), namun auth flow belum diaktifkan (fokus lokal hackathon). |

---

## 2. Technical Debt & Identifikasi Risiko

1. **Pydantic Deprecation Warnings:**
   - Model `UserOut`, `SecurityPreferenceOut`, dan `ScanHistoryItem` masih menggunakan inner `class Config: from_attributes = True` lama yang didepresiasi di Pydantic v2. Perlu migrasi ke `model_config = ConfigDict(from_attributes=True)`.
2. **Offline vs Online Quota Limitation:**
   - Free tier Google Gemini Flash memiliki limit 15 RPM. Mode passive URL browsing sudah diamankan dengan fallback heuristik + cache 10 menit.
3. **Audio Autoplay Restriction:**
   - Web Speech API pada content script bergantung pada gesture/interaksi pengguna di beberapa situs dengan kebijakan autoplay ketat.

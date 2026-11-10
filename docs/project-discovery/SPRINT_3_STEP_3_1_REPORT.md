# TRASCO SPRINT 3 — STEP 3.1 REPORT
> **Scope:** Targeted Debugging & Integration Validation Issues Resolution
> **Status:** PASS (All issues resolved, 54/54 unit tests passed, 10/10 integration scenarios passed, Gemini fallback 100% resilient)
> **Date:** 2026-11-09

---

## 1. Ringkasan Eksekutif

Pada STEP 3.1, dilakukan investigasi dan perbaikan terarah (*targeted debugging*) terhadap dua kegagalan validasi integrasi yang ditemukan pada pengujian STEP 3:
1. **Kegagalan Skenario 8 pada 10 Integration Scenarios:** Pesan berisi tautan pemendek URL (*shortener*) yang dikombinasikan dengan pencurian OTP dan undian hadiah sebelumnya hanya menghasilkan skor 65 (MEDIUM).
2. **Kegagalan Error Handling pada Gemini Fallback:** Panggilan AI pada `orchestrate_detection` belum membungkus pengecualian tak terduga (*unhandled network/timeout exception*) dari lapisan API secara defensif di level orchestrator.

Selain menyelesaikan kedua isu di atas, dilakukan penyempurnaan deteksi kontekstual:
- **URL Shortener False Positive Elimination:** Menyebutkan kata "bitly" dalam teks percakapan biasa menghasilkan skor 0 (SAFE). Tautan pemendek URL riil yang disematkan dalam teks dikenali sebagai sinyal risiko (+20), dan bila berkombinasi dengan pencurian OTP/hadiah mencapai skor 85 (HIGH).
- **Context-Aware Ponzi / Money Game Detection:** Pertanyaan edukatif atau hukum ("Apa itu skema Ponzi?", "Bagaimana cara kerja money game menurut hukum di Indonesia?") menghasilkan skor 0 (SAFE). Modus penawaran riil tetap terdeteksi sebagai `INVESTMENT_FRAUD`.

Seluruh perbaikan diverifikasi dengan **54/54 tests passed** pada backend pytest, **10/10 integration scenarios passed**, **4/4 fallback scenarios passed**, serta validasi TypeScript dan Vite build dashboard yang bersih.

---

## 2. Investigasi Mendalam & Solusi Dua Validasi Gagal

### A. Validasi 1: `validate 10 integration scenarios` (Skenario 8)

- **Gejala / Traceback:**
  `AssertionError: assert s8['riskLevel'] == 'HIGH'`
  Hasil sebelum perbaikan: `riskScore: 65, riskLevel: 'MEDIUM'`
- **Akar Masalah (Root Cause):**
  Deteksi pemendek URL sebelumnya hanya dieksekusi di `analyze_url_heuristics(url_str)`. Ketika pengguna menguji pesan teks yang di dalamnya disematkan URL pendek (misal `https://bit.ly/...`), fungsi `analyze_text_heuristics` hanya mendeteksi pencurian OTP (+40) dan hadiah (+25) = 65, tanpa memperhitungkan sinyal pemendek URL di dalam badan teks.
- **Solusi yang Diterapkan:**
  Menambahkan pola regex `shortener_link_pattern` pada `analyze_text_heuristics` di `heuristic_engine.py`:
  ```python
  shortener_link_pattern = r"(?i)(?:https?://)?(?:www\.)?(?:bit\.ly|tinyurl\.com|t\.co|s\.id|cutt\.ly|is\.gd|shorturl\.at|rb\.gy|rebrand\.ly)/[a-zA-Z0-9_\-]+"
  ```
  Bila ditemukan tautan pemendek URL di dalam teks, skor ditambah proporsional (+20) dan indikator `SHORTENER_IN_TEXT` dicatat.
- **Hasil Setelah Perbaikan:**
  Skor terakumulasi menjadi 85 (HIGH, `OTP_THEFT`), memenuhi ekspektasi pengujian.

---

### B. Validasi 2: `verify Gemini fallback behavior` (Unhandled Exception)

- **Gejala / Traceback:**
  `Exception: Connection Timeout` saat `analyze_with_gemini` mengalami kegagalan koneksi atau error jaringan eksternal.
- **Akar Masalah (Root Cause):**
  Pada `risk_scorer.py`, fungsi `orchestrate_detection` mengasumsikan seluruh pengecualian telah ditangani di dalam `analyze_with_gemini`. Jika terjadi kegagalan jaringan eksternal tak terduga, mock error, atau timeout yang lolos, orchestrator tidak membungkus pemanggilan AI dalam blok defensif `try...except`, menyebabkan proses deteksi crash alih-alih melakukan *graceful fallback*.
- **Solusi yang Diterapkan:**
  Membungkus pemanggilan `analyze_with_gemini` dan `analyze_image_with_gemini` di `risk_scorer.py` dengan blok `try...except Exception as exc:` defensif:
  ```python
  try:
      ai_result = analyze_with_gemini(...)
  except Exception as exc:
      logger.warning("Gemini analysis encountered an unhandled exception: %s. Falling back to heuristics.", exc)
      ai_result = None
  ```
- **Hasil Setelah Perbaikan:**
  Ketika Gemini API timeout, offline, atau melempar exception jaringan, deteksi TRASCO 100% beralih secara mulus ke mesin heuristik deterministik tanpa crash dan tanpa menurunkan risk floor.

---

## 3. Resolusi False Positive & Deteksi Kontekstual

### A. URL Shortener Detection

| Input Uji | Kategori | Skor | Level | Keterangan |
|---|:---:|:---:|:---:|---|
| `"Saya membaca artikel tentang bitly kemarin"` | `SAFE` | 0 | LOW | Penyebutan kata bitly biasa tidak menaikkan skor. |
| `"Kunjungi link promosi kami: https://bit.ly/promo-toko"` | `PHISHING_URL` | 20 | LOW | Tautan pemendek URL dikenali sebagai risk signal (+20). |
| `"Klaim hadiah undian 50jt klik https://bit.ly/undian-bca-gratis dan masukkan kode OTP."` | `OTP_THEFT` | 85 | HIGH | Kombinasi OTP (40) + Hadiah (25) + Shortener (20) memicu status HIGH. |

- **Keamanan:** Nol panggilan HTTP atau DNS query. Zero risk of SSRF / tracking.

---

### B. Context-Aware Ponzi / Money Game Detection

| Input Uji | Kategori | Skor | Level | Keterangan |
|---|:---:|:---:|:---:|---|
| `"Apa itu skema Ponzi dan bagaimana cara kerja money game menurut hukum di Indonesia?"` | `SAFE` | 0 | LOW | Pertanyaan edukatif tidak memicu alarm palsu. |
| `"Apa perbedaan antara skema ponzi dengan multi level marketing resmi?"` | `SAFE` | 0 | LOW | Analisis perbandingan netral tetap berstatus aman. |
| `"Gabung bersama kami, skema ponzi berkedok investasi resmi, profit 10% per hari pasti untung"` | `INVESTMENT_FRAUD` | 40 | MEDIUM | Penawaran riil dengan kata kunci ajakan/kedok langsung terdeteksi. |
| `"Titip dana trading crypto pasti cuan 5% per hari anti loss"` | `INVESTMENT_FRAUD` | 40 | MEDIUM | Modus titip dana trading otomatis terdeteksi. |

---

## 4. Hasil Pengujian Lengkap

### A. Backend Unit Tests (`pytest -v`)
```
======================= 54 passed, 3 warnings in 1.74s ========================
```
- Total **54/54 tests passed** (100% success rate):
  - `test_heuristics.py`: **26 tests** (6 baseline lama + 18 penambahan Step 2 + 2 penambahan Step 3.1)
  - `test_security_hardening.py`: **23 tests** (8 SEC-01 CORS & Handshake + 6 SEC-02 Universal Risk Floor + 9 SEC-03 Phone Scrubbing)
  - `test_security_scrubber.py`: **5 tests** (Core PII Scrubber & Anti Prompt Injection Gatekeeper)
- Seluruh 34 baseline test keamanan (SEC-01, SEC-02, SEC-03) tetap utuh dan lulus 100%.

### B. 10 Integration Scenarios Validation
- Skenario 1: Pinjol Ilegal (Ancaman sebar KTP) -> `PINJOL_ILLEGAL` (40 / MEDIUM) **[PASS]**
- Skenario 2: Edukasi Pinjol Resmi OJK -> `SAFE` (0 / LOW) **[PASS]**
- Skenario 3: Investasi Bodong Profit Pasti -> `INVESTMENT_FRAUD` (40 / MEDIUM) **[PASS]**
- Skenario 4: Edukasi Skema Ponzi -> `SAFE` (0 / LOW) **[PASS]**
- Skenario 5: Darurat Keluarga (Kecelakaan) -> `EMERGENCY_IMPERSONATION` (40 / MEDIUM) **[PASS]**
- Skenario 6: Berita Netral Kecelakaan -> `SAFE` (0 / LOW) **[PASS]**
- Skenario 7: URL Bitly Promosi Biasa -> `PHISHING_URL` (20 / LOW) **[PASS]**
- Skenario 8: URL Shortener + Hadiah + OTP -> `OTP_THEFT` (85 / HIGH) **[PASS]**
- Skenario 9: Domain Homoglif (`kl1kbca.com`) -> `TYPOSQUATTING` (65 / MEDIUM) **[PASS]**
- Skenario 10: Nama Bank Resmi Teks Normal -> `SAFE` (0 / LOW) **[PASS]**

### C. Gemini Fallback Verification
- Test 1 (Gemini Offline / Mock None): Fallback ke heuristik (Score: 40, `PINJOL_ILLEGAL`) **[PASS]**
- Test 2 (Gemini Empty API Key): Fallback ke heuristik (Score: 40, `INVESTMENT_FRAUD`) **[PASS]**
- Test 3 (Gemini Timeout/Network Exception): Pengecualian ditangani defensif, fallback berhasil (Score: 40, `EMERGENCY_IMPERSONATION`) **[PASS]**
- Test 4 (Universal Risk Floor SEC-02): AI mencoba downgrade ke 0, skor akhir tetap terjaga pada 65 **[PASS]**

### D. Monorepo Frontend & Extension Integrity
- **Dashboard Type Check:** `npx tsc --noEmit` -> 0 errors **[PASS]**
- **Dashboard Build:** `npm run build` -> 39 modules transformed in 1.27s **[PASS]**
- **Extension Syntax:** `node --check` -> 3/3 scripts valid **[PASS]**
- **Git Whitespace:** `git diff --check` -> Exit code 0, no trailing whitespace **[PASS]**

---

## 5. File yang Dimodifikasi

1. **`apps/backend/app/services/heuristic_engine.py`**:
   - Menambahkan deteksi `shortener_link_pattern` pada `analyze_text_heuristics`.
   - Menjadikan deteksi kata kunci `skema ponzi`/`money game` peka konteks (*context-aware*).
   - Pembersihan trailing whitespace.
2. **`apps/backend/app/services/risk_scorer.py`**:
   - Menambahkan *defensive exception wrapper* di sekitar pemanggilan `analyze_with_gemini` dan `analyze_image_with_gemini`.
3. **`apps/backend/app/services/gemini_service.py`**:
   - Penyelarasan prompt skema JSON kategori ancaman baru Sprint 3.
4. **`apps/backend/tests/test_heuristics.py`**:
   - Penambahan regression tests untuk validasi URL shortener dalam teks dan pertanyaan edukasi Ponzi.
   - Pembersihan trailing whitespace.

---

## 6. Batasan & Pertimbangan Keamanan (Known Limitations)

1. **No External Network in Heuristics:** Mesin heuristik tidak melakukan query DNS atau HTTP unshortening untuk menjaga latensi mendekati instan (<1 ms) dan privasi penuh tanpa ketergantungan koneksi.
2. **Obfuscated Multi-Hop Links:** Jika penyerang menggunakan multi-hop redirect rantai kompleks tanpa pola phishing jelas dalam teks, lapisan deteksi diserahkan kepada Gemini AI pada mode online.

---

## 7. Kesimpulan & Rekomendasi

### **STATUS: STEP 3.1 PASS** ✅

Seluruh isu integrasi dan potensi false positive telah diselesaikan dengan bersih, aman, dan teruji secara komprehensif. Tidak ada breaking changes pada monorepo.

**Rekomendasi Langkah Berikutnya:**
Menunggu konfirmasi dan persetujuan pengguna untuk melakukan staging/commit hasil STEP 1 - STEP 3.1, sebelum melangkah ke tahapan perencanaan Sprint berikutnya.

# TRASCO — Trap & Scope (AI Cyber Guardian)
> **AI-Powered Cybersecurity Browser Extension & Security Analytics Dashboard**  
> *Developed for Hackathon Web Development — Cybersecurity Track (MIT UNMUL 2026)*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Extension: Manifest V3](https://img.shields.io/badge/Chrome_Extension-Manifest_V3-green.svg)](https://developer.chrome.com/docs/extensions/)
[![AI Engine: Hybrid](https://img.shields.io/badge/AI_Engine-Heuristics_%2B_Gemini-cyan.svg)](https://ai.google.dev/)

---

## Executive Summary

**TRASCO (Trap & Scope)** adalah platform keamanan siber terpadu yang dirancang khusus untuk melindungi generasi muda Indonesia dari ancaman penipuan digital yang semakin marak—seperti penipuan lowongan kerja paruh waktu *like & subscribe*, modus deposit dana, pencurian OTP, situs phishing perbankan (*typosquatting*), hingga bukti transfer palsu (*fake payment slip*).

TRASCO dibangun di atas tiga pilar utama:
1. **PROACTIVE DETECTION:** Analisis instan berbasis hybrid (aturan heuristik deterministik + Google Gemini AI multimodal) terhadap URL, teks percakapan sosial, dan gambar transaksi.
2. **INTELLIGENT INTERVENTION:** Peringatan kontekstual visual dan verbal melalui **Interactive AI Cyber Guardian Avatar** yang diisolasi dalam **Shadow DOM**.
3. **CONTINUOUS EDUCATION:** Pemahaman pola penipuan dan mitigasi jangka panjang melalui **Personal Scam Insight & Security Analytics Dashboard**.

---

## System Architecture

```text
TRASCO ECOSYSTEM (MONOREPO)
├── apps/
│   ├── extension/          # Chrome & Edge Extension (Manifest V3 + Shadow DOM Avatar)
│   ├── dashboard/          # Web Dashboard (React + Vite + Standalone Analytics SPA)
│   └── backend/            # Threat Intelligence Engine (FastAPI / Flask + SQLite + Gemini)
├── packages/
│   └── shared-types/       # TypeScript Shared Interfaces & Contracts
└── docs/                   # Hackathon Live Demo Guide & Architecture Specs
```

---

## Panduan Memulai Cepat (Quick Start)

### 1. Menjalankan Backend Engine
Pastikan Python 3.10+ telah terpasang di komputer Anda.

```bash
# Pindah ke direktori backend
cd apps/backend

# Jalankan server API (menggunakan SQLite bawaan)
python -m app.flask_app
```
*Backend API akan aktif di `http://localhost:8000`.*  
*Endpoint status kesehatan:* `http://localhost:8000/health`

### 2. Memasang Browser Extension (Chrome / Microsoft Edge)
1. Buka browser berbasis Chromium (Google Chrome, Microsoft Edge, atau Brave).
2. Akses halaman manajemen ekstensi: `chrome://extensions` (atau `edge://extensions`).
3. Aktifkan **Developer mode** (Mode pengembang) di pojok kanan atas.
4. Klik **Load unpacked** (Muat yang belum dibongkar).
5. Arahkan dan pilih folder: `apps/extension` di dalam repositori ini.
6. Ekstensi **TRASCO Cyber Guardian** siap digunakan dan akan muncul di toolbar.

### 3. Membuka Web Dashboard
Buka file `apps/dashboard/standalone_dashboard.html` langsung di browser Anda:
```bash
# Atau jika menggunakan React dev server:
cd apps/dashboard
npm run dev
```

---

## Skenario Demonstrasi Utama (Demo Scenarios)

1. **Uji Coba Teks Penipuan (Social Engineering / Job Scam):**
   - Seleksi teks: *"Lowongan kerja freelance like video komisi 500rb/hari, transfer deposit 50rb dan kirimkan kode OTP WA Anda."*
   - Klik kanan -> Pilih **" Periksa dengan TRASCO"**.
   - Avatar otomatis mengintervensi dengan status **CRITICAL SHIELD (Merah)** dan mengeluarkan peringatan suara edukasi berbahasa Indonesia.

2. **Uji Coba Phishing & Typosquatting:**
   - Kunjungi atau masukkan URL: `https://klikbca-verifikasi-hadiah.xyz/login`.
   - Sistem mendeteksi nama domain bank BCA palsu dengan TLD `.xyz` berisiko tinggi.
   - Masukkan `https://www.klikbca.com` untuk memverifikasi situs resmi berstatus aman.

3. **Live Threat Simulator di Web Dashboard:**
   - Buka Web Dashboard -> Tab **Live Scam Simulator** untuk mendemonstrasikan pengujian berbagai skenario penipuan lokal secara langsung di hadapan dewan juri.

Detail lengkap skrip presentasi 5 menit tersedia di: [docs/demo_scenarios.md](docs/demo_scenarios.md).

---

## Privasi & Keamanan (Security by Design)

- **Shadow DOM Encapsulation:** Komponen UI avatar di-render di dalam isolated Shadow Root tertutup sehingga stylesheet dan JavaScript halaman target tidak dapat memanipulasi peringatan keamanan.
- **Kepatuhan UU PDP No. 27/2022:** Ekstensi menerapkan prinsip minimisasi data. Tidak ada perekaman riwayat penelusuran secara menyeluruh; hanya potongan teks atau domain berisiko yang dipindai saat pengguna memintanya.
- **Backend Token Proxying:** Ekstensi browser tidak menyimpan API key Gemini untuk mencegah kebocoran kredensial dari client-side inspection.

---

## Tim Pengembang

Dibuat dengan dedikasi untuk **MIT UNMUL 2026 Hackathon Web Development**  
*Membangun Ruang Digital yang Lebih Aman dan Cerdas bagi Generasi Muda Indonesia.*

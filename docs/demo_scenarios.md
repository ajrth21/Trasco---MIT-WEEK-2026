# Panduan Skenario Demonstrasi Juri — TRASCO (MIT UNMUL 2026)

Dokumen ini adalah skrip operasional untuk mendemonstrasikan ekosistem **TRASCO** di hadapan dewan juri hackathon.

---

## 🚀 Persiapan Lingkungan (Pre-Demo Setup)

### 1. Menjalankan Backend TRASCO
Buka terminal dan navigasikan ke direktori backend:
```bash
cd apps/backend
python -m app.flask_app
```
*Backend akan aktif pada: `http://localhost:8000` (Database SQLite otomatis terinisialisasi).*

### 2. Memuat Browser Extension di Google Chrome / Microsoft Edge
1. Buka browser Chrome/Edge dan ketik di address bar: `chrome://extensions`
2. Aktifkan **"Developer mode"** di pojok kanan atas.
3. Klik tombol **"Load unpacked"** (Muat yang belum dibongkar).
4. Pilih folder: `c:\Users\ACER\hackathon\mit-unmul\Trasco---MIT-WEEK-2026\apps\extension`
5. Pin ikon **TRASCO Cyber Guardian (🛡️)** pada toolbar browser.

### 3. Membuka Web Dashboard
Buka file `apps/dashboard/standalone_dashboard.html` di browser Anda (atau jalankan server React jika diinginkan).

---

## 🎭 Skenario Demonstrasi (Durasi: 5 Menit)

### SKENARIO 1: Deteksi Rekayasa Sosial & Penipuan Chat Telegram / WA (2 Menit)
*Modus: Lowongan kerja paruh waktu like video dengan tuntutan deposit uang jaminan.*

1. Buka halaman web percakapan atau dokumen simulasi yang memuat teks:
   > *"Selamat siang kak! Kami dari agensi digital membuka lowongan kerja freelance like video TikTok komisi 500rb per hari langsung cair! Syarat cukup transfer biaya deposit jaminan 50rb ke Rek BCA 8820129381 dan kirimkan kode OTP yang masuk ke nomor WA Anda."*
2. **Aksi Pengguna:** Blok (seleksi) teks tersebut di browser -> Klik Kanan -> Pilih **"🛡️ Periksa dengan TRASCO (AI Scam Check)"**.
3. **Reaksi Sistem & AI Guardian Avatar:**
   - Avatar TRASCO yang mengapung di pojok kanan bawah seketika berubah menjadi **Perisai Kritis (Merah Berkedip)**.
   - Suara edukasi verbal berbahasa Indonesia otomatis berbunyi via Web Speech API:
     *"Awas! Ini adalah penipuan berbahaya. Jangan berikan kode OTP atau transfer uang!"*
   - Kartu dialog muncul menampilkan:
     - **Tingkat Risiko:** HIGH RISK (Skor: 96/100)
     - **Indikator Kunci:** Permintaan Kode OTP (CRITICAL) & Skema Deposit Awal (CRITICAL).
     - **Rekomendasi Tindakan:** "JANGAN PERNAH membagikan kode OTP atau mentransfer uang".

### SKENARIO 2: Deteksi Situs Phishing & Typosquatting Perbankan (1.5 Menit)
*Modus: Penyamaran domain resmi bank menggunakan TLD murah.*

1. Ketik URL simulasi pada popup extension atau browser:
   `https://klikbca-verifikasi-gebyar-hadiah.xyz/login`
2. **Deteksi Proaktif Ekstensi:**
   - Mesin Heuristik & Shannon Entropy mendeteksi nama domain mencantumkan merek resmi `BCA` pada domain tidak resmi dengan TLD `.xyz`.
   - Avatar memunculkan peringatan waspada sebelum pengguna memasukkan kredensial login.
3. Bandingkan dengan memasukkan URL resmi `https://www.klikbca.com` yang secara otomatis terverifikasi berstatus **LOW RISK (Aman)**.

### SKENARIO 3: Personal Scam Insight & Security Analytics Dashboard (1.5 Menit)
1. Buka Web Dashboard TRASCO.
2. Tunjukkan **Security Hygiene Score** pengguna.
3. Tunjukkan visualisasi **Distribusi Kategori Ancaman** (Lowongan Fiktif, Pencurian OTP, Phishing).
4. Tunjukkan bagaimana riwayat deteksi dari Ekstensi otomatis tersinkronisasi di tabel log.
5. Jalankan tab **Live Scam Simulator** untuk menunjukkan pengujian interaktif berbagai skenario langsung di hadapan juri.

---

## 🛡️ Poin Kunci Keamanan & Privasi untuk Pertanyaan Juri

1. **Prinsip Least Privilege & Shadow DOM:** 
   Widget avatar berada dalam *closed Shadow DOM*, mencegah situs web nakal membaca atau memanipulasi peringatan keamanan.
2. **Kepatuhan UU PDP No. 27/2022:**
   TRASCO tidak merekam isi chat atau browsing secara menyeluruh; hanya potongan anonim dan hash SHA256 yang diproses saat pemindaian diaktifkan oleh pengguna.
3. **Hybrid Risk Engine:**
   Kombinasi aturan deterministik keamanan siber (Shannon entropy, regex pola rekening/OTP lokal) + Gemini Multimodal Vision AI menjamin akurasi tinggi dan minim halusinasi.


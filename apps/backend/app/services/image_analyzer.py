import json
import logging
from typing import Dict, Any, Optional, Tuple
from app.core.config import settings
from app.schemas.detection import ErrorDetail

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False

IMAGE_SYSTEM_PROMPT = """
Anda adalah TRASCO Image Forensics & Visual Scam Detector AI, sistem pakar pendeteksi penipuan visual dan rekayasa grafis digital di Indonesia.

Cakupan Deteksi:
1. Poster/Brosur Giveaway, Undian Palsu, Lowongan Kerja Palsu, dan Modus Investasi Bodong.
2. Tangkapan layar chat rekayasa (fake chat WhatsApp/Telegram mengatasnamakan instansi resmi, CS bank, atau pejabat).
3. Modus APK berbahaya bertarget (brosur undangan pernikahan digital/paket kurir/surat tilang palsu).
4. Pemalsuan dokumen, kwitansi, atau bukti transfer perbankan/e-wallet fiktif (fake transfer slip BCA, BRI, Mandiri, BNI, Dana, GoPay, OVO, QRIS).
5. Phishing visual / QRIS palsu (QRIS tempelan di masjid/toko, login page perbankan palsu dalam bentuk tangkapan layar).

Periksa:
1. Konten teks & klaim: Janji keuntungan tidak wajar, hadiah bombastis mencatut logo institusi resmi (BUMN, Kemensos, Bank), desakan transfer uang/DP klaim, iming-iming instan.
2. Manipulasi grafis: Font tidak seragam, tata letak logo tidak resmi/resolusi pecah, manipulasi visual teks/nominal.
3. Kredibilitas & legitimasi: Kontak yang dicantumkan (nomor WhatsApp pribadi alih-alih kanal resmi bercentang biru/domain resmi pemerintah/bank).
4. Tanda-tanda rekayasa digital / hasil editan aplikasi generator hoax.

Berikan output strictly dalam format JSON:
{
  "isScam": true/false,
  "confidenceScore": 0 to 100,
  "threatCategory": "SUSPICIOUS_PROMOTION" | "FAKE_TRANSFER_SLIP" | "SOCIAL_ENGINEERING" | "MALICIOUS_DOWNLOAD" | "SAFE",
  "summary": "Analisis visual dan kesimpulan indikasi penipuan dalam 1-2 kalimat lugas",
  "aiIndicators": [
    {
      "indicator": "Nama temuan visual / indikasi penipuan",
      "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
      "explanation": "Penjelasan detail mengapa elemen grafis atau isi pesan dalam gambar ini berbahaya/mencurigakan"
    }
  ],
  "recommendedActions": [
    "Langkah mitigasi konkret yang harus dilakukan pengguna (misal: Jangan kirim uang, Abaikan tawaran, Hubungi kontak resmi institusi)"
  ],
  "avatarMood": "IDLE_VIGILANT" | "CAUTION_ALERT" | "CRITICAL_SHIELD",
  "speechWarning": "Pesan peringatan suara avatar yang tegas dan edukatif dalam Bahasa Indonesia."
}
"""


def analyze_image_with_gemini(image_bytes: bytes, mime_type: str = "image/jpeg") -> Tuple[Optional[Dict[str, Any]], Optional[ErrorDetail], Optional[int]]:
    """
    Analyzes an already-validated image buffer using Gemini Vision multimodal.
    Strictly fail-closed: Never returns fake mock fallback.
    Returns: (ai_result_dict, error_detail, http_status_code)
    """
    if not GENAI_AVAILABLE or genai is None:
        logger.warning("Gemini Vision library 'google.generativeai' not installed.")
        return None, ErrorDetail(
            code="VISION_SERVICE_UNAVAILABLE",
            message="Pustaka google.generativeai tidak tersedia pada server."
        ), 503

    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is not configured in backend settings.")
        return None, ErrorDetail(
            code="AI_KEY_NOT_CONFIGURED",
            message="Kredensial GEMINI_API_KEY tidak dikonfigurasi di server backend."
        ), 503

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY, transport="rest")
        model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.1
            },
            system_instruction=IMAGE_SYSTEM_PROMPT
        )

        image_part = {
            "mime_type": mime_type,
            "data": image_bytes
        }

        import socket
        timeout_sec = getattr(settings, "GEMINI_IMAGE_TIMEOUT_SECONDS", 15.0)
        old_timeout = socket.getdefaulttimeout()
        try:
            socket.setdefaulttimeout(timeout_sec)
            # Upstream call with configurable timeout target
            response = model.generate_content(
                [
                    "Analisis citra/gambar berikut secara mendalam untuk mendeteksi potensi penipuan digital, poster palsu, atau bukti transfer fiktif:",
                    image_part
                ],
                request_options={"timeout": timeout_sec}
            )
        finally:
            socket.setdefaulttimeout(old_timeout)

        if not response or not response.text:
            return None, ErrorDetail(
                code="INVALID_AI_RESPONSE",
                message="Layanan AI mengembalikan respons kosong."
            ), 502

        try:
            parsed_json = json.loads(response.text)
            if not isinstance(parsed_json, dict) or "confidenceScore" not in parsed_json:
                return None, ErrorDetail(
                    code="INVALID_AI_RESPONSE",
                    message="Struktur JSON dari AI tidak lengkap atau tidak memiliki 'confidenceScore'."
                ), 502
            return parsed_json, None, 200
        except json.JSONDecodeError as jde:
            return None, ErrorDetail(
                code="INVALID_AI_RESPONSE",
                message=f"Output dari AI bukan format JSON yang sah: {str(jde)}"
            ), 502

    except Exception as e:
        err_msg = str(e).lower()
        logger.error("Error calling Gemini Vision API (%s).", type(e).__name__)
        if "deadline" in err_msg or "timed out" in err_msg or "timeout" in err_msg:
            return None, ErrorDetail(
                code="VISION_TIMEOUT",
                message=f"Permintaan analisis ke upstream Gemini Vision melebihi batas waktu {timeout_sec:.1f} detik."
            ), 504
        elif "quota" in err_msg or "429" in err_msg or "resourceexhausted" in err_msg:
            return None, ErrorDetail(
                code="AI_QUOTA_EXHAUSTED",
                message="Batas kuota harian atau rate-limit API Gemini terlampaui."
            ), 503
        else:
            return None, ErrorDetail(
                code="VISION_SERVICE_UNAVAILABLE",
                message="Gagal menghubungi layanan Gemini Vision."
            ), 503

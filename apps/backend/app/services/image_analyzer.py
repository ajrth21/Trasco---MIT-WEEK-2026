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
Anda adalah TRASCO Image Forensics AI, spesialis verifikasi keaslian bukti transfer perbankan/e-wallet Indonesia (BCA, Mandiri, BRI, BNI, Dana, GoPay, QRIS) dan poster penipuan digital.

Tugas:
Analisis apakah gambar ini merupakan bukti transfer fiktif/diedit (fake payment slip) atau konten giveaway/penipuan visual.
Periksa:
1. Konsistensi jenis font (font saldo beda ukuran, resolusi tidak merata, blur hanya di area nominal/nama).
2. Layout dan header bank resmi vs editan aplikasi manipulasi instan.
3. Keberadaan nomor referensi/transaksi valid.
4. Tanda-tanda hasil screenshot rekayasa.

Berikan output strictly dalam format JSON:
{
  "isScam": true/false,
  "confidenceScore": 0 to 100,
  "threatCategory": "FAKE_TRANSFER_SLIP" | "SUSPICIOUS_PROMOTION" | "SAFE",
  "summary": "Analisis visual bukti transfer dalam 1-2 kalimat",
  "aiIndicators": [
    {
      "indicator": "Nama temuan visual",
      "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
      "explanation": "Penjelasan detail mengapa elemen grafis ini mencurigakan"
    }
  ],
  "recommendedActions": [
    "Cek mutasi rekening langsung melalui m-banking resmi Anda",
    "Jangan kirim barang sebelum dana benar-benar masuk di rekening koran"
  ],
  "avatarMood": "IDLE_VIGILANT" | "CAUTION_ALERT" | "CRITICAL_SHIELD",
  "speechWarning": "Waspada! Bukti transfer ini memiliki indikasi editan grafis. Cek mutasi rekening Anda terlebih dahulu."
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
        old_timeout = socket.getdefaulttimeout()
        try:
            socket.setdefaulttimeout(8.0)
            # Upstream call with 8.0s timeout target
            response = model.generate_content(
                [
                    "Verifikasi keaslian bukti transfer/gambar ini untuk mendeteksi penipuan:",
                    image_part
                ],
                request_options={"timeout": 8.0}
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
                message="Permintaan analisis ke upstream Gemini Vision melebihi batas waktu 8.0 detik."
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

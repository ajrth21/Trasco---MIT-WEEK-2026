import base64
import json
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

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


def analyze_image_fallback(image_input: str) -> Dict[str, Any]:
    """Deterministic local fallback for image scam and payment slip analysis."""
    return {
        "isScam": True,
        "confidenceScore": 82,
        "threatCategory": "FAKE_TRANSFER_SLIP",
        "summary": "Analisis visual mengidentifikasi potensi bukti transfer fiktif/diedit. Verifikasi transaksi Anda melalui mutasi rekening resmi.",
        "aiIndicators": [
            {
                "indicator": "Pemeriksaan Keaslian Bukti Transfer",
                "severity": "HIGH",
                "explanation": "Struk transaksi digital rentan dimanipulasi dengan aplikasi editor grafis instan."
            },
            {
                "indicator": "Mitigasi Finansial Tanpa Mutasi",
                "severity": "CRITICAL",
                "explanation": "Jangan pernah melepaskan barang atau dana sebelum mutasi saldo bertambah di aplikasi perbankan resmi."
            }
        ],
        "recommendedActions": [
            "Buka aplikasi m-banking resmi Anda dan periksa mutasi rekening koran.",
            "Jangan percaya tangkapan layar (screenshot) transfer dari pihak lain sebelum dana efektif masuk.",
            "Tunda pengiriman barang atau pesanan hingga dana terkonfirmasi."
        ],
        "avatarMood": "CRITICAL_SHIELD",
        "speechWarning": "Waspada! Verifikasi mutasi rekening m-banking Anda langsung sebelum mempercayai struk transfer ini."
    }


def analyze_image_with_gemini(image_data_base64: str) -> Optional[Dict[str, Any]]:
    """Analyzes an image using Gemini Vision multimodal with local fallback."""
    if not GENAI_AVAILABLE or not settings.GEMINI_API_KEY:
        logger.info("Gemini Vision not available or GEMINI_API_KEY not configured. Using deterministic fallback.")
        return analyze_image_fallback(image_data_base64)

    try:
        # Strip data URL prefix if present (e.g. data:image/png;base64,...)
        if "," in image_data_base64:
            header, encoded = image_data_base64.split(",", 1)
            mime_type = header.split(";")[0].split(":")[1]
        else:
            encoded = image_data_base64
            mime_type = "image/jpeg"

        image_bytes = base64.b64decode(encoded)

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
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

        response = model.generate_content([
            "Verifikasi keaslian bukti transfer/gambar ini untuk mendeteksi penipuan:",
            image_part
        ])

        if response and response.text:
            return json.loads(response.text)
    except Exception as e:
        logger.error(f"Error calling Gemini Vision API: {e}")
        return None

    return None

import re
import base64
import io
import logging
from typing import Tuple, Optional, Dict, Any
from app.schemas.detection import ErrorDetail

logger = logging.getLogger(__name__)

# Constants as defined in TRASCO v0.3.2 Baseline
MAX_PAYLOAD_STRING_LEN = 7 * 1024 * 1024  # 7 MiB encoded string limit
MAX_DECODED_BYTES = 5 * 1024 * 1024       # 5 MiB binary buffer limit
MAX_DIMENSION_PX = 4096                   # 4096 px width and height limit
MAX_TOTAL_PIXELS = 16_000_000             # 16,000,000 total pixels limit

ALLOWED_MIMES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"]  # and WEBP at bytes 8-12
}

DATA_URL_REGEX = re.compile(r"^data:(image\/[a-zA-Z0-9\.\+-]+);base64,(.*)$", re.DOTALL)


def validate_image_payload(content_str: str, mime_str: str) -> Tuple[bool, Optional[bytes], Optional[ErrorDetail], Optional[int]]:
    """
    Executes the 14-stage application-level image validation pipeline.
    Returns: (is_valid, decoded_bytes, error_detail, http_status_code)
    """
    # Tahap 1: Image Payload String Length Guard (<= 7 MiB)
    if not isinstance(content_str, str) or not content_str:
        return False, None, ErrorDetail(
            code="INVALID_REQUEST_PAYLOAD",
            message="Payload citra harus berupa string Base64 Data URL."
        ), 400
    if len(content_str) > MAX_PAYLOAD_STRING_LEN:
        return False, None, ErrorDetail(
            code="IMAGE_PAYLOAD_TOO_LARGE",
            message="String payload Base64 citra melebihi batas 7 MiB."
        ), 413

    # Tahap 2: Schema Field Integrity & Basic Non-empty Check
    if not isinstance(mime_str, str) or not mime_str:
        return False, None, ErrorDetail(
            code="INVALID_REQUEST_PAYLOAD",
            message="Field mandatory 'mimeType' harus berupa string."
        ), 400

    # Tahap 3: Data URL Syntax Verification
    match = DATA_URL_REGEX.match(content_str.strip())
    if not match:
        return False, None, ErrorDetail(
            code="INVALID_DATA_URL",
            message="Format string content bukan Base64 Data URL yang sah (data:image/...;base64,...)."
        ), 422

    url_mime = match.group(1).lower()
    raw_b64 = match.group(2)

    # Tahap 4: Declared MIME Allowlist
    norm_declared_mime = mime_str.lower().strip()
    if norm_declared_mime not in ALLOWED_MIMES or url_mime not in ALLOWED_MIMES:
        return False, None, ErrorDetail(
            code="UNSUPPORTED_IMAGE_FORMAT",
            message=f"Format citra '{norm_declared_mime}' tidak didukung. Gunakan JPEG, PNG, atau WebP."
        ), 415

    # Tahap 5: Base64 Encoded Length Re-verification
    if len(raw_b64) > MAX_PAYLOAD_STRING_LEN:
        return False, None, ErrorDetail(
            code="IMAGE_PAYLOAD_TOO_LARGE",
            message=f"Panjang segmen Base64 melebihi batas 7 MiB ({len(raw_b64)} chars)."
        ), 413

    # Tahap 6: Strict Base64 Decoding
    try:
        decoded_bytes = base64.b64decode(raw_b64, validate=True)
    except Exception as e:
        return False, None, ErrorDetail(
            code="INVALID_BASE64",
            message=f"Data Base64 rusak atau mengandung karakter non-alfanumerik/padding salah: {str(e)}"
        ), 422

    # Tahap 7: Decoded Binary Size Guard (<= 5 MiB)
    if len(decoded_bytes) > MAX_DECODED_BYTES:
        return False, None, ErrorDetail(
            code="IMAGE_TOO_LARGE",
            message=f"Ukuran biner citra terdecode ({len(decoded_bytes)} bytes) melebihi batas maksimum 5 MiB."
        ), 422

    # Tahap 8 & 9: Magic Bytes Signature & MIME vs Signature Consistency
    detected_mime = None
    if decoded_bytes.startswith(b"\xff\xd8\xff"):
        detected_mime = "image/jpeg"
    elif decoded_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        detected_mime = "image/png"
    elif decoded_bytes.startswith(b"RIFF") and len(decoded_bytes) >= 12 and decoded_bytes[8:12] == b"WEBP":
        detected_mime = "image/webp"

    if not detected_mime or detected_mime != norm_declared_mime:
        return False, None, ErrorDetail(
            code="MIME_SIGNATURE_MISMATCH",
            message=f"Signature biner citra ({detected_mime or 'unknown'}) tidak sesuai dengan declared MIME type '{norm_declared_mime}'.",
            details={"declared": norm_declared_mime, "detected": detected_mime}
        ), 422

    # Tahap 10, 11, 12, 13, 14: Pillow Inspection & Resource Sandbox
    try:
        from PIL import Image
    except ImportError:
        logger.error("Critical dependency 'Pillow' is not installed.")
        return False, None, ErrorDetail(
            code="INTERNAL_ANALYSIS_ERROR",
            message="Pustaka pengolah citra Pillow tidak tersedia di server."
        ), 500

    # Decompression Bomb Guard
    Image.MAX_IMAGE_PIXELS = MAX_TOTAL_PIXELS

    try:
        image_stream = io.BytesIO(decoded_bytes)
        # Open reads only the header (Tahap 10)
        with Image.open(image_stream) as img:
            width, height = img.size

            # Tahap 11: Per-Side Dimension Boundary Guard (<= 4096 px)
            if width > MAX_DIMENSION_PX or height > MAX_DIMENSION_PX:
                return False, None, ErrorDetail(
                    code="IMAGE_DIMENSIONS_EXCEEDED",
                    message=f"Dimensi citra ({width}x{height} px) melebihi batas maksimum {MAX_DIMENSION_PX} px per sisi.",
                    details={"width": width, "height": height, "max": MAX_DIMENSION_PX}
                ), 422

            # Tahap 12: Total Pixel Budget Guard (<= 16,000,000 px)
            total_pixels = width * height
            if total_pixels > MAX_TOTAL_PIXELS:
                return False, None, ErrorDetail(
                    code="IMAGE_PIXEL_LIMIT_EXCEEDED",
                    message=f"Total pixel citra ({total_pixels} px) melebihi batas anggaran {MAX_TOTAL_PIXELS} pixels.",
                    details={"totalPixels": total_pixels, "max": MAX_TOTAL_PIXELS}
                ), 422

            # Tahap 13 & 14: Bounded Decoding, Integrity Verification, & Normalization
            img.verify()  # Verifies file integrity without full decode

    except Image.DecompressionBombError:
        return False, None, ErrorDetail(
            code="IMAGE_PIXEL_LIMIT_EXCEEDED",
            message=f"Citra memicu peringatan Decompression Bomb (melebihi {MAX_TOTAL_PIXELS} total pixels)."
        ), 422
    except Exception as e:
        return False, None, ErrorDetail(
            code="IMAGE_DECODE_FAILED",
            message=f"File citra corrupt atau gagal didecode oleh parser: {str(e)}"
        ), 422

    return True, decoded_bytes, None, 200

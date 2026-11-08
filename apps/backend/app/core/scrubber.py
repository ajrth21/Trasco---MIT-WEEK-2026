import re


def scrub_pii(text: str) -> str:
    """Redacts Personally Identifiable Information (PII) before storage or logging.
    Compliant with Indonesia's UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi.
    """
    if not text:
        return ""

    # Redact 16-digit NIK / Credit Card numbers
    text = re.sub(r"\b\d{16}\b", "[NIK_DISENSOR]", text)

    # --- ISSUE-SEC-03: Indonesian phone number redaction ---
    # Supports formats: 081234567890, 0812-3456-7890, 0812 3456 7890,
    # +6281234567890, +62812-3456-7890, +62 812 3456 7890, 628123456789
    # The pattern requires a leading 0 or +62/62 followed by 8[1-9],
    # then 7-10 more digits (with optional hyphens or spaces as separators).
    # This avoids masking short unrelated numbers like dates or prices.
    text = re.sub(
        r"(?:\+?62[\s-]?|0)8[1-9](?:[\s-]?\d){7,10}",
        "[NO_HP_DISENSOR]",
        text
    )

    # Redact email addresses
    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL_DISENSOR]", text)

    # Redact 6-digit verification / OTP codes
    text = re.sub(r"\b\d{6}\b", "[OTP_DISENSOR]", text)

    # Redact 10-14 digit bank account numbers
    text = re.sub(r"\b\d{10,14}\b", "[NO_REK_DISENSOR]", text)

    return text


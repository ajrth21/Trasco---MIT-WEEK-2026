import re


def scrub_pii(text: str) -> str:
    """Redacts Personally Identifiable Information (PII) before storage or logging.
    Compliant with Indonesia's UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi.
    """
    if not text:
        return ""

    # Redact 16-digit NIK / Credit Card numbers
    text = re.sub(r"\b\d{16}\b", "[NIK_DISENSOR]", text)

    # Redact Indonesian phone numbers (08... or +628...)
    text = re.sub(r"\b(?:\+?62|0)8[1-9][0-9]{7,10}\b", "[NO_HP_DISENSOR]", text)

    # Redact email addresses
    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL_DISENSOR]", text)

    # Redact 6-digit verification / OTP codes
    text = re.sub(r"\b\d{6}\b", "[OTP_DISENSOR]", text)

    # Redact 10-14 digit bank account numbers
    text = re.sub(r"\b\d{10,14}\b", "[NO_REK_DISENSOR]", text)

    return text


import re
import math
from urllib.parse import urlparse
from typing import Dict, List, Any


OFFICIAL_BRAND_DOMAINS = {
    "bca": ["bca.co.id", "klikbca.com", "bca.com", "mybca.bca.co.id"],
    "klikbca": ["klikbca.com"],
    "bri": ["bri.co.id", "ib.bri.co.id", "brimo.bri.co.id"],
    "bni": ["bni.co.id", "bni-life.co.id"],
    "mandiri": ["bankmandiri.co.id", "livinbymandiri.id", "mandiri.co.id"],
    "dana": ["dana.id"],
    "gopay": ["gopay.co.id", "gojek.com"],
    "ovo": ["ovo.id"],
    "shopeepay": ["shopee.co.id"],
    "prakerja": ["prakerja.go.id"],
    "kemnaker": ["kemnaker.go.id"],
    "pln": ["pln.co.id"],
    "telkomsel": ["telkomsel.com"],
    "indodax": ["indodax.com"]
}

SUSPICIOUS_TLDS = {
    ".xyz", ".top", ".tk", ".ml", ".cf", ".icu", ".buzz", 
    ".cam", ".club", ".work", ".site", ".online", ".vip", ".cc"
}

SCAM_TEXT_PATTERNS = [
    {
        "id": "OTP_THEFT",
        "regex": r"(?i)(kode\s*(?:otp|rahasia|sms)|minta\s*otp|kirimkan\s*otp|6\s*digit\s*kode|pin\s*atm|kata\s*sandi\s*anda)",
        "indicator": "Permintaan Informasi Rahasia (OTP / PIN)",
        "severity": "CRITICAL",
        "explanation": "Pesan secara eksplisit meminta kode OTP atau PIN yang merupakan kredensial keamanan pribadi."
    },
    {
        "id": "JOB_TASK_SCAM",
        "regex": r"(?i)(kerja\s*paruh\s*waktu|freelance\s*like|like\s*video|komisi\s*(?:harian|\d+rb|\d+k)|tugas\s*like\s*(?:tiktok|youtube)|like\s*dan\s*subscribe|gaji\s*\d+\s*(?:ribu|rb|jt)\s*per\s*hari)",
        "indicator": "Modus Lowongan Kerja Fiktif (Like & Subscribe)",
        "severity": "HIGH",
        "explanation": "Pola janji upah instan hanya dengan like/subscribe adalah modus klasik penipuan digital."
    },
    {
        "id": "DEPOSIT_SCAM",
        "regex": r"(?i)(deposit(?:\s*(?:awal|\d+|uang|dana|saldo|rp|rupiah|jaminan))?|uang\s*jaminan|biaya\s*pendaftaran|setor\s*(?:dana|uang)|transfer\s*dulu|kembali\s*berkali\s*lipat)",
        "indicator": "Tuntutan Deposit / Uang Muka",
        "severity": "CRITICAL",
        "explanation": "Pesan meminta pengiriman uang jaminan/deposit di muka dengan dalih keuntungan besar."
    },
    {
        "id": "FAKE_GIVEAWAY",
        "regex": r"(?i)(selamat[\s,!.]*anda\s*(?:terpilih|menang)|undian\s*(?:berhadiah|\d+jt|\d+juta)|klaim\s*hadiah|dana\s*kaget|saldo\s*gratis|hadiah\s*(?:ratusan|jutaan|\d+jt))",
        "indicator": "Klaim Hadiah / Undian Fiktif",
        "severity": "HIGH",
        "explanation": "Pesan memanipulasi keserakahan korban dengan mengklaim hadiah fiktif tanpa dasar partisipasi."
    },
    {
        "id": "MALICIOUS_APK",
        "regex": r"(?i)(surat\s*tilang\.apk|undangan\s*(?:pernikahan|nikah)\.apk|resi\s*(?:paket|jnt|jne|pos)\.apk|foto\s*paket\.apk|\.apk)",
        "indicator": "Penyebaran File APK Berbahaya (Malware Android)",
        "severity": "CRITICAL",
        "explanation": "Pesan membujuk korban untuk menginstal file paket .apk yang biasanya mencuri SMS OTP dan mobile banking."
    },
    {
        "id": "URGENCY_MANIPULATION",
        "regex": r"(?i)(segera\s*sebelum\s*(?:diblokir|hangus)|dalam\s*(?:5|10|15|30)\s*menit|rekening\s*(?:dibekukan|ditutup)|tindakan\s*hukum)",
        "indicator": "Manipulasi Psikologis Urgensi / Panik",
        "severity": "MEDIUM",
        "explanation": "Pesan menciptakan kepanikan buatan agar korban tergesa-gesa tanpa berpikir rasional."
    },
    {
        "id": "BANK_TRANSFER_REQUEST",
        "regex": r"(?i)(transfer\s*ke\s*(?:rek|rekening)|no(?:mor)?\s*rek(?:ening)?\s*:?\s*\d{8,16}|an\s*:\s*[A-Z\s]+)",
        "indicator": "Instruksi Transfer ke Rekening Pribadi",
        "severity": "MEDIUM",
        "explanation": "Pesan memuat instruksi spesifik untuk memindahkan dana ke rekening perorangan."
    }
]


def calculate_shannon_entropy(text: str) -> float:
    """Calculates the Shannon entropy of a string."""
    if not text:
        return 0.0
    entropy = 0.0
    length = len(text)
    freq = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1
    for count in freq.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy


def analyze_url_heuristics(url_str: str) -> Dict[str, Any]:
    """Analyzes a URL using deterministic cybersecurity heuristics."""
    indicators: List[Dict[str, str]] = []
    heuristic_score = 0
    threat_category = "SAFE"

    # Prepend schema if missing for parsing
    if not url_str.startswith(("http://", "https://")):
        parsed = urlparse("https://" + url_str)
    else:
        parsed = urlparse(url_str)

    hostname = (parsed.hostname or "").lower()
    path = (parsed.path or "").lower()

    # 1. IP Address as host
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname):
        heuristic_score += 40
        indicators.append({
            "indicator": "Host Berupa IP Address",
            "severity": "CRITICAL",
            "explanation": "Website resmi bank/lembaga tidak pernah menggunakan IP telanjang tanpa nama domain tepercaya."
        })
        threat_category = "PHISHING_URL"

    # 2. Suspicious TLD
    for tld in SUSPICIOUS_TLDS:
        if hostname.endswith(tld):
            heuristic_score += 25
            indicators.append({
                "indicator": f"Domain Menggunakan TLD Berisiko Tinggi ({tld})",
                "severity": "HIGH",
                "explanation": "Domain berbiaya murah ini memiliki reputasi tinggi sering dimanfaatkan pelaku penipuan."
            })
            break

    # 3. High Hostname Entropy (Random string generation)
    host_without_tld = hostname.split(".")[0] if "." in hostname else hostname
    entropy = calculate_shannon_entropy(host_without_tld)
    if entropy > 3.8 and len(host_without_tld) > 12:
        heuristic_score += 20
        indicators.append({
            "indicator": "Nama Domain Acak (Algorithmic DGA / High Entropy)",
            "severity": "MEDIUM",
            "explanation": "Nama domain tampak seperti susunan karakter acak yang umum dibuat oleh bot penipuan."
        })

    # 4. Indonesian Brand Typosquatting / Impersonation
    for brand, official_domains in OFFICIAL_BRAND_DOMAINS.items():
        if brand in hostname:
            is_official = any(hostname == off or hostname.endswith("." + off) for off in official_domains)
            if not is_official:
                heuristic_score += 45
                indicators.append({
                    "indicator": f"Indikasi Penyamaran Merek Resmi ({brand.upper()})",
                    "severity": "CRITICAL",
                    "explanation": f"Nama domain mencantumkan '{brand}' tetapi bukan domain resmi lembaga bersangkutan."
                })
                threat_category = "TYPOSQUATTING"
                break

    # 5. Phishing Keywords in Path or Host
    phish_keywords = ["login", "verifikasi", "klaim", "hadiah", "otp", "bantuan", "update-data", "secure"]
    matched_kws = [kw for kw in phish_keywords if kw in hostname or kw in path]
    if matched_kws and heuristic_score > 0:
        heuristic_score += 15
        indicators.append({
            "indicator": f"Kata Kunci Mencurigakan ({', '.join(matched_kws)})",
            "severity": "MEDIUM",
            "explanation": "URL mengandung parameter penipuan identitas atau klaim tidak wajar."
        })

    return {
        "heuristicScore": min(heuristic_score, 100),
        "indicators": indicators,
        "threatCategory": threat_category
    }


def analyze_text_heuristics(text: str) -> Dict[str, Any]:
    """Scans text content for known Indonesian scam patterns."""
    indicators: List[Dict[str, str]] = []
    heuristic_score = 0
    threat_category = "SAFE"

    for pattern in SCAM_TEXT_PATTERNS:
        match = re.search(pattern["regex"], text)
        if match:
            sev = pattern["severity"]
            weight = 40 if sev == "CRITICAL" else (25 if sev == "HIGH" else 15)
            heuristic_score += weight
            indicators.append({
                "indicator": pattern["indicator"],
                "severity": pattern["severity"],
                "explanation": pattern["explanation"]
            })
            if pattern["id"] in ["OTP_THEFT", "DEPOSIT_SCAM", "MALICIOUS_APK"]:
                threat_category = pattern["id"]
            elif threat_category == "SAFE":
                threat_category = pattern["id"]

    return {
        "heuristicScore": min(heuristic_score, 100),
        "indicators": indicators,
        "threatCategory": threat_category
    }

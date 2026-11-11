import re
import math
from urllib.parse import parse_qsl, urlparse
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

# Known common URL shortener domains (indicates obfuscated destination)
URL_SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "t.co", "s.id", "cutt.ly",
    "is.gd", "shorturl.at", "rb.gy", "rebrand.ly", "linktr.ee", "ln.run"
}

# Lookalike homoglyph mapping: common digit/symbol to Latin substitutions
LOOKALIKE_CHAR_MAP = {
    '0': ['o'],
    '1': ['l', 'i'],
    '3': ['e'],
    '4': ['a'],
    '5': ['s'],
    '7': ['t'],
    '8': ['b'],
    '@': ['a'],
    'vv': ['w'],
}

SCAM_TEXT_PATTERNS = [
    # 1. Existing Core Threats
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
    },

    # 2. Sprint 3 Expansion: PINJOL_ILLEGAL
    {
        "id": "PINJOL_ILLEGAL",
        "regex": r"(?i)(pinjol\s*(?:langsung\s*cair|tanpa\s*ojk|ilegal)|dana\s*cepat\s*tanpa\s*ktp|pinjaman\s*(?:kilat|online)\s*tanpa\s*(?:jaminan|syarat|bi\s*checking)|bunga\s*(?:harian\s*\d+%|rendah\s*pasti\s*cair))",
        "indicator": "Penawaran Pinjaman Online Ilegal / Tanpa Izin OJK",
        "severity": "HIGH",
        "explanation": "Pesan mempromosikan pinjaman online tanpa verifikasi resmi/OJK yang berisiko pemerasan bunga ekstrem."
    },
    {
        "id": "PINJOL_ILLEGAL",
        "regex": r"(?i)((?:sebar|sebarkan|menyebarkan)\s*(?:seluruh\s*)?(?:data|foto|ktp|kontak)|(?:sebar|sebarkan|menyebarkan)\s*(?:ke\s*)?(?:seluruh|semua)\s*kontak|(?:data|foto|ktp)\s*(?:kamu|anda|pribadi)?\s*(?:akan\s*)?(?:kami\s*)?(?:sebar|sebarkan)|hubungi\s*(?:seluruh|semua)\s*kontak|permalukan\s*anda|teror\s*(?:kontak|keluarga))",
        "indicator": "Intimidasi Penagihan & Ancaman Sebar Data Pribadi",
        "severity": "CRITICAL",
        "explanation": "Pesan memuat pola intimidasi khas penagihan pinjol ilegal yang mengancam penyebaran data pribadi korban."
    },
    {
        "id": "PINJOL_ILLEGAL",
        "regex": r"(?i)(biaya\s*(?:admin|pencairan|materai)\s*(?:di\s*awal|dimuka|transfer\s*dulu)|bayar\s*administrasi\s*sebelum\s*dana\s*cair)",
        "indicator": "Pungutan Biaya Administrasi Sebelum Pencairan Pinjaman",
        "severity": "CRITICAL",
        "explanation": "Pinjaman legal tidak pernah meminta peminjam mentransfer biaya administrasi di muka sebelum dana dicairkan."
    },

    # 3. Sprint 3 Expansion: INVESTMENT_FRAUD
    {
        "id": "INVESTMENT_FRAUD",
        "regex": r"(?i)(profit\s*(?:pasti|harian|konsisten|\d+%\s*(?:per\s*hari|setiap\s*hari))|keuntungan\s*(?:pasti|tetap)\s*tanpa\s*risiko|anti\s*loss|garansi\s*modal\s*kembali\s*100%)",
        "indicator": "Klaim Investasi Bodong (Janji Profit Pasti Tanpa Risiko)",
        "severity": "CRITICAL",
        "explanation": "Setiap instrumen investasi resmi memiliki risiko fluktuasi; janji keuntungan pasti harian adalah ciri utama skema Ponzi."
    },
    {
        "id": "INVESTMENT_FRAUD",
        "regex": r"(?i)(titip\s*dana\s*(?:trading|investasi|crypto|kripto)|robot\s*trading\s*(?:otomatis\s*profit|pasti\s*cuan)|(?:skema\s*ponzi|money\s*game)\s*(?:berkedok|penipuan|resmi|gabung|daftar|modal))",
        "indicator": "Skema Titip Dana / Robot Trading Fiktif",
        "severity": "HIGH",
        "explanation": "Penawaran pengelolaan titip dana pribadi dengan jaminan keuntungan tinggi adalah modus investasi ilegal."
    },
    {
        "id": "INVESTMENT_FRAUD",
        "regex": r"(?i)(ajak\s*(?:\d+|teman|anggota|member)\s*dapat\s*(?:komisi|bonus|keuntungan)|tambah\s*deposit\s*agar\s*(?:profit|dana)\s*(?:bisa|dapat)\s*ditarik)",
        "indicator": "Manipulasi Rekrutmen Anggota (Skema Piramida) & Penahanan Penarikan",
        "severity": "HIGH",
        "explanation": "Pola mewajibkan penambahan deposit untuk menarik profit merupakan indikator penipuan investasi macet."
    },

    # 4. Sprint 3 Expansion: EMERGENCY_IMPERSONATION
    {
        "id": "EMERGENCY_IMPERSONATION",
        "regex": r"(?i)((?:anak|ibu|ayah|mama|papa|keluarga|suami|istri)\s*(?:anda\s*)?(?:mengalami\s*)?kecelakaan|sedang\s*kritis\s*di\s*rumah\s*sakit|butuh\s*(?:biaya|operasi|darah)\s*segera|transfer\s*biaya\s*medis)",
        "indicator": "Rekayasa Sosial Skenario Kecelakaan Darurat Keluarga",
        "severity": "CRITICAL",
        "explanation": "Pesan memanfaatkan kepanikan korban dengan memalsukan kondisi kecelakaan darurat anggota keluarga."
    },
    {
        "id": "EMERGENCY_IMPERSONATION",
        "regex": r"(?i)((?:ditahan|tertangkap|urusan\s*dengan)\s*polisi|kantor\s*polisi\s*(?:kasus\s*narkoba|tilang)|uang\s*(?:damai|tebusan|jaminan\s*polisi)|jangan\s*(?:kasih\s*tahu|bilang|hubungi)\s*(?:siapa-siapa|keluarga))",
        "indicator": "Skenario Penangkapan Polisi & Permintaan Tebusan Rahasia",
        "severity": "CRITICAL",
        "explanation": "Pesan menakut-nakuti korban dengan dalih ditangkap polisi dan meminta uang tebusan serta melarang konfirmasi."
    },
    {
        "id": "EMERGENCY_IMPERSONATION",
        "regex": r"(?i)(ini\s*(?:nomor|no)\s*baru\s*(?:mama|ibu|ayah|papa|anakmu)|hp\s*(?:lama\s*)?(?:rusak|hilang|jatuh)|simpan\s*nomor\s*(?:ini|baru)\s*ya)",
        "indicator": "Klaim Nomor Baru Menyamar Sebagai Anggota Keluarga",
        "severity": "MEDIUM",
        "explanation": "Modus penyamaran nomor baru sebelum melancarkan permintaan transfer dana darurat."
    },

    # 5. JUDI_ONLINE / SLOT_SCAM (Judol & Obfuscated Slot Promotion)
    {
        "id": "JUDI_ONLINE",
        "regex": r"(?i)(?:slot\s*(?:gacor|online|resmi|zeus|pragmatic|server)|(?:mahjong|pg\s*soft|pgsoft|pragmatic\s*play)|(?:pasti\s*(?:dikasih\s*)?menang|pasti\s*jp|auto\s*max\s*win|max\s*win)|(?:saldo\s*\d+k?\s*(?:utk|untuk)?\s*main|kasih\s*kamu\s*saldo|bagi2\s*saldo)|(?:w\.?d\s*\d+|withdraw\s*(?:lancar|jutaan|cepat))|(?:dp|depo)\s*(?:utk|untuk)?\s*klaim|bonus\s*new\s*member|klaim\s*bns|bonus\s*deposit)",
        "indicator": "Promosi Judi Online & Jebakan Deposit Slot (Judol)",
        "severity": "CRITICAL",
        "explanation": "Pesan mempromosikan judi online ilegal (slot/mahjong/deposit bonus) yang kerap menggunakan taktik manipulasi iming-iming saldo dan tautan terselubung."
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


def detect_homoglyph_brand(hostname: str) -> str:
    """Detects brand impersonation using character substitutions (digits/symbols replacing letters).
    Example: 'kl1kbca' -> 'klikbca', 'm4ndiri' -> 'mandiri'.
    Returns brand name if homoglyph is detected, or empty string.
    """
    raw_host = hostname.lower()

    # Try multiple substitution variations
    candidate_variations = [raw_host]
    for char, reps in LOOKALIKE_CHAR_MAP.items():
        if char in raw_host:
            new_variations = []
            for base in candidate_variations:
                for rep in reps:
                    new_variations.append(base.replace(char, rep))
            candidate_variations.extend(new_variations)

    for brand in OFFICIAL_BRAND_DOMAINS:
        for norm in candidate_variations:
            # If the normalized variant matches a brand but wasn't exact official domain
            if brand in norm and brand not in raw_host:
                return brand
            # Also check if it mimics full brand keyword like 'klikbca'
            if brand in ["klikbca"] and "bca" in raw_host and "klikbca" not in raw_host and "klikbca" in norm:
                return brand
    return ""


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

    # Decode international/punycode domain safely
    try:
        raw_host = (parsed.hostname or "").lower()
        # Handle punycode (e.g. xn--...)
        hostname = raw_host.encode("idna").decode("ascii") if raw_host else ""
    except Exception:
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

    # 2. URL Shortener Detection (Risk signal without external network calls)
    is_shortener = any(hostname == s or hostname.endswith("." + s) for s in URL_SHORTENER_DOMAINS)
    if is_shortener:
        heuristic_score += 25
        indicators.append({
            "indicator": f"Tautan Menggunakan Layanan Pemendek URL ({hostname})",
            "severity": "HIGH",
            "explanation": "Layanan shortener menyembunyikan alamat situs sebenarnya dan kerap digunakan untuk menyelubungi link phishing."
        })
        if threat_category == "SAFE":
            threat_category = "PHISHING_URL"

    # 3. Suspicious TLD
    for tld in SUSPICIOUS_TLDS:
        if hostname.endswith(tld):
            heuristic_score += 25
            indicators.append({
                "indicator": f"Domain Menggunakan TLD Berisiko Tinggi ({tld})",
                "severity": "HIGH",
                "explanation": "Domain berbiaya murah ini memiliki reputasi tinggi sering dimanfaatkan pelaku penipuan."
            })
            break

    # 4. High Hostname Entropy (Random string generation)
    host_without_tld = hostname.split(".")[0] if "." in hostname else hostname
    entropy = calculate_shannon_entropy(host_without_tld)
    if entropy > 3.8 and len(host_without_tld) > 12:
        heuristic_score += 20
        indicators.append({
            "indicator": "Nama Domain Acak (Algorithmic DGA / High Entropy)",
            "severity": "MEDIUM",
            "explanation": "Nama domain tampak seperti susunan karakter acak yang umum dibuat oleh bot penipuan."
        })

    # 5. Homoglyph & Lookalike Typosquatting (Evaluated first to catch disguised brands like kl1kbca)
    homoglyph_brand = detect_homoglyph_brand(hostname)
    if homoglyph_brand:
        heuristic_score += 50
        indicators.append({
            "indicator": f"Substitusi Karakter Homoglif / Peniruan Visual ({homoglyph_brand.upper()})",
            "severity": "CRITICAL",
            "explanation": f"Domain menggunakan angka atau karakter pengganti visual untuk meniru merek resmi '{homoglyph_brand}'."
        })
        threat_category = "TYPOSQUATTING"
    else:
        # 6. Indonesian Brand Direct Typosquatting
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

    # 7. Reward and gift-claim URL patterns
    reward_terms = {"bonus", "hadiah", "gift", "redeem", "reward", "claim", "klaim", "jackpot"}
    normalized_host = re.sub(r"[^a-z0-9]", "", hostname)
    normalized_path = re.sub(r"[^a-z0-9]", "", path)
    host_reward_terms = {term for term in reward_terms if term in normalized_host}
    path_reward_terms = {term for term in reward_terms if term in normalized_path}
    query_keys = {key.lower() for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}
    has_referral_registration = bool(query_keys & {"register", "registration", "daftar"}) and bool(
        query_keys & {"ref", "referral", "refer"}
    )
    reward_signup_pattern = bool(host_reward_terms) and has_referral_registration
    gift_redemption_pattern = {"redeem", "gift"}.issubset(path_reward_terms)

    if reward_signup_pattern or gift_redemption_pattern:
        heuristic_score += 35
        pattern_name = "Bonus referral dan pendaftaran" if reward_signup_pattern else "Penukaran hadiah/reward"
        indicators.append({
            "indicator": f"Pola URL promosi berisiko ({pattern_name})",
            "severity": "MEDIUM",
            "explanation": "Kombinasi klaim bonus/hadiah dengan pendaftaran referral atau halaman penukaran perlu diverifikasi melalui kanal resmi; pola ini bukan bukti tunggal bahwa situs berbahaya."
        })
        if threat_category == "SAFE":
            threat_category = "SUSPICIOUS_PROMOTION"

    # 8. Phishing Keywords in Path or Host
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


def deobfuscate_indonesian_scam_text(text: str) -> str:
    """Normalizes leetspeak, interstitial punctuation, and obfuscation commonly used
    by scammers to bypass regex filters (e.g., 'SAL.D0 50K UTK M\'A1.N', 'PGS0F-T', 'MA,XW,1N').
    """
    if not text:
        return ""
    deobf = re.sub(r"(?<=[a-zA-Z0-9])[.,'_-](?=[a-zA-Z0-9])", "", text)

    leet_map = str.maketrans({
        '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '8': 'b', '@': 'a', '$': 's'
    })

    def normalize_token(match: re.Match[str]) -> str:
        token = match.group(0)
        if sum(char.isalpha() for char in token) < 2:
            return token.lower()
        return token.lower().translate(leet_map)

    return re.sub(r"[a-zA-Z0-9@$]+", normalize_token, deobf)


def analyze_text_heuristics(text: str) -> Dict[str, Any]:
    """Scans text content for known Indonesian scam patterns."""
    indicators: List[Dict[str, str]] = []
    heuristic_score = 0
    threat_category = "SAFE"

    # Check if text contains actual URL shortener link (e.g. bit.ly/..., s.id/..., ln.run/...)
    # This acts as an obfuscation risk signal when combined with other indicators
    shortener_link_pattern = r"(?i)(?:https?://)?(?:www\.)?(?:bit\.ly|tinyurl\.com|t\.co|s\.id|cutt\.ly|is\.gd|shorturl\.at|rb\.gy|rebrand\.ly|ln\.run)/[a-zA-Z0-9_\-]+"
    has_shortener_link = bool(re.search(shortener_link_pattern, text))
    if has_shortener_link:
        heuristic_score += 25
        indicators.append({
            "indicator": "Tautan Menggunakan Layanan Pemendek URL (Obfuscated Link)",
            "severity": "HIGH",
            "explanation": "Pesan memuat tautan shortener yang menyamarkan alamat web tujuan sebenarnya."
        })
        threat_category = "PHISHING_URL"

    # Priority mapping for multiple threat matches
    category_weights = {
        "OTP_THEFT": 90,
        "MALICIOUS_APK": 85,
        "JUDI_ONLINE": 82,
        "EMERGENCY_IMPERSONATION": 80,
        "PINJOL_ILLEGAL": 75,
        "INVESTMENT_FRAUD": 70,
        "DEPOSIT_SCAM": 65,
        "JOB_TASK_SCAM": 60,
        "FAKE_GIVEAWAY": 50,
        "URGENCY_MANIPULATION": 40,
        "BANK_TRANSFER_REQUEST": 30,
        "SAFE": 0
    }

    current_highest_weight = 0
    normalized_text = deobfuscate_indonesian_scam_text(text)

    for pattern in SCAM_TEXT_PATTERNS:
        # Check both raw text and deobfuscated text
        match_raw = re.search(pattern["regex"], text)
        match_norm = re.search(pattern["regex"], normalized_text)
        if match_raw or match_norm:
            sev = pattern["severity"]
            weight = 40 if sev == "CRITICAL" else (25 if sev == "HIGH" else 15)
            heuristic_score += weight
            indicators.append({
                "indicator": pattern["indicator"],
                "severity": pattern["severity"],
                "explanation": pattern["explanation"]
            })
            pat_id = pattern["id"]
            pat_weight = category_weights.get(pat_id, 50)
            if pat_weight > current_highest_weight:
                current_highest_weight = pat_weight
                threat_category = pat_id

    return {
        "heuristicScore": min(heuristic_score, 100),
        "indicators": indicators,
        "threatCategory": threat_category
    }

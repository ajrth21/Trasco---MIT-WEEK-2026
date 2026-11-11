from app.services.heuristic_engine import (
    analyze_url_heuristics,
    analyze_text_heuristics,
    detect_homoglyph_brand
)
from app.services.risk_scorer import determine_risk_level, orchestrate_detection


# =====================================================================
# Existing Core Heuristics Tests (Preserved)
# =====================================================================

def test_url_heuristic_phishing():
    # Typosquatting BCA with suspicious TLD
    res = analyze_url_heuristics("https://klikbca-verifikasi-hadiah.xyz/login")
    assert res["heuristicScore"] >= 45
    assert len(res["indicators"]) > 0
    assert any("BCA" in ind["indicator"] for ind in res["indicators"])


def test_url_heuristic_official_domain():
    # Official BCA domain should not trigger typosquatting
    res = analyze_url_heuristics("https://www.klikbca.com")
    assert res["heuristicScore"] == 0
    assert res["threatCategory"] == "SAFE"


def test_text_heuristic_otp_and_deposit():
    scam_msg = "Selamat! Anda menang undian 50jt. Segera kirimkan kode OTP sms Anda dan deposit 50rb untuk pencairan."
    res = analyze_text_heuristics(scam_msg)
    assert res["heuristicScore"] >= 50
    assert res["threatCategory"] in ["OTP_THEFT", "DEPOSIT_SCAM", "FAKE_GIVEAWAY"]


def test_text_heuristic_safe():
    safe_msg = "Halo besok kita ada rapat kerja kelompok jam 10 pagi di perpustakaan ya."
    res = analyze_text_heuristics(safe_msg)
    assert res["heuristicScore"] == 0
    assert res["threatCategory"] == "SAFE"


def test_risk_level_boundaries():
    assert determine_risk_level(85) == "HIGH"
    assert determine_risk_level(70) == "HIGH"
    assert determine_risk_level(50) == "MEDIUM"
    assert determine_risk_level(35) == "MEDIUM"
    assert determine_risk_level(20) == "LOW"


def test_orchestration_high_risk():
    scam_text = "Kerja paruh waktu like video TikTok komisi 500rb/hari, transfer uang jaminan 50rb dan kirimkan kode OTP."
    res = orchestrate_detection("TEXT", scam_text)
    assert res["riskLevel"] == "HIGH"
    assert res["riskScore"] >= 70
    assert res["avatarGuidance"]["mood"] == "CRITICAL_SHIELD"
    assert res["avatarGuidance"]["accentColor"] == "#EF4444"


# =====================================================================
# Sprint 3 Expansion Tests: PINJOL_ILLEGAL
# =====================================================================

def test_pinjol_illegal_contact_threat():
    """Positive test: Pinjol ilegal threatening to blast contacts and photos."""
    text = "Tagihan Anda jatuh tempo! Jika tidak bayar hari ini, data dan foto KTP kamu akan kami sebarkan ke seluruh kontak!"
    res = analyze_text_heuristics(text)
    assert res["threatCategory"] == "PINJOL_ILLEGAL"
    assert res["heuristicScore"] >= 40
    assert any("Intimidasi" in ind["indicator"] or "Penyebaran" in ind["indicator"] for ind in res["indicators"])


def test_pinjol_illegal_upfront_fee():
    """Positive test: Upfront disbursement admin fee scam."""
    text = "Pinjaman dana cepat tanpa KTP disetujui 20 juta. Bayar administrasi sebelum dana cair sebesar 500rb."
    res = analyze_text_heuristics(text)
    assert res["threatCategory"] == "PINJOL_ILLEGAL"
    assert res["heuristicScore"] >= 40
    assert any("Administrasi" in ind["indicator"] for ind in res["indicators"])


def test_pinjol_educational_negative_safe():
    """Negative test: Educational content discussing legal fintech/OJK."""
    text = "OJK mengimbau masyarakat untuk memilih fintech peer to peer lending yang berizin resmi dan menghindari jeratan pinjaman ilegal."
    res = analyze_text_heuristics(text)
    assert res["threatCategory"] == "SAFE"
    assert res["heuristicScore"] == 0


# =====================================================================
# Sprint 3 Expansion Tests: INVESTMENT_FRAUD
# =====================================================================

def test_investment_fraud_guaranteed_profit():
    """Positive test: Ponzi / guaranteed daily profit with anti-loss claims."""
    text = "Gabung VIP trading kami! Profit 5% setiap hari dijamin tanpa risiko, anti loss garansi modal kembali 100%."
    res = analyze_text_heuristics(text)
    assert res["threatCategory"] == "INVESTMENT_FRAUD"
    assert res["heuristicScore"] >= 40
    assert any("Investasi Bodong" in ind["indicator"] for ind in res["indicators"])


def test_investment_fraud_deposit_lock():
    """Positive test: Recruitment bonus & locked withdrawals demanding more deposit."""
    text = "Selamat bonus Anda 10 juta! Tambah deposit agar profit bisa ditarik ke rekening pribadi Anda."
    res = analyze_text_heuristics(text)
    assert res["threatCategory"] == "INVESTMENT_FRAUD"
    assert res["heuristicScore"] >= 25


def test_investment_education_negative_safe():
    """Negative test: Genuine mutual fund / stock investment discussion."""
    text = "Investasi reksa dana pasar uang cocok untuk pemula yang ingin belajar mengelola portofolio keuangan jangka panjang."
    res = analyze_text_heuristics(text)
    assert res["threatCategory"] == "SAFE"
    assert res["heuristicScore"] == 0


def test_investment_ponzi_inquiry_negative_safe():
    """Negative test: Educational question asking what Ponzi / money game is."""
    text = "Apa itu skema Ponzi dan bagaimana cara kerja money game menurut hukum di Indonesia?"
    res = analyze_text_heuristics(text)
    assert res["threatCategory"] == "SAFE"
    assert res["heuristicScore"] == 0


def test_shortener_link_in_text_increases_risk_with_otp():
    """Positive test: URL shortener in text raises risk score to HIGH when paired with OTP/Prize."""
    text = "Klaim hadiah undian 50jt klik https://bit.ly/undian-bca-gratis dan masukkan kode OTP."
    res = orchestrate_detection("TEXT", text)
    assert res["riskLevel"] == "HIGH"
    assert res["riskScore"] >= 70
    assert any("Pemendek URL" in ind["indicator"] for ind in res["detectionIndicators"])


# =====================================================================
# Sprint 3 Expansion Tests: EMERGENCY_IMPERSONATION
# =====================================================================

def test_emergency_impersonation_accident():
    """Positive test: Family hospital accident scam."""
    text = "Halo pak, anak anda mengalami kecelakaan parah di jalan dan sedang kritis di rumah sakit, butuh biaya operasi segera!"
    res = analyze_text_heuristics(text)
    assert res["threatCategory"] == "EMERGENCY_IMPERSONATION"
    assert res["heuristicScore"] >= 40
    assert any("Kecelakaan" in ind["indicator"] for ind in res["indicators"])


def test_emergency_impersonation_police():
    """Positive test: Police arrest secret extortion scam."""
    text = "Mama saya ditahan polisi kasus razia, transfer uang tebusan 5 juta sekarang juga, jangan bilang siapa-siapa ya ma."
    res = analyze_text_heuristics(text)
    assert res["threatCategory"] == "EMERGENCY_IMPERSONATION"
    assert res["heuristicScore"] >= 40
    assert any("Polisi" in ind["indicator"] for ind in res["indicators"])


def test_emergency_new_number_probe():
    """Positive test: New number pretext probe."""
    text = "Ini nomor baru mama, hp lama rusak jatuh kemarin. Tolong simpan nomor ini ya nak."
    res = analyze_text_heuristics(text)
    assert res["threatCategory"] == "EMERGENCY_IMPERSONATION"
    assert res["heuristicScore"] >= 15


def test_emergency_neutral_negative_safe():
    """Negative test: Harmless mention of accident in news context."""
    text = "Polisi mengimbau pengendara motor untuk berhati-hati saat hujan deras agar terhindar dari kecelakaan lalu lintas."
    res = analyze_text_heuristics(text)
    assert res["threatCategory"] == "SAFE"
    assert res["heuristicScore"] == 0


# =====================================================================
# Sprint 3 Expansion Tests: URL SHORTENER DETECTION
# =====================================================================

def test_url_shortener_detection():
    """Positive test: Common shorteners flagged with high risk score without external HTTP calls."""
    res = analyze_url_heuristics("https://bit.ly/undian-bca-gratis")
    assert any("Pemendek URL" in ind["indicator"] for ind in res["indicators"])
    assert res["heuristicScore"] >= 25
    assert res["threatCategory"] == "PHISHING_URL"


def test_url_shortener_s_id():
    """Positive test: Indonesian popular shortener s.id."""
    res = analyze_url_heuristics("https://s.id/dana-kaget-2026")
    assert any("Pemendek URL" in ind["indicator"] for ind in res["indicators"])
    assert res["heuristicScore"] >= 25


def test_url_shortener_in_text_negative_safe():
    """Negative test: Normal text discussing a link shortener without link payload."""
    text = "Untuk berbagi tautan presentasi kita bisa gunakan bitly atau link internal kampus."
    res = analyze_text_heuristics(text)
    assert res["threatCategory"] == "SAFE"
    assert res["heuristicScore"] == 0


# =====================================================================
# Online gambling and obfuscated scam text tests
# =====================================================================

def test_online_gambling_promotion_detected():
    text = "Slot gacor, bonus new member, deposit untuk klaim hadiah!"
    res = analyze_text_heuristics(text)
    assert res["threatCategory"] == "JUDI_ONLINE"
    assert res["heuristicScore"] >= 40


def test_obfuscated_online_gambling_promotion_detected():
    text = "SAL.D0 50K UTK M'A1.N bareng PGS0F-T, auto max win!"
    res = analyze_text_heuristics(text)
    assert res["threatCategory"] == "JUDI_ONLINE"
    assert res["heuristicScore"] >= 40


def test_new_shortener_ln_run_detected_in_text():
    text = "Periksa tautan https://ln.run/klaim-bonus"
    res = analyze_text_heuristics(text)
    assert res["threatCategory"] == "PHISHING_URL"
    assert res["heuristicScore"] >= 25
    assert any("Pemendek URL" in ind["indicator"] for ind in res["indicators"])


# =====================================================================
# Sprint 3 Expansion Tests: HOMOGLYPH & LOOKALIKE TYPOSQUATTING
# =====================================================================

def test_homoglyph_detection_kl1kbca():
    """Positive test: Number 1 replacing letter L in klikbca."""
    res = analyze_url_heuristics("https://kl1kbca.com/login")
    assert res["threatCategory"] == "TYPOSQUATTING"
    assert res["heuristicScore"] >= 50
    assert any("Homoglif" in ind["indicator"] for ind in res["indicators"])


def test_homoglyph_detection_m4ndiri():
    """Positive test: Number 4 replacing letter A in mandiri."""
    res = analyze_url_heuristics("https://bankm4ndiri-online.vip/auth")
    assert res["threatCategory"] == "TYPOSQUATTING"
    assert res["heuristicScore"] >= 50


def test_homoglyph_punycode_handling():
    """Positive test: Safe handling of punycode xn-- domain without exception."""
    res = analyze_url_heuristics("https://xn--klkbca-nta.xyz/login")
    assert res["heuristicScore"] >= 25
    assert isinstance(res["indicators"], list)


def test_official_mandiri_not_homoglyph():
    """Negative test: Official bank domain is never flagged as homoglyph."""
    res = analyze_url_heuristics("https://bankmandiri.co.id")
    assert res["heuristicScore"] == 0
    assert res["threatCategory"] == "SAFE"


# =====================================================================
# Sprint 3 Expansion Tests: Multiple Threat Combinations
# =====================================================================

def test_multiple_threats_combination():
    """Combined scam: Emergency police threat demanding bank transfer."""
    text = (
        "Anak anda mengalami kecelakaan parah ditabrak mobil! "
        "Segera transfer ke rekening 1234567890 an Budi untuk biaya operasi dalam 15 menit!"
    )
    res = analyze_text_heuristics(text)
    assert res["threatCategory"] == "EMERGENCY_IMPERSONATION"
    assert res["heuristicScore"] >= 70
    assert len(res["indicators"]) >= 2


def test_reward_signup_url_is_flagged_as_suspicious_promotion():
    url = "https://bonusbesar.dws88.net/home?register&ref=bckomik"
    res = analyze_url_heuristics(url)
    assert res["threatCategory"] == "SUSPICIOUS_PROMOTION"
    assert res["heuristicScore"] >= 35
    assert any("bonus" in ind["indicator"].lower() for ind in res["indicators"])


def test_redeem_gift_landing_url_is_flagged_as_suspicious_promotion():
    url = (
        "https://cdn.novalooe.com/tml/redeemGift.html?"
        "v=2604171905-3#/?pid=23329&did=619b5a8a-20a9-480c-876d-09fba88fbf0c"
    )
    res = analyze_url_heuristics(url)
    assert res["threatCategory"] == "SUSPICIOUS_PROMOTION"
    assert res["heuristicScore"] >= 35
    assert any("hadiah" in ind["indicator"].lower() for ind in res["indicators"])


def test_reward_signup_url_stays_flagged_when_ai_returns_safe():
    from unittest.mock import patch

    url = "https://bonusbesar.dws88.net/home?register&ref=bckomik"
    safe_ai_result = {"confidenceScore": 0, "threatCategory": "SAFE"}
    with patch("app.services.risk_scorer.analyze_with_gemini", return_value=safe_ai_result):
        res = orchestrate_detection("URL", url)

    assert res["riskLevel"] == "MEDIUM"
    assert res["riskScore"] >= 35
    assert res["threatCategory"] == "SUSPICIOUS_PROMOTION"


def test_reward_signup_url_falls_back_to_heuristics_when_ai_unavailable():
    from unittest.mock import patch

    url = "https://bonusbesar.dws88.net/home?register&ref=bckomik"
    with patch("app.services.risk_scorer.analyze_with_gemini", return_value=None):
        res = orchestrate_detection("URL", url)

    assert res["riskLevel"] == "MEDIUM"
    assert res["riskScore"] >= 35
    assert res["threatCategory"] == "SUSPICIOUS_PROMOTION"


def test_single_gift_term_in_normal_promo_url_is_not_flagged():
    res = analyze_url_heuristics("https://example.com/gift-card?campaign=spring")
    assert res["threatCategory"] == "SAFE"
    assert res["heuristicScore"] == 0

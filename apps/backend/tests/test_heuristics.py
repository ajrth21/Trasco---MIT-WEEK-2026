from app.services.heuristic_engine import analyze_url_heuristics, analyze_text_heuristics
from app.services.risk_scorer import determine_risk_level, orchestrate_detection


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


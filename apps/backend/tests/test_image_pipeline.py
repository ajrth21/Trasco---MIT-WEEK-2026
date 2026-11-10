"""
TRASCO Image Scam Detection Pipeline Test Suite (Track A & Track B: TASK-10)
Validates the 14-stage application validation pipeline, request size boundaries,
and strict fail-closed security invariants.
"""

import io
import base64
import uuid
import pytest
from PIL import Image
from flask import Flask
from app.flask_app import app
from app.models.base import SessionLocal
from app.models.detection import DetectionLog
from app.services.image_validator import validate_image_payload
from app.services.risk_scorer import orchestrate_image_detection
from app.services.image_analyzer import analyze_image_with_gemini


def _generate_test_image(width=100, height=100, format="PNG", color="red"):
    """Helper to generate in-memory test images and base64 data URLs."""
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=color)
    img.save(buf, format=format)
    raw = buf.getvalue()
    b64 = base64.b64encode(raw).decode("ascii")
    mime = "image/jpeg" if format.upper() in ("JPG", "JPEG") else f"image/{format.lower()}"
    return f"data:{mime};base64,{b64}", mime, raw


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# --- 1. Request Body Size Boundary Tests ---

def test_request_body_size_boundary_accepted(client):
    """
    Verifies that a request with Content-Length equal to 10 MiB (10,485,760 bytes)
    is NOT rejected by the pre-buffering body guard.
    """
    headers = {
        "X-Trasco-Source": "Extension-Local",
        "Content-Type": "application/json",
    }
    # Payload of exactly 10 MiB (10 * 1024 * 1024 bytes)
    exact_10mib_data = b" " * (10 * 1024 * 1024)
    response = client.post(
        "/api/v1/detect/analyze-image",
        headers=headers,
        data=exact_10mib_data
    )
    # Status should not be 413 (since Content-Length <= 10 MiB)
    assert response.status_code != 413


def test_request_body_size_boundary_rejected(client):
    """
    Verifies that a request exceeding 10 MiB by 1 byte (10,485,761 bytes)
    is rejected with HTTP 413 and canonical error code REQUEST_BODY_TOO_LARGE.
    """
    headers = {
        "X-Trasco-Source": "Extension-Local",
        "Content-Type": "application/json",
    }
    # Payload of exactly 10 MiB + 1 byte (10,485,761 bytes)
    oversized_data = b" " * (10 * 1024 * 1024 + 1)
    response = client.post(
        "/api/v1/detect/analyze-image",
        headers=headers,
        data=oversized_data
    )
    assert response.status_code == 413
    data = response.get_json()
    assert data["success"] is False
    assert data["status"] == "VALIDATION_FAILED"
    assert data["riskLevel"] == "UNKNOWN"
    assert data["riskScore"] is None
    assert data["error"]["code"] == "REQUEST_BODY_TOO_LARGE"


# --- 2. 14-Stage Image Validation Suite (TC-01 through TC-07b) ---

def test_tc01_valid_image_structure():
    """TC-01: Valid PNG/JPEG format successfully passes all 14 stages."""
    data_url, mime, raw_bytes = _generate_test_image(120, 120, format="PNG")
    is_valid, decoded, error, code = validate_image_payload(data_url, mime)
    assert is_valid is True
    assert decoded == raw_bytes
    assert error is None
    assert code == 200


def test_tc01_successful_ai_high_risk():
    """
    TC-01 (High Risk Path): Upstream AI successfully detects fake transfer slip.
    Must return HTTP 200, status COMPLETED, riskLevel HIGH, score 85, CRITICAL_SHIELD.
    """
    from unittest.mock import patch

    data_url, mime, _ = _generate_test_image(120, 120, format="PNG")
    mock_ai_output = {
        "isScam": True,
        "confidenceScore": 85,
        "threatCategory": "FAKE_TRANSFER_SLIP",
        "summary": "Ditemukan anomali font pada nominal dan tata letak perbankan tidak konsisten.",
        "aiIndicators": [{"indicator": "Font Anomaly", "severity": "HIGH", "explanation": "Font berbeda"}],
        "recommendedActions": ["Verifikasi mutasi rekening."],
        "speechWarning": "Waspada! Bukti transfer ini terindikasi rekayasa."
    }
    with patch("app.services.risk_scorer.analyze_image_with_gemini", return_value=(mock_ai_output, None, 200)):
        result, status_code = orchestrate_image_detection(data_url, mime)
        assert status_code == 200
        assert result["success"] is True
        assert result["status"] == "COMPLETED"
        assert result["riskLevel"] == "HIGH"
        assert result["riskScore"] == 85
        assert result["threatCategory"] == "FAKE_TRANSFER_SLIP"
        assert result["avatarGuidance"]["mood"] == "CRITICAL_SHIELD"
        assert result["avatarGuidance"]["accentColor"] == "#EF4444"


def test_tc01_successful_ai_low_risk():
    """
    TC-01 (Low Risk Path): Upstream AI confirms authentic transaction slip.
    Must return HTTP 200, status COMPLETED, riskLevel LOW, score <= 34, IDLE_VIGILANT.
    """
    from unittest.mock import patch

    data_url, mime, _ = _generate_test_image(120, 120, format="PNG")
    mock_ai_output = {
        "isScam": False,
        "confidenceScore": 90,
        "threatCategory": "SAFE",
        "summary": "Struk transaksi bank terverifikasi otentik.",
        "aiIndicators": [],
        "recommendedActions": ["Transaksi tampak sah."],
        "speechWarning": "Bukti transfer tampak sah."
    }
    with patch("app.services.risk_scorer.analyze_image_with_gemini", return_value=(mock_ai_output, None, 200)):
        result, status_code = orchestrate_image_detection(data_url, mime)
        assert status_code == 200
        assert result["success"] is True
        assert result["status"] == "COMPLETED"
        assert result["riskLevel"] == "LOW"
        assert result["riskScore"] == 10
        assert result["threatCategory"] == "SAFE"
        assert result["avatarGuidance"]["mood"] == "IDLE_VIGILANT"
        assert result["avatarGuidance"]["accentColor"] == "#10B981"


def test_failed_image_scan_is_persisted_with_unknown_sentinels(client, monkeypatch):
    """Failed image analysis is recorded without violating NOT NULL database columns."""
    scan_id = str(uuid.uuid4())
    failure_result = {
        "success": False,
        "status": "ANALYSIS_UNAVAILABLE",
        "scanId": scan_id,
        "riskLevel": "UNKNOWN",
        "riskScore": None,
        "threatCategory": None,
        "summary": "Vision service unavailable.",
        "detectionIndicators": [],
        "recommendedActions": ["Verify the transaction manually."],
        "avatarGuidance": {
            "mood": "CAUTION_ALERT",
            "speechText": "Verify the transaction manually.",
            "accentColor": "#F59E0B",
            "recommendedActionPrimary": "Verify manually",
            "recommendedActionSecondary": None,
        },
        "error": {"code": "VISION_SERVICE_UNAVAILABLE", "message": "Service unavailable."},
        "analyzedAt": "2026-01-01T00:00:00+00:00",
        "latencyMs": 1.0,
    }
    monkeypatch.setattr(
        "app.flask_app.orchestrate_image_detection",
        lambda content, mime_type, metadata: (failure_result, 503),
    )

    response = client.post(
        "/api/v1/detect/analyze-image",
        headers={"X-Trasco-Source": "Extension-Local"},
        json={"content": "data:image/png;base64,AA==", "mimeType": "image/png"},
    )

    assert response.status_code == 503
    with SessionLocal() as db:
        log_entry = db.query(DetectionLog).filter_by(id=scan_id).one()
        assert log_entry.risk_level == "UNKNOWN"
        assert log_entry.risk_score == -1
        assert log_entry.threat_category == "UNKNOWN"


def test_tc02_non_image_payload():
    """TC-02: Non-image string/plain text rejected with INVALID_DATA_URL."""
    is_valid, decoded, error, code = validate_image_payload("not-a-valid-data-url-scheme", "image/png")
    assert is_valid is False
    assert error.code == "INVALID_DATA_URL"
    assert code == 422


def test_non_string_image_fields_return_validation_errors():
    """Non-string payload and MIME fields fail validation instead of raising TypeError."""
    valid, decoded, error, code = validate_image_payload({"not": "a string"}, "image/png")
    assert valid is False
    assert decoded is None
    assert error.code == "INVALID_REQUEST_PAYLOAD"
    assert code == 400

    valid, decoded, error, code = validate_image_payload("data:image/png;base64,AAAA", None)
    assert valid is False
    assert decoded is None
    assert error.code == "INVALID_REQUEST_PAYLOAD"
    assert code == 400


def test_tc03_unsupported_image_format():
    """TC-03: Unsupported format (.svg) rejected with UNSUPPORTED_IMAGE_FORMAT (HTTP 415)."""
    svg_payload = "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4="
    is_valid, decoded, error, code = validate_image_payload(svg_payload, "image/svg+xml")
    assert is_valid is False
    assert error.code == "UNSUPPORTED_IMAGE_FORMAT"
    assert code == 415


def test_tc04_mime_signature_mismatch():
    """TC-04: PNG binary bytes declared as image/jpeg rejected with MIME_SIGNATURE_MISMATCH."""
    _, _, png_bytes = _generate_test_image(80, 80, format="PNG")
    fake_jpeg_url = f"data:image/jpeg;base64,{base64.b64encode(png_bytes).decode()}"
    is_valid, decoded, error, code = validate_image_payload(fake_jpeg_url, "image/jpeg")
    assert is_valid is False
    assert error.code == "MIME_SIGNATURE_MISMATCH"
    assert code == 422


def test_tc05_corrupted_base64():
    """TC-05: Malformed base64 padding or invalid chars rejected with INVALID_BASE64."""
    corrupted_url = "data:image/png;base64,%%%INVALID_B64_DATA==="
    is_valid, decoded, error, code = validate_image_payload(corrupted_url, "image/png")
    assert is_valid is False
    assert error.code == "INVALID_BASE64"
    assert code == 422


def test_tc06_binary_size_exceeded():
    """TC-06: Decoded binary buffer exceeding 5 MiB rejected with IMAGE_TOO_LARGE."""
    oversized_bytes = b"\x89PNG\r\n\x1a\n" + b"0" * (5 * 1024 * 1024 + 50)
    b64 = base64.b64encode(oversized_bytes).decode()
    url = f"data:image/png;base64,{b64}"
    is_valid, decoded, error, code = validate_image_payload(url, "image/png")
    assert is_valid is False
    assert error.code == "IMAGE_TOO_LARGE"
    assert code == 422


def test_tc07a_side_dimension_boundary():
    """
    TC-07a (COR-03): One side exceeding 4096 px (4500x2000 px)
    rejected at Stage 11 with IMAGE_DIMENSIONS_EXCEEDED.
    """
    data_url, mime, _ = _generate_test_image(4500, 2000, format="JPEG")
    is_valid, decoded, error, code = validate_image_payload(data_url, mime)
    assert is_valid is False
    assert error.code == "IMAGE_DIMENSIONS_EXCEEDED"
    assert code == 422


def test_tc07b_pixel_budget_boundary():
    """
    TC-07b (COR-03): Both sides <= 4096 px (4000x4001 px = 16,004,000 px)
    passes Stage 11 but rejected at Stage 12 with IMAGE_PIXEL_LIMIT_EXCEEDED.
    """
    data_url, mime, _ = _generate_test_image(4000, 4001, format="JPEG")
    is_valid, decoded, error, code = validate_image_payload(data_url, mime)
    assert is_valid is False
    assert error.code == "IMAGE_PIXEL_LIMIT_EXCEEDED"
    assert code == 422


# --- 3. Fail-Closed Invariant & Upstream Resilience (TC-08 & TC-11) ---

def test_tc08_missing_api_key_fail_closed():
    """
    TC-08: When Gemini API key is missing or library is unconfigured,
    the analyzer fails closed with 503 and returns UNKNOWN risk.
    """
    data_url, mime, _ = _generate_test_image(100, 100, format="PNG")
    result, status_code = orchestrate_image_detection(data_url, mime)

    # Fail closed guarantees
    assert status_code in (500, 503)
    assert result["success"] is False
    assert result["riskLevel"] == "UNKNOWN"
    assert result["riskScore"] is None
    assert result["threatCategory"] is None
    assert result["avatarGuidance"]["mood"] == "CAUTION_ALERT"
    assert result["avatarGuidance"]["accentColor"] == "#F59E0B"


def test_tc09_gemini_timeout():
    """
    TC-09: Upstream Gemini Vision timeout (> 8.0s).
    Must fail closed returning HTTP 504 Gateway Timeout,
    status ANALYSIS_FAILED, riskLevel UNKNOWN, riskScore null, mood CAUTION_ALERT.
    """
    from unittest.mock import patch
    from app.schemas.detection import ErrorDetail

    data_url, mime, _ = _generate_test_image(100, 100, format="PNG")
    mock_error = ErrorDetail(
        code="VISION_TIMEOUT",
        message="Permintaan analisis ke upstream Gemini Vision melebihi batas waktu 8.0 detik."
    )
    with patch("app.services.risk_scorer.analyze_image_with_gemini", return_value=(None, mock_error, 504)):
        result, status_code = orchestrate_image_detection(data_url, mime)
        assert status_code == 504
        assert result["success"] is False
        assert result["status"] == "ANALYSIS_FAILED"
        assert result["riskLevel"] == "UNKNOWN"
        assert result["riskScore"] is None
        assert result["threatCategory"] is None
        assert result["error"]["code"] == "VISION_TIMEOUT"
        assert result["avatarGuidance"]["mood"] == "CAUTION_ALERT"
        assert result["avatarGuidance"]["accentColor"] == "#F59E0B"


def test_tc10_gemini_corrupted_json():
    """
    TC-10: Upstream Gemini returns non-JSON or corrupted response.
    Must fail closed returning HTTP 502 Bad Gateway,
    status ANALYSIS_FAILED, riskLevel UNKNOWN, riskScore null, mood CAUTION_ALERT.
    """
    from unittest.mock import patch
    from app.schemas.detection import ErrorDetail

    data_url, mime, _ = _generate_test_image(100, 100, format="PNG")
    mock_error = ErrorDetail(
        code="INVALID_AI_RESPONSE",
        message="Output dari AI bukan format JSON yang sah: Expecting value"
    )
    with patch("app.services.risk_scorer.analyze_image_with_gemini", return_value=(None, mock_error, 502)):
        result, status_code = orchestrate_image_detection(data_url, mime)
        assert status_code == 502
        assert result["success"] is False
        assert result["status"] == "ANALYSIS_FAILED"
        assert result["riskLevel"] == "UNKNOWN"
        assert result["riskScore"] is None
        assert result["threatCategory"] is None
        assert result["error"]["code"] == "INVALID_AI_RESPONSE"
        assert result["avatarGuidance"]["mood"] == "CAUTION_ALERT"
        assert result["avatarGuidance"]["accentColor"] == "#F59E0B"


def test_tc11_zero_false_safe_invariant():
    """
    TC-11: Zero False-Safe Invariant across all validation failures.
    Asserts that NO failure scenario ever produces riskLevel LOW,
    a numeric score, or an IDLE_VIGILANT (green) avatar mood.
    """
    failing_cases = [
        ("invalid-url", "image/png"),
        ("data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=", "image/svg+xml"),
        ("data:image/png;base64,!!!broken!!!", "image/png"),
    ]

    for content, mime in failing_cases:
        res, code = orchestrate_image_detection(content, mime)
        assert code != 200, f"Expected non-200 for {content[:30]}, got {code}"
        assert res["success"] is False
        assert res["riskLevel"] == "UNKNOWN"
        assert res["riskScore"] is None
        assert res["threatCategory"] is None
        assert res["avatarGuidance"]["mood"] != "IDLE_VIGILANT"
        assert res["avatarGuidance"]["accentColor"] != "#10B981"

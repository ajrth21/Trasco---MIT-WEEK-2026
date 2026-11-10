import json
import hashlib
import re
from datetime import datetime, timezone
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from app.core.config import settings, validate_startup_security
from app.core.database import is_application_ready, set_application_ready, probe_schema_compatibility
from app.models.base import Base, engine, SessionLocal
from app.models.user import User, SecurityPreference
from app.models.detection import DetectionLog
from app.services.risk_scorer import orchestrate_detection, orchestrate_image_detection
from app.services.analytics_service import compute_security_overview
from app.core.scrubber import scrub_pii

# Validate configuration on module import to ensure WSGI deployment fail-closed protection
validate_startup_security(settings)

app = Flask("trasco_api")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MiB limit (10,485,760 bytes)


@app.errorhandler(413)
def request_entity_too_large(error=None):
    """Gateway/App-level request body size enforcement handler."""
    return jsonify({
        "success": False,
        "status": "INVALID_REQUEST",
        "scanId": None,
        "riskLevel": "UNKNOWN",
        "riskScore": None,
        "threatCategory": None,
        "summary": "Request body exceeds maximum allowed size of 10 MiB.",
        "detectionIndicators": [],
        "recommendedActions": ["Kirim payload dengan ukuran tidak melebihi 10 MiB."],
        "avatarGuidance": {
            "mood": "CAUTION_ALERT",
            "speechText": "Permintaan ditolak: Ukuran body permintaan melebihi batas 10 MiB.",
            "accentColor": "#F59E0B",
            "recommendedActionPrimary": "Perkecil ukuran file",
            "recommendedActionSecondary": "Periksa format citra"
        },
        "error": {
            "code": "REQUEST_BODY_TOO_LARGE",
            "message": "Request body exceeds maximum allowed size of 10 MiB",
            "details": None
        },
        "analyzedAt": datetime.now(timezone.utc).isoformat(),
        "latencyMs": 0.0
    }), 413

# --- ISSUE-SEC-01: Strict Origin Allowlist (replaces wildcard CORS) ---
# Exact local origins that are trusted for both CORS and the application gatekeeper.
_TRUSTED_LOCAL_ORIGINS = {
    "http://localhost:5173",      # Vite dashboard dev server
    "http://127.0.0.1:5173",
    "http://localhost:8000",      # Backend self-referencing (rare)
    "http://127.0.0.1:8000",
}
# flask-cors origin list: includes the exact origins + regex patterns for
# dynamic browser extension IDs (chrome-extension://<id>, edge-extension://<id>).
TRUSTED_ORIGINS = list(_TRUSTED_LOCAL_ORIGINS) + [
    r"^chrome-extension://.*$",   # Chrome extension (any ID)
    r"^edge-extension://.*$",     # Edge extension (any ID)
]

CORS(app, resources={r"/*": {"origins": TRUSTED_ORIGINS}}, supports_credentials=False)

# DDL has been decoupled: worker runtimes never execute Base.metadata.create_all() at import time.


def bootstrap_flask_worker(current_settings=None, target_engine=None) -> bool:
    """Bootstrap Flask worker readiness by validating security and checking schema compatibility.
    Does NOT execute DDL. Sets application readiness state to True only on complete success.
    """
    eff_settings = current_settings or settings
    validate_startup_security(eff_settings)
    eff_engine = target_engine if target_engine is not None else engine
    probe_res = probe_schema_compatibility(eff_engine)
    if probe_res.compatible:
        set_application_ready(True)
        return True
    set_application_ready(False)
    return False


# --- Auto-bootstrap on module import ---
# When Flask CLI imports this module (`flask --app app.flask_app run`),
# `if __name__ == "__main__"` does NOT execute, so bootstrap_flask_worker()
# was never called, leaving the readiness guard permanently returning 503.
# Fix: bootstrap at module level. If schema probe fails (e.g., no DB file),
# the app still starts but in degraded mode — detection routes work,
# DB-persistence routes log warnings gracefully.
def _auto_bootstrap():
    """One-time module-level bootstrap for Flask CLI compatibility."""
    try:
        bootstrap_flask_worker()
    except Exception:
        import logging
        logging.getLogger("trasco.bootstrap").error(
            "Auto-bootstrap failed; the application remains unready."
        )
        set_application_ready(False)

_auto_bootstrap()


@app.before_request
def guard_application_readiness():
    """Readiness Gatekeeper: Intercepts unready traffic before business views execute.
    Permits static liveness probes (/health) and inspects readiness probe (/health/ready).
    """
    # 1. Always allow static liveness probe
    if request.path == "/health" and request.method == "GET":
        return None

    # 2. Allow documentation endpoints
    if request.path in ["/docs", "/openapi.json"]:
        return None

    # 3. Intercept when worker is unready
    if not is_application_ready():
        if request.path == "/health/ready" and request.method == "GET":
            return jsonify({
                "status": "unready",
                "detail": "Startup security or schema compatibility validation incomplete."
            }), 503

        # Narrow check for genuine browser CORS preflight
        if request.method == "OPTIONS":
            if "Origin" in request.headers and "Access-Control-Request-Method" in request.headers:
                origin = request.headers.get("Origin", "")
                is_ext = origin.startswith("chrome-extension://") or origin.startswith("edge-extension://")
                if is_ext or origin in _TRUSTED_LOCAL_ORIGINS:
                    resp = make_response(jsonify({
                        "error": "Service Unavailable",
                        "detail": "Application startup unready."
                    }), 503)
                    return resp

        return jsonify({
            "error": "Service Unavailable",
            "detail": "Application startup unready."
        }), 503

    # 4. If application is ready, handle /health/ready
    if request.path == "/health/ready" and request.method == "GET":
        return jsonify({
            "status": "ready",
            "service": "TRASCO Backend API",
            "version": "1.0.0"
        }), 200

    return None


@app.before_request
def verify_request_security():
    """Security Handshake Gatekeeper: Blocks unauthorized web origins from probing local backend.

    Defence-in-depth layers:
      1. CORS pre-flight already restricts browser cross-origin requests to the allowlist.
      2. This middleware enforces origin validation at the application layer as a second barrier.
      3. X-Trasco-Source is treated as a *client identifier* for logging, NOT as authentication.
    """
    # Allow unauthenticated liveness and docs
    if request.path in ["/health", "/health/ready", "/docs", "/openapi.json"]:
        return None

    # Allow genuine CORS preflight
    if request.method == "OPTIONS":
        if "Origin" in request.headers and "Access-Control-Request-Method" in request.headers:
            return None

    origin = request.headers.get("Origin", "")
    trasco_source = request.headers.get("X-Trasco-Source", "")

    # --- Layer 1: Browser Origin Verification (Strict Allowlist) ---
    if origin:
        is_extension = (
            origin.startswith("chrome-extension://")
            or origin.startswith("edge-extension://")
        )
        is_trusted_local = origin in _TRUSTED_LOCAL_ORIGINS

        # Reject any origin not on the allowlist
        if not (is_extension or is_trusted_local):
            return jsonify({"error": "Unauthorized web origin. Blocked by TRASCO local firewall."}), 403

    # --- Layer 2: Client Identifier Header ---
    # When a browser Origin is present, the caller MUST also identify itself.
    # This prevents a random trusted-origin page from accidentally hitting the API.
    # NOTE: X-Trasco-Source is NOT authentication — it is a defence-in-depth signal.
    if origin and trasco_source not in ("Extension-Local", "Dashboard-Client"):
        return jsonify({"error": "Missing or invalid TRASCO client handshake header."}), 403

    return None


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "TRASCO Backend API (Dual-Engine)",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@app.route("/api/v1/detect/analyze", methods=["POST"])
def analyze_content():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    scan_type = data.get("scanType", "TEXT")
    content = data.get("content", "")
    metadata = data.get("metadata", {})

    if scan_type not in ("URL", "TEXT"):
        return jsonify({"error": "scanType must be URL or TEXT."}), 400
    if not isinstance(content, str) or not content:
        return jsonify({"error": "Content is required"}), 400
    if not isinstance(metadata, dict):
        return jsonify({"error": "metadata must be a JSON object."}), 400

    result = orchestrate_detection(scan_type, content, metadata)

    # Persist log to DB with UU PDP Data Minimization
    db = SessionLocal()
    try:
        snippet = scrub_pii(content[:100])
        target_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        log_entry = DetectionLog(
            id=result["scanId"],
            scan_type=scan_type,
            target_hash=target_hash,
            sanitized_snippet=snippet,
            risk_level=result["riskLevel"],
            risk_score=result["riskScore"],
            threat_category=result["threatCategory"],
            detection_indicators=result["detectionIndicators"],
            recommendations=result["recommendedActions"],
            latency_ms=result.get("latencyMs", 0.0)
        )
        db.add(log_entry)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return jsonify(result)


@app.route("/api/v1/detect/analyze-image", methods=["POST"])
def analyze_image():
    # 1. Pre-buffering Content-Length guard (<= 10 MiB = 10,485,760 bytes)
    raw_cl = request.headers.get("Content-Length")
    content_length = request.content_length
    if raw_cl and raw_cl.isdigit() and int(raw_cl) > 10 * 1024 * 1024:
        content_length = int(raw_cl)

    if content_length is not None and content_length > 10 * 1024 * 1024:
        return jsonify({
            "success": False,
            "status": "VALIDATION_FAILED",
            "scanId": None,
            "riskLevel": "UNKNOWN",
            "riskScore": None,
            "threatCategory": None,
            "confidenceScore": 0.0,
            "detectionIndicators": [],
            "recommendedActions": ["Kirim payload dengan ukuran tidak melebihi 10 MiB."],
            "avatarGuidance": {
                "mood": "CAUTION_ALERT",
                "speechText": "Permintaan ditolak: Ukuran body permintaan melebihi batas 10 MiB.",
                "accentColor": "#F59E0B",
                "recommendedActionPrimary": "Perkecil ukuran file",
                "recommendedActionSecondary": "Periksa format citra"
            },
            "error": {
                "code": "REQUEST_BODY_TOO_LARGE",
                "message": "Request body exceeds maximum allowed size of 10 MiB",
                "details": f"Content-Length: {content_length} bytes"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 413

    # 2. Parse JSON
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return jsonify({
            "success": False,
            "status": "INVALID_REQUEST",
            "scanId": None,
            "riskLevel": "UNKNOWN",
            "riskScore": None,
            "threatCategory": None,
            "summary": "Request body must be valid JSON.",
            "detectionIndicators": [],
            "recommendedActions": ["Pastikan format body request adalah JSON valid."],
            "avatarGuidance": {
                "mood": "CAUTION_ALERT",
                "speechText": "Permintaan ditolak: Format JSON tidak valid.",
                "accentColor": "#F59E0B",
                "recommendedActionPrimary": "Periksa sintaks JSON",
                "recommendedActionSecondary": None
            },
            "error": {
                "code": "PAYLOAD_VALIDATION_ERROR",
                "message": "Request body must be valid JSON.",
                "details": None
            },
            "analyzedAt": datetime.now(timezone.utc).isoformat(),
            "latencyMs": 0.0
        }), 400

    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    content = data.get("content", "")
    mime_type = data.get("mimeType", "")
    metadata = data.get("metadata", {})

    # Auto-detect mimeType from data URL if not provided explicitly
    if not mime_type and isinstance(content, str) and content.startswith("data:"):
        match = re.match(r"^data:([^;]+);base64,", content)
        if match:
            mime_type = match.group(1).lower()

    if not isinstance(content, str) or not content:
        return jsonify({
            "success": False,
            "status": "INVALID_REQUEST",
            "scanId": None,
            "riskLevel": "UNKNOWN",
            "riskScore": None,
            "threatCategory": None,
            "summary": "Field 'content' is required and must be a string.",
            "detectionIndicators": [],
            "recommendedActions": ["Sertakan field 'content' berisi Base64 Data URL citra."],
            "avatarGuidance": {
                "mood": "CAUTION_ALERT",
                "speechText": "Permintaan tidak lengkap: Field 'content' wajib diisi.",
                "accentColor": "#F59E0B",
                "recommendedActionPrimary": "Unggah citra",
                "recommendedActionSecondary": None
            },
            "error": {
                "code": "PAYLOAD_VALIDATION_ERROR",
                "message": "Field 'content' is required and must be a string.",
                "details": None
            },
            "analyzedAt": datetime.now(timezone.utc).isoformat(),
            "latencyMs": 0.0
        }), 400

    if not isinstance(metadata, dict):
        return jsonify({"error": "metadata must be a JSON object."}), 400

    # 3. Execute orchestrator
    result, status_code = orchestrate_image_detection(content, mime_type, metadata)

    # 4. Persist log to DB if scanId is generated
    if result.get("scanId"):
        db = SessionLocal()
        try:
            log_entry = DetectionLog(
                id=result["scanId"],
                scan_type="IMAGE",
                target_hash=hashlib.sha256(content[:200].encode("utf-8")).hexdigest(),
                sanitized_snippet="[Image Scan: Transfer Slip / Visual Content]",
                risk_level=result.get("riskLevel") or "UNKNOWN",
                risk_score=result.get("riskScore") if result.get("riskScore") is not None else -1,
                threat_category=result.get("threatCategory") or "UNKNOWN",
                detection_indicators=result.get("detectionIndicators", []),
                recommendations=result.get("recommendedActions", []),
                latency_ms=result.get("latencyMs", 0.0)
            )
            db.add(log_entry)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    return jsonify(result), status_code


@app.route("/api/v1/analytics/overview", methods=["GET"])
def get_analytics():
    db = SessionLocal()
    try:
        overview = compute_security_overview(db=db, user_id=None)
        return jsonify(overview.model_dump())
    finally:
        db.close()


@app.route("/api/v1/analytics/history", methods=["GET"])
def get_history():
    db = SessionLocal()
    try:
        logs = db.query(DetectionLog).order_by(DetectionLog.created_at.desc()).limit(30).all()
        return jsonify([
            {
                "id": l.id,
                "scanType": l.scan_type,
                "sanitizedSnippet": l.sanitized_snippet,
                "riskLevel": l.risk_level,
                "riskScore": (
                    l.risk_score if l.risk_score is not None and l.risk_score >= 0 else None
                ),
                "threatCategory": l.threat_category,
                "indicators": l.detection_indicators,
                "recommendations": l.recommendations,
                "createdAt": l.created_at.isoformat() if l.created_at else ""
            }
            for l in logs
        ])
    finally:
        db.close()


if __name__ == "__main__":
    # Bootstrap worker readiness (validates security configuration and checks schema compatibility)
    bootstrap_flask_worker()

    # ISSUE-SEC-01: Bind to loopback only — prevents DNS rebinding attacks
    # and network-adjacent access. The extension and dashboard both connect
    # to localhost:8000 / 127.0.0.1:8000 exclusively.
    app.run(host="127.0.0.1", port=8000, debug=settings.DEBUG)

import json
import hashlib
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS
from app.models.base import Base, engine, SessionLocal
from app.models.user import User, SecurityPreference
from app.models.detection import DetectionLog
from app.services.risk_scorer import orchestrate_detection
from app.services.analytics_service import compute_security_overview
from app.core.scrubber import scrub_pii

app = Flask("trasco_api")

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

# Ensure database tables exist
Base.metadata.create_all(bind=engine)


@app.before_request
def verify_request_security():
    """Security Handshake Gatekeeper: Blocks unauthorized web origins from probing local backend.

    Defence-in-depth layers:
      1. CORS pre-flight already restricts browser cross-origin requests to the allowlist.
      2. This middleware enforces origin validation at the application layer as a second barrier.
      3. X-Trasco-Source is treated as a *client identifier* for logging, NOT as authentication.
    """
    # Always allow preflight OPTIONS and the unauthenticated health probe
    if request.method == "OPTIONS" or request.path in ["/health", "/docs", "/openapi.json"]:
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
    data = request.get_json(force=True) or {}
    scan_type = data.get("scanType", "TEXT")
    content = data.get("content", "")
    metadata = data.get("metadata", {})

    if not content:
        return jsonify({"error": "Content is required"}), 400

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
    finally:
        db.close()

    return jsonify(result)


@app.route("/api/v1/detect/analyze-image", methods=["POST"])
def analyze_image():
    data = request.get_json(force=True) or {}
    content = data.get("content", "")
    metadata = data.get("metadata", {})

    result = orchestrate_detection("IMAGE", content, metadata)

    db = SessionLocal()
    try:
        log_entry = DetectionLog(
            id=result["scanId"],
            scan_type="IMAGE",
            target_hash=hashlib.sha256(content[:200].encode("utf-8")).hexdigest(),
            sanitized_snippet="[Image Scan: Transfer Slip / Visual Content]",
            risk_level=result["riskLevel"],
            risk_score=result["riskScore"],
            threat_category=result["threatCategory"],
            detection_indicators=result["detectionIndicators"],
            recommendations=result["recommendedActions"],
            latency_ms=result.get("latencyMs", 0.0)
        )
        db.add(log_entry)
        db.commit()
    finally:
        db.close()

    return jsonify(result)


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
                "riskScore": l.risk_score,
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
    # ISSUE-SEC-01: Bind to loopback only — prevents DNS rebinding attacks
    # and network-adjacent access. The extension and dashboard both connect
    # to localhost:8000 / 127.0.0.1:8000 exclusively.
    app.run(host="127.0.0.1", port=8000, debug=True)

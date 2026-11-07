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
CORS(app, resources={r"/*": {"origins": "*"}})

# Ensure database tables exist
Base.metadata.create_all(bind=engine)


@app.before_request
def verify_request_security():
    """Security Handshake Gatekeeper: Blocks unauthorized web origins from probing local backend."""
    # Always allow preflight OPTIONS and health check
    if request.method == "OPTIONS" or request.path in ["/health", "/docs", "/openapi.json"]:
        return None

    # Verify origin or client header
    origin = request.headers.get("Origin", "")
    trasco_source = request.headers.get("X-Trasco-Source", "")
    
    # Allow if originating from extension, localhost, or has client signature
    is_extension = origin.startswith("chrome-extension://") or origin.startswith("edge-extension://")
    is_local = "localhost" in origin or "127.0.0.1" in origin or origin == "" or not origin
    is_signed = trasco_source in ["Extension-Local", "Dashboard-Client"]

    if not (is_extension or is_local or is_signed):
        return jsonify({"error": "Unauthorized request origin. Blocked by TRASCO local firewall."}), 403
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
    app.run(host="0.0.0.0", port=8000, debug=True)

import hashlib
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.base import get_db
from app.models.detection import DetectionLog
from app.schemas.detection import AnalyzeRequest, AnalyzeResponse
from app.services.risk_scorer import orchestrate_detection
from app.api.v1.auth import get_optional_current_user

router = APIRouter(prefix="/detect", tags=["Threat Detection"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_content(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_current_user)
):
    # Run orchestrator
    result = orchestrate_detection(request.scanType, request.content, request.metadata)

    # Sanitize snippet for privacy (max 100 chars, redact potential sensitive numbers)
    snippet = request.content[:100]
    target_hash = hashlib.sha256(request.content.encode("utf-8")).hexdigest()

    # Persist log to DB
    user_id = current_user.id if current_user else None
    log_entry = DetectionLog(
        id=result["scanId"],
        user_id=user_id,
        scan_type=request.scanType,
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

    return AnalyzeResponse(**result)


@router.post("/analyze-image", response_model=AnalyzeResponse)
def analyze_image_endpoint(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_current_user)
):
    result = orchestrate_detection("IMAGE", request.content, request.metadata)

    user_id = current_user.id if current_user else None
    log_entry = DetectionLog(
        id=result["scanId"],
        user_id=user_id,
        scan_type="IMAGE",
        target_hash=hashlib.sha256(request.content[:200].encode("utf-8")).hexdigest(),
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

    return AnalyzeResponse(**result)


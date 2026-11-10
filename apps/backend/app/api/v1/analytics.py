from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.base import get_db
from app.models.detection import DetectionLog
from app.schemas.analytics import (
    SecurityOverviewResponse
)
from app.api.v1.auth import get_optional_current_user
from app.services.analytics_service import compute_security_overview

router = APIRouter(prefix="/analytics", tags=["Security Analytics"])


@router.get("/overview", response_model=SecurityOverviewResponse)
def get_overview(db: Session = Depends(get_db), current_user = Depends(get_optional_current_user)):
    user_id = current_user.id if current_user else None
    return compute_security_overview(db=db, user_id=user_id)


@router.get("/history")
def get_history(db: Session = Depends(get_db), current_user = Depends(get_optional_current_user)):
    user_id = current_user.id if current_user else None
    query = db.query(DetectionLog)
    if user_id:
        query = query.filter(DetectionLog.user_id == user_id)
    logs = query.order_by(desc(DetectionLog.created_at)).limit(30).all()
    
    return [
        {
            "id": l.id,
            "scanType": l.scan_type,
            "sanitizedSnippet": l.sanitized_snippet,
            "riskLevel": l.risk_level,
            "riskScore": l.risk_score if l.risk_score is not None and l.risk_score >= 0 else None,
            "threatCategory": l.threat_category,
            "indicators": l.detection_indicators,
            "recommendations": l.recommendations,
            "createdAt": l.created_at.isoformat()
        }
        for l in logs
    ]

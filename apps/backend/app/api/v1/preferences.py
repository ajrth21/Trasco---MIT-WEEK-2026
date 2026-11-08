from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.base import get_db
from app.models.user import SecurityPreference
from app.schemas.auth import SecurityPreferenceUpdate, SecurityPreferenceOut
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/preferences", tags=["Security Preferences"])


@router.get("", response_model=SecurityPreferenceOut)
def get_user_preferences(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    pref = db.query(SecurityPreference).filter(SecurityPreference.user_id == current_user.id).first()
    if not pref:
        pref = SecurityPreference(user_id=current_user.id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return SecurityPreferenceOut.model_validate(pref)


@router.put("", response_model=SecurityPreferenceOut)
def update_user_preferences(
    pref_in: SecurityPreferenceUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pref = db.query(SecurityPreference).filter(SecurityPreference.user_id == current_user.id).first()
    if not pref:
        pref = SecurityPreference(user_id=current_user.id)
        db.add(pref)

    if pref_in.avatar_enabled is not None:
        pref.avatar_enabled = pref_in.avatar_enabled
    if pref_in.avatar_theme is not None:
        pref.avatar_theme = pref_in.avatar_theme
    if pref_in.audio_alert_enabled is not None:
        pref.audio_alert_enabled = pref_in.audio_alert_enabled
    if pref_in.risk_threshold is not None:
        pref.risk_threshold = pref_in.risk_threshold
    if pref_in.auto_scan_urls is not None:
        pref.auto_scan_urls = pref_in.auto_scan_urls

    db.commit()
    db.refresh(pref)
    return SecurityPreferenceOut.model_validate(pref)


from pydantic import BaseModel, EmailStr
from typing import Optional


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    display_name: str
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    token: str
    token_type: str = "bearer"
    user: UserOut


class SecurityPreferenceUpdate(BaseModel):
    avatar_enabled: Optional[bool] = None
    avatar_theme: Optional[str] = None
    audio_alert_enabled: Optional[bool] = None
    risk_threshold: Optional[str] = None
    auto_scan_urls: Optional[bool] = None


class SecurityPreferenceOut(BaseModel):
    avatar_enabled: bool
    avatar_theme: str
    audio_alert_enabled: bool
    risk_threshold: str
    auto_scan_urls: bool

    class Config:
        from_attributes = True


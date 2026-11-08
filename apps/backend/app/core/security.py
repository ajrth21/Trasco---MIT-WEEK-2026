import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
from app.core.config import settings

try:
    from jose import jwt
    JOSE_AVAILABLE = True
except ImportError:
    jwt = None
    JOSE_AVAILABLE = False

try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    PASSLIB_AVAILABLE = True
except ImportError:
    pwd_context = None
    PASSLIB_AVAILABLE = False


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": int(expire.timestamp()), "sub": str(subject)}

    if JOSE_AVAILABLE:
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Standard library fallback token (HMAC-SHA256)
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps(to_encode).encode()).decode().rstrip("=")
    signature = base64.urlsafe_b64encode(
        hmac.new(settings.SECRET_KEY.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    ).decode().rstrip("=")
    return f"{header}.{payload}.{signature}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if PASSLIB_AVAILABLE:
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            pass
    # Fallback SHA256 comparison
    expected = hashlib.sha256((plain_password + settings.SECRET_KEY).encode()).hexdigest()
    return hmac.compare_digest(expected, hashed_password)


def get_password_hash(password: str) -> str:
    if PASSLIB_AVAILABLE:
        try:
            return pwd_context.hash(password)
        except Exception:
            pass
    # Fallback SHA256 hash
    return hashlib.sha256((password + settings.SECRET_KEY).encode()).hexdigest()


def decode_access_token(token: str) -> Optional[dict]:
    try:
        if JOSE_AVAILABLE:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        
        # Verify signature
        expected_sig = base64.urlsafe_b64encode(
            hmac.new(settings.SECRET_KEY.encode(), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256).digest()
        ).decode().rstrip("=")
        if not hmac.compare_digest(sig_b64, expected_sig):
            return None

        # Decode payload
        padded_payload = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded_payload).decode())

        # Check expiration
        if "exp" in payload and datetime.now(timezone.utc).timestamp() > payload["exp"]:
            return None
        return payload
    except Exception:
        return None


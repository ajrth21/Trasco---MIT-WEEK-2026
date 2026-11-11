import hashlib
import hmac
import re
import uuid

from app.core.config import settings


VISITOR_COOKIE_NAME = "trasco_visitor"
VISITOR_COOKIE_MAX_AGE = 60 * 60 * 24 * 365
_VISITOR_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


def create_visitor_id() -> str:
    return uuid.uuid4().hex


def _sign_visitor_id(visitor_id: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        f"trasco-visitor:{visitor_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_visitor_cookie(cookie_value: str | None) -> str | None:
    if not cookie_value:
        return None

    visitor_id, separator, signature = cookie_value.partition(".")
    if not separator or not _VISITOR_ID_PATTERN.fullmatch(visitor_id):
        return None

    if not hmac.compare_digest(_sign_visitor_id(visitor_id), signature):
        return None
    return visitor_id


def set_visitor_cookie(response, visitor_id: str, secure: bool = True):
    response.set_cookie(
        VISITOR_COOKIE_NAME,
        f"{visitor_id}.{_sign_visitor_id(visitor_id)}",
        max_age=VISITOR_COOKIE_MAX_AGE,
        httponly=True,
        secure=secure,
        samesite="None" if secure else "Lax",
        path="/",
    )
    return response

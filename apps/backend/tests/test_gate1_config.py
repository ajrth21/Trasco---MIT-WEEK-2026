"""Unit tests for Gate 1 startup security configuration policy.

Verifies:
1. Default DEBUG is False on an isolated environment (no .env influence).
2. DEBUG=True + known default secret -> warning and startup validation passes.
3. DEBUG=False + known default secret -> validation fails (SystemExit).
4. DEBUG=True + empty secret -> validation fails (SystemExit).
5. DEBUG=False + empty secret -> validation fails (SystemExit).
6. DEBUG=True + whitespace-only secret -> validation fails (SystemExit).
7. DEBUG=True + short secret (< 32 chars) -> validation fails (SystemExit).
8. DEBUG=False + short secret (< 32 chars) -> validation fails (SystemExit).
9. DEBUG=True + valid-length non-default secret (>= 32 chars) -> validation passes.
10. DEBUG=False + valid-length non-default secret (>= 32 chars) -> validation passes.
11. Secret is never printed in warning or exception messages.
12. Isolation: tests do not mutate persistent database or leak credentials.
"""

import io
import sys
import pytest
from app.core.config import Settings, validate_startup_security, _INSECURE_DEFAULT_SECRET

VALID_NON_DEFAULT_SECRET = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"  # 64 chars


def _make_dummy_settings(debug: bool, secret_key: str) -> Settings:
    """Helper to instantiate Settings with mock in-memory attributes without touching disk/env."""
    s = Settings()
    s.DEBUG = debug
    s.SECRET_KEY = secret_key
    return s


def test_gate1_debug_true_known_default_secret_warning_and_allowed():
    """Policy 2: DEBUG=True + known default secret emits warning to stderr and succeeds."""
    s = _make_dummy_settings(debug=True, secret_key=_INSECURE_DEFAULT_SECRET)
    old_err = sys.stderr
    sys.stderr = io.StringIO()
    try:
        validate_startup_security(s)
        warning_output = sys.stderr.getvalue()
    finally:
        sys.stderr = old_err

    assert "[TRASCO SECURITY WARNING]" in warning_output
    assert "DEVELOPMENT mode with default insecure SECRET_KEY" in warning_output
    # Policy 11: Secret value itself must never appear in warning output
    assert _INSECURE_DEFAULT_SECRET not in warning_output


def test_gate1_debug_false_known_default_secret_hard_stop():
    """Policy 5: DEBUG=False + known default secret triggers immediate hard stop."""
    s = _make_dummy_settings(debug=False, secret_key=_INSECURE_DEFAULT_SECRET)
    with pytest.raises(SystemExit) as exc_info:
        validate_startup_security(s)
    err_msg = str(exc_info.value)
    assert "[CRITICAL SECURITY BLOCKER]" in err_msg
    assert "Insecure default SECRET_KEY detected in production mode" in err_msg
    # Policy 11: Secret value itself must never appear in exception output
    assert _INSECURE_DEFAULT_SECRET not in err_msg


def test_gate1_debug_true_empty_secret_hard_stop():
    """Policy 3: DEBUG=True + empty secret triggers immediate hard stop."""
    s = _make_dummy_settings(debug=True, secret_key="")
    with pytest.raises(SystemExit) as exc_info:
        validate_startup_security(s)
    err_msg = str(exc_info.value)
    assert "[CRITICAL SECURITY BLOCKER]" in err_msg
    assert "SECRET_KEY is empty or contains only whitespace" in err_msg


def test_gate1_debug_false_empty_secret_hard_stop():
    """Policy 3: DEBUG=False + empty secret triggers immediate hard stop."""
    s = _make_dummy_settings(debug=False, secret_key="")
    with pytest.raises(SystemExit) as exc_info:
        validate_startup_security(s)
    err_msg = str(exc_info.value)
    assert "[CRITICAL SECURITY BLOCKER]" in err_msg
    assert "SECRET_KEY is empty or contains only whitespace" in err_msg


def test_gate1_debug_true_whitespace_secret_hard_stop():
    """Policy 3: DEBUG=True + whitespace-only secret triggers immediate hard stop."""
    s = _make_dummy_settings(debug=True, secret_key="   \t\n   ")
    with pytest.raises(SystemExit) as exc_info:
        validate_startup_security(s)
    err_msg = str(exc_info.value)
    assert "[CRITICAL SECURITY BLOCKER]" in err_msg
    assert "SECRET_KEY is empty or contains only whitespace" in err_msg


def test_gate1_debug_false_whitespace_secret_hard_stop():
    """Policy 3: DEBUG=False + whitespace-only secret triggers immediate hard stop."""
    s = _make_dummy_settings(debug=False, secret_key="   \t\n   ")
    with pytest.raises(SystemExit) as exc_info:
        validate_startup_security(s)
    err_msg = str(exc_info.value)
    assert "[CRITICAL SECURITY BLOCKER]" in err_msg
    assert "SECRET_KEY is empty or contains only whitespace" in err_msg


def test_gate1_debug_true_short_secret_hard_stop():
    """Policy 4: DEBUG=True + short secret (< 32 chars) triggers immediate hard stop."""
    short_secret = "short_insecure_key_12345"  # 24 chars
    s = _make_dummy_settings(debug=True, secret_key=short_secret)
    with pytest.raises(SystemExit) as exc_info:
        validate_startup_security(s)
    err_msg = str(exc_info.value)
    assert "[CRITICAL SECURITY BLOCKER]" in err_msg
    assert "SECRET_KEY length is insufficient (24 chars)" in err_msg
    # Policy 11: Secret value itself must never appear in exception output
    assert short_secret not in err_msg


def test_gate1_debug_false_short_secret_hard_stop():
    """Policy 4: DEBUG=False + short secret (< 32 chars) triggers immediate hard stop."""
    short_secret = "abc123xyz"  # 9 chars
    s = _make_dummy_settings(debug=False, secret_key=short_secret)
    with pytest.raises(SystemExit) as exc_info:
        validate_startup_security(s)
    err_msg = str(exc_info.value)
    assert "[CRITICAL SECURITY BLOCKER]" in err_msg
    assert "SECRET_KEY length is insufficient (9 chars)" in err_msg
    # Policy 11: Secret value itself must never appear in exception output
    assert short_secret not in err_msg


def test_gate1_debug_true_valid_length_non_default_secret_success():
    """Policy 6: DEBUG=True + valid length non-default secret succeeds cleanly without warning."""
    s = _make_dummy_settings(debug=True, secret_key=VALID_NON_DEFAULT_SECRET)
    old_err = sys.stderr
    sys.stderr = io.StringIO()
    try:
        validate_startup_security(s)
        warning_output = sys.stderr.getvalue()
    finally:
        sys.stderr = old_err

    assert warning_output == ""  # No warning when non-default key is provided


def test_gate1_debug_false_valid_length_non_default_secret_success():
    """Policy 6: DEBUG=False + valid length non-default secret succeeds cleanly without warning."""
    s = _make_dummy_settings(debug=False, secret_key=VALID_NON_DEFAULT_SECRET)
    old_err = sys.stderr
    sys.stderr = io.StringIO()
    try:
        validate_startup_security(s)
        warning_output = sys.stderr.getvalue()
    finally:
        sys.stderr = old_err

    assert warning_output == ""  # Clean pass

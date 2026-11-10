"""Unit tests for Stage B Phase 6.1 Database Initializer (init_db.py).
Strictly verifies that init_database enforces explicit target requirements,
rejects persistent targets by default, protects trasco.db, and runs in-memory cleanly.
"""

import os
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.init_db import init_database, _is_protected_target
from app.models.base import Base


def _make_dummy_settings(debug: bool, secret_key: str) -> Settings:
    s = Settings()
    s.DEBUG = debug
    s.SECRET_KEY = secret_key
    return s


def test_init_db_missing_target_raises():
    """Rule 4: Reject when no target is provided."""
    with pytest.raises(ValueError, match="Missing target"):
        init_database()


def test_init_db_ambiguous_target_raises():
    """Rule 3: Reject when both target_engine and target_url are provided."""
    test_engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    with pytest.raises(ValueError, match="Ambiguous target"):
        init_database(target_engine=test_engine, target_url="sqlite:///:memory:")


def test_init_db_in_memory_target_engine_succeeds():
    """Rule 5: Target in-memory engine initializes all ORM tables."""
    test_engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    res = init_database(target_engine=test_engine)
    assert res is True

    # Verify tables were created on the test engine
    inspector = inspect(test_engine)
    tables = inspector.get_table_names()
    assert "users" in tables
    assert "security_preferences" in tables
    assert "detection_logs" in tables
    assert "threat_statistics" in tables


def test_init_db_in_memory_url_succeeds():
    """In-memory URL initializes tables and disposes engine cleanly."""
    res = init_database(target_url="sqlite:///:memory:")
    assert res is True


def test_init_db_persistent_rejected_by_default(tmp_path):
    """Rule 5: Persistent file target is rejected unless allow_persistent=True."""
    temp_db_file = tmp_path / "scratch_test.db"
    target_url = f"sqlite:///{temp_db_file}"
    with pytest.raises(ValueError, match="is a persistent database"):
        init_database(target_url=target_url)


def test_init_db_persistent_allowed_with_flag(tmp_path):
    """Persistent target on temporary scratch file succeeds when allow_persistent=True."""
    temp_db_file = tmp_path / "scratch_test.db"
    target_url = f"sqlite:///{temp_db_file}"
    res = init_database(target_url=target_url, allow_persistent=True)
    assert res is True
    assert temp_db_file.exists()


def test_init_db_protected_database_strictly_blocked():
    """Targeting protected trasco.db is blocked even if allow_persistent=True."""
    with pytest.raises(PermissionError, match="protected persistent database"):
        init_database(target_url="sqlite:///./trasco.db", allow_persistent=True)

    with pytest.raises(PermissionError, match="protected persistent database"):
        init_database(target_url="sqlite:///apps/backend/trasco.db", allow_persistent=True)


def test_init_db_security_validation_failure_blocks_before_ddl():
    """Security validation failure halts initialization with RuntimeError before DDL."""
    test_engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    # Invalid secret: short key in production
    bad_settings = _make_dummy_settings(debug=False, secret_key="too-short")

    with pytest.raises(RuntimeError, match="Startup security validation rejected"):
        init_database(target_engine=test_engine, current_settings=bad_settings)

    # Verify NO tables were created on the engine
    inspector = inspect(test_engine)
    assert inspector.get_table_names() == []


def test_init_db_does_not_dispose_caller_engine():
    """Caller-provided engine remains open and usable after init_database."""
    test_engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    init_database(target_engine=test_engine)

    # Engine is not disposed by init_database; can still query
    inspector = inspect(test_engine)
    assert "users" in inspector.get_table_names()


def test_init_db_cli_missing_url_exits_1(monkeypatch):
    """CLI fails and exits with 1 if --url argument is missing."""
    import sys
    from app.core.init_db import main

    monkeypatch.setattr(sys, "argv", ["init_db"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1

def test_init_db_cli_in_memory_url_succeeds(monkeypatch):
    """CLI succeeds and exits with 0 for in-memory SQLite URL."""
    import sys
    from app.core.init_db import main

    monkeypatch.setattr(sys, "argv", ["init_db", "--url", "sqlite:///:memory:"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0


def test_init_db_cli_protected_db_blocked(monkeypatch):
    """CLI rejects protected trasco.db target and exits with 1."""
    import sys
    from app.core.init_db import main

    monkeypatch.setattr(sys, "argv", ["init_db", "--url", "sqlite:///./trasco.db", "--confirm-persistent"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1

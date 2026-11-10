"""Unit tests for Stage B Phase 6.2 Schema Compatibility Probe (probe_schema_compatibility).
Verifies read-only schema introspection across valid, partial, and incompatible schemas.
Strictly isolated using SQLite in-memory engines.
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.core.database import (
    probe_schema_compatibility,
    is_application_ready,
    set_application_ready,
    reset_application_readiness,
)


def _create_in_memory_engine():
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def test_schema_probe_valid_schema():
    """Valid schema created via Base.metadata.create_all passes compatibility probe."""
    engine = _create_in_memory_engine()
    Base.metadata.create_all(bind=engine)

    result = probe_schema_compatibility(engine)
    assert result.compatible is True
    assert result.missing_tables == []
    assert result.missing_columns == []
    assert result.primary_key_mismatches == []
    assert result.nullability_mismatches == []
    assert result.missing_unique_indexes == []
    assert result.foreign_key_mismatches == []
    assert result.errors == []


def test_schema_probe_missing_table():
    """Empty database or missing tables are accurately detected and reported."""
    engine = _create_in_memory_engine()
    # Empty DB - no tables created
    result = probe_schema_compatibility(engine)
    assert result.compatible is False
    assert "users" in result.missing_tables
    assert "security_preferences" in result.missing_tables
    assert "detection_logs" in result.missing_tables
    assert "threat_statistics" in result.missing_tables


def test_schema_probe_missing_column():
    """Table exists but lacks one required column -> incompatible."""
    engine = _create_in_memory_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE users (
                id VARCHAR(36) PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'USER',
                created_at DATETIME,
                updated_at DATETIME
            )
        """))
        conn.execute(text("""
            CREATE TABLE security_preferences (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES users(id),
                avatar_enabled BOOLEAN,
                avatar_theme VARCHAR(50),
                audio_alert_enabled BOOLEAN,
                risk_threshold VARCHAR(20),
                auto_scan_urls BOOLEAN,
                updated_at DATETIME
            )
        """))
        conn.execute(text("""
            CREATE TABLE detection_logs (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) REFERENCES users(id),
                scan_type VARCHAR(20) NOT NULL,
                target_hash VARCHAR(64),
                sanitized_snippet VARCHAR(255) NOT NULL,
                risk_level VARCHAR(20) NOT NULL,
                risk_score INTEGER NOT NULL,
                threat_category VARCHAR(50) NOT NULL,
                detection_indicators JSON NOT NULL,
                recommendations JSON NOT NULL,
                latency_ms FLOAT,
                created_at DATETIME
            )
        """))
        conn.execute(text("""
            CREATE TABLE threat_statistics (
                id VARCHAR(36) PRIMARY KEY,
                record_date VARCHAR(10) NOT NULL,
                category VARCHAR(50) NOT NULL,
                risk_level VARCHAR(20) NOT NULL,
                count INTEGER DEFAULT 1
            )
        """))

    result = probe_schema_compatibility(engine)
    assert result.compatible is False
    assert any("users.display_name" in col for col in result.missing_columns)


def test_schema_probe_nullability_mismatch():
    """Column with nullable=True in DB when ORM declares nullable=False -> mismatch."""
    engine = _create_in_memory_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE users (
                id VARCHAR(36) PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                display_name VARCHAR(100) NULL,
                role VARCHAR(20) DEFAULT 'USER',
                created_at DATETIME,
                updated_at DATETIME
            )
        """))
    result = probe_schema_compatibility(engine)
    assert result.compatible is False
    assert any("users.display_name" in m for m in result.nullability_mismatches)


def test_schema_probe_foreign_key_missing():
    """Table exists but lacks required foreign key -> foreign_key_mismatches detected."""
    engine = _create_in_memory_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE users (
                id VARCHAR(36) PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                display_name VARCHAR(100) NOT NULL,
                role VARCHAR(20) DEFAULT 'USER',
                created_at DATETIME,
                updated_at DATETIME
            )
        """))
        conn.execute(text("""
            CREATE TABLE security_preferences (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) UNIQUE NOT NULL,
                avatar_enabled BOOLEAN,
                avatar_theme VARCHAR(50),
                audio_alert_enabled BOOLEAN,
                risk_threshold VARCHAR(20),
                auto_scan_urls BOOLEAN,
                updated_at DATETIME
            )
        """))
    result = probe_schema_compatibility(engine)
    assert result.compatible is False
    assert any("security_preferences.user_id" in fk for fk in result.foreign_key_mismatches)


def test_schema_probe_is_strictly_read_only():
    """Probe execution does not create or alter tables."""
    engine = _create_in_memory_engine()
    result1 = probe_schema_compatibility(engine)
    assert result1.compatible is False

    from sqlalchemy import inspect
    inspector = inspect(engine)
    assert inspector.get_table_names() == []


def test_schema_probe_type_mismatch_detected():
    """Column with incompatible type affinity is detected and fails compatibility."""
    engine = _create_in_memory_engine()
    # Create detection_logs with risk_score as VARCHAR instead of INTEGER
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE detection_logs (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36),
                scan_type VARCHAR(20) NOT NULL,
                target_hash VARCHAR(64),
                sanitized_snippet VARCHAR(255) NOT NULL,
                risk_level VARCHAR(20) NOT NULL,
                risk_score VARCHAR(50) NOT NULL,
                threat_category VARCHAR(50) NOT NULL,
                detection_indicators JSON NOT NULL,
                recommendations JSON NOT NULL,
                latency_ms FLOAT,
                created_at DATETIME
            )
        """))
    result = probe_schema_compatibility(engine)
    assert result.compatible is False
    assert any("detection_logs.risk_score" in tm for tm in result.type_mismatches)


def test_application_readiness_state_helpers():
    """Readiness state helpers manipulate and reset the worker flag properly."""
    reset_application_readiness()
    assert is_application_ready() is False

    set_application_ready(True)
    assert is_application_ready() is True

    reset_application_readiness()
    assert is_application_ready() is False

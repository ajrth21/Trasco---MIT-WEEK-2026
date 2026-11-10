"""Unit tests for Stage B Phase 6.3 SQLite Foreign Key Enforcement.
Verifies that PRAGMA foreign_keys=ON is active and rejects orphaned child records.
Strictly isolated using SQLite in-memory engines.
"""

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.user import User, SecurityPreference


def _create_sqlite_engine_with_fk():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

    return engine


def test_sqlite_foreign_keys_pragma_enabled():
    """Verify PRAGMA foreign_keys returns 1 on new connections."""
    engine = _create_sqlite_engine_with_fk()
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA foreign_keys")).scalar()
        assert result == 1


def test_sqlite_invalid_foreign_key_insert_rejected():
    """Inserting a child record referencing a non-existent parent raises IntegrityError."""
    engine = _create_sqlite_engine_with_fk()
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()

    try:
        # Attempt to insert SecurityPreference with non-existent user_id
        pref = SecurityPreference(
            user_id="non-existent-user-uuid",
            avatar_enabled=True,
            avatar_theme="CYBER_GUARDIAN",
        )
        session.add(pref)
        with pytest.raises(IntegrityError, match="FOREIGN KEY constraint failed"):
            session.commit()
    finally:
        session.close()

def test_sqlite_valid_foreign_key_insert_succeeds():
    """Inserting a parent User record followed by a child SecurityPreference succeeds."""
    engine = _create_sqlite_engine_with_fk()
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()

    try:
        user = User(
            email="test_user@trasco.id",
            password_hash="hashed_pw_test",
            display_name="Analyst User",
            role="USER",
        )
        session.add(user)
        session.commit()

        # Insert child referencing valid user.id
        pref = SecurityPreference(
            user_id=user.id,
            avatar_enabled=True,
            avatar_theme="CYBER_GUARDIAN",
        )
        session.add(pref)
        session.commit()

        # Verify query
        saved_pref = session.query(SecurityPreference).filter_by(user_id=user.id).first()
        assert saved_pref is not None
        assert saved_pref.user.email == "test_user@trasco.id"
    finally:
        session.close()

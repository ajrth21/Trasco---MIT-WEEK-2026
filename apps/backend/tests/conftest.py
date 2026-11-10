"""Pytest fixtures for isolating backend test execution from persistent databases.

Architecture & Isolation Guarantees:
1. Module-level pre-import execution:
   Before `app.flask_app` is imported, this module creates the isolated in-memory
   SQLite engine (using `StaticPool`) and immediately patches `app.models.base.engine`
   and `app.models.base.SessionLocal`.
2. As a direct consequence, when `app.flask_app` is subsequently imported (e.g.,
   executing `from app.models.base import Base, engine, SessionLocal` and
   `Base.metadata.create_all(bind=engine)` at flask_app.py:33), it imports the
   isolated test engine and creates tables exclusively in RAM.
3. Dedicated test engine uses `StaticPool` with `connect_args={"check_same_thread": False}`
   so that all sessions across threads/connections share the exact same in-memory instance.
4. Safely restores original module references and disposes of the test engine on session teardown.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Step 1: Import base models module first (defines engine, SessionLocal, Base)
import app.models.base
from app.models.base import Base

# Step 2: Create dedicated isolated in-memory test engine BEFORE importing flask_app
_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Step 3: Initialize all tables defined on Base.metadata on the in-memory engine
Base.metadata.create_all(bind=_test_engine)

# Step 4: Create isolated sessionmaker bound strictly to the in-memory test engine
_TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

# Step 5: Save original references for clean teardown restoration
_orig_base_engine = app.models.base.engine
_orig_base_session = app.models.base.SessionLocal

# Step 6: Patch app.models.base BEFORE flask_app is imported
app.models.base.engine = _test_engine
app.models.base.SessionLocal = _TestSessionLocal

# Step 7: Now safely import app.models and app.flask_app
# When flask_app executes line 6 (`from app.models.base import Base, engine, SessionLocal`)
# and line 33 (`Base.metadata.create_all(bind=engine)`), it receives _test_engine!
import app.models
import app.flask_app

# Also patch any re-exported references on app.models and app.flask_app
if hasattr(app.models, "engine"):
    app.models.engine = _test_engine
if hasattr(app.models, "SessionLocal"):
    app.models.SessionLocal = _TestSessionLocal

if hasattr(app.flask_app, "engine"):
    app.flask_app.engine = _test_engine
if hasattr(app.flask_app, "SessionLocal"):
    app.flask_app.SessionLocal = _TestSessionLocal


@pytest.fixture(scope="session", autouse=True)
def isolate_test_database():
    """Global session-scoped autouse fixture maintaining the isolated in-memory database.

    Yields the test engine and sessionmaker, then disposes of the test engine and
    restores the original module references upon pytest session completion.
    """
    from app.core.database import set_application_ready, reset_application_readiness
    set_application_ready(True)

    yield {
        "engine": _test_engine,
        "SessionLocal": _TestSessionLocal,
    }

    # Teardown: Dispose test engine connections and restore original references
    reset_application_readiness()
    _test_engine.dispose()

    app.models.base.engine = _orig_base_engine
    app.models.base.SessionLocal = _orig_base_session

    if hasattr(app.models, "engine"):
        app.models.engine = _orig_base_engine
    if hasattr(app.models, "SessionLocal"):
        app.models.SessionLocal = _orig_base_session

    if hasattr(app.flask_app, "engine"):
        app.flask_app.engine = _orig_base_engine
    if hasattr(app.flask_app, "SessionLocal"):
        app.flask_app.SessionLocal = _orig_base_session

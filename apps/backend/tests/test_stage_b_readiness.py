"""Integration and unit tests for Stage B Phase 6.4 & 6.5 (Readiness & CORS).
Verifies fail-closed readiness guards, /health vs /health/ready, and CORS behavior
across both Flask WSGI and FastAPI ASGI frameworks using in-memory databases.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.database import (
    reset_application_readiness,
    set_application_ready,
    is_application_ready,
)
from app.models.base import Base
from app.flask_app import app as flask_app, bootstrap_flask_worker


try:
    import fastapi
    from starlette.testclient import TestClient
    from app.main import app as fastapi_app
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


def _create_in_memory_engine():
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


# ==============================================================================
# FLASK WSGI READINESS & CORS TESTS
# ==============================================================================

def test_flask_readiness_unready_blocks_business_routes():
    """When Flask worker is unready, business routes return 503 while /health returns 200."""
    reset_application_readiness()
    client = flask_app.test_client()

    # 1. Static Liveness is exempt and succeeds
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json["status"] == "healthy"

    # 2. Readiness probe reports 503 unready
    res_ready = client.get("/health/ready")
    assert res_ready.status_code == 503
    assert res_ready.json["status"] == "unready"

    # 3. Business route is fail-closed blocked with 503
    res_biz = client.post("/api/v1/detect/analyze", json={"content": "http://evil.com"})
    assert res_biz.status_code == 503
    assert res_biz.json["error"] == "Service Unavailable"


def test_flask_readiness_unready_cors_preflight():
    """Unready genuine CORS preflight returns 503 with proper CORS response headers."""
    reset_application_readiness()
    client = flask_app.test_client()

    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
    }
    res_preflight = client.options("/api/v1/detect/analyze", headers=headers)
    assert res_preflight.status_code == 503
    # Verify Flask-CORS attached allow-origin header to the 503 response
    assert res_preflight.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"


def test_flask_bootstrap_worker_succeeds_with_valid_schema():
    """Running bootstrap_flask_worker on a valid in-memory schema transitions readiness to True."""
    engine = _create_in_memory_engine()
    Base.metadata.create_all(bind=engine)

    # Valid settings
    valid_settings = Settings()
    valid_settings.DEBUG = True

    success = bootstrap_flask_worker(current_settings=valid_settings, target_engine=engine)
    assert success is True
    assert is_application_ready() is True

    client = flask_app.test_client()
    # Now /health/ready returns 200
    res_ready = client.get("/health/ready")
    assert res_ready.status_code == 200
    assert res_ready.json["status"] == "ready"


def test_flask_bootstrap_worker_fails_with_incompatible_schema():
    """Running bootstrap_flask_worker on an empty/broken schema keeps readiness False."""
    empty_engine = _create_in_memory_engine()
    # No tables created

    valid_settings = Settings()
    valid_settings.DEBUG = True

    success = bootstrap_flask_worker(current_settings=valid_settings, target_engine=empty_engine)
    assert success is False
    assert is_application_ready() is False


def test_flask_auto_bootstrap_exception_stays_unready(monkeypatch):
    """A bootstrap exception must not mark the Flask worker ready."""
    import app.flask_app

    readiness_updates = []

    def fail_bootstrap():
        raise RuntimeError("schema probe failed")

    monkeypatch.setattr(app.flask_app, "bootstrap_flask_worker", fail_bootstrap)
    monkeypatch.setattr(app.flask_app, "set_application_ready", readiness_updates.append)

    app.flask_app._auto_bootstrap()

    assert readiness_updates == [False]


def test_gunicorn_post_fork_hook(monkeypatch):
    """Gunicorn post_fork lifecycle hook executes bootstrap_flask_worker inside worker."""
    import importlib.util
    import sys
    from pathlib import Path

    conf_path = Path(__file__).resolve().parent.parent / "gunicorn.conf.py"
    spec = importlib.util.spec_from_file_location("gunicorn_conf", conf_path)
    gunicorn_conf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gunicorn_conf)

    assert hasattr(gunicorn_conf, "post_fork")
    assert callable(gunicorn_conf.post_fork)

    # 1. Test post_fork with valid schema
    engine = _create_in_memory_engine()
    Base.metadata.create_all(bind=engine)
    import app.flask_app
    monkeypatch.setattr(app.flask_app, "engine", engine)

    reset_application_readiness()
    assert is_application_ready() is False

    gunicorn_conf.post_fork(None, None)
    assert is_application_ready() is True

    # 2. Test post_fork with incompatible (empty) schema
    empty_engine = _create_in_memory_engine()
    monkeypatch.setattr(app.flask_app, "engine", empty_engine)

    reset_application_readiness()
    gunicorn_conf.post_fork(None, None)
    assert is_application_ready() is False



# ==============================================================================
# FASTAPI ASGI READINESS & CORS TESTS (Optional Alternative Runner)
# ==============================================================================

@pytest.mark.skipif(not HAS_FASTAPI, reason="FastAPI is an optional alternative runner and not installed in local environment")
def test_fastapi_unready_blocks_business_routes():
    """When FastAPI readiness is False, business endpoints return 503 while /health returns 200."""
    reset_application_readiness()
    client = TestClient(fastapi_app, raise_server_exceptions=False)

    # 1. Static Liveness probe succeeds
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    # 2. Readiness probe returns 503
    res_ready = client.get("/health/ready")
    assert res_ready.status_code == 503
    assert res_ready.json()["status"] == "unready"

    # 3. Business endpoint returns 503
    res_biz = client.get("/api/v1/analytics/overview")
    assert res_biz.status_code == 503
    assert res_biz.json()["error"] == "Service Unavailable"


@pytest.mark.skipif(not HAS_FASTAPI, reason="FastAPI is an optional alternative runner and not installed in local environment")
def test_fastapi_cors_preflight_handled_by_outer_middleware():
    """Starlette CORSMiddleware at the outer layer handles preflight requests directly."""
    reset_application_readiness()
    client = TestClient(fastapi_app, raise_server_exceptions=False)

    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
    }
    res_options = client.options("/api/v1/analytics/overview", headers=headers)
    assert res_options.status_code == 200
    assert res_options.headers.get("access-control-allow-origin") == "*"


@pytest.mark.skipif(not HAS_FASTAPI, reason="FastAPI is an optional alternative runner and not installed in local environment")
def test_fastapi_lifespan_startup_succeeds_with_valid_schema(monkeypatch):
    """FastAPI lifespan boots, verifies security and schema, and marks application ready."""
    test_engine = _create_in_memory_engine()
    Base.metadata.create_all(bind=test_engine)

    import app.main
    monkeypatch.setattr(app.main, "engine", test_engine)

    reset_application_readiness()
    with TestClient(fastapi_app) as client:
        assert is_application_ready() is True
        res_ready = client.get("/health/ready")
        assert res_ready.status_code == 200
        assert res_ready.json()["status"] == "ready"

    assert is_application_ready() is False


@pytest.mark.skipif(not HAS_FASTAPI, reason="FastAPI is an optional alternative runner and not installed in local environment")
def test_fastapi_lifespan_startup_fails_on_incompatible_schema(monkeypatch):
    """FastAPI lifespan raises RuntimeError on startup if database schema is missing."""
    empty_engine = _create_in_memory_engine()
    import app.main
    monkeypatch.setattr(app.main, "engine", empty_engine)

    reset_application_readiness()
    with pytest.raises(RuntimeError, match="Database schema compatibility probe failed"):
        with TestClient(fastapi_app):
            pass

    assert is_application_ready() is False

import json
import uuid

from flask import Response
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from app.core.migrate_browser_identity import migrate_browser_identity
from app.core.visitor import set_visitor_cookie
from app.models.base import SessionLocal
from app.models.detection import DetectionLog


def _client():
    from app.flask_app import app

    app.config["TESTING"] = True
    return app.test_client()


def _overview(client):
    response = client.get("/api/v1/analytics/overview")
    assert response.status_code == 200
    return response.get_json()


def _scan(client, content):
    return client.post(
        "/api/v1/detect/analyze",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"scanType": "TEXT", "content": content}),
    )


def test_browser_scans_and_analytics_are_isolated(monkeypatch):
    from app import flask_app

    scan_id = iter((str(uuid.uuid4()), str(uuid.uuid4())))
    monkeypatch.setattr(
        flask_app,
        "orchestrate_detection",
        lambda scan_type, content, metadata: {
            "scanId": next(scan_id),
            "riskLevel": "LOW",
            "riskScore": 0,
            "threatCategory": "SAFE",
            "detectionIndicators": [],
            "recommendedActions": [],
            "latencyMs": 0,
        },
    )

    first_browser = _client()
    second_browser = _client()

    first_cookie_response = first_browser.get("/api/v1/analytics/overview")
    second_cookie_response = second_browser.get("/api/v1/analytics/overview")
    first_cookie = first_cookie_response.headers["Set-Cookie"]
    second_cookie = second_cookie_response.headers["Set-Cookie"]
    assert first_cookie.split(";", 1)[0] != second_cookie.split(";", 1)[0]
    assert "HttpOnly" in first_cookie
    assert "SameSite=Lax" in first_cookie

    first_baseline = _overview(first_browser)
    second_baseline = _overview(second_browser)

    first_content = "Unique private scan for browser alpha."
    second_content = "Unique private scan for browser beta."
    assert _scan(first_browser, first_content).status_code == 200
    assert _scan(second_browser, second_content).status_code == 200

    first_result = _overview(first_browser)
    second_result = _overview(second_browser)

    assert first_result["riskBreakdown"]["totalScans"] == first_baseline["riskBreakdown"]["totalScans"] + 1
    assert second_result["riskBreakdown"]["totalScans"] == second_baseline["riskBreakdown"]["totalScans"] + 1

    first_history = [item["sanitizedSnippet"] for item in first_result["recentHistory"]]
    second_history = [item["sanitizedSnippet"] for item in second_result["recentHistory"]]
    assert any("browser alpha" in item for item in first_history)
    assert not any("browser beta" in item for item in first_history)
    assert any("browser beta" in item for item in second_history)
    assert not any("browser alpha" in item for item in second_history)


def test_legacy_unassigned_scans_are_not_exposed_to_new_browsers():
    db = SessionLocal()
    try:
        db.add(
            DetectionLog(
                id=str(uuid.uuid4()),
                scan_type="TEXT",
                sanitized_snippet="Legacy shared scan",
                risk_level="LOW",
                risk_score=0,
                threat_category="SAFE",
            )
        )
        db.commit()
    finally:
        db.close()

    overview = _overview(_client())

    assert all(
        item["sanitizedSnippet"] != "Legacy shared scan"
        for item in overview["recentHistory"]
    )


def test_browser_identity_migration_is_additive_and_idempotent():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    try:
        with engine.begin() as connection:
            connection.execute(
                text("CREATE TABLE detection_logs (id VARCHAR(36) PRIMARY KEY)")
            )
            connection.execute(
                text("INSERT INTO detection_logs (id) VALUES ('existing-log')")
            )

        migrate_browser_identity(engine)
        migrate_browser_identity(engine)

        columns = {column["name"] for column in inspect(engine).get_columns("detection_logs")}
        indexes = {index["name"] for index in inspect(engine).get_indexes("detection_logs")}
        assert "visitor_id" in columns
        assert "ix_detection_logs_visitor_id" in indexes
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT id FROM detection_logs")
            ).scalar_one() == "existing-log"
    finally:
        engine.dispose()


def test_production_visitor_cookie_is_secure_and_extension_compatible():
    response = Response("")
    set_visitor_cookie(response, uuid.uuid4().hex, secure=True)

    cookie = response.headers["Set-Cookie"]
    assert "Secure" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=None" in cookie
    assert "Path=/" in cookie

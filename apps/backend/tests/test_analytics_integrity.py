"""
Unit tests for TRASCO Phase 7.3 Data Integrity & Analytics Aggregation.
Verifies data lineage from detection logs to analytics overview using an isolated in-memory engine.
"""

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.detection import DetectionLog
from app.services.analytics_service import compute_security_overview


def _create_isolated_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, TestingSession


def test_empty_database_clean_state():
    """An empty database returns 0 scans and clean empty metrics (no fabricated 18 seed records)."""
    engine, Session = _create_isolated_db()
    db = Session()
    try:
        overview = compute_security_overview(db)
        assert overview.riskBreakdown.totalScans == 0
        assert overview.riskBreakdown.lowRiskCount == 0
        assert overview.riskBreakdown.mediumRiskCount == 0
        assert overview.riskBreakdown.highRiskCount == 0
        assert overview.riskBreakdown.unknownRiskCount == 0
        assert overview.securityHygieneScore == 100
        assert overview.threatDistribution == []
        assert overview.recentHistory == []
        assert len(overview.weeklyTrends) == 7
        assert all(t.scans == 0 for t in overview.weeklyTrends)
    finally:
        db.close()
        engine.dispose()


def test_data_integrity_four_scans_verification():
    """
    Controlled Phase 7.3 Data Integrity Test:
    Inserts 1 SAFE, 1 HIGH, 1 MEDIUM, and 1 UNKNOWN failed scan.
    Verifies:
      totalScans = 4
      lowRiskCount = 1 (Safe)
      highRiskCount = 1 (Critical)
      mediumRiskCount = 1 (Warning)
      unknownRiskCount = 1 (Failed/Unknown)
    """
    engine, Session = _create_isolated_db()
    db = Session()
    try:
        now = datetime.now(timezone.utc)

        # 1. SAFE completed scan
        scan_safe = DetectionLog(
            id=str(uuid.uuid4()),
            scan_type="IMAGE",
            target_hash="hash_safe",
            sanitized_snippet="Bukti transfer BCA valid",
            risk_level="LOW",
            risk_score=15,
            threat_category="SAFE",
            created_at=now
        )

        # 2. HIGH completed scan
        scan_high = DetectionLog(
            id=str(uuid.uuid4()),
            scan_type="IMAGE",
            target_hash="hash_high",
            sanitized_snippet="Bukti transfer Mandiri palsu",
            risk_level="HIGH",
            risk_score=85,
            threat_category="FAKE_TRANSFER_SLIP",
            created_at=now
        )

        # 3. MEDIUM completed scan
        scan_med = DetectionLog(
            id=str(uuid.uuid4()),
            scan_type="IMAGE",
            target_hash="hash_med",
            sanitized_snippet="Bukti transfer terindikasi editan",
            risk_level="MEDIUM",
            risk_score=50,
            threat_category="SUSPICIOUS_PROMOTION",
            created_at=now
        )

        # 4. UNKNOWN failed scan (risk_score: -1 fallback, threat_category: "UNKNOWN")
        scan_failed = DetectionLog(
            id=str(uuid.uuid4()),
            scan_type="IMAGE",
            target_hash="hash_failed",
            sanitized_snippet="[Image Scan: Failed to parse]",
            risk_level="UNKNOWN",
            risk_score=-1,
            threat_category="UNKNOWN",
            created_at=now
        )

        db.add_all([scan_safe, scan_high, scan_med, scan_failed])
        db.commit()

        # Compute overview
        overview = compute_security_overview(db)

        # Assert exact expected metrics
        assert overview.riskBreakdown.totalScans == 4
        assert overview.riskBreakdown.lowRiskCount == 1
        assert overview.riskBreakdown.highRiskCount == 1
        assert overview.riskBreakdown.mediumRiskCount == 1
        assert overview.riskBreakdown.unknownRiskCount == 1

        # Assert hygiene score is penalized only by real threats: 100 - (1*10) - (1*5) = 85
        assert overview.securityHygieneScore == 85

        # Assert category distribution contains real records
        categories = {item.category: item.count for item in overview.threatDistribution}
        assert categories.get("SAFE") == 1
        assert categories.get("FAKE TRANSFER SLIP") == 1
        assert categories.get("SUSPICIOUS PROMOTION") == 1
        assert categories.get("UNKNOWN") == 1

        # Assert recent history contains all 4 items with proper nullable handling
        assert len(overview.recentHistory) == 4
        failed_history = next(item for item in overview.recentHistory if item.id == scan_failed.id)
        assert failed_history.riskScore is None
        assert failed_history.riskLevel == "UNKNOWN"

    finally:
        db.close()
        engine.dispose()


def test_analytics_aggregates_all_records_beyond_recent_history():
    """Overview totals and distributions include records beyond the recent-history window."""
    engine, Session = _create_isolated_db()
    db = Session()
    try:
        db.add_all([
            DetectionLog(
                id=str(uuid.uuid4()),
                scan_type="TEXT",
                sanitized_snippet=f"Test record {index}",
                risk_level="LOW",
                risk_score=10,
                threat_category="SAFE",
            )
            for index in range(65)
        ])
        db.commit()

        overview = compute_security_overview(db)

        assert overview.riskBreakdown.totalScans == 65
        assert overview.riskBreakdown.lowRiskCount == 65
        assert len(overview.recentHistory) == 10
        assert overview.threatDistribution[0].count == 65
        assert overview.threatDistribution[0].percentage == 100.0
    finally:
        db.close()
        engine.dispose()


def test_history_endpoint_hides_failed_scan_sentinel_score():
    """Public history must serialize the internal failed-scan sentinel as null."""
    from app.flask_app import SessionLocal, app as flask_app

    scan_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        db.add(DetectionLog(
            id=scan_id,
            scan_type="IMAGE",
            sanitized_snippet="[Image Scan: unavailable]",
            risk_level="UNKNOWN",
            risk_score=-1,
            threat_category="UNKNOWN",
        ))
        db.commit()
    finally:
        db.close()

    response = flask_app.test_client().get("/api/v1/analytics/history")
    assert response.status_code == 200
    item = next(row for row in response.get_json() if row["id"] == scan_id)
    assert item["riskLevel"] == "UNKNOWN"
    assert item["riskScore"] is None


def test_weekly_trend_date_bucketing():
    """Weekly trends accurately bucket scans across actual calendar days."""
    engine, Session = _create_isolated_db()
    db = Session()
    try:
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)

        s1 = DetectionLog(id=str(uuid.uuid4()), scan_type="TEXT", sanitized_snippet="T1", risk_level="LOW", risk_score=10, threat_category="SAFE", created_at=now)
        s2 = DetectionLog(id=str(uuid.uuid4()), scan_type="TEXT", sanitized_snippet="T2", risk_level="HIGH", risk_score=90, threat_category="OTP_THEFT", created_at=now)
        s3 = DetectionLog(id=str(uuid.uuid4()), scan_type="URL", sanitized_snippet="U1", risk_level="MEDIUM", risk_score=50, threat_category="TYPOSQUATTING", created_at=yesterday)
        s4 = DetectionLog(id=str(uuid.uuid4()), scan_type="TEXT", sanitized_snippet="T3", risk_level="LOW", risk_score=20, threat_category="SAFE", created_at=two_days_ago)

        db.add_all([s1, s2, s3, s4])
        db.commit()

        overview = compute_security_overview(db)
        trends = overview.weeklyTrends
        assert len(trends) == 7

        # Today's bucket should have 2 scans and 1 threat
        today_trend = trends[-1]
        assert today_trend.scans == 2
        assert today_trend.threatsPrevented == 1

        # Yesterday's bucket should have 1 scan and 1 threat
        yesterday_trend = trends[-2]
        assert yesterday_trend.scans == 1
        assert yesterday_trend.threatsPrevented == 1

        # Two days ago should have 1 scan and 0 threats
        two_days_trend = trends[-3]
        assert two_days_trend.scans == 1
        assert two_days_trend.threatsPrevented == 0

    finally:
        db.close()
        engine.dispose()

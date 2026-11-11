from datetime import datetime, time, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from app.models.detection import DetectionLog
from app.schemas.analytics import (
    SecurityOverviewResponse, RiskBreakdown, ThreatDistribution, 
    DailyScanTrend, ScanHistoryItem
)


def compute_security_overview(
    db: Session,
    user_id: str | None = None,
    visitor_id: str | None = None,
) -> SecurityOverviewResponse:
    query = db.query(DetectionLog)
    if user_id is not None:
        query = query.filter(DetectionLog.user_id == user_id)
    elif visitor_id is not None:
        query = query.filter(DetectionLog.visitor_id == visitor_id)

    total_scans = query.with_entities(func.count(DetectionLog.id)).scalar() or 0
    risk_counts = dict(
        query.with_entities(DetectionLog.risk_level, func.count(DetectionLog.id))
        .group_by(DetectionLog.risk_level)
        .all()
    )
    low_count = risk_counts.get("LOW", 0)
    med_count = risk_counts.get("MEDIUM", 0)
    high_count = risk_counts.get("HIGH", 0)
    unknown_count = query.filter(
        or_(
            DetectionLog.risk_level.notin_(("LOW", "MEDIUM", "HIGH")),
            DetectionLog.risk_score < 0,
        )
    ).with_entities(func.count(DetectionLog.id)).scalar() or 0

    # Honest hygiene score: 100 for clean slate, penalized by real detected threats (range: 0 to 100)
    if total_scans == 0:
        hygiene_score = 100
    else:
        hygiene_score = max(0, min(100, int(100 - (high_count * 10) - (med_count * 5))))

    # Real Category counts from persisted records
    category_counts = dict(
        query.with_entities(DetectionLog.threat_category, func.count(DetectionLog.id))
        .group_by(DetectionLog.threat_category)
        .all()
    )

    threat_dist = [
        ThreatDistribution(
            category=(cat or "UNVERIFIED").replace("_", " "),
            count=cnt,
            percentage=round((cnt / total_scans) * 100, 1) if total_scans > 0 else 0.0
        )
        for cat, cnt in category_counts.items()
    ]

    # Real Weekly trend based on actual timestamps of last 7 days
    today = datetime.now(timezone.utc).date()
    daily_buckets = {today - timedelta(days=i): {"scans": 0, "threats": 0} for i in range(6, -1, -1)}
    week_start = datetime.combine(today - timedelta(days=6), time.min, tzinfo=timezone.utc)
    trend_logs = query.filter(DetectionLog.created_at >= week_start).all()

    for l in trend_logs:
        if l.created_at:
            log_date = l.created_at.date() if hasattr(l.created_at, "date") else None
            if log_date and log_date in daily_buckets:
                daily_buckets[log_date]["scans"] += 1
                if l.risk_level in ("HIGH", "MEDIUM"):
                    daily_buckets[log_date]["threats"] += 1

    trends = [
        DailyScanTrend(
            date=day.strftime("%a"),
            scans=metrics["scans"],
            threatsPrevented=metrics["threats"]
        )
        for day, metrics in daily_buckets.items()
    ]

    # Real Recent history from persisted logs
    logs = query.order_by(desc(DetectionLog.created_at)).limit(10).all()
    recent_items = [
        ScanHistoryItem(
            id=l.id,
            scanType=l.scan_type,
            sanitizedSnippet=l.sanitized_snippet,
            riskLevel=l.risk_level,
            riskScore=l.risk_score if (l.risk_score is not None and l.risk_score >= 0) else None,
            threatCategory=(l.threat_category or "PERIKSA MANUAL").replace("_", " "),
            createdAt=l.created_at.strftime("%Y-%m-%d %H:%M") if l.created_at else ""
        )
        for l in logs[:10]
    ]

    # Adaptive mitigation recommendations
    key_advice = []
    if high_count > 0:
        key_advice.append("Terdeteksi ancaman kritis: Segera amankan akun, ubah kata sandi, dan hubungi institusi perbankan resmi Anda.")
    if med_count > 0:
        key_advice.append("Waspadai rekayasa sosial: Jangan pernah mentransfer uang jaminan untuk lowongan kerja atau undian.")

    # Always include baseline fundamental advisories
    key_advice.extend([
        "JANGAN membagikan kode OTP atau PIN m-banking kepada siapa pun, termasuk pihak yang mengaku customer service.",
        "Verifikasi keaslian bukti transfer melalui mutasi rekening m-banking resmi sebelum mengirimkan barang atau jasa.",
        "Selalu periksa nama domain bank resmi (.co.id atau .id) sebelum memasukkan informasi login atau transaksi."
    ])

    return SecurityOverviewResponse(
        securityHygieneScore=hygiene_score,
        riskBreakdown=RiskBreakdown(
            lowRiskCount=low_count,
            mediumRiskCount=med_count,
            highRiskCount=high_count,
            unknownRiskCount=unknown_count,
            totalScans=total_scans
        ),
        threatDistribution=threat_dist,
        weeklyTrends=trends,
        recentHistory=recent_items,
        keyAdvice=key_advice[:3]
    )

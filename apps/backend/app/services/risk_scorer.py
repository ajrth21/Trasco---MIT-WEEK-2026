import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from app.services.heuristic_engine import analyze_url_heuristics, analyze_text_heuristics
from app.services.gemini_service import analyze_with_gemini
from app.services.image_validator import validate_image_payload
from app.services.image_analyzer import analyze_image_with_gemini
from app.schemas.detection import ErrorDetail


def determine_risk_level(score: int) -> str:
    if score >= 70:
        return "HIGH"
    elif score >= 35:
        return "MEDIUM"
    return "LOW"


def orchestrate_image_detection(content: str, mime_type: str, metadata: Dict[str, Any] = None) -> Tuple[Dict[str, Any], int]:
    """
    Dedicated fail-closed orchestrator for IMAGE scam detection.
    Enforces the 14-stage validation pipeline and strict fail-closed invariants.
    Returns: (AnalyzeResponse dict, http_status_code)
    """
    start_time = datetime.now()
    scan_id = str(uuid.uuid4())

    # Step 1: 14-Stage Image Validation Pipeline
    is_valid, decoded_bytes, val_error, val_status = validate_image_payload(content, mime_type)
    if not is_valid:
        # Determine status enum based on error code
        status = "INVALID_REQUEST" if val_status == 400 or val_status == 413 else "INVALID_IMAGE"
        latency_ms = round((datetime.now() - start_time).total_seconds() * 1000, 2)
        return {
            "success": False,
            "status": status,
            "scanId": scan_id,
            "riskLevel": "UNKNOWN",
            "riskScore": None,
            "threatCategory": None,
            "summary": val_error.message if val_error else "Validasi citra gagal.",
            "detectionIndicators": [],
            "recommendedActions": ["Unggah file bukti transfer asli dalam format JPEG, PNG, atau WebP (maks. 5MB)."],
            "avatarGuidance": {
                "mood": "CAUTION_ALERT",
                "speechText": "Peringatan: Format gambar tidak valid atau tidak didukung.",
                "accentColor": "#F59E0B",
                "recommendedActionPrimary": "Unggah Ulang",
                "recommendedActionSecondary": "Bantuan"
            },
            "error": val_error.model_dump() if val_error else None,
            "analyzedAt": datetime.now(timezone.utc).isoformat(),
            "latencyMs": latency_ms
        }, val_status

    # Step 2: Gemini Vision Multimodal Analysis
    ai_result, ai_error, ai_status = analyze_image_with_gemini(decoded_bytes, mime_type)
    if not ai_result:
        # Fail-closed invariant on AI failure
        status = "ANALYSIS_UNAVAILABLE" if ai_status == 503 else "ANALYSIS_FAILED"
        latency_ms = round((datetime.now() - start_time).total_seconds() * 1000, 2)
        return {
            "success": False,
            "status": status,
            "scanId": scan_id,
            "riskLevel": "UNKNOWN",
            "riskScore": None,
            "threatCategory": None,
            "summary": ai_error.message if ai_error else "Analisis forensik citra tidak dapat diselesaikan.",
            "detectionIndicators": [],
            "recommendedActions": [
                "Buka aplikasi m-banking resmi Anda dan periksa mutasi rekening secara langsung.",
                "Jangan melepaskan dana atau pesanan sebelum dana terverifikasi masuk mutasi."
            ],
            "avatarGuidance": {
                "mood": "CAUTION_ALERT",
                "speechText": "Layanan AI tidak dapat menganalisis gambar. Periksa mutasi bank Anda secara manual.",
                "accentColor": "#F59E0B",
                "recommendedActionPrimary": "Cek Mutasi Manual",
                "recommendedActionSecondary": "Coba Lagi Nanti"
            },
            "error": ai_error.model_dump() if ai_error else None,
            "analyzedAt": datetime.now(timezone.utc).isoformat(),
            "latencyMs": latency_ms
        }, ai_status

    # Step 3: Map AI Result to COMPLETED Invariant
    confidence = ai_result.get("confidenceScore", 0)
    is_scam = ai_result.get("isScam", False)

    # Calculate risk score
    if is_scam:
        final_score = max(35, min(100, int(confidence)))
    else:
        final_score = max(0, min(34, int(100 - confidence)))

    risk_level = determine_risk_level(final_score)
    category = ai_result.get("threatCategory", "FAKE_TRANSFER_SLIP" if is_scam else "SAFE")
    summary = ai_result.get("summary", "Analisis visual bukti transfer selesai.")
    indicators = ai_result.get("aiIndicators", [])
    recommended_actions = ai_result.get("recommendedActions", [
        "Verifikasi transaksi melalui aplikasi perbankan resmi Anda."
    ])

    if risk_level == "HIGH":
        accent_color = "#EF4444"
        avatar_mood = "CRITICAL_SHIELD"
    elif risk_level == "MEDIUM":
        accent_color = "#F59E0B"
        avatar_mood = "CAUTION_ALERT"
    else:
        accent_color = "#10B981"
        avatar_mood = "IDLE_VIGILANT"

    speech_text = ai_result.get("speechWarning", f"Status analisis {risk_level}. Tetap waspada saat bertransaksi.")
    latency_ms = round((datetime.now() - start_time).total_seconds() * 1000, 2)

    return {
        "success": True,
        "status": "COMPLETED",
        "scanId": scan_id,
        "riskLevel": risk_level,
        "riskScore": final_score,
        "threatCategory": category,
        "summary": summary,
        "detectionIndicators": indicators,
        "recommendedActions": recommended_actions,
        "avatarGuidance": {
            "mood": avatar_mood,
            "speechText": speech_text,
            "accentColor": accent_color,
            "recommendedActionPrimary": recommended_actions[0] if recommended_actions else "Tutup Halaman",
            "recommendedActionSecondary": "Pelajari Modus Ini"
        },
        "error": None,
        "analyzedAt": datetime.now(timezone.utc).isoformat(),
        "latencyMs": latency_ms
    }, 200


def orchestrate_detection(scan_type: str, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Orchestrates heuristic and AI detection for URL and TEXT scans."""
    if scan_type == "IMAGE":
        # Safe forwarder if invoked generically
        mime = (metadata or {}).get("mimeType", "image/jpeg")
        res, _ = orchestrate_image_detection(content, mime, metadata)
        return res

    start_time = datetime.now()
    indicators: List[Dict[str, Any]] = []
    category = "SAFE"
    final_score = 0
    summary = "Aktivitas terverifikasi aman. Tidak ditemukan indikator penipuan atau ancaman siber."
    recommended_actions: List[str] = ["Tetap berhati-hati saat berselancar di internet."]
    
    avatar_mood = "IDLE_VIGILANT"
    speech_text = "Status aman. TRASCO terus menjaga aktivitas digital Anda."
    accent_color = "#10B981"  # Emerald

    mode = (metadata or {}).get("mode", "active_deep")

    # Step 1: Run Heuristics
    if scan_type == "URL":
        h_result = analyze_url_heuristics(content)
        h_score = h_result["heuristicScore"]
        indicators.extend(h_result["indicators"])
        if h_result["threatCategory"] != "SAFE":
            category = h_result["threatCategory"]
    elif scan_type == "TEXT":
        h_result = analyze_text_heuristics(content)
        h_score = h_result["heuristicScore"]
        indicators.extend(h_result["indicators"])
        if h_result["threatCategory"] != "SAFE":
            category = h_result["threatCategory"]
    else:
        h_score = 0

    # Step 2: Run Gemini AI (Only for active user-triggered scans to conserve quota)
    ai_result = None
    if mode != "passive_heuristic":
        try:
            if scan_type in ["URL", "TEXT"]:
                ai_result = analyze_with_gemini(scan_type, content)
        except Exception:
            ai_result = None

    # Step 3: Hybrid Score Fusion & Anti-Prompt-Injection Gatekeeper
    if ai_result:
        ai_score = ai_result.get("confidenceScore", 0)
        ai_category = ai_result.get("threatCategory", "SAFE")
        
        for ind in ai_result.get("aiIndicators", []):
            if not any(existing["indicator"] == ind.get("indicator") for existing in indicators):
                indicators.append(ind)

        if h_score >= 70:
            final_score = max(h_score, int((0.5 * ai_score) + (0.5 * h_score)))
        elif h_score > 0:
            blended = int((0.6 * ai_score) + (0.4 * h_score))
            final_score = max(h_score, blended)
        else:
            final_score = ai_score

        if ai_category != "SAFE":
            category = ai_category

        summary = ai_result.get("summary", summary)
        recommended_actions = ai_result.get("recommendedActions", recommended_actions)
        avatar_mood = ai_result.get("avatarMood", avatar_mood)
        speech_text = ai_result.get("speechWarning", speech_text)
    else:
        final_score = h_score
        if final_score >= 70:
            summary = f"Terdeteksi ancaman siber berisiko tinggi ({category.replace('_', ' ')}). Pola ancaman sesuai basis data modus penipuan."
            recommended_actions = [
                "JANGAN membagikan data pribadi, kode OTP, atau transfer dana.",
                "Segera tutup halaman atau hentikan komunikasi dengan kontak ini.",
                "Laporkan kontak atau domain ini ke pihak berwenang."
            ]
            avatar_mood = "CRITICAL_SHIELD"
            speech_text = "Bahaya! Ini adalah pola penipuan siber. Segera hentikan interaksi sekarang!"
        elif final_score >= 35:
            summary = "Ditemukan beberapa indikator mencurigakan pada konten atau domain ini."
            recommended_actions = [
                "Verifikasi keaslian pengirim melalui saluran resmi terpisah.",
                "Jangan terburu-buru mengambil keputusan finansial atau mengklik tautan."
            ]
            avatar_mood = "CAUTION_ALERT"
            speech_text = "Hati-hati, ada indikasi mencurigakan. Periksa kembali sebelum melanjutkan."

    final_score = max(0, min(100, final_score))
    risk_level = determine_risk_level(final_score)

    if risk_level == "HIGH":
        accent_color = "#EF4444"
        avatar_mood = "CRITICAL_SHIELD"
    elif risk_level == "MEDIUM":
        accent_color = "#F59E0B"
        avatar_mood = "CAUTION_ALERT"
    else:
        accent_color = "#10B981"
        avatar_mood = "IDLE_VIGILANT"

    latency_ms = round((datetime.now() - start_time).total_seconds() * 1000, 2)

    return {
        "success": True,
        "status": "COMPLETED",
        "scanId": str(uuid.uuid4()),
        "riskLevel": risk_level,
        "riskScore": final_score,
        "threatCategory": category,
        "summary": summary,
        "detectionIndicators": indicators,
        "recommendedActions": recommended_actions,
        "avatarGuidance": {
            "mood": avatar_mood,
            "speechText": speech_text,
            "accentColor": accent_color,
            "recommendedActionPrimary": recommended_actions[0] if recommended_actions else "Tutup Halaman",
            "recommendedActionSecondary": "Pelajari Modus Ini"
        },
        "error": None,
        "analyzedAt": datetime.now(timezone.utc).isoformat(),
        "latencyMs": latency_ms
    }

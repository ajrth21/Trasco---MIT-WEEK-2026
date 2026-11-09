import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from app.services.heuristic_engine import analyze_url_heuristics, analyze_text_heuristics
from app.services.gemini_service import analyze_with_gemini
from app.services.image_analyzer import analyze_image_with_gemini


def determine_risk_level(score: int) -> str:
    if score >= 70:
        return "HIGH"
    elif score >= 35:
        return "MEDIUM"
    return "LOW"


def orchestrate_detection(scan_type: str, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Orchestrates heuristic and AI detection, producing deterministic risk assessment."""
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
    elif scan_type == "IMAGE":
        h_score = 0  # Heuristics for image will rely on visual inspection
    else:
        h_score = 0

    # Step 2: Run Gemini AI (Only for active user-triggered scans to conserve 15 RPM quota)
    ai_result = None
    if mode != "passive_heuristic":
        try:
            if scan_type in ["URL", "TEXT"]:
                ai_result = analyze_with_gemini(scan_type, content)
            elif scan_type == "IMAGE":
                ai_result = analyze_image_with_gemini(content)
        except Exception:
            # Graceful fallback: on any unexpected AI failure/network error, rely on heuristics
            ai_result = None

    # Step 3: Hybrid Score Fusion & Anti-Prompt-Injection Gatekeeper
    if ai_result:
        ai_score = ai_result.get("confidenceScore", 0)
        ai_category = ai_result.get("threatCategory", "SAFE")
        
        # If AI found indicators, incorporate them
        for ind in ai_result.get("aiIndicators", []):
            if not any(existing["indicator"] == ind.get("indicator") for existing in indicators):
                indicators.append(ind)

        # --- ISSUE-SEC-02: Universal Heuristic Risk Floor ---
        # The deterministic heuristic engine is the trust anchor. An LLM response
        # (which may have been manipulated via indirect prompt injection) is NEVER
        # allowed to push the final score below what the heuristic engine found.
        #
        # Tier 1 (h_score >= 70 — CRITICAL): LLM cannot lower below h_score.
        #   Weighted blend is only used if it would RAISE the score.
        # Tier 2 (h_score > 0 — MEDIUM/LOW findings): Blend AI + heuristic,
        #   but clamp the result so final_score >= h_score (risk floor).
        # Tier 3 (h_score == 0 — no heuristic findings): Defer to AI score.
        if h_score >= 70:
            final_score = max(h_score, int((0.5 * ai_score) + (0.5 * h_score)))
        elif h_score > 0:
            blended = int((0.6 * ai_score) + (0.4 * h_score))
            final_score = max(h_score, blended)
        else:
            final_score = ai_score

        # Preserve heuristic threat category when LLM says SAFE but heuristics disagree
        if ai_category != "SAFE":
            category = ai_category
        # If AI says SAFE but heuristics found a real threat, keep heuristic category
        # (prevents LLM from erasing the threat classification)

        summary = ai_result.get("summary", summary)
        recommended_actions = ai_result.get("recommendedActions", recommended_actions)
        avatar_mood = ai_result.get("avatarMood", avatar_mood)
        speech_text = ai_result.get("speechWarning", speech_text)
    else:
        # Fallback to pure heuristics when Gemini is unavailable
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

    # Clamp score to [0, 100]
    final_score = max(0, min(100, final_score))
    risk_level = determine_risk_level(final_score)

    # Color mapping according to risk level
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
        "analyzedAt": datetime.now(timezone.utc).isoformat(),
        "latencyMs": latency_ms
    }


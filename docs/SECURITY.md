# TRASCO Security & Privacy Architecture Specification

> **Document:** Security Architecture, Threat Model, Privacy Controls, and Vulnerability Disclosure  
> **Compliance Standard:** UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi (UU PDP) & Security by Design  
> **Status:** Audited & Verified  

---

## 1. Threat Modeling & Attack Surface

TRASCO operates directly in the user's web browsing environment. The threat model accounts for four primary attack vectors:

| Threat Vector | Potential Impact | TRASCO Mitigation Strategy |
|---|---|---|
| **Malicious Webpage DOM Manipulation** | Host page script attempts to alter avatar warning or extract sensitive alert data. | **Closed Shadow DOM:** The avatar and speech cards are rendered in an isolated Shadow Root detached from the host page's global CSS and script namespace. |
| **DOM-based Cross-Site Scripting (XSS)** | Malicious scam text containing HTML/script tags executes within the extension context. | **Safe DOM API Policy:** 100% of dynamic text (`summary`, `indicators`, `recommendations`) is injected using `textContent` and `createTextNode`. Zero dynamic `innerHTML`. |
| **Cross-Origin Request Forgery (CSRF)** | Arbitrary public website executes requests against the local backend running on `localhost:8000`. | **Handshake Header Enforcement:** Endpoints require `X-Trasco-Source` header checks and validate origin headers before serving responses. |
| **Prompt Injection Attacks** | Scam message contains adversarial instructions to force the LLM to classify content as "SAFE". | **Anti-Prompt-Injection Gatekeeper:** Hardcoded deterministic heuristic checks cannot be overridden by LLM scores if heuristic score $\ge 70$. |
| **PII Data Leakage (UU PDP Violation)** | Storage of user phone numbers, OTPs, or bank credentials violates Indonesian privacy laws. | **Pre-Storage Scrubbing:** Regex-driven redaction sanitizes sensitive PII before persistence or logging. |

---

## 2. In-Depth Security Controls

### A. Anti-DOM XSS Policy
In [`apps/extension/src/content/content-script.js`](../apps/extension/src/content/content-script.js), dynamic data received from the backend is handled exclusively through safe DOM manipulation:
```javascript
// Example from content-script.js
speechText.textContent = '';
const summaryStrong = document.createElement('strong');
summaryStrong.textContent = data.summary || 'Aktivitas terverifikasi aman.';
speechText.appendChild(summaryStrong);

// Dynamic indicators
const textSpan = document.createElement('span');
const titleStrong = document.createElement('strong');
titleStrong.textContent = (ind.indicator || '') + ': ';
const explText = document.createTextNode(ind.explanation || '');
textSpan.appendChild(titleStrong);
textSpan.appendChild(explText);
```
No user-controlled string or API response payload is ever evaluated as raw HTML.

### B. Extension Permissions (Least-Privilege MV3)
In [`apps/extension/manifest.json`](../apps/extension/manifest.json):
- `permissions`:
  - `storage`: Required for local settings (`protectionEnabled`, `audioAlertEnabled`).
  - `activeTab`: Grants temporary access to current tab upon user interaction.
  - `contextMenus`: Enables right-click context menu options for text selection and image scanning.
- `host_permissions`:
  - `http://localhost:8000/*` and `http://127.0.0.1:8000/*`: Strictly scoped to the local TRASCO backend. No broad external domain permissions are requested.
- `background`:
  - Ephemeral Service Worker (`service_worker.js`, type `module`).

### C. Handshake Header & Origin Verification
In [`apps/backend/app/flask_app.py`](../apps/backend/app/flask_app.py):
```python
@app.before_request
def verify_request_security():
    if request.method == "OPTIONS" or request.path in ["/health", "/docs", "/openapi.json"]:
        return None

    origin = request.headers.get("Origin", "")
    trasco_source = request.headers.get("X-Trasco-Source", "")

    is_extension = origin.startswith("chrome-extension://") or origin.startswith("edge-extension://")
    is_local = "localhost" in origin or "127.0.0.1" in origin or origin == "" or not origin
    is_signed = trasco_source in ["Extension-Local", "Dashboard-Client"]

    if not (is_extension or is_local or is_signed):
        return jsonify({"error": "Unauthorized request origin. Blocked by TRASCO local firewall."}), 403
    return None
```

> **Documented Limitation:**  
> The presence of wildcard CORS `CORS(app, resources={r"/*": {"origins": "*"}})`, combined with `is_signed` logic alone, could allow a public webpage sending a custom `X-Trasco-Source` header to satisfy the condition if the browser completes preflight. Hardening to explicitly reject external origin hosts regardless of custom headers is planned.

### D. UU PDP Privacy Compliance & PII Scrubber
In [`apps/backend/app/core/scrubber.py`](../apps/backend/app/core/scrubber.py):
The `scrub_pii(text)` function sanitizes content before persistence:
- **NIK / Credit Card Numbers:** Redacts continuous 16-digit sequences $\rightarrow$ `[NIK_DISENSOR]`.
- **Indonesian Phone Numbers:** Redacts continuous `08...` and `+628...` sequences $\rightarrow$ `[NO_HP_DISENSOR]`.
- **Email Addresses:** Standard RFC-5322 regex $\rightarrow$ `[EMAIL_DISENSOR]`.
- **OTP Verification Codes:** Redacts 6-digit standalone numbers $\rightarrow$ `[OTP_DISENSOR]`.
- **Bank Account Numbers:** Redacts 10-14 digit standalone numbers $\rightarrow$ `[NO_REK_DISENSOR]`.

> **Documented Limitation:**  
> Phone numbers with delimiters (e.g., `0812-3456-7890` or `0812 3456 7890`) and 4-digit OTPs are currently not redacted by the continuous digit regex. Enhancements supporting delimiter patterns are scheduled.

### E. Anti-Prompt-Injection Gatekeeper
In [`apps/backend/app/services/risk_scorer.py`](../apps/backend/app/services/risk_scorer.py):
```python
# Gatekeeper Rule: If deterministic heuristics found high danger,
# LLM CANNOT lower the score below heuristic threshold (Mitigating Indirect Prompt Injection)
if h_score >= 70:
    final_score = max(h_score, int((0.5 * ai_score) + (0.5 * h_score)))
elif h_score > 0:
    final_score = int((0.6 * ai_score) + (0.4 * h_score))
else:
    final_score = ai_score
```

> **Documented Limitation:**  
> If heuristic score is in the medium danger range ($35 \le h\_score < 70$), a malicious prompt injection resulting in `ai_score = 0` could dilute the final score to $<35$, lowering the classification to `LOW`. A universal risk floor ($\text{final\_score} \ge h\_score$) is recommended.

### F. SQLite Concurrency & Storage Safety
- In [`apps/backend/app/models/base.py`](../apps/backend/app/models/base.py), the engine explicitly enables:
  - `PRAGMA journal_mode=WAL` (Write-Ahead Logging for non-blocking read/write concurrency).
  - `PRAGMA synchronous=NORMAL` (Balances durability and latency).
- Database credentials: SQLite is an embedded file engine requiring no network ports or external credentials.

### G. Secret Management Policy
- `.env` files are strictly excluded from git tracking via [`.gitignore`](../.gitignore).
- No production secrets or live Gemini API keys are committed to the repository.
- System operates in deterministic offline heuristic mode if `GEMINI_API_KEY` is omitted.

---

## 3. Vulnerability Reporting & Responsible Disclosure

If you discover a security vulnerability within TRASCO:
1. Do not open a public GitHub issue.
2. Report the vulnerability privately to the project maintainers.
3. Provide a clear proof-of-concept (PoC), steps to reproduce, and impact assessment.
4. Maintainers will verify and issue patches in accordance with responsible disclosure principles.


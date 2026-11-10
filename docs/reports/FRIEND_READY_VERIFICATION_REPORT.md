# TRASCO Friend-Ready Verification Report

**Date:** 10 November 2026
**Branch:** `feature/final-mvp-stabilization`
**Starting commit:** `58c1ee99d92bff8f41099ad53749b454678e63e0`

## Executive summary

The README now provides a first-run path for Windows PowerShell and
macOS/Linux, with explicit instructions for local secrets, isolated local
database initialization, running the Flask backend and Vite dashboard, and
performing a first URL/text scan.

The primary Flask backend was started against a newly initialized disposable
SQLite database. Liveness/readiness, API-level dashboard-origin CORS, URL and
text scans, invalid and valid image behavior without Gemini, analytics, history
serialization, and persistence were exercised over loopback. Vite also started
on an alternate port and served its entry page and React module. These are
runtime/API checks, **not browser end-to-end verification**.

## README audit

Each entry below records the state found during the audit and what was
corrected or confirmed in the updated README.

| # | Section | Initial assessment | Audit result and disposition |
|---|---|---|---|
| 1 | Project overview | Accurate | Kept the MVP purpose and advisory limitation. |
| 2 | Features and actual MVP scope | Incomplete | Clarified that Gemini image analysis requires configuration/upstream availability, education is limited to inline advice, and FastAPI auth/preferences are outside the primary Flask dashboard workflow. |
| 3 | Architecture | Accurate | Kept the Mermaid diagram for the primary Flask flow; documented the alternative FastAPI runner separately. |
| 4 | Technology stack | Accurate | CI confirms Python 3.11 and Node 20; requirements use version ranges. |
| 5 | Repository structure | Accurate | Checked paths against the repository; dashboard lockfile and extension manifest/icons exist. |
| 6 | Prerequisites and supported versions | Incomplete | Described Python 3.11 and Node 20 as CI versions/recommendations, and clarified Internet/Gemini requirements. |
| 7 | Installation | Incomplete | Corrected PowerShell paths and changed both platform copy commands so they do not overwrite an existing `.env`. Added Quick Start commands. |
| 8 | Environment variables | Incomplete | Documented required `SECRET_KEY`, local-only `DEBUG`, `DATABASE_URL`, and optional Gemini settings. Warned that `CORS_ORIGINS` in the sample does not configure Flask's hard-coded allowlist. |
| 9 | Database initialization | Incomplete | Confirmed the explicit initializer and protected-name guard; clarified it creates missing tables but does not migrate an existing schema. |
| 10 | Backend startup | Incomplete | Verified the primary command and loopback bind; made explicit that initialization must precede readiness. |
| 11 | Dashboard startup | Incomplete | Verified `npm ci`/`npm run dev`, Vite's configured host/port, and the backend's allowed origins. Added port-conflict guidance. |
| 12 | Browser extension installation | Accurate | Verified Manifest V3, referenced icons, popup, permissions, and backend host permissions. Kept the context-menu image URL limitation. |
| 13 | User workflows | Incomplete | Clarified that text/URL heuristics work without Gemini, while valid image analysis returns UNKNOWN/unavailable without Gemini. Added first-scan examples. |
| 14 | API endpoints and request/response | Inaccurate | Found that Flask history returned the internal `-1` sentinel and that image MIME can be inferred from its data URL. Fixed history serialization, added a regression test, and updated the request/status documentation (including HTTP 500). |
| 15 | Testing commands | Incomplete | Replaced the local-`.env` test assumption with commands from a new temporary working directory, preventing Pydantic settings from loading the project's `.env`; tests force in-memory SQLite. |
| 16 | Troubleshooting | Inaccurate | Removed the claim that the backend port can be changed through configuration alone. Documented that related backend, dashboard, extension permissions, and URL settings must stay aligned. |
| 17 | Security and privacy | Incomplete | Clarified the unused Flask `CORS_ORIGINS` setting, hard-coded local allowlist, and that the alternative FastAPI runner binds all interfaces with wildcard CORS and should not be exposed. |
| 18 | Known limitations | Incomplete | Explicitly stated that Gemini success, FastAPI runtime, standalone dashboard runtime, and browser E2E remain unverified. |
| 19 | Development instructions | Incomplete | Aligned backend tests, dashboard build, extension syntax checks, and shared-contract paths with actual project scripts/files. |
| 20 | License and acknowledgements | Accurate | Kept the hackathon acknowledgement and states that no repository-level `LICENSE` file was verified. |

### Quick Start added

The README Quick Start includes exact commands for creating the backend virtual
environment, installing requirements, preserving an existing `.env`,
initializing `trasco_local.db`, starting the backend and dashboard, opening the
local dashboard, and submitting the first scan. Gemini is explicitly optional
for URL/text heuristics and required for image analysis.

## Commands for a new developer

### Windows PowerShell

From the repository root:

```powershell
py -3.11 -m venv apps\backend\.venv
.\apps\backend\.venv\Scripts\python.exe -m pip install -r apps\backend\requirements.txt
Set-Location apps\backend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Set a fresh `SECRET_KEY` in `apps/backend/.env` using
`python -c "import secrets; print(secrets.token_hex(32))"`. `GEMINI_API_KEY` is
optional for URL/text scans and needed for Gemini image analysis. Then:

```powershell
.\.venv\Scripts\python.exe -m app.core.init_db --url sqlite:///./trasco_local.db --confirm-persistent
.\.venv\Scripts\python.exe -m app.flask_app
```

In another PowerShell window from the repository root:

```powershell
Set-Location apps\dashboard
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`, select **Simulator**, and scan a URL or text. A
command-line text scan is:

```powershell
$body = @{ scanType = 'TEXT'; content = 'Saya mendapat tawaran kerja, tetapi diminta membayar biaya deposit terlebih dahulu.' } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/detect/analyze -Method Post -ContentType 'application/json' -Headers @{ 'X-Trasco-Source' = 'Dashboard-Client' } -Body $body
```

### macOS/Linux

From the repository root:

```bash
python3.11 -m venv apps/backend/.venv
source apps/backend/.venv/bin/activate
python -m pip install -r apps/backend/requirements.txt
cd apps/backend
if [ ! -f .env ]; then cp .env.example .env; fi
```

Set `SECRET_KEY` in `.env`, initialize the new local database, and start Flask:

```bash
python -m app.core.init_db --url sqlite:///./trasco_local.db --confirm-persistent
python -m app.flask_app
```

In another terminal:

```bash
cd apps/dashboard
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`. A first text scan can also be sent with:

```bash
curl -sS -X POST http://127.0.0.1:8000/api/v1/detect/analyze \
  -H 'Content-Type: application/json' \
  -H 'X-Trasco-Source: Dashboard-Client' \
  -d '{"scanType":"TEXT","content":"Saya mendapat tawaran kerja, tetapi diminta membayar biaya deposit terlebih dahulu."}'
```

## Runtime smoke-test results

All smoke inputs were synthetic. The final clean run used a new disposable
database under `%TEMP%` and an isolated working directory with
`GEMINI_CONFIGURED=False`. HTTP requests used loopback directly with proxy
settings disabled. The database was initialized through the explicit
initializer; no migration was run.

| Check | Result |
|---|---|
| Flask process startup and `/health` | Passed; HTTP 200 |
| `/health/ready` against initialized disposable schema | Passed; HTTP 200 |
| Request from configured dashboard origin `http://127.0.0.1:5173` to analytics | Passed; HTTP 200 and matching `Access-Control-Allow-Origin` |
| Browser-style CORS preflight for detection | Passed at API level; HTTP 200 |
| URL scan | Passed; HTTP 200, `COMPLETED`, heuristic result `MEDIUM` for synthetic test URL |
| Text scan | Passed; HTTP 200, `COMPLETED`, heuristic result `HIGH` for synthetic test text |
| Invalid PNG/Base64 payload | Rejected as expected; HTTP 422, `INVALID_IMAGE` |
| Valid generated 2×2 PNG with Gemini explicitly disabled | Handled fail-closed; HTTP 503, `ANALYSIS_UNAVAILABLE`, `riskLevel: UNKNOWN`, `riskScore: null` |
| Analytics overview | Passed; HTTP 200, `totalScans: 4` after four synthetic scans |
| Analytics history | Passed; HTTP 200; failed image's public `riskScore` is `null` |
| Persistence | Passed; four rows in disposable SQLite, including internal `risk_score=-1` for the failed image |
| Vite dashboard startup | Passed on alternate loopback port `15173`; `/` and `/src/main.tsx` both returned HTTP 200 |
| Dashboard-to-backend browser flow | Not performed. API/CORS and Vite serving were checked separately; no browser automation was available. |
| Default ports | Port 5173 was occupied, so it was not used or interrupted. Port 8000 later became unavailable; the final isolated backend smoke used port 18137. README defaults remain the source-configured ports. |

The README PowerShell `Invoke-RestMethod` first-scan example was also executed
against the isolated backend on port `18137` and returned `COMPLETED` with a
heuristic risk result. This additional scan occurred after the four-record
analytics/persistence assertions above.

### Smoke-test isolation caveat

Early exploratory backend attempts were made before the Pydantic Settings
`.env` loading behavior was understood. `PYTHON_DOTENV_DISABLED=1` alone does
not disable Pydantic's configured `.env` source. A valid synthetic image
request returned HTTP 504 from the Gemini path instead of the expected no-key
response. The actual `.env` and key value were not manually inspected, printed,
or committed; the processes were stopped. Those exploratory requests used
synthetic URL/text/image inputs and are excluded from no-key verification.
The final run used a fresh working directory, explicitly printed only
`GEMINI_CONFIGURED=False`, and observed the expected HTTP 503 unavailable
response. No Gemini analysis was successful or verified.

## Automated validation

- Backend: **116 passed, 4 skipped, 5 warnings**. Four optional FastAPI tests
  were skipped because FastAPI readiness test dependencies were unavailable.
  The run used an in-memory SQLite fixture from an isolated working directory.
- Dashboard: `npm run build` passed, including TypeScript build and Vite
  production bundle.
- Extension: `node --check` passed for the service worker, content script, and
  popup; Manifest V3 JSON validation passed.
- Standalone dashboard: its inline JavaScript parsed successfully. This does
  not count as UI/runtime testing.
- `git diff --check`: passed.

Warnings include the deprecated `google.generativeai` SDK and Pydantic v2
class-based schema configuration; they were not broadened into this task.

## Git and remaining limitations

Commits created for this work:

- `3f6b6ba3aef87c8f7b8bb212b9a20b3f26d2e4dc` — remove deprecated TypeScript
  `baseUrl`; dashboard build passed afterwards.
- `6a5dfe93c7b68ab41fcf35ad86432d4b2db7926f` — serialize failed-scan history
  scores as `null`; includes a regression test.

The audited README was committed separately as
`de9000b8807fc41e461943e1881e395503d3f6cb` (`docs: make TRASCO MVP
friend-ready`). This report is committed separately; its containing commit is
identified in the final Git status/output and cannot embed its own hash.

Remaining limitations:

- Gemini model `gemini-3.8-flash` and SDK compatibility have not been confirmed
  by a successful upstream analysis.
- Browser E2E and real extension installation/interactions were not tested.
- The default dashboard port was unavailable in this environment; the Vite
  dev server was verified on `15173`, not through a browser.
- Four optional FastAPI tests remain skipped; the FastAPI runner is not
  runtime-verified and has a broad network/CORS configuration.
- Image-analysis functionality cannot classify an image without Gemini; it
  returns UNKNOWN and instructs the user to verify through official channels.
- The application is advisory and can produce false positives and false
  negatives.
- The backend dependency set emits SDK/Pydantic deprecation warnings.

# TRASCO — Trap & Scope

TRASCO is a cybersecurity MVP for identifying common online scams affecting Indonesian users. It combines deterministic URL and text heuristics with an optional Google Gemini integration, a local analytics dashboard, and a Chromium browser extension.

The project was developed for the MIT UNMUL 2026 Web Development — Cybersecurity Track. Detection results are advisory: users should independently verify financial transactions and account notices through official channels.

## Quick start

The backend and dashboard run as two local processes. Python 3.11 (the CI
version), Node.js 20, and npm are recommended. Gemini is **optional** for URL
and text scans, which retain deterministic heuristic analysis without a key.
Gemini is required to analyze valid images; without it, validation still runs,
then the API returns `ANALYSIS_UNAVAILABLE` with an `UNKNOWN` result.

### Windows PowerShell

Run from the repository root. These commands create a virtual environment,
install backend dependencies, and copy the sample environment file only if you
do not already have a local `.env`:

```powershell
py -3.11 -m venv apps\backend\.venv
.\apps\backend\.venv\Scripts\python.exe -m pip install -r apps\backend\requirements.txt
Set-Location apps\backend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Edit `apps/backend/.env`: set `SECRET_KEY` to a new value generated with
`python -c "import secrets; print(secrets.token_hex(32))"`. Keep the key local
and never commit `.env`. Set `GEMINI_API_KEY` only if you want to enable Gemini
analysis; it is not required for heuristic URL/text scans. The default local
database is `trasco_local.db`, not the protected `trasco.db`.

Initialize the local schema, then start the backend:

```powershell
.\.venv\Scripts\python.exe -m app.core.init_db --url sqlite:///./trasco_local.db --confirm-persistent
.\.venv\Scripts\python.exe -m app.flask_app
```

In a second PowerShell window, from the repository root, install and start the
dashboard:

```powershell
Set-Location apps\dashboard
npm ci
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173), select **Simulator**, and
run a text or URL scan. You can also send a first text scan from PowerShell:

```powershell
$body = @{ scanType = 'TEXT'; content = 'Saya mendapat tawaran kerja, tetapi diminta membayar biaya deposit terlebih dahulu.' } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/detect/analyze -Method Post -ContentType 'application/json' -Headers @{ 'X-Trasco-Source' = 'Dashboard-Client' } -Body $body
```

### macOS/Linux

Run from the repository root:

```bash
python3.11 -m venv apps/backend/.venv
source apps/backend/.venv/bin/activate
python -m pip install -r apps/backend/requirements.txt
cd apps/backend
if [ ! -f .env ]; then cp .env.example .env; fi
```

Edit `.env`: set `SECRET_KEY` to a fresh value from
`python -c "import secrets; print(secrets.token_hex(32))"`. Keep `.env` local.
`GEMINI_API_KEY` is optional for URL/text scans and required only to enable
Gemini analysis, including image analysis.

```bash
python -m app.core.init_db --url sqlite:///./trasco_local.db --confirm-persistent
python -m app.flask_app
```

In a second terminal from the repository root:

```bash
cd apps/dashboard
npm ci
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173), select **Simulator**, and
run a text or URL scan. For a command-line text scan:

```bash
curl -sS -X POST http://127.0.0.1:8000/api/v1/detect/analyze \
  -H 'Content-Type: application/json' \
  -H 'X-Trasco-Source: Dashboard-Client' \
  -d '{"scanType":"TEXT","content":"Saya mendapat tawaran kerja, tetapi diminta membayar biaya deposit terlebih dahulu."}'
```

The initializer creates missing tables but does not migrate an existing
database. Use only a new local database that contains no data you need to
preserve. Never point it at `apps/backend/trasco.db`.

## Features and current status

| Capability | Status |
|---|---|
| URL and text detection | Implemented in the Flask API with deterministic heuristics, including online-gambling promotions, obfuscated text, and URL shorteners; Gemini analysis is optional and has not been live-verified in this setup. |
| Image upload validation | Implemented in the extension popup and backend for JPEG, PNG, and WebP, with payload, dimensions, and pixel limits. |
| Image scam analysis | Gemini Vision analysis covers suspicious promotions, fake documents, social engineering, malicious-download lures, and fake transfer slips; it requires a configured key and an available upstream model. Without them, the API returns an unavailable/UNKNOWN result; a screenshot is not proof of payment. Live upstream operation has not been verified. |
| Scan persistence and analytics | Implemented with SQLAlchemy and SQLite. Failed image scans are stored with an UNKNOWN risk level and a sentinel score, not a numeric risk score. |
| React dashboard | Implemented with overview, recent history, and a URL/text simulator. |
| Continuous education | Limited to mitigation advice, scan recommendations, and simulator examples; this is not a separate learning or curriculum system. |
| Browser extension | Manifest V3 extension with URL checks, selected-text scans, an avatar, and popup image upload. Context-menu image scans are not supported by the backend image endpoint yet. |
| User accounts and preferences | Present in the alternative FastAPI runner; they are not exposed by the primary Flask runner or wired into the dashboard. |

## Architecture

```mermaid
flowchart LR
  Browser[Chromium extension] -->|HTTP JSON| Flask[Flask API :8000]
  Dashboard[React dashboard :5173] -->|HTTP JSON| Flask
  Flask --> Heuristics[URL and text heuristics]
  Flask --> Validator[Image validation]
  Flask --> Gemini[Optional Google Gemini API]
  Flask --> SQLite[(Local SQLite database)]
  Dashboard -. shared contracts .-> Types[@trasco/shared-types]
```

The primary runnable backend is Flask (`apps/backend/app/flask_app.py`). A FastAPI application is also present as an alternative runner. Both use the backend service modules; their routing and CORS behavior are not identical. The dashboard imports its TypeScript contracts from `@trasco/shared-types`.

## Technology stack

- Python backend: Flask, SQLAlchemy, Pydantic, Pillow; optional FastAPI/Uvicorn runner.
- AI integration: `google-generativeai` package, configured by `GEMINI_API_KEY` and `GEMINI_MODEL`.
- Dashboard: React 18, TypeScript, Vite.
- Extension: Chrome/Edge Manifest V3 JavaScript.
- Database: SQLite by default, accessed through SQLAlchemy.
- CI configuration uses Python 3.11 and Node.js 20. The backend dependency file uses version ranges rather than a fully pinned lockfile.

## Repository layout

```text
apps/
  backend/       Flask/FastAPI API, detection services, persistence, and tests
  dashboard/     React dashboard and standalone HTML dashboard
  extension/     Load-unpacked Chromium extension
packages/
  shared-types/  Canonical TypeScript contracts
docs/            Project notes and reports
```

## Prerequisites

- Python 3.11 (the version used by CI).
- Node.js 20 and npm for the dashboard.
- A Chromium browser to load the extension.
- Internet access is needed for the dashboard's CDN-loaded Tailwind CSS and web font. A Gemini key and upstream access are optional for URL/text scans and required to analyze valid images beyond local validation.

## Install and configure

From the repository root, create a virtual environment and install backend dependencies. The Quick Start above provides a complete first-run path.

**Windows PowerShell**

```powershell
py -3.11 -m venv apps\backend\.venv
.\apps\backend\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r apps\backend\requirements.txt
Set-Location apps\backend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

**macOS/Linux**

```bash
python3.11 -m venv apps/backend/.venv
source apps/backend/.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r apps/backend/requirements.txt
cd apps/backend
if [ ! -f .env ]; then cp .env.example .env; fi
```

Edit `apps/backend/.env` and set `SECRET_KEY` to a fresh value. Generate one with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Paste the generated value into the local `.env`; do not commit that file. `DEBUG=true` is for local development only. `GEMINI_API_KEY` is optional: without it, URL/text scans use heuristics and image analysis returns an unavailable/UNKNOWN result. The configured default model identifier is `gemini-2.5-flash`; its availability and compatibility have not been verified by a live request.

The example config uses `sqlite:///./trasco_local.db`, a separate local database filename. Initialize that database explicitly from `apps/backend`:

```bash
python -m app.core.init_db --url sqlite:///./trasco_local.db --confirm-persistent
```

The initializer refuses the protected `trasco.db` path and does not initialize a persistent database unless `--confirm-persistent` is supplied. Do not point it at a database containing user data.

## Run the application

Start the primary Flask API from `apps/backend`:

```bash
python -m app.flask_app
```

It binds to `127.0.0.1:8000`. Check liveness at `http://127.0.0.1:8000/health` and readiness at `http://127.0.0.1:8000/health/ready`. Readiness remains unavailable until the configured database schema passes the compatibility check.

In another terminal, install and start the dashboard:

```bash
cd apps/dashboard
npm ci
npm run dev
```

The Vite server binds to `127.0.0.1:5173`. Open the URL printed by Vite. The standalone HTML page is not the recommended launch path; use the Vite-hosted dashboard so its origin matches the backend's local allowlist.

### Browser extension

1. Start the backend first.
2. Open `chrome://extensions` or `edge://extensions`.
3. Enable **Developer mode**, choose **Load unpacked**, and select `apps/extension`.
4. Open the extension popup to scan text or upload a JPEG, PNG, or WebP image. The extension sends requests only to its configured local backend URL (default `http://localhost:8000`).

The extension requests `storage`, `activeTab`, and `contextMenus` permissions and injects its content script on `<all_urls>` to support page checks. Review browser permission prompts and use the extension only on pages where its behavior is appropriate. The extension has no build step. Its npm `test` script is only a placeholder; use the syntax checks below instead.

## How to use

- **URL/text:** In the dashboard's simulator, choose text or URL, enter content, and run a scan. The extension can scan selected text or check a visited URL. Results include a risk level, score, indicators, and recommendations.
- **Image:** Use the extension popup's image picker. The API validates the encoded payload, MIME type/signature, decoded size, dimensions, and pixel count before requesting Gemini Vision.
- **Interpretation:** `COMPLETED` indicates analysis returned a result. `UNKNOWN` with a null score means analysis was not completed; it must not be interpreted as safe. Confirm transfers in the bank's official app.
- **Analytics/history:** The dashboard shows persisted scan totals, risk/category distribution, recent history, and a seven-day trend. Empty state values are real zeros, not demo data.
- **Education:** Read the mitigation advice and recommendations shown with the scan and dashboard. These are brief guidance, not personalized professional advice.

## API reference — primary Flask runner

Requests from browser pages must use an allowed local origin and the `X-Trasco-Source` client identifier (`Dashboard-Client` or `Extension-Local`). Command-line requests without an `Origin` header do not need that browser handshake.

| Method and route | Purpose and request | Response/important errors |
|---|---|---|
| `GET /health` | Liveness probe; no body required. | `200` with service status. |
| `GET /health/ready` | Readiness probe; no body required. | `200` when the schema is compatible; `503` while unready. |
| `POST /api/v1/detect/analyze` | JSON: `{"scanType":"TEXT","content":"..."}` or `{"scanType":"URL","content":"..."}`; optional object `metadata`. | Analysis result with `success`, `status`, `scanId`, `riskLevel`, nullable `riskScore`, `threatCategory`, indicators, recommendations, and avatar guidance. Invalid JSON/content/type returns `400`. |
| `POST /api/v1/detect/analyze-image` | JSON with `content` (Base64 data URL), optional `mimeType` (`image/jpeg`, `image/png`, or `image/webp`; inferred from the data URL when omitted), optional `fileName` and object `metadata`. | Result uses `COMPLETED` or an incomplete status such as `INVALID_REQUEST`, `INVALID_IMAGE`, `ANALYSIS_UNAVAILABLE`, or `ANALYSIS_FAILED`. Failures have `riskLevel: "UNKNOWN"` and `riskScore: null`; payloads may return `400`, `413`, `415`, `422`, `500`, `502`, `503`, or `504`. |
| `GET /api/v1/analytics/overview` | Returns aggregate risk/category counts, recent history, and seven-day trends. | Stored records are aggregated without the recent-history limit. |
| `GET /api/v1/analytics/history` | No body required. | Up to 30 most recent persisted records. Incomplete risk scores are `null`. |

The image upload limit is 5 MiB decoded, with a 7 MiB Base64 string limit and a 10 MiB HTTP request-body limit. The dashboard simulator currently supports only URL and text scans.

### Environment variables

The primary Flask runner reads `SECRET_KEY`, `DEBUG`, `DATABASE_URL`,
`GEMINI_API_KEY`, `GEMINI_MODEL`, and `GEMINI_IMAGE_TIMEOUT_SECONDS` (default
15 seconds). `SECRET_KEY` is required and must be at least 32 characters;
production mode rejects the bundled insecure default.
`DEBUG=true` is for local development only. `DATABASE_URL` in the sample points
to `trasco_local.db`. Gemini settings enable upstream analysis but do not
guarantee that the configured model is available.

The sample also includes `PROJECT_NAME`, `API_V1_STR`,
`ACCESS_TOKEN_EXPIRE_MINUTES`, and `ALGORITHM` for the alternative FastAPI
application and authentication code. `CORS_ORIGINS` is present in the sample
but is not used by the primary Flask runner, whose browser allowlist is
hard-coded to local development origins and extension origins. Do not rely on
that variable to change or secure CORS behavior.

### Alternative FastAPI runner

`apps/backend/app/main.py` provides the `/api/v1` detection, analytics,
authentication, and preferences routers, plus `/health`, `/health/ready`,
`/docs`, and `/redoc`. Its startup fails if security configuration or schema
checks fail. Unlike Flask, its current runner binds to all interfaces and
configures wildcard CORS, so do not expose it to an untrusted network. It is
not part of the verified primary workflow; use Flask for local development.

## Testing and verification

Run from the repository root with dependencies installed. Tests use an
in-memory SQLite fixture. Run them from a new temporary working directory so
Pydantic settings cannot load `apps/backend/.env`; this avoids both the local
database and any locally configured Gemini key.

```powershell
$backend = (Resolve-Path apps\backend).Path
$python = Join-Path $backend '.venv\Scripts\python.exe'
$testCwd = Join-Path $env:TEMP ('trasco-tests-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $testCwd | Out-Null
$env:PYTHONPATH = $backend
$env:PYTHON_DOTENV_DISABLED = '1'
$env:SECRET_KEY = 'test-only-secret-key-0123456789abcdef0123456789abcdef'
$env:DEBUG = 'true'
$env:DATABASE_URL = 'sqlite:///:memory:'
$env:GEMINI_API_KEY = ''
Push-Location $testCwd
& $python -m pytest -p no:cacheprovider -v (Join-Path $backend 'tests')
$testExitCode = $LASTEXITCODE
Pop-Location
Remove-Item -LiteralPath $testCwd
if ($testExitCode -ne 0) { exit $testExitCode }
```

On macOS/Linux:

```bash
backend="$PWD/apps/backend"
python="$backend/.venv/bin/python"
test_cwd="$(mktemp -d)"
(
  cd "$test_cwd"
  PYTHONPATH="$backend" PYTHON_DOTENV_DISABLED=1 \
    SECRET_KEY=test-only-secret-key-0123456789abcdef0123456789abcdef \
    DEBUG=true DATABASE_URL=sqlite:///:memory: GEMINI_API_KEY='' \
    "$python" -m pytest -p no:cacheprovider -v "$backend/tests"
)
test_status=$?
rmdir "$test_cwd"
exit "$test_status"
```

The test fixtures use in-memory SQLite databases; tests that need persistent scratch data use temporary directories. Do not set test configuration to the user's `trasco.db`.

From `apps/dashboard`:

```bash
npm ci
npm run build
```

From the repository root, check extension JavaScript syntax:

```bash
node --check apps/extension/src/background/service-worker.js
node --check apps/extension/src/content/content-script.js
node --check apps/extension/src/popup/popup.js
```

## Troubleshooting

- **Backend refuses to start:** Confirm that `.env` exists under `apps/backend`, `SECRET_KEY` is non-empty and at least 32 characters, and `DEBUG=true` is used only for local development.
- **Readiness is `503`:** The database has not been initialized or its schema does not match the ORM models. Check `DATABASE_URL` and initialize the designated local database with the command above. The backend does not migrate an existing schema.
- **Port 8000 is in use:** Stop the conflicting local service before starting TRASCO. The Flask development runner binds to `127.0.0.1:8000`; changing the port requires updating the backend, dashboard, extension host permissions, and extension backend URL consistently.
- **Dashboard cannot connect:** Keep the Flask server running on port 8000 and use the Vite origin `http://127.0.0.1:5173` or `http://localhost:5173`. If port 5173 is occupied, Vite may select another port that the backend does not allow; stop the conflicting service or deliberately update the backend allowlist and dashboard origin together. Use the Vite URL, not `file://`.
- **Gemini unavailable or rate-limited:** Check the key and configured model locally without sharing them. Text/URL scans continue with heuristics. Image scans report an unavailable/failed result; verify payment manually and do not treat it as safe.
- **Image is rejected:** Use JPEG, PNG, or WebP within the documented size/dimension limits. A file extension alone does not determine the validated image type.
- **Dependency or build errors:** Use Python 3.11 and Node.js 20 as in CI, then reinstall from `requirements.txt` or `package-lock.json`.

## Security and privacy

- Keep `.env`, API keys, and local databases out of Git. `.gitignore` excludes environment files, common local databases, caches, and `.phase7_backups/`.
- The Flask server binds to loopback by default. The dashboard dev server also binds to loopback. Do not expose these development services to an untrusted network.
- Scan text is sent to Google Gemini when a key is configured and active Gemini analysis is selected. Review Google's terms and privacy practices before sending sensitive content. Image contents are also sent for Vision analysis when configured.
- The backend stores a scrubbed text snippet or a fixed image label, a content hash, risk data, and scan metadata. This is not a guarantee of regulatory compliance or zero data retention.
- The extension does not store a Gemini key. The closed Shadow DOM isolates the avatar UI from page styles; this does not make the extension or backend a security boundary.
- Heuristics can produce false positives and false negatives. A completed result is not proof that a website or payment is safe.

## Current limitations

- The configured Gemini model name and SDK call path have not been confirmed as working. An early smoke attempt returned an upstream timeout; a later isolated test with Gemini explicitly disabled confirmed the expected unavailable response. No successful Gemini analysis has been verified.
- The alternative FastAPI runner and authentication/preferences flow are not part of the verified primary workflow. The standalone dashboard's inline JavaScript syntax has been checked, but it has not been runtime-verified.
- Right-click context-menu image scanning passes an image URL, while the backend currently expects an uploaded Base64 data URL. Use popup image upload instead.
- The education content is limited to inline advice and examples. The dashboard has no separate lesson-management system.
- No root `LICENSE` file was present when this README was prepared. Package metadata declares MIT for individual packages; that is not a substitute for a verified repository-level license.

## Development

- Backend: use the isolated temporary-working-directory test command above.
- Dashboard: `cd apps/dashboard; npm run build`
- Extension syntax: run the three `node --check` commands above.
- Keep shared TypeScript contracts in `packages/shared-types/src/`; dashboard imports them through the Vite alias.
- CI workflow: `.github/workflows/ci.yml`.

## Acknowledgements

TRASCO was developed for the MIT UNMUL 2026 Hackathon, Web Development — Cybersecurity Track. No additional acknowledgements or repository-level license were verified.

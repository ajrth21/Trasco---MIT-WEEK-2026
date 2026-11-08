# TRASCO Development Guide & Contribution Standards

> **Platform:** TRASCO (Trap & Scope) Monorepo  
> **Target Audience:** Engineering Contributors & DevOps Maintainers  
> **Status:** Active Standard  

---

## 1. Prerequisites & Tooling Requirements

Before contributing to TRASCO, ensure your workstation meets the following runtime specifications:

| Component | Minimum Version | Verified Tested Version | Notes |
|---|---|---|---|
| **Python** | 3.10+ | 3.13.7 | Required for Threat Intelligence Backend Engine. |
| **Node.js** | 18.0+ | 26.10.0 | Required for Web Dashboard build tooling. |
| **npm** | 10.0+ | 11.19.1 | Node package manager. |
| **Browser** | Chromium 109+ | Chrome 120+, Edge 120+ | Required for Manifest V3 extension loading and Web Speech API. |
| **Git** | 2.40+ | 2.48.1 | Distributed version control. |

---

## 2. Workspace Setup

### A. Clone & Branch Initialization
```bash
git clone https://github.com/ajrth21/Trasco---MIT-WEEK-2026.git
cd Trasco---MIT-WEEK-2026

# Active development occurs on the feature/development branch
git checkout feature/development
```

---

## 3. Component Workflows

### A. Threat Intelligence Backend (`apps/backend`)

1. **Install Python Dependencies:**
   ```bash
   cd apps/backend
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables (Optional):**
   Copy the template environment file:
   ```bash
   cp .env.example .env
   ```
   *Note: If `GEMINI_API_KEY` is left blank, the backend operates in 100% deterministic offline heuristic mode.*

3. **Start the Backend Server (Primary Runner):**
   ```bash
   # From apps/backend/ directory:
   python -m app.flask_app
   ```
   - Server binds to: `http://127.0.0.1:8000`
   - Health check endpoint: `http://127.0.0.1:8000/health`
   - SQLite database `trasco.db` initializes automatically with WAL mode on startup.

4. **Run Backend Unit Tests:**
   ```bash
   cd apps/backend
   python -c "from tests.test_heuristics import *; test_url_heuristic_phishing(); test_url_heuristic_official_domain(); test_text_heuristic_otp_and_deposit(); test_text_heuristic_safe(); print('test_heuristics: PASSED'); from tests.test_security_scrubber import *; test_pii_scrubber_otp(); test_pii_scrubber_phone_number(); test_pii_scrubber_email(); test_pii_scrubber_bank_account(); test_anti_prompt_injection_gatekeeper(); print('test_security_scrubber: PASSED')"
   ```

---

### B. Web Dashboard (`apps/dashboard`)

1. **Install Dependencies:**
   ```bash
   cd apps/dashboard
   npm install
   ```

2. **Start Vite Development Server (with HMR):**
   ```bash
   npm run dev
   ```
   - Local Dashboard URL: `http://localhost:5173`
   - Network Dashboard URL: `http://<your-ip>:5173`

3. **Validate Production Build & Type Checking:**
   ```bash
   npm run build
   ```
   - Runs `tsc -b && vite build`.
   - Output bundle generated in `apps/dashboard/dist/`.

4. **Zero-Dependency Fallback Mode (Offline Presentation):**
   If Node.js or `npm install` is unavailable, open `apps/dashboard/standalone_dashboard.html` directly in any web browser. It runs a full SPA powered by React and Tailwind CDN without build steps.

---

### C. Browser Extension (`apps/extension`)

1. **Load Unpacked Extension in Chrome or Edge:**
   - Open `chrome://extensions` or `edge://extensions`.
   - Toggle **Developer mode** in the top right corner.
   - Click **Load unpacked** and select the directory:  
     `<repository-path>/apps/extension`
   - Verify the TRASCO shield icon (🛡️) appears in the toolbar.

2. **Validate Extension Script Syntax:**
   ```bash
   node --check apps/extension/src/background/service-worker.js
   node --check apps/extension/src/content/content-script.js
   node --check apps/extension/src/popup/popup.js
   ```

3. **Test with the Interactive Playground:**
   - Open `apps/extension/demo_testpage.html` in your browser.
   - Select text from sample Indonesian scam bubbles (e.g., job offer, OTP request) -> Right-click -> Select **"🛡️ Periksa dengan TRASCO"**.
   - Observe Avatar mood transition (`CRITICAL_SHIELD`) and Indonesian audio guidance.

---

## 4. 1-Click Automation Scripts

For rapid development and demo startup, TRASCO provides root launcher scripts:
- **`run_all.bat`**: Launches the Flask backend in a separate terminal and opens `standalone_dashboard.html`.
- **`run_all.ps1`**: PowerShell equivalent with terminal status messages.
- **`run_backend.bat`**: Launches the Flask backend exclusively on port 8000.
- **`run_dashboard.bat`**: Launches the standalone dashboard in your default browser.

---

## 5. Git & Commit Guidelines

1. **Branching Strategy:**
   - `main`: Production-stable hackathon submission branch.
   - `feature/development`: Active development branch.
2. **Conventional Commits Standard:**
   - `feat:` New features or capabilities.
   - `fix:` Bug fixes or security mitigations.
   - `chore:` Maintenance, scaffolding, documentation, or dependency updates.
   - `test:` Unit or integration test suites.
3. **Commit Rule:**
   - Never commit `.env`, credentials, `node_modules`, or database binary files (`trasco.db`, `*.db-wal`, `*.db-shm`).


# TRASCO AI Agent Interaction & Collaboration Guide (AGENTS.md)

> **Platform:** TRASCO (Trap & Scope) — AI-Powered Cybersecurity Platform  
> **Target Audience:** Autonomous Coding Agents, Pair-Programming AI Assistants, and Human Architects  
> **Status:** Active Reference Standard  

---

## 1. Project Overview & Mission

TRASCO is an AI-powered cybersecurity solution developed for the **MIT UNMUL 2026 Hackathon (Web Development — Cybersecurity Track)**. It protects Indonesian youth and active digital citizens from prevalent online financial scams (fake jobs, OTP theft, phishing/typosquatting, deposit scams, fake payment slips).

### Repository Architecture (Monorepo)
```text
Trasco---MIT-WEEK-2026/
├── apps/
│   ├── backend/             # Python 3.11+ Threat Intelligence Engine (Flask primary runner)
│   ├── dashboard/           # React 18 + Vite + TypeScript Web Dashboard
│   └── extension/           # Chrome / Edge Extension (Manifest V3 + Closed Shadow DOM)
├── packages/
│   └── shared-types/        # Canonical TypeScript definitions (@trasco/shared-types)
├── docs/                    # Architecture, Security, API, Database, Testing, CI/CD specs
└── .github/workflows/       # Automated Quality Gate (ci.yml)
```

---

## 2. Core Guardrails & Behavioral Rules for AI Agents

When modifying this repository, every AI agent **MUST** obey these principles:

1. **Security by Design:**
   - **Never introduce dynamic `innerHTML`** into [`apps/extension/src/content/content-script.js`](apps/extension/src/content/content-script.js). All dynamic content must use DOM APIs (`textContent`, `createElement`, `createTextNode`).
   - Avatar elements must stay encapsulated inside the **Closed Shadow DOM** host `#trasco-cyber-guardian-host`.
   - Never disable the **Universal Heuristic Risk Floor** in [`apps/backend/app/services/risk_scorer.py`](apps/backend/app/services/risk_scorer.py). Deterministic heuristics always serve as the immutable trust anchor against prompt injection.
   - Respect UU PDP No. 27 Tahun 2022: Always sanitize NIK, phone numbers, emails, bank accounts, and OTPs through [`scrub_pii()`](apps/backend/app/core/scrubber.py) before logging or persisting.

2. **Single Source of Truth:**
   - Canonical types reside in [`packages/shared-types/src/`](packages/shared-types/src/).
   - Dashboard imports from `@trasco/shared-types`. Never duplicate or drift contract types.

3. **Evidence-Based Reporting:**
   - Never report a test as "Passed" without running it and verifying exit code 0.
   - All tests must pass before declaring a task complete:
     ```bash
     cd apps/backend && pytest -v
     cd apps/dashboard && npm run build
     ```

4. **Vertical Slice Development:**
   - Do not implement multiple features across different domains at once. Build one end-to-end slice (Extension -> Backend -> Dashboard -> Storage) completely and verify before proceeding.

5. **Zero Unapproved Commits / Pushes:**
   - Never push to remote Git without explicit human user approval.
   - Commit only staged, relevant changes with clean conventional commit messages.

---

## 3. Key Development Commands

| Component | Task | Command |
|---|---|---|
| **Backend** | Start dev server | `cd apps/backend && python -m app.flask_app` (binds to `127.0.0.1:8000`) |
| **Backend** | Run test suite | `cd apps/backend && pytest -v` (34 test cases) |
| **Dashboard** | Start dev server | `cd apps/dashboard && npm run dev` (binds to `localhost:5173`) |
| **Dashboard** | Build bundle | `cd apps/dashboard && npm run build` (`tsc -b && vite build`) |
| **Extension** | Syntax check | `node --check apps/extension/src/background/service-worker.js` |
| **Extension** | Load extension | In Chrome/Edge: open `chrome://extensions`, enable Dev Mode, load `apps/extension` |

---

## 4. Current Milestone & Status

- **Scaffolding & Architecture:** Complete and audited.
- **Sprint 2 (Extension Core):** Complete (commit `28b1e36`).
- **Security Hardening (SEC-01, SEC-02, SEC-03):** Complete (commit `32d8596`).
- **CI/CD Quality Gate (ISSUE-CI-01):** Complete (commit `a5e81b6`).
- **Upcoming Milestone:** **Sprint 3 — AI Scam Detection Engine** (expanding patterns in `heuristic_engine.py` for Pinjol Ilegal, Investasi Bodong, and Homoglyphs).


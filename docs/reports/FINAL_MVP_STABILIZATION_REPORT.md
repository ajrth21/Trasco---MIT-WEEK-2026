# TRASCO Final MVP Stabilization Report

## Scope and Git state

This report records the final MVP stabilization work on
`feature/final-mvp-stabilization`. The branch was created at
`0a04904c7f2a192414c380e0072ddd8874d0c5f0`, preserving the six existing commits
ahead of `origin/main`. The stabilization changes and this report are intended
to be included in a local commit on this branch. No push, merge, tag, or history
rewrite was performed.

The working tree initially contained pre-existing user changes. Those changes
were preserved and integrated; no attempt was made to reconstruct or revert
them. The protected `apps/backend/trasco.db` was not opened, queried, migrated,
or modified. The actual `apps/backend/.env` was not read. No credentials were
included in the changes.

## Implemented

- Analytics totals, risk counts, and category distributions now aggregate the
  full persisted dataset. Recent history and the seven-day trend remain
  separately bounded.
- The FastAPI analytics endpoint uses the shared analytics service instead of
  its duplicate mock-based implementation.
- Image-analysis failures with a scan identifier are persisted using safe
  non-null sentinel values, while API responses retain their failure status
  and nullable public risk score.
- Flask bootstrap exceptions leave application readiness false.
- Image payload and MIME type validation rejects non-string inputs with a
  structured client error.
- Gemini errors are logged without logging response or exception details, and
  the image call has a bounded timeout. API-key availability and upstream model
  compatibility were not tested.
- Dashboard weekly bars have a fixed-height track; incomplete/UNKNOWN results
  preserve nullable risk scores; simulator results no longer use a fabricated
  fixed-delay fallback.
- API-provided values in the standalone dashboard are inserted as text/DOM
  content, and the extension avatar uses a closed Shadow DOM.
- The local environment example, ignore rules, and root README were updated.
- Regression coverage was added for analytics beyond 50 records, failed image
  persistence, malformed image field types, and bootstrap exceptions.

## Verification

| Area | Result |
|---|---|
| Backend test suite | `python -m pytest -v`: **115 passed, 4 skipped, 5 warnings** |
| Database isolation during tests | Tests ran from `apps/backend` with dotenv loading disabled and `DATABASE_URL=sqlite:///:memory:` |
| Dashboard | `npm run build`: passed (`tsc -b` and Vite production build) |
| Extension JavaScript | `node --check` passed for service worker, content script, and popup |
| Standalone dashboard JavaScript | Inline script parsed successfully with Node |
| Diff whitespace | `git diff --check`: passed |

The four skipped tests cover the optional FastAPI readiness paths because
FastAPI is not installed in the current environment. The five test warnings
include Pydantic v2 deprecation notices for class-based schema configuration.
Git also reports expected LF-to-CRLF working-copy notices for text files; these
are not `git diff --check` failures.

## Verification level and limitations

- **Unit/regression tested:** backend detection, validation, analytics, and
  persistence behavior covered by the passing pytest suite.
- **Integration tested:** test-client and persistence tests use in-memory
  SQLite; this does not verify the protected database or a persistent local DB.
- **Build/syntax verified:** dashboard production build, extension JavaScript
  syntax, and standalone dashboard inline JavaScript.
- **Live application runtime:** no backend/dashboard browser session or
  end-to-end browser workflow was launched for this stabilization.
- **Gemini:** the configured identifier is `gemini-3.8-flash`, but upstream
  availability and compatibility with the installed SDK remain unverified.
  No live Gemini request was made, and no API key was inspected.
- **Alternative FastAPI runner:** not runtime-verified; its optional readiness
  tests were skipped.

## Remaining risks

- Confirm the Gemini model identifier and SDK compatibility in an authorized
  environment with a properly managed key before relying on live AI analysis.
- Run the alternative FastAPI runner's readiness tests in an environment where
  its optional dependencies are installed.
- The app remains advisory and heuristic-based; a completed scan is not proof
  that a site, message, or payment is safe.
- Existing Pydantic v2 deprecation warnings should be addressed separately.
- No repository-level `LICENSE` file was present during this work; package
  metadata is not evidence of a repository-wide license.

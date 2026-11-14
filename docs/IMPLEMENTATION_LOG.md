# Implementation log

## 2026-11-14 — Integrate and review existing P0 work

The owner requested development directly on `main`, no new branches or PRs,
with verified checkpoints approximately every 10 minutes during active work.

Integrated the existing provider-contract and official OAuth work from the two
previously open branches, preserving their history. Reviewed the code and fixed
OAuth response handling: enforce a 64 KiB limit during streaming, reject
compressed bodies, enforce a total deadline, validate nonempty tokens, reject
boolean expiration values, and keep upstream errors sanitized.

Validation: `PYTHONPATH=services/api .venv/bin/python -m pytest -q services/api/tests`
— **82 passed**. These tests use offline fixtures/MockTransport only. No credentials,
TeraBox account, real file metadata or completed live download was used.

Next: bound and rate-limit API requests, redact framework validation errors and
unexpected provider failures, then prepare a reproducible operator validation path.

External blocker: approved partner credentials, confirmed scopes/regional hosts,
and operator-owned test shares are still required. The default provider remains
disabled. G1 is not complete; unrelated premium/billing work remains deferred.

## 2026-11-14 — API admission and browser privacy

Added per-process fixed-window rate limits with bounded client storage, a strict
4 KiB body cap (including chunked requests), body/provider deadlines, concurrency
admission, no-store responses, exact-origin CORS and sanitized JSON validation
and provider errors. Health probes remain available during API throttling.
Limits are configurable through `.env.example`. Use shared edge limits for
multiple workers/replicas; configure trusted proxy peers explicitly.

The extension now rejects credentials, custom ports, duplicate share tokens and
path-normalization tricks. It strips tracking/password fields and passes the
normalized link in a fragment, which the website consumes and clears. The
website aborts stale requests when inputs change, handles deadlines, and sends
no-referrer headers. No new extension permissions were added.

Validation: **100 Python tests**, **16 extension tests**, Next.js production
build and TypeScript check passed. npm audit reported **0 vulnerabilities** for
the resolved dependency tree. Python and Node dependencies are pinned/locked.
Playwright covers the current validation/provider-unavailable flow against the
real local FastAPI server at desktop and mobile viewports; its delayed-response
case is an explicit browser mock. This does not test live TeraBox service access.

Commands: `PYTHONPATH=services/api .venv/bin/python -m pytest -q services/api/tests`,
`node --test apps/extension/tests/*.test.mjs`, `npm run build`,
`npm run typecheck`, `npm audit --audit-level=high`, `npm run test:e2e` (web directory).

Local browser execution limitation: Chromium could not launch because the managed
workspace denied its process-singleton socket (`Operation not permitted`). No
browser scenario passed locally; GitHub Actions is the next verification source.
The first harness attempt also caught and fixed the Uvicorn app import string.

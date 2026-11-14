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

## 2026-11-14 — Operator-only metadata/download validation path

Added `official_shares.py`, `egress.py` and `python -m app.preflight` with a
no-network default and explicit `--live` opt-in. The candidate uses documented
share metadata/download endpoints, selects only a resolved file, validates
response shape and approved hosts, then hashes a bounded fixture transfer.
DNS answers must all be public; connections target a checked IP while retaining
the original TLS hostname. Separate clients isolate API cookies from the CDN.
No new dependencies or third-party repository source were incorporated.

Evidence: **153 Python tests pass** (all offline). The current environment's
no-network preflight reports missing partner credentials/token, approved hosts,
fixture URL/ID/hash and approval confirmation. No live test was attempted.
`uvx pip-audit -r services/api/requirements.lock --no-deps --disable-pip`
reported **no known vulnerabilities**; npm audit had also reported zero.

GitHub run [43586294273](https://github.com/kawakaze430/create-terabox-downloader/actions/runs/43586294273)
passed API, extension, web build and type checks. Browser execution found test
selectors matching Next.js's route announcer in addition to our alert; selectors
are now scoped to the app's main landmark, with a fresh CI run required.

See [operator validation](OPERATOR_VALIDATION.md) for precise prerequisites,
commands, return codes, protocol ambiguities and public-authentication work.
A fixture probe is not a production downloader; public routes remain disabled.

## 2026-11-14 — Verified checkpoint and handoff

[Commit 5ed2df6](https://github.com/kawakaze430/create-terabox-downloader/commit/5ed2df64a15701342232030ccfb78b30d6aa00bb)
passed all three jobs in [CI run 43586842144](https://github.com/kawakaze430/create-terabox-downloader/actions/runs/43586842144).
Results: **153 backend tests, 16 extension parser tests, 10 browser tests**, plus
production build, TypeScript and Python dependency consistency checks. Both
desktop and mobile scenarios exercised validation, unavailable-provider messages,
fragment handoff, input changes during requests and service outages. These are
Chromium viewport tests, not installed Chrome/Edge extension or real TeraBox tests.

Three implementation checkpoints were pushed directly to `main`; no new branch
or PR was created. This final documentation checkpoint records the passing result
and extends ignored environment filenames to reduce accidental secret commits.

Remaining blocker is concrete: no partner credentials, consented access token,
confirmed API/CDN hosts, operator-owned share/file ID or expected checksum are
configured. The offline preflight lists these requirements without network calls.
The next engineering gate is a partner-authorized live probe, resolving documented
protocol ambiguities, followed by per-user authorization/session isolation before
exposing metadata/downloads to website users. G1 is still blocked; folders, player,
ZIP, accounts, billing and production launch must not be marked complete.

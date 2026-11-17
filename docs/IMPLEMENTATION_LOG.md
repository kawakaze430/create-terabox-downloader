# Implementation log

## 2026-11-17 — Reorganized repository validation

After the structure and recovery documentation commits, tested `main` at
`08cffee`. Local checks passed 173 offline API tests, 16 extension parser
tests, 10 Playwright Chromium tests across desktop and mobile, the Next.js
production build and TypeScript check, Python dependency consistency, the
DOCX/archive checks, and npm/Python dependency audits (no known findings).
Seven current entrypoint/relocated Markdown files had no missing local links.
The API tests emitted one Starlette/httpx deprecation warning.

The offline operator preflight exited 2 as designed and reported
`configuration_ready: false`, `live_verified: false`, and
`public_provider_enabled: false`. No provider credentials were configured,
no `--live` probe ran, and no TeraBox metadata or file transfer was verified.
See [the detailed validation report](../AnalyseFuture/TEST_AND_VALIDATION_REPORT.txt).

Corrected the local-development instructions to use the existing Python lock
and fixed an npm installation typo. No application source, dependency lock,
public API or provider enablement was changed.

## 2026-11-16 — G1 OAuth outbound credential gate and reference audit

Inspected main at `6a088e3795eb8c52cff46180ae1776d3487582ca`,
open issue #2, open PRs (none), three GitHub Actions jobs,
the operator-only client, egress, API limits, web and extension source, and both
primary public references. The latest baseline CI was green; live provider
integration was and remains unconfigured.

Pushed [commit 8203a017](https://github.com/kawakaze430/create-terabox-downloader/commit/8203a017032516e9ae30a9790fc141752604880a)
directly to `main`: require printable ASCII and bounded tokens on OAuth
refresh/token-info **before** building outbound HTTP requests; also reject
non-ASCII authorization codes, provider-returned tokens and operator-probe
tokens. Four code/test files changed. Regression tests prove malformed tokens
do not cause HTTP calls and that invalid offline operator configuration cannot
run `--live`. No provider credentials or external service was used.

[GitHub Actions run 43750414786](https://github.com/kawakaze430/create-terabox-downloader/actions/runs/43750414786)
passed at `8203a017`: **173 offline Python tests**, **16 extension
tests**, successful Next.js production build/typecheck, **10 Playwright
Chromium desktop/mobile tests**, and the no-network preflight. These are
CI tests with fixture/mocked provider behavior, not authorized live file
metadata, a completed download or installed-extension verification.

Source-checked exactly two reference repositories, TeraPlayer at
`2e60ba4b4963a4112aab57eb2d4770175c5f9965` and TeraBox Gateway at
`063f61fc61bb173fb936fc487f4a18e40436caab`; their inspected LICENSE
files are MIT. Both contain worker/third-party extraction or cookie paths
that are unsuitable as unapproved production providers. See
[research audit and strict priorities](RESEARCH_AND_LICENSES.md).
No third-party code was imported.

**Next:** secure written TeraBox partner approval for external-share metadata
and file-transfer scopes, approved hosts and a non-sensitive owner-controlled
fixture with trusted SHA-256. Run the explicit live probe only after that.
Until then G1 remains blocked, and public routes stay disabled.


## 2026-11-15 — Operator token validation before any partner network call

Reviewed main at `a93fa7a`, issue #2, current CI, provider boundary, official
OAuth, pinned egress, URL admission, mock tests and public provider gating.
Found that malformed operator-supplied access tokens could pass the *offline*
configuration check and reach the OAuth token-info request before the later
`OfficialShares` validation. Shared the existing token policy through
`validated_operator_token()` and apply it during offline configuration,
before network-client construction in `probe()`, and in `OfficialShares`.
Five regression cases cover embedded spaces, newline, tab, DEL and tokens
exceeding 8192 characters. The invalid-token `--live` path now exits at the
configuration gate without network calls; no credentials were added.

Added an explicit `python -m app.preflight` **offline** step to GitHub Actions
(no `--live`). It exited with unconfigured status, reporting
`configuration_ready: false`, `live_verified: false` and
`public_provider_enabled: false`. The step checks these safety invariants
without exposing variable contents.

Verification: [Platform CI run 43650510463](https://github.com/kawakaze430/create-terabox-downloader/actions/runs/43650510463)
passed all jobs: **158 backend tests** (fixtures/MockTransport only),
**16 extension unit tests**, Next.js production build, TypeScript check,
**10 Playwright desktop/mobile tests** against the local API, Python
dependency check and offline preflight. An earlier intermediate run caught
a newly introduced Python syntax error; it was fixed before the passing run.
Playwright exercises URL validation, disabled-provider responses and browser
behavior, not a real TeraBox account or completed download.

**G1 remains blocked:** TeraBox partner approval and exact permitted public-share
scopes, operator-consented access token, partner-approved regional/CDN hosts,
operator-owned small fixture with file ID and trusted SHA-256, followed by
authorized live verification. Do not use `--live` until these are confirmed.
Public `UnconfiguredProvider` remains enabled as the safe default; no
operator credential is exposed to public routes. Next engineering task:
after operator authorization, validate one approved fixture's real metadata
and full checksum-matching download, record sanitized evidence, then design
per-user authorization before enabling visitor downloads.


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

## 2026-11-17 — Root-level task and review handoff

At the owner's request, added [PROJECT_STATUS_AND_TASKS.md](../PROJECT_STATUS_AND_TASKS.md)
as the operational entrypoint for another implementation tool. It maps every
tracked file/folder, separates implemented local behavior from mock-only provider
candidates and absent features, and defines 25 ordered tasks with dependencies,
acceptance criteria, an implementer prompt and PR review procedure. README and
the documentation index/checklist link to it. AGENTS.md now records the owner's
new request that follow-up implementation tools submit PRs for review instead
of following the historical direct-to-main implementation instructions.

Source reviewed: `de7e4b34f4a935bcfe96f47594d0c2b31abc60df` in the current
`sarfiaroui-oss/create-terabox-downloader` checkout. Read-only Git access confirmed
the remote main tip at that SHA. GitHub PR and Actions API reads returned
`Forbidden`; current-fork PR/CI state and future continuous monitoring are not
claimed. No live TeraBox operation was attempted and no application code changed.

Validation for this documentation change: all 81 pre-existing tracked file paths
plus the new guide are covered; relative Markdown file links resolve; all task
IDs T01–T25 have detailed sections; `git diff --check` passes. API and client
source reviews checked the implementation claims. Application test counts in the
guide refer explicitly to the preceding local onboarding validation at the same
application revision, not a new test run for this documentation-only change.

## 2026-11-17 — Independent-engine priorities and extension checkpoint

The latest owner engine prompt supersedes PR-only/provider-first execution.
Checkpoint `a03a4c3` persisted the complete 82-file/18-directory organization
audit, independent-engine design and continuation record. Fresh baseline:
173 API tests passed; pip check passed, with the existing testclient deprecation.
No source moves/deletions, dependency changes or provider enablement occurred.

E04 adds validated build-time extension website origins, safe popup tab/error
states and a deterministic minimal ZIP builder. Source config is unchanged by
packaging; MV3 activeTab-only permissions and fragment privacy are retained.
The website View source href now names the current repository. Validation:
50 extension tests, popup syntax and package command passed. Installed Chrome/
Edge/store verification remains unrun. See EXTENSION_DEVELOPMENT.md and
CODEX_CONTINUITY.md. Generic engine work is being tested separately.

## 2026-11-17 — Source-independent streaming and Range recovery

E02/E03 add `app/download_engine.py` and the operator `app/download_cli.py`.
Production uses existing approved HTTPS host/DNS-pinned TLS transport, without
OAuth dependency or a public arbitrary-URL endpoint. Transfers stream bounded
chunks to private temporary files, retry transient GET failures within attempts/
deadlines, respect Retry-After, verify expected size/SHA-256 and publish atomically
without clobbering existing files. Cancellation/failure cleans temporary files.
Interrupted streams can resume within the call only when a known total and strong
ETag permit validated Range/If-Range recovery; ignored Range resets safely.

Validation: 74 real-local-socket/contract engine tests and 3 CLI tests passed;
the complete API suite passed 250 tests, pip check passed. Independent review
identified a non-string digest validation bug; its regression test now passes.
No lockfile/dependency change, public provider enablement or claimed TeraBox
transfer. See DOWNLOAD_ENGINE.md for exact commands and limitations, including
trusted output paths, cooperative disk deadlines and no cross-process resume.
Parallel/adaptive algorithms remain unimplemented pending measured justification.

## 2026-11-17 — Controlled recovery benchmark

Added `scripts/benchmark_download_engine.py` and persisted the complete measured
JSON as `docs/ENGINE_BENCHMARK_2026-11-17.json`. Command: API venv Python running
the script with `--size-mib 4 --repeats 3`; a minimum-size smoke also passed.
All nine measured actual-socket transfers matched the 4 MiB fixture hash/size.
Median elapsed clean/restart/resume: 0.044010/0.044481/0.045834 seconds; body bytes
4,194,304/4,718,592/4,194,304. Resume avoided 512 KiB retransmission; no speed
advantage claimed. Traced allocations and limits are reported in DOWNLOAD_ENGINE.md.
No third-party service, parallel scheduling or production throughput was tested.

## 2026-11-17 — Typed website metadata and truthful states

Added `apps/web/app/api-contract.ts` to validate successful validation/resolution
JSON at runtime and provide TypeScript models aligned with current API schemas.
The page renders only returned file name/kind/byte size/MIME/quality labels, has
an honest empty state, rejects malformed responses and clears metadata on edits,
new validation or resolution. No download/preview action or progress was invented.
Existing abort/deadline logic remains; stale provider references on new validation
were also cleared. String validation bounds allocation before counting Unicode.

Build and typecheck passed. Fresh-server Playwright passed 20 checks (10 scenarios
in desktop/mobile). New metadata cases are explicitly simulated: hostile names
rendered as text, invalid payloads rejected, empty list, delayed stale resolution
discarded and malformed validation rejected. Real local API still returns truthful
provider-unconfigured status. Initial stale-server and route-announcer selector
failures were diagnosed and corrected; the final current-build run passed.

## 2026-11-17 — Final independent-engine continuation and inventory

Remote main confirmed five meaningful checkpoints before this documentation
checkpoint: `a03a4c3` (audit/plan), `f36a72b` (extension), `0a8117a` (engine/CLI),
`bf1eea2` (benchmark), `5b9ac57` (typed website). Every push was accepted; no force
push, history rewrite, source deletion or dependency change was used.

Current root/status/structure/setup/roadmap/checklist docs reflect independent
engine priority and actual evidence: 250 API, 50 extension, 20 browser checks,
build/typecheck and pip consistency passed. All 97 tracked files are covered in
the current handoff; the dated audit retains its 82-file/18-directory baseline.
CODEX_CONTINUITY.md records exact checkpoint references, commands, limitations
and the next five focused tasks. No visitor transfer API, production deployment,
parallel/adaptive scheduling, durable resume or live TeraBox success is claimed.

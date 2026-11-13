# Delivery Roadmap, Quality Gates and Credible Status

**Status:** Planned; this document does not certify any implementation.  
**Updated:** 2026-11-13

## What is actually in the repository?

At initialization on 2026-11-13, only a README existed. On the `feat/phase-0-foundation` branch, an initial FastAPI share-link validator, disabled provider adapter, responsive Next.js development UI, Chrome/Edge extension popup, and CI have now been committed. **20 API unit tests passed locally**, and the [GitHub Actions run](https://github.com/kawakaze430/create-terabox-downloader/actions/runs/43470500522) passed all three jobs (API, website production build, extension syntax). **No authorized TeraBox metadata, preview, download, browser-based integration or production deployment has yet been demonstrated.**

## Hard-gated development plan

| Gate | Implementation focus | Exit criteria — required evidence |
| --- | --- | --- |
| G0 — Audit / feasibility | Audit repo and reference projects, license review, provider terms and authorized interface | Written comparison, risk register, architecture decision and realistic test plan; no unsupported assumptions |
| G1 — Download engine proof | URL validation, permitted metadata/preview/download flow, structured errors | Reproducible authorized test shares; working actual transfers; clear blocker if unavailable; mocks kept separate |
| G2 — Complete core product | Website, player, details, folders where supported, Chrome/Edge extension, shared API | Web and extension E2E with authorized shares; responsive UX; permission and accessibility review |
| G3 — Production readiness | CI, security, observability, deployment, rate limits, support and policy docs | Passing CI and security checks, staging smoke tests, operational metrics, cost-budget approval |
| G4 — Differentiation | History/bookmarks, Continue Watching, themes/locales, more workflows, Firefox/PWA where justified | Usage evidence and measurable user value; security and regression tests |
| G5 — Commercial growth | Accounts, developer API, premium memberships, subscriptions, further apps | Legal/compliance approval, secure billing, privacy, customer support, scalable operations |

**Do not accelerate into G4/G5 while G1 fails or is unverifiable.** This protects both the business and Codex credits.

## Initial work queue (not claims of completion)

- [ ] Verify upstream TeraBox access policies and permissible technical integration.
- [ ] Audit each reference repository's current source, feature completeness, activity, vulnerabilities, external services, and license.
- [ ] Decide the shared API contract and provider capability model.
- [ ] Implement server-side URL/redirect allowlist and SSRF tests.
- [ ] Build mocked fixtures for file/folder metadata and expected error states.
- [ ] Create/revoke own authorized test shares for real integration tests.
- [ ] Demonstrate at least one verifiably completed authorized file download.
- [ ] Prove correct expiry, unsupported, access denied and provider failure handling.
- [ ] Build the responsive website and playback controls on top of verified API.
- [ ] Build Chrome/Edge extension with minimal permissions and common backend.
- [ ] Add bounded folder/ZIP workflows if provider and operating budget support them.
- [ ] Add CI, browser E2E, dependency/license/security checks and staging.
- [ ] Review analytics, privacy, content/copyright reporting, terms and support.
- [ ] Measure actual reliability, latency, cost and browser compatibility.
- [ ] Prioritize optional features based on usability evidence.

## Test matrix

| Scenario | Expected behavior |
| --- | --- |
| Valid own public share, small file | Accurate metadata and authorized completed download |
| Valid own public share, larger file | Accurate size; reasonable handoff/progress; no unexpected memory spikes |
| Multi-file folder | Correct listing and child paths; bounded selection; only supported batch/ZIP actions |
| Nested folder/search | Correct pagination/filtering and breadcrumbs |
| Unsupported domain or malformed URL | Immediate safe validation failure; no backend arbitrary fetch |
| Redirect to private IP/internal service | Block request and log a safe diagnostic code |
| Expired/removed share | Explicit unavailable/expired error; no false download button |
| Protected/access-limited share | Request compliant access or mark unsupported; never bypass |
| Temporary download link expiration | Explain and optionally re-resolve only through permitted flow |
| Unsupported codec or preview | Download can remain available if permitted; player shows graceful fallback |
| No alternative qualities | Show the actual available file only, not imaginary 480p/720p/1080p |
| Upstream timeout/rate-limit | Finite retries/backoff, clear message, no uncontrolled retry storm |
| Mobile screen / slow network | Usable responsive interface, sensible loading and failure state |
| Extension on unrelated site | No invasive behavior or unrelated host access |
| Browser download cancellation | UI exits pending state; bounded cleanup |
| Oversized ZIP/concurrent batch | Deterministic size/quota rejection and cleanup |
| Privacy / telemetry | No secrets or raw share links in normal logs; deletion and retention tested |

## Success metrics and honest reporting

For each release, report *actual values* and test data, not guesses:

- `supported_share_resolution_success_rate` with denominator and share class documented.
- `completed_authorized_download_rate`, acknowledging that browser handoff is not the same as transfer completion.
- Metadata resolution p50/p95, download handoff p50/p95, and upstream error categories.
- Regression pass rate, critical vulnerabilities, browser extension permissions, accessibility checks.
- Hosting and bandwidth cost per successful operation; ZIP and API resource usage.
- User task completion (paste → preview/download), satisfaction, support incidents.

An aspirational benchmark is **at least 95%** resolution success for a defined representative sample of accessible, supported shares; this is **not** a current measured result or universal guarantee.

Maintain a per-feature status table with these exact categories as implementation progresses: **Not started; Implemented/unverified; Verified with mocks; Verified with authorized live test; Blocked by upstream/policy; Deferred.** Cite test command and date in each verified entry.

## Codex credit conservation rules

1. Read `README.md`, `AGENTS.md` and relevant docs, then inspect actual code before editing.
2. Audit what already works; do not regenerate the entire app or build a duplicate frontend/backend.
3. Use compatible maintained libraries for media, testing and monitoring rather than recreating them.
4. One deliverable per scoped change set with relevant tests and a concrete exit criterion.
5. Prefer small reviewed commits and reuse the existing workspace; do not start needless new tasks.
6. Keep implementation code separate from speculative future ideas; provide interface seams instead.
7. If authorization/provider access is blocked, document evidence and stop that work rather than inventing compatibility or adding cosmetic features.
8. Run the smallest relevant checks before heavy E2E; run full suite at milestones.
9. Do not repeatedly reinstall all dependencies when the environment is already usable.
10. Preserve functioning code; avoid broad reformatting that obscures real changes.

## Release definition of done

Release is ready only when: permitted integration works in live authorized tests; important UI and extension workflows pass; appropriate licensing notices are present; critical security issues are resolved; error monitoring and runbooks exist; production costs are bounded; data handling, support and copyright reporting documentation is available; release is deployed and tested in the owner's infrastructure. Record any remaining limitations publicly and clearly.

## Handover to any new developer

Start with `README.md` → `AGENTS.md` → `docs/PRODUCT_REQUIREMENTS.md` → `docs/ARCHITECTURE.md` → this roadmap → `docs/RESEARCH_AND_LICENSES.md`. Inspect latest commits, PRs, issue board, deployed environments, test reports and known failures. Never infer completed features from a checklist target or README marketing statement.

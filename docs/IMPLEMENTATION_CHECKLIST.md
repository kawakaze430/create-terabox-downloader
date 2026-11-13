# Ordered Implementation Checklist

**Updated:** 2026-11-13. **This is the live plan, not a claim of completion.**
A checkmark is used only for implemented items with the evidence noted. The starter website and extension exist as source but have NOT been live/browser-tested. The TeraBox downloader engine is NOT connected.

## Gate 0 — Project foundation and feasibility
- [x] Publish mission, feature requirements, architecture and developer instructions (README, AGENTS.md, docs/).
- [x] Establish feature branch and initial Python API, Next.js website and Manifest V3 extension source (feat/phase-0-foundation).
- [x] Create strict offline-only share-link parser and disabled provider contract (services/api/app/).
- [x] Run initial parser/API unit tests (20 tests passed locally on 2026-11-13).
- [x] Check extension JS syntax/manifest JSON locally (2026-11-13).
- [x] Verify GitHub CI for API, Next.js production build, extension checks: [successful run](https://github.com/kawakaze430/create-terabox-downloader/actions/runs/43470500522) (2026-11-13). Browser/manual tests remain pending.
- [ ] Generate and commit locked dependency manifests; pin patch versions and audit vulnerabilities.
- [ ] Audit all five reference repositories for features, current licenses, code health and upstream dependencies.
- [x] Review TeraBox's published terms and record outstanding API authorization questions in [PROVIDER_FEASIBILITY.md](PROVIDER_FEASIBILITY.md) (2026-11-13); a usable permitted integration remains unconfirmed.
- [ ] Create or receive own authorized, non-sensitive sample TeraBox share URLs for functional tests.

## Gate 1 — Authorized core engine (BLOCKED pending viable permitted provider)
- [x] Validate known share URL formats, reject unsupported domains/paths (offline parsing only).
- [x] Expose versioned API validation route and structured error codes.
- [x] Add provider adapter seam; deliberately return PROVIDER_NOT_CONFIGURED instead of fictional file metadata.
- [x] Add typed metadata/capabilities schema, bounded upstream-error mapping and readiness checks; verified with offline fixtures in `services/api/tests/test_provider_contract.py` (CI evidence pending).
- [ ] Security review of allowed share hosts/path variants, redirect behavior, DNS/SSRF egress, and rate limits before HTTP fetching.
- [ ] Select and legally/security-validate permitted provider implementation.
- [ ] Get real metadata: filename, size, type, thumbnails, folders (where offered).
- [ ] Get real playable preview URL and supported quality options (where offered).
- [ ] Get permitted downloadable file; verify a completed real transfer using own authorized files.
- [ ] Support expiry, protected links (only permitted access), missing/removed links, upstream outages.
- [ ] Add provider contract and live integration tests for valid, expired, unavailable, folder and large-file cases.
- [ ] Benchmark real resolution speed, success/failure and bandwidth cost.

## Gate 2 — Complete minimum competitive product
- [x] Add initial mobile-friendly Next.js input/status interface (CI production build passed; browser behavior untested).
- [x] Add initial Chrome/Edge Manifest V3 popup for recognizing supported share links (browser testing pending).
- [x] Verify Next.js production build in GitHub CI (run 43470500522).
- [ ] Verify frontend API connectivity in browser and accessibility.
- [ ] Verify extension behavior in real Chrome and Edge without excessive permissions.
- [ ] Implement verified file metadata cards and real preview thumbnails.
- [ ] Add proper media player with fullscreen/PiP and source-specific unsupported states.
- [ ] Implement real download handoff, safe filenames and truthful progress reporting.
- [ ] Add authorized folder browser, pagination and search.
- [ ] Add bounded multi-file selection and ZIP jobs where provider, rights and cost permit.
- [ ] Display ONLY available quality/format options and support correct fallbacks.
- [ ] Original brand, consistent mobile/desktop UX, theme, localization foundation.

## Gate 3 — Production, privacy and operational quality
- [ ] Add exhaustive URL/redirect SSRF tests, HTTP egress limits, size/time/concurrency quotas.
- [ ] Add API rate limiting, secure error handling, privacy-safe logs and secret management.
- [ ] Add unit/contract/E2E Playwright tests, cross-browser extension tests and CI gates.
- [ ] Add health/readiness, monitoring/alerts, incident runbook and cost dashboard.
- [ ] Deploy owned staging environment, test with authorized files and track releases.
- [ ] Add Docker/reproducible local setup, reliable dependency locks, backups where applicable.
- [ ] Add domain, HTTPS, SEO, support, privacy policy, terms and copyright reporting.
- [ ] Publish extension only after store and permission-policy review.

## Gate 4 — Competitive differentiation (after reliable release)
- [ ] Picture-in-picture improvements, actual subtitles if provided, optional Continue Watching.
- [ ] Bookmarks and download/history controls with privacy and deletion.
- [ ] Supported HTTP Range/resume, link expiry recovery, copy link for external download managers where safe.
- [ ] Advanced folder search, batch workflow and performance improvements.
- [ ] Dark/light theme and prioritized international languages.
- [ ] Firefox browser compatibility, installable PWA, performance and accessibility work.
- [ ] Dated competitor benchmark with own supported authorized test set.

## Gate 5 — Commercial platform and growth (after core validation)
- [ ] Optional secure user accounts, settings/history sync and consent.
- [ ] Versioned public API with auth, quotas, documentation and abuse prevention.
- [ ] Premium entitlements, subscriptions and billing compliance if viable.
- [ ] Support operations, user feedback, reliability and cost reviews.
- [ ] Evaluate Android, Telegram bot and other channels with separate security/legal decisions.
- [ ] Measure actual user completion and retention; prioritize based on evidence.

## Hard acceptance rules
- **Do not call mock data a working download.**
- **Do not bypass TeraBox auth, access controls, DRM, premium restrictions or others' rights.**
- **Do not blindly merge unrelated repositories or reuse code without license verification.**
- **Do not advance to premium/billing features while a legitimate core downloader is unproven.**
- For each newly checked item record code, test method/date and any limitations.

## Blocker for Codex/developer
**Provider integration G1:** See [PROVIDER_FEASIBILITY.md](PROVIDER_FEASIBILITY.md) for reviewed terms, domain lookalike warning, contract implementation and Codex review tasks.

**Provider integration G1:** First determine whether the current provider supports an authorized, stable API or integration. Use user-owned public test files and permitted access. If unavailable, return a grounded feasibility report and keep the provider disabled rather than pretending downloads work.

# Technical Architecture and Engineering Standards

**Status:** Proposed target architecture — validate against the real codebase before committing to implementation.  
**Updated:** 2026-11-13

## Architectural north star

**One owned monorepo, multiple presentation surfaces, one backend/API contract, one replaceable authorized provider integration.** Prefer a modular monolith until traffic and engineering evidence justify separate services.

```text
Browser website (Next.js/React) ─┐
Chrome/Edge MV3 extension ──────┼── HTTPS / versioned API
Future clients ─────────────────┘             │
                                         FastAPI backend
                                              │
                                 Link validation / abuse checks
                                              │
                                 Provider adapter interface
                                              │
                                 Permitted TeraBox integration
                                              │
                       Metadata / preview / authorized download handoff

Supporting: CI/CD · telemetry · docs · tests · staging · optional database
```

## Proposed repository layout

```text
/
├── README.md                  # Entry point and honest status
├── AGENTS.md                  # Instructions for Codex and contributors
├── docs/
│   ├── PRODUCT_REQUIREMENTS.md
│   ├── ARCHITECTURE.md
│   ├── ROADMAP_AND_QA.md
│   └── RESEARCH_AND_LICENSES.md
├── apps/
│   ├── web/                   # Next.js + TypeScript + Tailwind (proposed)
│   └── extension/             # Chrome/Edge Manifest V3 (proposed)
├── services/
│   └── api/                   # Python FastAPI provider-integrated backend
├── packages/
│   └── contracts/             # Versioned JSON Schema/OpenAPI types or generated clients
├── tests/                     # Unit, contract, integration and E2E
└── infra/                     # Docker, CI, hosting configs, runbooks
```

This layout is a **target**. Do not manufacture empty folders or overwrite working code just to match the diagram. Document deviations and decisions.

## Provider adapter: critical boundary

Define a minimal provider contract with capabilities discovered at runtime:

- `normalizeShareUrl(input)`: validate supported URLs, strip unsafe tracking info and normalize.
- `getShareMetadata(share)`: filenames, sizes, types, thumbnails, expiry where known.
- `listFiles(share, folderCursor)`: only if folder browsing is supported.
- `getPreview(share, fileId)`: allowed preview URL/type when available.
- `getDownload(share, fileId)`: authorized, time-bound transfer handoff; no fabricated direct URLs.
- `getCapabilities(share)`: per-share support (folders, ZIP, qualities, range, streaming, password flow).

Interface signatures can differ by implementation language; the invariant is that **the UI never relies on an undocumented provider's internal response schema**. Unknown capabilities are unsupported, not assumed.

Evaluate permitted API options first. Public third-party GitHub repos are reference implementations only; any reliance on scraping, cookies, proxy workers or unofficial endpoints must be documented, legally/operationally reviewed and tested. If there is no feasible compliant provider integration, explicitly block the milestone instead of wasting credits on cosmetic features.

## API surface (illustrative, not implemented)

- `POST /api/v1/shares/resolve` — link input → sanitized metadata, share-scoped opaque ID and capabilities.
- `GET /api/v1/shares/{id}/files` — authorized folder listing with pagination.
- `POST /api/v1/downloads` — select file(s); return short-lived authorized handoff or bounded job status.
- `GET /api/v1/jobs/{id}` — optional ZIP/batch job progress and result.
- `GET /healthz` / `GET /readyz` — service health and readiness.

Use generated OpenAPI or shared schema to keep website and extension compatible. Explicitly version responses and model failures with stable error codes: `INVALID_LINK`, `UNSUPPORTED_HOST`, `EXPIRED_SHARE`, `AUTH_REQUIRED`, `ACCESS_DENIED`, `NOT_FOUND`, `UPSTREAM_UNAVAILABLE`, `RATE_LIMITED`, `UNSUPPORTED_OPERATION`. Do not include secrets or raw upstream tokens in errors.

## Website and player

- Mobile-first responsive design; original visual identity; fast path to paste → inspect → download.
- React/Next.js and Tailwind are recommended, not mandates without code inspection.
- Use an established media stack such as [Video.js](https://github.com/videojs/video.js) and, if genuinely required for compatible HLS media, [hls.js](https://github.com/video-dev/hls.js).
- Video player states: loading, ready, unsupported format, missing preview, denied share, expired stream. Fullscreen/PiP when browser supports; captions only when available and permitted.
- Do not convert/transcode merely to advertise fake quality choices.

## Extension

- Chrome and Edge: Manifest V3; popup and optional supported-page action.
- Request **minimal** host, tab and download permissions; no blanket browsing-history tracking.
- Send a validated share link to the same backend; do not embed server secrets or persist raw provider account cookies.
- Use browser download APIs for permitted handoffs; test temporary URL expiry and errors.
- Publish only after permission review, privacy disclosures and manual browser tests.

## Data and operational dependencies

First release can avoid a database if share state can be short-lived and stateless. Use PostgreSQL for optional accounts/history/billing only when required. Use Redis or a bounded queue for jobs/rate limiting only if deployment warrants it. Do not invent infrastructure that adds maintenance without a demonstrated need.

For downloads, prefer a permitted direct browser handoff if safely available. Proxying video through our infrastructure can incur very large bandwidth cost, privacy exposure, failure modes and legal consequences. If a proxy/ZIP worker is essential: require admission limits, timeouts, maximum size, concurrency quotas, temporary storage lifecycle, cancellation, and an explicit cost model. HTTP Range/resume only if the upstream actually supports it.

## Security baseline

- Parse input URL; allow only exact known schemes/hosts; forbid arbitrary redirects and DNS targets (SSRF, rebinding, internal/private/link-local IP defense).
- Enforce network egress rules on server-side HTTP clients; revalidate every redirect.
- Apply rate limits, timeouts, request-size limits, pagination caps, ZIP decompression/size safeguards and per-origin rules.
- Secrets in an approved secret manager/environment; never commit credentials, cookies, signed URLs or production traces.
- Restrict CORS to deployed clients; version API and protect state-changing endpoints.
- Prevent XSS, injection, insecure direct object reference and malicious filenames; review browser extension message handlers and CSP.
- Short-lived opaque identifiers; explicit auth design before account features.
- Respect provider restrictions; never implement a protection bypass.
- Privacy-safe structured errors/metrics; audit and delete any data retention.

## Suggested tooling and dependency rules

- Quality: ESLint/TypeScript, Python Ruff/pytest, type checking, OpenAPI schema validation.
- Browser automation: [Playwright](https://github.com/microsoft/playwright).
- Observability: error reporting such as [Sentry SDK](https://github.com/getsentry/sentry-javascript), after privacy and cost review.
- Evaluate any download-manager functionality with normal browser APIs first. [aria2](https://github.com/aria2/aria2) has GPL obligations; do **not** embed it by default without explicit license review.
- [ffmpeg.wasm](https://github.com/ffmpegwasm/ffmpeg.wasm) is a later optional tool, not a mandatory dependency.

Pin versions; scan vulnerabilities and licenses; keep dependency count manageable. Never copy code from a repo without determining applicable license and required notices.

## Deployment, staging and observability

Suggested: static/server-rendered frontend on an appropriate web host, API on a Python-capable host, and independent domain/accounts owned by the project owner. Vercel and managed Python hosting are candidate choices, not required vendors. Maintain example environment variables, reproducible development setup, Docker where helpful, and separate production/staging configs.

Record aggregated: provider resolve success by supported share class, failures by error code, p50/p95 latency, downloads handed off, extension errors, server resource consumption, bandwidth cost per successful download, and rate-limit hits. Avoid logging share URLs or personal file details unless strictly needed with explicit retention controls. Add alerts for sustained failure and unexpected cost spikes.

## Testing and change-management standards

Unit tests for validation and errors; contract tests for provider adapter and API; authorized integration tests using revocable test shares; Playwright E2E; extension smoke tests; SSRF/security regression checks; browser/device accessibility checks. Never treat mocked tests as proof of upstream functionality.

Maintain ADR-style decisions for high-impact architectural changes (an ADR index may be added as work begins). Update documentation and the feature-status matrix with evidence for each merged milestone.

See [ROADMAP_AND_QA.md](ROADMAP_AND_QA.md) for acceptance gates and [RESEARCH_AND_LICENSES.md](RESEARCH_AND_LICENSES.md) for references.

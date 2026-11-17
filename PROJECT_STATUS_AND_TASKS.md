# Project status, file guide, and implementation tasks

> Historical implementation handoff from 17 November 2026. Current checkpoints and tasks are in [CODEX_CONTINUITY.md](docs/CODEX_CONTINUITY.md). See the [incident review](docs/security/incident-review.md) for current repository handling and owner actions. The task and verification history below describes the earlier baseline.

## Contents

1. [Goal and architecture](#1-goal-and-architecture)
2. [What is implemented](#2-what-is-implemented)
3. [Every folder and tracked file](#3-every-folder-and-tracked-file)
4. [Ordered implementation tasks](#4-ordered-implementation-tasks)
5. [Development commands and evidence](#5-development-commands-and-evidence)
6. [Instructions for the implementing tool](#6-instructions-for-the-implementing-tool)
7. [PR review and monitoring](#7-pr-review-and-monitoring)

## 1. Goal and architecture

Build an independently branded, reliable TeraBox file-access product: a responsive website, Chrome/Edge extensions, and one shared backend. A user should be able to paste an authorized supported share, see its real files and available capabilities, preview supported media, and complete an authorized download with accurate errors. Aim for measurable reliability, accessibility, privacy, performance, and sustainable operating cost. Market leadership is an ambition, not an established fact.

The owner controls the product's source, brand, hosting, domain, release process, and credentials. TeraBox remains an external dependency; owning this application cannot guarantee access to every remote file.

```text
Next.js website ───────────┐
                          ├── versioned JSON API ── FastAPI
Chrome/Edge extension ─────┘                           │
                                            validation and limits
                                                     │
                                              provider contract
                                                     │
                                  currently: UnconfiguredProvider
                                                     │
                                  future: approved user-scoped adapter
                                                     │
                                  real metadata / preview / transfer
```

Today the extension opens the website; it does not itself resolve or download files. The separate operator probe is an integration candidate, not the public provider.

The independent transfer engine is `services/api/app/download_engine.py`, operated through `download_cli.py` or a trusted Python caller. It consumes an already authorized direct source, separately from share resolution. No public arbitrary-URL transfer route was added. Strong-validator in-call resume is implemented; parallel ranges, adaptive scheduling and cross-process resume are not. See `docs/DOWNLOAD_ENGINE.md`.

Keep the existing Python FastAPI, Next.js/TypeScript, and small JavaScript extension. Do not rewrite them, merge whole reference projects, or create empty framework folders to match an architecture proposal. There is currently no application database, account service, job queue, payment system, AI media engine, or production deployment configuration.

### Delivery gates

| Gate | Required outcome | Current state |
| --- | --- | --- |
| G0 — Foundation and feasibility | Understand source, establish reproducible checks, audit references and permitted access | Foundation and historical audits exist; current access permission still unresolved |
| Generic engine milestone | Accessible-source streaming/recovery and complete size/hash verification | **Implemented and local-socket tested**, independently of TeraBox |
| G1 — TeraBox source proof | Real metadata and a completed owned-file TeraBox download with correct size and SHA-256 | **Unverified source access; separate from completed generic engine work** |
| G2 — Core product | Website and extension consume verified API; supported previews, folders, and downloads | Validation/handoff foundation only |
| G3 — Production readiness | Owned staging, security, privacy, operations, release and store checks | CI/local checks exist; production work incomplete |
| G4 — Differentiation | Useful playback, local preferences, localization, supported resume and extra browsers | Deferred |
| G5 — Growth | Optional accounts, developer API, billing, additional platforms | Deferred |

**Do not start premium, AI, or unrelated product expansion because G1 is blocked.** Continue bounded security/contract work that helps G1 and report the external requirement. Any alternative owned-media product direction needs an explicit owner decision.

## 2. What is implemented

Status definitions:

- **Verified locally/offline:** exercised without contacting TeraBox; includes local web-to-API behavior.
- **Mock-tested candidate:** source and synthetic upstream tests exist; real provider compatibility is unproven.
- **Partial:** some supporting code exists, but the complete user journey does not.
- **Blocked:** an external permission, credential, fixture, or capability is missing.
- **Not implemented / deferred:** a requirement or idea, not a feature users can use today.

| Feature | Actual behavior today | Evidence / boundary |
| --- | --- | --- |
| Independent download engine | Bounded streaming-to-disk, connect/read/total deadlines, transient GET retries with jitter/Retry-After, expected size/hash, cancellation cleanup and atomic no-clobber completion | 74 engine + 3 CLI tests against controlled local sockets/invalid-input cases; production defaults to exact-host DNS-pinned HTTPS. No new dependency or public URL-fetch endpoint |
| Range recovery | Resume an interrupted call only with strong ETag and known size; validate 206 interval/total/version, restart on ignored Range | Tested including corruption/changed ETag/truncated response; no durable resume or parallel/adaptive algorithm |
| Share-link validation | Exact HTTPS host/path checks; rejects malformed inputs, credentials, unsupported ports/hosts; normalizes supported URL shapes | Verified offline in `links.py`, API and extension parser tests. Valid syntax does not prove the file exists or may be downloaded |
| Versioned API | Health, readiness, validation, and resolve routes with typed safe responses | Local/offline tests; routes listed below |
| Provider abstraction | Typed files/capabilities, errors, injectable provider interface | Mock-tested contract. Capability fields do not implement downloads or preview |
| Request/security controls | Body/deadline/rate/concurrency limits, bounded client memory, redacted errors, CORS and privacy headers | Verified offline. Rate/concurrency state is per process; shared production quotas are absent |
| Approved outbound transport | Exact HTTPS hosts, public DNS checks, checked-IP pinning with TLS SNI, no redirect or implicit proxy fallback | Synthetic DNS/HTTP tests; real hosting/API/CDN compatibility remains unverified |
| Official OAuth helper | Authorization URL/signature, token exchange/refresh/info and approved regional host checks | Mock-tested candidate; no visitor login/callback/session/token store |
| Operator metadata/download probe | Candidate metadata/link calls; explicit live opt-in; bounded full transfer with size and checksum verification | Mock-tested only; not wired into public resolve; no live successful transfer recorded |
| Website | Responsive validation/status flow plus strict runtime response guards, returned file metadata/qualities/empty states, safe errors/deadlines, stale-request cancellation and private handoff clearing | 20 desktop/mobile browser checks, including explicitly simulated metadata. Real TeraBox data remains unavailable; no media/download action or progress UI |
| Extension | MV3 active-tab fragment handoff, validated configurable website origin, popup failure states and deterministic minimal release packaging | 50 parser/popup/packaging tests; checked-in local default, selectable owned HTTPS release origin; installed Chrome/Edge/store flow unverified |
| CI and reproducible installs | Locked Python/npm dependencies; API, web, and extension checks | Workflow source exists. Current fork's PR/CI state was not accessible during this handoff |
| Documentation/reference recovery | Product plans, historical records, Word archive verifier, two isolated sanitized reference ZIPs, safe extraction | Supporting material, not additional implemented product features |
| Live TeraBox metadata/download/preview | No verified public source adapter; webpage can render a valid sanitized metadata response | Real source access and scoped integration still required; generic operator engine already exists |
| Folders, batch/ZIP, protected-share access | No active routes or user workflow | Planned; implement only supported permitted operations |
| Production hosting, monitoring, support/legal pages, published extension | Not delivered by this repository | Tasks below |
| History/bookmarks, theme switch, i18n, accounts, billing, public developer auth/API, PWA/mobile/AI | No active implementation | Later gated work only |

### API behavior to preserve

| Route / command | Expected current result |
| --- | --- |
| `GET /healthz` | HTTP 200; process operational; provider `not_configured` |
| `GET /readyz` | HTTP 503 while provider unavailable; do not make it report ready just to pass a check |
| `POST /api/v1/shares/validate` | Supported valid URL shape returns normalized URL; no upstream request |
| `POST /api/v1/shares/resolve` | Recognized valid link returns HTTP 501 `PROVIDER_NOT_CONFIGURED` by default |
| `python -m app.preflight` | Offline configuration report; exit 2 while required live settings are absent |
| `python -m app.preflight --live` | Explicit authorized operator probe only; **not successfully exercised against TeraBox** |
| `python -m app.download_cli` | Generic permitted HTTPS transfer using private `ENGINE_SOURCE_URL`, explicit host allowlist, output path and limits; no OAuth dependency |

## 3. Every folder and tracked file

The tables cover every versioned file at the inspected snapshot, plus this new handoff. Excluded dependency files and generated caches are explained separately. Files *inside* the third-party ZIPs are reference-project internals: their full 341-member listing is in [ZIP_MEMBER_INVENTORY.txt](research/archives/ZIP_MEMBER_INVENTORY.txt), not part of our implemented feature count.

### Folder map

| Folder | Purpose and ownership |
| --- | --- |
| Repository root | Project entry, handoff, contributor rules, structure and research index |
| `.github/` → `workflows/` | GitHub automation; one existing CI workflow |
| `apps/` | User-facing clients of the shared backend |
| `apps/web/` | Next.js website dependencies, configuration, source and browser tests |
| `apps/web/app/` | Root layout, home page and global CSS; no separate metadata/player/folder pages yet |
| `apps/web/tests/` | Playwright local website/browser scenarios |
| `apps/extension/` | MV3 popup and URL handoff; no background worker or content script |
| `apps/extension/tests/` | Node parser/handoff tests; not an installed-extension test harness |
| `services/` → `api/` | Python API configuration, dependency locks, code and tests |
| `services/api/app/` | Independent transfer engine/CLI, routes, URL admission, models, limits, disabled TeraBox provider and optional operator clients |
| `services/api/tests/` | Engine/CLI local-socket and existing API/provider/OAuth/egress/limit/probe tests |
| `scripts/` | Controlled benchmarks, deterministic extension packaging and safe reference extraction, not an application service |
| `docs/` | Requirements, technical plans, operator/setup guides and dated continuity records |
| `docs/history/repository-reviews/` | Review reports, inventories, recovered ideas and reference material; not a second application |
| `research/archives/` | Two sanitized third-party ZIPs and their inventory/extraction guide |
| `research/future-ideas/` | Preserved older broad product/media/AI vision |
| `docs/security/recovery/` | Dated repository restructuring audit |

### Root and automation files

| File | What it does / how to use it |
| --- | --- |
| `README.md` | GitHub homepage overview and navigation; states honest current functionality |
| `PROJECT_STATUS_AND_TASKS.md` | This current operational handoff: implementation status, complete file guide, task IDs, acceptance and PR review |
| `AGENTS.md` | Contributor instructions; current owner workflow and architecture/security constraints |
| `PROJECT_STRUCTURE.md` | Concise directory/feature ownership map and placement rules |
| `PUBLIC_REPOSITORY_STUDY_LIST.txt` | 49 research repository links and licensing cautions; no installed engines |
| `.gitignore` | Excludes environments, secrets/local settings, dependencies, builds, test outputs and extracted references; keeps example settings |
| `.github/workflows/ci.yml` | API pytest/pip/archive/offline-preflight checks; web install/build/typecheck/browser checks; extension syntax/parser/manifest checks. Runs for PRs and `main` pushes; does not deploy or test live TeraBox |

### API files

| File | Implemented responsibility / limit |
| --- | --- |
| `services/api/.env.example` | Names/defaults for local origins, admission limits, partner credentials, approved hosts and owned-file probe. No live values. CLI does not load `.env` automatically |
| `services/api/requirements.txt` | Pinned direct API/test dependencies; update deliberately with the full lock |
| `services/api/requirements.lock` | Resolved Python 3.12 dependency set used for reproducible installation and CI; version-pinned, not artifact-hash-pinned |
| `services/api/app/__init__.py` | Python application package marker; no business feature |
| `services/api/app/download_engine.py` | Source-independent streaming/retry/integrity/atomic output and strict in-call Range recovery; trusted source/destination inputs, pinned HTTPS by default |
| `services/api/app/download_cli.py` | Operator CLI reads private source URL from environment, uses allowlisted hosts/limits and outputs sanitized actual transfer statistics |
| `services/api/app/main.py` | FastAPI app factory, current four routes, request schemas, CORS, provider timeout and sanitized errors |
| `services/api/app/links.py` | Offline exact-host/path URL parser and normalizer; no metadata fetch |
| `services/api/app/provider.py` | `ShareProvider` protocol, public error mapping and intentional `UnconfiguredProvider`; extension point for a future authorized adapter |
| `services/api/app/models.py` | Strict file/capability/response schemas with bounded names, IDs and collections; no tokens or raw upstream download URLs in public models |
| `services/api/app/limits.py` | Body/type/deadline guards, rate/client-count/concurrency admission and privacy headers; in-memory single-process quotas |
| `services/api/app/open_platform.py` | Official OAuth/signature/token/region candidate; validates credentials and responses; only mock-tested, not public auth |
| `services/api/app/egress.py` | Approved-host, public-DNS, IP-pinned TLS transport; used by operator integration, with no unsafe redirect/proxy fallback |
| `services/api/app/official_shares.py` | Operator-only candidate metadata, selected-file link and complete size/SHA-256 transfer check. Limited public `/s/1...` share/root file flow; no recursive folders or player |
| `services/api/app/preflight.py` | Offline config checker and explicit `--live` probe; safe JSON and exit codes; does not enable public provider |
| `services/api/tests/test_api.py` | Route/URL normalization, rejection, health and related API behavior |
| `services/api/tests/test_download_engine.py` | 74 controlled socket/admission/policy/retry/integrity/range/cancellation/publication tests; no TeraBox access |
| `services/api/tests/test_download_cli.py` | Safe missing config, actual controlled CLI transfer, redacted integrity failure/cleanup |
| `services/api/tests/test_provider_contract.py` | Fake-provider injection, strict metadata/capability/error contracts and safe response boundaries |
| `services/api/tests/test_limits.py` | Rate/client memory/body/timeout/concurrency/privacy tests, including forwarded-header abuse cases |
| `services/api/tests/test_open_platform.py` | Mock OAuth/signature/token/region/error/response-limit tests; no live authentication |
| `services/api/tests/test_egress.py` | Synthetic host/address/DNS/pinned-IP/SNI/rebinding tests; no approved CDN connectivity proof |
| `services/api/tests/test_official_shares.py` | Mock metadata, selected-file, transfer/checksum failures, config preflight and no-network defaults |

### Website files

| File | Implemented responsibility / limit |
| --- | --- |
| `apps/web/.env.example` | Browser-visible API base URL, currently localhost. Never put credentials in `NEXT_PUBLIC_*` |
| `apps/web/package.json` | Pinned Next.js/React/TypeScript/Playwright and dev/build/start/typecheck/e2e scripts; no lint script |
| `apps/web/package-lock.json` | Exact npm resolution and artifact-integrity data; use `npm ci` |
| `apps/web/tsconfig.json` | Strict TypeScript, Next.js type/plugin configuration and import alias |
| `apps/web/next-env.d.ts` | Next-generated type references; avoid manual feature edits; dev/build may regenerate this tracked file |
| `apps/web/next.config.ts` | Website config with no-referrer, nosniff and frame-deny headers; not hosting/deployment infrastructure |
| `apps/web/app/layout.tsx` | English root document, development-preview metadata, global CSS import |
| `apps/web/app/globals.css` | Existing dark responsive page styles; no light-theme switching |
| `apps/web/app/page.tsx` | Client validation/status/returned-metadata/empty/error UI, request cancellation/deadlines and fragment clearing. No enabled player/download/progress action |
| `apps/web/app/api-contract.ts` | Runtime validation and TypeScript types for internal validation/metadata JSON, bounded names/qualities and safe fixed invalid-response errors; rejects extra upstream URL fields |
| `apps/web/playwright.config.ts` | Desktop/mobile Chromium projects; starts local production website and API, one worker, traces disabled, optional system Chromium path |
| `apps/web/tests/core.spec.ts` | Ten scenarios in two viewports: existing local flow plus simulated hostile-name metadata, malformed responses, empty files and stale-resolution cleanup. Intercepted metadata is not live TeraBox proof |

### Extension files

| File | Implemented responsibility / limit |
| --- | --- |
| `apps/extension/manifest.json` | Unpublished MV3 development extension; only `activeTab` permission; popup entry |
| `apps/extension/config.mjs` | Local development website origin; packager replaces only the ZIP copy with validated release origin |
| `apps/extension/popup.html` | Popup content/button/status and development disclosure; loads CSS and script |
| `apps/extension/popup.css` | Small dark popup styling |
| `apps/extension/popup.js` | Reads active tab, handles browser errors, enables supported-link action and opens website |
| `apps/extension/links.mjs` | Exact-host share parser, strict website-origin validation and configured normalized fragment handoff; no cookies/history scraping |
| `apps/extension/tests/links.test.mjs` | Share parsing and configured-origin rejection/canonicalization/handoff tests |
| `apps/extension/tests/popup.test.mjs` | Controlled browser stubs exercise supported/unsupported tabs, invalid config and safe navigation errors; not installed-extension evidence |
| `apps/extension/tests/package.test.mjs` | Deterministic ZIP content/origin/source-preservation and invalid-config checks; runs local Python builder |

### Documentation and tooling files

| File | Purpose / authority |
| --- | --- |
| `docs/README.md` | Index of current and historical documentation by responsibility |
| `docs/CODEX_CONTINUITY.md` | Current durable tasks, previous confirmed remote checkpoints, results, blockers and exact resume commands; newest owner execution priorities |
| `docs/DOWNLOAD_ENGINE.md` | Actual independent-engine algorithms, operator CLI, testing, limitations and benchmark guidance |
| `docs/ENGINE_BENCHMARK_2026-11-17.json` | Complete synthetic 4 MiB recovery benchmark samples, byte/attempt/hash/time/allocation measurements and interpretation limits |
| `docs/REPOSITORY_ORGANIZATION_AUDIT.md` | Complete dated 82-file/18-directory baseline classification and preserve/repair decisions; no needless source moves |
| `docs/EXTENSION_DEVELOPMENT.md` | Unpacked Chrome/Edge steps, safe destination configuration and deterministic packaging/checks |
| `docs/PRODUCT_REQUIREMENTS.md` | Target user journeys and feature IDs/priorities; requirements are not completed features |
| `docs/ARCHITECTURE.md` | Target boundaries, provider/API/security/deployment design; illustrative routes/folders are not automatically implemented |
| `docs/ROADMAP_AND_QA.md` | G0–G5 gates, test matrix, known local/historical evidence |
| `docs/IMPLEMENTATION_CHECKLIST.md` | Detailed gate checklist; maintain with this handoff after accepted work; older unchecked broad items can include partially completed work |
| `docs/IMPLEMENTATION_LOG.md` | Dated change/test history; append new evidence rather than rewriting old outcomes |
| `docs/LOCAL_DEVELOPMENT.md` | API, website, extension and browser-test setup; supplement with environment notes below |
| `docs/PROVIDER_FEASIBILITY.md` | Access/terms/technical constraints and blocked provider questions |
| `docs/OFFICIAL_OPEN_PLATFORM.md` | Official API/OAuth research, candidate implementation and partner prerequisites |
| `docs/OPERATOR_VALIDATION.md` | Existing approved-fixture live test runbook; required before any `--live` probe |
| `docs/RESEARCH_AND_LICENSES.md` | Primary reference audits, licenses, unsafe patterns to avoid and permitted selective reuse |
| `docs/START_HERE_PROJECT_HANDOFF.md` | Dated continuity snapshot; read for context, reconcile against this newer handoff/current source |
| `docs/PROJECT_CONVERSATION_ARCHIVE.md` | Recoverable historical request/change chronology, not a full raw chat export |
| `docs/MASTER_DEVELOPMENT_PROMPT_2026-11-15.md` | Verbatim historical owner prompt; preserve as evidence, apply newer owner directions where they differ |
| `docs/PROJECT_SOURCE_INDEX_2026-11-16.md` | Dated immutable source/reference links; old repository identity remains historical |
| `docs/PROJECT_MASTER_HANDOFF.docx` | Archived Word copy of project context; not automatically synchronized with every new change |
| `docs/verify_handoff_archive.py` | Stdlib CI verifier for Word archive structure and required historical content |
| `scripts/unpack_reference_archives.py` | SHA-256/CRC/path/symlink/size/count-checked reference ZIP extraction; verifies existing extracted files without blindly overwriting them |
| `scripts/package_extension.py` | Minimal reproducible six-file extension ZIP with reviewed permissions and validated build-time website origin; source config not mutated |
| `scripts/benchmark_download_engine.py` | Standalone controlled local HTTP clean/restart/resume comparison with real hash/size assertions, no external service and no parallel speed claim |

### Preserved review and archive files

These reports describe earlier inspections. Recheck claims against current code; do not use their old direct-to-main instructions over the owner's current PR workflow.

| File | Why it exists |
| --- | --- |
| `docs/history/repository-reviews/README.md` | Entry to isolated references, recovery records and known credential-history caveat |
| `docs/history/repository-reviews/REPOSITORY_AUDIT.txt` | Dated repository/Git/structure/provenance findings |
| `docs/history/repository-reviews/COMPLETE_FILE_INVENTORY.txt` | Earlier path-by-path classification; this handoff includes newly added paths |
| `docs/history/repository-reviews/FEATURE_INVENTORY.txt` | Active/blocked/planned feature inventory and evidence distinctions |
| `docs/history/repository-reviews/PROJECT_VISION_AND_FUTURE_ROADMAP.txt` | Current recovery-era vision, conditional future goals and research horizons |
| `docs/history/repository-reviews/TECHNICAL_DEBT.txt` | Known external blockers and prioritized security/contract/deployment gaps |
| `docs/security/recovery/SECURITY_AUDIT.txt` | Dated source/ZIP review; records session-shaped values in historical archive commits, not a full production security certification |
| `docs/history/repository-reviews/TEST_AND_VALIDATION_REPORT.txt` | Exact earlier local checks, counts, outcomes and live-provider limits |
| `docs/history/repository-reviews/WORK_PROGRESS.txt` | Recovery and follow-up progress checkpoints |
| `docs/history/repository-reviews/CONSOLIDATION_REPORT.txt` | Decision to keep one running API/web/extension and isolate references |
| `docs/history/repository-reviews/DUPLICATE_ANALYSIS.txt` | Duplicate/overlap review and why whole reference projects were not merged |
| `docs/history/repository-reviews/MIGRATION_SUMMARY.txt` | Summary of previous structural changes |
| `docs/history/repository-reviews/ORIGINAL_TO_NEW_PATH_MAPPING.txt` | Old-to-new path mapping for preserved/moved files |
| `docs/history/repository-reviews/ARCHIVED_FILES_MANIFEST.txt` | Preserved material manifest and disposition |
| `docs/history/repository-reviews/NEXT_DEVELOPER_INSTRUCTIONS.txt` | Older continuation notes; useful context but its main-push workflow is superseded |
| `research/archives/REFERENCE_ARCHIVES.md` | Archive provenance, extraction, licensing and security guide |
| `research/archives/ZIP_MEMBER_INVENTORY.txt` | Every nested file/folder in both uploaded ZIPs; reference-only inventory |
| `research/archives/Teraplayer-main.zip` | Sanitized third-party FastAPI/React/extension product reference. Player/folder ideas exist there, not in our active app |
| `research/archives/terabox-gateway-main.zip` | Sanitized third-party Flask/aiohttp provider/failure-handling reference; not our running backend |
| `research/future-ideas/PROJECT_IDEA_AND_FUTURE_VISION.txt` | Full older media/import/conversion/AI idea; speculative scope, not existing features or automatic task authorization |
| `docs/security/recovery/REPOSITORY_STRUCTURE_AUDIT_2026-11-17.md` | Earlier restructuring and archive security findings |

### Generated/local folders, not product source

- `services/api/.venv/`: installed Python environment; recreate from `requirements.lock`.
- `apps/web/node_modules/`: installed npm dependency tree; recreate with `npm ci`.
- `apps/web/.next/`, `out/`, `dist/`, `*.tsbuildinfo`: build/type output; regenerate as appropriate, do not commit.
- Python `__pycache__/`, `.pytest_cache/`: bytecode/test caches.
- `apps/web/test-results/`, `playwright-report/`: generated browser-test results; never retain private-link traces without a reviewed need.
- `.env`, `.env.local` and other real environment files: local configuration, not shared credentials. Example files are intentionally tracked.
- `research/extracted/Teraplayer-main/` and `research/extracted/terabox-gateway-main/`: ignored copies recreated by the extraction script. Third-party workers, helper agents, cron scripts and cookie paths are not our startup instructions.
- `/workspace/.npm-cache/`: cloud machine package cache outside the checkout; not a project feature.
- `.git/`: repository metadata; do not edit manually. Workspace-level platform folders outside this checkout are not application folders.

Proposed `infra/`, `packages/contracts/`, upload/storage workers and account services are **not present**. Add a component only when a selected task needs it.

## 4. Ordered implementation tasks

**Current engine queue (newer owner instruction):** E01 audit/checkpoint complete; E02 bounded streaming/retry/integrity/cleanup complete; E03 strict in-call Range recovery complete; E04 extension config/package/source-link complete; E05 controlled benchmark, typed metadata UI and affected application validation complete. Final documentation/remote evidence is recorded in the continuation record. T01–T25 below remain longer-term source/product definitions, not prerequisites for independent engine development.

Use these IDs in branches, commits and PRs. An unchecked item is not finished. Sizes are rough engineering scope (`S`, `M`, `L`), not delivery promises; external approval has no predictable code estimate.

### Immediate queue and dependencies

| ID | Priority / size | State | Dependency / responsible role |
| --- | --- | --- | --- |
| T01 | P0 / S | Complete for this checkpoint; recheck on resume | Implementer + reviewer: baseline/source/remote inspection; CI API unavailable |
| T02 | P0 / S | Owner action unresolved | Owner: confirm revocation of any exposed historical sessions |
| T03 | P0 / external | Blocked | Owner + provider: permitted scope and partner access |
| T04 | P0 / S + external | Blocked | Owner: approved credentials, exact hosts and small owned fixture after T03 |
| T05 | P0 / M | Feasible offline | API implementer: focused egress/transfer regression gaps after T01 |
| T06 | P0 / M | Live proof blocked | API implementer + owner: existing probe after T03–T04 |
| T07 | P0 / L | Design feasible; enablement blocked | API/security: provider-approved individual user authorization |
| T08 | P0 / L | Blocked for real field mapping | API: authorized provider adapter after T06–T07 |
| T09 | P0 / L | Blocked | API: secure single-file delivery after T06–T08 |
| T10 | P0 / M | Partly feasible offline | QA/API: real integration matrix after T06; new routes after T08–T09 |
| T11 | P1 / M | Runtime client types complete; shared fixtures pending | API/client: consistent host fixtures and types |
| T12 | P1 / M | Renderer locally verified; live source proof blocked | Web: returned metadata/error UI present; real source depends on T08 |
| T13 | P1 / M | Deferred until G1 | Web: real download UX after T09, T12 |
| T14 | P1 / M–L | Provider-dependent | API/web: verified preview/player/qualities after T06–T08 |
| T15 | P1 / L | Provider-dependent | API/web: folder navigation and pagination |
| T16 | P1 / L | Conditional | API/web: protected-share access only with approved supported flow |
| T17 | P1 / L | Conditional | API/jobs/web: bounded batch/ZIP after reliable single-file/folders |
| T18 | P1 / M | Config/package verified; installed release unverified | Extension: actual Chrome/Edge evidence and owned-site release remain |
| T19 | P1 / M | Existing-flow audit feasible | Web/QA: accessibility and client compatibility |
| T20 | P1 / M–L | Design feasible; deploy needs owner | Ops: owned staging, reproducible deployment, limits and secrets |
| T21 | P1 / M | Not implemented | Ops: privacy-safe monitoring and cost controls after T20 |
| T22 | P1 / M | Existing CI; hardening pending | CI/security: dependable PR/release checks and dependency integrity |
| T23 | P1 / M | Owner decisions + implementation | Product/ops: brand, policies, support and release approval |
| T24 | P2 / varies | Deferred | Measured differentiation after G1–G3 |
| T25 | P3 / varies | Deferred | Commercial/extra platforms/AI only after proven core and owner decision |

**Next implementer task:** resume the current E-series engine/client queue from `docs/CODEX_CONTINUITY.md`, then select a measured recovery/correctness gap. T03–T04 apply only to the optional official TeraBox adapter, not generic transfer work. Do not spend an entire task restating a credential blocker or skip ahead to billing/player decoration.

### T01 — Establish the current baseline and select one bounded PR

- [ ] Inspect clean/dirty working state, actual origin, latest default-branch SHA, relevant issues, open PRs and current CI. Do not assume historical GitHub links describe this fork.
- [ ] Run affected existing checks; reproduce any failure before proposing changes. Record versions, command, target SHA, counts and failure classification.
- [ ] Claim a task with specific paths to avoid overlapping edits. Use main for verified completed checkpoints under the newest owner instruction; keep unfinished work on a durable named branch. A worktree is unnecessary unless explicitly requested.
- **Files:** this handoff, `AGENTS.md`, CI and relevant tests; inspect application source before modifying it.
- **Acceptance:** checkpoint log or fallback PR identifies task ID, SHA, current behavior, change, tests and blockers. Unavailable PR/CI metadata is reported as unavailable, never “all green.”

### T02 — Resolve the known historical reference-session exposure

- [ ] Owner confirms whether sessions/token-like values recorded in `docs/security/recovery/SECURITY_AUDIT.txt` were theirs or valid; revoke any affected credentials at the provider.
- [ ] Record only remediation status/date, never the values. Current ZIP sanitization does not remove old Git blobs or revoke sessions.
- [ ] If history cleanup is needed, plan it separately with the owner and collaborators; no force-push/history rewrite as part of routine development.
- **Acceptance:** owner-confirmed remediation or an explicit unresolved owner action. Source inspection cannot certify account security or revocation.

### T03 — Confirm a permitted integration and exact supported scope

- [ ] Use official partner process and current documentation to confirm external/public-share metadata, downloads, protected shares, folders/previews, commercial use, regions, quotas and consent requirements.
- [ ] Record supported/unsupported operations and approval evidence without private documents or credentials in Git. Confirm endpoint/parameter semantics with the provider.
- **Files:** `docs/PROVIDER_FEASIBILITY.md`, `docs/OFFICIAL_OPEN_PLATFORM.md`, `docs/IMPLEMENTATION_LOG.md`.
- **Acceptance:** approved access path and explicit boundaries, or a precise remaining external blocker. Setting `TERABOX_PARTNER_APPROVED=true` is not itself approval. Never substitute borrowed cookies or a public proxy.

### T04 — Prepare private configuration and a trusted owned fixture

- [ ] Check existing variable names/bindings before requesting new secrets. Configure `TERABOX_CLIENT_ID`, `TERABOX_CLIENT_SECRET`, `TERABOX_PRIVATE_SECRET`, and a consented `TERABOX_ACCESS_TOKEN` through a secure runtime/secret manager.
- [ ] Supply exact approved API/CDN hosts and an owned small unprotected `/s/1...` share, selected file ID, independently calculated byte length and SHA-256. Configure probe variables documented in `services/api/.env.example`.
- [ ] Record the independent byte length securely with the fixture. The current CLI has no separate expected-length setting: it checks the trusted SHA-256 and upstream size when supplied. Compare its verified byte count with the original file's length separately; do not imply that an independent size assertion already exists in code.
- [ ] Start with the default 1 MiB budget or smaller; the probe's hard ceiling is 10 MiB. The current probe supports one selected root-level file, not every accepted public URL format.
- **Acceptance:** offline preflight exits 0 with no missing/invalid configuration. Do not print values, commit real `.env`, or treat offline success as live proof. Configuration must be exported; the CLI does not auto-load `.env`.

### T05 — Close specific offline egress/transfer security test gaps

- [ ] Inspect existing tests first; select a demonstrated missing case, such as malformed URL/host, mixed/private DNS, checked-IP/TLS behavior, redirect, oversized/encoded response, truncated transfer, timeout, cancellation or cleanup.
- [ ] Preserve exact-host allowlists, TLS verification, finite response budgets and credential separation. Fix the smallest affected path if a regression test exposes a defect.
- **Files:** `services/api/app/egress.py`, `official_shares.py`, related tests; OAuth tests only when relevant.
- **Acceptance:** a bug fix has a meaningful test that fails before and passes after correction; a coverage-only PR can exercise existing correct code without inventing a defect. Existing security/API tests still pass. No generic proxy fallback, disabled TLS/checksum verification, or redundant rewrites. Mocked transfer results remain labelled offline.

### T06 — Prove one real authorized file using the existing probe

- [ ] Follow `docs/OPERATOR_VALIDATION.md`: valid offline config first, then explicitly authorized `--live` on a small owned fixture.
- [ ] Verify regional/token behavior, real file ID/name/size and the documented `access_token` versus `access_tokens` and `fs_id` versus `fid_id` inconsistencies. Fix mappings only from approved actual responses, with redacted regression fixtures.
- [ ] Verify the entire transfer, exact expected size and independently known SHA-256; record date, commit, limits, permission scope and sanitized result.
- **Acceptance:** actual matching bytes, not HTTP 200, a resolved URL, or a browser click. A failure remains blocked/failed with diagnosis. Operator success is limited to that fixture/account and does not enable anonymous downloads.
- **Environment caveat:** the secure transport uses direct checked-IP connections with no implicit proxy. Confirm the execution host supports that model; diagnose connectivity without weakening the transport or bypassing host/network policy.

### T07 — Design and implement individual authorization and isolation

- [ ] Define provider-approved consent, OAuth state/callback protection, session lifecycle, per-user scopes, token storage/encryption/access controls, refresh/revocation and deletion.
- [ ] Decide what can be accessed anonymously under actual approval. Never place an operator-wide token behind an anonymous route.
- [ ] Add adversarial tests for cross-user/share/file access, expired/revoked tokens, callback misuse and logging leaks.
- **Files:** provider/OAuth/API boundaries and new auth/storage modules only where the approved design requires them; document architecture before public enablement.
- **Acceptance:** reviewed design plus tests demonstrating isolation and safe expiry/revocation. No tokens in frontend, extension, public models, logs or API/CDN cross-client leakage. General optional user accounts/billing remain separate later tasks.

### T08 — Implement the authorized public provider adapter

- [ ] Reuse `ShareProvider`, current schemas and safe egress; map actual verified metadata into bounded sanitized public records.
- [ ] Report only actual capabilities; implement stable expired/not-found/protected/denied/rate-limit/outage errors. Leave unsupported operations disabled.
- [ ] Preserve safe unconfigured behavior for missing/invalid setup; return meaningful readiness only for a genuinely usable provider.
- **Files:** `provider.py`, `models.py`, `main.py`, verified official-client boundary and corresponding contract tests.
- **Acceptance:** passing offline contracts and authorized fixture evidence through the public API under T07 isolation. No raw upstream tokens/links or guessed filenames/qualities in metadata responses.

### T09 — Implement secure single-file download delivery

- [ ] Choose an approved short-lived direct handoff or a bounded controlled stream; document why it fits provider terms and cost limits.
- [ ] Authorize selected file IDs against share/session; protect temporary links, safe filenames/content disposition, redirects, size/time/concurrency, cancellation, and cleanup.
- [ ] Define observable completion honestly: a handoff proves dispatch, while a verified transfer proves completion. Do not invent progress.
- **Files:** new versioned download route/service only as needed, existing models/provider/egress and focused tests.
- **Acceptance:** an actual owned-file transfer through the selected public flow matches size/hash. Unauthorized IDs, expired handoffs, malicious filenames/hosts, partial responses and resource-limit failures behave safely.

### T10 — Expand the authorized integration and failure matrix

- [ ] Maintain revocable owned fixtures for valid, expired/deleted, denied/protected, folder/nested and approved larger-file scenarios, when the provider supports them.
- [ ] Exercise expiry, timeout/rate limit, interruption/cancellation, regional behavior and limits; distinguish controlled simulations from actual provider responses.
- [ ] Add gated live checks without making offline CI depend on secrets. Avoid private-link traces, response dumps or durable sensitive artifacts.
- **Acceptance:** reproducible commands, fixture ownership/limits and dated outcomes for each supported capability; unsupported/blocked/skipped cases explicit. No requirement that production integration always succeeds merely because 173 offline tests pass.

### T11 — Prevent API/client contract drift

- [ ] Compare Python and extension URL rules using shared safe fixtures; keep backend admission authoritative.
- [ ] As API responses grow, generate/reuse TypeScript contracts from OpenAPI rather than maintaining divergent client assumptions. Do not add an unused contract package just for structure.
- **Files:** `links.py`, `links.mjs`, API schemas, client types and their tests.
- **Acceptance:** same supported/rejected fixture expectations across clients; meaningful schema drift fails a check; no server secrets in generated artifacts.

### T12 — Render verified metadata and complete web states

- [x] Replace provider-status-only success with runtime-validated returned file name, size/type and actual quality labels; empty/malformed/stale states tested locally. The current public model does not supply thumbnail or expiry URLs; do not invent them.
- [ ] Preserve validation, loading, empty, protected/denied/expired, unsupported and retry states, cancellation and privacy-safe handoff.
- **Files:** `apps/web/app/page.tsx`, small components/styles as justified, browser tests.
- **Acceptance:** accessible desktop/mobile journey against the authorized API, safe hostile-name rendering, no fabricated files or capability buttons. Mock UI tests are separate from live acceptance.

### T13 — Add truthful website download actions

- [ ] Consume T09 using only authorized file/share references; handle expiry, denied access, retries and cancellation.
- [ ] Label transfer dispatch versus verified completion accurately; show byte progress only when actually observable.
- **Acceptance:** owned-fixture journey completes, bytes match independently, errors recover without stale actions, and credentials/private links do not enter analytics or logs.

### T14 — Add supported media preview and real qualities

- [ ] Establish source format/preview/quality capabilities from approved provider evidence first; extend sanitized API contracts where needed.
- [ ] Use browser-native playback or a reviewed maintained player library; add accessible controls, fullscreen/PiP where available and explicit unsupported/expired states.
- **Acceptance:** an actual permitted media source plays on supported target browsers; quality/subtitle options come from real source data. No pretend 720p/1080p/4K or expensive transcoding to fill UI options.

### T15 — Add bounded folder browsing and search

- [ ] Confirm permitted folder APIs; implement authorized pagination, hierarchy/breadcrumbs, selection and bounded search. Distinguish searching loaded entries from an entire remote tree.
- [ ] Add traversal/ID ownership checks, collection/request limits and clear empty/partial/failure states.
- **Acceptance:** authorized nested-folder fixture shows correct hierarchy/page boundaries; malicious paths and foreign file IDs fail; unsupported folders are not advertised.

### T16 — Support protected shares only through an approved flow

- [ ] Confirm provider-supported user consent/password verification and secret-handling requirements; otherwise return an explicit unsupported/auth-required state.
- [ ] Never persist/share passwords casually, reuse third-party sessions, or bypass protection.
- **Acceptance:** owned protected fixtures demonstrate permitted access, wrong/expired credentials and safe errors without leaks; absent permission keeps the feature disabled.

### T17 — Add bounded batch selection and ZIP jobs where justified

- [ ] Confirm rights/provider capability and operating budget; define file-count, total-byte, time, memory/storage and concurrency limits before writing job code.
- [ ] Implement owned job IDs, traversal-safe archive names, duplicate handling, cancellation, expiry/cleanup and accurate partial failure results.
- **Acceptance:** oversize, malicious-name, cross-user, cancelled and partly failed jobs respect bounds and leave no unintended files. Single-file reliability must already be proven; no unbounded large proxy jobs.

### T18 — Complete the Chrome/Edge extension journey

- [ ] Install the existing unpacked development extension in actual Chrome and Edge; document supported/unsupported tabs, browser failures and fragment handoff. Parser tests alone do not satisfy this.
- [x] Support controlled validated owned HTTPS release configuration and exact local defaults while preserving minimal permissions/shared handoff.
- [x] Package reproducibly without changing source config, with automated popup/origin/archive checks. Actual installed-browser outage/expiry/privacy/store review remains pending.
- **Files:** extension manifest/popup/link module/tests and release docs.
- **Acceptance:** dated installed-browser evidence and real authorized end-to-end journey when G1 is available; no unrelated tab/history/cookie access. Store publishing requires owner accounts and separate release authorization.

### T19 — Audit accessibility, responsiveness and browser behavior

- [ ] Test keyboard/focus order, labels, status announcements, contrast, responsive overflow, reduced motion and real failure recovery.
- [ ] Add relevant browser/device coverage beyond Chromium where the product claims support; keep tests tied to user journeys.
- **Acceptance:** documented findings fixed or explicitly tracked, usable mobile/desktop flow, targeted regression coverage. Existing dark responsive CSS is not a completed accessibility audit or theme/i18n system.

### T20 — Prepare owned staging and reproducible deployment

- [ ] Select owned hosting/domain, define reproducible build/start/deploy and rollback; add container/setup files only if useful to the chosen host.
- [ ] Configure HTTPS, exact production API/CORS origins, trusted proxy peers, secret manager, egress compatible with checked-IP transport, and aggregate rate/concurrency/bandwidth limits across workers.
- [ ] Keep process liveness distinct from provider readiness. Preserve the cloud environment's saved install/start instructions and restart processes after restoration.
- **Acceptance:** staged web/API smoke and authorized owned-file transfer, security headers, no localhost production dependency/client secrets, tested limits and rollback. Production publish/deploy is a separate owner-authorized release step.

### T21 — Add privacy-safe operations and cost visibility

- [ ] Measure aggregate resolve/error rates, latency, observed transfers versus handoffs, quota hits, resource use and cost per completed fixture transfer.
- [ ] Define alerts, bandwidth/storage budgets, retention/deletion and an incident runbook; build an operator dashboard only when those metrics exist.
- **Acceptance:** staged failures trigger actionable alerts; raw share URLs, tokens, signed links and personal filenames are absent from routine metrics/logs; cost ceilings have an enforceable response.

### T22 — Strengthen PR quality gates and dependency integrity

- [ ] Keep current API/web/extension checks; make required PR jobs reliable at exact head SHA. Add focused lint/static checks only with actionable coverage and scripts that actually exist.
- [ ] Review dependency/license scanning, Python artifact hashes and immutable CI action pins; resolve the known Starlette/httpx testclient deprecation during a controlled dependency review, not by disabling tests.
- [ ] Add installed-extension/release checks and gated authorized live checks where practical. Do not send secrets to untrusted PR code.
- **Acceptance:** relevant checks execute nonzero tests, preserve exit status and pass at reviewed SHA; reproducible installs retain TLS/signature/checksum verification. Report vulnerabilities or skipped checks truthfully rather than suppressing them.

### T23 — Establish production identity, policies and release approval

- [ ] Confirm original brand and production source/support links. The website View source href is now repaired to the current repository; historical documentation links remain historical.
- [ ] Publish clear non-affiliation, privacy/retention, terms, support and copyright-reporting information; review analytics/cookie choices and extension store requirements.
- [ ] Reconcile outdated summaries using dated evidence, while preserving verbatim prompts and historical records. Add third-party notices when licensed code is actually reused.
- **Acceptance:** owned staging has correct public configuration, identity and support/policy surfaces; permission/license/release review complete. Do not claim production readiness or submit stores solely because CI passed.

### T24 — Later differentiation, after reliable core and operations

- [ ] Opt-in/local-first Continue Watching, bookmarks/history and erase controls.
- [ ] Accessible light/dark preference and prioritized localization.
- [ ] HTTP Range/resume, source subtitle/quality support and safe external-manager handoff only where proven available; no credential-bearing link sharing.
- [ ] Measured folder/search/performance improvements, Firefox compatibility and PWA if justified.
- **Requirements:** `PLAYER-01..03`, `DL-01`, `UX-02..03`, `EXT-03`, `WEB-05`, `SEO-01` in product requirements. Existing English/dark presentation is not these completed capabilities.
- **Acceptance:** each item gets its own bounded task/PR, measurable user value, privacy controls and relevant fixture/browser tests. No offline remote-media promise from a PWA shell.

### T25 — Later business, additional providers/platforms and optional AI

- [ ] Evaluate optional accounts/sync, authenticated developer API/quotas, entitlements/billing and support only after reliability and unit economics are established.
- [ ] Consider Android/Telegram or other permitted storage adapters only through a separate owner-approved scope with security/licensing/support analysis.
- [ ] Owned-media import/conversion, opt-in transcripts/captions/search/AI remain research ideas. Require authorized input bytes, consent, deletion controls, licensing and resource budgets; AI cannot establish access rights or recover provider-withheld files.
- **Requirements:** `ACCOUNT-01`, `API-01`, `BILLING-01`, `PLATFORM-01..02` and conditional future roadmap.
- **Acceptance:** separate approved requirements and evidence for each feature. Do not add accounts, billing, media workers, or a second product as a workaround for blocked TeraBox access.

### Completion rule for every task

A task is complete only when its acceptance criteria are met, relevant code/tests pass, the exact reviewed commit is recorded, and the status/checklist/log reflect its real limits. A merged PR may complete one task without completing an entire gate. The reviewer must keep **offline**, **mocked**, **authorized live**, **manual installed-browser**, and **production** evidence distinct.

## 5. Development commands and evidence

**Latest current-source results:** 250 API tests (74 engine + 3 CLI + 173 existing), 50 extension tests and 20 browser checks passed; build/typecheck and pip check passed. New API/engine commands are in `docs/DOWNLOAD_ENGINE.md`; extension packaging commands are in `docs/EXTENSION_DEVELOPMENT.md`. The earlier onboarding table below remains historical evidence, not the latest counts. Current validation is local; no fresh vulnerability audit or current-fork CI pass is claimed.

Use the existing isolated checkout at `/workspace/create-terabox-downloader`. No worktree is required. CI uses Python 3.12 and Node 22; the prepared cloud machine was validated with Python 3.12.14 and Node 24.22.1. Prefer repository locks and inspect tool versions when moving hosts.

```bash
# Repository root: reproduce dependencies when absent/stale.
python3 -m venv services/api/.venv
services/api/.venv/bin/python -m pip install --no-cache-dir -r services/api/requirements.lock
services/api/.venv/bin/python -m pip check
cd apps/web
npm ci --cache /workspace/.npm-cache --no-audit --no-fund
NEXT_TELEMETRY_DISABLED=1 npm run build
npm run typecheck
```

The workspace npm cache is intentional: the prepared machine's home cache was not writable. Keep lockfiles unchanged unless a selected dependency-update task requires a deliberate review.

```bash
# Repository root: existing offline and extension checks.
PYTHONPATH=services/api services/api/.venv/bin/python -m pytest -q services/api/tests
node --check apps/extension/popup.js
node --test apps/extension/tests/*.test.mjs
node -e "if (require('./apps/extension/manifest.json').manifest_version !== 3) process.exit(1)"
services/api/.venv/bin/python docs/verify_handoff_archive.py

# Offline only; exit 2 is expected until approved provider configuration exists.
PYTHONPATH=services/api services/api/.venv/bin/python -m app.preflight
```

```bash
# From apps/web, after production build; ensure ports 3000/8000 are free
# or deliberately use the known local services. It can launch both itself.
PATH=/workspace/create-terabox-downloader/services/api/.venv/bin:$PATH \
PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium \
NEXT_TELEMETRY_DISABLED=1 npm run test:e2e
```

System Chromium is installed in this cloud machine. On another host install Playwright's required browser/dependencies using the documented setup instead of assuming that path exists.

Start services in separate terminals:

```bash
# From services/api
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log

# From apps/web, after a build
NEXT_TELEMETRY_DISABLED=1 npm run start -- --hostname 0.0.0.0 --port 3000
```

For hot reload, web `npm run dev -- --hostname 0.0.0.0 --port 3000` and API `--reload` are available. This Next.js version generates `apps/web/AGENTS.md` and changes `next-env.d.ts` in dev mode. Inspect Git status before/after; preserve pre-existing changes and remove only generated changes caused by your own setup. Never overwrite user work while cleaning outputs.

Use local requests internally to verify health, valid-link normalization and actual homepage content; an open port alone is insufficient. Do not create user-facing localhost preview links during onboarding. Processes are not preserved by environment snapshots.

### Evidence available at this handoff

The earlier cloud onboarding in this conversation tested the same `de7e4b3` application source with these outcomes:

| Check | Observed result | Limit |
| --- | --- | --- |
| API pytest | 173 passed; one Starlette/httpx testclient deprecation warning | Offline/mocked upstream |
| Extension parser tests | 16 passed; syntax check passed | No installed-extension proof |
| Web build and TypeScript | Passed | No live provider validation |
| Playwright | 10 passed: five cases × desktop/mobile | Local API and controlled browser interception; no TeraBox network |
| Python dependency compatibility | `pip check` passed | Not a fresh vulnerability scan |
| Word archive verifier | Passed | Historical archive consistency only |
| Service requests | API health and valid-link normalization; dev and production homepage content verified | Local services only |
| Offline preflight | Exit 2, required partner/fixture settings missing, provider disabled | Expected blocked live setup |

The table above preserves the earlier onboarding evidence. The latest engine/client work additionally ran the 250 API, 50 extension and 20 browser checks summarized at the start of this section; it did not run a new vulnerability audit. Markdown paths/file coverage/diff were checked for the final docs. Earlier detailed validation remains in [TEST_AND_VALIDATION_REPORT.txt](docs/history/repository-reviews/TEST_AND_VALIDATION_REPORT.txt). No current-fork Actions success or live TeraBox transfer is certified here.

## 6. Instructions for the implementing tool

Read `AGENTS.md`, this handoff, current source, and the focused docs for your task. Historical prompts provide context; the owner's newest instructions take precedence. Do not restart the project or assume checked-in reference features are integrated.

Suggested task prompt to copy:

> Continue sarfiaroui-oss/create-terabox-downloader. Read AGENTS.md, docs/CODEX_CONTINUITY.md and PROJECT_STATUS_AND_TASKS.md. Inspect latest main, concurrent changes and relevant CI/PR evidence. Continue independent download-engine improvements against controlled permitted sources; do not make official partner credentials a dependency for generic transfer work. Preserve source-access security and truthful TeraBox-unavailable behavior. Implement one bounded meaningful improvement, test it, update continuity/status/log, commit and immediately push verified main checkpoints without force. If main is protected, push a durable named branch and use a PR. Never put incomplete work on main, expose an arbitrary URL proxy, invent download/benchmark success, or build unrelated developer APIs/billing/AI products.

Each tool should work on one clearly assigned task/PR. Coordinate overlapping API, auth and schema changes before editing. Never overwrite someone else's local modifications, force-push shared history, or rewrite historical prompts/recovery records merely to match new status.

Exactly two primary code references remain [TeraPlayer](https://github.com/gitmarcus07/Teraplayer) and [TeraBox Gateway](https://github.com/saahiyo/terabox-gateway), as audited in `docs/RESEARCH_AND_LICENSES.md`. Their MIT files allow potential selective reuse subject to provenance/notices; they do not prove a permitted live provider. Do not import their external workers, borrowed sessions, unsafe forwarded-IP trust, raw-link logging, or whole competing frameworks.

## 7. PR review and monitoring

The later engine prompt authorizes direct verified main checkpoints; this review procedure remains applicable to PRs from other tools or protected-main fallback branches. It does not revoke that newer authorization.

### Required PR description

```markdown
Task ID(s): T__
Base SHA / reviewed head SHA:
Problem and resulting behavior:
Files changed and why:
Dependencies / provider approval required:
Acceptance criteria met:
Tests: exact commands, counts, pass/fail/skipped and local/CI/live distinction:
Security, privacy, licensing and operating-cost implications:
Remaining blockers / deliberately unsupported behavior:
Documentation/status updated:
```

### Reviewer checklist

- [ ] Verify actual repository, base/head SHA, concurrent PRs and task scope; review the complete diff.
- [ ] Check that the PR reuses existing modules, contains no unrelated rewrite, and preserves provider-disabled behavior unless the live/authorization gates genuinely pass.
- [ ] Review URL/SSRF/TLS/redirect, user/file ownership, credentials/logging, request/transfer bounds and cancellation for affected paths.
- [ ] Inspect tests and execute relevant checks. Check CI at the exact PR head; stale green runs and zero-test success do not validate changes.
- [ ] Require authorized real metadata/bytes/hash for provider-dependent claims; separately review installed-browser and staging evidence when applicable.
- [ ] Require truthful file/task/checklist/log updates, source/license notices where needed, and clear outstanding blockers.
- [ ] Report concrete findings by severity and file/line, propose bounded fixes, then recheck the changed head. Mark ready only after material findings are resolved.
- [ ] Do not merge/publish/deploy automatically. Obtain the owner's merge/release instruction, or follow an explicit standing authorization when one is provided.

### Review queue

| Task | PR URL | Head SHA reviewed | Checks / findings | Next action |
| --- | --- | --- | --- | --- |
| No PR registered in this handoff | — | — | Current-fork PR/CI API returned `Forbidden`; no assertion that the PR queue is empty | Register the implementing tool's PR URL, inspect it when accessible |

The assistant can review and recheck submitted PRs during an active session when GitHub access is available. **This file does not install a background watcher or promise continuous monitoring after a chat ends.** Share the PR URL or request another review when the other tool submits or updates it; update this queue with exact reviewed SHA and outstanding findings. Read-only Git remote access worked during this handoff, but PR/CI API access did not. Do not infer missing Git credentials from that API error or request secret values in chat.

Keep this file current after accepted changes: update the inspected date/SHA, feature status, new/removed paths, task state/dependencies and review evidence. Keep detailed acceptance history in the implementation log. Another tool should be able to resume from the repository without relying on this conversation.

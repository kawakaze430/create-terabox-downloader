# Product Requirements — TeraBox Downloader Platform

**Status:** Product vision and target requirements; not a claim that any feature is implemented.  
**Updated:** 2026-11-13  
**Owner:** Repository maintainer  
**Audience:** Product managers, software engineers, Codex agents, designers, QA, security, and operations.

## 1. Mission and business objective

Create an **independently branded, commercially competitive, reliable and trustworthy TeraBox file-access and downloading platform**. This is a real software product, not a proof-of-concept UI, an exact clone of another website, or an unmaintained pile of merged repositories.

Build and operate a cohesive system under the owner's control: a fast mobile-friendly website, Chrome/Edge extensions, a shared backend and provider integration, monitoring, tests, documentation, and deployment. Longer-term extensions include Firefox, PWA, user accounts, API access, subscription plans, and further distribution channels.

**North-star outcome:** For an authorized, supported TeraBox share, a user can understand what files are available, preview when possible, download permitted content with accurate status/errors, and trust the site with their privacy.

**Competitive ambition:** Aim to outperform leading products on reliability, speed, user experience, privacy, transparency, accessibility, and feature depth. No reliable global #1 ranking has been established; never claim we are #1 without independently sourced evidence.

## 2. User groups and experiences

| Persona | Main job to be done |
| --- | --- |
| First-time website visitor | Paste a legitimate TeraBox share URL; inspect, preview and download authorized files with minimal steps. |
| Returning viewer | Resume a permitted preview, use bookmarks/history if opted in, and manage their own preferences. |
| Large-folder user | Browse/search a share, select several files and obtain a multi-file or ZIP download where supported. |
| Browser-extension user | Detect a supported TeraBox page, inspect the shared file and trigger the same authorized backend workflow. |
| Mobile user | Use a fast, responsive, accessible site without installing an app. |
| Site operator | See reliability, capacity, cost, abuse and error metrics without unnecessarily storing personal share URLs. |
| Future subscriber/developer | Access clearly defined, lawful, rate-limited optional paid features and documented API. |

## 3. Non-negotiable product principles

1. **Working engine before visual polish.** A slick frontend that cannot reliably access permitted files is not a successful release.
2. **Rights and access first.** Handle publicly shared files or files for which the user has legitimate authorization. Do not bypass TeraBox authentication, CAPTCHA, access controls, premium restrictions, or protections, and do not facilitate unauthorized copyrighted downloads.
3. **One system, not five apps merged together.** Maintain a single monorepo with well-defined component boundaries and consistent UX.
4. **Be independent where possible.** Own our hosting, domain, backend, API definitions, branding, deployment, monitoring and credentials. TeraBox remains an upstream dependency; do not claim true independence from its service.
5. **Truthful feature display.** Never invent a 1080p/4K option, a file format, a filename, a speed, or a working download. List only capabilities returned by a verified, authorized integration.
6. **Respect source licenses.** Reuse code only when licensing and provenance are verified; retain required copyright/license notices. New original product code and branding are maintained separately.
7. **Privacy and safety by design.** Minimal permissions and data retention; avoid exposing files, session tokens, passwords, private shares or sensitive logs.
8. **Avoid wasted Codex credits.** Audit existing code before rewriting, reuse maintained libraries where suitable, work in tested milestones, and defer speculative features.

## 4. Competitive landscape and differentiation

Products worth periodically evaluating: [iTeraPlay](https://iteraplay.com), [TeraDownloader](https://teradownloader.com), [TeraGrab](https://teragrab.com), [TeraPlayer](https://teraplayer.in), and [TeraLoader](https://teraloader.com). Their advertised features are *research leads*, not independently verified performance or endorsement.

Benchmark the user flow, file/folder handling, video player, copy-link workflows, retry behavior, responsive design, browser integration, privacy, cost, accessibility, and support. Maintain dated evidence before making comparisons. We should win through measurable engineering outcomes, not an unsupported “#1” claim.

## 5. Product scope and priority

**Statuses in this document are intended targets, not implementation claims.** The progress checklist must be maintained separately as evidence is generated.

| ID | Capability | Priority | Acceptance intent / caveat |
| --- | --- | --- | --- |
| CORE-01 | Validate and normalize supported TeraBox share links | P0 | Exact allowed hosts; clear unsupported-link errors; no arbitrary server fetch. |
| CORE-02 | Resolve permitted share metadata | P0 | Real filename, size, MIME/file type, availability, and thumbnail when provided. |
| CORE-03 | Download authorized files | P0 | Successful verified transfer; no broken/fictional links. |
| CORE-04 | Expiry and error handling | P0 | Explain invalid, expired, unavailable, password-required, permission-denied, upstream-down, and rate-limited states. |
| CORE-05 | Share-level security and abuse limits | P0 | SSRF defense, host/redirect validation, rate limiting, privacy-safe logging. |
| CORE-06 | Repeatable provider integration tests | P0 | Authorized public test fixtures plus mocked contract tests; integration may be environment-gated. |
| WEB-01 | Responsive paste-link experience | P1 | Mobile and desktop; loading, success, empty, and error states. |
| WEB-02 | File details, previews and thumbnails | P1 | No previews when media is unsupported or unavailable. |
| WEB-03 | Built-in video player | P1 | Controls, fullscreen and picture-in-picture where supported; fallbacks. |
| WEB-04 | Available-quality display | P1 | Show only verified source formats/resolutions; no fabricated transcoding. |
| FOLDER-01 | Folder navigation and searchable listing | P1 | Correct hierarchy, pagination/limits, safe filenames. |
| FOLDER-02 | Multi-select and batch downloads | P1 | Clear limits, cancellations and transfer status. |
| FOLDER-03 | ZIP export | P1 | Only where licensed access, upstream capabilities and cost budgets permit; bounded resource use. |
| EXT-01 | Chrome extension, Manifest V3 | P1 | Detect current supported link with minimal permissions; shared backend workflow. |
| EXT-02 | Microsoft Edge support | P1 | Reuse Chromium extension architecture and test packaging. |
| UX-01 | Accessible modern original brand | P1 | Mobile-first, keyboard use, meaningful contrast, no imitation of competitors' trade dress. |
| UX-02 | Localized interface | P1 | Language-ready architecture; initially English, add languages based on real demand. |
| OPS-01 | CI, observability, docs and deployment | P1 | Build/test/lint/security check; staging and deployment instructions; basic dashboards. |
| OPS-02 | Admin health and cost dashboard | P1 | Provider success, latency, upstream errors, extension health, bandwidth costs; minimize user data. |
| UX-03 | Dark/light theme | P2 | Accessible, persisted locally without requiring sign-in. |
| PLAYER-01 | Continue Watching | P2 | Opt-in/local-first playback position; user can erase it. |
| PLAYER-02 | Bookmarks and history | P2 | Opt-in/local-first initially; clear privacy and deletion controls. |
| PLAYER-03 | External download-manager handoff | P2 | Copy a link only if legitimately obtainable and not a secret/credential-bearing URL; warn about expiry. |
| DL-01 | Resume/progress reporting | P2 | Only where upstream HTTP Range/transport supports it; no false promises. |
| EXT-03 | Firefox extension | P2 | Browser-specific compatibility, security and listing review. |
| WEB-05 | Installable PWA | P2 | Useful offline shell only; do not suggest offline access to remote video data. |
| API-01 | Versioned public developer API | P3 | Auth, rate limits, privacy, docs, abuse protections. |
| ACCOUNT-01 | Optional accounts and synced preferences | P3 | Data minimization, explicit consent, deletion and security controls. |
| BILLING-01 | Future free/premium tiers | P3 | Entitlements and paid plans after core feasibility and compliance are established. |
| PLATFORM-01 | Android app and Telegram bot | P3 | Separate business/privacy/security assessment before build. |
| PLATFORM-02 | Advanced video processing | P3 | Only for content users have rights to process and if useful; avoid expensive unnecessary transcoding. |
| SEO-01 | Public SEO pages, docs, FAQ, support | P2 | Genuine/helpful content, fast Core Web Vitals, clear non-affiliation and copyright support. |

Priority meaning: **P0** prove viability/security; **P1** first competitive release; **P2** differentiation after reliability; **P3** growth ideas, not current commitments.

## 6. Required user journeys

### A. Single public share
User pastes an allowed TeraBox share link → UI validates format → backend verifies host and share access through permitted integration → display verified metadata/preview/options → user chooses a supported file → browser downloads from a properly authorized source or controlled safe transfer mechanism → informative success/failure feedback.

### B. Folder
User opens a share with folders → browse hierarchy and search loaded metadata → select one or more files → download individually or bounded ZIP where supported. Filenames must be sanitized and limits clearly communicated.

### C. Browser extension
User visits a supported share page → activates extension or uses a minimal page action → extension retrieves the active URL with minimal permissions → same API and error states as website → authorized browser download. No silent scraping of unrelated tabs, cookies, or histories.

### D. Account/password-protected share
Treat authorization as an explicit product decision. Only implement a provider-supported, permitted flow with user consent and secure secret handling. Never circumvent access controls; if no compliant implementation is available, return an understandable “unsupported” state.

### E. Unsupported or changed upstream behavior
When TeraBox changes, detect the failure, classify it, degrade gracefully, notify operations, and disable misleading broken buttons. Do not “fix” compatibility by bypassing protections.

## 7. Non-functional requirements

- **Reliability:** measurable successful metadata resolution and completed download rates for supported authorized test shares.
- **Performance:** fast loading, low JS payload, caching only non-sensitive metadata, sensible concurrent request controls, predictable worst-case ZIP/bandwidth costs.
- **Availability:** health checks, upstream failure detection, timeouts/circuit breakers where sensible, incident runbooks.
- **Security:** OWASP-aligned API protection; SSRF and DNS-rebinding defenses; strict host/scheme validation across redirects; secrets kept server-side; no sensitive logs.
- **Privacy:** do not log raw share links by default, full filenames, account credentials or download URL tokens; redact identifiers and set short retention. Consent before optional user tracking; provide deletion controls.
- **Accessibility:** keyboard operation, screen-reader labels, meaningful error messages and contrast testing.
- **Internationalization:** string catalogs and locale-aware formatting with no hard-coded translation UI assumptions.
- **Cost:** avoid streaming gigabytes through app servers when a safe permitted direct download exists; quotas on background jobs, ZIP size and concurrency.
- **Transparency:** accurately explain capabilities, failure cases and that this is not an official TeraBox product.

## 8. Indicative success measures (targets, not measured results)

- First gate: demonstrate repeatable, authorized metadata retrieval and file downloads on a documented test matrix.
- Subsequent objective: **≥95% successful resolution** on a defined, representative set of *supported and accessible* authorized links; exclude invalid inputs transparently rather than manipulating the rate.
- Monitor p50/p95 time-to-metadata and download handoff, test coverage, extension compatibility, conversion from paste to successful download, incident duration, accessibility defects and infrastructure cost per completed download.
- Do not assert a “top-ranked” market position, fastest speed, or reliable 4K output without evidence.

## 9. Business and operational requirements

Independently managed domain, hosting, environments, repository ownership, release control, support, acceptable-use policy, privacy notice, copyright/reporting channel, terms, and operational monitoring. Investigate legal and TeraBox policy constraints before commercial launch, and revisit them when upstream behavior changes.

Do not sell subscriptions or deploy advertisements until core reliability, user trust, applicable payment policies and legal obligations are addressed. Treat billing, accounts and analytics as modular extensions to the core.

## 10. Explicit non-goals and blocked behavior

- No bypass of authentication, CAPTCHA, premium restrictions, DRM, rate limits or other access controls.
- No unauthorized downloading or redistribution of copyrighted files.
- No claim that unofficial reverse-engineered endpoints, external proxy services or leaked cookies are official or stable.
- No forced requirement to log in to the downloader for ordinary public-link features unless needed.
- No invented download URL, multiple resolution options, previews or transfer progress.
- No bundling five complete GitHub repositories as a single app without legal and architectural review.

## 11. What developers must deliver as evidence

Every feature PR should state: user value, affected surfaces, implementation details, security/privacy impact, dependency/license notes, test commands/results, screenshots or browser results if UI, limitations, and updated status in the roadmap. A working-looking mock does **not** count as a verified downloader. See [ARCHITECTURE.md](ARCHITECTURE.md), [ROADMAP_AND_QA.md](ROADMAP_AND_QA.md), and [RESEARCH_AND_LICENSES.md](RESEARCH_AND_LICENSES.md).

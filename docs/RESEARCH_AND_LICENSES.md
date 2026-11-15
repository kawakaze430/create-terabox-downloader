# Competitive Research, Reference Repositories, Dependencies & Licensing

**Updated:** 2026-11-13  
**Status:** Research backlog. Mentioning a source here does not mean its code has been audited, reused, or verified to work.

## Why references matter

We intend to build an **original, maintainable product** using proven ideas and legally compatible components rather than blindly combining five full applications. A competitive feature is not necessarily technically feasible or permitted by the provider. Engineers must distinguish an upstream limitation from a defect in our app.

## Reference applications to audit

| Reference | Intended research scope | Licensing / integration action |
| --- | --- | --- |
| [gitmarcus07/Teraplayer](https://github.com/gitmarcus07/Teraplayer) | Main architectural reference: site, API, extension, folders, ZIP, player | Verify the license from current commit; audit each component, tests and upstream assumptions before reuse. |
| [Itz-Ashlynn/Terabox-Web](https://github.com/Itz-Ashlynn/Terabox-Web) | Responsive React UI and share processing experience | Check license and provenance; use patterns when reuse is not permitted. |
| [saahiyo/terabox-gateway](https://github.com/saahiyo/terabox-gateway) | Provider adapter, metadata, streaming and backend mechanics | Evaluate cookies, tokens, worker/proxy dependencies; verify permitted access and license. |
| [SH20RAJ/terabox-player-chrome-extension](https://github.com/SH20RAJ/terabox-player-chrome-extension) | Browser page detection, video playback, extension UX | Audit Manifest version, permissions, origin handling, update health, license. |
| [saahiyo/tera-peek](https://github.com/saahiyo/tera-peek) | Metadata, thumbnail, video-preview and Next.js UX | Audit demo-worker dependence, license and current provider compatibility. |
| [SarangGit/TeraDLDW](https://github.com/SarangGit/TeraDLDW) | Additional Flask + vanilla UI approach | Optional reference only; avoid importing redundant frameworks. |
| [Paidguy/terabox-api](https://github.com/Paidguy/terabox-api) | Optional Cloudflare Workers implementation | Evaluate provenance, access authorization, security and longevity. |
| [0xarchit/Terabox-Downloader](https://github.com/0xarchit/Terabox-Downloader) | Historical upstream compatibility issues | Do not select as foundation without verifying current function. |

Prior discussions described some repositories as MIT-licensed, but **do not rely on old descriptions**. Check each current LICENSE, file-level notices, dependencies and potential copied code before reuse. Unlicensed repository content is *not* automatically open-source for copying.

## Market and feature benchmarking

Candidates: [iTeraPlay](https://iteraplay.com), [TeraDownloader](https://teradownloader.com), [TeraGrab](https://teragrab.com), [TeraPlayer](https://teraplayer.in), [TeraLoader](https://teraloader.com).

Assess with dated screenshots and own authorized test shares:
- Flow from paste → metadata → preview → download.
- Real (not advertised) support for folders, multi-file/ZIP, alternate qualities, temporary links, failure recovery and extension integration.
- Video controls: fullscreen, picture-in-picture, subtitles, Continue Watching, bookmarks.
- UI speed, mobile usability, accessibility, localization, privacy, tracking, support and transparency.
- Operating limits, authentication, premium gating, account features and actual costs.

Do not infer market leadership from a single traffic screenshot or marketing claim. Do not present third-party feature listings as tested capabilities. A market benchmark document with date, test condition and evidence should be produced before making competitive claims.

## Libraries to evaluate (not automatically install)

| Library/tool | Intended value | Key review before adoption |
| --- | --- | --- |
| [Video.js](https://github.com/videojs/video.js) | Accessible, mature player controls and plugin ecosystem | Browser support, build size, version license, maintainability. |
| [hls.js](https://github.com/video-dev/hls.js) | HLS playback where a legitimate stream is actually offered | Do not assume provider supplies HLS; confirm integration and license. |
| [Playwright](https://github.com/microsoft/playwright) | Browser E2E and smoke testing | Scope to local/staging site and authorized fixtures; manage resources. |
| [Sentry SDK](https://github.com/getsentry/sentry-javascript) | Error monitoring | Data processing, privacy redaction, cost and vendor dependency. |
| [aria2](https://github.com/aria2/aria2) | Download/resume techniques | GPL licensing can impose obligations: do not embed/distribute without dedicated review. Prefer standards/browser functionality. |
| [ffmpeg.wasm](https://github.com/ffmpegwasm/ffmpeg.wasm) | Optional browser video processing | Only implement with proven user need and rights; size, performance, license. |

Favor mature libraries, minimal bundles, pinned versions, dependency scanning, compliance attribution and documented replacement paths. Avoid dependencies added only to imitate a competitor.

## Licenses, rights, branding and provider compliance

- Keep the project owner's original source, distinctive brand, graphics and hosting configurations separately documented.
- Preserve copyright notices and third-party licenses for reused code. Add `THIRD_PARTY_NOTICES.md` when material is actually imported.
- A publicly viewable GitHub repository is not automatically permission to copy.
- Do not take other sites' graphics, trademarks, proprietary text or protected source.
- Access only authorized public shares or the user's own authorized files. Do not defeat login, CAPTCHA, DRM, premium restrictions or access controls.
- Verify TeraBox's current terms and integration possibilities with suitable legal review before commercial release.
- Never import third-party users' cookies, session credentials or hardcoded secrets; do not route production traffic through untrusted demo proxies.
- Test and document actual upstream response and breakage; recognize that third-party APIs can disappear overnight.

## Research deliverables for the first Codex milestone

1. Table of reference repos with license URL, commit audited, last activity, major dependencies, security issues, features present, actual test results and a reuse/rewrite/ignore verdict.
2. Benchmark matrix for competitors with observation dates, screenshots or reproduced authorized test evidence, and explicit unknowns.
3. Provider feasibility finding: compliant data access methods, unsupported operations, temporary URL expiry, bandwidth and upstream rate limits.
4. Dependency evaluation: why each extra library is needed, its exact license and compatibility, maintenance signals, size and security.
5. Explicit architecture decision with risks and first implementation milestones.


## 2026-11-16 — audited two primary code references (not provider acceptance)

**Selection: exactly two primary study repositories.** The 49-entry inventory in
`PUBLIC_REPOSITORY_STUDY_LIST.txt` was reviewed by purpose, priority and recorded
license warnings; source-level review concentrated on the two initial candidates.
Supporting libraries in that inventory are not additional primary download engines.

| Primary reference and audited revision | What the inspected source actually provides | Risks, license and actionable decision |
| --- | --- | --- |
| [TeraPlayer](https://github.com/gitmarcus07/Teraplayer) at `2e60ba4b4963a4112aab57eb2d4770175c5f9965` (2026-10-18) | FastAPI `backend/server.py`, React/CRACO `frontend/src/components/FolderBrowser.jsx` and `VideoPlayer.jsx`, browser extension, `backend/services/terabox.py` caching/orchestration, tests. Folder filtering, selection and status UI are useful patterns. | MIT LICENSE file inspected. `backend/services/extractors.py` explicitly uses public third-party API fallbacks and a configurable worker. `terabox.py` can use `COOKIE_JSON`/`TERABOX_NDUS`; MongoDB/admin/caching complexity is not needed for G1. Its legacy `terabox_engine.py` needs individual verification, not blind importing. **Adapt UI state and bounded file-selection concepts after G1; do not import extraction paths, branding, cache of secret links or provider sessions.** |
| [TeraBox Gateway](https://github.com/saahiyo/terabox-gateway) at `063f61fc61bb173fb936fc487f4a18e40436caab` (2026-06-29) | Flask `src/terabox_gateway/api.py`, aiohttp `terabox_client.py`, `utils.py` retries and parsing, `cache.py` bounded TTL/LRU, `rate_limiter.py` windowed control, `config.py` settings. Its API wrapper and error-normalization patterns can inform offline contract cases. | MIT LICENSE file inspected. `config.py` hardcodes an external Cloudflare Worker, loads cookies; `terabox_client.py` uses the Worker and optional session cookies; `rate_limiter.py` directly trusts caller-supplied forwarded IP headers; `cache.py` logs raw share URLs. No test directory in the audited tree. **Study failure handling only, retaining our existing FastAPI, HTTPX, exact host transport and safer peer-derived limits. Do not import Flask, worker, cookies, IP-header trust or raw-link logging.** |

Both repositories have MIT licenses at the audited revisions, which would permit
reuse *subject to notices and provenance review*, but **no third-party code was
copied in this checkpoint**. No current live downloading was reproduced in either
reference, and a repository README's claims are not our acceptance evidence.
TeraPlayer is the stronger product/UX reference; Gateway is the focused Python
provider-boundary/failure-mode reference. Their overlap with existing FastAPI,
validation, API contracts, request admission and extension code argues against
framework imports or a rewrite.

### Ranked next actions and acceptance gates

| Priority | Task / source boundary | Dependency; required evidence; feasible now? |
| --- | --- | --- |
| 1 | Written partner scope and commercial authorization: `docs/OFFICIAL_OPEN_PLATFORM.md` | TeraBox's approval for external shares, downloads, regions and quotas; **external blocker** |
| 2 | Operator-owned small public fixture, file ID and trusted SHA-256: `docs/OPERATOR_VALIDATION.md` | Authorized fixture and secrets configured privately; **external blocker** |
| 3 | Verify real share metadata and endpoint parameter semantics: `app/official_shares.py` | Approved token, regional API host, fixture; filename, ID and size match; **blocked for live proof** |
| 4 | Demonstrate a complete pinned-host checksum-verified transfer: `app/preflight.py`, `app/egress.py` | Approved CDN host and safe fixture, exact byte count and SHA-256; **blocked for live proof** |
| 5 | Prevent malformed OAuth credentials from reaching HTTP: `app/open_platform.py`, `app/official_shares.py` | Offline tests; **implemented 2026-11-16, CI 173 backend tests passed** |
| 6 | Extend SSRF/DNS/redirect and bounded-transfer negative tests: `app/egress.py`, `tests/test_egress.py` | MockTransport and synthetic DNS fixtures; **feasible now**, not live verification |
| 7 | Design individual user authorization and isolation: `app/provider.py`, `app/open_platform.py` | Scope agreement and per-user consent/token lifecycle; **design feasible, live integration blocked** |
| 8 | Map verified live provider fields to sanitized contract: `app/models.py`, `tests/test_provider_contract.py` | Real authorized response samples; **blocked for accurate field mapping** |
| 9 | Implement truthful metadata and file handoff UI: `apps/web/app/page.tsx` | G1 verified download/provider integration and secured API; **deferred** |
| 10 | Test/publish permission-minimal Chrome/Edge extension and production operations: `apps/extension/`, `docs/ROADMAP_AND_QA.md` | Verified web flow, owned deployment, manual browsers and store accounts; **deferred** |

**Official documentation correction:** TeraBox publishes an Open Platform
integration guide at https://www.terabox.com/integrations/docs?lang=en (including
documented OAuth, file/share API operations and regional hosts). Its existence
does not grant partner credentials, external-share scopes, a production download
license or permission to reuse account sessions. The public provider remains
`UnconfiguredProvider` until authorized live validation and per-user isolation.
